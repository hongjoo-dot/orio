"""
Utility Router
- 피벗 해제 등 데이터 변환 유틸리티 API
- BOM 분해 유틸리티 API
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from core.dependencies import require_permission
from core.database import get_db_cursor
import pandas as pd
import io
from urllib.parse import quote

router = APIRouter(prefix="/api/utilities", tags=["Utilities"])


def _read_excel_raw(file_bytes: bytes, header_rows: int = 1, fill_merged: bool = False):
    """엑셀 파일 읽기 (멀티 헤더 + 병합 셀 지원)

    Returns:
        tuple: (header_data, data_df)
        - header_data: 헤더 행들의 리스트 (각 행은 칼럼 값 리스트)
        - data_df: 데이터 부분 DataFrame
    """
    try:
        df_raw = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl', header=None)
    except Exception:
        try:
            df_raw = pd.read_excel(io.BytesIO(file_bytes), engine='xlrd', header=None)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"엑셀 파일을 읽을 수 없습니다: {str(e)}")

    if df_raw.empty:
        raise HTTPException(status_code=400, detail="엑셀 파일에 데이터가 없습니다")

    # 헤더 행들 추출
    header_df = df_raw.iloc[:header_rows].copy()

    # 병합 셀 처리: 각 헤더 행에서 NaN을 앞 값으로 채움
    if fill_merged:
        header_df = header_df.ffill(axis=1)

    # 헤더 데이터를 리스트로 변환
    header_data = []
    for row_idx in range(header_rows):
        row_values = []
        for col_idx in range(len(header_df.columns)):
            val = header_df.iloc[row_idx, col_idx]
            if pd.notna(val):
                val_str = str(val).strip()
                if not val_str.startswith('Unnamed'):
                    row_values.append(val_str)
                else:
                    row_values.append('')
            else:
                row_values.append('')
        header_data.append(row_values)

    # 데이터 부분 추출
    data_df = df_raw.iloc[header_rows:].copy()
    data_df = data_df.reset_index(drop=True)

    return header_data, data_df


def _unpivot_multi_header(header_data: list, data_df: pd.DataFrame, fixed_count: int) -> pd.DataFrame:
    """멀티 헤더 피벗 해제 변환

    헤더 행 수만큼 구분 칼럼이 생성됨:
    - 헤더 1행: 고정칼럼들 + 구분 + 값
    - 헤더 2행: 고정칼럼들 + 구분1 + 구분2 + 값
    """
    header_rows = len(header_data)
    total_cols = len(header_data[0]) if header_data else 0

    if fixed_count < 1:
        raise HTTPException(status_code=400, detail="고정 칼럼 수는 1 이상이어야 합니다")
    if fixed_count >= total_cols:
        raise HTTPException(status_code=400, detail="고정 칼럼 수가 전체 칼럼 수보다 작아야 합니다")

    # 고정 칼럼 이름 (첫 번째 헤더 행 또는 모든 헤더 행 합침)
    fixed_col_names = []
    for col_idx in range(fixed_count):
        parts = [header_data[row_idx][col_idx] for row_idx in range(header_rows) if header_data[row_idx][col_idx]]
        # 중복 제거
        unique_parts = []
        for p in parts:
            if not unique_parts or unique_parts[-1] != p:
                unique_parts.append(p)
        fixed_col_names.append('_'.join(unique_parts) if unique_parts else f'Column{col_idx}')

    # 결과 데이터 구성
    result_rows = []

    for data_row_idx in range(len(data_df)):
        # 고정 칼럼 값
        fixed_values = [data_df.iloc[data_row_idx, col_idx] for col_idx in range(fixed_count)]

        # 피벗 칼럼들 처리
        for col_idx in range(fixed_count, total_cols):
            # 각 헤더 행의 값을 구분 칼럼으로
            category_values = [header_data[row_idx][col_idx] for row_idx in range(header_rows)]
            # 데이터 값
            data_value = data_df.iloc[data_row_idx, col_idx]

            row = fixed_values + category_values + [data_value]
            result_rows.append(row)

    # 결과 칼럼 이름
    if header_rows == 1:
        category_col_names = ['구분']
    else:
        category_col_names = [f'구분{i+1}' for i in range(header_rows)]

    result_columns = fixed_col_names + category_col_names + ['값']

    result_df = pd.DataFrame(result_rows, columns=result_columns)

    # 고정 칼럼 기준 정렬
    result_df = result_df.sort_values(by=fixed_col_names).reset_index(drop=True)

    return result_df


@router.post("/unpivot/preview")
async def unpivot_preview(
    file: UploadFile = File(...),
    fixed_count: int = Form(...),
    header_rows: int = Form(1),
    fill_merged: bool = Form(False),
    _=Depends(require_permission("Utility", "READ"))
):
    """피벗 해제 미리보기 - 헤더 + 변환된 처음 10행"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        if header_rows < 1:
            raise HTTPException(status_code=400, detail="헤더 행 수는 1 이상이어야 합니다")

        file_bytes = await file.read()
        header_data, data_df = _read_excel_raw(file_bytes, header_rows, fill_merged)

        # 원본 헤더 (합친 형태로 표시)
        original_headers = []
        for col_idx in range(len(header_data[0])):
            parts = [header_data[row_idx][col_idx] for row_idx in range(header_rows) if header_data[row_idx][col_idx]]
            unique_parts = []
            for p in parts:
                if not unique_parts or unique_parts[-1] != p:
                    unique_parts.append(p)
            original_headers.append('_'.join(unique_parts) if unique_parts else f'Column{col_idx}')

        # 원본 데이터에 헤더 적용
        data_df.columns = original_headers
        original_preview = data_df.head(5).fillna('').to_dict(orient='records')

        # 변환
        result = _unpivot_multi_header(header_data, data_df, fixed_count)
        converted_headers = result.columns.tolist()
        converted_preview = result.head(10).fillna('').to_dict(orient='records')

        return {
            "original": {
                "headers": original_headers,
                "preview": original_preview,
                "total_rows": len(data_df),
                "total_cols": len(original_headers)
            },
            "converted": {
                "headers": converted_headers,
                "preview": converted_preview,
                "total_rows": len(result)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"미리보기 실패: {str(e)}")


@router.post("/unpivot/download")
async def unpivot_download(
    file: UploadFile = File(...),
    fixed_count: int = Form(...),
    header_rows: int = Form(1),
    fill_merged: bool = Form(False),
    _=Depends(require_permission("Utility", "READ"))
):
    """피벗 해제 후 엑셀 다운로드"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        if header_rows < 1:
            raise HTTPException(status_code=400, detail="헤더 행 수는 1 이상이어야 합니다")

        file_bytes = await file.read()
        header_data, data_df = _read_excel_raw(file_bytes, header_rows, fill_merged)

        # 원본 헤더 적용
        original_headers = []
        for col_idx in range(len(header_data[0])):
            parts = [header_data[row_idx][col_idx] for row_idx in range(header_rows) if header_data[row_idx][col_idx]]
            unique_parts = []
            for p in parts:
                if not unique_parts or unique_parts[-1] != p:
                    unique_parts.append(p)
            original_headers.append('_'.join(unique_parts) if unique_parts else f'Column{col_idx}')
        data_df.columns = original_headers

        result = _unpivot_multi_header(header_data, data_df, fixed_count)

        # 엑셀 생성
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result.to_excel(writer, index=False, sheet_name='변환결과')

            # 칼럼 너비 조정
            worksheet = writer.sheets['변환결과']
            for i, col in enumerate(result.columns):
                max_len = max(
                    result[col].astype(str).map(len).max() if len(result) > 0 else 0,
                    len(str(col))
                )
                worksheet.column_dimensions[chr(65 + i) if i < 26 else 'A'].width = min(max_len + 4, 40)

        output.seek(0)

        # 파일명 생성
        original_name = file.filename.rsplit('.', 1)[0]
        download_name = f"{original_name}_unpivot.xlsx"
        encoded_name = quote(download_name)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다운로드 실패: {str(e)}")


# ============================================================
# BOM 분해 유틸리티
# ============================================================

def _read_bom_excel(file_bytes: bytes) -> list:
    """BOM 분해용 엑셀 읽기 (컬럼: 품목코드, 상품명, 수량)

    Returns:
        list: [{"row": int, "erp_code": str, "ref_name": str, "quantity": float}, ...]
    """
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl', header=0)
    except Exception:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), engine='xlrd', header=0)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"엑셀 파일을 읽을 수 없습니다: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="엑셀 파일에 데이터가 없습니다")

    if len(df.columns) < 3:
        raise HTTPException(status_code=400, detail="엑셀에 최소 3개 컬럼(품목코드, 상품명, 수량)이 필요합니다")

    items = []
    for idx, row in df.iterrows():
        erp_code = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
        ref_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''
        raw_qty = row.iloc[2]

        if not erp_code:
            continue

        quantity = pd.to_numeric(raw_qty, errors='coerce')
        items.append({
            "row": idx + 2,  # 엑셀 행 번호 (헤더=1행, 데이터=2행부터)
            "erp_code": erp_code,
            "ref_name": ref_name,
            "quantity": quantity
        })

    if not items:
        raise HTTPException(status_code=400, detail="유효한 데이터가 없습니다")

    return items


def _resolve_erp_codes(erp_codes: list) -> dict:
    """ERPCode 목록을 ProductBox+Product 정보로 일괄 조회"""
    if not erp_codes:
        return {}

    with get_db_cursor(commit=False) as cursor:
        placeholders = ','.join(['?' for _ in erp_codes])
        cursor.execute(f"""
            SELECT
                pb.ERPCode,
                pb.BoxID,
                p.ProductID,
                p.Name,
                p.ProductType,
                p.Barcode2
            FROM [dbo].[ProductBox] pb
            JOIN [dbo].[Product] p ON pb.ProductID = p.ProductID
            WHERE pb.ERPCode IN ({placeholders})
        """, *erp_codes)

        result = {}
        for row in cursor.fetchall():
            result[row[0]] = {
                "BoxID": row[1],
                "ProductID": row[2],
                "Name": row[3],
                "ProductType": row[4],
                "Barcode2": row[5]
            }
        return result


def _get_bom_children_batch(parent_erp_codes: list) -> dict:
    """SET/BUNDLE ERPCode 목록의 BOM 자식 일괄 조회"""
    if not parent_erp_codes:
        return {}

    with get_db_cursor(commit=False) as cursor:
        placeholders = ','.join(['?' for _ in parent_erp_codes])
        cursor.execute(f"""
            SELECT
                pb_parent.ERPCode AS ParentERPCode,
                pb_child.ERPCode AS ChildERPCode,
                p_child.Name AS ChildName,
                p_child.Barcode2 AS ChildBarcode2,
                bom.QuantityRequired
            FROM [dbo].[ProductBOM] bom
            JOIN [dbo].[ProductBox] pb_parent ON bom.ParentProductBoxID = pb_parent.BoxID
            JOIN [dbo].[ProductBox] pb_child ON bom.ChildProductBoxID = pb_child.BoxID
            JOIN [dbo].[Product] p_child ON pb_child.ProductID = p_child.ProductID
            WHERE pb_parent.ERPCode IN ({placeholders})
            ORDER BY pb_parent.ERPCode, pb_child.ERPCode
        """, *parent_erp_codes)

        result = {}
        for row in cursor.fetchall():
            parent_erp = row[0]
            if parent_erp not in result:
                result[parent_erp] = []
            result[parent_erp].append({
                "ChildERPCode": row[1],
                "ChildName": row[2],
                "ChildBarcode2": row[3],
                "QuantityRequired": float(row[4])
            })
        return result


def _validate_bom_items(items: list, erp_map: dict, bom_children: dict) -> list:
    """BOM 분해 전 전체 검증. 에러가 있으면 에러 목록 반환, 없으면 빈 리스트."""
    errors = []

    for item in items:
        erp_code = item["erp_code"]
        row_num = item["row"]

        # 수량 검증
        if pd.isna(item["quantity"]) or item["quantity"] <= 0:
            errors.append({
                "row": row_num,
                "erp_code": erp_code,
                "ref_name": item["ref_name"],
                "reason": "수량이 유효하지 않음"
            })
            continue

        # ERPCode 존재 검증
        if erp_code not in erp_map:
            errors.append({
                "row": row_num,
                "erp_code": erp_code,
                "ref_name": item["ref_name"],
                "reason": "등록되지 않은 품목코드"
            })
            continue

        product_info = erp_map[erp_code]
        product_type = (product_info.get("ProductType") or "").upper()

        # EXCLUDE 검증
        if product_type == "EXCLUDE":
            errors.append({
                "row": row_num,
                "erp_code": erp_code,
                "ref_name": item["ref_name"],
                "reason": "제외 대상(EXCLUDE) 상품"
            })
            continue

        # SET/BUNDLE BOM 존재 검증
        if product_type in ("SET", "BUNDLE"):
            if erp_code not in bom_children or not bom_children[erp_code]:
                errors.append({
                    "row": row_num,
                    "erp_code": erp_code,
                    "ref_name": item["ref_name"],
                    "reason": f"BOM 구성품이 등록되지 않음 (ProductType={product_type})"
                })

    return errors


def _decompose_bom(items: list, erp_map: dict, bom_children: dict) -> tuple:
    """BOM 분해 실행 (검증 통과 후 호출) - 부모-자식 매핑 행 형태"""
    result_rows = []
    sets_count = 0
    singles_count = 0

    for item in items:
        erp_code = item["erp_code"]
        quantity = item["quantity"]
        product_info = erp_map[erp_code]
        product_type = (product_info.get("ProductType") or "").upper()

        if product_type in ("SET", "BUNDLE"):
            sets_count += 1
            for child in bom_children[erp_code]:
                result_rows.append({
                    "parent_erp": erp_code,
                    "parent_barcode2": product_info.get("Barcode2") or "",
                    "parent_name": product_info["Name"],
                    "parent_qty": quantity,
                    "child_erp": child["ChildERPCode"],
                    "child_barcode2": child.get("ChildBarcode2") or "",
                    "child_name": child["ChildName"],
                    "child_qty": child["QuantityRequired"] * quantity
                })
        else:
            # SINGLE → 품목 = 구성품 동일
            singles_count += 1
            result_rows.append({
                "parent_erp": erp_code,
                "parent_barcode2": product_info.get("Barcode2") or "",
                "parent_name": product_info["Name"],
                "parent_qty": quantity,
                "child_erp": erp_code,
                "child_barcode2": product_info.get("Barcode2") or "",
                "child_name": product_info["Name"],
                "child_qty": quantity
            })

    summary = {
        "input_rows": len(items),
        "output_rows": len(result_rows),
        "sets_decomposed": sets_count,
        "singles_passed": singles_count
    }

    return result_rows, summary


def _process_bom_decompose(file_bytes: bytes):
    """BOM 분해 공통 처리 (preview/download 공용)"""
    items = _read_bom_excel(file_bytes)

    # 1. ERPCode 일괄 조회
    erp_codes = list(set(item["erp_code"] for item in items))
    erp_map = _resolve_erp_codes(erp_codes)

    # 2. SET/BUNDLE만 BOM 자식 조회
    set_bundle_codes = [
        code for code in erp_codes
        if code in erp_map and (erp_map[code].get("ProductType") or "").upper() in ("SET", "BUNDLE")
    ]
    bom_children = _get_bom_children_batch(set_bundle_codes)

    # 3. 검증
    errors = _validate_bom_items(items, erp_map, bom_children)
    if errors:
        return {"success": False, "errors": errors}

    # 4. 분해 실행
    result_list, summary = _decompose_bom(items, erp_map, bom_children)

    return {
        "success": True,
        "input_preview": [
            {"품목코드": item["erp_code"], "상품명(참고)": item["ref_name"], "수량": item["quantity"]}
            for item in items[:5]
        ],
        "input_total": len(items),
        "result": result_list,
        "summary": summary
    }


@router.post("/bom-decompose/preview")
async def bom_decompose_preview(
    file: UploadFile = File(...),
    _=Depends(require_permission("Utility", "READ"))
):
    """BOM 분해 미리보기 - 검증 + 분해 결과"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        file_bytes = await file.read()
        return _process_bom_decompose(file_bytes)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BOM 분해 실패: {str(e)}")


@router.post("/bom-decompose/download")
async def bom_decompose_download(
    file: UploadFile = File(...),
    _=Depends(require_permission("Utility", "READ"))
):
    """BOM 분해 결과 엑셀 다운로드"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        file_bytes = await file.read()
        data = _process_bom_decompose(file_bytes)

        if not data["success"]:
            raise HTTPException(status_code=400, detail="검증 실패: 엑셀 데이터를 수정 후 다시 업로드하세요")

        # 엑셀 생성
        result_df = pd.DataFrame([
            {
                "품목코드(품목)": r["parent_erp"],
                "바코드2(품목)": r["parent_barcode2"],
                "상품명(품목)": r["parent_name"],
                "수량(품목)": r["parent_qty"],
                "품목코드(구성품)": r["child_erp"],
                "바코드2(구성품)": r["child_barcode2"],
                "상품명(구성품)": r["child_name"],
                "수량(구성품)": r["child_qty"]
            }
            for r in data["result"]
        ])

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False, sheet_name='분해결과')

            worksheet = writer.sheets['분해결과']
            for i, col in enumerate(result_df.columns):
                max_len = max(
                    result_df[col].astype(str).map(len).max() if len(result_df) > 0 else 0,
                    len(str(col))
                )
                worksheet.column_dimensions[chr(65 + i)].width = min(max_len + 4, 40)

        output.seek(0)

        original_name = file.filename.rsplit('.', 1)[0]
        download_name = f"{original_name}_BOM분해.xlsx"
        encoded_name = quote(download_name)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다운로드 실패: {str(e)}")