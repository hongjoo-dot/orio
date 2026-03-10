"""
ProductBox 단가 업로드 스크립트
- 엑셀 파일에서 ERPCode 기준으로 UnitCostKRW, SalesPrice, SupplyPrice를 ProductBox에 업데이트
- 3개 컬럼 중 엑셀에 있는 것만 업데이트
- 하나라도 매핑 실패 시 전체 롤백
"""

import sys
import pandas as pd
from pathlib import Path

# WebApp_v2_admin의 DB 연결 모듈 직접 import (순환 import 방지)
import importlib.util

_db_path = Path(__file__).parent / "WebApp_v2_admin" / "core" / "database.py"
_spec = importlib.util.spec_from_file_location("database", _db_path)
_db_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_db_module)
get_db_cursor = _db_module.get_db_cursor

# 업로드 대상 컬럼 정의: (엑셀 컬럼명 소문자, DB 컬럼명, 미리보기 라벨)
PRICE_COLUMNS = [
    ("unitcostkrw", "UnitCostKRW", "원가"),
    ("salesprice", "SalesPrice", "판매가"),
    ("supplyprice", "SupplyPrice", "공급가"),
]


def upload_unit_cost(file_path: str):
    """엑셀 파일의 단가 정보를 ProductBox 테이블에 업데이트"""

    # 1. 엑셀 읽기
    df = pd.read_excel(file_path, engine="openpyxl", header=0)
    print(f"[1] 엑셀 로드 완료: {len(df)}행")

    # ERPCode 컬럼 찾기
    erp_col = None
    for col in df.columns:
        if str(col).strip().lower() == "erpcode":
            erp_col = col
            break

    if erp_col is None:
        print(f"[오류] 'ERPCode' 컬럼이 필요합니다. 현재 컬럼: {list(df.columns)}")
        return

    # 가격 컬럼 찾기 (있는 것만)
    col_map = {}  # {엑셀컬럼명: (DB컬럼명, 라벨)}
    col_lower_map = {str(c).strip().lower(): c for c in df.columns}
    for excel_key, db_col, label in PRICE_COLUMNS:
        if excel_key in col_lower_map:
            col_map[col_lower_map[excel_key]] = (db_col, label)

    if not col_map:
        print(f"[오류] UnitCostKRW, SalesPrice, SupplyPrice 중 하나 이상 필요합니다. 현재 컬럼: {list(df.columns)}")
        return

    found_labels = [label for _, (_, label) in col_map.items()]
    print(f"    → 업데이트 대상: {', '.join(found_labels)}")

    # 2. 데이터 추출
    items = []
    for idx, row in df.iterrows():
        erp_code = str(row[erp_col]).strip() if pd.notna(row[erp_col]) else ""

        if not erp_code or erp_code == "nan":
            continue

        prices = {}
        has_value = False
        for excel_col, (db_col, label) in col_map.items():
            val = row[excel_col]
            if pd.isna(val):
                continue
            try:
                prices[db_col] = float(val)
                has_value = True
            except (ValueError, TypeError):
                print(f"[오류] 행 {idx + 2}: {label} 값이 숫자가 아닙니다 → {val}")
                return

        if not has_value:
            continue

        items.append({"row": idx + 2, "erp_code": erp_code, "prices": prices})

    if not items:
        print("[오류] 유효한 데이터가 없습니다")
        return

    print(f"[2] 유효 데이터: {len(items)}건")

    # 3. DB에서 ERPCode → ProductBox 매핑 조회
    erp_codes = list(set(item["erp_code"] for item in items))
    db_cols = [db_col for _, (db_col, _) in col_map.items()]
    db_col_select = ", ".join(f"pb.{c}" for c in db_cols)

    with get_db_cursor(commit=False) as cursor:
        placeholders = ",".join(["?" for _ in erp_codes])
        cursor.execute(f"""
            SELECT pb.ERPCode, p.UniqueCode, p.Name, {db_col_select}
            FROM [dbo].[ProductBox] pb
            JOIN [dbo].[Product] p ON pb.ProductID = p.ProductID
            WHERE pb.ERPCode IN ({placeholders})
        """, *erp_codes)

        erp_map = {}
        for row in cursor.fetchall():
            current = {}
            for i, dc in enumerate(db_cols):
                current[dc] = row[3 + i]
            erp_map[row[0]] = {
                "UniqueCode": row[1],
                "Name": row[2],
                "current": current,
            }

    # 4. 검증: 매핑 실패 확인
    errors = []
    mappings = []

    for item in items:
        if item["erp_code"] not in erp_map:
            errors.append(item)
        else:
            info = erp_map[item["erp_code"]]
            mappings.append({
                "ERPCode": item["erp_code"],
                "UniqueCode": info["UniqueCode"],
                "Name": info["Name"],
                "current": info["current"],
                "new": item["prices"],
            })

    if errors:
        print(f"\n[실패] 매핑되지 않는 ERPCode {len(errors)}건 → 전체 업데이트 중단")
        print("-" * 50)
        for e in errors:
            print(f"  행 {e['row']}: {e['erp_code']}")
        return

    # 5. 미리보기
    labels = {db_col: label for _, (db_col, label) in col_map.items()}
    print(f"\n[3] 매핑 결과 미리보기 ({len(mappings)}건)")
    print("-" * 90)
    header = f"{'ERPCode':<15} {'UniqueCode':<15} {'상품명':<20}"
    for dc in db_cols:
        header += f" {labels[dc]}(현재→신규)"
    print(header)
    print("-" * 90)
    for m in mappings:
        name = m["Name"][:17] + "..." if len(m["Name"]) > 17 else m["Name"]
        line = f"{m['ERPCode']:<15} {m['UniqueCode']:<15} {name:<20}"
        for dc in db_cols:
            cur = f"{m['current'][dc]:,.0f}" if m["current"].get(dc) is not None else "-"
            if dc in m["new"]:
                line += f" {cur}→{m['new'][dc]:,.0f}"
            else:
                line += f" {cur}(유지)"
        print(line)

    # 6. 확인
    confirm = input(f"\n{len(mappings)}건을 업데이트하시겠습니까? (y/n): ").strip().lower()
    if confirm != "y":
        print("[취소] 업데이트가 취소되었습니다")
        return

    # 7. 트랜잭션 업데이트
    with get_db_cursor(commit=True) as cursor:
        for m in mappings:
            if not m["new"]:
                continue
            set_clause = ", ".join(f"{col} = ?" for col in m["new"])
            values = list(m["new"].values())
            values.append(m["ERPCode"])
            cursor.execute(f"""
                UPDATE [dbo].[ProductBox]
                SET {set_clause}
                WHERE ERPCode = ?
            """, *values)

    print(f"\n[완료] {len(mappings)}건의 단가 정보가 업데이트되었습니다")


if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Python\SDPRICE.xlsx"
    upload_unit_cost(file_path)