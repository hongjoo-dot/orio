"""
Utility Router
- 피벗 해제 등 데이터 변환 유틸리티 API
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from core.dependencies import require_permission
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