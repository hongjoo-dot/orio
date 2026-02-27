"""
Expected1PIrregular (사입 비정기 관리) Router
- 사입 비정기 (Expected1PIrregular) CRUD + 통합 엑셀
- 사입 비정기 상품 (Expected1PIrregularProduct) CRUD
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import io
from datetime import datetime
from repositories.expected_1p_irregular_repository import Expected1PIrregularRepository
from repositories.expected_1p_irregular_product_repository import Expected1PIrregularProductRepository
from repositories import BrandRepository, ChannelRepository, ProductRepository, ActivityLogRepository
from core import get_db_cursor
from core.dependencies import get_client_ip, CurrentUser
from core import log_activity, log_delete, log_bulk_delete, require_permission
from core.models import BulkDeleteAnyRequest as BulkDeleteRequest
from utils.helpers import format_time_value


# ========== Repository 인스턴스 ==========
expected_1p_irregular_repo = Expected1PIrregularRepository()
expected_1p_irregular_product_repo = Expected1PIrregularProductRepository()
brand_repo = BrandRepository()
channel_repo = ChannelRepository()
product_repo = ProductRepository()
activity_log_repo = ActivityLogRepository()

# ========== 양식 포맷 설정 ==========
FORMAT_CONFIGS = {
    'oliveyoung': {
        'name': '올리브영',
        'channel_keyword': '올리브영',
        'extra_columns': {
            'export_name': '올리브영유형',
            'internal_name': 'OliveyoungType',
            'dropdown_values': ['온라인', '오프라인'],
            'dropdown_message': '올리브영유형을 선택하세요',
        },
    },
    'coupang': {
        'name': '쿠팡',
        'channel_keyword': '쿠팡',
        'extra_columns': None,
        'product_code': {
            'export_name': '쿠팡SKU',
            'db_column': 'CoupangSKU',
        },
    },
    'kurly': {
        'name': '마켓컬리',
        'channel_keyword': '컬리',
        'extra_columns': None,
    },
    'offline': {
        'name': '오프라인',
        'channel_keyword': None,
        'extra_columns': None,
    },
}


# ========== Pydantic Models — Expected1PIrregular ==========

class Expected1PIrregularCreate(BaseModel):
    IrregularName: str
    IrregularType: str
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
    InputMonth: Optional[str] = None
    OliveyoungType: Optional[str] = None


class Expected1PIrregularUpdate(BaseModel):
    IrregularName: Optional[str] = None
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
    InputMonth: Optional[str] = None
    OliveyoungType: Optional[str] = None


# ========== Pydantic Models — Expected1PIrregularProduct ==========

class Expected1PIrregularProductCreate(BaseModel):
    Expected1PIrregularID: str
    ERPCode: str
    ProductName: Optional[str] = None
    SellingPrice: Optional[float] = None
    IrregularPrice: Optional[float] = None
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


class Expected1PIrregularProductUpdate(BaseModel):
    ProductName: Optional[str] = None
    SellingPrice: Optional[float] = None
    IrregularPrice: Optional[float] = None
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


class Expected1PIrregularProductBulkUpdateItem(BaseModel):
    Expected1PIrregularProductID: int
    IrregularPrice: Optional[float] = None
    ExpectedSalesAmount: Optional[float] = None
    ExpectedQuantity: Optional[int] = None
    Notes: Optional[str] = None


class Expected1PIrregularProductBulkUpdateRequest(BaseModel):
    items: List[Expected1PIrregularProductBulkUpdateItem]


# ==========================================================
#  Expected1PIrregular Router (행사 목록 CRUD + 통합 엑셀)
# ==========================================================
router = APIRouter(prefix="/api/expected/1p/irregular", tags=["Expected1PIrregular"])


# ========== 행사 목록 조회 ==========

@router.get("")
async def get_expected_1p_irregular_list(
    page: int = 1,
    limit: int = 20,
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    irregular_type: Optional[str] = None,
    status: Optional[str] = None,
    input_month: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "DESC",
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "READ"))
):
    """행사 목록 조회"""
    try:
        ALLOWED_SORT = {
            "Expected1PIrregularID": "p.Expected1PIrregularID",
            "IrregularName": "p.IrregularName",
            "IrregularType": "p.IrregularType",
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
        if irregular_type:
            filters['irregular_type'] = irregular_type
        if status:
            filters['status'] = status
        if input_month:
            filters['input_month'] = input_month

        result = expected_1p_irregular_repo.get_list(
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
async def get_expected_1p_irregular_year_months(user: CurrentUser = Depends(require_permission("Expected1PIrregular", "READ"))):
    """행사 년월 목록 조회"""
    try:
        year_months = expected_1p_irregular_repo.get_year_months()
        return {"year_months": year_months}
    except Exception as e:
        raise HTTPException(500, f"년월 목록 조회 실패: {str(e)}")


@router.get("/input-months")
async def get_expected_1p_irregular_input_months(
    year_month: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "READ"))
):
    """사입 비정기 InputMonth(입력월) 목록 조회"""
    try:
        input_months = expected_1p_irregular_repo.get_input_months(year_month)
        return {"input_months": input_months}
    except Exception as e:
        raise HTTPException(500, f"입력월 목록 조회 실패: {str(e)}")


@router.get("/irregular-types")
async def get_irregular_types(user: CurrentUser = Depends(require_permission("Expected1PIrregular", "READ"))):
    """행사유형 목록 조회 (IrregularType 테이블에서 DisplayName)"""
    try:
        irregular_types = expected_1p_irregular_repo.get_irregular_type_display_names()
        return {"irregular_types": irregular_types}
    except Exception as e:
        raise HTTPException(500, f"행사유형 목록 조회 실패: {str(e)}")


@router.get("/statuses")
async def get_expected_1p_irregular_statuses(user: CurrentUser = Depends(require_permission("Expected1PIrregular", "READ"))):
    """행사 상태 목록 조회 (고정값)"""
    try:
        statuses = expected_1p_irregular_repo.get_statuses()
        return {"statuses": statuses}
    except Exception as e:
        raise HTTPException(500, f"상태 목록 조회 실패: {str(e)}")


# ========== 마스터 패널용 요약 목록 ==========

@router.get("/master-summary")
async def get_expected_1p_irregular_master_summary(
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    irregular_type: Optional[str] = None,
    status: Optional[str] = None,
    input_month: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "READ"))
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
        if irregular_type:
            filters['irregular_type'] = irregular_type
        if status:
            filters['status'] = status
        if input_month:
            filters['input_month'] = input_month

        data = expected_1p_irregular_repo.get_master_summary(filters)
        return {"data": data, "total": len(data)}
    except Exception as e:
        raise HTTPException(500, f"비정기 목록 조회 실패: {str(e)}")


# ========== 통합 엑셀 다운로드 ==========

@router.get("/download")
async def download_expected_1p_irregulars(
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    irregular_type: Optional[str] = None,
    status: Optional[str] = None,
    ids: Optional[str] = None,
    format_type: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "EXPORT"))
):
    """행사 + 행사 상품 통합 엑셀 다운로드"""
    try:
        # 포맷 설정
        format_config = FORMAT_CONFIGS.get(format_type) if format_type else None
        format_name = format_config['name'] if format_config else '사입'
        extra_col = format_config.get('extra_columns') if format_config else None
        has_extra_col = extra_col is not None
        product_code_config = format_config.get('product_code') if format_config else None
        product_col_name = product_code_config['export_name'] if product_code_config else '품목코드'

        irregulars = []
        products = []

        # 데이터 조회
        if ids:
            id_list = [id.strip() for id in ids.split(',') if id.strip()]
            irregulars = expected_1p_irregular_repo.get_by_ids(id_list)
            products = expected_1p_irregular_product_repo.get_by_expected_1p_irregular_ids(id_list)
        elif year_month or brand_id or channel_id or irregular_type or status:
            filters = {}
            if year_month:
                filters['year_month'] = year_month
            if brand_id:
                filters['brand_id'] = brand_id
            if channel_id:
                filters['channel_id'] = channel_id
            if irregular_type:
                filters['irregular_type'] = irregular_type
            if status:
                filters['status'] = status

            result = expected_1p_irregular_repo.get_list(page=1, limit=100000, filters=filters)
            irregulars = result['data']

            if irregulars:
                promo_ids = [p['Expected1PIrregularID'] for p in irregulars]
                products = expected_1p_irregular_product_repo.get_by_expected_1p_irregular_ids(promo_ids)

        # 행사별 상품 매핑
        products_by_promo = {}
        for prod in products:
            pid = prod['Expected1PIrregularID']
            if pid not in products_by_promo:
                products_by_promo[pid] = []
            products_by_promo[pid].append(prod)

        # 쿠팡 양식: ERPCode → CoupangSKU 매핑 준비
        erp_to_product_code = {}
        if product_code_config and products:
            all_erp = list(set(p['ERPCode'] for p in products if p.get('ERPCode')))
            if all_erp:
                with get_db_cursor(commit=False) as cursor:
                    placeholders = ','.join(['?' for _ in all_erp])
                    cursor.execute(f"""
                        SELECT pb.ERPCode, p.{product_code_config['db_column']}
                        FROM ProductBox pb
                        JOIN Product p ON pb.ProductID = p.ProductID
                        WHERE pb.ERPCode IN ({placeholders})
                    """, *all_erp)
                    for row in cursor.fetchall():
                        if row[1]:
                            erp_to_product_code[row[0]] = row[1]

        # 통합 행 생성 (행사 정보 + 상품 정보를 1행으로 합침)
        rows = []
        for irreg in irregulars:
            promo_products = products_by_promo.get(irreg['Expected1PIrregularID'], [])

            # 기본 행사 정보
            def build_row(prod=None):
                row = {
                    '행사ID': irreg['Expected1PIrregularID'],
                    '입력월(YYYY-MM)': irreg.get('InputMonth'),
                }
                if has_extra_col:
                    row[extra_col['export_name']] = irreg.get(extra_col['internal_name'])
                row.update({
                    '행사명': irreg['IrregularName'],
                    '행사유형': irreg['IrregularType'],
                    '시작일': irreg['StartDate'],
                    '시작시간': irreg['StartTime'],
                    '종료일': irreg['EndDate'],
                    '종료시간': irreg['EndTime'],
                    '브랜드명': irreg['BrandName'],
                    '채널명': irreg['ChannelName'],
                    '수수료율': irreg['CommissionRate'],
                    '할인부담': irreg['DiscountOwner'],
                    '자사분담율': irreg['CompanyShare'],
                    '채널분담율': irreg['ChannelShare'],
                    '메모(행사)': irreg['Notes'],
                    '상품ID': prod['Expected1PIrregularProductID'] if prod else None,
                    product_col_name: (erp_to_product_code.get(prod['ERPCode'], prod['ERPCode']) if product_code_config else prod['ERPCode']) if prod else None,
                    '판매가': prod['SellingPrice'] if prod else None,
                    '행사가': prod['IrregularPrice'] if prod else None,
                    '공급가': prod['SupplyPrice'] if prod else None,
                    '쿠폰할인율': prod['CouponDiscountRate'] if prod else None,
                    '원가': prod['UnitCost'] if prod else None,
                    '물류비': prod['LogisticsCost'] if prod else None,
                    '관리비': prod['ManagementCost'] if prod else None,
                    '창고비': prod['WarehouseCost'] if prod else None,
                    'EDI비': prod['EDICost'] if prod else None,
                    '기타비': prod['MisCost'] if prod else None,
                    '예상매출(상품)': prod['ExpectedSalesAmount'] if prod else None,
                    '예상수량(상품)': prod['ExpectedQuantity'] if prod else None,
                    '메모(상품)': prod['Notes'] if prod else None,
                })
                return row

            if promo_products:
                for prod in promo_products:
                    rows.append(build_row(prod))
            else:
                rows.append(build_row())

        # 컬럼 정의 (동적 구성)
        export_columns = ['행사ID', '입력월(YYYY-MM)']
        if has_extra_col:
            export_columns.append(extra_col['export_name'])
        export_columns += [
            '행사명', '행사유형', '시작일', '시작시간', '종료일', '종료시간',
            '브랜드명', '채널명', '수수료율', '할인부담', '자사분담율', '채널분담율',
            '메모(행사)',
            '상품ID', product_col_name, '판매가', '행사가', '공급가', '쿠폰할인율',
            '원가', '물류비', '관리비', '창고비', 'EDI비', '기타비',
            '예상매출(상품)', '예상수량(상품)', '메모(상품)'
        ]

        # 인덱스 동적 계산
        id_column_indices = [export_columns.index('행사ID'), export_columns.index('상품ID')]
        readonly_column_names = ['입력월(YYYY-MM)', '행사명', '행사유형', '시작일', '브랜드명', '채널명', product_col_name]
        readonly_columns = [export_columns.index(name) for name in readonly_column_names]

        if not rows:
            df = pd.DataFrame(columns=export_columns)
        else:
            df = pd.DataFrame(rows, columns=export_columns)

        # 안내 시트
        guide_data = [
            [f'[{format_name} 행사 관리 통합 업로드 안내]', ''],
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
            ['메모(행사)', '메모'],
            ['상품ID (빨간색)', '수정할 상품 식별용 (비워두면 신규 등록)'],
            [f'{product_col_name} (검정)', f'Product 테이블의 {product_col_name} (수정 불가)' if product_code_config else 'ProductBox 테이블의 품목코드 (수정 불가)'],
            ['판매가~기타비', '가격/비용 정보'],
            ['예상매출(상품)', '숫자'],
            ['예상수량(상품)', '숫자'],
            ['메모(상품)', '메모'],
        ]
        if has_extra_col:
            guide_data.append([extra_col['export_name'], f"{', '.join(extra_col['dropdown_values'])} 중 선택"])
        guide_data += [
            ['', ''],
            ['■ 주의사항', ''],
            ['1. 같은 행사의 여러 상품은 행사 정보가 동일하게 반복됩니다.', ''],
            ['2. 행사ID를 비워두면 행사명+행사유형+시작일+브랜드명+채널명으로 그룹핑됩니다.', ''],
            ['3. 검정색/빨간색 배경 컬럼은 수정해도 반영되지 않습니다.', ''],
            ['4. 브랜드명, 채널명, 품목코드, 행사유형은 반드시 DB에 등록된 값이어야 합니다.', ''],
        ]
        guide_df = pd.DataFrame(guide_data, columns=['항목', '설명'])

        # 드롭다운용 목록 조회
        channels_1p = channel_repo.get_channel_list(contract_type='1P')
        channels_2p = channel_repo.get_channel_list(contract_type='2P')
        channels = channels_1p + channels_2p
        brands = brand_repo.get_all_brands()

        # 포맷별 채널 필터링
        keyword = format_config.get('channel_keyword') if format_config else None
        if keyword:
            filtered_channels = [ch for ch in channels if keyword in ch['Name']]
        else:
            filtered_channels = channels
        channel_names = [ch['Name'] for ch in filtered_channels]
        brand_names = [br['Name'] for br in brands]
        irregular_type_display_names = expected_1p_irregular_repo.get_irregular_type_display_names()
        discount_owner_list = ['COMPANY', 'CHANNEL', 'BOTH']

        # 품목코드/쿠팡SKU 목록
        if product_code_config:
            with get_db_cursor(commit=False) as cursor:
                db_col = product_code_config['db_column']
                cursor.execute(f"""
                    SELECT DISTINCT p.{db_col}
                    FROM Product p
                    WHERE p.Status = 'YES' AND p.{db_col} IS NOT NULL AND p.{db_col} != ''
                    ORDER BY p.{db_col}
                """)
                product_codes = [row[0] for row in cursor.fetchall()]
        else:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT DISTINCT pb.ERPCode
                    FROM ProductBox pb
                    INNER JOIN Product p ON pb.ProductID = p.ProductID
                    WHERE p.Status = 'YES'
                    ORDER BY pb.ERPCode
                """)
                product_codes = [row[0] for row in cursor.fetchall()]

        # 시트명
        sheet_name = f'{format_name} 행사관리'

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
            guide_df.to_excel(writer, index=False, sheet_name='안내')

            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

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
            for i, name in enumerate(irregular_type_display_names):
                list_sheet.write(i, 2, name)
            # D열: 할인부담 목록
            for i, name in enumerate(discount_owner_list):
                list_sheet.write(i, 3, name)
            # E열: 품목코드/쿠팡SKU 목록
            for i, code in enumerate(product_codes):
                list_sheet.write(i, 4, code)
            # F열: 전용 컬럼 드롭다운 값 (있으면)
            extra_dropdown_values = []
            if has_extra_col:
                extra_dropdown_values = extra_col['dropdown_values']
                for i, val in enumerate(extra_dropdown_values):
                    list_sheet.write(i, 5, val)

            # 드롭다운 적용 범위
            max_row = max(len(df) + 100, 1000)

            # 브랜드명 드롭다운
            br_col_idx = export_columns.index('브랜드명')
            if brand_names:
                worksheet.data_validation(1, br_col_idx, max_row, br_col_idx, {
                    'validate': 'list',
                    'source': f'=목록!$A$1:$A${len(brand_names)}',
                    'input_message': '브랜드를 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 채널명 드롭다운
            ch_col_idx = export_columns.index('채널명')
            if channel_names:
                worksheet.data_validation(1, ch_col_idx, max_row, ch_col_idx, {
                    'validate': 'list',
                    'source': f'=목록!$B$1:$B${len(channel_names)}',
                    'input_message': '채널을 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 행사유형 드롭다운
            type_col_idx = export_columns.index('행사유형')
            if irregular_type_display_names:
                worksheet.data_validation(1, type_col_idx, max_row, type_col_idx, {
                    'validate': 'list',
                    'source': f'=목록!$C$1:$C${len(irregular_type_display_names)}',
                    'input_message': '행사유형을 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 할인부담 드롭다운
            disc_col_idx = export_columns.index('할인부담')
            worksheet.data_validation(1, disc_col_idx, max_row, disc_col_idx, {
                'validate': 'list',
                'source': f'=목록!$D$1:$D${len(discount_owner_list)}',
                'input_message': '할인부담을 선택하세요',
                'error_message': '목록에서 선택해주세요'
            })

            # 품목코드/쿠팡SKU 드롭다운
            prod_code_col_idx = export_columns.index(product_col_name)
            if product_codes:
                worksheet.data_validation(1, prod_code_col_idx, max_row, prod_code_col_idx, {
                    'validate': 'list',
                    'source': f'=목록!$E$1:$E${len(product_codes)}',
                    'input_message': f'{product_col_name}를 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 전용 컬럼 드롭다운 (있으면)
            if has_extra_col and extra_dropdown_values:
                extra_col_idx = export_columns.index(extra_col['export_name'])
                worksheet.data_validation(1, extra_col_idx, max_row, extra_col_idx, {
                    'validate': 'list',
                    'source': f'=목록!$F$1:$F${len(extra_dropdown_values)}',
                    'input_message': extra_col['dropdown_message'],
                    'error_message': '목록에서 선택해주세요'
                })

            # 서식 정의
            id_header_format = workbook.add_format({
                'bold': True, 'font_color': 'white', 'bg_color': '#dc2626', 'border': 1
            })
            readonly_header_format = workbook.add_format({
                'bold': True, 'font_color': 'white', 'bg_color': '#000000', 'border': 1
            })
            editable_header_format = workbook.add_format({
                'bold': True, 'border': 1
            })
            id_data_format = workbook.add_format({
                'font_color': 'white', 'bg_color': '#ef4444', 'border': 1
            })
            readonly_data_format = workbook.add_format({
                'font_color': 'white', 'bg_color': '#333333', 'border': 1
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
                    for id_col in id_column_indices:
                        col_name = export_columns[id_col]
                        if col_name in df.columns:
                            value = df.iloc[row_idx][col_name]
                            if pd.notna(value):
                                worksheet.write(row_idx + 1, id_col, value, id_data_format)
                            else:
                                worksheet.write_blank(row_idx + 1, id_col, None, id_data_format)

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

        format_suffix = f'_{format_type}' if format_type else ''
        filename = f"expected_1p_irregulars{format_suffix}_{year_month or 'template'}.xlsx"
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
async def upload_expected_1p_irregulars(
    file: UploadFile = File(...),
    input_month: Optional[str] = Form(None),
    request: Request = None,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "UPLOAD"))
):
    """행사 + 행사 상품 통합 엑셀 업로드 (input_month: 입력월 YYYY-MM)"""
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
            '행사ID': 'Expected1PIrregularID',
            '입력월(YYYY-MM)': 'InputMonth',
            '입력월': 'InputMonth',
            '올리브영유형': 'OliveyoungType',
            '행사명': 'IrregularName',
            '행사유형': 'IrregularType',
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
            '메모(행사)': 'PromoNotes',
            '비고(행사)': 'PromoNotes',
            '상품ID': 'Expected1PIrregularProductID',
            '품목코드': 'ERPCode',
            '상품코드': 'ERPCode',  # 기존 양식 호환
            '상품명': 'ProductName',
            '판매가': 'SellingPrice',
            '행사가': 'IrregularPrice',
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
            '메모(상품)': 'ProdNotes',
            '비고(상품)': 'ProdNotes',
            '쿠팡SKU': 'CoupangSKU',
        }
        df = df.rename(columns=column_map)

        # 쿠팡SKU → ERPCode 변환 (쿠팡 양식 업로드 시)
        if 'CoupangSKU' in df.columns and 'ERPCode' not in df.columns:
            df['CoupangSKU'] = df['CoupangSKU'].astype(str).str.strip()
            sku_values = df['CoupangSKU'].dropna().unique().tolist()
            sku_values = [v for v in sku_values if v and v != 'nan']
            sku_to_erp = {}
            sku_errors = {}
            for sku in sku_values:
                with get_db_cursor(commit=False) as cursor:
                    cursor.execute("""
                        SELECT TOP 1 pb.ERPCode
                        FROM Product p
                        JOIN ProductBox pb ON p.ProductID = pb.ProductID
                        WHERE p.CoupangSKU = ?
                    """, (sku,))
                    row = cursor.fetchone()
                    if row:
                        sku_to_erp[sku] = row[0]
                    else:
                        row_nums = df[df['CoupangSKU'] == sku].index.tolist()
                        sku_errors[sku] = [r + 2 for r in row_nums]
            if sku_errors:
                error_messages = []
                for sku, rows in sku_errors.items():
                    error_messages.append(f"매핑되지 않는 쿠팡SKU: {sku} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
                raise HTTPException(400, "\n".join(error_messages))
            df['ERPCode'] = df['CoupangSKU'].map(sku_to_erp)
            df['ERPCode'] = df['ERPCode'].astype(str).str.strip()

        # 3. 필수 컬럼 확인
        required_cols = ['IrregularName', 'IrregularType', 'StartDate', 'EndDate', 'BrandName', 'ChannelName']
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
            'SellingPrice', 'IrregularPrice', 'SupplyPrice', 'CouponDiscountRate',
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
        df['IrregularType'] = df['IrregularType'].astype(str).str.strip()
        if 'ERPCode' in df.columns:
            df['ERPCode'] = df['ERPCode'].astype(str).str.strip()

        # 5. 마스터 데이터 검증
        errors = {
            'brand': {},
            'channel': {},
            'product': {},
            'irregular_type': {}
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

        # 채널명 → ChannelID 매핑 (사입 1P/2P 채널만 허용)
        channel_names_unique = df['ChannelName'].dropna().unique().tolist()
        channel_names_unique = [n for n in channel_names_unique if n and n != 'nan']
        channel_map = {}
        for name in channel_names_unique:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("SELECT ChannelID, Name, ContractType FROM Channel WHERE Name = ?", (name,))
                row = cursor.fetchone()
                if row and row[2] in ('1P', '2P'):
                    channel_map[name] = {'ChannelID': row[0], 'ChannelName': row[1]}
                elif row:
                    row_nums = df[df['ChannelName'] == name].index.tolist()
                    errors['channel'][f"{name} (사입 채널이 아님)"] = [r + 2 for r in row_nums]
                else:
                    row_nums = df[df['ChannelName'] == name].index.tolist()
                    errors['channel'][name] = [r + 2 for r in row_nums]

        # 품목코드(ERPCode) → UniqueCode, ProductName 매핑
        if 'ERPCode' in df.columns:
            erp_codes_unique = df['ERPCode'].dropna().unique().tolist()
            erp_codes_unique = [c for c in erp_codes_unique if c and c != 'nan']
            product_map = {}
            for code in erp_codes_unique:
                with get_db_cursor(commit=False) as cursor:
                    cursor.execute("""
                        SELECT pb.ERPCode, p.UniqueCode, p.Name
                        FROM ProductBox pb
                        INNER JOIN Product p ON pb.ProductID = p.ProductID
                        WHERE pb.ERPCode = ?
                    """, (code,))
                    row = cursor.fetchone()
                    if row:
                        product_map[code] = {'ERPCode': row[0], 'UniqueCode': row[1], 'ProductName': row[2]}
                    else:
                        row_nums = df[df['ERPCode'] == code].index.tolist()
                        errors['product'][code] = [r + 2 for r in row_nums]
        else:
            product_map = {}

        # 행사유형 → DisplayName, TypeCode 매핑
        irregular_type_map = {}
        missing_type_codes = []
        promo_types_unique = df['IrregularType'].dropna().unique().tolist()
        promo_types_unique = [t for t in promo_types_unique if t and str(t) != 'nan']
        for display_name in promo_types_unique:
            display_name_str = str(display_name).strip()
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("SELECT DisplayName, TypeCode FROM IrregularType WHERE DisplayName = ?", (display_name_str,))
                row = cursor.fetchone()
                if row:
                    type_code = row[1] if row[1] else ''
                    irregular_type_map[display_name_str] = {
                        'DisplayName': row[0],
                        'TypeCode': type_code
                    }
                    if not type_code:
                        missing_type_codes.append(display_name_str)
                else:
                    row_nums = df[df['IrregularType'] == display_name].index.tolist()
                    errors['irregular_type'][display_name_str] = [r + 2 for r in row_nums]

        if missing_type_codes:
            raise HTTPException(400, f"TypeCode가 설정되지 않은 행사유형이 있습니다: {', '.join(missing_type_codes)}. IrregularType 테이블에서 TypeCode를 설정해주세요.")

        # 에러 모아서 반환
        if errors['brand'] or errors['channel'] or errors['product'] or errors['irregular_type']:
            error_messages = []
            for name, rows in errors['brand'].items():
                error_messages.append(f"존재하지 않는 브랜드명: {name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for name, rows in errors['channel'].items():
                error_messages.append(f"존재하지 않는 채널명: {name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for code, rows in errors['product'].items():
                error_messages.append(f"존재하지 않는 품목코드: {code} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for display_name, rows in errors['irregular_type'].items():
                error_messages.append(f"존재하지 않는 행사유형: {display_name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            raise HTTPException(400, "\n".join(error_messages))

        # 6. 행사 단위 그룹핑
        def get_group_key(row, has_irregular_id):
            if has_irregular_id:
                return row['Expected1PIrregularID']
            else:
                brand = str(row['BrandName']).strip() if pd.notna(row['BrandName']) else ''
                channel = str(row['ChannelName']).strip() if pd.notna(row['ChannelName']) else ''
                ptype = str(row['IrregularType']).strip() if pd.notna(row['IrregularType']) else ''
                sdate = row['StartDate'].strftime('%Y-%m-%d') if hasattr(row['StartDate'], 'strftime') else str(row['StartDate'])[:10]
                pname = str(row['IrregularName']).strip() if pd.notna(row['IrregularName']) else ''
                return f"{brand}_{channel}_{ptype}_{sdate}_{pname}"

        groups = {}  # {group_key: [row_indices]}
        for idx, row in df.iterrows():
            has_promo_id = (
                'Expected1PIrregularID' in row
                and pd.notna(row.get('Expected1PIrregularID'))
                and str(row.get('Expected1PIrregularID')).strip() not in ['', 'nan']
            )
            key = get_group_key(row, has_promo_id)
            if key not in groups:
                groups[key] = []
            groups[key].append(idx)

        # 7. 신규 행사 복합키 중복 체크
        duplicate_irregulars = []
        for key, indices in groups.items():
            first_row = df.iloc[indices[0]]
            has_promo_id = (
                'Expected1PIrregularID' in first_row
                and pd.notna(first_row.get('Expected1PIrregularID'))
                and str(first_row.get('Expected1PIrregularID')).strip() not in ['', 'nan']
            )

            if not has_promo_id:
                # 신규 행사 → 복합키 중복 체크
                brand_name = str(first_row['BrandName']).strip() if pd.notna(first_row['BrandName']) else None
                channel_name = str(first_row['ChannelName']).strip() if pd.notna(first_row['ChannelName']) else None
                promo_type = str(first_row['IrregularType']).strip() if pd.notna(first_row['IrregularType']) else None
                promo_name = str(first_row['IrregularName']).strip() if pd.notna(first_row['IrregularName']) else None
                start_date_val = first_row['StartDate'].strftime('%Y-%m-%d') if hasattr(first_row['StartDate'], 'strftime') else str(first_row['StartDate'])[:10]

                brand_info = brand_map.get(brand_name, {})
                channel_info = channel_map.get(channel_name, {})

                b_id = brand_info.get('BrandID')
                c_id = channel_info.get('ChannelID')

                if b_id and c_id and promo_type and promo_name:
                    with get_db_cursor(commit=False) as cursor:
                        cursor.execute("""
                            SELECT Expected1PIrregularID FROM [dbo].[Expected1PIrregular]
                            WHERE BrandID = ? AND ChannelID = ? AND IrregularType = ?
                              AND StartDate = ? AND IrregularName = ?
                        """, b_id, c_id, promo_type, start_date_val, promo_name)
                        existing = cursor.fetchone()
                        if existing:
                            row_num = int(indices[0]) + 2
                            duplicate_irregulars.append(
                                f"행 {row_num}: 이미 등록된 행사 (행사명: {promo_name}, 시작일: {start_date_val}, 브랜드: {brand_name}, 채널: {channel_name}, 유형: {promo_type})"
                            )

        if duplicate_irregulars:
            raise HTTPException(400, "중복된 행사가 있습니다. 동일 복합키(브랜드+채널+행사유형+시작일+행사명)의 행사가 이미 존재합니다.\n" + "\n".join(duplicate_irregulars[:10]))

        # 8. 신규 행사만 IrregularID 자동 생성
        prefix_sequences = {}  # {prefix: current_sequence}

        # DB에서 각 접두사의 최대 순번 조회
        all_prefixes = set()
        for key, indices in groups.items():
            first_row = df.iloc[indices[0]]
            has_promo_id = (
                'Expected1PIrregularID' in first_row
                and pd.notna(first_row.get('Expected1PIrregularID'))
                and str(first_row.get('Expected1PIrregularID')).strip() not in ['', 'nan']
            )

            if not has_promo_id:
                brand_name = str(first_row['BrandName']).strip() if pd.notna(first_row['BrandName']) else None
                promo_type = str(first_row['IrregularType']).strip() if pd.notna(first_row['IrregularType']) else None

                if brand_name and promo_type and pd.notna(first_row['StartDate']):
                    b_info = brand_map.get(brand_name, {})
                    t_info = irregular_type_map.get(promo_type, {})
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
            max_sequences = expected_1p_irregular_repo.get_max_sequences_by_prefixes(list(all_prefixes))
            for prefix, max_seq in max_sequences.items():
                prefix_sequences[prefix] = max_seq

        # 각 그룹에 대해 IrregularID 할당
        group_irregular_ids = {}  # {group_key: IrregularID}
        for key, indices in groups.items():
            first_row = df.iloc[indices[0]]
            has_promo_id = (
                'Expected1PIrregularID' in first_row
                and pd.notna(first_row.get('Expected1PIrregularID'))
                and str(first_row.get('Expected1PIrregularID')).strip() not in ['', 'nan']
            )

            if has_promo_id:
                group_irregular_ids[key] = str(first_row['Expected1PIrregularID']).strip()
            else:
                # 신규 IrregularID 생성
                brand_name = str(first_row['BrandName']).strip() if pd.notna(first_row['BrandName']) else None
                promo_type = str(first_row['IrregularType']).strip() if pd.notna(first_row['IrregularType']) else None

                b_info = brand_map.get(brand_name, {})
                t_info = irregular_type_map.get(promo_type, {})
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
                    expected_1p_irregular_id = f"{prefix}{current_seq:02d}"
                    group_irregular_ids[key] = expected_1p_irregular_id
                    print(f"   [Expected1PIrregularID 자동 생성] {expected_1p_irregular_id}")
                else:
                    row_num = int(indices[0]) + 2
                    raise HTTPException(400, f"행사ID를 생성할 수 없습니다. BrandCode, 행사유형, 시작일을 확인해주세요. (행 {row_num})")

        # 9. Irregular 레코드 준비 + bulk_upsert
        irregular_records = []
        for key, indices in groups.items():
            first_row = df.iloc[indices[0]]
            promo_id = group_irregular_ids[key]

            brand_name = str(first_row['BrandName']).strip() if pd.notna(first_row['BrandName']) and str(first_row['BrandName']).strip() != 'nan' else None
            channel_name = str(first_row['ChannelName']).strip() if pd.notna(first_row['ChannelName']) and str(first_row['ChannelName']).strip() != 'nan' else None
            promo_type = str(first_row['IrregularType']).strip() if pd.notna(first_row['IrregularType']) and str(first_row['IrregularType']).strip() != 'nan' else None

            brand_info = brand_map.get(brand_name, {})
            channel_info = channel_map.get(channel_name, {})
            type_info = irregular_type_map.get(promo_type, {})

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

            irregular_records.append({
                'Expected1PIrregularID': promo_id,
                'IrregularName': str(first_row['IrregularName']).strip() if pd.notna(first_row.get('IrregularName')) else None,
                'IrregularType': type_info.get('DisplayName') or promo_type,
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
                'InputMonth': input_month or datetime.now().strftime('%Y-%m'),
                'OliveyoungType': str(first_row['OliveyoungType']).strip() if pd.notna(first_row.get('OliveyoungType')) and str(first_row.get('OliveyoungType')).strip() != 'nan' else None,
            })

        promo_result = expected_1p_irregular_repo.bulk_upsert(irregular_records)

        # 중복 체크 (Repository 방어)
        promo_duplicates = promo_result.get('duplicates', [])
        if promo_duplicates:
            error_messages = []
            for dup in promo_duplicates[:10]:
                error_messages.append(
                    f"행사 중복: {dup.get('expected_1p_irregular_name', '')} (시작일: {dup.get('start_date', '')}, 브랜드: {dup.get('brand_name', '')})"
                )
            raise HTTPException(400, "중복된 행사가 있습니다.\n" + "\n".join(error_messages))

        # 10. IrregularProduct 레코드 준비 + bulk_upsert
        product_records = []
        for key, indices in groups.items():
            promo_id = group_irregular_ids[key]

            for idx in indices:
                row = df.iloc[idx]

                erp_code = str(row['ERPCode']).strip() if pd.notna(row.get('ERPCode')) and str(row.get('ERPCode')).strip() not in ['', 'nan'] else None

                if not erp_code:
                    continue  # 품목코드 없으면 스킵

                product_info = product_map.get(erp_code, {})

                product_id = None
                if 'Expected1PIrregularProductID' in row and pd.notna(row.get('Expected1PIrregularProductID')):
                    try:
                        product_id = int(row['Expected1PIrregularProductID'])
                    except (ValueError, TypeError):
                        product_id = None

                product_records.append({
                    'Expected1PIrregularProductID': product_id,
                    'Expected1PIrregularID': promo_id,
                    'ERPCode': erp_code,
                    'UniqueCode': product_info.get('UniqueCode'),
                    'ProductName': product_info.get('ProductName') or (str(row['ProductName']).strip() if pd.notna(row.get('ProductName')) and str(row.get('ProductName')).strip() != 'nan' else None),
                    'SellingPrice': float(row['SellingPrice']) if pd.notna(row.get('SellingPrice')) else None,
                    'IrregularPrice': float(row['IrregularPrice']) if pd.notna(row.get('IrregularPrice')) else None,
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
            prod_result = expected_1p_irregular_product_repo.bulk_upsert(product_records)

            prod_duplicates = prod_result.get('duplicates', [])
            if prod_duplicates:
                error_messages = []
                for dup in prod_duplicates[:10]:
                    error_messages.append(
                        f"행 {dup.get('row', '')}: 중복 상품 (행사ID: {dup.get('expected_1p_irregular_id', '')}, 상품코드: {dup.get('unique_code', '')})"
                    )
                raise HTTPException(400, "중복된 행사 상품이 있습니다.\n" + "\n".join(error_messages))

        upload_end_time = datetime.now()
        duration = (upload_end_time - upload_start_time).total_seconds()

        # 11. 활동 로그
        if user and request:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="Expected1PIrregular",
                details={
                    "action": "EXCEL_UPLOAD",
                    "filename": file.filename,
                    "total_rows": len(df),
                    "expected_1p_irregular_inserted": promo_result['inserted'],
                    "expected_1p_irregular_updated": promo_result['updated'],
                    "product_inserted": prod_result['inserted'],
                    "product_updated": prod_result['updated'],
                    "duration_seconds": duration
                },
                ip_address=get_client_ip(request)
            )

        print(f"   업로드 완료: 행사 {promo_result['inserted']}건 삽입/{promo_result['updated']}건 수정, 상품 {prod_result['inserted']}건 삽입/{prod_result['updated']}건 수정")

        # Slack 알림 (비동기 - 응답 지연 없음)
        try:
            from utils.slack_notifier import send_expected_upload_notification_async
            total_inserted = promo_result['inserted'] + prod_result['inserted']
            total_updated = promo_result['updated'] + prod_result['updated']
            send_expected_upload_notification_async(
                sales_type="사입(1P)",
                data_type="비정기",
                total_rows=len(df),
                inserted=total_inserted,
                updated=total_updated,
                input_month=input_month,
                username=user.username if user else None
            )
        except Exception:
            pass

        # 12. 결과 반환
        return {
            "message": "업로드 완료",
            "total_rows": len(df),
            "expected_1p_irregular_inserted": promo_result['inserted'],
            "expected_1p_irregular_updated": promo_result['updated'],
            "product_inserted": prod_result['inserted'],
            "product_updated": prod_result['updated'],
            "duration_seconds": duration
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"업로드 실패: {str(e)}")


# ========== 행사 단일 CRUD ==========

@router.get("/{expected_1p_irregular_id}")
async def get_expected_1p_irregular_item(expected_1p_irregular_id: str, user: CurrentUser = Depends(require_permission("Expected1PIrregular", "READ"))):
    """행사 단일 조회"""
    try:
        item = expected_1p_irregular_repo.get_by_id(expected_1p_irregular_id)
        if not item:
            raise HTTPException(404, "행사 데이터를 찾을 수 없습니다")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 조회 실패: {str(e)}")


@router.post("")
@log_activity("CREATE", "Expected1PIrregular", id_key="Expected1PIrregularID")
async def create_expected_1p_irregular(
    data: Expected1PIrregularCreate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "CREATE"))
):
    """행사 생성"""
    try:
        # IrregularID 자동 생성
        brand_name = data.BrandName
        promo_type = data.IrregularType

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
            cursor.execute("SELECT TypeCode FROM IrregularType WHERE DisplayName = ?", (promo_type,))
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
        max_sequences = expected_1p_irregular_repo.get_max_sequences_by_prefixes([prefix])
        current_seq = max_sequences.get(prefix, 0) + 1
        expected_1p_irregular_id = f"{prefix}{current_seq:02d}"

        create_data = data.dict(exclude_none=True)
        create_data['Expected1PIrregularID'] = expected_1p_irregular_id

        expected_1p_irregular_repo.create(create_data, user_id=user.user_id)

        return {"IrregularID": expected_1p_irregular_id, "IrregularName": data.IrregularName}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 생성 실패: {str(e)}")


@router.put("/{expected_1p_irregular_id}")
@log_activity("UPDATE", "Expected1PIrregular", id_key="Expected1PIrregularID")
async def update_expected_1p_irregular(
    expected_1p_irregular_id: str,
    data: Expected1PIrregularUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "UPDATE"))
):
    """행사 수정"""
    try:
        if not expected_1p_irregular_repo.exists(expected_1p_irregular_id):
            raise HTTPException(404, "행사 데이터를 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = expected_1p_irregular_repo.update(expected_1p_irregular_id, update_data, user_id=user.user_id)
        if not success:
            raise HTTPException(500, "행사 수정 실패")

        # Slack 알림 (비동기)
        try:
            from utils.slack_notifier import send_expected_upload_notification_async
            send_expected_upload_notification_async(
                sales_type="사입(1P)", data_type="비정기",
                total_rows=1, inserted=0, updated=1,
                username=user.username if user else None,
                action="인라인 수정"
            )
        except Exception:
            pass

        return {"IrregularID": expected_1p_irregular_id, **update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 수정 실패: {str(e)}")


@router.delete("/{expected_1p_irregular_id}")
@log_delete("Expected1PIrregular", id_param="expected_1p_irregular_id")
async def delete_expected_1p_irregular(
    expected_1p_irregular_id: str,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "DELETE"))
):
    """행사 삭제 (IrregularProduct도 함께 삭제)"""
    try:
        if not expected_1p_irregular_repo.exists(expected_1p_irregular_id):
            raise HTTPException(404, "행사 데이터를 찾을 수 없습니다")

        # IrregularProduct 먼저 삭제
        expected_1p_irregular_product_repo.delete_by_expected_1p_irregular_id(expected_1p_irregular_id)

        # Irregular 삭제
        success = expected_1p_irregular_repo.delete(expected_1p_irregular_id)
        if not success:
            raise HTTPException(500, "행사 삭제 실패")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
@log_bulk_delete("Expected1PIrregular")
async def bulk_delete_expected_1p_irregulars(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "DELETE"))
):
    """행사 일괄 삭제 (IrregularProduct도 함께 삭제)"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = expected_1p_irregular_repo.bulk_delete(request_body.ids)

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ==========================================================
#  Expected1PIrregularProduct Router (행사 상품 CRUD)
# ==========================================================
product_router = APIRouter(prefix="/api/expected/1p/irregular/products", tags=["Expected1PIrregularProduct"])


@product_router.get("")
async def get_expected_1p_irregular_product_list(
    page: int = 1,
    limit: int = 20,
    expected_1p_irregular_id: Optional[str] = None,
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    irregular_type: Optional[str] = None,
    status: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "READ"))
):
    """행사 상품 목록 조회"""
    try:
        filters = {}
        if expected_1p_irregular_id:
            filters['expected_1p_irregular_id'] = expected_1p_irregular_id
        if year_month:
            filters['year_month'] = year_month
        if brand_id:
            filters['brand_id'] = brand_id
        if channel_id:
            filters['channel_id'] = channel_id
        if irregular_type:
            filters['irregular_type'] = irregular_type
        if status:
            filters['status'] = status

        result = expected_1p_irregular_product_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by="pp.Expected1PIrregularID",
            order_dir="DESC"
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"행사 상품 조회 실패: {str(e)}")


@product_router.put("/bulk-update")
@log_activity("UPDATE", "Expected1PIrregularProduct")
async def bulk_update_expected_1p_irregular_products_inline(
    data: Expected1PIrregularProductBulkUpdateRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "UPDATE"))
):
    """비정기 상품 인라인 편집 일괄 저장"""
    try:
        items = [item.dict() for item in data.items]
        result = expected_1p_irregular_product_repo.bulk_update_products(items, user_id=user.user_id)

        # Slack 알림 (비동기)
        try:
            from utils.slack_notifier import send_expected_upload_notification_async
            updated_count = result.get('updated', len(items))
            send_expected_upload_notification_async(
                sales_type="사입(1P)", data_type="비정기",
                total_rows=updated_count, inserted=0, updated=updated_count,
                username=user.username if user else None,
                action="인라인 수정"
            )
        except Exception:
            pass

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 수정 실패: {str(e)}")


@product_router.get("/{product_id}")
async def get_expected_1p_irregular_product_item(product_id: int, user: CurrentUser = Depends(require_permission("Expected1PIrregular", "READ"))):
    """행사 상품 단일 조회"""
    try:
        item = expected_1p_irregular_product_repo.get_by_id(product_id)
        if not item:
            raise HTTPException(404, "행사 상품 데이터를 찾을 수 없습니다")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 상품 조회 실패: {str(e)}")


@product_router.post("")
@log_activity("CREATE", "Expected1PIrregularProduct", id_key="Expected1PIrregularProductID")
async def create_expected_1p_irregular_product(
    data: Expected1PIrregularProductCreate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "CREATE"))
):
    """행사 상품 생성"""
    try:
        # ERPCode → UniqueCode, ProductName 매핑
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT pb.ERPCode, p.UniqueCode, p.Name
                FROM ProductBox pb
                INNER JOIN Product p ON pb.ProductID = p.ProductID
                WHERE pb.ERPCode = ?
            """, (data.ERPCode,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(400, f"존재하지 않는 품목코드: {data.ERPCode}")

        create_data = data.dict(exclude_none=True)
        create_data['UniqueCode'] = row[1]
        create_data['ProductName'] = row[2]
        product_id = expected_1p_irregular_product_repo.create(create_data, user_id=user.user_id)

        return {"IrregularProductID": product_id, "Expected1PIrregularID": data.Expected1PIrregularID, "ERPCode": data.ERPCode}
    except Exception as e:
        raise HTTPException(500, f"행사 상품 생성 실패: {str(e)}")


@product_router.put("/{product_id}")
@log_activity("UPDATE", "Expected1PIrregularProduct", id_key="Expected1PIrregularProductID")
async def update_expected_1p_irregular_product(
    product_id: int,
    data: Expected1PIrregularProductUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "UPDATE"))
):
    """행사 상품 수정"""
    try:
        if not expected_1p_irregular_product_repo.exists(product_id):
            raise HTTPException(404, "행사 상품 데이터를 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = expected_1p_irregular_product_repo.update(product_id, update_data, user_id=user.user_id)
        if not success:
            raise HTTPException(500, "행사 상품 수정 실패")

        return {"IrregularProductID": product_id, **update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 상품 수정 실패: {str(e)}")


@product_router.delete("/{product_id}")
@log_delete("Expected1PIrregularProduct", id_param="product_id")
async def delete_expected_1p_irregular_product(
    product_id: int,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "DELETE"))
):
    """행사 상품 삭제"""
    try:
        if not expected_1p_irregular_product_repo.exists(product_id):
            raise HTTPException(404, "행사 상품 데이터를 찾을 수 없습니다")

        success = expected_1p_irregular_product_repo.delete(product_id)
        if not success:
            raise HTTPException(500, "행사 상품 삭제 실패")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"행사 상품 삭제 실패: {str(e)}")


@product_router.post("/bulk-delete")
@log_bulk_delete("Expected1PIrregularProduct")
async def bulk_delete_expected_1p_irregular_products(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PIrregular", "DELETE"))
):
    """행사 상품 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = expected_1p_irregular_product_repo.bulk_delete(request_body.ids)

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")
