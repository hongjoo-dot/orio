"""
Promotion Router
- 행사 관리 API 엔드포인트
- Promotion(마스터) + PromotionProduct(디테일) CRUD
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pandas as pd
import io
from datetime import datetime
from repositories.promotion_repository import (
    PromotionRepository,
    PromotionProductRepository,
    PROMOTION_TYPE_MAP,
    PROMOTION_TYPE_REVERSE_MAP,
    STATUS_MAP,
    STATUS_REVERSE_MAP
)
from repositories import ActivityLogRepository, ExpectedSalesProductRepository
from core import get_db_cursor
from core.dependencies import get_current_user, get_client_ip, CurrentUser
from utils.excel import PromotionExcelHandler

router = APIRouter(prefix="/api/promotions", tags=["Promotions"])

# Repository 인스턴스
promotion_repo = PromotionRepository()
promotion_product_repo = PromotionProductRepository()
expected_sales_repo = ExpectedSalesProductRepository()
activity_log_repo = ActivityLogRepository()


# Pydantic Models
class BulkDeleteRequest(BaseModel):
    ids: List[str]


# ========== 마스터(Promotion) 엔드포인트 ==========

@router.get("")
async def get_promotions(
    page: int = 1,
    limit: int = 20,
    promotion_type: Optional[str] = None,
    status: Optional[str] = None,
    channel_name: Optional[str] = None,
    brand_id: Optional[int] = None,
    year: Optional[int] = None,
    search: Optional[str] = None
):
    """행사 목록 조회 (페이지네이션 및 필터링)"""
    try:
        filters = {}
        if promotion_type:
            filters['promotion_type'] = promotion_type
        if status:
            filters['status'] = status
        if channel_name:
            filters['channel_name'] = channel_name
        if brand_id:
            filters['brand_id'] = brand_id
        if year:
            filters['year'] = year
        if search:
            filters['search'] = search

        result = promotion_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by="p.StartDate",
            order_dir="DESC"
        )

        return result
    except Exception as e:
        raise HTTPException(500, f"행사 목록 조회 실패: {str(e)}")


@router.get("/filter-options")
async def get_filter_options():
    """필터 옵션 목록 조회 (PromotionType, Status, ChannelName)"""
    try:
        channel_names = promotion_repo.get_distinct_channel_names()

        return {
            "promotion_types": [
                {"value": k, "label": v} for k, v in PROMOTION_TYPE_MAP.items()
            ],
            "statuses": [
                {"value": k, "label": v} for k, v in STATUS_MAP.items()
            ],
            "channel_names": channel_names
        }
    except Exception as e:
        raise HTTPException(500, f"필터 옵션 조회 실패: {str(e)}")


@router.get("/{promotion_id}")
async def get_promotion(promotion_id: str):
    """행사 단일 조회"""
    try:
        item = promotion_repo.get_by_id(promotion_id)
        if not item:
            raise HTTPException(404, "행사를 찾을 수 없습니다")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 조회 실패: {str(e)}")


@router.delete("/{promotion_id}")
async def delete_promotion(
    promotion_id: str,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """행사 삭제 (연관 상품, 목표매출도 함께 삭제)"""
    try:
        if not promotion_repo.exists(promotion_id):
            raise HTTPException(404, "행사를 찾을 수 없습니다")

        # 먼저 ExpectedSalesProduct 삭제 (FK 제약 때문에 먼저)
        deleted_expected_sales = expected_sales_repo.delete_by_promotion_id(promotion_id)

        # 연관 상품 삭제
        deleted_products = promotion_product_repo.delete_by_promotion_id(promotion_id)

        # 마스터 삭제
        success = promotion_repo.delete(promotion_id)
        if not success:
            raise HTTPException(500, "행사 삭제 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="DELETE",
                target_table="Promotion",
                target_id=promotion_id,
                details={
                    "deleted_products": deleted_products,
                    "deleted_expected_sales": deleted_expected_sales
                },
                ip_address=get_client_ip(request)
            )

        return {
            "message": "삭제되었습니다",
            "deleted_products": deleted_products,
            "deleted_expected_sales": deleted_expected_sales
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
async def bulk_delete_promotions(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """행사 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        total_deleted_products = 0
        total_deleted_expected_sales = 0
        deleted_promotions = 0

        for promotion_id in request_body.ids:
            # ExpectedSalesProduct 삭제 (FK 제약 때문에 먼저)
            deleted_expected_sales = expected_sales_repo.delete_by_promotion_id(promotion_id)
            total_deleted_expected_sales += deleted_expected_sales

            # 연관 상품 삭제
            deleted_products = promotion_product_repo.delete_by_promotion_id(promotion_id)
            total_deleted_products += deleted_products

            # 마스터 삭제
            if promotion_repo.delete(promotion_id):
                deleted_promotions += 1

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="BULK_DELETE",
                target_table="Promotion",
                details={
                    "deleted_ids": request_body.ids,
                    "deleted_count": deleted_promotions,
                    "deleted_products": total_deleted_products,
                    "deleted_expected_sales": total_deleted_expected_sales
                },
                ip_address=get_client_ip(request)
            )

        return {
            "message": "삭제되었습니다",
            "deleted_count": deleted_promotions,
            "deleted_products": total_deleted_products,
            "deleted_expected_sales": total_deleted_expected_sales
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ========== 디테일(PromotionProduct) 엔드포인트 ==========

@router.get("/{promotion_id}/products")
async def get_promotion_products(promotion_id: str):
    """특정 행사의 상품 목록 조회"""
    try:
        if not promotion_repo.exists(promotion_id):
            raise HTTPException(404, "행사를 찾을 수 없습니다")

        products = promotion_product_repo.get_by_promotion_id(promotion_id)
        return {"data": products, "total": len(products)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"상품 목록 조회 실패: {str(e)}")


# ========== 엑셀 업로드/다운로드 ==========

@router.get("/download/template")
async def download_template():
    """
    엑셀 업로드용 양식 다운로드 (통합 시트)
    - Promotion 칼럼: 파란색 헤더 (#4472C4)
    - PromotionProduct 칼럼: 초록색 헤더 (#70AD47)
    - 행사ID는 자동생성되므로 템플릿에 포함하지 않음
    - 유니크 키: 브랜드 + 채널명 + 행사명 + 시작일
    """

    # 통합 칼럼 정의 (Promotion + PromotionProduct)
    # Promotion 칼럼 (파란색) - 행사ID 제외
    promotion_columns = [
        '행사명', '행사유형', '시작일', '종료일', '상태',
        '브랜드', '채널명', '수수료율(%)',
        '할인분담주체', '회사분담율(%)', '채널분담율(%)',
        '행사비고'
    ]

    # PromotionProduct 칼럼 (초록색)
    product_columns = [
        '상품코드', '판매가', '행사가', '공급가', '쿠폰할인율(%)',
        '원가', '물류비', '관리비', '창고비', 'EDI비용', '잡손실',
        '예상매출액', '예상수량', '상품비고'
    ]

    all_columns = promotion_columns + product_columns

    # 샘플 데이터 (같은 행사에 여러 상품)
    sample_data = [
        {
            # Promotion 정보 (파란색)
            '행사명': '스크럽대디 1월 할인행사',
            '행사유형': '판매가할인',
            '시작일': '2026-01-01',
            '종료일': '2026-01-31',
            '상태': '예정',
            '브랜드': '스크럽대디',
            '채널명': '쿠팡',
            '수수료율(%)': 10.5,
            '할인분담주체': 'BOTH',
            '회사분담율(%)': 50.0,
            '채널분담율(%)': 50.0,
            '행사비고': '신년 프로모션',
            # PromotionProduct 정보 (초록색)
            '상품코드': 1001,
            '판매가': 15900,
            '행사가': 12900,
            '공급가': None,
            '쿠폰할인율(%)': None,
            '원가': 5000,
            '물류비': 500,
            '관리비': 300,
            '창고비': 200,
            'EDI비용': 100,
            '잡손실': 50,
            '예상매출액': 50000000,
            '예상수량': 2500,
            '상품비고': ''
        },
        {
            # 같은 행사, 다른 상품
            '행사명': '스크럽대디 1월 할인행사',
            '행사유형': '판매가할인',
            '시작일': '2026-01-01',
            '종료일': '2026-01-31',
            '상태': '예정',
            '브랜드': '스크럽대디',
            '채널명': '쿠팡',
            '수수료율(%)': 10.5,
            '할인분담주체': 'BOTH',
            '회사분담율(%)': 50.0,
            '채널분담율(%)': 50.0,
            '행사비고': '신년 프로모션',
            # PromotionProduct 정보
            '상품코드': 1002,
            '판매가': 29900,
            '행사가': 24900,
            '공급가': None,
            '쿠폰할인율(%)': None,
            '원가': 9000,
            '물류비': 700,
            '관리비': 400,
            '창고비': 300,
            'EDI비용': 150,
            '잡손실': 80,
            '예상매출액': 50000000,
            '예상수량': 2500,
            '상품비고': ''
        },
        {
            # 다른 행사
            '행사명': '프로그 2월 원매가할인',
            '행사유형': '원매가할인',
            '시작일': '2026-02-01',
            '종료일': '2026-02-28',
            '상태': '예정',
            '브랜드': '프로그',
            '채널명': '이마트',
            '수수료율(%)': None,
            '할인분담주체': 'COMPANY',
            '회사분담율(%)': 100.0,
            '채널분담율(%)': 0,
            '행사비고': '',
            # PromotionProduct 정보
            '상품코드': 2001,
            '판매가': 8900,
            '행사가': 6900,
            '공급가': 5500,
            '쿠폰할인율(%)': None,
            '원가': 3000,
            '물류비': 300,
            '관리비': 200,
            '창고비': 150,
            'EDI비용': 80,
            '잡손실': 30,
            '예상매출액': 30000000,
            '예상수량': 3000,
            '상품비고': ''
        }
    ]

    df = pd.DataFrame(sample_data, columns=all_columns)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book

        # 헤더 스타일 정의
        promotion_header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#4472C4',  # 파란색
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        product_header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#70AD47',  # 초록색
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        # 데이터 시트 (헤더 없이 데이터만 먼저 쓰기)
        df.to_excel(writer, index=False, sheet_name='행사등록', startrow=1, header=False)
        ws = writer.sheets['행사등록']

        # 헤더 직접 작성 (색상 적용)
        for col_idx, col_name in enumerate(all_columns):
            if col_name in promotion_columns:
                ws.write(0, col_idx, col_name, promotion_header_format)
            else:
                ws.write(0, col_idx, col_name, product_header_format)

        # 칼럼 너비 설정
        for i, col in enumerate(all_columns):
            if col in ['행사명', '행사비고', '상품비고']:
                ws.set_column(i, i, 25)
            elif col in ['시작일', '종료일', '행사유형']:
                ws.set_column(i, i, 15)
            else:
                ws.set_column(i, i, 12)

        # 안내 시트
        info_data = [
            ['칼럼 색상 안내', ''],
            ['파란색 헤더', '행사(Promotion) 정보 - 같은 행사는 동일한 값 입력'],
            ['초록색 헤더', '상품(PromotionProduct) 정보 - 상품별로 다른 값 입력'],
            ['', ''],
            ['유니크 키 (행사 식별)', ''],
            ['브랜드 + 채널명 + 행사명 + 시작일', '이 4개 값이 같으면 같은 행사로 인식'],
            ['', ''],
            ['행사유형 옵션', ''],
            ['판매가할인', 'ONLINE_PRICE_DISCOUNT'],
            ['쿠폰', 'ONLINE_COUPON'],
            ['판매가+쿠폰', 'ONLINE_PRICE_COUPON'],
            ['정산후보정', 'ONLINE_POST_SETTLEMENT'],
            ['원매가할인', 'OFFLINE_WHOLESALE_DISCOUNT'],
            ['기획상품', 'OFFLINE_SPECIAL_PRODUCT'],
            ['에누리', 'OFFLINE_BUNDLE_DISCOUNT'],
            ['', ''],
            ['상태 옵션', ''],
            ['예정', 'SCHEDULED'],
            ['진행중', 'ACTIVE'],
            ['완료', 'COMPLETED'],
            ['취소', 'CANCELLED'],
            ['', ''],
            ['할인분담주체 옵션', ''],
            ['COMPANY', '회사 부담'],
            ['CHANNEL', '채널 부담'],
            ['BOTH', '공동 부담'],
        ]
        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, index=False, header=False, sheet_name='안내')
        ws_info = writer.sheets['안내']
        ws_info.set_column(0, 0, 35)
        ws_info.set_column(1, 1, 45)

    output.seek(0)

    headers = {
        'Content-Disposition': 'attachment; filename="promotion_template.xlsx"'
    }

    return StreamingResponse(
        output,
        headers=headers,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    request: Request = None,
    user: CurrentUser = Depends(get_current_user)
):
    """
    엑셀 파일 업로드 및 Promotion/PromotionProduct에 UPSERT

    지원 형식:
    1. 통합 시트 ('행사등록'): Promotion + PromotionProduct 정보가 하나의 시트에 있음
       - 행사ID 자동 생성 (유니크 키: 브랜드 + 채널명 + 행사명 + 시작일)
    2. 기존 2시트 방식 ('Promotion', 'PromotionProduct'): 하위 호환성 유지
    """
    try:
        start_time = datetime.now()

        # 핸들러 초기화
        handler = PromotionExcelHandler()
        handler.validate_file(file)

        print(f"\n[행사 업로드 시작] {file.filename}")

        # 파일 읽기
        excel_file = await handler.read_file(file)

        # 시트 구조 확인 (통합 시트 vs 기존 2시트)
        df_unified = handler.read_sheet(excel_file, '행사등록', required=False)
        is_unified_format = df_unified is not None and len(df_unified) > 0

        # 매핑 테이블 로드
        handler.load_mappings(load_brand=True, load_channel=True, load_product=True)
        print(f"   매핑 테이블 로드 완료")

        promotion_records = []
        product_records = []

        if is_unified_format:
            # ========== 통합 시트 처리 ==========
            print(f"   [형식] 통합 시트 (행사등록)")
            print(f"   행사등록: {len(df_unified):,}행")

            promotion_records, product_records = handler.process_unified_sheet(
                df_unified, promotion_repo
            )
            print(f"   유효 Promotion 레코드: {len(promotion_records):,}건")
            print(f"   유효 PromotionProduct 레코드: {len(product_records):,}건")
        else:
            # ========== 기존 2시트 방식 처리 ==========
            print(f"   [형식] 기존 2시트 (Promotion, PromotionProduct)")

            df_promotion = handler.read_sheet(excel_file, 'Promotion', required=True)
            df_product = handler.read_sheet(excel_file, 'PromotionProduct', required=False)

            if df_product is None:
                print("   [안내] PromotionProduct 시트 없음 - 마스터만 처리")

            print(f"   Promotion: {len(df_promotion):,}행, PromotionProduct: {len(df_product) if df_product is not None else 0:,}행")

            promotion_records = handler.process_promotion_sheet(df_promotion)
            print(f"   유효 Promotion 레코드: {len(promotion_records):,}건")

            if df_product is not None and len(df_product) > 0:
                try:
                    product_records = handler.process_product_sheet(df_product)
                    print(f"   유효 PromotionProduct 레코드: {len(product_records):,}건")
                except Exception as e:
                    print(f"   [경고] PromotionProduct 처리 실패: {str(e)} - 스킵")

        # ========== Promotion INSERT/UPDATE ==========
        promotion_result = {'inserted': 0, 'updated': 0}
        if promotion_records:
            promotion_result = promotion_repo.bulk_insert(promotion_records)

        # ========== PromotionProduct INSERT/UPDATE ==========
        product_result = {'inserted': 0, 'updated': 0}
        if product_records:
            product_result = promotion_product_repo.bulk_insert(product_records)

        # ========== ExpectedSalesProduct 자동 생성 (PROMOTION 타입) ==========
        expected_sales_result = {'inserted': 0, 'updated': 0}

        if product_records:
            try:
                expected_sales_records = _build_expected_sales_records(
                    promotion_records, product_records
                )
                print(f"   ExpectedSalesProduct 레코드 생성: {len(expected_sales_records):,}건")

                if expected_sales_records:
                    expected_sales_result = expected_sales_repo.bulk_insert(expected_sales_records)
                    print(f"   ExpectedSalesProduct: INSERT {expected_sales_result['inserted']:,}건, UPDATE {expected_sales_result['updated']:,}건")
            except Exception as e:
                print(f"   [경고] ExpectedSalesProduct 자동 생성 실패: {str(e)} - 스킵")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 매핑 실패 정보
        warnings = handler.get_unmapped_summary()

        # 활동 로그
        if user and request:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="Promotion",
                details={
                    "action": "EXCEL_UPLOAD",
                    "filename": file.filename,
                    "format": "unified" if is_unified_format else "legacy",
                    "promotion_inserted": promotion_result['inserted'],
                    "promotion_updated": promotion_result['updated'],
                    "product_inserted": product_result['inserted'],
                    "product_updated": product_result['updated'],
                    "expected_sales_inserted": expected_sales_result['inserted'],
                    "expected_sales_updated": expected_sales_result['updated'],
                    "unmapped_brands": warnings['unmapped_brands']['count'],
                    "unmapped_products": warnings['unmapped_products']['count'],
                    "duration_seconds": duration
                },
                ip_address=get_client_ip(request)
            )

        print(f"\n{'='*60}")
        print(f"업로드 완료:")
        print(f"   Promotion: INSERT {promotion_result['inserted']:,}건, UPDATE {promotion_result['updated']:,}건")
        print(f"   PromotionProduct: INSERT {product_result['inserted']:,}건, UPDATE {product_result['updated']:,}건")
        print(f"   ExpectedSalesProduct: INSERT {expected_sales_result['inserted']:,}건, UPDATE {expected_sales_result['updated']:,}건")
        if warnings['unmapped_brands']['items']:
            print(f"   [경고] 매핑 안 된 브랜드: {warnings['unmapped_brands']['items']}")
        if warnings['unmapped_channels']['items']:
            print(f"   [경고] 매핑 안 된 채널: {warnings['unmapped_channels']['items']}")
        if warnings['unmapped_products']['items']:
            print(f"   [경고] 매핑 안 된 상품코드: {warnings['unmapped_products']['items']}")
        print(f"{'='*60}")

        return {
            "message": "업로드 완료",
            "success": True,
            "format": "unified" if is_unified_format else "legacy",
            "promotion": {
                "valid_records": len(promotion_records),
                "inserted": promotion_result['inserted'],
                "updated": promotion_result['updated']
            },
            "promotion_product": {
                "valid_records": len(product_records),
                "inserted": product_result['inserted'],
                "updated": product_result['updated']
            },
            "expected_sales_product": {
                "inserted": expected_sales_result['inserted'],
                "updated": expected_sales_result['updated']
            },
            "warnings": warnings,
            "duration_seconds": duration
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"업로드 실패: {str(e)}")


def _build_expected_sales_records(
    promotion_records: List[Dict[str, Any]],
    product_records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Promotion + PromotionProduct 데이터로 ExpectedSalesProduct 레코드 생성

    Args:
        promotion_records: Promotion 레코드 리스트
        product_records: PromotionProduct 레코드 리스트

    Returns:
        ExpectedSalesProduct 레코드 리스트
    """
    # Promotion 정보를 딕셔너리로 변환 (PromotionID -> Promotion 정보)
    promotion_map = {}
    for promo in promotion_records:
        promotion_map[promo['PromotionID']] = promo

    expected_records = []

    for product in product_records:
        promotion_id = product['PromotionID']
        promotion = promotion_map.get(promotion_id)

        if not promotion:
            print(f"   [경고] PromotionID '{promotion_id}' 에 해당하는 Promotion 정보 없음 - 스킵")
            continue

        # StartDate에서 Year, Month 추출
        start_date = promotion.get('StartDate')
        if not start_date:
            print(f"   [경고] PromotionID '{promotion_id}' StartDate 없음 - 스킵")
            continue

        # start_date가 문자열인 경우 파싱
        if isinstance(start_date, str):
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                print(f"   [경고] PromotionID '{promotion_id}' StartDate 파싱 실패: {start_date} - 스킵")
                continue

        year = start_date.year
        month = start_date.month

        # ExpectedSalesProduct 레코드 생성
        expected_record = {
            'Year': year,
            'Month': month,
            'BrandID': promotion['BrandID'],
            'ChannelID': promotion.get('ChannelID'),
            'ProductID': product['ProductID'],
            'SalesType': 'PROMOTION',
            'PromotionID': promotion_id,
            'PromotionProductID': None,  # 아직 PromotionProductID가 없음 (INSERT 후 생성됨)
            'ExpectedAmount': product.get('ExpectedSalesAmount'),
            'ExpectedQuantity': product.get('ExpectedQuantity')
        }

        # 필수 값 체크
        if not expected_record['ChannelID']:
            print(f"   [경고] PromotionID '{promotion_id}' ChannelID 없음 - 스킵")
            continue

        expected_records.append(expected_record)

    return expected_records
