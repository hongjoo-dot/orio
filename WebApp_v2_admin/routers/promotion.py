"""
Promotion (행사 관리) Router
- 행사 (Promotion) CRUD + 통합 엑셀
- 행사 상품 (PromotionProduct) CRUD
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Any
import pandas as pd
import io
from datetime import datetime
from repositories.promotion_repository import PromotionRepository
from repositories.promotion_product_repository import PromotionProductRepository
from repositories import BrandRepository, ChannelRepository, ProductRepository, ActivityLogRepository
from core import get_db_cursor
from core.dependencies import get_client_ip, CurrentUser
from core import log_activity, log_delete, log_bulk_delete, require_permission
from core.models import BulkDeleteAnyRequest as BulkDeleteRequest
from utils.helpers import format_time_value


# ========== Repository 인스턴스 ==========
promotion_repo = PromotionRepository()
promotion_product_repo = PromotionProductRepository()
brand_repo = BrandRepository()
channel_repo = ChannelRepository()
product_repo = ProductRepository()
activity_log_repo = ActivityLogRepository()


# ========== Pydantic Models — Promotion ==========

class PromotionCreate(BaseModel):
    PromotionName: str
    PromotionType: str
    StartDate: str
    StartTime: Optional[str] = "00:00:00"
    EndDate: str
    EndTime: Optional[str] = "23:59:59"
    BrandID: int
    BrandName: Optional[str] = None
    ChannelID: int
    ChannelName: Optional[str] = None
    CommissionRate: Optional[float] = None
    DiscountOwner: Optional[str] = None
    CompanyShare: Optional[float] = None
    ChannelShare: Optional[float] = None
    ExpectedSalesAmount: Optional[float] = None
    ExpectedQuantity: Optional[int] = None
    Notes: Optional[str] = None


class PromotionUpdate(BaseModel):
    PromotionName: Optional[str] = None
    EndDate: Optional[str] = None
    EndTime: Optional[str] = None
    StartTime: Optional[str] = None
    Status: Optional[str] = None
    CommissionRate: Optional[float] = None
    DiscountOwner: Optional[str] = None
    CompanyShare: Optional[float] = None
    ChannelShare: Optional[float] = None
    ExpectedSalesAmount: Optional[float] = None
    ExpectedQuantity: Optional[int] = None
    Notes: Optional[str] = None


# ========== Pydantic Models — PromotionProduct ==========

class PromotionProductCreate(BaseModel):
    PromotionID: str
    UniqueCode: str
    ProductName: Optional[str] = None
    SellingPrice: Optional[float] = None
    PromotionPrice: Optional[float] = None
    SupplyPrice: Optional[float] = None
    CouponDiscountRate: Optional[float] = None
    UnitCost: Optional[float] = None
    LogisticsCost: Optional[float] = None
    ManagementCost: Optional[float] = None
    WarehouseCost: Optional[float] = None
    EDICost: Optional[float] = None
    MisCost: Optional[float] = None
    ExpectedSalesAmount: Optional[float] = None
    ExpectedQuantity: Optional[int] = None
    Notes: Optional[str] = None


class PromotionProductUpdate(BaseModel):
    ProductName: Optional[str] = None
    SellingPrice: Optional[float] = None
    PromotionPrice: Optional[float] = None
    SupplyPrice: Optional[float] = None
    CouponDiscountRate: Optional[float] = None
    UnitCost: Optional[float] = None
    LogisticsCost: Optional[float] = None
    ManagementCost: Optional[float] = None
    WarehouseCost: Optional[float] = None
    EDICost: Optional[float] = None
    MisCost: Optional[float] = None
    ExpectedSalesAmount: Optional[float] = None
    ExpectedQuantity: Optional[int] = None
    Notes: Optional[str] = None


class PromotionProductBulkUpdateItem(BaseModel):
    PromotionProductID: int
    PromotionPrice: Optional[float] = None
    ExpectedSalesAmount: Optional[float] = None
    ExpectedQuantity: Optional[int] = None
    Notes: Optional[str] = None


class PromotionProductBulkUpdateRequest(BaseModel):
    items: List[PromotionProductBulkUpdateItem]


# ==========================================================
#  Promotion Router (행사 목록 CRUD + 통합 엑셀)
# ==========================================================
router = APIRouter(prefix="/api/promotions", tags=["Promotion"])


# ========== 행사 목록 조회 ==========

@router.get("")
async def get_promotion_list(
    page: int = 1,
    limit: int = 20,
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    promotion_type: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "DESC",
    user: CurrentUser = Depends(require_permission("Promotion", "READ"))
):
    """행사 목록 조회"""
    try:
        ALLOWED_SORT = {
            "PromotionID": "p.PromotionID",
            "PromotionName": "p.PromotionName",
            "PromotionType": "p.PromotionType",
            "StartDate": "p.StartDate",
            "EndDate": "p.EndDate",
            "BrandName": "b.Name",
            "ChannelName": "ch.Name",
            "Status": "p.Status",
            "CommissionRate": "p.CommissionRate",
            "DiscountBurden": "p.DiscountOwner",
            "ExpectedSalesAmount": "p.ExpectedSalesAmount",
            "ExpectedQuantity": "p.ExpectedQuantity",
        }
        order_by = ALLOWED_SORT.get(sort_by, "p.StartDate")
        order_dir = sort_dir if sort_dir in ("ASC", "DESC") else "DESC"

        filters = {}
        if year_month:
            filters['year_month'] = year_month
        if brand_id:
            filters['brand_id'] = brand_id
        if channel_id:
            filters['channel_id'] = channel_id
        if promotion_type:
            filters['promotion_type'] = promotion_type
        if status:
            filters['status'] = status

        result = promotion_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by=order_by,
            order_dir=order_dir
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"행사 목록 조회 실패: {str(e)}")


@router.get("/year-months")
async def get_promotion_year_months(user: CurrentUser = Depends(require_permission("Promotion", "READ"))):
    """행사 년월 목록 조회"""
    try:
        year_months = promotion_repo.get_year_months()
        return {"year_months": year_months}
    except Exception as e:
        raise HTTPException(500, f"년월 목록 조회 실패: {str(e)}")


@router.get("/promotion-types")
async def get_promotion_types(user: CurrentUser = Depends(require_permission("Promotion", "READ"))):
    """행사유형 목록 조회 (PromotionType 테이블에서 DisplayName)"""
    try:
        promotion_types = promotion_repo.get_promotion_type_display_names()
        return {"promotion_types": promotion_types}
    except Exception as e:
        raise HTTPException(500, f"행사유형 목록 조회 실패: {str(e)}")


@router.get("/statuses")
async def get_promotion_statuses(user: CurrentUser = Depends(require_permission("Promotion", "READ"))):
    """행사 상태 목록 조회 (고정값)"""
    try:
        statuses = promotion_repo.get_statuses()
        return {"statuses": statuses}
    except Exception as e:
        raise HTTPException(500, f"상태 목록 조회 실패: {str(e)}")


# ========== 마스터 패널용 요약 목록 ==========

@router.get("/master-summary")
async def get_promotion_master_summary(
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    promotion_type: Optional[str] = None,
    status: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Promotion", "READ"))
):
    """마스터 패널용 비정기 목록 + 상품 수 조회"""
    try:
        filters = {}
        if year_month:
            filters['year_month'] = year_month
        if brand_id:
            filters['brand_id'] = brand_id
        if channel_id:
            filters['channel_id'] = channel_id
        if promotion_type:
            filters['promotion_type'] = promotion_type
        if status:
            filters['status'] = status

        data = promotion_repo.get_master_summary(filters)
        return {"data": data, "total": len(data)}
    except Exception as e:
        raise HTTPException(500, f"비정기 목록 조회 실패: {str(e)}")


# ========== 통합 엑셀 다운로드 ==========

@router.get("/download")
async def download_promotions(
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    promotion_type: Optional[str] = None,
    status: Optional[str] = None,
    ids: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Promotion", "EXPORT"))
):
    """행사 + 행사 상품 통합 엑셀 다운로드"""
    try:
        promotions = []
        products = []

        # 데이터 조회
        if ids:
            # PromotionID 리스트로 조회
            id_list = [id.strip() for id in ids.split(',') if id.strip()]
            promotions = promotion_repo.get_by_ids(id_list)
            products = promotion_product_repo.get_by_promotion_ids(id_list)
        elif year_month or brand_id or channel_id or promotion_type or status:
            # 필터 조건으로 조회
            filters = {}
            if year_month:
                filters['year_month'] = year_month
            if brand_id:
                filters['brand_id'] = brand_id
            if channel_id:
                filters['channel_id'] = channel_id
            if promotion_type:
                filters['promotion_type'] = promotion_type
            if status:
                filters['status'] = status

            result = promotion_repo.get_list(page=1, limit=100000, filters=filters)
            promotions = result['data']

            if promotions:
                promo_ids = [p['PromotionID'] for p in promotions]
                products = promotion_product_repo.get_by_promotion_ids(promo_ids)

        # 행사별 상품 매핑
        products_by_promo = {}
        for prod in products:
            pid = prod['PromotionID']
            if pid not in products_by_promo:
                products_by_promo[pid] = []
            products_by_promo[pid].append(prod)

        # 통합 행 생성 (행사 정보 + 상품 정보를 1행으로 합침)
        rows = []
        for promo in promotions:
            promo_products = products_by_promo.get(promo['PromotionID'], [])
            if promo_products:
                for prod in promo_products:
                    rows.append({
                        '행사ID': promo['PromotionID'],
                        '행사명': promo['PromotionName'],
                        '행사유형': promo['PromotionType'],
                        '시작일': promo['StartDate'],
                        '시작시간': promo['StartTime'],
                        '종료일': promo['EndDate'],
                        '종료시간': promo['EndTime'],
                        '브랜드명': promo['BrandName'],
                        '채널명': promo['ChannelName'],
                        '수수료율': promo['CommissionRate'],
                        '할인부담': promo['DiscountOwner'],
                        '자사분담율': promo['CompanyShare'],
                        '채널분담율': promo['ChannelShare'],
                        '비고(행사)': promo['Notes'],
                        '상품ID': prod['PromotionProductID'],
                        '상품코드': prod['UniqueCode'],
                        '판매가': prod['SellingPrice'],
                        '행사가': prod['PromotionPrice'],
                        '공급가': prod['SupplyPrice'],
                        '쿠폰할인율': prod['CouponDiscountRate'],
                        '원가': prod['UnitCost'],
                        '물류비': prod['LogisticsCost'],
                        '관리비': prod['ManagementCost'],
                        '창고비': prod['WarehouseCost'],
                        'EDI비': prod['EDICost'],
                        '기타비': prod['MisCost'],
                        '예상매출(상품)': prod['ExpectedSalesAmount'],
                        '예상수량(상품)': prod['ExpectedQuantity'],
                        '비고(상품)': prod['Notes'],
                    })
            else:
                # 상품이 없는 행사도 출력 (상품 컬럼은 빈 값)
                rows.append({
                    '행사ID': promo['PromotionID'],
                    '행사명': promo['PromotionName'],
                    '행사유형': promo['PromotionType'],
                    '시작일': promo['StartDate'],
                    '시작시간': promo['StartTime'],
                    '종료일': promo['EndDate'],
                    '종료시간': promo['EndTime'],
                    '브랜드명': promo['BrandName'],
                    '채널명': promo['ChannelName'],
                    '수수료율': promo['CommissionRate'],
                    '할인부담': promo['DiscountOwner'],
                    '자사분담율': promo['CompanyShare'],
                    '채널분담율': promo['ChannelShare'],
                    '비고(행사)': promo['Notes'],
                    '상품ID': None,
                    '상품코드': None,
                    '판매가': None,
                    '행사가': None,
                    '공급가': None,
                    '쿠폰할인율': None,
                    '원가': None,
                    '물류비': None,
                    '관리비': None,
                    '창고비': None,
                    'EDI비': None,
                    '기타비': None,
                    '예상매출(상품)': None,
                    '예상수량(상품)': None,
                    '비고(상품)': None,
                })

        # 컬럼 정의 (순서 중요)
        export_columns = [
            '행사ID', '행사명', '행사유형', '시작일', '시작시간', '종료일', '종료시간',
            '브랜드명', '채널명', '수수료율', '할인부담', '자사분담율', '채널분담율',
            '비고(행사)',
            '상품ID', '상품코드', '판매가', '행사가', '공급가', '쿠폰할인율',
            '원가', '물류비', '관리비', '창고비', 'EDI비', '기타비',
            '예상매출(상품)', '예상수량(상품)', '비고(상품)'
        ]

        # ID 컬럼 인덱스 (빨간색)
        promo_id_col_idx = 0   # 행사ID
        product_id_col_idx = 14  # 상품ID
        id_column_indices = [promo_id_col_idx, product_id_col_idx]

        # 수정 불가 (복합키) 컬럼 인덱스 (검정색)
        # 행사명(1), 행사유형(2), 시작일(3), 브랜드명(7), 채널명(8), 상품코드(15)
        readonly_columns = [1, 2, 3, 7, 8, 15]

        if not rows:
            df = pd.DataFrame(columns=export_columns)
        else:
            df = pd.DataFrame(rows, columns=export_columns)

        # 안내 시트
        guide_data = [
            ['[행사 관리 통합 업로드 안내]', ''],
            ['', ''],
            ['■ 업로드 방식', ''],
            ['행사ID가 있는 행', '행사ID 기준으로 해당 행사를 수정합니다.'],
            ['행사ID가 없는 행', '행사명+행사유형+시작일+브랜드명+채널명 조합으로 그룹핑하여 신규 등록합니다.'],
            ['상품ID가 있는 행', '상품ID 기준으로 해당 상품을 수정합니다.'],
            ['상품ID가 없는 행', '해당 행사에 신규 상품으로 등록합니다.'],
            ['', ''],
            ['■ 행사ID 자동 생성 규칙', ''],
            ['형식', 'BrandCode(2자리) + TypeCode(2자리) + YYMM(4자리) + 순번(2자리)'],
            ['예시', 'OREN250101 (오리온 + 에누리 + 25년01월 + 01번)'],
            ['', ''],
            ['■ 컬럼 설명', ''],
            ['행사ID (빨간색)', '수정할 행사 식별용 (비워두면 신규 등록)'],
            ['행사명', '행사 이름'],
            ['행사유형 (검정)', '행사유형 목록 참조 (수정 불가)'],
            ['시작일 (검정)', 'YYYY-MM-DD 형식 (수정 불가)'],
            ['시작시간', 'HH:MM:SS 형식 (기본값: 00:00:00)'],
            ['종료일', 'YYYY-MM-DD 형식'],
            ['종료시간', 'HH:MM:SS 형식 (기본값: 00:00:00)'],
            ['브랜드명 (검정)', 'Brand 테이블에 등록된 브랜드명 (수정 불가)'],
            ['채널명 (검정)', 'Channel 테이블에 등록된 채널명 (수정 불가)'],
            ['수수료율', '숫자 (예: 15.5)'],
            ['할인부담', 'COMPANY / CHANNEL / BOTH'],
            ['자사분담율', '숫자 (예: 50.0)'],
            ['채널분담율', '숫자 (예: 50.0)'],
            ['비고(행사)', '메모'],
            ['상품ID (빨간색)', '수정할 상품 식별용 (비워두면 신규 등록)'],
            ['상품코드 (검정)', 'Product 테이블에 등록된 상품코드 (수정 불가)'],
            ['판매가~기타비', '가격/비용 정보'],
            ['예상매출(상품)', '숫자'],
            ['예상수량(상품)', '숫자'],
            ['비고(상품)', '메모'],
            ['', ''],
            ['■ 주의사항', ''],
            ['1. 같은 행사의 여러 상품은 행사 정보가 동일하게 반복됩니다.', ''],
            ['2. 행사ID를 비워두면 행사명+행사유형+시작일+브랜드명+채널명으로 그룹핑됩니다.', ''],
            ['3. 검정색/빨간색 배경 컬럼은 수정해도 반영되지 않습니다.', ''],
            ['4. 브랜드명, 채널명, 상품코드, 행사유형은 반드시 DB에 등록된 값이어야 합니다.', ''],
        ]
        guide_df = pd.DataFrame(guide_data, columns=['항목', '설명'])

        # 드롭다운용 목록 조회
        channels = channel_repo.get_channel_list()
        brands = brand_repo.get_all_brands()
        channel_names = [ch['Name'] for ch in channels]
        brand_names = [br['Name'] for br in brands]
        promotion_type_display_names = promotion_repo.get_promotion_type_display_names()
        discount_owner_list = ['COMPANY', 'CHANNEL', 'BOTH']

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='행사관리')
            guide_df.to_excel(writer, index=False, sheet_name='안내')

            workbook = writer.book
            worksheet = writer.sheets['행사관리']

            # 목록 시트 생성 (드롭다운 소스용)
            list_sheet = workbook.add_worksheet('목록')
            list_sheet.hide()

            # A열: 브랜드 목록
            for i, name in enumerate(brand_names):
                list_sheet.write(i, 0, name)
            # B열: 채널 목록
            for i, name in enumerate(channel_names):
                list_sheet.write(i, 1, name)
            # C열: 행사유형 목록
            for i, name in enumerate(promotion_type_display_names):
                list_sheet.write(i, 2, name)
            # D열: 할인부담 목록
            for i, name in enumerate(discount_owner_list):
                list_sheet.write(i, 3, name)

            # 드롭다운 적용 범위
            max_row = max(len(df) + 100, 1000)

            # 브랜드명 드롭다운 (인덱스 7)
            if brand_names:
                worksheet.data_validation(1, 7, max_row, 7, {
                    'validate': 'list',
                    'source': f'=목록!$A$1:$A${len(brand_names)}',
                    'input_message': '브랜드를 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 채널명 드롭다운 (인덱스 8)
            if channel_names:
                worksheet.data_validation(1, 8, max_row, 8, {
                    'validate': 'list',
                    'source': f'=목록!$B$1:$B${len(channel_names)}',
                    'input_message': '채널을 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 행사유형 드롭다운 (인덱스 2)
            if promotion_type_display_names:
                worksheet.data_validation(1, 2, max_row, 2, {
                    'validate': 'list',
                    'source': f'=목록!$C$1:$C${len(promotion_type_display_names)}',
                    'input_message': '행사유형을 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 할인부담 드롭다운 (인덱스 10)
            worksheet.data_validation(1, 10, max_row, 10, {
                'validate': 'list',
                'source': f'=목록!$D$1:$D${len(discount_owner_list)}',
                'input_message': '할인부담을 선택하세요',
                'error_message': '목록에서 선택해주세요'
            })

            # 서식 정의
            id_header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#dc2626',
                'border': 1
            })
            readonly_header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#000000',
                'border': 1
            })
            editable_header_format = workbook.add_format({
                'bold': True,
                'border': 1
            })
            id_data_format = workbook.add_format({
                'font_color': 'white',
                'bg_color': '#ef4444',
                'border': 1
            })
            readonly_data_format = workbook.add_format({
                'font_color': 'white',
                'bg_color': '#333333',
                'border': 1
            })

            # 헤더 서식 적용
            for col_idx, col_name in enumerate(export_columns):
                if col_idx in id_column_indices:
                    worksheet.write(0, col_idx, col_name, id_header_format)
                elif col_idx in readonly_columns:
                    worksheet.write(0, col_idx, col_name, readonly_header_format)
                else:
                    worksheet.write(0, col_idx, col_name, editable_header_format)

            # 데이터 행 서식 적용
            if len(df) > 0:
                for row_idx in range(len(df)):
                    # ID 컬럼 빨간색
                    for id_col in id_column_indices:
                        col_name = export_columns[id_col]
                        if col_name in df.columns:
                            value = df.iloc[row_idx][col_name]
                            if pd.notna(value):
                                worksheet.write(row_idx + 1, id_col, value, id_data_format)
                            else:
                                worksheet.write_blank(row_idx + 1, id_col, None, id_data_format)

                    # 수정 불가 컬럼 검정색
                    for col_idx in readonly_columns:
                        if col_idx < len(export_columns):
                            col_name = export_columns[col_idx]
                            if col_name in df.columns:
                                value = df.iloc[row_idx][col_name]
                                if pd.notna(value):
                                    worksheet.write(row_idx + 1, col_idx, value, readonly_data_format)
                                else:
                                    worksheet.write_blank(row_idx + 1, col_idx, None, readonly_data_format)

            # 컬럼 너비 설정
            for i in range(len(export_columns)):
                worksheet.set_column(i, i, 15)

            guide_sheet = writer.sheets['안내']
            guide_sheet.set_column(0, 0, 65)
            guide_sheet.set_column(1, 1, 40)

        output.seek(0)

        filename = f"promotions_{year_month or 'template'}.xlsx"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }

        return StreamingResponse(
            output,
            headers=headers,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"다운로드 실패: {str(e)}")


# ========== 통합 엑셀 업로드 ==========

@router.post("/upload")
async def upload_promotions(
    file: UploadFile = File(...),
    request: Request = None,
    user: CurrentUser = Depends(require_permission("Promotion", "UPLOAD"))
):
    """행사 + 행사 상품 통합 엑셀 업로드"""
    try:
        upload_start_time = datetime.now()

        # 1. 파일 확장자 검증
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, "엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        print(f"\n[행사 관리 통합 업로드 시작] {file.filename}")

        content = await file.read()
        excel_file = io.BytesIO(content)
        df = pd.read_excel(excel_file)
        print(f"   총 {len(df):,}행 로드됨")

        # 2. 컬럼 매핑 (한글 → 영문)
        column_map = {
            '행사ID': 'PromotionID',
            '행사명': 'PromotionName',
            '행사유형': 'PromotionType',
            '시작일': 'StartDate',
            '시작시간': 'StartTime',
            '종료일': 'EndDate',
            '종료시간': 'EndTime',
            '브랜드명': 'BrandName',
            '채널명': 'ChannelName',
            '수수료율': 'CommissionRate',
            '할인부담': 'DiscountOwner',
            '자사분담율': 'CompanyShare',
            '채널분담율': 'ChannelShare',
            '비고(행사)': 'PromoNotes',
            '상품ID': 'PromotionProductID',
            '상품코드': 'UniqueCode',
            '상품명': 'ProductName',
            '판매가': 'SellingPrice',
            '행사가': 'PromotionPrice',
            '공급가': 'SupplyPrice',
            '쿠폰할인율': 'CouponDiscountRate',
            '원가': 'UnitCost',
            '물류비': 'LogisticsCost',
            '관리비': 'ManagementCost',
            '창고비': 'WarehouseCost',
            'EDI비': 'EDICost',
            '기타비': 'MisCost',
            '예상매출(상품)': 'ProdExpectedSalesAmount',
            '예상수량(상품)': 'ProdExpectedQuantity',
            '비고(상품)': 'ProdNotes',
        }
        df = df.rename(columns=column_map)

        # 3. 필수 컬럼 확인
        required_cols = ['PromotionName', 'PromotionType', 'StartDate', 'EndDate', 'BrandName', 'ChannelName']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(400, f"필수 컬럼이 없습니다: {missing_cols}")

        # 4. 날짜/시간/숫자 변환
        df['StartDate'] = pd.to_datetime(df['StartDate'], errors='coerce')
        df['EndDate'] = pd.to_datetime(df['EndDate'], errors='coerce')

        invalid_start_dates = df['StartDate'].isna().sum()
        invalid_end_dates = df['EndDate'].isna().sum()
        if invalid_start_dates > 0 or invalid_end_dates > 0:
            raise HTTPException(400, f"날짜 형식이 잘못된 행이 있습니다 (시작일: {invalid_start_dates}개, 종료일: {invalid_end_dates}개)")

        # 시간 기본값
        if 'StartTime' not in df.columns:
            df['StartTime'] = '00:00:00'
        if 'EndTime' not in df.columns:
            df['EndTime'] = '23:59:59'

        # 숫자 변환 (행사)
        for col in ['CommissionRate', 'CompanyShare', 'ChannelShare']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 숫자 변환 (상품)
        product_numeric_cols = [
            'SellingPrice', 'PromotionPrice', 'SupplyPrice', 'CouponDiscountRate',
            'UnitCost', 'LogisticsCost', 'ManagementCost', 'WarehouseCost',
            'EDICost', 'MisCost', 'ProdExpectedSalesAmount'
        ]
        for col in product_numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'ProdExpectedQuantity' in df.columns:
            df['ProdExpectedQuantity'] = pd.to_numeric(df['ProdExpectedQuantity'], errors='coerce').fillna(0).astype(int)

        # 문자열 컬럼 공백 제거
        df['BrandName'] = df['BrandName'].astype(str).str.strip()
        df['ChannelName'] = df['ChannelName'].astype(str).str.strip()
        df['PromotionType'] = df['PromotionType'].astype(str).str.strip()
        if 'UniqueCode' in df.columns:
            df['UniqueCode'] = df['UniqueCode'].astype(str).str.strip()

        # 5. 마스터 데이터 검증
        errors = {
            'brand': {},
            'channel': {},
            'product': {},
            'promotion_type': {}
        }

        # 브랜드명 → BrandID, BrandCode 매핑
        brand_names_unique = df['BrandName'].dropna().unique().tolist()
        brand_names_unique = [n for n in brand_names_unique if n and n != 'nan']
        brand_map = {}
        missing_brand_codes = []
        for name in brand_names_unique:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("SELECT BrandID, Name, BrandCode FROM Brand WHERE Name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    brand_code = row[2]
                    if not brand_code:
                        missing_brand_codes.append(name)
                    brand_map[name] = {'BrandID': row[0], 'BrandName': row[1], 'BrandCode': brand_code}
                else:
                    row_nums = df[df['BrandName'] == name].index.tolist()
                    errors['brand'][name] = [r + 2 for r in row_nums]

        if missing_brand_codes:
            raise HTTPException(400, f"BrandCode가 설정되지 않은 브랜드가 있습니다: {', '.join(missing_brand_codes)}. 브랜드 설정에서 BrandCode를 입력해주세요.")

        # 채널명 → ChannelID 매핑
        channel_names_unique = df['ChannelName'].dropna().unique().tolist()
        channel_names_unique = [n for n in channel_names_unique if n and n != 'nan']
        channel_map = {}
        for name in channel_names_unique:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("SELECT ChannelID, Name FROM Channel WHERE Name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    channel_map[name] = {'ChannelID': row[0], 'ChannelName': row[1]}
                else:
                    row_nums = df[df['ChannelName'] == name].index.tolist()
                    errors['channel'][name] = [r + 2 for r in row_nums]

        # 상품코드 → ProductName 매핑
        if 'UniqueCode' in df.columns:
            unique_codes = df['UniqueCode'].dropna().unique().tolist()
            unique_codes = [c for c in unique_codes if c and c != 'nan']
            product_map = {}
            for code in unique_codes:
                with get_db_cursor(commit=False) as cursor:
                    cursor.execute("SELECT UniqueCode, Name FROM Product WHERE UniqueCode = ?", (code,))
                    row = cursor.fetchone()
                    if row:
                        product_map[code] = {'UniqueCode': row[0], 'ProductName': row[1]}
                    else:
                        row_nums = df[df['UniqueCode'] == code].index.tolist()
                        errors['product'][code] = [r + 2 for r in row_nums]
        else:
            product_map = {}

        # 행사유형 → DisplayName, TypeCode 매핑
        promotion_type_map = {}
        missing_type_codes = []
        promo_types_unique = df['PromotionType'].dropna().unique().tolist()
        promo_types_unique = [t for t in promo_types_unique if t and str(t) != 'nan']
        for display_name in promo_types_unique:
            display_name_str = str(display_name).strip()
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("SELECT DisplayName, TypeCode FROM PromotionType WHERE DisplayName = ?", (display_name_str,))
                row = cursor.fetchone()
                if row:
                    type_code = row[1] if row[1] else ''
                    promotion_type_map[display_name_str] = {
                        'DisplayName': row[0],
                        'TypeCode': type_code
                    }
                    if not type_code:
                        missing_type_codes.append(display_name_str)
                else:
                    row_nums = df[df['PromotionType'] == display_name].index.tolist()
                    errors['promotion_type'][display_name_str] = [r + 2 for r in row_nums]

        if missing_type_codes:
            raise HTTPException(400, f"TypeCode가 설정되지 않은 행사유형이 있습니다: {', '.join(missing_type_codes)}. PromotionType 테이블에서 TypeCode를 설정해주세요.")

        # 에러 모아서 반환
        if errors['brand'] or errors['channel'] or errors['product'] or errors['promotion_type']:
            error_messages = []
            for name, rows in errors['brand'].items():
                error_messages.append(f"존재하지 않는 브랜드명: {name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for name, rows in errors['channel'].items():
                error_messages.append(f"존재하지 않는 채널명: {name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for code, rows in errors['product'].items():
                error_messages.append(f"존재하지 않는 상품코드: {code} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for display_name, rows in errors['promotion_type'].items():
                error_messages.append(f"존재하지 않는 행사유형: {display_name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            raise HTTPException(400, "\n".join(error_messages))

        # 6. 행사 단위 그룹핑
        def get_group_key(row, has_promotion_id):
            if has_promotion_id:
                return row['PromotionID']
            else:
                brand = str(row['BrandName']).strip() if pd.notna(row['BrandName']) else ''
                channel = str(row['ChannelName']).strip() if pd.notna(row['ChannelName']) else ''
                ptype = str(row['PromotionType']).strip() if pd.notna(row['PromotionType']) else ''
                sdate = row['StartDate'].strftime('%Y-%m-%d') if hasattr(row['StartDate'], 'strftime') else str(row['StartDate'])[:10]
                pname = str(row['PromotionName']).strip() if pd.notna(row['PromotionName']) else ''
                return f"{brand}_{channel}_{ptype}_{sdate}_{pname}"

        groups = {}  # {group_key: [row_indices]}
        for idx, row in df.iterrows():
            has_promo_id = (
                'PromotionID' in row
                and pd.notna(row.get('PromotionID'))
                and str(row.get('PromotionID')).strip() not in ['', 'nan']
            )
            key = get_group_key(row, has_promo_id)
            if key not in groups:
                groups[key] = []
            groups[key].append(idx)

        # 7. 신규 행사 복합키 중복 체크
        duplicate_promotions = []
        for key, indices in groups.items():
            first_row = df.iloc[indices[0]]
            has_promo_id = (
                'PromotionID' in first_row
                and pd.notna(first_row.get('PromotionID'))
                and str(first_row.get('PromotionID')).strip() not in ['', 'nan']
            )

            if not has_promo_id:
                # 신규 행사 → 복합키 중복 체크
                brand_name = str(first_row['BrandName']).strip() if pd.notna(first_row['BrandName']) else None
                channel_name = str(first_row['ChannelName']).strip() if pd.notna(first_row['ChannelName']) else None
                promo_type = str(first_row['PromotionType']).strip() if pd.notna(first_row['PromotionType']) else None
                promo_name = str(first_row['PromotionName']).strip() if pd.notna(first_row['PromotionName']) else None
                start_date_val = first_row['StartDate'].strftime('%Y-%m-%d') if hasattr(first_row['StartDate'], 'strftime') else str(first_row['StartDate'])[:10]

                brand_info = brand_map.get(brand_name, {})
                channel_info = channel_map.get(channel_name, {})

                b_id = brand_info.get('BrandID')
                c_id = channel_info.get('ChannelID')

                if b_id and c_id and promo_type and promo_name:
                    with get_db_cursor(commit=False) as cursor:
                        cursor.execute("""
                            SELECT PromotionID FROM [dbo].[Promotion]
                            WHERE BrandID = ? AND ChannelID = ? AND PromotionType = ?
                              AND StartDate = ? AND PromotionName = ?
                        """, b_id, c_id, promo_type, start_date_val, promo_name)
                        existing = cursor.fetchone()
                        if existing:
                            row_num = int(indices[0]) + 2
                            duplicate_promotions.append(
                                f"행 {row_num}: 이미 등록된 행사 (행사명: {promo_name}, 시작일: {start_date_val}, 브랜드: {brand_name}, 채널: {channel_name}, 유형: {promo_type})"
                            )

        if duplicate_promotions:
            raise HTTPException(400, "중복된 행사가 있습니다. 동일 복합키(브랜드+채널+행사유형+시작일+행사명)의 행사가 이미 존재합니다.\n" + "\n".join(duplicate_promotions[:10]))

        # 8. 신규 행사만 PromotionID 자동 생성
        prefix_sequences = {}  # {prefix: current_sequence}

        # DB에서 각 접두사의 최대 순번 조회
        all_prefixes = set()
        for key, indices in groups.items():
            first_row = df.iloc[indices[0]]
            has_promo_id = (
                'PromotionID' in first_row
                and pd.notna(first_row.get('PromotionID'))
                and str(first_row.get('PromotionID')).strip() not in ['', 'nan']
            )

            if not has_promo_id:
                brand_name = str(first_row['BrandName']).strip() if pd.notna(first_row['BrandName']) else None
                promo_type = str(first_row['PromotionType']).strip() if pd.notna(first_row['PromotionType']) else None

                if brand_name and promo_type and pd.notna(first_row['StartDate']):
                    b_info = brand_map.get(brand_name, {})
                    t_info = promotion_type_map.get(promo_type, {})
                    b_code = b_info.get('BrandCode', '')[:2] if b_info.get('BrandCode') else ''
                    t_code = t_info.get('TypeCode', '')

                    if b_code and t_code:
                        start_dt = first_row['StartDate']
                        if hasattr(start_dt, 'strftime'):
                            yymm = start_dt.strftime('%y%m')
                        else:
                            yymm = pd.to_datetime(start_dt).strftime('%y%m')
                        prefix = f"{b_code}{t_code}{yymm}"
                        all_prefixes.add(prefix)

        if all_prefixes:
            max_sequences = promotion_repo.get_max_sequences_by_prefixes(list(all_prefixes))
            for prefix, max_seq in max_sequences.items():
                prefix_sequences[prefix] = max_seq

        # 각 그룹에 대해 PromotionID 할당
        group_promotion_ids = {}  # {group_key: PromotionID}
        for key, indices in groups.items():
            first_row = df.iloc[indices[0]]
            has_promo_id = (
                'PromotionID' in first_row
                and pd.notna(first_row.get('PromotionID'))
                and str(first_row.get('PromotionID')).strip() not in ['', 'nan']
            )

            if has_promo_id:
                group_promotion_ids[key] = str(first_row['PromotionID']).strip()
            else:
                # 신규 PromotionID 생성
                brand_name = str(first_row['BrandName']).strip() if pd.notna(first_row['BrandName']) else None
                promo_type = str(first_row['PromotionType']).strip() if pd.notna(first_row['PromotionType']) else None

                b_info = brand_map.get(brand_name, {})
                t_info = promotion_type_map.get(promo_type, {})
                b_code = b_info.get('BrandCode', '')[:2] if b_info.get('BrandCode') else ''
                t_code = t_info.get('TypeCode', '')

                if b_code and t_code and pd.notna(first_row['StartDate']):
                    start_dt = first_row['StartDate']
                    if hasattr(start_dt, 'strftime'):
                        yymm = start_dt.strftime('%y%m')
                    else:
                        yymm = pd.to_datetime(start_dt).strftime('%y%m')
                    prefix = f"{b_code}{t_code}{yymm}"

                    current_seq = prefix_sequences.get(prefix, 0) + 1
                    prefix_sequences[prefix] = current_seq
                    promotion_id = f"{prefix}{current_seq:02d}"
                    group_promotion_ids[key] = promotion_id
                    print(f"   [PromotionID 자동 생성] {promotion_id}")
                else:
                    row_num = int(indices[0]) + 2
                    raise HTTPException(400, f"행사ID를 생성할 수 없습니다. BrandCode, 행사유형, 시작일을 확인해주세요. (행 {row_num})")

        # 9. Promotion 레코드 준비 + bulk_upsert
        promotion_records = []
        for key, indices in groups.items():
            first_row = df.iloc[indices[0]]
            promo_id = group_promotion_ids[key]

            brand_name = str(first_row['BrandName']).strip() if pd.notna(first_row['BrandName']) and str(first_row['BrandName']).strip() != 'nan' else None
            channel_name = str(first_row['ChannelName']).strip() if pd.notna(first_row['ChannelName']) and str(first_row['ChannelName']).strip() != 'nan' else None
            promo_type = str(first_row['PromotionType']).strip() if pd.notna(first_row['PromotionType']) and str(first_row['PromotionType']).strip() != 'nan' else None

            brand_info = brand_map.get(brand_name, {})
            channel_info = channel_map.get(channel_name, {})
            type_info = promotion_type_map.get(promo_type, {})

            start_time_val = format_time_value(first_row.get('StartTime', '00:00:00'))
            end_time_val = format_time_value(first_row.get('EndTime', '23:59:59'))

            # 상품 레벨 예상매출/예상수량 합산 → 행사 레벨 자동 계산
            sum_sales = 0.0
            sum_qty = 0
            for idx in indices:
                row = df.iloc[idx]
                if pd.notna(row.get('ProdExpectedSalesAmount')):
                    sum_sales += float(row['ProdExpectedSalesAmount'])
                if pd.notna(row.get('ProdExpectedQuantity')):
                    sum_qty += int(row['ProdExpectedQuantity'])

            promotion_records.append({
                'PromotionID': promo_id,
                'PromotionName': str(first_row['PromotionName']).strip() if pd.notna(first_row.get('PromotionName')) else None,
                'PromotionType': type_info.get('DisplayName') or promo_type,
                'StartDate': first_row['StartDate'].strftime('%Y-%m-%d') if pd.notna(first_row['StartDate']) else None,
                'StartTime': start_time_val,
                'EndDate': first_row['EndDate'].strftime('%Y-%m-%d') if pd.notna(first_row['EndDate']) else None,
                'EndTime': end_time_val,
                'BrandID': brand_info.get('BrandID'),
                'BrandName': brand_info.get('BrandName'),
                'ChannelID': channel_info.get('ChannelID'),
                'ChannelName': channel_info.get('ChannelName'),
                'CommissionRate': float(first_row['CommissionRate']) if pd.notna(first_row.get('CommissionRate')) else None,
                'DiscountOwner': str(first_row.get('DiscountOwner')).strip() if pd.notna(first_row.get('DiscountOwner')) and str(first_row.get('DiscountOwner')).strip() != 'nan' else None,
                'CompanyShare': float(first_row['CompanyShare']) if pd.notna(first_row.get('CompanyShare')) else None,
                'ChannelShare': float(first_row['ChannelShare']) if pd.notna(first_row.get('ChannelShare')) else None,
                'ExpectedSalesAmount': sum_sales if sum_sales > 0 else None,
                'ExpectedQuantity': sum_qty if sum_qty > 0 else None,
                'Notes': str(first_row['PromoNotes']) if pd.notna(first_row.get('PromoNotes')) and str(first_row.get('PromoNotes')).strip() != 'nan' else None,
            })

        promo_result = promotion_repo.bulk_upsert(promotion_records)

        # 중복 체크 (Repository 방어)
        promo_duplicates = promo_result.get('duplicates', [])
        if promo_duplicates:
            error_messages = []
            for dup in promo_duplicates[:10]:
                error_messages.append(
                    f"행사 중복: {dup.get('promotion_name', '')} (시작일: {dup.get('start_date', '')}, 브랜드: {dup.get('brand_name', '')})"
                )
            raise HTTPException(400, "중복된 행사가 있습니다.\n" + "\n".join(error_messages))

        # 10. PromotionProduct 레코드 준비 + bulk_upsert
        product_records = []
        for key, indices in groups.items():
            promo_id = group_promotion_ids[key]

            for idx in indices:
                row = df.iloc[idx]

                unique_code = str(row['UniqueCode']).strip() if pd.notna(row.get('UniqueCode')) and str(row.get('UniqueCode')).strip() not in ['', 'nan'] else None

                if not unique_code:
                    continue  # 상품코드 없으면 스킵

                product_info = product_map.get(unique_code, {})

                product_id = None
                if 'PromotionProductID' in row and pd.notna(row.get('PromotionProductID')):
                    try:
                        product_id = int(row['PromotionProductID'])
                    except (ValueError, TypeError):
                        product_id = None

                product_records.append({
                    'PromotionProductID': product_id,
                    'PromotionID': promo_id,
                    'UniqueCode': unique_code,
                    'ProductName': product_info.get('ProductName') or (str(row['ProductName']).strip() if pd.notna(row.get('ProductName')) and str(row.get('ProductName')).strip() != 'nan' else None),
                    'SellingPrice': float(row['SellingPrice']) if pd.notna(row.get('SellingPrice')) else None,
                    'PromotionPrice': float(row['PromotionPrice']) if pd.notna(row.get('PromotionPrice')) else None,
                    'SupplyPrice': float(row['SupplyPrice']) if pd.notna(row.get('SupplyPrice')) else None,
                    'CouponDiscountRate': float(row['CouponDiscountRate']) if pd.notna(row.get('CouponDiscountRate')) else None,
                    'UnitCost': float(row['UnitCost']) if pd.notna(row.get('UnitCost')) else None,
                    'LogisticsCost': float(row['LogisticsCost']) if pd.notna(row.get('LogisticsCost')) else None,
                    'ManagementCost': float(row['ManagementCost']) if pd.notna(row.get('ManagementCost')) else None,
                    'WarehouseCost': float(row['WarehouseCost']) if pd.notna(row.get('WarehouseCost')) else None,
                    'EDICost': float(row['EDICost']) if pd.notna(row.get('EDICost')) else None,
                    'MisCost': float(row['MisCost']) if pd.notna(row.get('MisCost')) else None,
                    'ExpectedSalesAmount': float(row['ProdExpectedSalesAmount']) if pd.notna(row.get('ProdExpectedSalesAmount')) else None,
                    'ExpectedQuantity': int(row['ProdExpectedQuantity']) if pd.notna(row.get('ProdExpectedQuantity')) else None,
                    'Notes': str(row['ProdNotes']) if pd.notna(row.get('ProdNotes')) and str(row.get('ProdNotes')).strip() != 'nan' else None,
                    '_row_num': int(idx) + 2,
                })

        prod_result = {"inserted": 0, "updated": 0, "duplicates": []}
        if product_records:
            prod_result = promotion_product_repo.bulk_upsert(product_records)

            prod_duplicates = prod_result.get('duplicates', [])
            if prod_duplicates:
                error_messages = []
                for dup in prod_duplicates[:10]:
                    error_messages.append(
                        f"행 {dup.get('row', '')}: 중복 상품 (행사ID: {dup.get('promotion_id', '')}, 상품코드: {dup.get('unique_code', '')})"
                    )
                raise HTTPException(400, "중복된 행사 상품이 있습니다.\n" + "\n".join(error_messages))

        upload_end_time = datetime.now()
        duration = (upload_end_time - upload_start_time).total_seconds()

        # 11. 활동 로그
        if user and request:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="Promotion",
                details={
                    "action": "EXCEL_UPLOAD",
                    "filename": file.filename,
                    "total_rows": len(df),
                    "promotion_inserted": promo_result['inserted'],
                    "promotion_updated": promo_result['updated'],
                    "product_inserted": prod_result['inserted'],
                    "product_updated": prod_result['updated'],
                    "duration_seconds": duration
                },
                ip_address=get_client_ip(request)
            )

        print(f"   업로드 완료: 행사 {promo_result['inserted']}건 삽입/{promo_result['updated']}건 수정, 상품 {prod_result['inserted']}건 삽입/{prod_result['updated']}건 수정")

        # 12. 결과 반환
        return {
            "message": "업로드 완료",
            "total_rows": len(df),
            "promotion_inserted": promo_result['inserted'],
            "promotion_updated": promo_result['updated'],
            "product_inserted": prod_result['inserted'],
            "product_updated": prod_result['updated'],
            "duration_seconds": duration
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"업로드 실패: {str(e)}")


# ========== 행사 단일 CRUD ==========

@router.get("/{promotion_id}")
async def get_promotion_item(promotion_id: str, user: CurrentUser = Depends(require_permission("Promotion", "READ"))):
    """행사 단일 조회"""
    try:
        item = promotion_repo.get_by_id(promotion_id)
        if not item:
            raise HTTPException(404, "행사 데이터를 찾을 수 없습니다")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 조회 실패: {str(e)}")


@router.post("")
@log_activity("CREATE", "Promotion", id_key="PromotionID")
async def create_promotion(
    data: PromotionCreate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Promotion", "CREATE"))
):
    """행사 생성"""
    try:
        # PromotionID 자동 생성
        brand_name = data.BrandName
        promo_type = data.PromotionType

        # 브랜드 BrandCode 조회
        brand_code = ''
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT BrandCode FROM Brand WHERE BrandID = ?", (data.BrandID,))
            row = cursor.fetchone()
            if row and row[0]:
                brand_code = row[0][:2]

        # 행사유형 TypeCode 조회
        type_code = ''
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT TypeCode FROM PromotionType WHERE DisplayName = ?", (promo_type,))
            row = cursor.fetchone()
            if row and row[0]:
                type_code = row[0]

        if not brand_code or not type_code:
            raise HTTPException(400, "BrandCode 또는 TypeCode가 설정되지 않았습니다")

        # YYMM
        start_date = pd.to_datetime(data.StartDate)
        yymm = start_date.strftime('%y%m')
        prefix = f"{brand_code}{type_code}{yymm}"

        # 최대 순번 조회
        max_sequences = promotion_repo.get_max_sequences_by_prefixes([prefix])
        current_seq = max_sequences.get(prefix, 0) + 1
        promotion_id = f"{prefix}{current_seq:02d}"

        create_data = data.dict(exclude_none=True)
        create_data['PromotionID'] = promotion_id

        promotion_repo.create(create_data)

        return {"PromotionID": promotion_id, "PromotionName": data.PromotionName}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 생성 실패: {str(e)}")


@router.put("/{promotion_id}")
@log_activity("UPDATE", "Promotion", id_key="PromotionID")
async def update_promotion(
    promotion_id: str,
    data: PromotionUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Promotion", "UPDATE"))
):
    """행사 수정"""
    try:
        if not promotion_repo.exists(promotion_id):
            raise HTTPException(404, "행사 데이터를 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = promotion_repo.update(promotion_id, update_data)
        if not success:
            raise HTTPException(500, "행사 수정 실패")

        return {"PromotionID": promotion_id, **update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 수정 실패: {str(e)}")


@router.delete("/{promotion_id}")
@log_delete("Promotion", id_param="promotion_id")
async def delete_promotion(
    promotion_id: str,
    request: Request,
    user: CurrentUser = Depends(require_permission("Promotion", "DELETE"))
):
    """행사 삭제 (PromotionProduct도 함께 삭제)"""
    try:
        if not promotion_repo.exists(promotion_id):
            raise HTTPException(404, "행사 데이터를 찾을 수 없습니다")

        # PromotionProduct 먼저 삭제
        promotion_product_repo.delete_by_promotion_id(promotion_id)

        # Promotion 삭제
        success = promotion_repo.delete(promotion_id)
        if not success:
            raise HTTPException(500, "행사 삭제 실패")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
@log_bulk_delete("Promotion")
async def bulk_delete_promotions(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Promotion", "DELETE"))
):
    """행사 일괄 삭제 (PromotionProduct도 함께 삭제)"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = promotion_repo.bulk_delete(request_body.ids)

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ==========================================================
#  PromotionProduct Router (행사 상품 CRUD)
# ==========================================================
product_router = APIRouter(prefix="/api/promotions/products", tags=["PromotionProduct"])


@product_router.get("")
async def get_promotion_product_list(
    page: int = 1,
    limit: int = 20,
    promotion_id: Optional[str] = None,
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    promotion_type: Optional[str] = None,
    status: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Promotion", "READ"))
):
    """행사 상품 목록 조회"""
    try:
        filters = {}
        if promotion_id:
            filters['promotion_id'] = promotion_id
        if year_month:
            filters['year_month'] = year_month
        if brand_id:
            filters['brand_id'] = brand_id
        if channel_id:
            filters['channel_id'] = channel_id
        if promotion_type:
            filters['promotion_type'] = promotion_type
        if status:
            filters['status'] = status

        result = promotion_product_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by="pp.PromotionID",
            order_dir="DESC"
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"행사 상품 조회 실패: {str(e)}")


@product_router.put("/bulk-update")
@log_activity("UPDATE", "PromotionProduct")
async def bulk_update_promotion_products_inline(
    data: PromotionProductBulkUpdateRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Promotion", "UPDATE"))
):
    """비정기 상품 인라인 편집 일괄 저장"""
    try:
        items = [item.dict() for item in data.items]
        result = promotion_product_repo.bulk_update_products(items)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 수정 실패: {str(e)}")


@product_router.get("/{product_id}")
async def get_promotion_product_item(product_id: int, user: CurrentUser = Depends(require_permission("Promotion", "READ"))):
    """행사 상품 단일 조회"""
    try:
        item = promotion_product_repo.get_by_id(product_id)
        if not item:
            raise HTTPException(404, "행사 상품 데이터를 찾을 수 없습니다")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 상품 조회 실패: {str(e)}")


@product_router.post("")
@log_activity("CREATE", "PromotionProduct", id_key="PromotionProductID")
async def create_promotion_product(
    data: PromotionProductCreate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Promotion", "CREATE"))
):
    """행사 상품 생성"""
    try:
        product_id = promotion_product_repo.create(data.dict(exclude_none=True))

        return {"PromotionProductID": product_id, "PromotionID": data.PromotionID, "UniqueCode": data.UniqueCode}
    except Exception as e:
        raise HTTPException(500, f"행사 상품 생성 실패: {str(e)}")


@product_router.put("/{product_id}")
@log_activity("UPDATE", "PromotionProduct", id_key="PromotionProductID")
async def update_promotion_product(
    product_id: int,
    data: PromotionProductUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Promotion", "UPDATE"))
):
    """행사 상품 수정"""
    try:
        if not promotion_product_repo.exists(product_id):
            raise HTTPException(404, "행사 상품 데이터를 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = promotion_product_repo.update(product_id, update_data)
        if not success:
            raise HTTPException(500, "행사 상품 수정 실패")

        return {"PromotionProductID": product_id, **update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 상품 수정 실패: {str(e)}")


@product_router.delete("/{product_id}")
@log_delete("PromotionProduct", id_param="product_id")
async def delete_promotion_product(
    product_id: int,
    request: Request,
    user: CurrentUser = Depends(require_permission("Promotion", "DELETE"))
):
    """행사 상품 삭제"""
    try:
        if not promotion_product_repo.exists(product_id):
            raise HTTPException(404, "행사 상품 데이터를 찾을 수 없습니다")

        success = promotion_product_repo.delete(product_id)
        if not success:
            raise HTTPException(500, "행사 상품 삭제 실패")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 상품 삭제 실패: {str(e)}")


@product_router.post("/bulk-delete")
@log_bulk_delete("PromotionProduct")
async def bulk_delete_promotion_products(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Promotion", "DELETE"))
):
    """행사 상품 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = promotion_product_repo.bulk_delete(request_body.ids)

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")
