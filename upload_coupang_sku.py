"""
CoupangSKU 매핑 업로드 스크립트
- 엑셀 파일에서 ERPCode, CoupangSKU를 읽어 Product 테이블에 업데이트
- 하나라도 매핑 실패 시 전체 롤백
"""

import sys
import pandas as pd
from pathlib import Path

# WebApp_v2_admin의 DB 연결 모듈 재사용
sys.path.insert(0, str(Path(__file__).parent / "WebApp_v2_admin"))
from core.database import get_db_cursor


def upload_coupang_sku(file_path: str):
    """엑셀 파일의 ERPCode-CoupangSKU 매핑을 Product 테이블에 업데이트"""

    # 1. 엑셀 읽기
    df = pd.read_excel(file_path, engine="openpyxl", header=0)
    print(f"[1] 엑셀 로드 완료: {len(df)}행")

    # ERPCode, CoupangSKU 컬럼 찾기
    erp_col = None
    sku_col = None
    for col in df.columns:
        col_lower = str(col).strip().lower()
        if col_lower == "erpcode":
            erp_col = col
        elif col_lower == "coupangsku":
            sku_col = col

    if erp_col is None or sku_col is None:
        print(f"[오류] 'ERPCode'와 'CoupangSKU' 컬럼이 필요합니다. 현재 컬럼: {list(df.columns)}")
        return

    # 2. 데이터 추출
    items = []
    for idx, row in df.iterrows():
        erp_code = str(row[erp_col]).strip() if pd.notna(row[erp_col]) else ""
        coupang_sku = str(row[sku_col]).strip() if pd.notna(row[sku_col]) else ""

        if not erp_code or erp_code == "nan":
            continue

        items.append({"row": idx + 2, "erp_code": erp_code, "coupang_sku": coupang_sku})

    if not items:
        print("[오류] 유효한 데이터가 없습니다")
        return

    print(f"[2] 유효 데이터: {len(items)}건")

    # 3. DB에서 ERPCode → Product 매핑 조회
    erp_codes = list(set(item["erp_code"] for item in items))

    with get_db_cursor(commit=False) as cursor:
        placeholders = ",".join(["?" for _ in erp_codes])
        cursor.execute(f"""
            SELECT pb.ERPCode, p.ProductID, p.UniqueCode, p.Name, p.CoupangSKU
            FROM [dbo].[ProductBox] pb
            JOIN [dbo].[Product] p ON pb.ProductID = p.ProductID
            WHERE pb.ERPCode IN ({placeholders})
        """, *erp_codes)

        erp_map = {}
        for row in cursor.fetchall():
            erp_map[row[0]] = {
                "ProductID": row[1],
                "UniqueCode": row[2],
                "Name": row[3],
                "CurrentSKU": row[4] or "",
            }

    # 4. 검증: 매핑 실패 확인
    errors = []
    mappings = []

    for item in items:
        if item["erp_code"] not in erp_map:
            errors.append(item)
        else:
            product = erp_map[item["erp_code"]]
            mappings.append({
                "ProductID": product["ProductID"],
                "ERPCode": item["erp_code"],
                "UniqueCode": product["UniqueCode"],
                "Name": product["Name"],
                "CurrentSKU": product["CurrentSKU"],
                "NewSKU": item["coupang_sku"],
            })

    if errors:
        print(f"\n[실패] 매핑되지 않는 ERPCode {len(errors)}건 → 전체 업데이트 중단")
        print("-" * 50)
        for e in errors:
            print(f"  행 {e['row']}: {e['erp_code']}")
        return

    # 5. 미리보기
    print(f"\n[3] 매핑 결과 미리보기 ({len(mappings)}건)")
    print("-" * 80)
    print(f"{'ERPCode':<15} {'UniqueCode':<15} {'상품명':<25} {'현재SKU':<15} → {'신규SKU'}")
    print("-" * 80)
    for m in mappings:
        name = m["Name"][:22] + "..." if len(m["Name"]) > 22 else m["Name"]
        print(f"{m['ERPCode']:<15} {m['UniqueCode']:<15} {name:<25} {m['CurrentSKU']:<15} → {m['NewSKU']}")

    # 6. 확인
    confirm = input(f"\n{len(mappings)}건을 업데이트하시겠습니까? (y/n): ").strip().lower()
    if confirm != "y":
        print("[취소] 업데이트가 취소되었습니다")
        return

    # 7. 트랜잭션 업데이트
    with get_db_cursor(commit=True) as cursor:
        for m in mappings:
            cursor.execute("""
                UPDATE [dbo].[Product]
                SET CoupangSKU = ?, UpdatedDate = GETDATE()
                WHERE ProductID = ?
            """, m["NewSKU"], m["ProductID"])

    print(f"\n[완료] {len(mappings)}건의 CoupangSKU가 업데이트되었습니다")


if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Python\상품목록_20260227.xlsx"
    upload_coupang_sku(file_path)
