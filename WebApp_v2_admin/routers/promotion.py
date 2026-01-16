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
    """
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, "엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.")

        start_time = datetime.now()
        print(f"\n[행사 업로드 시작] {file.filename}")

        contents = await file.read()
        excel_file = io.BytesIO(contents)

        # 시트 읽기
        try:
            df_promotion = pd.read_excel(excel_file, sheet_name='Promotion')
            excel_file.seek(0)
        except Exception:
            raise HTTPException(400, "Promotion 시트를 찾을 수 없습니다.")

        try:
            df_product = pd.read_excel(excel_file, sheet_name='PromotionProduct')
        except Exception:
            df_product = None
            print("   [안내] PromotionProduct 시트 없음 - 마스터만 처리")

        print(f"   Promotion: {len(df_promotion):,}행, PromotionProduct: {len(df_product) if df_product is not None else 0:,}행")

        # 한글 칼럼명 -> 영문 칼럼명 매핑
        promotion_col_map = {
            '행사ID': 'PROMOTION_ID', '행사명': 'PROMOTION_NAME', '행사유형': 'PROMOTION_TYPE',
            '시작일': 'START_DATE', '종료일': 'END_DATE', '상태': 'STATUS',
            '브랜드': 'BRAND', '채널명': 'CHANNEL_NAME', '수수료율(%)': 'COMMISSION_RATE',
            '할인분담주체': 'DISCOUNT_OWNER', '회사분담율(%)': 'COMPANY_SHARE', '채널분담율(%)': 'CHANNEL_SHARE',
            '목표매출액': 'TARGET_SALES_AMOUNT', '목표수량': 'TARGET_QUANTITY', '비고': 'NOTES'
        }
        product_col_map = {
            '행사ID': 'PROMOTION_ID', '상품코드': 'UNIQUECODE', '상품명': 'PRODUCT_NAME',
            '판매가': 'SELLING_PRICE', '행사가': 'PROMOTION_PRICE', '공급가': 'SUPPLY_PRICE', 
            '쿠폰할인율(%)': 'COUPON_DISCOUNT_RATE',
            '원가': 'UNIT_COST', '물류비': 'LOGISTICS_COST', '관리비': 'MANAGEMENT_COST', 
            '창고비': 'WAREHOUSE_COST', 'EDI비용': 'EDI_COST', '잡손실': 'MIS_COST',
            '목표매출액': 'TARGET_SALES_AMOUNT', '목표수량': 'TARGET_QUANTITY', '비고': 'NOTES'
        }

        # 컬럼명 변환 (한글 -> 영문)
        df_promotion.columns = [promotion_col_map.get(col.strip(), col.upper().strip().replace(' ', '_')) for col in df_promotion.columns]
        if df_product is not None:
            df_product.columns = [product_col_map.get(col.strip(), col.upper().strip().replace(' ', '_')) for col in df_product.columns]

        # 필수 컬럼 확인 (Promotion)
        required_promotion_cols = ['PROMOTION_ID', 'PROMOTION_NAME', 'START_DATE', 'END_DATE', 'BRAND']
        missing_cols = [col for col in required_promotion_cols if col not in df_promotion.columns]
        if missing_cols:
            raise HTTPException(400, f"Promotion 시트 필수 컬럼 누락: {', '.join(missing_cols)}")

        # 매핑 테이블 로드
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT Name, BrandID FROM [dbo].[Brand]")
            brand_map = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT Name, ChannelID FROM [dbo].[Channel]")
            channel_map = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT Uniquecode, ProductID FROM [dbo].[Product]")
            product_map = {row[0]: row[1] for row in cursor.fetchall()}

        print(f"   매핑 테이블 로드 완료 (Brand: {len(brand_map)}, Channel: {len(channel_map)}, Product: {len(product_map)})")

        # 매핑 실패 추적
        unmapped_brands = set()
        unmapped_channels = set()
        unmapped_products = set()

        # ========== Promotion 처리 ==========
        promotion_records = []
        for idx, row in df_promotion.iterrows():
            brand_name = str(row['BRAND']).strip() if pd.notna(row.get('BRAND')) else None
            brand_id = brand_map.get(brand_name)

            if brand_name and brand_id is None:
                unmapped_brands.add(brand_name)
                continue

            if brand_id is None:
                continue

            # 채널명으로 ChannelID 매핑
            channel_name = str(row['CHANNEL_NAME']).strip() if pd.notna(row.get('CHANNEL_NAME')) else None
            channel_id = None
            if channel_name:
                channel_id = channel_map.get(channel_name)
                if channel_id is None:
                    unmapped_channels.add(channel_name)

            # PromotionType 변환 (한글 -> 영문)
            promotion_type = row.get('PROMOTION_TYPE')
            if pd.notna(promotion_type):
                promotion_type = str(promotion_type).strip()
                promotion_type = PROMOTION_TYPE_REVERSE_MAP.get(promotion_type, promotion_type)

            # Status 변환 (한글 -> 영문)
            status = row.get('STATUS', 'SCHEDULED')
            if pd.notna(status):
                status = str(status).strip()
                status = STATUS_REVERSE_MAP.get(status, status)

            promotion_records.append({
                'PromotionID': str(row['PROMOTION_ID']).strip(),
                'PromotionName': str(row['PROMOTION_NAME']).strip(),
                'PromotionType': promotion_type,
                'StartDate': pd.to_datetime(row['START_DATE']).strftime('%Y-%m-%d') if pd.notna(row['START_DATE']) else None,
                'EndDate': pd.to_datetime(row['END_DATE']).strftime('%Y-%m-%d') if pd.notna(row['END_DATE']) else None,
                'Status': status,
                'BrandID': brand_id,
                'ChannelID': channel_id,
                'ChannelName': channel_name,
                'CommissionRate': float(row['COMMISSION_RATE']) if pd.notna(row.get('COMMISSION_RATE')) else None,
                'DiscountOwner': str(row['DISCOUNT_OWNER']).strip() if pd.notna(row.get('DISCOUNT_OWNER')) else None,
                'CompanyShare': float(row['COMPANY_SHARE']) if pd.notna(row.get('COMPANY_SHARE')) else None,
                'ChannelShare': float(row['CHANNEL_SHARE']) if pd.notna(row.get('CHANNEL_SHARE')) else None,
                'TargetSalesAmount': float(row['TARGET_SALES_AMOUNT']) if pd.notna(row.get('TARGET_SALES_AMOUNT')) else None,
                'TargetQuantity': int(row['TARGET_QUANTITY']) if pd.notna(row.get('TARGET_QUANTITY')) else None,
                'Notes': str(row['NOTES']).strip() if pd.notna(row.get('NOTES')) else None
            })

        print(f"   유효 Promotion 레코드: {len(promotion_records):,}건")

        # Promotion INSERT/UPDATE
        promotion_result = promotion_repo.bulk_insert(promotion_records)

        # ========== PromotionProduct 처리 ==========
        product_result = {'inserted': 0, 'updated': 0}

        if df_product is not None and len(df_product) > 0:
            required_product_cols = ['PROMOTION_ID', 'UNIQUECODE']
            missing_cols = [col for col in required_product_cols if col not in df_product.columns]
            if missing_cols:
                print(f"   [경고] PromotionProduct 필수 컬럼 누락: {', '.join(missing_cols)} - 스킵")
            else:
                product_records = []
                for idx, row in df_product.iterrows():
                    uniquecode = int(row['UNIQUECODE']) if pd.notna(row['UNIQUECODE']) else None
                    product_id = product_map.get(uniquecode)

                    if uniquecode and product_id is None:
                        unmapped_products.add(uniquecode)
                        continue

                    if product_id is None:
                        continue

                    product_records.append({
                        'PromotionID': str(row['PROMOTION_ID']).strip(),
                        'ProductID': product_id,
                        'Uniquecode': uniquecode,
                        'SellingPrice': float(row['SELLING_PRICE']) if pd.notna(row.get('SELLING_PRICE')) else None,
                        'PromotionPrice': float(row['PROMOTION_PRICE']) if pd.notna(row.get('PROMOTION_PRICE')) else None,
                        'SupplyPrice': float(row['SUPPLY_PRICE']) if pd.notna(row.get('SUPPLY_PRICE')) else None,
                        'CouponDiscountRate': float(row['COUPON_DISCOUNT_RATE']) if pd.notna(row.get('COUPON_DISCOUNT_RATE')) else None,
                        'UnitCost': float(row['UNIT_COST']) if pd.notna(row.get('UNIT_COST')) else None,
                        'LogisticsCost': float(row['LOGISTICS_COST']) if pd.notna(row.get('LOGISTICS_COST')) else None,
                        'ManagementCost': float(row['MANAGEMENT_COST']) if pd.notna(row.get('MANAGEMENT_COST')) else None,
                        'WarehouseCost': float(row['WAREHOUSE_COST']) if pd.notna(row.get('WAREHOUSE_COST')) else None,
                        'EDICost': float(row['EDI_COST']) if pd.notna(row.get('EDI_COST')) else None,
                        'MisCost': float(row['MIS_COST']) if pd.notna(row.get('MIS_COST')) else None,
                        'TargetSalesAmount': float(row['TARGET_SALES_AMOUNT']) if pd.notna(row.get('TARGET_SALES_AMOUNT')) else None,
                        'TargetQuantity': int(row['TARGET_QUANTITY']) if pd.notna(row.get('TARGET_QUANTITY')) else None,
                        'Notes': str(row['NOTES']).strip() if pd.notna(row.get('NOTES')) else None
                    })

                print(f"   유효 PromotionProduct 레코드: {len(product_records):,}건")

                if product_records:
                    product_result = promotion_product_repo.bulk_insert(product_records)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

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
                    "unmapped_brands": len(unmapped_brands),
                    "unmapped_products": len(unmapped_products),
                    "duration_seconds": duration
                },
                ip_address=get_client_ip(request)
            )

        print(f"\n{'='*60}")
        print(f"업로드 완료:")
        print(f"   Promotion: INSERT {promotion_result['inserted']:,}건, UPDATE {promotion_result['updated']:,}건")
        print(f"   PromotionProduct: INSERT {product_result['inserted']:,}건, UPDATE {product_result['updated']:,}건")
        if unmapped_brands:
            print(f"   [경고] 매핑 안 된 브랜드: {sorted(unmapped_brands)}")
        if unmapped_channels:
            print(f"   [경고] 매핑 안 된 채널: {sorted(unmapped_channels)}")
        if unmapped_products:
            print(f"   [경고] 매핑 안 된 상품코드: {sorted(unmapped_products)}")
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
            "warnings": {
                "unmapped_brands": {
                    "count": len(unmapped_brands),
                    "items": sorted(list(unmapped_brands))
                },
                "unmapped_channels": {
                    "count": len(unmapped_channels),
                    "items": sorted(list(unmapped_channels))
                },
                "unmapped_products": {
                    "count": len(unmapped_products),
                    "items": sorted(list(unmapped_products))
                }
            },
            "duration_seconds": duration
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"업로드 실패: {str(e)}")
