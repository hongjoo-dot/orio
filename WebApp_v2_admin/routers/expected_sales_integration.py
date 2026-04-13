"""
예상 판매량 통합 조회 Router
- 위탁(3P) 정기/비정기, 사입(1P) 정기/비정기, 불출 데이터를 통합 조회
- 피벗 테이블: 행=브랜드/채널/상품, 열=연월
- 읽기 전용 (조회 + 엑셀 다운로드)
"""

from fastapi import APIRouter, Query, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from collections import OrderedDict
from urllib.parse import quote
import io
from core import get_db_cursor, log_activity
from core.dependencies import get_current_user, CurrentUser, require_permission
from core.changelog import log_changes
from utils.helpers import calculate_amount_ex_vat

router = APIRouter(prefix="/api/expected-sales-integration", tags=["ExpectedSalesIntegration"])


def _parse_multi(value: str) -> list:
    """콤마 구분 문자열을 리스트로 변환 (빈 값 제거)"""
    if not value:
        return []
    return [v.strip() for v in value.split(',') if v.strip()]


def _get_owner_channels(owner: str) -> list:
    """Owner 값으로 소유 채널명 목록 조회 (콤마 구분 다중값 지원)"""
    if not owner:
        return []
    owners = _parse_multi(owner)
    if not owners:
        return []
    placeholders = ','.join(['?' for _ in owners])
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(f"SELECT Name FROM Channel WHERE Owner IN ({placeholders})", *owners)
        return [row[0] for row in cursor.fetchall()]


def _add_in_filter(where_list, params, value_str, column_expr):
    """콤마 구분 문자열을 IN 필터로 WHERE 절에 추가"""
    if not value_str:
        return
    values = _parse_multi(value_str)
    if not values:
        return
    placeholders = ','.join(['?' for _ in values])
    where_list.append(f"{column_expr} IN ({placeholders})")
    params.extend(values)


def _add_owner_filter(where_list, params, owner_channels, channel_expr):
    """owner_channels IN 필터를 WHERE 절에 추가"""
    if owner_channels:
        placeholders = ','.join(['?' for _ in owner_channels])
        where_list.append(f"{channel_expr} IN ({placeholders})")
        params.extend(owner_channels)


def _build_union_query(
    year_month_from: str, year_month_to: str,
    input_month: Optional[str] = None,
    brand: Optional[str] = None,
    channel: Optional[str] = None,
    owner_channels: Optional[list] = None
):
    """UNION ALL 쿼리 및 파라미터 빌드 (연월 범위)"""
    params = []

    # --- 3P 정기 ---
    w3r = ["FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    if input_month:
        w3r.append("t.InputMonth = ?")
        params.append(input_month)
    _add_in_filter(w3r, params, brand, "t.BrandName")
    _add_in_filter(w3r, params, channel, "t.ChannelName")
    _add_owner_filter(w3r, params, owner_channels, "t.ChannelName")
    q3r = f"""
        SELECT FORMAT(t.[Date], 'yyyy-MM') AS YearMonth,
               t.BrandName, t.ChannelName, t.UniqueCode, t.ProductName,
               t.ExpectedAmount, t.ExpectedQuantity
        FROM Expected3PRegularProduct t
        WHERE {' AND '.join(w3r)}
    """

    # --- 3P 비정기 ---
    w3i = ["FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    if input_month:
        w3i.append("p.InputMonth = ?")
        params.append(input_month)
    _add_in_filter(w3i, params, brand, "p.BrandName")
    _add_in_filter(w3i, params, channel, "p.ChannelName")
    _add_owner_filter(w3i, params, owner_channels, "p.ChannelName")
    q3i = f"""
        SELECT FORMAT(p.StartDate, 'yyyy-MM') AS YearMonth,
               p.BrandName, p.ChannelName, pp.UniqueCode, pp.ProductName,
               pp.ExpectedSalesAmount AS ExpectedAmount, pp.ExpectedQuantity
        FROM Expected3PIrregularProduct pp
        INNER JOIN Expected3PIrregular p ON pp.Expected3PIrregularID = p.Expected3PIrregularID
        WHERE {' AND '.join(w3i)}
    """

    # --- 1P 정기 ---
    w1r = ["FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    if input_month:
        w1r.append("t.InputMonth = ?")
        params.append(input_month)
    _add_in_filter(w1r, params, brand, "t.BrandName")
    _add_in_filter(w1r, params, channel, "t.ChannelName")
    _add_owner_filter(w1r, params, owner_channels, "t.ChannelName")
    q1r = f"""
        SELECT FORMAT(t.[Date], 'yyyy-MM') AS YearMonth,
               t.BrandName, t.ChannelName, t.UniqueCode, t.ProductName,
               t.ExpectedAmount, t.ExpectedQuantity
        FROM Expected1PRegularProduct t
        WHERE {' AND '.join(w1r)}
    """

    # --- 1P 비정기 ---
    w1i = ["FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    if input_month:
        w1i.append("p.InputMonth = ?")
        params.append(input_month)
    _add_in_filter(w1i, params, brand, "p.BrandName")
    _add_in_filter(w1i, params, channel, "p.ChannelName")
    _add_owner_filter(w1i, params, owner_channels, "p.ChannelName")
    q1i = f"""
        SELECT FORMAT(p.StartDate, 'yyyy-MM') AS YearMonth,
               p.BrandName, p.ChannelName, pp.UniqueCode, pp.ProductName,
               pp.ExpectedSalesAmount AS ExpectedAmount, pp.ExpectedQuantity
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        WHERE {' AND '.join(w1i)}
    """

    # --- 불출 ---
    # 채널 필터에 '불출'이 포함되지 않으면 불출 서브쿼리 제외
    # owner_channels 필터 활성 시 불출 제외 (불출은 채널 소유 개념 없음)
    channel_list = _parse_multi(channel) if channel else []
    include_withdrawal = (not channel_list or '불출' in channel_list) and not owner_channels
    if include_withdrawal:
        wwp = ["FORMAT(w.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
        params.extend([year_month_from, year_month_to])
        if input_month:
            wwp.append("w.InputMonth = ?")
            params.append(input_month)
        _add_in_filter(wwp, params, brand, "b.Name")
        qwp = f"""
            SELECT FORMAT(w.[Date], 'yyyy-MM') AS YearMonth,
                   ISNULL(b.Name, N'미분류') AS BrandName,
                   N'불출' AS ChannelName,
                   w.UniqueCode, w.ProductName,
                   NULL AS ExpectedAmount, w.PlannedQty AS ExpectedQuantity
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            WHERE {' AND '.join(wwp)}
        """

    # UNION ALL 조합
    sub_queries = [q3r, q3i, q1r, q1i]
    if include_withdrawal:
        sub_queries.append(qwp)

    full_query = f"""
        SELECT YearMonth, BrandName, ChannelName, UniqueCode, ProductName,
               SUM(ISNULL(ExpectedAmount, 0)) AS TotalAmount,
               SUM(ISNULL(ExpectedQuantity, 0)) AS TotalQuantity
        FROM (
            {' UNION ALL '.join(sub_queries)}
        ) AS Combined
        GROUP BY YearMonth, BrandName, ChannelName, UniqueCode, ProductName
        ORDER BY BrandName, ChannelName, UniqueCode, YearMonth
    """

    return full_query, params


def _pivot_data(rows):
    """SQL 결과를 피벗 데이터로 변환 (열=연월)"""
    year_months_set = OrderedDict()
    product_map = OrderedDict()

    for row in rows:
        ym, brand, channel, code, name, amount, qty = row
        brand = brand or '미분류'
        channel = channel or '미분류'
        code = code or ''
        name = name or ''
        amount = float(amount or 0)
        qty = int(qty or 0)

        year_months_set[ym] = True
        key = (brand, channel, code, name)

        if key not in product_map:
            product_map[key] = {
                'brand': brand,
                'channel': channel,
                'code': code,
                'name': name,
                'months': {},
                'totalAmount': 0,
                'totalQuantity': 0,
            }

        entry = product_map[key]
        if ym not in entry['months']:
            entry['months'][ym] = {'amount': 0, 'quantity': 0}

        entry['months'][ym]['amount'] += amount
        entry['months'][ym]['quantity'] += qty
        entry['totalAmount'] += amount
        entry['totalQuantity'] += qty

    year_months = sorted(year_months_set.keys())
    data = list(product_map.values())

    return year_months, data


@router.get("/data")
async def get_integration_data(
    year_month_from: str = Query(..., description="시작 연월 (YYYY-MM)"),
    year_month_to: str = Query(..., description="종료 연월 (YYYY-MM)"),
    input_month: Optional[str] = Query(None, description="입력월"),
    brand: Optional[str] = Query(None, description="브랜드"),
    channel: Optional[str] = Query(None, description="채널"),
    owner: Optional[str] = Query(None, description="채널 Owner 필터"),
    user: CurrentUser = Depends(get_current_user)
):
    """통합 예상 판매량 피벗 데이터 조회 (열=연월)"""
    oc = _get_owner_channels(owner) if owner else None
    if owner and not oc:
        return {"year_months": [], "data": []}
    query, params = _build_union_query(year_month_from, year_month_to, input_month, brand, channel, oc)

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        rows = cursor.fetchall()

    year_months, data = _pivot_data(rows)
    return {"year_months": year_months, "data": data}


@router.get("/year-months")
async def get_year_months(
    input_month: Optional[str] = Query(None, description="입력월 필터"),
    owner: Optional[str] = Query(None, description="채널 Owner 필터"),
    user: CurrentUser = Depends(get_current_user)
):
    """데이터가 존재하는 연월 목록 (입력월 기준 종속 필터)"""
    oc = _get_owner_channels(owner) if owner else None
    if owner and not oc:
        return []

    params = []
    subs = []

    # 3P 정기
    w = ["1=1"]
    if input_month:
        w.append("t.InputMonth = ?"); params.append(input_month)
    _add_owner_filter(w, params, oc, "t.ChannelName")
    subs.append(f"SELECT FORMAT(t.[Date],'yyyy-MM') AS ym FROM Expected3PRegularProduct t WHERE {' AND '.join(w)}")

    # 3P 비정기
    w = ["1=1"]
    if input_month:
        w.append("p.InputMonth = ?"); params.append(input_month)
    _add_owner_filter(w, params, oc, "p.ChannelName")
    subs.append(f"SELECT FORMAT(p.StartDate,'yyyy-MM') AS ym FROM Expected3PIrregular p WHERE {' AND '.join(w)}")

    # 1P 정기
    w = ["1=1"]
    if input_month:
        w.append("t.InputMonth = ?"); params.append(input_month)
    _add_owner_filter(w, params, oc, "t.ChannelName")
    subs.append(f"SELECT FORMAT(t.[Date],'yyyy-MM') AS ym FROM Expected1PRegularProduct t WHERE {' AND '.join(w)}")

    # 1P 비정기
    w = ["1=1"]
    if input_month:
        w.append("p.InputMonth = ?"); params.append(input_month)
    _add_owner_filter(w, params, oc, "p.ChannelName")
    subs.append(f"SELECT FORMAT(p.StartDate,'yyyy-MM') AS ym FROM Expected1PIrregular p WHERE {' AND '.join(w)}")

    # 불출 (owner 필터 시 제외)
    if not oc:
        w = ["1=1"]
        if input_month:
            w.append("w.InputMonth = ?"); params.append(input_month)
        subs.append(f"SELECT FORMAT(w.[Date],'yyyy-MM') AS ym FROM WithdrawalPlan w WHERE {' AND '.join(w)}")

    query = f"SELECT DISTINCT ym FROM ({' UNION '.join(subs)}) AS A WHERE ym IS NOT NULL ORDER BY ym DESC"
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        return [row[0] for row in cursor.fetchall()]


@router.get("/input-months")
async def get_input_months(
    year_month_from: Optional[str] = Query(None, description="시작 연월"),
    year_month_to: Optional[str] = Query(None, description="종료 연월"),
    owner: Optional[str] = Query(None, description="채널 Owner 필터"),
    user: CurrentUser = Depends(get_current_user)
):
    """입력월 목록 (연월 범위 선택 시 해당 범위만, 없으면 전체)"""
    oc = _get_owner_channels(owner) if owner else None
    if owner and not oc:
        return []

    has_range = year_month_from and year_month_to
    params = []
    subs = []

    # 3P 정기
    w = ["t.InputMonth IS NOT NULL"]
    if has_range:
        w.append("FORMAT(t.[Date],'yyyy-MM') BETWEEN ? AND ?"); params.extend([year_month_from, year_month_to])
    _add_owner_filter(w, params, oc, "t.ChannelName")
    subs.append(f"SELECT t.InputMonth AS im FROM Expected3PRegularProduct t WHERE {' AND '.join(w)}")

    # 3P 비정기
    w = ["p.InputMonth IS NOT NULL"]
    if has_range:
        w.append("FORMAT(p.StartDate,'yyyy-MM') BETWEEN ? AND ?"); params.extend([year_month_from, year_month_to])
    _add_owner_filter(w, params, oc, "p.ChannelName")
    subs.append(f"SELECT p.InputMonth AS im FROM Expected3PIrregular p WHERE {' AND '.join(w)}")

    # 1P 정기
    w = ["t.InputMonth IS NOT NULL"]
    if has_range:
        w.append("FORMAT(t.[Date],'yyyy-MM') BETWEEN ? AND ?"); params.extend([year_month_from, year_month_to])
    _add_owner_filter(w, params, oc, "t.ChannelName")
    subs.append(f"SELECT t.InputMonth AS im FROM Expected1PRegularProduct t WHERE {' AND '.join(w)}")

    # 1P 비정기
    w = ["p.InputMonth IS NOT NULL"]
    if has_range:
        w.append("FORMAT(p.StartDate,'yyyy-MM') BETWEEN ? AND ?"); params.extend([year_month_from, year_month_to])
    _add_owner_filter(w, params, oc, "p.ChannelName")
    subs.append(f"SELECT p.InputMonth AS im FROM Expected1PIrregular p WHERE {' AND '.join(w)}")

    # 불출 (owner 필터 시 제외)
    if not oc:
        w = ["w.InputMonth IS NOT NULL"]
        if has_range:
            w.append("FORMAT(w.[Date],'yyyy-MM') BETWEEN ? AND ?"); params.extend([year_month_from, year_month_to])
        subs.append(f"SELECT w.InputMonth AS im FROM WithdrawalPlan w WHERE {' AND '.join(w)}")

    query = f"SELECT DISTINCT im FROM ({' UNION '.join(subs)}) AS A WHERE im IS NOT NULL ORDER BY im DESC"
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        return [row[0] for row in cursor.fetchall()]


@router.get("/brands")
async def get_brands(
    year_month_from: str = Query(..., description="시작 연월"),
    year_month_to: str = Query(..., description="종료 연월"),
    owner: Optional[str] = Query(None, description="채널 Owner 필터"),
    user: CurrentUser = Depends(get_current_user)
):
    """연월 범위 기준 브랜드 목록"""
    oc = _get_owner_channels(owner) if owner else None
    if owner and not oc:
        return []

    params = []
    subs = []

    # 3P 정기
    w = ["FORMAT(t.[Date],'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    _add_owner_filter(w, params, oc, "t.ChannelName")
    subs.append(f"SELECT t.BrandName AS bn FROM Expected3PRegularProduct t WHERE {' AND '.join(w)}")

    # 3P 비정기
    w = ["FORMAT(p.StartDate,'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    _add_owner_filter(w, params, oc, "p.ChannelName")
    subs.append(f"SELECT p.BrandName AS bn FROM Expected3PIrregular p WHERE {' AND '.join(w)}")

    # 1P 정기
    w = ["FORMAT(t.[Date],'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    _add_owner_filter(w, params, oc, "t.ChannelName")
    subs.append(f"SELECT t.BrandName AS bn FROM Expected1PRegularProduct t WHERE {' AND '.join(w)}")

    # 1P 비정기
    w = ["FORMAT(p.StartDate,'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    _add_owner_filter(w, params, oc, "p.ChannelName")
    subs.append(f"SELECT p.BrandName AS bn FROM Expected1PIrregular p WHERE {' AND '.join(w)}")

    # 불출 (owner 필터 시 제외)
    if not oc:
        w = ["FORMAT(w.[Date],'yyyy-MM') BETWEEN ? AND ?"]
        params.extend([year_month_from, year_month_to])
        subs.append(f"""SELECT ISNULL(b.Name, N'미분류') AS bn
            FROM WithdrawalPlan w LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID WHERE {' AND '.join(w)}""")

    query = f"SELECT DISTINCT bn FROM ({' UNION '.join(subs)}) AS A WHERE bn IS NOT NULL ORDER BY bn"
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        return [row[0] for row in cursor.fetchall()]


@router.get("/channels")
async def get_channels(
    year_month_from: str = Query(..., description="시작 연월"),
    year_month_to: str = Query(..., description="종료 연월"),
    owner: Optional[str] = Query(None, description="채널 Owner 필터"),
    user: CurrentUser = Depends(get_current_user)
):
    """연월 범위 기준 채널 목록"""
    oc = _get_owner_channels(owner) if owner else None
    if owner and not oc:
        return []

    params = []
    subs = []

    # 3P 정기
    w = ["FORMAT(t.[Date],'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    _add_owner_filter(w, params, oc, "t.ChannelName")
    subs.append(f"SELECT t.ChannelName AS cn FROM Expected3PRegularProduct t WHERE {' AND '.join(w)}")

    # 3P 비정기
    w = ["FORMAT(p.StartDate,'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    _add_owner_filter(w, params, oc, "p.ChannelName")
    subs.append(f"SELECT p.ChannelName AS cn FROM Expected3PIrregular p WHERE {' AND '.join(w)}")

    # 1P 정기
    w = ["FORMAT(t.[Date],'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    _add_owner_filter(w, params, oc, "t.ChannelName")
    subs.append(f"SELECT t.ChannelName AS cn FROM Expected1PRegularProduct t WHERE {' AND '.join(w)}")

    # 1P 비정기
    w = ["FORMAT(p.StartDate,'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    _add_owner_filter(w, params, oc, "p.ChannelName")
    subs.append(f"SELECT p.ChannelName AS cn FROM Expected1PIrregular p WHERE {' AND '.join(w)}")

    # 불출 (owner 필터 시 제외)
    if not oc:
        w = ["FORMAT(w.[Date],'yyyy-MM') BETWEEN ? AND ?"]
        params.extend([year_month_from, year_month_to])
        subs.append(f"SELECT N'불출' AS cn FROM WithdrawalPlan w WHERE {' AND '.join(w)}")

    query = f"SELECT DISTINCT cn FROM ({' UNION '.join(subs)}) AS A WHERE cn IS NOT NULL ORDER BY cn"
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        return [row[0] for row in cursor.fetchall()]


@router.get("/owners")
async def get_owners(
    user: CurrentUser = Depends(get_current_user)
):
    """Channel.Owner DISTINCT 목록 조회"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT DISTINCT Owner FROM Channel WHERE Owner IS NOT NULL AND Owner != '' ORDER BY Owner"
        )
        return [row[0] for row in cursor.fetchall()]


@router.get("/download")
async def download_excel(
    year_month_from: str = Query(..., description="시작 연월"),
    year_month_to: str = Query(..., description="종료 연월"),
    input_month: Optional[str] = Query(None, description="입력월"),
    brand: Optional[str] = Query(None, description="브랜드"),
    channel: Optional[str] = Query(None, description="채널"),
    owner: Optional[str] = Query(None, description="채널 Owner 필터"),
    user: CurrentUser = Depends(get_current_user)
):
    """통합 예상 판매량 엑셀 다운로드 (피벗 형태, 열=연월)"""
    import xlsxwriter

    oc = _get_owner_channels(owner) if owner else None
    query, params = _build_union_query(year_month_from, year_month_to, input_month, brand, channel, oc)

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        rows = cursor.fetchall()

    year_months, data = _pivot_data(rows)

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('통합 조회')

    # 스타일
    header_fmt = workbook.add_format({
        'bold': True, 'bg_color': '#4472C4', 'font_color': 'white',
        'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center'
    })
    num_fmt = workbook.add_format({'num_format': '#,##0', 'border': 1})
    text_fmt = workbook.add_format({'border': 1})
    total_header_fmt = workbook.add_format({
        'bold': True, 'bg_color': '#E2EFDA', 'border': 1,
        'text_wrap': True, 'valign': 'vcenter', 'align': 'center'
    })
    total_num_fmt = workbook.add_format({
        'num_format': '#,##0', 'border': 1, 'bold': True, 'bg_color': '#E2EFDA'
    })

    # 헤더 작성
    headers = ['브랜드', '채널', '상품명']
    header_fmts_list = [header_fmt] * 3
    for ym in year_months:
        headers.extend([f'{ym}(매출)', f'{ym}(수량)'])
        header_fmts_list.extend([header_fmt, header_fmt])
    headers.extend(['합계(매출)', '합계(수량)'])
    header_fmts_list.extend([total_header_fmt, total_header_fmt])

    for i, h in enumerate(headers):
        worksheet.write(0, i, h, header_fmts_list[i])

    # 데이터 작성
    for row_idx, item in enumerate(data, start=1):
        worksheet.write(row_idx, 0, item['brand'], text_fmt)
        worksheet.write(row_idx, 1, item['channel'], text_fmt)
        worksheet.write(row_idx, 2, item['name'], text_fmt)

        col = 3
        for ym in year_months:
            ym_data = item['months'].get(ym, {'amount': 0, 'quantity': 0})
            worksheet.write(row_idx, col, ym_data['amount'], num_fmt)
            worksheet.write(row_idx, col + 1, ym_data['quantity'], num_fmt)
            col += 2

        worksheet.write(row_idx, col, item['totalAmount'], total_num_fmt)
        worksheet.write(row_idx, col + 1, item['totalQuantity'], total_num_fmt)

    # 열 너비
    worksheet.set_column(0, 0, 12)
    worksheet.set_column(1, 1, 14)
    worksheet.set_column(2, 2, 25)
    if len(headers) > 3:
        worksheet.set_column(3, len(headers) - 1, 14)

    workbook.close()
    output.seek(0)

    filename = f"예상판매량_통합_{year_month_from}~{year_month_to}"
    if input_month:
        filename += f"_입력월{input_month}"
    if brand:
        filename += f"_{brand}"
    if channel:
        filename += f"_{channel}"
    filename += ".xlsx"

    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{quote(filename)}"}
    )


# ========== BOM 분해 ==========

def _build_bom_query(
    year_month_from: str, year_month_to: str,
    input_month: Optional[str] = None,
    brand: Optional[str] = None,
    channel: Optional[str] = None,
    owner_channels: Optional[list] = None
):
    """BOM 분해 UNION ALL 쿼리 빌드 (단품 pass-through + 세트 분해, 불출 포함)"""
    params = []
    sub_queries = []

    def _reg_where(alias):
        w = [f"FORMAT({alias}.[Date],'yyyy-MM') BETWEEN ? AND ?"]
        p = [year_month_from, year_month_to]
        if input_month:
            w.append(f"{alias}.InputMonth = ?"); p.append(input_month)
        _add_in_filter(w, p, brand, f"{alias}.BrandName")
        _add_in_filter(w, p, channel, f"{alias}.ChannelName")
        if owner_channels:
            ph = ','.join(['?' for _ in owner_channels])
            w.append(f"{alias}.ChannelName IN ({ph})")
            p.extend(owner_channels)
        return ' AND '.join(w), p

    def _irreg_where(pa):
        w = [f"FORMAT({pa}.StartDate,'yyyy-MM') BETWEEN ? AND ?"]
        p = [year_month_from, year_month_to]
        if input_month:
            w.append(f"{pa}.InputMonth = ?"); p.append(input_month)
        _add_in_filter(w, p, brand, f"{pa}.BrandName")
        _add_in_filter(w, p, channel, f"{pa}.ChannelName")
        if owner_channels:
            ph = ','.join(['?' for _ in owner_channels])
            w.append(f"{pa}.ChannelName IN ({ph})")
            p.extend(owner_channels)
        return ' AND '.join(w), p

    # --- 3P 정기 단품 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT FORMAT(e.[Date],'yyyy-MM') AS YearMonth,
               e.BrandName, e.ChannelName, e.UniqueCode, e.ProductName,
               pb.ERPCode,
               e.ExpectedQuantity AS ComponentQuantity
        FROM Expected3PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        LEFT JOIN ProductBox pb ON pr.ProductID = pb.ProductID
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 3P 정기 세트 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT FORMAT(e.[Date],'yyyy-MM') AS YearMonth,
               e.BrandName, e.ChannelName, cp.UniqueCode, cp.Name AS ProductName,
               pb.ERPCode,
               e.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS ComponentQuantity
        FROM Expected3PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        LEFT JOIN ProductBox pb ON cp.ProductID = pb.ProductID
        WHERE {ws}
    """)

    # --- 3P 비정기 단품 ---
    ws, wp = _irreg_where('p')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT FORMAT(p.StartDate,'yyyy-MM') AS YearMonth,
               p.BrandName, p.ChannelName, pp.UniqueCode, pp.ProductName,
               pb.ERPCode,
               pp.ExpectedQuantity AS ComponentQuantity
        FROM Expected3PIrregularProduct pp
        INNER JOIN Expected3PIrregular p ON pp.Expected3PIrregularID = p.Expected3PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        LEFT JOIN ProductBox pb ON pr.ProductID = pb.ProductID
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 3P 비정기 세트 ---
    ws, wp = _irreg_where('p')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT FORMAT(p.StartDate,'yyyy-MM') AS YearMonth,
               p.BrandName, p.ChannelName, cp.UniqueCode, cp.Name AS ProductName,
               pb.ERPCode,
               pp.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS ComponentQuantity
        FROM Expected3PIrregularProduct pp
        INNER JOIN Expected3PIrregular p ON pp.Expected3PIrregularID = p.Expected3PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        LEFT JOIN ProductBox pb ON cp.ProductID = pb.ProductID
        WHERE {ws}
    """)

    # --- 1P 정기 단품 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT FORMAT(e.[Date],'yyyy-MM') AS YearMonth,
               e.BrandName, e.ChannelName, e.UniqueCode, e.ProductName,
               pb.ERPCode,
               e.ExpectedQuantity AS ComponentQuantity
        FROM Expected1PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        LEFT JOIN ProductBox pb ON pr.ProductID = pb.ProductID
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 1P 정기 세트 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT FORMAT(e.[Date],'yyyy-MM') AS YearMonth,
               e.BrandName, e.ChannelName, cp.UniqueCode, cp.Name AS ProductName,
               pb.ERPCode,
               e.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS ComponentQuantity
        FROM Expected1PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        LEFT JOIN ProductBox pb ON cp.ProductID = pb.ProductID
        WHERE {ws}
    """)

    # --- 1P 비정기 단품 ---
    ws, wp = _irreg_where('p')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT FORMAT(p.StartDate,'yyyy-MM') AS YearMonth,
               p.BrandName, p.ChannelName, pp.UniqueCode, pp.ProductName,
               pb.ERPCode,
               pp.ExpectedQuantity AS ComponentQuantity
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        LEFT JOIN ProductBox pb ON pr.ProductID = pb.ProductID
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 1P 비정기 세트 ---
    ws, wp = _irreg_where('p')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT FORMAT(p.StartDate,'yyyy-MM') AS YearMonth,
               p.BrandName, p.ChannelName, cp.UniqueCode, cp.Name AS ProductName,
               pb.ERPCode,
               pp.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS ComponentQuantity
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        LEFT JOIN ProductBox pb ON cp.ProductID = pb.ProductID
        WHERE {ws}
    """)

    # --- 불출 ---
    # owner_channels 필터 활성 시 불출 제외
    channel_list = _parse_multi(channel) if channel else []
    include_withdrawal = (not channel_list or '불출' in channel_list) and not owner_channels
    if include_withdrawal:
        ww = ["FORMAT(w.[Date],'yyyy-MM') BETWEEN ? AND ?"]
        wp = [year_month_from, year_month_to]
        if input_month:
            ww.append("w.InputMonth = ?"); wp.append(input_month)
        _add_in_filter(ww, wp, brand, "b.Name")
        ww_str = ' AND '.join(ww)

        # 불출 단품
        params.extend(wp)
        sub_queries.append(f"""
            SELECT FORMAT(w.[Date],'yyyy-MM') AS YearMonth,
                   ISNULL(b.Name, N'미분류') AS BrandName,
                   N'불출' AS ChannelName,
                   w.UniqueCode, w.ProductName,
                   pb.ERPCode,
                   w.PlannedQty AS ComponentQuantity
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            LEFT JOIN ProductBox pb ON pr.ProductID = pb.ProductID
            WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
              AND {ww_str}
        """)
        # 불출 세트
        params.extend(wp)
        sub_queries.append(f"""
            SELECT FORMAT(w.[Date],'yyyy-MM') AS YearMonth,
                   ISNULL(b.Name, N'미분류') AS BrandName,
                   N'불출' AS ChannelName,
                   cp.UniqueCode, cp.Name AS ProductName,
                   pb.ERPCode,
                   w.PlannedQty * CAST(bom.QuantityRequired AS int) AS ComponentQuantity
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
            INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
            LEFT JOIN ProductBox pb ON cp.ProductID = pb.ProductID
            WHERE {ww_str}
        """)

    full_query = f"""
        SELECT YearMonth, BrandName, ChannelName, UniqueCode, ProductName,
               MAX(ERPCode) AS ERPCode,
               SUM(ISNULL(ComponentQuantity, 0)) AS TotalQuantity
        FROM (
            {' UNION ALL '.join(sub_queries)}
        ) AS BOMAll
        GROUP BY YearMonth, BrandName, ChannelName, UniqueCode, ProductName
        ORDER BY BrandName, ChannelName, UniqueCode, YearMonth
    """

    return full_query, params


def _pivot_bom_data(rows):
    """BOM 분해 결과를 피벗 데이터로 변환 (수량만)"""
    year_months_set = OrderedDict()
    product_map = OrderedDict()

    for row in rows:
        ym, brand, channel, code, name, erp_code, qty = row
        brand = brand or '미분류'
        channel = channel or '미분류'
        code = code or ''
        name = name or ''
        erp_code = erp_code or ''
        qty = int(qty or 0)

        year_months_set[ym] = True
        key = (brand, channel, code, name)

        if key not in product_map:
            product_map[key] = {
                'brand': brand,
                'channel': channel,
                'name': name,
                'erpCode': erp_code,
                'months': {},
                'totalQuantity': 0,
            }

        entry = product_map[key]
        if ym not in entry['months']:
            entry['months'][ym] = 0

        entry['months'][ym] += qty
        entry['totalQuantity'] += qty

    year_months = sorted(year_months_set.keys())
    data = list(product_map.values())

    return year_months, data


@router.get("/bom-data")
async def get_bom_data(
    year_month_from: str = Query(..., description="시작 연월 (YYYY-MM)"),
    year_month_to: str = Query(..., description="종료 연월 (YYYY-MM)"),
    input_month: Optional[str] = Query(None, description="입력월"),
    brand: Optional[str] = Query(None, description="브랜드"),
    channel: Optional[str] = Query(None, description="채널"),
    owner: Optional[str] = Query(None, description="채널 Owner 필터"),
    user: CurrentUser = Depends(get_current_user)
):
    """BOM 분해 피벗 데이터 조회 (수량만)"""
    oc = _get_owner_channels(owner) if owner else None
    if owner and not oc:
        return {"year_months": [], "data": []}
    query, params = _build_bom_query(year_month_from, year_month_to, input_month, brand, channel, oc)

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        rows = cursor.fetchall()

    year_months, data = _pivot_bom_data(rows)
    return {"year_months": year_months, "data": data}


@router.get("/bom-download")
async def download_bom_excel(
    year_month_from: str = Query(..., description="시작 연월 (YYYY-MM)"),
    year_month_to: str = Query(..., description="종료 연월 (YYYY-MM)"),
    input_month: Optional[str] = Query(None, description="입력월"),
    brand: Optional[str] = Query(None, description="브랜드"),
    channel: Optional[str] = Query(None, description="채널"),
    owner: Optional[str] = Query(None, description="채널 Owner 필터"),
    user: CurrentUser = Depends(get_current_user)
):
    """BOM 분해 엑셀 다운로드 (수량만 피벗)"""
    import xlsxwriter

    oc = _get_owner_channels(owner) if owner else None
    query, params = _build_bom_query(year_month_from, year_month_to, input_month, brand, channel, oc)

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        rows = cursor.fetchall()

    year_months, data = _pivot_bom_data(rows)

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('BOM 분해')

    header_fmt = workbook.add_format({
        'bold': True, 'bg_color': '#4472C4', 'font_color': 'white',
        'border': 1, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center'
    })
    num_fmt = workbook.add_format({'num_format': '#,##0', 'border': 1})
    text_fmt = workbook.add_format({'border': 1})
    total_header_fmt = workbook.add_format({
        'bold': True, 'bg_color': '#E2EFDA', 'border': 1,
        'text_wrap': True, 'valign': 'vcenter', 'align': 'center'
    })
    total_num_fmt = workbook.add_format({
        'num_format': '#,##0', 'border': 1, 'bold': True, 'bg_color': '#E2EFDA'
    })

    headers = ['브랜드', '채널', 'ERP코드', '상품명']
    for ym in year_months:
        headers.append(f'{ym}(수량)')
    headers.append('합계(수량)')

    for i, h in enumerate(headers):
        fmt = total_header_fmt if h.startswith('합계') else header_fmt
        worksheet.write(0, i, h, fmt)

    for row_idx, item in enumerate(data, start=1):
        worksheet.write(row_idx, 0, item['brand'], text_fmt)
        worksheet.write(row_idx, 1, item['channel'], text_fmt)
        worksheet.write(row_idx, 2, item.get('erpCode', ''), text_fmt)
        worksheet.write(row_idx, 3, item['name'], text_fmt)

        col = 4
        for ym in year_months:
            qty = item['months'].get(ym, 0)
            worksheet.write(row_idx, col, qty, num_fmt)
            col += 1

        worksheet.write(row_idx, col, item['totalQuantity'], total_num_fmt)

    worksheet.set_column(0, 0, 12)
    worksheet.set_column(1, 1, 14)
    worksheet.set_column(2, 2, 14)
    worksheet.set_column(3, 3, 25)
    if len(headers) > 4:
        worksheet.set_column(4, len(headers) - 1, 14)

    workbook.close()
    output.seek(0)

    filename = f"BOM분해_{year_month_from}~{year_month_to}"
    if input_month:
        filename += f"_입력월{input_month}"
    if brand:
        filename += f"_{brand}"
    if channel:
        filename += f"_{channel}"
    filename += ".xlsx"

    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f"attachment; filename*=UTF-8''{quote(filename)}"}
    )


# ========== BOM 분해 v2 (SKU 중심 요약 + 상세) ==========

def _build_bom_summary_query(
    year_month_from: str, year_month_to: str,
    input_month: Optional[str] = None,
    brand: Optional[str] = None,
    channel: Optional[str] = None,
    owner_channels: Optional[list] = None
):
    """BOM 분해 SKU 중심 요약 쿼리 — 단품통과/세트분해 구분 포함"""
    params = []
    sub_queries = []

    def _reg_where(alias):
        w = [f"FORMAT({alias}.[Date],'yyyy-MM') BETWEEN ? AND ?"]
        p = [year_month_from, year_month_to]
        if input_month:
            w.append(f"{alias}.InputMonth = ?"); p.append(input_month)
        _add_in_filter(w, p, brand, f"{alias}.BrandName")
        _add_in_filter(w, p, channel, f"{alias}.ChannelName")
        _add_owner_filter(w, p, owner_channels, f"{alias}.ChannelName")
        return ' AND '.join(w), p

    def _irreg_where(pa):
        w = [f"FORMAT({pa}.StartDate,'yyyy-MM') BETWEEN ? AND ?"]
        p = [year_month_from, year_month_to]
        if input_month:
            w.append(f"{pa}.InputMonth = ?"); p.append(input_month)
        _add_in_filter(w, p, brand, f"{pa}.BrandName")
        _add_in_filter(w, p, channel, f"{pa}.ChannelName")
        _add_owner_filter(w, p, owner_channels, f"{pa}.ChannelName")
        return ' AND '.join(w), p

    # --- 3P 정기 단품 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT e.UniqueCode, e.ProductName,
               e.ExpectedQuantity AS Qty, N'single' AS DecompType
        FROM Expected3PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 3P 정기 세트 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT cp.UniqueCode, cp.Name AS ProductName,
               e.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS Qty, N'set' AS DecompType
        FROM Expected3PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        WHERE {ws}
    """)

    # --- 3P 비정기 단품 ---
    ws, wp = _irreg_where('p')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT pp.UniqueCode, pp.ProductName,
               pp.ExpectedQuantity AS Qty, N'single' AS DecompType
        FROM Expected3PIrregularProduct pp
        INNER JOIN Expected3PIrregular p ON pp.Expected3PIrregularID = p.Expected3PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 3P 비정기 세트 ---
    ws, wp = _irreg_where('p')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT cp.UniqueCode, cp.Name AS ProductName,
               pp.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS Qty, N'set' AS DecompType
        FROM Expected3PIrregularProduct pp
        INNER JOIN Expected3PIrregular p ON pp.Expected3PIrregularID = p.Expected3PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        WHERE {ws}
    """)

    # --- 1P 정기 단품 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT e.UniqueCode, e.ProductName,
               e.ExpectedQuantity AS Qty, N'single' AS DecompType
        FROM Expected1PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 1P 정기 세트 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT cp.UniqueCode, cp.Name AS ProductName,
               e.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS Qty, N'set' AS DecompType
        FROM Expected1PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        WHERE {ws}
    """)

    # --- 1P 비정기 단품 ---
    ws, wp = _irreg_where('p')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT pp.UniqueCode, pp.ProductName,
               pp.ExpectedQuantity AS Qty, N'single' AS DecompType
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 1P 비정기 세트 ---
    ws, wp = _irreg_where('p')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT cp.UniqueCode, cp.Name AS ProductName,
               pp.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS Qty, N'set' AS DecompType
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        WHERE {ws}
    """)

    # --- 불출 ---
    channel_list = _parse_multi(channel) if channel else []
    include_withdrawal = (not channel_list or '불출' in channel_list) and not owner_channels
    if include_withdrawal:
        ww = ["FORMAT(w.[Date],'yyyy-MM') BETWEEN ? AND ?"]
        wp = [year_month_from, year_month_to]
        if input_month:
            ww.append("w.InputMonth = ?"); wp.append(input_month)
        _add_in_filter(ww, wp, brand, "b.Name")
        ww_str = ' AND '.join(ww)

        # 불출 단품
        params.extend(wp)
        sub_queries.append(f"""
            SELECT w.UniqueCode, w.ProductName,
                   w.PlannedQty AS Qty, N'single' AS DecompType
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
              AND {ww_str}
        """)
        # 불출 세트
        params.extend(wp)
        sub_queries.append(f"""
            SELECT cp.UniqueCode, cp.Name AS ProductName,
                   w.PlannedQty * CAST(bom.QuantityRequired AS int) AS Qty, N'set' AS DecompType
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
            INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
            WHERE {ww_str}
        """)

    full_query = f"""
        SELECT UniqueCode, ProductName,
               SUM(ISNULL(Qty, 0)) AS TotalQty,
               SUM(CASE WHEN DecompType = N'set' THEN ISNULL(Qty, 0) ELSE 0 END) AS FromSetQty,
               SUM(CASE WHEN DecompType = N'single' THEN ISNULL(Qty, 0) ELSE 0 END) AS FromSingleQty
        FROM (
            {' UNION ALL '.join(sub_queries)}
        ) AS BOMAll
        GROUP BY UniqueCode, ProductName
        ORDER BY UniqueCode
    """

    return full_query, params


def _build_bom_detail_query(
    unique_code: str,
    year_month_from: str, year_month_to: str,
    input_month: Optional[str] = None,
    brand: Optional[str] = None,
    channel: Optional[str] = None,
    owner_channels: Optional[list] = None
):
    """특정 SKU의 BOM 분해 상세 쿼리 — 세트 부모 정보 포함"""
    params = []
    sub_queries = []

    def _reg_where(alias):
        w = [f"FORMAT({alias}.[Date],'yyyy-MM') BETWEEN ? AND ?"]
        p = [year_month_from, year_month_to]
        if input_month:
            w.append(f"{alias}.InputMonth = ?"); p.append(input_month)
        _add_in_filter(w, p, brand, f"{alias}.BrandName")
        _add_in_filter(w, p, channel, f"{alias}.ChannelName")
        _add_owner_filter(w, p, owner_channels, f"{alias}.ChannelName")
        return ' AND '.join(w), p

    def _irreg_where(pa):
        w = [f"FORMAT({pa}.StartDate,'yyyy-MM') BETWEEN ? AND ?"]
        p = [year_month_from, year_month_to]
        if input_month:
            w.append(f"{pa}.InputMonth = ?"); p.append(input_month)
        _add_in_filter(w, p, brand, f"{pa}.BrandName")
        _add_in_filter(w, p, channel, f"{pa}.ChannelName")
        _add_owner_filter(w, p, owner_channels, f"{pa}.ChannelName")
        return ' AND '.join(w), p

    def _add_sub(sql, code_params, filter_params):
        """서브쿼리 + 파라미터 추가 (unique_code 먼저, 필터 뒤)"""
        params.extend(code_params)
        params.extend(filter_params)
        sub_queries.append(sql)

    # --- 3P 정기 단품 ---
    ws, wp = _reg_where('e')
    _add_sub(f"""
        SELECT FORMAT(e.[Date],'yyyy-MM') AS YearMonth,
               e.ChannelName, N'3P정기' AS SourceType,
               e.ExpectedQuantity AS Qty,
               N'single' AS DecompType,
               NULL AS ParentCode, NULL AS ParentName, NULL AS QtyRequired
        FROM Expected3PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        WHERE pr.UniqueCode = ? AND NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """, [unique_code], wp)

    # --- 3P 정기 세트 ---
    ws, wp = _reg_where('e')
    _add_sub(f"""
        SELECT FORMAT(e.[Date],'yyyy-MM') AS YearMonth,
               e.ChannelName, N'3P정기' AS SourceType,
               e.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS Qty,
               N'set' AS DecompType,
               pr.UniqueCode AS ParentCode, e.ProductName AS ParentName,
               CAST(bom.QuantityRequired AS int) AS QtyRequired
        FROM Expected3PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        WHERE cp.UniqueCode = ? AND {ws}
    """, [unique_code], wp)

    # --- 3P 비정기 단품 ---
    ws, wp = _irreg_where('p')
    _add_sub(f"""
        SELECT FORMAT(p.StartDate,'yyyy-MM') AS YearMonth,
               p.ChannelName, N'3P비정기' AS SourceType,
               pp.ExpectedQuantity AS Qty,
               N'single' AS DecompType,
               NULL AS ParentCode, NULL AS ParentName, NULL AS QtyRequired
        FROM Expected3PIrregularProduct pp
        INNER JOIN Expected3PIrregular p ON pp.Expected3PIrregularID = p.Expected3PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        WHERE pr.UniqueCode = ? AND NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """, [unique_code], wp)

    # --- 3P 비정기 세트 ---
    ws, wp = _irreg_where('p')
    _add_sub(f"""
        SELECT FORMAT(p.StartDate,'yyyy-MM') AS YearMonth,
               p.ChannelName, N'3P비정기' AS SourceType,
               pp.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS Qty,
               N'set' AS DecompType,
               pr.UniqueCode AS ParentCode, pp.ProductName AS ParentName,
               CAST(bom.QuantityRequired AS int) AS QtyRequired
        FROM Expected3PIrregularProduct pp
        INNER JOIN Expected3PIrregular p ON pp.Expected3PIrregularID = p.Expected3PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        WHERE cp.UniqueCode = ? AND {ws}
    """, [unique_code], wp)

    # --- 1P 정기 단품 ---
    ws, wp = _reg_where('e')
    _add_sub(f"""
        SELECT FORMAT(e.[Date],'yyyy-MM') AS YearMonth,
               e.ChannelName, N'1P정기' AS SourceType,
               e.ExpectedQuantity AS Qty,
               N'single' AS DecompType,
               NULL AS ParentCode, NULL AS ParentName, NULL AS QtyRequired
        FROM Expected1PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        WHERE pr.UniqueCode = ? AND NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """, [unique_code], wp)

    # --- 1P 정기 세트 ---
    ws, wp = _reg_where('e')
    _add_sub(f"""
        SELECT FORMAT(e.[Date],'yyyy-MM') AS YearMonth,
               e.ChannelName, N'1P정기' AS SourceType,
               e.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS Qty,
               N'set' AS DecompType,
               pr.UniqueCode AS ParentCode, e.ProductName AS ParentName,
               CAST(bom.QuantityRequired AS int) AS QtyRequired
        FROM Expected1PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        WHERE cp.UniqueCode = ? AND {ws}
    """, [unique_code], wp)

    # --- 1P 비정기 단품 ---
    ws, wp = _irreg_where('p')
    _add_sub(f"""
        SELECT FORMAT(p.StartDate,'yyyy-MM') AS YearMonth,
               p.ChannelName, N'1P비정기' AS SourceType,
               pp.ExpectedQuantity AS Qty,
               N'single' AS DecompType,
               NULL AS ParentCode, NULL AS ParentName, NULL AS QtyRequired
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        WHERE pr.UniqueCode = ? AND NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """, [unique_code], wp)

    # --- 1P 비정기 세트 ---
    ws, wp = _irreg_where('p')
    _add_sub(f"""
        SELECT FORMAT(p.StartDate,'yyyy-MM') AS YearMonth,
               p.ChannelName, N'1P비정기' AS SourceType,
               pp.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS Qty,
               N'set' AS DecompType,
               pr.UniqueCode AS ParentCode, pp.ProductName AS ParentName,
               CAST(bom.QuantityRequired AS int) AS QtyRequired
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        WHERE cp.UniqueCode = ? AND {ws}
    """, [unique_code], wp)

    # --- 불출 ---
    channel_list = _parse_multi(channel) if channel else []
    include_withdrawal = (not channel_list or '불출' in channel_list) and not owner_channels
    if include_withdrawal:
        ww = ["FORMAT(w.[Date],'yyyy-MM') BETWEEN ? AND ?"]
        wp_w = [year_month_from, year_month_to]
        if input_month:
            ww.append("w.InputMonth = ?"); wp_w.append(input_month)
        _add_in_filter(ww, wp_w, brand, "b.Name")
        ww_str = ' AND '.join(ww)

        # 불출 단품
        _add_sub(f"""
            SELECT FORMAT(w.[Date],'yyyy-MM') AS YearMonth,
                   N'불출' AS ChannelName, N'불출' AS SourceType,
                   w.PlannedQty AS Qty,
                   N'single' AS DecompType,
                   NULL AS ParentCode, NULL AS ParentName, NULL AS QtyRequired
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            WHERE pr.UniqueCode = ? AND NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
              AND {ww_str}
        """, [unique_code], wp_w)
        # 불출 세트
        _add_sub(f"""
            SELECT FORMAT(w.[Date],'yyyy-MM') AS YearMonth,
                   N'불출' AS ChannelName, N'불출' AS SourceType,
                   w.PlannedQty * CAST(bom.QuantityRequired AS int) AS Qty,
                   N'set' AS DecompType,
                   pr.UniqueCode AS ParentCode, w.ProductName AS ParentName,
                   CAST(bom.QuantityRequired AS int) AS QtyRequired
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
            INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
            WHERE cp.UniqueCode = ? AND {ww_str}
        """, [unique_code], wp_w)

    full_query = f"""
        SELECT YearMonth, ChannelName, SourceType, Qty,
               DecompType, ParentCode, ParentName, QtyRequired
        FROM (
            {' UNION ALL '.join(sub_queries)}
        ) AS BOMDetail
        ORDER BY DecompType DESC, ParentCode, ChannelName, SourceType, YearMonth
    """

    return full_query, params


@router.get("/bom-summary")
async def get_bom_summary(
    year_month_from: str = Query(...),
    year_month_to: str = Query(...),
    input_month: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user)
):
    """BOM 분해 SKU 중심 요약 데이터"""
    oc = _get_owner_channels(owner) if owner else None
    if owner and not oc:
        return {"data": [], "summary": {"skuCount": 0, "totalQty": 0, "fromSetQty": 0, "fromSingleQty": 0}}
    query, params = _build_bom_summary_query(year_month_from, year_month_to, input_month, brand, channel, oc)

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        rows = cursor.fetchall()

    data = []
    total_qty = 0
    from_set_qty = 0
    from_single_qty = 0

    for row in rows:
        code, name, tq, fsq, fsnq = row
        tq = int(tq or 0)
        fsq = int(fsq or 0)
        fsnq = int(fsnq or 0)
        data.append({
            "code": code or '',
            "name": name or '',
            "totalQty": tq,
            "fromSet": fsq,
            "fromSingle": fsnq
        })
        total_qty += tq
        from_set_qty += fsq
        from_single_qty += fsnq

    return {
        "data": data,
        "summary": {
            "skuCount": len(data),
            "totalQty": total_qty,
            "fromSetQty": from_set_qty,
            "fromSingleQty": from_single_qty
        }
    }


@router.get("/bom-detail")
async def get_bom_detail(
    unique_code: str = Query(...),
    year_month_from: str = Query(...),
    year_month_to: str = Query(...),
    input_month: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user)
):
    """특정 SKU의 BOM 분해 상세 (세트 부모 정보 포함)"""
    oc = _get_owner_channels(owner) if owner else None
    if owner and not oc:
        return {"fromSet": [], "fromSingle": []}
    query, params = _build_bom_detail_query(
        unique_code, year_month_from, year_month_to,
        input_month, brand, channel, oc
    )

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        rows = cursor.fetchall()

    # 세트 분해 건: parentCode별 그룹핑
    set_map = {}
    single_list = []

    for row in rows:
        ym, ch, src, qty, decomp, p_code, p_name, q_req = row
        qty = int(qty or 0)
        q_req = int(q_req) if q_req else None

        if decomp == 'set':
            key = p_code or ''
            if key not in set_map:
                set_map[key] = {
                    "parentCode": p_code or '',
                    "parentName": p_name or '',
                    "qtyRequired": q_req,
                    "details": []
                }
            set_map[key]["details"].append({
                "channel": ch or '',
                "sourceType": src or '',
                "yearMonth": ym or '',
                "qty": qty
            })
        else:
            single_list.append({
                "channel": ch or '',
                "sourceType": src or '',
                "yearMonth": ym or '',
                "qty": qty
            })

    return {
        "fromSet": list(set_map.values()),
        "fromSingle": single_list
    }


# ==================== SKU 관리 ====================

def _build_sku_summary_query(
    year_month_from: str, year_month_to: str,
    input_month: Optional[str] = None,
    brand: Optional[str] = None,
    channel: Optional[str] = None,
    owner_channels: Optional[list] = None
):
    """SKU 단위 합산 쿼리 (UniqueCode+ProductName 기준)"""
    params = []

    # --- 3P 정기 ---
    w3r = ["FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    if input_month:
        w3r.append("t.InputMonth = ?"); params.append(input_month)
    _add_in_filter(w3r, params, brand, "t.BrandName")
    _add_in_filter(w3r, params, channel, "t.ChannelName")
    _add_owner_filter(w3r, params, owner_channels, "t.ChannelName")
    q3r = f"""
        SELECT t.UniqueCode, t.ProductName, t.BrandName,
               t.ExpectedAmount, t.ExpectedQuantity
        FROM Expected3PRegularProduct t
        WHERE {' AND '.join(w3r)}
    """

    # --- 3P 비정기 ---
    w3i = ["FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    if input_month:
        w3i.append("p.InputMonth = ?"); params.append(input_month)
    _add_in_filter(w3i, params, brand, "p.BrandName")
    _add_in_filter(w3i, params, channel, "p.ChannelName")
    _add_owner_filter(w3i, params, owner_channels, "p.ChannelName")
    q3i = f"""
        SELECT pp.UniqueCode, pp.ProductName, p.BrandName,
               pp.ExpectedSalesAmount AS ExpectedAmount, pp.ExpectedQuantity
        FROM Expected3PIrregularProduct pp
        INNER JOIN Expected3PIrregular p ON pp.Expected3PIrregularID = p.Expected3PIrregularID
        WHERE {' AND '.join(w3i)}
    """

    # --- 1P 정기 ---
    w1r = ["FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    if input_month:
        w1r.append("t.InputMonth = ?"); params.append(input_month)
    _add_in_filter(w1r, params, brand, "t.BrandName")
    _add_in_filter(w1r, params, channel, "t.ChannelName")
    _add_owner_filter(w1r, params, owner_channels, "t.ChannelName")
    q1r = f"""
        SELECT t.UniqueCode, t.ProductName, t.BrandName,
               t.ExpectedAmount, t.ExpectedQuantity
        FROM Expected1PRegularProduct t
        WHERE {' AND '.join(w1r)}
    """

    # --- 1P 비정기 ---
    w1i = ["FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    if input_month:
        w1i.append("p.InputMonth = ?"); params.append(input_month)
    _add_in_filter(w1i, params, brand, "p.BrandName")
    _add_in_filter(w1i, params, channel, "p.ChannelName")
    _add_owner_filter(w1i, params, owner_channels, "p.ChannelName")
    q1i = f"""
        SELECT pp.UniqueCode, pp.ProductName, p.BrandName,
               pp.ExpectedSalesAmount AS ExpectedAmount, pp.ExpectedQuantity
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        WHERE {' AND '.join(w1i)}
    """

    # --- 불출 ---
    channel_list = _parse_multi(channel) if channel else []
    include_withdrawal = (not channel_list or '불출' in channel_list) and not owner_channels
    if include_withdrawal:
        wwp = ["FORMAT(w.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
        params.extend([year_month_from, year_month_to])
        if input_month:
            wwp.append("w.InputMonth = ?"); params.append(input_month)
        _add_in_filter(wwp, params, brand, "b.Name")
        qwp = f"""
            SELECT w.UniqueCode, w.ProductName,
                   ISNULL(b.Name, N'미분류') AS BrandName,
                   NULL AS ExpectedAmount, w.PlannedQty AS ExpectedQuantity
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            WHERE {' AND '.join(wwp)}
        """

    sub_queries = [q3r, q3i, q1r, q1i]
    if include_withdrawal:
        sub_queries.append(qwp)

    full_query = f"""
        SELECT UniqueCode, ProductName,
               SUM(ISNULL(ExpectedAmount, 0)) AS TotalAmount,
               SUM(ISNULL(ExpectedQuantity, 0)) AS TotalQuantity
        FROM (
            {' UNION ALL '.join(sub_queries)}
        ) AS Combined
        GROUP BY UniqueCode, ProductName
        ORDER BY UniqueCode
    """

    return full_query, params


def _build_sku_detail_query(
    unique_code: str,
    year_month_from: str, year_month_to: str,
    input_month: Optional[str] = None,
    brand: Optional[str] = None,
    channel: Optional[str] = None,
    owner_channels: Optional[list] = None
):
    """특정 SKU의 채널/구분별 상세 쿼리 (개별 레코드 ID 포함, 인라인 편집용)"""
    params = []

    # --- 3P 정기 ---
    w3r = ["t.UniqueCode = ?", "FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([unique_code, year_month_from, year_month_to])
    if input_month:
        w3r.append("t.InputMonth = ?"); params.append(input_month)
    _add_in_filter(w3r, params, brand, "t.BrandName")
    _add_in_filter(w3r, params, channel, "t.ChannelName")
    _add_owner_filter(w3r, params, owner_channels, "t.ChannelName")
    q3r = f"""
        SELECT t.Expected3PRegularID AS RecordID,
               FORMAT(t.[Date], 'yyyy-MM') AS YearMonth,
               t.ChannelName, N'정기' AS SourceType, N'3P정기' AS SourceCode,
               ISNULL(t.ExpectedAmount, 0) AS ExpectedAmount,
               ISNULL(t.ExpectedQuantity, 0) AS ExpectedQuantity,
               NULL AS IrregularName
        FROM Expected3PRegularProduct t
        WHERE {' AND '.join(w3r)}
    """

    # --- 3P 비정기 ---
    w3i = ["pp.UniqueCode = ?", "FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([unique_code, year_month_from, year_month_to])
    if input_month:
        w3i.append("p.InputMonth = ?"); params.append(input_month)
    _add_in_filter(w3i, params, brand, "p.BrandName")
    _add_in_filter(w3i, params, channel, "p.ChannelName")
    _add_owner_filter(w3i, params, owner_channels, "p.ChannelName")
    q3i = f"""
        SELECT pp.Expected3PIrregularProductID AS RecordID,
               FORMAT(p.StartDate, 'yyyy-MM') AS YearMonth,
               p.ChannelName, N'비정기' AS SourceType, N'3P비정기' AS SourceCode,
               ISNULL(pp.ExpectedSalesAmount, 0) AS ExpectedAmount,
               ISNULL(pp.ExpectedQuantity, 0) AS ExpectedQuantity,
               p.IrregularName
        FROM Expected3PIrregularProduct pp
        INNER JOIN Expected3PIrregular p ON pp.Expected3PIrregularID = p.Expected3PIrregularID
        WHERE {' AND '.join(w3i)}
    """

    # --- 1P 정기 ---
    w1r = ["t.UniqueCode = ?", "FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([unique_code, year_month_from, year_month_to])
    if input_month:
        w1r.append("t.InputMonth = ?"); params.append(input_month)
    _add_in_filter(w1r, params, brand, "t.BrandName")
    _add_in_filter(w1r, params, channel, "t.ChannelName")
    _add_owner_filter(w1r, params, owner_channels, "t.ChannelName")
    q1r = f"""
        SELECT t.Expected1PRegularID AS RecordID,
               FORMAT(t.[Date], 'yyyy-MM') AS YearMonth,
               t.ChannelName, N'정기' AS SourceType, N'1P정기' AS SourceCode,
               ISNULL(t.ExpectedAmount, 0) AS ExpectedAmount,
               ISNULL(t.ExpectedQuantity, 0) AS ExpectedQuantity,
               NULL AS IrregularName
        FROM Expected1PRegularProduct t
        WHERE {' AND '.join(w1r)}
    """

    # --- 1P 비정기 ---
    w1i = ["pp.UniqueCode = ?", "FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([unique_code, year_month_from, year_month_to])
    if input_month:
        w1i.append("p.InputMonth = ?"); params.append(input_month)
    _add_in_filter(w1i, params, brand, "p.BrandName")
    _add_in_filter(w1i, params, channel, "p.ChannelName")
    _add_owner_filter(w1i, params, owner_channels, "p.ChannelName")
    q1i = f"""
        SELECT pp.Expected1PIrregularProductID AS RecordID,
               FORMAT(p.StartDate, 'yyyy-MM') AS YearMonth,
               p.ChannelName, N'비정기' AS SourceType, N'1P비정기' AS SourceCode,
               ISNULL(pp.ExpectedSalesAmount, 0) AS ExpectedAmount,
               ISNULL(pp.ExpectedQuantity, 0) AS ExpectedQuantity,
               p.IrregularName
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        WHERE {' AND '.join(w1i)}
    """

    # --- 불출 ---
    channel_list = _parse_multi(channel) if channel else []
    include_withdrawal = (not channel_list or '불출' in channel_list) and not owner_channels
    if include_withdrawal:
        wwp = ["w.UniqueCode = ?", "FORMAT(w.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
        params.extend([unique_code, year_month_from, year_month_to])
        if input_month:
            wwp.append("w.InputMonth = ?"); params.append(input_month)
        _add_in_filter(wwp, params, brand, "b.Name")
        qwp = f"""
            SELECT w.PlanID AS RecordID,
                   FORMAT(w.[Date], 'yyyy-MM') AS YearMonth,
                   N'불출' AS ChannelName, N'불출' AS SourceType, N'불출' AS SourceCode,
                   0 AS ExpectedAmount,
                   ISNULL(w.PlannedQty, 0) AS ExpectedQuantity,
                   NULL AS IrregularName
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            WHERE {' AND '.join(wwp)}
        """

    sub_queries = [q3r, q3i, q1r, q1i]
    if include_withdrawal:
        sub_queries.append(qwp)

    full_query = f"""
        SELECT RecordID, YearMonth, ChannelName, SourceType, SourceCode,
               ExpectedAmount, ExpectedQuantity, IrregularName
        FROM (
            {' UNION ALL '.join(sub_queries)}
        ) AS Combined
        ORDER BY ChannelName,
                 CASE SourceType
                     WHEN N'정기' THEN 1 WHEN N'비정기' THEN 2
                     WHEN N'불출' THEN 3 ELSE 4
                 END,
                 IrregularName, YearMonth
    """

    return full_query, params


@router.get("/sku-data")
async def get_sku_data(
    year_month_from: str = Query(...),
    year_month_to: str = Query(...),
    input_month: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user)
):
    """SKU 단위 합산 데이터 조회"""
    oc = _get_owner_channels(owner) if owner else None
    if owner and not oc:
        return {"data": [], "summary": {"totalAmount": 0, "totalQuantity": 0, "productCount": 0}}
    query, params = _build_sku_summary_query(
        year_month_from, year_month_to, input_month, brand, channel, oc
    )

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        rows = cursor.fetchall()

    data = []
    total_amount = 0
    total_quantity = 0

    for row in rows:
        code, name, amount, qty = row
        amount = float(amount) if amount else 0
        qty = int(qty) if qty else 0
        data.append({
            "code": code,
            "name": name,
            "totalAmount": amount,
            "totalQuantity": qty
        })
        total_amount += amount
        total_quantity += qty

    return {
        "data": data,
        "summary": {
            "totalAmount": total_amount,
            "totalQuantity": total_quantity,
            "productCount": len(data)
        }
    }


@router.get("/sku-detail")
async def get_sku_detail(
    unique_code: str = Query(...),
    year_month_from: str = Query(...),
    year_month_to: str = Query(...),
    input_month: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user)
):
    """특정 SKU의 채널/구분별 상세 데이터 (개별 레코드 ID 포함)"""
    oc = _get_owner_channels(owner) if owner else None
    if owner and not oc:
        return []
    query, params = _build_sku_detail_query(
        unique_code, year_month_from, year_month_to,
        input_month, brand, channel, oc
    )

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        rows = cursor.fetchall()

    return [
        {
            "recordId": int(row[0]),
            "yearMonth": row[1],
            "channel": row[2],
            "sourceType": row[3],
            "sourceCode": row[4],
            "amount": float(row[5]) if row[5] else 0,
            "quantity": int(row[6]) if row[6] else 0,
            "irregularName": row[7] if row[7] else None
        }
        for row in rows
    ]


# ==================== SKU 인라인 편집 ====================

class SkuInlineUpdateItem(BaseModel):
    recordId: int
    sourceType: str
    channel: Optional[str] = None
    yearMonth: Optional[str] = None
    amount: Optional[float] = None
    quantity: Optional[int] = None


class SkuInlineUpdateRequest(BaseModel):
    uniqueCode: Optional[str] = None
    productName: Optional[str] = None
    items: List[SkuInlineUpdateItem]


# sourceType별 테이블 매핑
_SOURCE_CONFIG = {
    '3P정기': {
        'table': 'Expected3PRegularProduct',
        'pk': 'Expected3PRegularID',
        'amount_col': 'ExpectedAmount',
        'ex_vat_col': 'ExpectedAmountExVAT',
        'qty_col': 'ExpectedQuantity',
    },
    '3P비정기': {
        'table': 'Expected3PIrregularProduct',
        'pk': 'Expected3PIrregularProductID',
        'amount_col': 'ExpectedSalesAmount',
        'ex_vat_col': 'ExpectedSalesAmountExVAT',
        'qty_col': 'ExpectedQuantity',
    },
    '1P정기': {
        'table': 'Expected1PRegularProduct',
        'pk': 'Expected1PRegularID',
        'amount_col': 'ExpectedAmount',
        'ex_vat_col': 'ExpectedAmountExVAT',
        'qty_col': 'ExpectedQuantity',
    },
    '1P비정기': {
        'table': 'Expected1PIrregularProduct',
        'pk': 'Expected1PIrregularProductID',
        'amount_col': 'ExpectedSalesAmount',
        'ex_vat_col': 'ExpectedSalesAmountExVAT',
        'qty_col': 'ExpectedQuantity',
    },
    '불출': {
        'table': 'WithdrawalPlan',
        'pk': 'PlanID',
        'amount_col': None,
        'ex_vat_col': None,
        'qty_col': 'PlannedQty',
    },
}


@router.put("/sku-inline-update")
@log_activity("UPDATE", "ExpectedSalesIntegration", id_key="updated")
async def sku_inline_update(
    data: SkuInlineUpdateRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("ExpectedSalesIntegration", "UPDATE"))
):
    """SKU 디테일 인라인 편집 저장"""
    if not data.items:
        raise HTTPException(400, "수정할 데이터가 없습니다")

    total_updated = 0
    user_id = user.user_id
    user_name = None
    slack_changes = []  # Slack 알림용 변동 내역

    try:
        with get_db_cursor() as cursor:
            # 사용자 이름 조회
            cursor.execute("SELECT Name FROM [dbo].[User] WHERE UserID = ?", user_id)
            name_row = cursor.fetchone()
            if name_row:
                user_name = name_row[0]

            for item in data.items:
                config = _SOURCE_CONFIG.get(item.sourceType)
                if not config:
                    continue

                table = config['table']
                pk = config['pk']
                amount_col = config['amount_col']
                ex_vat_col = config['ex_vat_col']
                qty_col = config['qty_col']
                record_id = item.recordId

                if amount_col:
                    # 매출+수량 편집 (3P/1P 정기/비정기) - VAT 포함 기준
                    cursor.execute(
                        f"SELECT {amount_col}, {qty_col} FROM [dbo].[{table}] WHERE {pk} = ?",
                        record_id
                    )
                    old_row = cursor.fetchone()
                    if not old_row:
                        continue

                    new_amount = float(item.amount or 0)
                    new_qty = int(item.quantity or 0)
                    old_amount = float(old_row[0] or 0)
                    old_qty = int(old_row[1] or 0)
                    old_data = {amount_col: old_row[0], qty_col: old_row[1]}
                    new_data = {amount_col: new_amount, qty_col: new_qty}

                    log_changes(cursor, table, record_id, old_data, new_data, user_id)

                    new_ex_vat = calculate_amount_ex_vat(new_amount)
                    cursor.execute(
                        f"""UPDATE [dbo].[{table}]
                            SET {amount_col} = ?, {ex_vat_col} = ?,
                                {qty_col} = ?, UpdatedDate = GETDATE()
                            WHERE {pk} = ?""",
                        new_amount, new_ex_vat, new_qty, record_id
                    )

                    if cursor.rowcount > 0:
                        total_updated += 1
                        if old_amount != new_amount or old_qty != new_qty:
                            slack_changes.append({
                                'channel': item.channel or '',
                                'source_type': item.sourceType.replace('3P', '').replace('1P', '') if item.sourceType != '불출' else '불출',
                                'year_month': item.yearMonth or '',
                                'old_amount': old_amount, 'new_amount': new_amount,
                                'old_qty': old_qty, 'new_qty': new_qty,
                            })
                else:
                    # 수량만 편집 (불출)
                    cursor.execute(
                        f"SELECT {qty_col} FROM [dbo].[{table}] WHERE {pk} = ?",
                        record_id
                    )
                    old_row = cursor.fetchone()
                    if not old_row:
                        continue

                    new_qty = int(item.quantity or 0)
                    old_qty = int(old_row[0] or 0)
                    old_data = {qty_col: old_row[0]}
                    new_data = {qty_col: new_qty}

                    log_changes(cursor, table, record_id, old_data, new_data, user_id)

                    cursor.execute(
                        f"""UPDATE [dbo].[{table}]
                            SET {qty_col} = ?, UpdatedDate = GETDATE()
                            WHERE {pk} = ?""",
                        new_qty, record_id
                    )

                    if cursor.rowcount > 0:
                        total_updated += 1
                        if old_qty != new_qty:
                            slack_changes.append({
                                'channel': item.channel or '불출',
                                'source_type': '불출',
                                'year_month': item.yearMonth or '',
                                'old_amount': 0, 'new_amount': 0,
                                'old_qty': old_qty, 'new_qty': new_qty,
                            })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"저장 실패: {str(e)}")

    # Slack 알림 (비동기)
    if slack_changes:
        try:
            from utils.slack_notifier import send_sku_inline_update_notification_async
            send_sku_inline_update_notification_async(
                unique_code=data.uniqueCode or '',
                product_name=data.productName or '',
                changes=slack_changes,
                username=user_name or user.email,
            )
        except Exception:
            pass

    return {"message": f"{total_updated}건이 수정되었습니다", "updated": total_updated}


# ==================== 재고 대비 분석 ====================

def _build_inv_bom_query(
    year_month_from: str, year_month_to: str,
    input_month: Optional[str] = None,
    brand: Optional[str] = None,
    channel: Optional[str] = None,
    owner_channels: Optional[list] = None
):
    """ERPCode 기준 BOM 분해 소요량 쿼리 (재고 대비 분석용)"""
    params = []
    sub_queries = []

    def _reg_where(alias):
        w = [f"FORMAT({alias}.[Date],'yyyy-MM') BETWEEN ? AND ?"]
        p = [year_month_from, year_month_to]
        if input_month:
            w.append(f"{alias}.InputMonth = ?"); p.append(input_month)
        _add_in_filter(w, p, brand, f"{alias}.BrandName")
        _add_in_filter(w, p, channel, f"{alias}.ChannelName")
        _add_owner_filter(w, p, owner_channels, f"{alias}.ChannelName")
        return ' AND '.join(w), p

    def _irreg_where(pa):
        w = [f"FORMAT({pa}.StartDate,'yyyy-MM') BETWEEN ? AND ?"]
        p = [year_month_from, year_month_to]
        if input_month:
            w.append(f"{pa}.InputMonth = ?"); p.append(input_month)
        _add_in_filter(w, p, brand, f"{pa}.BrandName")
        _add_in_filter(w, p, channel, f"{pa}.ChannelName")
        _add_owner_filter(w, p, owner_channels, f"{pa}.ChannelName")
        return ' AND '.join(w), p

    # --- 3P 정기 단품 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT e.ERPCode, pr.UniqueCode, e.ProductName, e.BrandName,
               e.ExpectedQuantity AS Qty
        FROM Expected3PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 3P 정기 세트 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT cpb.ERPCode, cp.UniqueCode, cp.Name AS ProductName, e.BrandName,
               e.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS Qty
        FROM Expected3PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN ProductBox cpb ON cpb.BoxID = bom.ChildProductBoxID
        INNER JOIN Product cp ON cpb.ProductID = cp.ProductID
        WHERE {ws}
    """)

    # --- 3P 비정기 단품 ---
    ws, wp = _irreg_where('p')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT pp.ERPCode, pr.UniqueCode, pp.ProductName, p.BrandName,
               pp.ExpectedQuantity AS Qty
        FROM Expected3PIrregularProduct pp
        INNER JOIN Expected3PIrregular p ON pp.Expected3PIrregularID = p.Expected3PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 3P 비정기 세트 ---
    ws, wp = _irreg_where('p')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT cpb.ERPCode, cp.UniqueCode, cp.Name AS ProductName, p.BrandName,
               pp.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS Qty
        FROM Expected3PIrregularProduct pp
        INNER JOIN Expected3PIrregular p ON pp.Expected3PIrregularID = p.Expected3PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN ProductBox cpb ON cpb.BoxID = bom.ChildProductBoxID
        INNER JOIN Product cp ON cpb.ProductID = cp.ProductID
        WHERE {ws}
    """)

    # --- 1P 정기 단품 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT e.ERPCode, pr.UniqueCode, e.ProductName, e.BrandName,
               e.ExpectedQuantity AS Qty
        FROM Expected1PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 1P 정기 세트 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT cpb.ERPCode, cp.UniqueCode, cp.Name AS ProductName, e.BrandName,
               e.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS Qty
        FROM Expected1PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN ProductBox cpb ON cpb.BoxID = bom.ChildProductBoxID
        INNER JOIN Product cp ON cpb.ProductID = cp.ProductID
        WHERE {ws}
    """)

    # --- 1P 비정기 단품 ---
    ws, wp = _irreg_where('p')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT pp.ERPCode, pr.UniqueCode, pp.ProductName, p.BrandName,
               pp.ExpectedQuantity AS Qty
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 1P 비정기 세트 ---
    ws, wp = _irreg_where('p')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT cpb.ERPCode, cp.UniqueCode, cp.Name AS ProductName, p.BrandName,
               pp.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS Qty
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN ProductBox cpb ON cpb.BoxID = bom.ChildProductBoxID
        INNER JOIN Product cp ON cpb.ProductID = cp.ProductID
        WHERE {ws}
    """)

    # --- 불출 단품 ---
    channel_list = _parse_multi(channel) if channel else []
    include_withdrawal = (not channel_list or '불출' in channel_list) and not owner_channels
    if include_withdrawal:
        ww = ["FORMAT(w.[Date],'yyyy-MM') BETWEEN ? AND ?"]
        wp = [year_month_from, year_month_to]
        if input_month:
            ww.append("w.InputMonth = ?"); wp.append(input_month)
        _add_in_filter(ww, wp, brand, "b.Name")
        ww_str = ' AND '.join(ww)

        params.extend(wp)
        sub_queries.append(f"""
            SELECT pb.ERPCode, pr.UniqueCode, w.ProductName, b.Name AS BrandName,
                   w.PlannedQty AS Qty
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            LEFT JOIN ProductBox pb ON pb.ProductID = pr.ProductID
            WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
              AND {ww_str}
        """)
        # 불출 세트
        params.extend(wp)
        sub_queries.append(f"""
            SELECT cpb.ERPCode, cp.UniqueCode, cp.Name AS ProductName, b.Name AS BrandName,
                   w.PlannedQty * CAST(bom.QuantityRequired AS int) AS Qty
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
            INNER JOIN ProductBox cpb ON cpb.BoxID = bom.ChildProductBoxID
            INNER JOIN Product cp ON cpb.ProductID = cp.ProductID
            WHERE {ww_str}
        """)

    full_query = f"""
        SELECT ERPCode, MAX(UniqueCode) AS UniqueCode, MAX(ProductName) AS ProductName, MAX(BrandName) AS BrandName,
               SUM(ISNULL(Qty, 0)) AS TotalQty
        FROM (
            {' UNION ALL '.join(sub_queries)}
        ) AS InvBOM
        WHERE ERPCode IS NOT NULL
        GROUP BY ERPCode
        ORDER BY ERPCode
    """

    return full_query, params


@router.get("/inventory-analysis")
async def get_inventory_analysis(
    year_month_from: str = Query(...),
    year_month_to: str = Query(...),
    input_month: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user)
):
    """재고 대비 분석 - ERPCode 기준 BOM 분해 소요량 + 최신 재고 스냅샷"""
    oc = _get_owner_channels(owner) if owner else None
    if owner and not oc:
        return {"data": [], "summary": {}}

    # 1. ERPCode 기준 BOM 분해 소요량 쿼리
    bom_query, bom_params = _build_inv_bom_query(
        year_month_from, year_month_to, input_month, brand, channel, oc
    )

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(bom_query, *bom_params)
        bom_rows = cursor.fetchall()

    # ERPCode → 소요량 맵
    bom_map = {}
    for row in bom_rows:
        erp_code, unique_code, product_name, brand_name, tq = row
        bom_map[erp_code] = {
            "code": erp_code or '',
            "uniqueCode": unique_code or '',
            "name": product_name or '',
            "brand": brand_name or '',
            "requiredQty": int(tq or 0),
        }

    # 2. 최신 재고 스냅샷 조회 (ERPCode = ShippingProductID 기준)
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT TOP 1 SnapshotDate, SnapshotTime
            FROM [dbo].[SabangnetInventorySnapshot]
            ORDER BY SnapshotDate DESC, CASE SnapshotTime WHEN 'PM' THEN 1 ELSE 2 END
        """)
        latest = cursor.fetchone()
        if not latest:
            data = []
            for item in bom_map.values():
                item.update({"normalStock": None, "totalStock": None, "shortage": None, "daysLeft": None, "matched": False, "bomOnly": True})
                data.append(item)
            data.sort(key=lambda x: x.get("shortage") or 0)
            return {"data": data, "summary": _build_inv_summary(data), "snapshotDate": None}

        snap_date, snap_time = latest[0], latest[1]

        inv_where = ["s.SnapshotDate = ?", "s.SnapshotTime = ?"]
        inv_params = [snap_date, snap_time]
        if brand:
            brand_list = _parse_multi(brand)
            if brand_list:
                placeholders = ','.join(['?' for _ in brand_list])
                inv_where.append(f"b.Name IN ({placeholders})")
                inv_params.extend(brand_list)

        inv_where_sql = ' AND '.join(inv_where)

        # 단품 재고: BOM에 부모로 등록되지 않은 ERPCode
        cursor.execute(f"""
            SELECT
                pb.ERPCode, p.UniqueCode,
                COALESCE(p.Name, s.ProductName) AS ProductName,
                b.Name AS BrandName,
                s.NormalStock, s.TotalStock,
                s.ReceivingStock, s.OrderStock, s.ShippingStock,
                s.DamagedStock, s.ReturnStock, s.KeepingStock
            FROM [dbo].[SabangnetInventorySnapshot] s
            LEFT JOIN [dbo].[ProductBox] pb ON s.ProductCode = pb.ERPCode
            LEFT JOIN [dbo].[Product] p ON pb.ProductID = p.ProductID
            LEFT JOIN [dbo].[Brand] b ON p.BrandID = b.BrandID
            WHERE {inv_where_sql}
              AND NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductBoxID = pb.BoxID)
        """, inv_params)
        single_rows = cursor.fetchall()

        # 세트 재고: BOM 분해 → 자식 ERPCode별 환산
        cursor.execute(f"""
            SELECT
                cpb.ERPCode, cp.UniqueCode,
                cp.Name AS ProductName,
                b.Name AS BrandName,
                s.NormalStock * CAST(bom.QuantityRequired AS int) AS NormalStock,
                s.TotalStock * CAST(bom.QuantityRequired AS int) AS TotalStock,
                s.ReceivingStock * CAST(bom.QuantityRequired AS int) AS ReceivingStock,
                s.OrderStock * CAST(bom.QuantityRequired AS int) AS OrderStock,
                s.ShippingStock * CAST(bom.QuantityRequired AS int) AS ShippingStock,
                s.DamagedStock * CAST(bom.QuantityRequired AS int) AS DamagedStock,
                s.ReturnStock * CAST(bom.QuantityRequired AS int) AS ReturnStock,
                s.KeepingStock * CAST(bom.QuantityRequired AS int) AS KeepingStock
            FROM [dbo].[SabangnetInventorySnapshot] s
            INNER JOIN [dbo].[ProductBox] pb ON s.ProductCode = pb.ERPCode
            INNER JOIN [dbo].[ProductBOM] bom ON bom.ParentProductBoxID = pb.BoxID
            INNER JOIN [dbo].[ProductBox] cpb ON cpb.BoxID = bom.ChildProductBoxID
            INNER JOIN [dbo].[Product] cp ON cpb.ProductID = cp.ProductID
            LEFT JOIN [dbo].[Product] p ON pb.ProductID = p.ProductID
            LEFT JOIN [dbo].[Brand] b ON p.BrandID = b.BrandID
            WHERE {inv_where_sql}
        """, inv_params)
        set_rows = cursor.fetchall()

    # ERPCode → 재고 맵 (단품 + 세트분해 합산)
    inv_map = {}
    for row in list(single_rows) + list(set_rows):
        erp_code = row[0]
        if not erp_code:
            continue
        if erp_code not in inv_map:
            inv_map[erp_code] = {
                "uniqueCode": row[1] or '',
                "name": row[2] or '',
                "brand": row[3] or '',
                "normalStock": 0, "totalStock": 0,
                "receivingStock": 0, "orderStock": 0, "shippingStock": 0,
                "damagedStock": 0, "returnStock": 0, "keepingStock": 0,
            }
        inv = inv_map[erp_code]
        inv["normalStock"] += int(row[4] or 0)
        inv["totalStock"] += int(row[5] or 0)
        inv["receivingStock"] += int(row[6] or 0)
        inv["orderStock"] += int(row[7] or 0)
        inv["shippingStock"] += int(row[8] or 0)
        inv["damagedStock"] += int(row[9] or 0)
        inv["returnStock"] += int(row[10] or 0)
        inv["keepingStock"] += int(row[11] or 0)

    # 3. ERPCode 기준 FULL JOIN
    all_codes = set(list(bom_map.keys()) + list(inv_map.keys()))
    data = []
    for code in all_codes:
        bom = bom_map.get(code)
        inv = inv_map.get(code)

        required = bom["requiredQty"] if bom else 0
        normal = inv["normalStock"] if inv else None
        shortage = (normal - required) if normal is not None else None

        days_left = None
        if normal is not None and required > 0:
            days_left = round(normal / (required / 30))

        unique_code = bom.get("uniqueCode", '') if bom else (inv.get("uniqueCode", '') if inv else '')
        item = {
            "code": code,
            "uniqueCode": unique_code,
            "name": bom["name"] if bom else (inv["name"] if inv else ''),
            "brand": bom.get("brand", '') if bom else (inv.get("brand", '') if inv else ''),
            "requiredQty": required,
            "normalStock": normal,
            "totalStock": inv["totalStock"] if inv else None,
            "receivingStock": inv.get("receivingStock", 0) if inv else None,
            "orderStock": inv.get("orderStock", 0) if inv else None,
            "shippingStock": inv.get("shippingStock", 0) if inv else None,
            "damagedStock": inv.get("damagedStock", 0) if inv else None,
            "returnStock": inv.get("returnStock", 0) if inv else None,
            "keepingStock": inv.get("keepingStock", 0) if inv else None,
            "shortage": shortage,
            "daysLeft": days_left,
            "matched": bom is not None and inv is not None,
            "bomOnly": bom is not None and inv is None,
        }
        # 소요량 0 + 재고 0 → 제외
        if required == 0 and (normal is None or normal == 0):
            continue
        data.append(item)

    data.sort(key=lambda x: (x.get("brand") or '', x.get("name") or '', x.get("code") or ''))

    return {
        "data": data,
        "summary": _build_inv_summary(data),
        "snapshotDate": str(snap_date),
        "snapshotTime": snap_time,
    }


def _build_inv_summary(data):
    total = len(data)
    matched = sum(1 for d in data if d["matched"])
    bom_only = sum(1 for d in data if d.get("bomOnly"))
    shortage_count = sum(1 for d in data if d["matched"] and d.get("shortage") is not None and d["shortage"] < 0)
    warning_count = sum(1 for d in data if d.get("daysLeft") is not None and d["daysLeft"] <= 30)
    return {
        "totalItems": total,
        "matchedItems": matched,
        "unmatchedItems": bom_only,
        "matchRate": round(matched / total * 100, 1) if total > 0 else 0,
        "shortageCount": shortage_count,
        "warningCount": warning_count,
    }
