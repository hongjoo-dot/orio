"""
예상 판매량 통합 조회 Router
- 위탁(3P) 정기/비정기, 사입(1P) 정기/비정기, 불출 데이터를 통합 조회
- 피벗 테이블: 행=브랜드/채널/상품, 열=연월
- 읽기 전용 (조회 + 엑셀 다운로드)
"""

from fastapi import APIRouter, Query, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from collections import OrderedDict
from urllib.parse import quote
import io
from core import get_db_cursor
from core.dependencies import get_current_user, CurrentUser

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

    # --- 불출 (InputMonth 없음) ---
    # 채널 필터가 '불출'이 아닌 값이면 불출 서브쿼리 제외
    include_withdrawal = (channel is None or channel == '불출')
    if include_withdrawal:
        wwp = ["FORMAT(w.[Date], 'yyyy-MM') BETWEEN ? AND ?"]
        params.extend([year_month_from, year_month_to])
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
        ) AS AllInputMonths
        WHERE im IS NOT NULL
        ORDER BY im DESC
    """
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query,
            year_month_from, year_month_to, year_month_from, year_month_to,
            year_month_from, year_month_to, year_month_from, year_month_to)
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
