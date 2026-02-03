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


def _read_excel(file_bytes: bytes) -> pd.DataFrame:
    """엑셀 파일 읽기"""
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
    except Exception:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), engine='xlrd')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"엑셀 파일을 읽을 수 없습니다: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="엑셀 파일에 데이터가 없습니다")

    return df


def _unpivot(df: pd.DataFrame, fixed_count: int) -> pd.DataFrame:
    """피벗 해제 변환"""
    total_cols = len(df.columns)

    if fixed_count < 1:
        raise HTTPException(status_code=400, detail="고정 칼럼 수는 1 이상이어야 합니다")
    if fixed_count >= total_cols:
        raise HTTPException(status_code=400, detail="고정 칼럼 수가 전체 칼럼 수보다 작아야 합니다")

    fixed_cols = df.columns[:fixed_count].tolist()
    pivot_cols = df.columns[fixed_count:].tolist()

    result = df.melt(
        id_vars=fixed_cols,
        value_vars=pivot_cols,
        var_name='구분',
        value_name='값'
    )

    # 고정 칼럼 기준 정렬
    result = result.sort_values(by=fixed_cols).reset_index(drop=True)

    return result


@router.post("/unpivot/preview")
async def unpivot_preview(
    file: UploadFile = File(...),
    fixed_count: int = Form(...),
    _=Depends(require_permission("Utility", "READ"))
):
    """피벗 해제 미리보기 - 헤더 + 변환된 처음 10행"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        file_bytes = await file.read()
        df = _read_excel(file_bytes)

        # 원본 정보
        headers = df.columns.tolist()
        original_preview = df.head(5).fillna('').to_dict(orient='records')

        # 변환
        result = _unpivot(df, fixed_count)
        converted_headers = result.columns.tolist()
        converted_preview = result.head(10).fillna('').to_dict(orient='records')

        return {
            "original": {
                "headers": headers,
                "preview": original_preview,
                "total_rows": len(df),
                "total_cols": len(headers)
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
    _=Depends(require_permission("Utility", "READ"))
):
    """피벗 해제 후 엑셀 다운로드"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        file_bytes = await file.read()
        df = _read_excel(file_bytes)
        result = _unpivot(df, fixed_count)

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
