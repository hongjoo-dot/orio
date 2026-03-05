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


def _build_union_query(
    year_month_from: str, year_month_to: str,
    input_month: Optional[str] = None,
    brand: Optional[str] = None,
    channel: Optional[str] = None
):
    """UNION ALL 쿼리 및 파라미터 빌드 (연월 범위)"""
    params = []

    # --- 3P 정기 ---
    w3r = ["FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    if input_month:
        w3r.append("t.InputMonth = ?")
        params.append(input_month)
    if brand:
        w3r.append("t.BrandName = ?")
        params.append(brand)
    if channel:
        w3r.append("t.ChannelName = ?")
        params.append(channel)
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
    if brand:
        w3i.append("p.BrandName = ?")
        params.append(brand)
    if channel:
        w3i.append("p.ChannelName = ?")
        params.append(channel)
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
    if brand:
        w1r.append("t.BrandName = ?")
        params.append(brand)
    if channel:
        w1r.append("t.ChannelName = ?")
        params.append(channel)
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
    if brand:
        w1i.append("p.BrandName = ?")
        params.append(brand)
    if channel:
        w1i.append("p.ChannelName = ?")
        params.append(channel)
    q1i = f"""
        SELECT FORMAT(p.StartDate, 'yyyy-MM') AS YearMonth,
               p.BrandName, p.ChannelName, pp.UniqueCode, pp.ProductName,
               pp.ExpectedSalesAmount AS ExpectedAmount, pp.ExpectedQuantity
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        WHERE {' AND '.join(w1i)}
    """

    # --- 불출 ---
    # 채널 필터가 '불출'이 아닌 값이면 불출 서브쿼리 제외
    include_withdrawal = (channel is None or channel == '불출')
    if include_withdrawal:
        wwp = ["FORMAT(w.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
        params.extend([year_month_from, year_month_to])
        if input_month:
            wwp.append("w.InputMonth = ?")
            params.append(input_month)
        if brand:
            wwp.append("b.Name = ?")
            params.append(brand)
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
    user: CurrentUser = Depends(get_current_user)
):
    """통합 예상 판매량 피벗 데이터 조회 (열=연월)"""
    query, params = _build_union_query(year_month_from, year_month_to, input_month, brand, channel)

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        rows = cursor.fetchall()

    year_months, data = _pivot_data(rows)
    return {"year_months": year_months, "data": data}


@router.get("/input-months")
async def get_input_months(
    year_month_from: str = Query(..., description="시작 연월"),
    year_month_to: str = Query(..., description="종료 연월"),
    user: CurrentUser = Depends(get_current_user)
):
    """연월 범위 기준 입력월 목록"""
    query = """
        SELECT DISTINCT im FROM (
            SELECT t.InputMonth AS im FROM Expected3PRegularProduct t
            WHERE FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ? AND t.InputMonth IS NOT NULL
            UNION
            SELECT p.InputMonth AS im FROM Expected3PIrregular p
            WHERE FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ? AND p.InputMonth IS NOT NULL
            UNION
            SELECT t.InputMonth AS im FROM Expected1PRegularProduct t
            WHERE FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ? AND t.InputMonth IS NOT NULL
            UNION
            SELECT p.InputMonth AS im FROM Expected1PIrregular p
            WHERE FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ? AND p.InputMonth IS NOT NULL
            UNION
            SELECT w.InputMonth AS im FROM WithdrawalPlan w
            WHERE FORMAT(w.[Date], 'yyyy-MM') BETWEEN ? AND ? AND w.InputMonth IS NOT NULL
        ) AS AllInputMonths
        WHERE im IS NOT NULL
        ORDER BY im DESC
    """
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query,
            year_month_from, year_month_to, year_month_from, year_month_to,
            year_month_from, year_month_to, year_month_from, year_month_to,
            year_month_from, year_month_to)
        return [row[0] for row in cursor.fetchall()]


@router.get("/brands")
async def get_brands(
    year_month_from: str = Query(..., description="시작 연월"),
    year_month_to: str = Query(..., description="종료 연월"),
    user: CurrentUser = Depends(get_current_user)
):
    """연월 범위 기준 브랜드 목록"""
    query = """
        SELECT DISTINCT bn FROM (
            SELECT t.BrandName AS bn FROM Expected3PRegularProduct t
            WHERE FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?
            UNION
            SELECT p.BrandName AS bn FROM Expected3PIrregular p
            WHERE FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ?
            UNION
            SELECT t.BrandName AS bn FROM Expected1PRegularProduct t
            WHERE FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?
            UNION
            SELECT p.BrandName AS bn FROM Expected1PIrregular p
            WHERE FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ?
            UNION
            SELECT ISNULL(b.Name, N'미분류') AS bn
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            WHERE FORMAT(w.[Date], 'yyyy-MM') BETWEEN ? AND ?
        ) AS AllBrands
        WHERE bn IS NOT NULL
        ORDER BY bn
    """
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query,
            year_month_from, year_month_to, year_month_from, year_month_to,
            year_month_from, year_month_to, year_month_from, year_month_to,
            year_month_from, year_month_to)
        return [row[0] for row in cursor.fetchall()]


@router.get("/channels")
async def get_channels(
    year_month_from: str = Query(..., description="시작 연월"),
    year_month_to: str = Query(..., description="종료 연월"),
    user: CurrentUser = Depends(get_current_user)
):
    """연월 범위 기준 채널 목록"""
    query = """
        SELECT DISTINCT cn FROM (
            SELECT t.ChannelName AS cn FROM Expected3PRegularProduct t
            WHERE FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?
            UNION
            SELECT p.ChannelName AS cn FROM Expected3PIrregular p
            WHERE FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ?
            UNION
            SELECT t.ChannelName AS cn FROM Expected1PRegularProduct t
            WHERE FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?
            UNION
            SELECT p.ChannelName AS cn FROM Expected1PIrregular p
            WHERE FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ?
            UNION
            SELECT N'불출' AS cn FROM WithdrawalPlan w
            WHERE FORMAT(w.[Date], 'yyyy-MM') BETWEEN ? AND ?
        ) AS AllChannels
        WHERE cn IS NOT NULL
        ORDER BY cn
    """
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query,
            year_month_from, year_month_to, year_month_from, year_month_to,
            year_month_from, year_month_to, year_month_from, year_month_to,
            year_month_from, year_month_to)
        return [row[0] for row in cursor.fetchall()]


@router.get("/download")
async def download_excel(
    year_month_from: str = Query(..., description="시작 연월"),
    year_month_to: str = Query(..., description="종료 연월"),
    input_month: Optional[str] = Query(None, description="입력월"),
    brand: Optional[str] = Query(None, description="브랜드"),
    channel: Optional[str] = Query(None, description="채널"),
    user: CurrentUser = Depends(get_current_user)
):
    """통합 예상 판매량 엑셀 다운로드 (피벗 형태, 열=연월)"""
    import xlsxwriter

    query, params = _build_union_query(year_month_from, year_month_to, input_month, brand, channel)

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
    channel: Optional[str] = None
):
    """BOM 분해 UNION ALL 쿼리 빌드 (단품 pass-through + 세트 분해, 불출 포함)"""
    params = []
    sub_queries = []

    def _reg_where(alias):
        w = [f"FORMAT({alias}.[Date],'yyyy-MM') BETWEEN ? AND ?"]
        p = [year_month_from, year_month_to]
        if input_month:
            w.append(f"{alias}.InputMonth = ?"); p.append(input_month)
        if brand:
            w.append(f"{alias}.BrandName = ?"); p.append(brand)
        if channel:
            w.append(f"{alias}.ChannelName = ?"); p.append(channel)
        return ' AND '.join(w), p

    def _irreg_where(pa):
        w = [f"FORMAT({pa}.StartDate,'yyyy-MM') BETWEEN ? AND ?"]
        p = [year_month_from, year_month_to]
        if input_month:
            w.append(f"{pa}.InputMonth = ?"); p.append(input_month)
        if brand:
            w.append(f"{pa}.BrandName = ?"); p.append(brand)
        if channel:
            w.append(f"{pa}.ChannelName = ?"); p.append(channel)
        return ' AND '.join(w), p

    # --- 3P 정기 단품 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT FORMAT(e.[Date],'yyyy-MM') AS YearMonth,
               e.BrandName, e.ChannelName, e.UniqueCode, e.ProductName,
               e.ExpectedQuantity AS ComponentQuantity
        FROM Expected3PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 3P 정기 세트 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT FORMAT(e.[Date],'yyyy-MM') AS YearMonth,
               e.BrandName, e.ChannelName, cp.UniqueCode, cp.Name AS ProductName,
               e.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS ComponentQuantity
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
        SELECT FORMAT(p.StartDate,'yyyy-MM') AS YearMonth,
               p.BrandName, p.ChannelName, pp.UniqueCode, pp.ProductName,
               pp.ExpectedQuantity AS ComponentQuantity
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
        SELECT FORMAT(p.StartDate,'yyyy-MM') AS YearMonth,
               p.BrandName, p.ChannelName, cp.UniqueCode, cp.Name AS ProductName,
               pp.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS ComponentQuantity
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
        SELECT FORMAT(e.[Date],'yyyy-MM') AS YearMonth,
               e.BrandName, e.ChannelName, e.UniqueCode, e.ProductName,
               e.ExpectedQuantity AS ComponentQuantity
        FROM Expected1PRegularProduct e
        INNER JOIN Product pr ON e.UniqueCode = pr.UniqueCode
        WHERE NOT EXISTS (SELECT 1 FROM ProductBOM bom WHERE bom.ParentProductID = pr.ProductID)
          AND {ws}
    """)
    # --- 1P 정기 세트 ---
    ws, wp = _reg_where('e')
    params.extend(wp)
    sub_queries.append(f"""
        SELECT FORMAT(e.[Date],'yyyy-MM') AS YearMonth,
               e.BrandName, e.ChannelName, cp.UniqueCode, cp.Name AS ProductName,
               e.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS ComponentQuantity
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
        SELECT FORMAT(p.StartDate,'yyyy-MM') AS YearMonth,
               p.BrandName, p.ChannelName, pp.UniqueCode, pp.ProductName,
               pp.ExpectedQuantity AS ComponentQuantity
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
        SELECT FORMAT(p.StartDate,'yyyy-MM') AS YearMonth,
               p.BrandName, p.ChannelName, cp.UniqueCode, cp.Name AS ProductName,
               pp.ExpectedQuantity * CAST(bom.QuantityRequired AS int) AS ComponentQuantity
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        INNER JOIN Product pr ON pp.UniqueCode = pr.UniqueCode
        INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
        INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
        WHERE {ws}
    """)

    # --- 불출 ---
    include_withdrawal = (channel is None or channel == '불출')
    if include_withdrawal:
        ww = ["FORMAT(w.[Date],'yyyy-MM') BETWEEN ? AND ?"]
        wp = [year_month_from, year_month_to]
        if input_month:
            ww.append("w.InputMonth = ?"); wp.append(input_month)
        if brand:
            ww.append("b.Name = ?"); wp.append(brand)
        ww_str = ' AND '.join(ww)

        # 불출 단품
        params.extend(wp)
        sub_queries.append(f"""
            SELECT FORMAT(w.[Date],'yyyy-MM') AS YearMonth,
                   ISNULL(b.Name, N'미분류') AS BrandName,
                   N'불출' AS ChannelName,
                   w.UniqueCode, w.ProductName,
                   w.PlannedQty AS ComponentQuantity
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
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
                   w.PlannedQty * CAST(bom.QuantityRequired AS int) AS ComponentQuantity
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            INNER JOIN ProductBOM bom ON bom.ParentProductID = pr.ProductID
            INNER JOIN Product cp ON bom.ChildProductID = cp.ProductID
            WHERE {ww_str}
        """)

    full_query = f"""
        SELECT YearMonth, BrandName, ChannelName, UniqueCode, ProductName,
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
        ym, brand, channel, code, name, qty = row
        brand = brand or '미분류'
        channel = channel or '미분류'
        code = code or ''
        name = name or ''
        qty = int(qty or 0)

        year_months_set[ym] = True
        key = (brand, channel, code, name)

        if key not in product_map:
            product_map[key] = {
                'brand': brand,
                'channel': channel,
                'name': name,
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
    user: CurrentUser = Depends(get_current_user)
):
    """BOM 분해 피벗 데이터 조회 (수량만)"""
    query, params = _build_bom_query(year_month_from, year_month_to, input_month, brand, channel)

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
    user: CurrentUser = Depends(get_current_user)
):
    """BOM 분해 엑셀 다운로드 (수량만 피벗)"""
    import xlsxwriter

    query, params = _build_bom_query(year_month_from, year_month_to, input_month, brand, channel)

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

    headers = ['브랜드', '채널', '상품명']
    for ym in year_months:
        headers.append(f'{ym}(수량)')
    headers.append('합계(수량)')

    for i, h in enumerate(headers):
        fmt = total_header_fmt if h.startswith('합계') else header_fmt
        worksheet.write(0, i, h, fmt)

    for row_idx, item in enumerate(data, start=1):
        worksheet.write(row_idx, 0, item['brand'], text_fmt)
        worksheet.write(row_idx, 1, item['channel'], text_fmt)
        worksheet.write(row_idx, 2, item['name'], text_fmt)

        col = 3
        for ym in year_months:
            qty = item['months'].get(ym, 0)
            worksheet.write(row_idx, col, qty, num_fmt)
            col += 1

        worksheet.write(row_idx, col, item['totalQuantity'], total_num_fmt)

    worksheet.set_column(0, 0, 12)
    worksheet.set_column(1, 1, 14)
    worksheet.set_column(2, 2, 25)
    if len(headers) > 3:
        worksheet.set_column(3, len(headers) - 1, 14)

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


# ==================== SKU 관리 ====================

def _build_sku_summary_query(
    year_month_from: str, year_month_to: str,
    input_month: Optional[str] = None,
    brand: Optional[str] = None,
    channel: Optional[str] = None
):
    """SKU 단위 합산 쿼리 (UniqueCode+ProductName 기준)"""
    params = []

    # --- 3P 정기 ---
    w3r = ["FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([year_month_from, year_month_to])
    if input_month:
        w3r.append("t.InputMonth = ?"); params.append(input_month)
    if brand:
        w3r.append("t.BrandName = ?"); params.append(brand)
    if channel:
        w3r.append("t.ChannelName = ?"); params.append(channel)
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
    if brand:
        w3i.append("p.BrandName = ?"); params.append(brand)
    if channel:
        w3i.append("p.ChannelName = ?"); params.append(channel)
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
    if brand:
        w1r.append("t.BrandName = ?"); params.append(brand)
    if channel:
        w1r.append("t.ChannelName = ?"); params.append(channel)
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
    if brand:
        w1i.append("p.BrandName = ?"); params.append(brand)
    if channel:
        w1i.append("p.ChannelName = ?"); params.append(channel)
    q1i = f"""
        SELECT pp.UniqueCode, pp.ProductName, p.BrandName,
               pp.ExpectedSalesAmount AS ExpectedAmount, pp.ExpectedQuantity
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        WHERE {' AND '.join(w1i)}
    """

    # --- 불출 ---
    include_withdrawal = (channel is None or channel == '불출')
    if include_withdrawal:
        wwp = ["FORMAT(w.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
        params.extend([year_month_from, year_month_to])
        if input_month:
            wwp.append("w.InputMonth = ?"); params.append(input_month)
        if brand:
            wwp.append("b.Name = ?"); params.append(brand)
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
    channel: Optional[str] = None
):
    """특정 SKU의 채널/구분별 상세 쿼리 (개별 레코드 ID 포함, 인라인 편집용)"""
    params = []

    # --- 3P 정기 ---
    w3r = ["t.UniqueCode = ?", "FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([unique_code, year_month_from, year_month_to])
    if input_month:
        w3r.append("t.InputMonth = ?"); params.append(input_month)
    if brand:
        w3r.append("t.BrandName = ?"); params.append(brand)
    if channel:
        w3r.append("t.ChannelName = ?"); params.append(channel)
    q3r = f"""
        SELECT t.Expected3PRegularID AS RecordID,
               FORMAT(t.[Date], 'yyyy-MM') AS YearMonth,
               t.ChannelName, N'3P정기' AS SourceType,
               ISNULL(t.ExpectedAmount, 0) AS ExpectedAmount,
               ISNULL(t.ExpectedQuantity, 0) AS ExpectedQuantity
        FROM Expected3PRegularProduct t
        WHERE {' AND '.join(w3r)}
    """

    # --- 3P 비정기 ---
    w3i = ["pp.UniqueCode = ?", "FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([unique_code, year_month_from, year_month_to])
    if input_month:
        w3i.append("p.InputMonth = ?"); params.append(input_month)
    if brand:
        w3i.append("p.BrandName = ?"); params.append(brand)
    if channel:
        w3i.append("p.ChannelName = ?"); params.append(channel)
    q3i = f"""
        SELECT pp.Expected3PIrregularProductID AS RecordID,
               FORMAT(p.StartDate, 'yyyy-MM') AS YearMonth,
               p.ChannelName, N'3P비정기' AS SourceType,
               ISNULL(pp.ExpectedSalesAmount, 0) AS ExpectedAmount,
               ISNULL(pp.ExpectedQuantity, 0) AS ExpectedQuantity
        FROM Expected3PIrregularProduct pp
        INNER JOIN Expected3PIrregular p ON pp.Expected3PIrregularID = p.Expected3PIrregularID
        WHERE {' AND '.join(w3i)}
    """

    # --- 1P 정기 ---
    w1r = ["t.UniqueCode = ?", "FORMAT(t.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([unique_code, year_month_from, year_month_to])
    if input_month:
        w1r.append("t.InputMonth = ?"); params.append(input_month)
    if brand:
        w1r.append("t.BrandName = ?"); params.append(brand)
    if channel:
        w1r.append("t.ChannelName = ?"); params.append(channel)
    q1r = f"""
        SELECT t.Expected1PRegularID AS RecordID,
               FORMAT(t.[Date], 'yyyy-MM') AS YearMonth,
               t.ChannelName, N'1P정기' AS SourceType,
               ISNULL(t.ExpectedAmount, 0) AS ExpectedAmount,
               ISNULL(t.ExpectedQuantity, 0) AS ExpectedQuantity
        FROM Expected1PRegularProduct t
        WHERE {' AND '.join(w1r)}
    """

    # --- 1P 비정기 ---
    w1i = ["pp.UniqueCode = ?", "FORMAT(p.StartDate, 'yyyy-MM') BETWEEN ? AND ?"]
    params.extend([unique_code, year_month_from, year_month_to])
    if input_month:
        w1i.append("p.InputMonth = ?"); params.append(input_month)
    if brand:
        w1i.append("p.BrandName = ?"); params.append(brand)
    if channel:
        w1i.append("p.ChannelName = ?"); params.append(channel)
    q1i = f"""
        SELECT pp.Expected1PIrregularProductID AS RecordID,
               FORMAT(p.StartDate, 'yyyy-MM') AS YearMonth,
               p.ChannelName, N'1P비정기' AS SourceType,
               ISNULL(pp.ExpectedSalesAmount, 0) AS ExpectedAmount,
               ISNULL(pp.ExpectedQuantity, 0) AS ExpectedQuantity
        FROM Expected1PIrregularProduct pp
        INNER JOIN Expected1PIrregular p ON pp.Expected1PIrregularID = p.Expected1PIrregularID
        WHERE {' AND '.join(w1i)}
    """

    # --- 불출 ---
    include_withdrawal = (channel is None or channel == '불출')
    if include_withdrawal:
        wwp = ["w.UniqueCode = ?", "FORMAT(w.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
        params.extend([unique_code, year_month_from, year_month_to])
        if input_month:
            wwp.append("w.InputMonth = ?"); params.append(input_month)
        if brand:
            wwp.append("b.Name = ?"); params.append(brand)
        qwp = f"""
            SELECT w.PlanID AS RecordID,
                   FORMAT(w.[Date], 'yyyy-MM') AS YearMonth,
                   N'불출' AS ChannelName, N'불출' AS SourceType,
                   0 AS ExpectedAmount,
                   ISNULL(w.PlannedQty, 0) AS ExpectedQuantity
            FROM WithdrawalPlan w
            LEFT JOIN Product pr ON w.UniqueCode = pr.UniqueCode
            LEFT JOIN Brand b ON pr.BrandID = b.BrandID
            WHERE {' AND '.join(wwp)}
        """

    sub_queries = [q3r, q3i, q1r, q1i]
    if include_withdrawal:
        sub_queries.append(qwp)

    full_query = f"""
        SELECT RecordID, YearMonth, ChannelName, SourceType,
               ExpectedAmount, ExpectedQuantity
        FROM (
            {' UNION ALL '.join(sub_queries)}
        ) AS Combined
        ORDER BY ChannelName, SourceType, YearMonth
    """

    return full_query, params


@router.get("/sku-data")
async def get_sku_data(
    year_month_from: str = Query(...),
    year_month_to: str = Query(...),
    input_month: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user)
):
    """SKU 단위 합산 데이터 조회"""
    query, params = _build_sku_summary_query(
        year_month_from, year_month_to, input_month, brand, channel
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
    current_user: CurrentUser = Depends(get_current_user)
):
    """특정 SKU의 채널/구분별 상세 데이터 (개별 레코드 ID 포함)"""
    query, params = _build_sku_detail_query(
        unique_code, year_month_from, year_month_to,
        input_month, brand, channel
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
            "amount": float(row[4]) if row[4] else 0,
            "quantity": int(row[5]) if row[5] else 0
        }
        for row in rows
    ]


# ==================== SKU 인라인 편집 ====================

class SkuInlineUpdateItem(BaseModel):
    recordId: int
    sourceType: str
    amount: Optional[float] = None
    quantity: Optional[int] = None


class SkuInlineUpdateRequest(BaseModel):
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

    try:
        with get_db_cursor() as cursor:
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
                    # 매출+수량 편집 (3P/1P 정기/비정기)
                    cursor.execute(
                        f"SELECT {amount_col}, {qty_col} FROM [dbo].[{table}] WHERE {pk} = ?",
                        record_id
                    )
                    old_row = cursor.fetchone()
                    if not old_row:
                        continue

                    new_amount = float(item.amount or 0)
                    new_qty = int(item.quantity or 0)
                    old_data = {amount_col: old_row[0], qty_col: old_row[1]}
                    new_data = {amount_col: new_amount, qty_col: new_qty}

                    log_changes(cursor, table, pk, record_id, old_data, new_data, user_id)

                    new_ex_vat = calculate_amount_ex_vat(new_amount)
                    cursor.execute(
                        f"""UPDATE [dbo].[{table}]
                            SET {amount_col} = ?, {ex_vat_col} = ?,
                                {qty_col} = ?, UpdatedDate = GETDATE()
                            WHERE {pk} = ?""",
                        new_amount, new_ex_vat, new_qty, record_id
                    )
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
                    old_data = {qty_col: old_row[0]}
                    new_data = {qty_col: new_qty}

                    log_changes(cursor, table, pk, record_id, old_data, new_data, user_id)

                    cursor.execute(
                        f"""UPDATE [dbo].[{table}]
                            SET {qty_col} = ?, UpdatedDate = GETDATE()
                            WHERE {pk} = ?""",
                        new_qty, record_id
                    )

                if cursor.rowcount > 0:
                    total_updated += 1

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"저장 실패: {str(e)}")

    return {"message": f"{total_updated}건이 수정되었습니다", "updated": total_updated}
