"""
Coupang Router
- 쿠팡 판매(CoupangSales) / 재고(CoupangInventory) 데이터 업로드 API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
import pandas as pd
import io
from datetime import datetime
from core import get_db_cursor
from core.dependencies import CurrentUser
from core import require_permission

router = APIRouter(prefix="/api/coupang", tags=["Coupang"])


def load_coupang_sku_mapping() -> dict:
    """
    ProductBox.CoupangSKU → (BoxID, BrandID) 매핑 테이블 로드
    """
    mapping = {}
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT pb.CoupangSKU, pb.BoxID, p.BrandID
            FROM [dbo].[ProductBox] pb
            JOIN [dbo].[Product] p ON pb.ProductID = p.ProductID
            WHERE pb.CoupangSKU IS NOT NULL AND pb.CoupangSKU != ''
        """)
        for row in cursor.fetchall():
            mapping[str(row[0]).strip()] = {"BoxID": row[1], "BrandID": row[2]}
    return mapping


# ============================================================
# 쿠팡 판매 데이터 업로드 (Excel)
# ============================================================

SALES_COL_MAP = {
    "날짜": "Date",
    "Product ID": "ProductID_Coupang",
    "바코드": "Barcode",
    "SKU ID": "SKUID",
    "SKU 명": "SKUName",
    "벤더아이템 ID": "VendorItemID",
    "벤더아이템명": "VendorItemName",
    "로켓프레시": "IsRocketFresh",
    "상품카테고리": "ProductCategory",
    "하위카테고리": "SubCategory",
    "세부카테고리": "DetailCategory",
    "브랜드": "Brand",
    "매출액(GMV)": "GMV",
    "판매수량(Units Sold)": "UnitsSold",
    "반품수량(Return Units)": "ReturnUnits",
    "매입원가(COGS)": "COGS",
    "AMV": "AMV",
    "쿠폰 할인가(쿠팡 추가 할인가 제외)": "CouponDiscount",
    "쿠팡 추가 할인가": "CoupangExtraDiscount",
    "즉시 할인가": "InstantDiscount",
    "프로모션발생매출액(GMV)": "PromoGMV",
    "프로모션발생판매수량(Units Sold)": "PromoUnitsSold",
    "평균판매금액(ASP)": "ASP",
    "주문건수": "OrderCount",
    "주문 고객 수": "OrderCustomerCount",
    "객단가": "PricePerCustomer",
    "구매전환율": "ConversionRate",
    "PV": "PV",
    "정기배송 매출액(SnS GMV)": "SnSGMV",
    "정기배송 매입원가(SnS COGS)": "SnSCOGS",
    "정기배송 비중(SnS %)": "SnSPercent",
    "정기배송 판매수량(SnS Units Sold)": "SnSUnitsSold",
    "정기배송 반품수량(Return Units)": "SnSReturnUnits",
    "상품평 수": "ReviewCount",
    "평균 상품 평점": "AvgRating",
}

SALES_MERGE_SQL = """
MERGE INTO [dbo].[CoupangSales] AS target
USING (SELECT ? AS [Date], ? AS SKUID, ? AS VendorItemID) AS source
ON  target.[Date]        = source.[Date]
AND target.SKUID         = source.SKUID
AND target.VendorItemID  = source.VendorItemID
WHEN MATCHED THEN UPDATE SET
    ProductID_Coupang = ?, Barcode = ?, SKUName = ?, VendorItemName = ?,
    IsRocketFresh = ?, ProductCategory = ?, SubCategory = ?, DetailCategory = ?,
    Brand = ?, GMV = ?, UnitsSold = ?, ReturnUnits = ?, COGS = ?, AMV = ?,
    CouponDiscount = ?, CoupangExtraDiscount = ?, InstantDiscount = ?,
    PromoGMV = ?, PromoUnitsSold = ?, ASP = ?, OrderCount = ?,
    OrderCustomerCount = ?, PricePerCustomer = ?, ConversionRate = ?, PV = ?,
    SnSGMV = ?, SnSCOGS = ?, SnSPercent = ?, SnSUnitsSold = ?, SnSReturnUnits = ?,
    ReviewCount = ?, AvgRating = ?, BoxID = ?, BrandID = ?, CollectedDate = getdate()
WHEN NOT MATCHED THEN INSERT (
    [Date], SKUID, VendorItemID,
    ProductID_Coupang, Barcode, SKUName, VendorItemName,
    IsRocketFresh, ProductCategory, SubCategory, DetailCategory,
    Brand, GMV, UnitsSold, ReturnUnits, COGS, AMV,
    CouponDiscount, CoupangExtraDiscount, InstantDiscount,
    PromoGMV, PromoUnitsSold, ASP, OrderCount,
    OrderCustomerCount, PricePerCustomer, ConversionRate, PV,
    SnSGMV, SnSCOGS, SnSPercent, SnSUnitsSold, SnSReturnUnits,
    ReviewCount, AvgRating, BoxID, BrandID
) VALUES (
    ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?,
    ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?, ?,
    ?, ?, ?, ?
);
"""


@router.post("/upload/sales")
async def upload_coupang_sales(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_permission("Coupang", "UPLOAD"))
):
    """쿠팡 판매 데이터 업로드 (Excel)"""
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Excel 파일(.xlsx, .xls)만 업로드 가능합니다.")

    content = await file.read()
    df = pd.read_excel(io.BytesIO(content), sheet_name="RAW DATA")

    # 컬럼 매핑
    df = df.rename(columns=SALES_COL_MAP)

    # 필수 컬럼 확인
    required = ["Date", "SKUID", "VendorItemID"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"필수 컬럼 누락: {missing}")

    # 날짜 변환
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df = df[df["Date"].notna()]

    # 문자열 변환
    df["SKUID"] = df["SKUID"].astype(str).str.strip()
    df["VendorItemID"] = df["VendorItemID"].astype(str).str.strip()

    # BoxID / BrandID 매핑
    sku_map = load_coupang_sku_mapping()
    df["BoxID"] = df["SKUID"].map(lambda x: sku_map.get(x, {}).get("BoxID"))
    df["BrandID"] = df["SKUID"].map(lambda x: sku_map.get(x, {}).get("BrandID"))

    unmapped = int(df["BoxID"].isna().sum())

    # None 처리 헬퍼
    def v(val):
        if pd.isna(val) if not isinstance(val, str) else False:
            return None
        return val

    inserted = updated = failed = 0

    with get_db_cursor() as cursor:
        for _, row in df.iterrows():
            try:
                params_key = (row["Date"], row["SKUID"], row["VendorItemID"])
                params_data = (
                    v(row.get("ProductID_Coupang")), v(row.get("Barcode")),
                    v(row.get("SKUName")), v(row.get("VendorItemName")),
                    v(row.get("IsRocketFresh")), v(row.get("ProductCategory")),
                    v(row.get("SubCategory")), v(row.get("DetailCategory")),
                    v(row.get("Brand")), v(row.get("GMV")), v(row.get("UnitsSold")),
                    v(row.get("ReturnUnits")), v(row.get("COGS")), v(row.get("AMV")),
                    v(row.get("CouponDiscount")), v(row.get("CoupangExtraDiscount")),
                    v(row.get("InstantDiscount")), v(row.get("PromoGMV")),
                    v(row.get("PromoUnitsSold")), v(row.get("ASP")),
                    v(row.get("OrderCount")), v(row.get("OrderCustomerCount")),
                    v(row.get("PricePerCustomer")), v(row.get("ConversionRate")),
                    v(row.get("PV")), v(row.get("SnSGMV")), v(row.get("SnSCOGS")),
                    v(row.get("SnSPercent")), v(row.get("SnSUnitsSold")),
                    v(row.get("SnSReturnUnits")), v(row.get("ReviewCount")),
                    v(row.get("AvgRating")),
                    v(row.get("BoxID")), v(row.get("BrandID")),
                )
                cursor.execute(
                    SALES_MERGE_SQL,
                    (*params_key, *params_data, *params_key, *params_data)
                )
                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1
            except Exception as e:
                failed += 1
                print(f"[CoupangSales 오류] {row.get('SKUID')} / {row.get('VendorItemID')}: {e}")

    return {
        "success": True,
        "filename": file.filename,
        "total": len(df),
        "inserted": inserted,
        "updated": updated,
        "failed": failed,
        "unmapped_sku": unmapped,
    }


# ============================================================
# 쿠팡 재고 데이터 업로드 (CSV)
# ============================================================

INVENTORY_COL_MAP = {
    "날짜": "Date",
    "상품 카테고리": "ProductCategory",
    "하위 카테고리": "SubCategory",
    "세부 카테고리": "DetailCategory",
    "브랜드": "Brand",
    "센터": "Center",
    "SKU ID": "SKUID",
    "SKU 명": "SKUName",
    "바코드": "Barcode",
    "발주가능상태": "OrderableStatus",
    "발주가능상태_세부": "OrderableStatusDetail",
    "입고수량": "InboundQty",
    "출고수량": "OutboundQty",
    "현재재고수량": "CurrentStockQty",
    "매입원가": "PurchaseCost",
    "발주대비 납품율": "OrderFulfillmentRate",
    "확정대비 납품율": "ConfirmFulfillmentRate",
    "회송율": "ReturnRate",
    "회송사유": "ReturnReason",
    "품절여부": "SoldOut",
    "세부카테고리 품절율": "DetailCategorySoldOutRate",
}

INVENTORY_MERGE_SQL = """
MERGE INTO [dbo].[CoupangInventory] AS target
USING (SELECT ? AS [Date], ? AS SKUID, ? AS Center) AS source
ON  target.[Date]   = source.[Date]
AND target.SKUID    = source.SKUID
AND target.Center   = source.Center
WHEN MATCHED THEN UPDATE SET
    ProductCategory = ?, SubCategory = ?, DetailCategory = ?, Brand = ?,
    SKUName = ?, Barcode = ?, OrderableStatus = ?, OrderableStatusDetail = ?,
    InboundQty = ?, OutboundQty = ?, CurrentStockQty = ?, PurchaseCost = ?,
    OrderFulfillmentRate = ?, ConfirmFulfillmentRate = ?, ReturnRate = ?,
    ReturnReason = ?, SoldOut = ?, DetailCategorySoldOutRate = ?,
    BoxID = ?, BrandID = ?, CollectedDate = getdate()
WHEN NOT MATCHED THEN INSERT (
    [Date], SKUID, Center,
    ProductCategory, SubCategory, DetailCategory, Brand,
    SKUName, Barcode, OrderableStatus, OrderableStatusDetail,
    InboundQty, OutboundQty, CurrentStockQty, PurchaseCost,
    OrderFulfillmentRate, ConfirmFulfillmentRate, ReturnRate,
    ReturnReason, SoldOut, DetailCategorySoldOutRate,
    BoxID, BrandID
) VALUES (
    ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?,
    ?, ?, ?,
    ?, ?
);
"""


@router.post("/upload/inventory")
async def upload_coupang_inventory(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_permission("Coupang", "UPLOAD"))
):
    """쿠팡 재고 데이터 업로드 (CSV)"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV 파일만 업로드 가능합니다.")

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")

    # 컬럼 매핑
    df = df.rename(columns=INVENTORY_COL_MAP)

    # 필수 컬럼 확인
    required = ["Date", "SKUID", "Center"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"필수 컬럼 누락: {missing}")

    # 날짜 변환 (YYYYMMDD 형식)
    df["Date"] = pd.to_datetime(df["Date"].astype(str), format="%Y%m%d", errors="coerce").dt.date
    df = df[df["Date"].notna()]

    df["SKUID"] = df["SKUID"].astype(str).str.strip()
    df["Center"] = df["Center"].astype(str).str.strip()

    # BoxID / BrandID 매핑
    sku_map = load_coupang_sku_mapping()
    df["BoxID"] = df["SKUID"].map(lambda x: sku_map.get(x, {}).get("BoxID"))
    df["BrandID"] = df["SKUID"].map(lambda x: sku_map.get(x, {}).get("BrandID"))

    unmapped = int(df["BoxID"].isna().sum())

    def v(val):
        if pd.isna(val) if not isinstance(val, str) else False:
            return None
        return val

    inserted = updated = failed = 0

    with get_db_cursor() as cursor:
        for _, row in df.iterrows():
            try:
                params_key = (row["Date"], row["SKUID"], row["Center"])
                params_data = (
                    v(row.get("ProductCategory")), v(row.get("SubCategory")),
                    v(row.get("DetailCategory")), v(row.get("Brand")),
                    v(row.get("SKUName")), v(row.get("Barcode")),
                    v(row.get("OrderableStatus")), v(row.get("OrderableStatusDetail")),
                    v(row.get("InboundQty")), v(row.get("OutboundQty")),
                    v(row.get("CurrentStockQty")), v(row.get("PurchaseCost")),
                    v(row.get("OrderFulfillmentRate")), v(row.get("ConfirmFulfillmentRate")),
                    v(row.get("ReturnRate")), v(row.get("ReturnReason")),
                    v(row.get("SoldOut")), v(row.get("DetailCategorySoldOutRate")),
                    v(row.get("BoxID")), v(row.get("BrandID")),
                )
                cursor.execute(
                    INVENTORY_MERGE_SQL,
                    (*params_key, *params_data, *params_key, *params_data)
                )
                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1
            except Exception as e:
                failed += 1
                print(f"[CoupangInventory 오류] {row.get('SKUID')} / {row.get('Center')}: {e}")

    return {
        "success": True,
        "filename": file.filename,
        "total": len(df),
        "inserted": inserted,
        "updated": updated,
        "failed": failed,
        "unmapped_sku": unmapped,
    }