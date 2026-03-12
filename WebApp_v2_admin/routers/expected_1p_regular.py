"""
Expected1P (예상 매출 관리) Router
- 사입 정기 예상 (Expected1PRegularProduct) API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import io
from datetime import datetime
from repositories.expected_1p_regular_repository import Expected1PRegularRepository
from repositories import BrandRepository, ChannelRepository, ProductRepository, ActivityLogRepository
from core import get_db_cursor
from core.dependencies import get_client_ip, CurrentUser
from core import log_activity, log_delete, log_bulk_delete, require_permission
from core.models import BulkDeleteRequest


def _parse_int_list(value):
    if not value:
        return None
    parts = [int(v.strip()) for v in value.split(',') if v.strip()]
    if not parts:
        return None
    return parts if len(parts) > 1 else parts[0]


# ========== 사입 정기 예상 Router ==========
router = APIRouter(prefix="/api/expected/1p/regular", tags=["Expected1PRegular"])

# Repository 인스턴스
expected_1p_regular_repo = Expected1PRegularRepository()
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
        'channel_owner': '오프라인영업',
        'extra_columns': None,
    },
}


# Pydantic Models - 사입 정기 예상
class Expected1PRegularCreate(BaseModel):
    Date: str
    BrandID: int
    BrandName: Optional[str] = None
    ChannelID: int
    ChannelName: Optional[str] = None
    UniqueCode: str
    ProductName: Optional[str] = None
    ExpectedAmount: Optional[float] = None
    ExpectedQuantity: Optional[int] = None
    Notes: Optional[str] = None
    InputMonth: Optional[str] = None
    OliveyoungType: Optional[str] = None


class Expected1PRegularUpdate(BaseModel):
    Date: Optional[str] = None
    BrandID: Optional[int] = None
    BrandName: Optional[str] = None
    ChannelID: Optional[int] = None
    ChannelName: Optional[str] = None
    UniqueCode: Optional[str] = None
    ProductName: Optional[str] = None
    ExpectedAmount: Optional[float] = None
    ExpectedQuantity: Optional[int] = None
    Notes: Optional[str] = None
    InputMonth: Optional[str] = None
    OliveyoungType: Optional[str] = None


class FilterDeleteRequest(BaseModel):
    year_month: str
    brand_id: Optional[int] = None
    channel_id: Optional[int] = None
    input_month: Optional[str] = None


class Expected1PRegularBulkUpdateItem(BaseModel):
    Expected1PRegularID: int
    ExpectedAmount: Optional[float] = None
    ExpectedQuantity: Optional[int] = None
    Notes: Optional[str] = None


class Expected1PRegularBulkUpdateRequest(BaseModel):
    items: List[Expected1PRegularBulkUpdateItem]


# ========== 사입 정기 예상 CRUD ==========

@router.get("")
async def get_expected_1p_regular_list(
    page: int = 1,
    limit: int = 20,
    year_month: Optional[str] = None,
    brand_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    input_month: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "DESC",
    user: CurrentUser = Depends(require_permission("Expected1PRegular", "READ"))
):
    """사입 정기 예상 목록 조회"""
    try:
        ALLOWED_SORT = {
            "Date": "t.[Date]",
            "BrandName": "t.BrandName",
            "ChannelName": "t.ChannelName",
            "UniqueCode": "t.UniqueCode",
            "ProductName": "t.ProductName",
            "ExpectedAmount": "t.ExpectedAmount",
            "ExpectedQuantity": "t.ExpectedQuantity",
        }
        order_by = ALLOWED_SORT.get(sort_by, "t.[Date]")
        order_dir = sort_dir if sort_dir in ("ASC", "DESC") else "DESC"

        filters = {}
        if year_month:
            filters['year_month'] = year_month
        parsed_brand = _parse_int_list(brand_id)
        if parsed_brand is not None:
            filters['brand_id'] = parsed_brand
        parsed_channel = _parse_int_list(channel_id)
        if parsed_channel is not None:
            filters['channel_id'] = parsed_channel
        if input_month:
            filters['input_month'] = input_month

        result = expected_1p_regular_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by=order_by,
            order_dir=order_dir
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"사입 정기 예상 조회 실패: {str(e)}")


@router.get("/year-months")
async def get_expected_1p_regular_year_months(user: CurrentUser = Depends(require_permission("Expected1PRegular", "READ"))):
    """사입 정기 예상 년월 목록 조회"""
    try:
        year_months = expected_1p_regular_repo.get_year_months()
        return {"year_months": year_months}
    except Exception as e:
        raise HTTPException(500, f"년월 목록 조회 실패: {str(e)}")


@router.get("/input-months")
async def get_expected_1p_regular_input_months(
    year_month: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Expected1PRegular", "READ"))
):
    """사입 정기 예상 InputMonth(입력월) 목록 조회"""
    try:
        input_months = expected_1p_regular_repo.get_input_months(year_month)
        return {"input_months": input_months}
    except Exception as e:
        raise HTTPException(500, f"입력월 목록 조회 실패: {str(e)}")


@router.get("/channels")
async def get_expected_1p_regular_channels(
    year_month: str,
    brand_id: Optional[str] = None,
    input_month: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Expected1PRegular", "READ"))
):
    """채널별 사입 정기 예상 요약 조회 (마스터 패널용)"""
    try:
        if not year_month:
            raise HTTPException(400, "년월은 필수입니다")
        channels = expected_1p_regular_repo.get_channels_summary(year_month, _parse_int_list(brand_id), input_month)
        return {"data": channels, "total": len(channels)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"채널 요약 조회 실패: {str(e)}")


@router.get("/channel/{channel_id}/items")
async def get_expected_1p_regular_channel_items(
    channel_id: int,
    year_month: str,
    brand_id: Optional[str] = None,
    input_month: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Expected1PRegular", "READ"))
):
    """특정 채널의 사입 정기 예상 상품 목록 조회 (디테일 패널용)"""
    try:
        if not year_month:
            raise HTTPException(400, "년월은 필수입니다")
        items = expected_1p_regular_repo.get_by_channel(channel_id, year_month, _parse_int_list(brand_id), input_month)
        return {"data": items, "total": len(items)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"채널 상품 목록 조회 실패: {str(e)}")


@router.put("/bulk-update")
@log_activity("UPDATE", "Expected1PRegularProduct")
async def bulk_update_expected_1p_regular(
    request_body: Expected1PRegularBulkUpdateRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PRegular", "UPDATE"))
):
    """사입 정기 예상 인라인 편집 일괄 저장"""
    try:
        if not request_body.items:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        records = [item.dict() for item in request_body.items]
        result = expected_1p_regular_repo.bulk_update_amounts(records, user_id=user.user_id)

        return {
            "message": f"{result['updated']}건 수정 완료",
            "updated": result['updated']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 수정 실패: {str(e)}")


@router.get("/download")
async def download_expected_1p_regular(
    year_month: Optional[str] = None,
    brand_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    channel_ids: Optional[str] = None,
    input_month: Optional[str] = None,
    ids: Optional[str] = None,
    format_type: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Expected1PRegular", "EXPORT"))
):
    """사입 정기 예상 엑셀 양식 다운로드 (신규/수정 통합)"""
    try:
        # 포맷 설정
        format_config = FORMAT_CONFIGS.get(format_type) if format_type else None
        format_name = format_config['name'] if format_config else '사입'
        product_code_config = format_config.get('product_code') if format_config else None
        product_col_name = product_code_config['export_name'] if product_code_config else '품목코드'

        data = []

        # 선택된 ID가 있으면 해당 ID들만 조회
        if ids:
            id_list = [int(id.strip()) for id in ids.split(',') if id.strip()]
            data = expected_1p_regular_repo.get_by_ids(id_list)
        elif channel_ids and year_month:
            # 다중 채널 선택 시 각 채널의 상품을 합산
            ch_id_list = [int(c.strip()) for c in channel_ids.split(',') if c.strip()]
            parsed_brand = _parse_int_list(brand_id)
            for ch_id in ch_id_list:
                items = expected_1p_regular_repo.get_by_channel(ch_id, year_month, parsed_brand, input_month)
                data.extend(items)
        elif year_month or brand_id is not None or channel_id is not None:
            # 필터 조건이 있으면 해당 조건으로 조회
            filters = {}
            if year_month:
                filters['year_month'] = year_month
            parsed_brand = _parse_int_list(brand_id)
            if parsed_brand is not None:
                filters['brand_id'] = parsed_brand
            parsed_channel = _parse_int_list(channel_id)
            if parsed_channel is not None:
                filters['channel_id'] = parsed_channel
            if input_month:
                filters['input_month'] = input_month

            result = expected_1p_regular_repo.get_list(page=1, limit=100000, filters=filters)
            data = result['data']

        # 컬럼 정의 (동적 구성)
        base_export_columns = ['ID(수정X)', '입력월(YYYY-MM)', '날짜(YYYY-MM-01)', '브랜드명', '채널명', product_col_name, '예상금액(VAT포함)', '예상수량']
        base_column_map = {
            'Expected1PRegularID': 'ID(수정X)',
            'InputMonth': '입력월(YYYY-MM)',
            'Date': '날짜(YYYY-MM-01)',
            'BrandName': '브랜드명',
            'ChannelName': '채널명',
            'ERPCode': product_col_name,
            'ExpectedAmount': '예상금액(VAT포함)',
            'ExpectedQuantity': '예상수량',
        }

        # 포맷별 전용 컬럼 삽입 (메모 앞)
        extra_col = format_config.get('extra_columns') if format_config else None
        if extra_col:
            base_export_columns.append(extra_col['export_name'])
            base_column_map[extra_col['internal_name']] = extra_col['export_name']

        # 메모는 항상 마지막
        base_export_columns.append('메모')
        base_column_map['Notes'] = '메모'

        export_columns = base_export_columns

        # 인덱스 동적 계산
        id_column_idx = export_columns.index('ID(수정X)')
        readonly_column_names = ['입력월(YYYY-MM)', '날짜(YYYY-MM-01)', '브랜드명', '채널명', product_col_name]
        readonly_columns = [export_columns.index(name) for name in readonly_column_names]

        if not data:
            df = pd.DataFrame(columns=export_columns)
        else:
            df = pd.DataFrame(data)
            internal_columns = list(base_column_map.keys())
            df = df[[col for col in internal_columns if col in df.columns]]
            df = df.rename(columns=base_column_map)

            # 쿠팡 양식: ERPCode 값을 CoupangSKU로 변환
            if product_code_config and product_col_name in df.columns:
                erp_values = df[product_col_name].dropna().unique().tolist()
                erp_values = [str(v) for v in erp_values if v and str(v) != 'nan']
                if erp_values:
                    erp_to_sku = {}
                    with get_db_cursor(commit=False) as cursor:
                        placeholders = ','.join(['?' for _ in erp_values])
                        cursor.execute(f"""
                            SELECT pb.ERPCode, pb.{product_code_config['db_column']}
                            FROM ProductBox pb
                            WHERE pb.ERPCode IN ({placeholders})
                        """, *erp_values)
                        for row in cursor.fetchall():
                            if row[1]:
                                erp_to_sku[row[0]] = row[1]
                    df[product_col_name] = df[product_col_name].map(lambda x: erp_to_sku.get(x, x))

        # 안내 시트 데이터
        guide_data = [
            [f'[{format_name} 정기 예상 업로드 안내]', ''],
            ['', ''],
            ['■ 업로드 방식', ''],
            ['ID가 있는 행', 'ID 기준으로 해당 데이터를 수정합니다.'],
            ['ID가 없는 행', '날짜+채널+품목코드 기준으로 신규 등록 또는 수정합니다.'],
            ['', ''],
            ['■ 컬럼 설명', ''],
            ['ID(수정X)', '수정할 데이터의 ID (비워두면 신규 등록, 수정 불가)'],
            ['날짜(YYYY-MM-01)', '예상 매출 날짜 (YYYY-MM-01 형식, 월 단위)'],
            ['브랜드명', 'Brand 테이블에 등록된 브랜드명'],
            ['채널명', 'Channel 테이블에 등록된 채널명'],
            [product_col_name, f'Product 테이블에 등록된 {product_col_name} (드롭다운 선택)' if product_code_config else 'ProductBox 테이블에 등록된 품목코드 (ERPCode, 드롭다운 선택)'],
            ['예상금액(VAT포함)', 'VAT 포함 금액 (예: 1000000). VAT제외 금액은 서버에서 자동 계산됩니다.'],
            ['예상수량', '숫자 (예: 100)'],
            ['메모', '메모/참고사항'],
        ]
        if extra_col:
            guide_data.append([extra_col['export_name'], f"{', '.join(extra_col['dropdown_values'])} 중 선택"])
        guide_data += [
            ['', ''],
            ['■ 수정 가능/불가 컬럼', ''],
            ['수정 가능', '예상금액(VAT포함), 예상수량, 메모' + (f", {extra_col['export_name']}" if extra_col else '')],
            ['수정 불가 (검정)', f'입력월, 날짜, 브랜드명, 채널명, {product_col_name}'],
            ['ID(수정X) (빨간색)', '수정할 데이터 식별용 (비워두면 신규 등록)'],
            ['', ''],
            ['■ 주의사항', ''],
            ['1. ID 컬럼을 비워두면 신규 등록으로 처리됩니다.', ''],
            ['2. 동일한 날짜+채널+품목코드 조합이 있으면 기존 데이터가 수정됩니다.', ''],
            ['3. 브랜드명, 채널명, 품목코드는 반드시 DB에 등록된 값이어야 합니다.', ''],
            ['4. 검정색/빨간색 배경 컬럼은 수정해도 반영되지 않습니다.', ''],
        ]
        guide_df = pd.DataFrame(guide_data, columns=['항목', '설명'])

        # 드롭다운용 목록 조회 (사입 1P/2P 채널)
        channels_1p = channel_repo.get_channel_list(contract_type='1P')
        channels_2p = channel_repo.get_channel_list(contract_type='2P')
        channels = channels_1p + channels_2p
        brands = brand_repo.get_all_brands()

        # 포맷별 채널 필터링
        keyword = format_config.get('channel_keyword') if format_config else None
        owner = format_config.get('channel_owner') if format_config else None
        if keyword:
            filtered_channels = [ch for ch in channels if keyword in ch['Name']]
        elif owner:
            filtered_channels = [ch for ch in channels if ch.get('Owner') == owner]
        else:
            filtered_channels = channels
        channel_names = [ch['Name'] for ch in filtered_channels]
        brand_names = [br['Name'] for br in brands]

        # 품목코드/쿠팡SKU 드롭다운용 목록 조회 (Status = 'YES'인 제품만)
        if product_code_config:
            with get_db_cursor(commit=False) as cursor:
                db_col = product_code_config['db_column']
                cursor.execute(f"""
                    SELECT DISTINCT pb.{db_col}
                    FROM ProductBox pb
                    INNER JOIN Product p ON pb.ProductID = p.ProductID
                    WHERE p.Status = 'YES' AND pb.{db_col} IS NOT NULL AND pb.{db_col} != ''
                    ORDER BY pb.{db_col}
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
        sheet_name = f'{format_name} 정기 예상'

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
            guide_df.to_excel(writer, index=False, sheet_name='안내')

            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            # 목록 시트 생성 (드롭다운 소스용)
            list_sheet = workbook.add_worksheet('목록')
            list_sheet.hide()

            # A열: 채널 목록
            for i, name in enumerate(channel_names):
                list_sheet.write(i, 0, name)
            # B열: 브랜드 목록
            for i, name in enumerate(brand_names):
                list_sheet.write(i, 1, name)
            # C열: 품목코드/쿠팡SKU 목록
            for i, code in enumerate(product_codes):
                list_sheet.write(i, 2, code)
            # D열: 전용 컬럼 드롭다운 값 (있으면)
            extra_dropdown_values = []
            if extra_col:
                extra_dropdown_values = extra_col['dropdown_values']
                for i, val in enumerate(extra_dropdown_values):
                    list_sheet.write(i, 3, val)

            # 드롭다운 적용 범위
            max_row = max(len(df) + 100, 1000)

            # 채널명 드롭다운
            ch_col_idx = export_columns.index('채널명')
            if channel_names:
                worksheet.data_validation(1, ch_col_idx, max_row, ch_col_idx, {
                    'validate': 'list',
                    'source': f'=목록!$A$1:$A${len(channel_names)}',
                    'input_message': '채널을 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 브랜드명 드롭다운
            br_col_idx = export_columns.index('브랜드명')
            if brand_names:
                worksheet.data_validation(1, br_col_idx, max_row, br_col_idx, {
                    'validate': 'list',
                    'source': f'=목록!$B$1:$B${len(brand_names)}',
                    'input_message': '브랜드를 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 품목코드/쿠팡SKU 드롭다운
            prod_code_col_idx = export_columns.index(product_col_name)
            if product_codes:
                worksheet.data_validation(1, prod_code_col_idx, max_row, prod_code_col_idx, {
                    'validate': 'list',
                    'source': f'=목록!$C$1:$C${len(product_codes)}',
                    'input_message': f'{product_col_name}를 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 전용 컬럼 드롭다운 (있으면)
            if extra_col and extra_dropdown_values:
                extra_col_idx = export_columns.index(extra_col['export_name'])
                worksheet.data_validation(1, extra_col_idx, max_row, extra_col_idx, {
                    'validate': 'list',
                    'source': f'=목록!$D$1:$D${len(extra_dropdown_values)}',
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
                if col_idx == id_column_idx:
                    worksheet.write(0, col_idx, col_name, id_header_format)
                elif col_idx in readonly_columns:
                    worksheet.write(0, col_idx, col_name, readonly_header_format)
                else:
                    worksheet.write(0, col_idx, col_name, editable_header_format)

            # 데이터 행에 서식 적용
            if len(df) > 0:
                for row_idx in range(len(df)):
                    col_name = export_columns[id_column_idx]
                    if col_name in df.columns:
                        value = df.iloc[row_idx][col_name]
                        worksheet.write(row_idx + 1, id_column_idx, value, id_data_format)

                    for col_idx in readonly_columns:
                        if col_idx < len(export_columns):
                            col_name = export_columns[col_idx]
                            if col_name in df.columns:
                                value = df.iloc[row_idx][col_name]
                                worksheet.write(row_idx + 1, col_idx, value, readonly_data_format)

            # 컬럼 너비 설정
            for i in range(len(export_columns)):
                worksheet.set_column(i, i, 15)

            guide_sheet = writer.sheets['안내']
            guide_sheet.set_column(0, 0, 55)
            guide_sheet.set_column(1, 1, 40)

        output.seek(0)

        format_suffix = f'_{format_type}' if format_type else ''
        filename = f"expected_1p_regular{format_suffix}_{year_month or 'template'}.xlsx"
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


@router.get("/{target_id}")
async def get_expected_1p_regular_item(target_id: int, user: CurrentUser = Depends(require_permission("Expected1PRegular", "READ"))):
    """사입 정기 예상 단일 조회"""
    try:
        item = expected_1p_regular_repo.get_by_id(target_id)
        if not item:
            raise HTTPException(404, "예상 매출 데이터를 찾을 수 없습니다")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"예상 매출 조회 실패: {str(e)}")


@router.post("")
@log_activity("CREATE", "Expected1PRegularProduct", id_key="Expected1PRegularID")
async def create_expected_1p_regular(
    data: Expected1PRegularCreate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PRegular", "CREATE"))
):
    """사입 정기 예상 생성"""
    try:
        target_id = expected_1p_regular_repo.create(data.dict(exclude_none=True), user_id=user.user_id)

        return {"Expected1PRegularID": target_id, "UniqueCode": data.UniqueCode, "Date": data.Date}
    except Exception as e:
        raise HTTPException(500, f"예상 매출 생성 실패: {str(e)}")


@router.put("/{target_id}")
@log_activity("UPDATE", "Expected1PRegularProduct", id_key="Expected1PRegularID")
async def update_expected_1p_regular(
    target_id: int,
    data: Expected1PRegularUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PRegular", "UPDATE"))
):
    """사입 정기 예상 수정"""
    try:
        if not expected_1p_regular_repo.exists(target_id):
            raise HTTPException(404, "예상 매출 데이터를 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = expected_1p_regular_repo.update(target_id, update_data, user_id=user.user_id)
        if not success:
            raise HTTPException(500, "예상 매출 수정 실패")

        return {"Expected1PRegularID": target_id, **update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"예상 매출 수정 실패: {str(e)}")


@router.delete("/{target_id}")
@log_delete("Expected1PRegularProduct", id_param="target_id")
async def delete_expected_1p_regular(
    target_id: int,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PRegular", "DELETE"))
):
    """사입 정기 예상 삭제"""
    try:
        if not expected_1p_regular_repo.exists(target_id):
            raise HTTPException(404, "예상 매출 데이터를 찾을 수 없습니다")

        success = expected_1p_regular_repo.delete(target_id)
        if not success:
            raise HTTPException(500, "예상 매출 삭제 실패")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"예상 매출 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
@log_bulk_delete("Expected1PRegularProduct")
async def bulk_delete_expected_1p_regular(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PRegular", "DELETE"))
):
    """사입 정기 예상 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = expected_1p_regular_repo.bulk_delete(request_body.ids)

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


@router.post("/filter-delete")
@log_activity("BULK_DELETE", "Expected1PRegularProduct")
async def filter_delete_expected_1p_regular(
    request_body: FilterDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Expected1PRegular", "DELETE"))
):
    """필터 조건으로 사입 정기 예상 일괄 삭제"""
    try:
        deleted_count = expected_1p_regular_repo.delete_by_filter(
            year_month=request_body.year_month,
            brand_id=request_body.brand_id,
            channel_id=request_body.channel_id,
            input_month=request_body.input_month
        )

        return {
            "deleted_count": deleted_count,
            "filter": request_body.dict()
        }
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ========== 사입 정기 예상 엑셀 ==========

@router.post("/upload")
async def upload_expected_1p_regular(
    file: UploadFile = File(...),
    input_month: Optional[str] = Form(None),
    request: Request = None,
    user: CurrentUser = Depends(require_permission("Expected1PRegular", "UPLOAD"))
):
    """사입 정기 예상 엑셀 업로드 (input_month: 입력월 YYYY-MM)"""
    try:
        upload_start_time = datetime.now()

        # 파일 확장자 검증
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, "엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        print(f"\n[사입 정기 예상 업로드 시작] {file.filename}")

        # 파일 읽기
        content = await file.read()
        excel_file = io.BytesIO(content)
        df = pd.read_excel(excel_file)
        print(f"   총 {len(df):,}행 로드됨")

        # 컬럼 매핑 (엑셀 컬럼명 → 내부 컬럼명)
        column_map = {
            'ID(수정X)': 'Expected1PRegularID',
            '날짜(YYYY-MM-01)': 'Date',
            '입력월(YYYY-MM)': 'InputMonth',
            '입력월(수정X)': 'InputMonth',
            '브랜드명': 'BrandName',
            '채널명': 'ChannelName',
            '품목코드': 'ERPCode',
            '예상금액(+VAT)': 'ExpectedAmount',
            '예상금액(VAT포함)': 'ExpectedAmount',
            '예상수량': 'ExpectedQuantity',
            '비고': 'Notes',
            '메모': 'Notes',
            '올리브영유형': 'OliveyoungType',
            '쿠팡SKU': 'CoupangSKU'
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
                        FROM ProductBox pb
                        WHERE pb.CoupangSKU = ?
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

        # 필수 컬럼 확인
        required_cols = ['Date', 'BrandName', 'ChannelName', 'ERPCode']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(400, f"필수 컬럼이 없습니다: {missing_cols}")

        # 날짜 변환
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        invalid_dates = df['Date'].isna().sum()
        if invalid_dates > 0:
            raise HTTPException(400, f"날짜 형식이 잘못된 행이 {invalid_dates}개 있습니다")

        # 데이터 타입 변환
        df['ExpectedAmount'] = pd.to_numeric(df['ExpectedAmount'], errors='coerce').fillna(0)
        df['ExpectedQuantity'] = pd.to_numeric(df['ExpectedQuantity'], errors='coerce').fillna(0).astype(int)

        # 문자열 컬럼 공백 제거 (strip)
        df['BrandName'] = df['BrandName'].astype(str).str.strip()
        df['ChannelName'] = df['ChannelName'].astype(str).str.strip()
        df['ERPCode'] = df['ERPCode'].astype(str).str.strip()

        # 에러 수집용 딕셔너리
        errors = {
            'brand': {},      # {name: [행번호들]}
            'channel': {},    # {name: [행번호들]}
            'product': {}     # {code: [행번호들]}
        }

        # 브랜드명 → BrandID 매핑 테이블 생성
        brand_names = df['BrandName'].dropna().unique().tolist()
        brand_names = [n for n in brand_names if n and n != 'nan']
        brand_map = {}
        for name in brand_names:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT BrandID, Name FROM Brand WHERE Name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    brand_map[name] = {'BrandID': row[0], 'BrandName': row[1]}
                else:
                    # 해당 브랜드명이 있는 행 번호 수집 (엑셀 기준 2부터 시작)
                    row_nums = df[df['BrandName'] == name].index.tolist()
                    errors['brand'][name] = [r + 2 for r in row_nums]

        # 채널명 → ChannelID 매핑 테이블 생성 (사입 1P/2P 채널만 허용)
        channel_names = df['ChannelName'].dropna().unique().tolist()
        channel_names = [n for n in channel_names if n and n != 'nan']
        channel_map = {}
        for name in channel_names:
            with get_db_cursor() as cursor:
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

        # 품목코드(ERPCode) → UniqueCode, ProductName 매핑 테이블 생성
        erp_codes = df['ERPCode'].dropna().unique().tolist()
        erp_codes = [c for c in erp_codes if c and c != 'nan']
        product_map = {}
        for code in erp_codes:
            with get_db_cursor() as cursor:
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

        # 에러가 있으면 모두 모아서 반환
        if errors['brand'] or errors['channel'] or errors['product']:
            error_messages = []
            for name, rows in errors['brand'].items():
                error_messages.append(f"존재하지 않는 브랜드명: {name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for name, rows in errors['channel'].items():
                error_messages.append(f"존재하지 않는 채널명: {name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for code, rows in errors['product'].items():
                error_messages.append(f"존재하지 않는 품목코드: {code} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            raise HTTPException(400, "\n".join(error_messages))

        # InputMonth 결정: 엑셀 컬럼 > 폼 파라미터 > 현재 월
        default_input_month = input_month or datetime.now().strftime('%Y-%m')

        # 레코드 준비
        records = []
        for _, row in df.iterrows():
            brand_name = row['BrandName'] if pd.notna(row['BrandName']) and row['BrandName'] != 'nan' else None
            channel_name = row['ChannelName'] if pd.notna(row['ChannelName']) and row['ChannelName'] != 'nan' else None
            erp_code = row['ERPCode'] if pd.notna(row['ERPCode']) and row['ERPCode'] != 'nan' else None

            brand_info = brand_map.get(brand_name, {})
            channel_info = channel_map.get(channel_name, {})
            product_info = product_map.get(erp_code, {})

            # ID가 있으면 포함 (수정 양식인 경우)
            target_id = None
            if 'Expected1PRegularID' in row and pd.notna(row['Expected1PRegularID']):
                target_id = int(row['Expected1PRegularID'])

            # InputMonth: 엑셀 컬럼이 있으면 사용, 없으면 기본값
            row_input_month = default_input_month
            if 'InputMonth' in row and pd.notna(row.get('InputMonth')) and str(row['InputMonth']).strip():
                row_input_month = str(row['InputMonth']).strip()

            records.append({
                'Expected1PRegularID': target_id,
                'Date': row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else None,
                'BrandID': brand_info.get('BrandID'),
                'BrandName': brand_info.get('BrandName'),
                'ChannelID': channel_info.get('ChannelID'),
                'ChannelName': channel_info.get('ChannelName'),
                'ERPCode': erp_code,
                'UniqueCode': product_info.get('UniqueCode'),
                'ProductName': product_info.get('ProductName'),
                'ExpectedAmount': float(row['ExpectedAmount']) if pd.notna(row.get('ExpectedAmount')) else 0,
                'ExpectedQuantity': int(row['ExpectedQuantity']) if pd.notna(row.get('ExpectedQuantity')) else 0,
                'Notes': str(row['Notes']) if pd.notna(row.get('Notes')) else None,
                'InputMonth': row_input_month,
                'OliveyoungType': str(row['OliveyoungType']) if 'OliveyoungType' in row and pd.notna(row.get('OliveyoungType')) else None,
            })

        # UPSERT 실행
        result = expected_1p_regular_repo.bulk_upsert(records)

        upload_end_time = datetime.now()
        duration = (upload_end_time - upload_start_time).total_seconds()

        # 중복 데이터 체크 - 에러 반환
        duplicates = result.get('duplicates', [])
        if duplicates:
            error_messages = []
            for dup in duplicates[:10]:  # 최대 10개까지 표시
                error_messages.append(
                    f"행 {dup['row']}: 중복 데이터 (날짜: {dup['date']}, 상품코드: {dup['unique_code']}, 채널: {dup['channel_name']})"
                )
            if len(duplicates) > 10:
                error_messages.append(f"... 외 {len(duplicates) - 10}건 더 있음")
            raise HTTPException(400, "중복 데이터가 있습니다. ID 없이 신규 입력 시 기존 데이터와 중복될 수 없습니다.\n" + "\n".join(error_messages))

        # 활동 로그
        if user and request:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="Expected1PRegularProduct",
                details={
                    "action": "EXCEL_UPLOAD",
                    "filename": file.filename,
                    "total_rows": len(df),
                    "inserted": result['inserted'],
                    "updated": result['updated'],
                    "duration_seconds": duration
                },
                ip_address=get_client_ip(request)
            )

        print(f"   업로드 완료: {result['inserted']}건 삽입, {result['updated']}건 수정")

        # Slack 알림 (비동기 - 응답 지연 없음)
        try:
            from utils.slack_notifier import send_expected_upload_notification_async
            send_expected_upload_notification_async(
                sales_type="사입(1P)",
                data_type="정기",
                total_rows=len(df),
                inserted=result['inserted'],
                updated=result['updated'],
                input_month=default_input_month,
                username=user.username if user else None
            )
        except Exception:
            pass

        # 이전 입력월 대비 변동 감지
        try:
            _detect_upload_diff_1p_regular(default_input_month, records, user)
        except Exception:
            pass

        return {
            "message": "업로드 완료",
            "total_rows": len(df),
            "inserted": result['inserted'],
            "updated": result['updated'],
            "duration_seconds": duration
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"업로드 실패: {str(e)}")


def _detect_upload_diff_1p_regular(current_input_month: str, records: list, user):
    """업로드된 데이터와 이전 입력월 데이터를 비교하여 변동 감지 알림"""
    from core.database import get_db_cursor
    from utils.slack_notifier import send_upload_diff_notification_async
    from datetime import datetime

    try:
        dt = datetime.strptime(current_input_month, '%Y-%m')
        if dt.month == 1:
            prev_dt = dt.replace(year=dt.year - 1, month=12)
        else:
            prev_dt = dt.replace(month=dt.month - 1)
        previous_input_month = prev_dt.strftime('%Y-%m')
    except Exception:
        return

    upload_map = {}
    for rec in records:
        date_val = rec.get('Date')
        if hasattr(date_val, 'strftime'):
            ym = date_val.strftime('%Y-%m')
        else:
            ym = str(date_val)[:7]
        key = (ym, rec.get('ChannelName', ''), rec.get('UniqueCode', ''))
        upload_map[key] = {
            'amount': float(rec.get('ExpectedAmount', 0) or 0),
            'quantity': int(rec.get('ExpectedQuantity', 0) or 0),
            'product_name': rec.get('ProductName', ''),
        }

    if not upload_map:
        return

    diffs = []
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT FORMAT([Date], 'yyyy-MM') AS YearMonth, ChannelName, UniqueCode,
                   ISNULL(ExpectedAmount, 0), ISNULL(ExpectedQuantity, 0), ProductName
            FROM [dbo].[Expected1PRegularProduct]
            WHERE InputMonth = ?
        """, previous_input_month)

        prev_map = {}
        for row in cursor.fetchall():
            key = (row[0], row[1], row[2])
            prev_map[key] = {
                'amount': float(row[3]),
                'quantity': int(row[4]),
                'product_name': row[5] or '',
            }

    for key, curr in upload_map.items():
        prev = prev_map.get(key)
        if prev and (prev['amount'] != curr['amount'] or prev['quantity'] != curr['quantity']):
            diffs.append({
                'unique_code': key[2],
                'product_name': curr['product_name'] or prev.get('product_name', ''),
                'channel': key[1],
                'year_month': key[0],
                'prev_amount': prev['amount'],
                'curr_amount': curr['amount'],
                'prev_qty': prev['quantity'],
                'curr_qty': curr['quantity'],
            })

    if diffs:
        send_upload_diff_notification_async(
            sales_type="사입(1P)",
            data_type="정기",
            current_input_month=current_input_month,
            previous_input_month=previous_input_month,
            diffs=diffs,
            username=user.username if user else None,
        )
