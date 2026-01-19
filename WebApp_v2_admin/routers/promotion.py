"""
Promotion Router
- 행사 관리 API 엔드포인트
- Promotion(마스터) + PromotionProduct(디테일) CRUD
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
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
from repositories import ActivityLogRepository
from core import get_db_cursor
from core.dependencies import get_current_user, get_client_ip, CurrentUser
from utils.excel import PromotionExcelHandler

router = APIRouter(prefix="/api/promotions", tags=["Promotions"])

# Repository 인스턴스
promotion_repo = PromotionRepository()
promotion_product_repo = PromotionProductRepository()
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
    """행사 삭제 (연관 상품도 함께 삭제)"""
    try:
        if not promotion_repo.exists(promotion_id):
            raise HTTPException(404, "행사를 찾을 수 없습니다")

        # 먼저 연관 상품 삭제
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
                details={"deleted_products": deleted_products},
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다", "deleted_products": deleted_products}
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
        deleted_promotions = 0

        for promotion_id in request_body.ids:
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
                    "deleted_products": total_deleted_products
                },
                ip_address=get_client_ip(request)
            )

        return {
            "message": "삭제되었습니다",
            "deleted_count": deleted_promotions,
            "deleted_products": total_deleted_products
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
    """엑셀 업로드용 양식 다운로드 (2개 시트: Promotion, PromotionProduct)"""

    # Promotion 시트 (마스터) - DB 테이블의 모든 칼럼 포함 (자동생성 칼럼 제외)
    promotion_columns = [
        '행사ID', '행사명', '행사유형',
        '시작일', '종료일', '상태',
        '브랜드', '채널명', '수수료율(%)',
        '할인분담주체', '회사분담율(%)', '채널분담율(%)',
        '목표매출액', '목표수량', '비고'
    ]

    promotion_sample = [
        {
            '행사ID': 'SDPD260101',
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
            '목표매출액': 100000000,
            '목표수량': 5000,
            '비고': '신년 프로모션'
        },
        {
            '행사ID': 'PGWD260201',
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
            '목표매출액': 50000000,
            '목표수량': 2000,
            '비고': ''
        }
    ]

    # PromotionProduct 시트 (디테일)
    product_columns = [
        '행사ID', '상품코드', '상품명',
        '판매가', '행사가', '공급가', '쿠폰할인율(%)',
        '원가', '물류비', '관리비', '창고비', 'EDI비용', '잡손실',
        '목표매출액', '목표수량', '비고'
    ]

    product_sample = [
        {
            '행사ID': 'SDPD260201',
            '상품코드': 1001,
            '상품명': '스크럽대디 스폰지 3입',
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
            '목표매출액': 50000000,
            '목표수량': 2500,
            '비고': ''
        },
        {
            '행사ID': 'SDPD260201',
            '상품코드': 1002,
            '상품명': '스크럽대디 스폰지 6입',
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
            '목표매출액': 50000000,
            '목표수량': 2500,
            '비고': ''
        }
    ]

    df_promotion = pd.DataFrame(promotion_sample, columns=promotion_columns)
    df_product = pd.DataFrame(product_sample, columns=product_columns)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Promotion 시트
        df_promotion.to_excel(writer, index=False, sheet_name='Promotion')
        ws_promotion = writer.sheets['Promotion']
        for i, col in enumerate(promotion_columns):
            ws_promotion.set_column(i, i, 20)

        # PromotionProduct 시트
        df_product.to_excel(writer, index=False, sheet_name='PromotionProduct')
        ws_product = writer.sheets['PromotionProduct']
        for i, col in enumerate(product_columns):
            ws_product.set_column(i, i, 18)

        # 안내 시트
        info_data = [
            ['시트명', '설명'],
            ['Promotion', '행사 마스터 정보 (필수)'],
            ['PromotionProduct', '행사별 상품 정보 (선택)'],
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
        ws_info.set_column(0, 0, 25)
        ws_info.set_column(1, 1, 30)

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
    - 2개 시트: Promotion, PromotionProduct
    - 행사ID 미입력 시 자동 생성 (브랜드코드+유형코드+년월+순번)
    """
    try:
        start_time = datetime.now()

        # 핸들러 초기화
        handler = PromotionExcelHandler()
        handler.validate_file(file)

        print(f"\n[행사 업로드 시작] {file.filename}")

        # 파일 읽기
        excel_file = await handler.read_file(file)

        # 시트 읽기
        df_promotion = handler.read_sheet(excel_file, 'Promotion', required=True)
        df_product = handler.read_sheet(excel_file, 'PromotionProduct', required=False)

        if df_product is None:
            print("   [안내] PromotionProduct 시트 없음 - 마스터만 처리")

        print(f"   Promotion: {len(df_promotion):,}행, PromotionProduct: {len(df_product) if df_product is not None else 0:,}행")

        # 매핑 테이블 로드
        handler.load_mappings(load_brand=True, load_channel=True, load_product=True)
        print(f"   매핑 테이블 로드 완료")

        # ========== Promotion 처리 ==========
        promotion_records = handler.process_promotion_sheet(df_promotion)
        print(f"   유효 Promotion 레코드: {len(promotion_records):,}건")

        # Promotion INSERT/UPDATE
        promotion_result = promotion_repo.bulk_insert(promotion_records)

        # ========== PromotionProduct 처리 ==========
        product_result = {'inserted': 0, 'updated': 0}

        if df_product is not None and len(df_product) > 0:
            try:
                product_records = handler.process_product_sheet(df_product)
                print(f"   유효 PromotionProduct 레코드: {len(product_records):,}건")

                if product_records:
                    product_result = promotion_product_repo.bulk_insert(product_records)
            except Exception as e:
                print(f"   [경고] PromotionProduct 처리 실패: {str(e)} - 스킵")

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
                    "promotion_inserted": promotion_result['inserted'],
                    "promotion_updated": promotion_result['updated'],
                    "product_inserted": product_result['inserted'],
                    "product_updated": product_result['updated'],
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
            "promotion": {
                "total_rows": len(df_promotion),
                "valid_records": len(promotion_records),
                "inserted": promotion_result['inserted'],
                "updated": promotion_result['updated']
            },
            "promotion_product": {
                "total_rows": len(df_product) if df_product is not None else 0,
                "inserted": product_result['inserted'],
                "updated": product_result['updated']
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
