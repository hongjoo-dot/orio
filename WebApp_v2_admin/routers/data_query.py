"""
데이터 조회 Router
- ERPSales 일별 채널별 제품별 매출 조회 (채널별 그룹 + 일자 피벗)
- 읽기 전용 (조회 + 엑셀 다운로드)
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
from core.database import get_db_cursor
from core.dependencies import require_permission, CurrentUser
from urllib.parse import quote
from collections import OrderedDict
import pandas as pd
import io

router = APIRouter(prefix="/api/data-query", tags=["DataQuery"])


def _fetch_daily_sales(
    brand_id: Optional[int] = None,
    channel_name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """일별 채널별 제품별 매출 원본 데이터 조회"""
    params = []
    where = ["e.Quantity > 0", "e.PRODUCT_NAME NOT LIKE N'%배송%'"]

    if brand_id:
        where.append("e.BrandID = ?")
        params.append(brand_id)
    if channel_name:
        where.append("e.ChannelName = ?")
        params.append(channel_name)
    if date_from:
        where.append("e.[DATE] >= ?")
        params.append(date_from)
    if date_to:
        where.append("e.[DATE] <= ?")
        params.append(date_to)

    where_clause = " AND ".join(where)

    query = f"""
        SELECT
            e.ChannelName,
            e.ERPCode,
            e.PRODUCT_NAME,
            CONVERT(char(10), e.[DATE], 23) AS SaleDate,
            SUM(e.Quantity) AS TotalQuantity,
            SUM(e.TaxableAmount) AS TotalAmount
        FROM [dbo].[ERPSales] e
        WHERE {where_clause}
        GROUP BY e.ChannelName, e.ERPCode, e.PRODUCT_NAME, CONVERT(char(10), e.[DATE], 23)
        ORDER BY e.ChannelName, e.PRODUCT_NAME, SaleDate
    """

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(query, *params)
        return cursor.fetchall()


def _pivot_data(rows):
    """원본 데이터를 채널별 그룹 + 일자 피벗 구조로 변환"""
    # 일자 목록 수집 (정렬)
    dates_set = OrderedDict()
    # 채널 > 제품 > 일자별 데이터
    channel_map = OrderedDict()

    for row in rows:
        channel = row[0] or "미분류"
        erp_code = row[1] or ""
        product_name = row[2] or ""
        sale_date = row[3]
        quantity = float(row[4] or 0)
        amount = float(row[5] or 0)

        dates_set[sale_date] = True

        if channel not in channel_map:
            channel_map[channel] = OrderedDict()

        product_key = f"{erp_code}||{product_name}"
        if product_key not in channel_map[channel]:
            channel_map[channel][product_key] = {
                "ERPCode": erp_code,
                "PRODUCT_NAME": product_name,
                "dates": {}
            }

        channel_map[channel][product_key]["dates"][sale_date] = {
            "Quantity": quantity,
            "TaxableAmount": amount
        }

    dates = list(dates_set.keys())

    # 응답 구조 생성
    channels = []
    for channel_name, products in channel_map.items():
        product_list = []
        for product_key, product_data in products.items():
            daily = {}
            for d in dates:
                val = product_data["dates"].get(d, {"Quantity": 0, "TaxableAmount": 0})
                daily[d] = val
            product_list.append({
                "ERPCode": product_data["ERPCode"],
                "PRODUCT_NAME": product_data["PRODUCT_NAME"],
                "daily": daily
            })
        channels.append({
            "ChannelName": channel_name,
            "products": product_list
        })

    return {"dates": dates, "channels": channels}


@router.get("/daily-sales")
async def get_daily_sales(
    brand_id: Optional[int] = None,
    channel_name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("DataQuery", "READ")),
):
    """일별 채널별 제품별 매출 조회 (채널별 그룹 + 일자 피벗)"""
    try:
        rows = _fetch_daily_sales(
            brand_id=brand_id, channel_name=channel_name,
            date_from=date_from, date_to=date_to,
        )
        return _pivot_data(rows)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/daily-sales/download/excel")
async def download_daily_sales_excel(
    brand_id: Optional[int] = None,
    channel_name: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("DataQuery", "EXPORT")),
):
    """일별 매출 데이터 엑셀 다운로드 (채널별 그룹 + 일자 피벗)"""
    try:
        rows = _fetch_daily_sales(
            brand_id=brand_id, channel_name=channel_name,
            date_from=date_from, date_to=date_to,
        )
        pivot = _pivot_data(rows)
        dates = pivot["dates"]

        # 엑셀 행 데이터 구성
        excel_rows = []
        for ch in pivot["channels"]:
            # 채널 구분 행
            excel_rows.append({"채널": ch["ChannelName"], "ERPCode": "", "상품명": ""})
            for product in ch["products"]:
                row_qty = {"채널": "", "ERPCode": product["ERPCode"], "상품명": product["PRODUCT_NAME"] + " (수량)"}
                row_amt = {"채널": "", "ERPCode": "", "상품명": product["PRODUCT_NAME"] + " (매출)"}
                for d in dates:
                    val = product["daily"].get(d, {"Quantity": 0, "TaxableAmount": 0})
                    row_qty[d] = val["Quantity"]
                    row_amt[d] = val["TaxableAmount"]
                excel_rows.append(row_qty)
                excel_rows.append(row_amt)
            # 채널 간 빈 행
            excel_rows.append({})

        df = pd.DataFrame(excel_rows)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="일별매출")
            worksheet = writer.sheets["일별매출"]
            for i, col in enumerate(df.columns):
                max_len = max(
                    df[col].astype(str).map(len).max() if len(df) > 0 else 0,
                    len(str(col)),
                )
                from openpyxl.utils import get_column_letter
                worksheet.column_dimensions[get_column_letter(i + 1)].width = min(max_len + 4, 40)

        output.seek(0)

        download_name = "일별매출_조회결과.xlsx"
        encoded_name = quote(download_name)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다운로드 실패: {str(e)}")


@router.get("/metadata")
async def get_metadata(
    user: CurrentUser = Depends(require_permission("DataQuery", "READ")),
):
    """필터용 메타데이터 (브랜드, 채널 목록)"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT BrandID, Name FROM [dbo].[Brand] WHERE IsActive = 1 ORDER BY Name")
            brands = [{"BrandID": row[0], "Name": row[1]} for row in cursor.fetchall()]

            cursor.execute("""
                SELECT DISTINCT ChannelName
                FROM [dbo].[ERPSales]
                WHERE ChannelName IS NOT NULL
                ORDER BY ChannelName
            """)
            channels = [row[0] for row in cursor.fetchall()]

        return {"brands": brands, "channels": channels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메타데이터 조회 실패: {str(e)}")
