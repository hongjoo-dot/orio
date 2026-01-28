"""
Target (목표 관리) Router
- 기본 목표 (TargetBaseProduct) API
- 행사 목표 (TargetPromotionProduct) API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import io
from datetime import datetime
from repositories.target_base_repository import TargetBaseRepository
from repositories.target_promotion_repository import TargetPromotionRepository
from repositories import BrandRepository, ChannelRepository, ProductRepository, ActivityLogRepository
from core import get_db_cursor
from core.dependencies import get_client_ip, CurrentUser
from core import log_activity, log_delete, log_bulk_delete, require_permission


def _format_time_value(value, default: str = '00:00:00') -> str:
    """시간 값을 HH:MM:SS 형식으로 변환"""
    if pd.isna(value):
        return default
    if hasattr(value, 'strftime'):
        return value.strftime('%H:%M:%S')
    time_str = str(value).strip()
    if len(time_str) == 5:  # HH:MM
        return time_str + ':00'
    elif len(time_str) >= 8:  # HH:MM:SS
        return time_str[:8]
    return default


# ========== 기본 목표 Router ==========
router = APIRouter(prefix="/api/targets/base", tags=["TargetBase"])

# Repository 인스턴스
target_base_repo = TargetBaseRepository()
brand_repo = BrandRepository()
channel_repo = ChannelRepository()
product_repo = ProductRepository()
activity_log_repo = ActivityLogRepository()


# Pydantic Models - 기본 목표
class TargetBaseCreate(BaseModel):
    Date: str
    BrandID: int
    BrandName: Optional[str] = None
    ChannelID: int
    ChannelName: Optional[str] = None
    UniqueCode: str
    ProductName: Optional[str] = None
    TargetAmount: Optional[float] = None
    TargetQuantity: Optional[int] = None
    Notes: Optional[str] = None


class TargetBaseUpdate(BaseModel):
    Date: Optional[str] = None
    BrandID: Optional[int] = None
    BrandName: Optional[str] = None
    ChannelID: Optional[int] = None
    ChannelName: Optional[str] = None
    UniqueCode: Optional[str] = None
    ProductName: Optional[str] = None
    TargetAmount: Optional[float] = None
    TargetQuantity: Optional[int] = None
    Notes: Optional[str] = None


class BulkDeleteRequest(BaseModel):
    ids: List[int]


class FilterDeleteRequest(BaseModel):
    year_month: str
    brand_id: Optional[int] = None
    channel_id: Optional[int] = None


# ========== 기본 목표 CRUD ==========

@router.get("")
async def get_target_base_list(
    page: int = 1,
    limit: int = 20,
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    user: CurrentUser = Depends(require_permission("Target", "READ"))
):
    """기본 목표 목록 조회"""
    try:
        filters = {}
        if year_month:
            filters['year_month'] = year_month
        if brand_id:
            filters['brand_id'] = brand_id
        if channel_id:
            filters['channel_id'] = channel_id

        result = target_base_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by="t.[Date]",
            order_dir="DESC"
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"기본 목표 조회 실패: {str(e)}")


@router.get("/year-months")
async def get_target_base_year_months(user: CurrentUser = Depends(require_permission("Target", "READ"))):
    """기본 목표 년월 목록 조회"""
    try:
        year_months = target_base_repo.get_year_months()
        return {"year_months": year_months}
    except Exception as e:
        raise HTTPException(500, f"년월 목록 조회 실패: {str(e)}")


@router.get("/download")
async def download_target_base(
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    ids: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Target", "EXPORT"))
):
    """기본 목표 엑셀 양식 다운로드 (신규/수정 통합)"""
    try:
        data = []

        # 선택된 ID가 있으면 해당 ID들만 조회
        if ids:
            id_list = [int(id.strip()) for id in ids.split(',') if id.strip()]
            data = target_base_repo.get_by_ids(id_list)
        elif year_month or brand_id or channel_id:
            # 필터 조건이 있으면 해당 조건으로 조회
            filters = {}
            if year_month:
                filters['year_month'] = year_month
            if brand_id:
                filters['brand_id'] = brand_id
            if channel_id:
                filters['channel_id'] = channel_id

            result = target_base_repo.get_list(page=1, limit=100000, filters=filters)
            data = result['data']

        # 컬럼 정의 (ID 포함 - 통합 양식)
        export_columns = ['ID', '날짜', '브랜드명', '채널명', '상품코드', '목표금액', '목표수량', '비고']
        # 수정 불가 컬럼 인덱스 (검정 배경 + 흰 글자 적용) - ID 제외
        readonly_columns = [1, 2, 3, 4]  # 날짜, 브랜드명, 채널명, 상품코드
        id_column_idx = 0  # ID 컬럼은 빨간색으로 별도 처리

        if not data:
            # 데이터가 없으면 헤더만 있는 빈 양식 반환
            df = pd.DataFrame(columns=export_columns)
        else:
            # DataFrame 생성
            df = pd.DataFrame(data)

            # 컬럼 순서 및 이름 변경
            column_map = {
                'TargetBaseID': 'ID',
                'Date': '날짜',
                'BrandName': '브랜드명',
                'ChannelName': '채널명',
                'UniqueCode': '상품코드',
                'TargetAmount': '목표금액',
                'TargetQuantity': '목표수량',
                'Notes': '비고'
            }

            # 필요한 컬럼만 선택
            internal_columns = list(column_map.keys())
            df = df[[col for col in internal_columns if col in df.columns]]
            df = df.rename(columns=column_map)

        # 안내 시트 데이터
        guide_data = [
            ['[기본 목표 업로드 안내]', ''],
            ['', ''],
            ['■ 업로드 방식', ''],
            ['ID가 있는 행', 'ID 기준으로 해당 데이터를 수정합니다.'],
            ['ID가 없는 행', '날짜+채널+상품코드 기준으로 신규 등록 또는 수정합니다.'],
            ['', ''],
            ['■ 컬럼 설명', ''],
            ['ID', '수정할 데이터의 ID (비워두면 신규 등록)'],
            ['날짜', '목표 날짜 (YYYY-MM-DD 형식)'],
            ['브랜드명', 'Brand 테이블에 등록된 브랜드명'],
            ['채널명', 'Channel 테이블에 등록된 채널명'],
            ['상품코드', 'Product 테이블에 등록된 상품코드 (UniqueCode)'],
            ['목표금액', '숫자 (예: 1000000)'],
            ['목표수량', '숫자 (예: 100)'],
            ['비고', '메모'],
            ['', ''],
            ['■ 수정 가능/불가 컬럼', ''],
            ['수정 가능', '목표금액, 목표수량, 비고'],
            ['수정 불가 (검정)', '날짜, 브랜드명, 채널명, 상품코드'],
            ['ID (빨간색)', '수정할 데이터 식별용 (비워두면 신규 등록)'],
            ['', ''],
            ['■ 주의사항', ''],
            ['1. ID 컬럼을 비워두면 신규 등록으로 처리됩니다.', ''],
            ['2. 동일한 날짜+채널+상품코드 조합이 있으면 기존 데이터가 수정됩니다.', ''],
            ['3. 브랜드명, 채널명, 상품코드는 반드시 DB에 등록된 값이어야 합니다.', ''],
            ['4. 검정색/빨간색 배경 컬럼은 수정해도 반영되지 않습니다.', ''],
        ]
        guide_df = pd.DataFrame(guide_data, columns=['항목', '설명'])

        # 드롭다운용 목록 조회
        channels = channel_repo.get_channel_list()
        brands = brand_repo.get_all_brands()
        channel_names = [ch['Name'] for ch in channels]
        brand_names = [br['Name'] for br in brands]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='기본목표')
            guide_df.to_excel(writer, index=False, sheet_name='안내')

            workbook = writer.book
            worksheet = writer.sheets['기본목표']

            # 목록 시트 생성 (드롭다운 소스용)
            list_sheet = workbook.add_worksheet('목록')
            list_sheet.hide()  # 숨김 처리

            # 채널 목록 작성 (A열)
            for i, name in enumerate(channel_names):
                list_sheet.write(i, 0, name)

            # 브랜드 목록 작성 (B열)
            for i, name in enumerate(brand_names):
                list_sheet.write(i, 1, name)

            # 드롭다운 적용 범위 (2행~1000행)
            max_row = max(len(df) + 100, 1000)  # 데이터 + 여유분

            # 채널명 드롭다운 (D열, 인덱스 3)
            if channel_names:
                worksheet.data_validation(1, 3, max_row, 3, {
                    'validate': 'list',
                    'source': f'=목록!$A$1:$A${len(channel_names)}',
                    'input_message': '채널을 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 브랜드명 드롭다운 (C열, 인덱스 2)
            if brand_names:
                worksheet.data_validation(1, 2, max_row, 2, {
                    'validate': 'list',
                    'source': f'=목록!$B$1:$B${len(brand_names)}',
                    'input_message': '브랜드를 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # ID 컬럼 헤더 서식 (빨간색 배경 + 흰 글자)
            id_header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#dc2626',
                'border': 1
            })

            # 수정 불가 컬럼 헤더 서식 (검정 배경 + 흰 글자)
            readonly_header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#000000',
                'border': 1
            })

            # 수정 가능 컬럼 헤더 서식 (기본)
            editable_header_format = workbook.add_format({
                'bold': True,
                'border': 1
            })

            # 헤더 서식 적용
            for col_idx, col_name in enumerate(export_columns):
                if col_idx == id_column_idx:
                    worksheet.write(0, col_idx, col_name, id_header_format)
                elif col_idx in readonly_columns:
                    worksheet.write(0, col_idx, col_name, readonly_header_format)
                else:
                    worksheet.write(0, col_idx, col_name, editable_header_format)

            # ID 컬럼 데이터 서식 (빨간색 배경 + 흰 글자)
            id_data_format = workbook.add_format({
                'font_color': 'white',
                'bg_color': '#ef4444',
                'border': 1
            })

            # 데이터 행 서식 (수정 불가 컬럼)
            readonly_data_format = workbook.add_format({
                'font_color': 'white',
                'bg_color': '#333333',
                'border': 1
            })

            # 데이터 행에 서식 적용
            if len(df) > 0:
                for row_idx in range(len(df)):
                    # ID 컬럼 빨간색 적용
                    col_name = export_columns[id_column_idx]
                    if col_name in df.columns:
                        value = df.iloc[row_idx][col_name]
                        worksheet.write(row_idx + 1, id_column_idx, value, id_data_format)

                    # 수정 불가 컬럼 검정색 적용
                    for col_idx in readonly_columns:
                        if col_idx < len(export_columns):
                            col_name = export_columns[col_idx]
                            if col_name in df.columns:
                                value = df.iloc[row_idx][col_name]
                                worksheet.write(row_idx + 1, col_idx, value, readonly_data_format)

            # 컬럼 너비 설정
            for i in range(len(export_columns)):
                worksheet.set_column(i, i, 15)

            guide_sheet = writer.sheets['안내']
            guide_sheet.set_column(0, 0, 55)
            guide_sheet.set_column(1, 1, 40)

        output.seek(0)

        filename = f"target_base_{year_month or 'template'}.xlsx"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }

        return StreamingResponse(
            output,
            headers=headers,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"다운로드 실패: {str(e)}")


@router.get("/{target_id}")
async def get_target_base_item(target_id: int, user: CurrentUser = Depends(require_permission("Target", "READ"))):
    """기본 목표 단일 조회"""
    try:
        item = target_base_repo.get_by_id(target_id)
        if not item:
            raise HTTPException(404, "목표 데이터를 찾을 수 없습니다")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"목표 조회 실패: {str(e)}")


@router.post("")
@log_activity("CREATE", "TargetBaseProduct", id_key="TargetBaseID")
async def create_target_base(
    data: TargetBaseCreate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Target", "CREATE"))
):
    """기본 목표 생성"""
    try:
        target_id = target_base_repo.create(data.dict(exclude_none=True))

        return {"TargetBaseID": target_id, "UniqueCode": data.UniqueCode, "Date": data.Date}
    except Exception as e:
        raise HTTPException(500, f"목표 생성 실패: {str(e)}")


@router.put("/{target_id}")
@log_activity("UPDATE", "TargetBaseProduct", id_key="TargetBaseID")
async def update_target_base(
    target_id: int,
    data: TargetBaseUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Target", "UPDATE"))
):
    """기본 목표 수정"""
    try:
        if not target_base_repo.exists(target_id):
            raise HTTPException(404, "목표 데이터를 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = target_base_repo.update(target_id, update_data)
        if not success:
            raise HTTPException(500, "목표 수정 실패")

        return {"TargetBaseID": target_id, **update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"목표 수정 실패: {str(e)}")


@router.delete("/{target_id}")
@log_delete("TargetBaseProduct", id_param="target_id")
async def delete_target_base(
    target_id: int,
    request: Request,
    user: CurrentUser = Depends(require_permission("Target", "DELETE"))
):
    """기본 목표 삭제"""
    try:
        if not target_base_repo.exists(target_id):
            raise HTTPException(404, "목표 데이터를 찾을 수 없습니다")

        success = target_base_repo.delete(target_id)
        if not success:
            raise HTTPException(500, "목표 삭제 실패")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"목표 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
@log_bulk_delete("TargetBaseProduct")
async def bulk_delete_target_base(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Target", "DELETE"))
):
    """기본 목표 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = target_base_repo.bulk_delete(request_body.ids)

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


@router.post("/filter-delete")
@log_activity("BULK_DELETE", "TargetBaseProduct")
async def filter_delete_target_base(
    request_body: FilterDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Target", "DELETE"))
):
    """필터 조건으로 기본 목표 일괄 삭제"""
    try:
        deleted_count = target_base_repo.delete_by_filter(
            year_month=request_body.year_month,
            brand_id=request_body.brand_id,
            channel_id=request_body.channel_id
        )

        return {
            "deleted_count": deleted_count,
            "filter": request_body.dict()
        }
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ========== 기본 목표 엑셀 ==========

@router.post("/upload")
async def upload_target_base(
    file: UploadFile = File(...),
    request: Request = None,
    user: CurrentUser = Depends(require_permission("Target", "UPLOAD"))
):
    """기본 목표 엑셀 업로드"""
    try:
        upload_start_time = datetime.now()

        # 파일 확장자 검증
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, "엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        print(f"\n[기본 목표 업로드 시작] {file.filename}")

        # 파일 읽기
        content = await file.read()
        excel_file = io.BytesIO(content)
        df = pd.read_excel(excel_file)
        print(f"   총 {len(df):,}행 로드됨")

        # 컬럼 매핑 (엑셀 컬럼명 → 내부 컬럼명)
        column_map = {
            'ID': 'TargetBaseID',
            '날짜': 'Date',
            '브랜드명': 'BrandName',
            '채널명': 'ChannelName',
            '상품코드': 'UniqueCode',
            '목표금액': 'TargetAmount',
            '목표수량': 'TargetQuantity',
            '비고': 'Notes'
        }
        df = df.rename(columns=column_map)

        # 필수 컬럼 확인
        required_cols = ['Date', 'BrandName', 'ChannelName', 'UniqueCode']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(400, f"필수 컬럼이 없습니다: {missing_cols}")

        # 날짜 변환
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        invalid_dates = df['Date'].isna().sum()
        if invalid_dates > 0:
            raise HTTPException(400, f"날짜 형식이 잘못된 행이 {invalid_dates}개 있습니다")

        # 데이터 타입 변환
        df['TargetAmount'] = pd.to_numeric(df['TargetAmount'], errors='coerce').fillna(0)
        df['TargetQuantity'] = pd.to_numeric(df['TargetQuantity'], errors='coerce').fillna(0).astype(int)

        # 문자열 컬럼 공백 제거 (strip)
        df['BrandName'] = df['BrandName'].astype(str).str.strip()
        df['ChannelName'] = df['ChannelName'].astype(str).str.strip()
        df['UniqueCode'] = df['UniqueCode'].astype(str).str.strip()

        # 에러 수집용 딕셔너리
        errors = {
            'brand': {},      # {name: [행번호들]}
            'channel': {},    # {name: [행번호들]}
            'product': {}     # {code: [행번호들]}
        }

        # 브랜드명 → BrandID 매핑 테이블 생성
        brand_names = df['BrandName'].dropna().unique().tolist()
        brand_names = [n for n in brand_names if n and n != 'nan']
        brand_map = {}
        for name in brand_names:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT BrandID, Name FROM Brand WHERE Name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    brand_map[name] = {'BrandID': row[0], 'BrandName': row[1]}
                else:
                    # 해당 브랜드명이 있는 행 번호 수집 (엑셀 기준 2부터 시작)
                    row_nums = df[df['BrandName'] == name].index.tolist()
                    errors['brand'][name] = [r + 2 for r in row_nums]

        # 채널명 → ChannelID 매핑 테이블 생성
        channel_names = df['ChannelName'].dropna().unique().tolist()
        channel_names = [n for n in channel_names if n and n != 'nan']
        channel_map = {}
        for name in channel_names:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT ChannelID, Name FROM Channel WHERE Name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    channel_map[name] = {'ChannelID': row[0], 'ChannelName': row[1]}
                else:
                    row_nums = df[df['ChannelName'] == name].index.tolist()
                    errors['channel'][name] = [r + 2 for r in row_nums]

        # 상품코드 → ProductName 매핑 테이블 생성
        unique_codes = df['UniqueCode'].dropna().unique().tolist()
        unique_codes = [c for c in unique_codes if c and c != 'nan']
        product_map = {}
        for code in unique_codes:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT UniqueCode, Name FROM Product WHERE UniqueCode = ?", (code,))
                row = cursor.fetchone()
                if row:
                    product_map[code] = {'UniqueCode': row[0], 'ProductName': row[1]}
                else:
                    row_nums = df[df['UniqueCode'] == code].index.tolist()
                    errors['product'][code] = [r + 2 for r in row_nums]

        # 에러가 있으면 모두 모아서 반환
        if errors['brand'] or errors['channel'] or errors['product']:
            error_messages = []
            for name, rows in errors['brand'].items():
                error_messages.append(f"존재하지 않는 브랜드명: {name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for name, rows in errors['channel'].items():
                error_messages.append(f"존재하지 않는 채널명: {name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for code, rows in errors['product'].items():
                error_messages.append(f"존재하지 않는 상품코드: {code} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            raise HTTPException(400, "\n".join(error_messages))

        # 레코드 준비
        records = []
        for _, row in df.iterrows():
            brand_name = row['BrandName'] if pd.notna(row['BrandName']) and row['BrandName'] != 'nan' else None
            channel_name = row['ChannelName'] if pd.notna(row['ChannelName']) and row['ChannelName'] != 'nan' else None
            unique_code = row['UniqueCode'] if pd.notna(row['UniqueCode']) and row['UniqueCode'] != 'nan' else None

            brand_info = brand_map.get(brand_name, {})
            channel_info = channel_map.get(channel_name, {})
            product_info = product_map.get(unique_code, {})

            # ID가 있으면 포함 (수정 양식인 경우)
            target_id = None
            if 'TargetBaseID' in row and pd.notna(row['TargetBaseID']):
                target_id = int(row['TargetBaseID'])

            records.append({
                'TargetBaseID': target_id,
                'Date': row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else None,
                'BrandID': brand_info.get('BrandID'),
                'BrandName': brand_info.get('BrandName'),
                'ChannelID': channel_info.get('ChannelID'),
                'ChannelName': channel_info.get('ChannelName'),
                'UniqueCode': unique_code,
                'ProductName': product_info.get('ProductName'),
                'TargetAmount': float(row['TargetAmount']) if pd.notna(row.get('TargetAmount')) else 0,
                'TargetQuantity': int(row['TargetQuantity']) if pd.notna(row.get('TargetQuantity')) else 0,
                'Notes': str(row['Notes']) if pd.notna(row.get('Notes')) else None,
            })

        # UPSERT 실행
        result = target_base_repo.bulk_upsert(records)

        upload_end_time = datetime.now()
        duration = (upload_end_time - upload_start_time).total_seconds()

        # 중복 데이터 체크 - 에러 반환
        duplicates = result.get('duplicates', [])
        if duplicates:
            error_messages = []
            for dup in duplicates[:10]:  # 최대 10개까지 표시
                error_messages.append(
                    f"행 {dup['row']}: 중복 데이터 (날짜: {dup['date']}, 상품코드: {dup['unique_code']}, 채널: {dup['channel_name']})"
                )
            if len(duplicates) > 10:
                error_messages.append(f"... 외 {len(duplicates) - 10}건 더 있음")
            raise HTTPException(400, "중복 데이터가 있습니다. ID 없이 신규 입력 시 기존 데이터와 중복될 수 없습니다.\n" + "\n".join(error_messages))

        # 활동 로그
        if user and request:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="TargetBaseProduct",
                details={
                    "action": "EXCEL_UPLOAD",
                    "filename": file.filename,
                    "total_rows": len(df),
                    "inserted": result['inserted'],
                    "updated": result['updated'],
                    "duration_seconds": duration
                },
                ip_address=get_client_ip(request)
            )

        print(f"   업로드 완료: {result['inserted']}건 삽입, {result['updated']}건 수정")

        return {
            "message": "업로드 완료",
            "total_rows": len(df),
            "inserted": result['inserted'],
            "updated": result['updated'],
            "duration_seconds": duration
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"업로드 실패: {str(e)}")


# ========== 행사 목표 Router ==========
promotion_router = APIRouter(prefix="/api/targets/promotion", tags=["TargetPromotion"])

# Repository 인스턴스
target_promotion_repo = TargetPromotionRepository()


# Pydantic Models - 행사 목표
class TargetPromotionCreate(BaseModel):
    PromotionID: str
    PromotionName: Optional[str] = None
    StartDate: str
    StartTime: Optional[str] = "00:00:00"
    EndDate: str
    EndTime: Optional[str] = "23:59:59"
    BrandID: int
    BrandName: Optional[str] = None
    ChannelID: int
    ChannelName: Optional[str] = None
    UniqueCode: str
    ProductName: Optional[str] = None
    TargetAmount: Optional[float] = None
    TargetQuantity: Optional[int] = None
    Notes: Optional[str] = None


class TargetPromotionUpdate(BaseModel):
    PromotionID: Optional[str] = None
    PromotionName: Optional[str] = None
    StartDate: Optional[str] = None
    StartTime: Optional[str] = None
    EndDate: Optional[str] = None
    EndTime: Optional[str] = None
    BrandID: Optional[int] = None
    BrandName: Optional[str] = None
    ChannelID: Optional[int] = None
    ChannelName: Optional[str] = None
    UniqueCode: Optional[str] = None
    ProductName: Optional[str] = None
    TargetAmount: Optional[float] = None
    TargetQuantity: Optional[int] = None
    Notes: Optional[str] = None


class PromotionFilterDeleteRequest(BaseModel):
    year_month: str
    brand_id: Optional[int] = None
    channel_id: Optional[int] = None
    promotion_type: Optional[str] = None


# ========== 행사 목표 CRUD ==========

@promotion_router.get("")
async def get_target_promotion_list(
    page: int = 1,
    limit: int = 20,
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    promotion_type: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Target", "READ"))
):
    """행사 목표 목록 조회"""
    try:
        filters = {}
        if year_month:
            filters['year_month'] = year_month
        if brand_id:
            filters['brand_id'] = brand_id
        if channel_id:
            filters['channel_id'] = channel_id
        if promotion_type:
            filters['promotion_type'] = promotion_type

        result = target_promotion_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by="t.StartDate",
            order_dir="DESC"
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"행사 목표 조회 실패: {str(e)}")


@promotion_router.get("/year-months")
async def get_target_promotion_year_months(user: CurrentUser = Depends(require_permission("Target", "READ"))):
    """행사 목표 년월 목록 조회"""
    try:
        year_months = target_promotion_repo.get_year_months()
        return {"year_months": year_months}
    except Exception as e:
        raise HTTPException(500, f"년월 목록 조회 실패: {str(e)}")


@promotion_router.get("/promotion-types")
async def get_promotion_types(user: CurrentUser = Depends(require_permission("Target", "READ"))):
    """행사유형 목록 조회 (드롭다운용)"""
    try:
        promotion_types = target_promotion_repo.get_promotion_types()
        return {"promotion_types": promotion_types}
    except Exception as e:
        raise HTTPException(500, f"행사유형 목록 조회 실패: {str(e)}")


@promotion_router.get("/download")
async def download_target_promotion(
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    promotion_type: Optional[str] = None,
    ids: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Target", "EXPORT"))
):
    """행사 목표 엑셀 양식 다운로드 (신규/수정 통합)"""
    try:
        data = []

        # 선택된 ID가 있으면 해당 ID들만 조회
        if ids:
            id_list = [int(id.strip()) for id in ids.split(',') if id.strip()]
            data = target_promotion_repo.get_by_ids(id_list)
        elif year_month or brand_id or channel_id or promotion_type:
            # 필터 조건이 있으면 해당 조건으로 조회
            filters = {}
            if year_month:
                filters['year_month'] = year_month
            if brand_id:
                filters['brand_id'] = brand_id
            if channel_id:
                filters['channel_id'] = channel_id
            if promotion_type:
                filters['promotion_type'] = promotion_type

            result = target_promotion_repo.get_list(page=1, limit=100000, filters=filters)
            data = result['data']

        # 컬럼 정의
        export_columns = [
            'ID', '행사명', '행사유형', '시작일', '시작시간', '종료일', '종료시간',
            '브랜드명', '채널명', '상품코드', '목표금액', '목표수량', '비고'
        ]
        # 수정 불가 컬럼 인덱스 (검정 배경 + 흰 글자 적용) - ID 제외
        readonly_columns = [2, 3, 5, 7, 8, 9]  # 행사유형, 시작일, 종료일, 브랜드명, 채널명, 상품코드
        id_column_idx = 0  # ID 컬럼은 빨간색으로 별도 처리

        if not data:
            # 데이터가 없으면 헤더만 있는 빈 양식 반환
            df = pd.DataFrame(columns=export_columns)
        else:
            df = pd.DataFrame(data)

            column_map = {
                'TargetPromotionID': 'ID',
                'PromotionName': '행사명',
                'PromotionType': '행사유형',
                'StartDate': '시작일',
                'StartTime': '시작시간',
                'EndDate': '종료일',
                'EndTime': '종료시간',
                'BrandName': '브랜드명',
                'ChannelName': '채널명',
                'UniqueCode': '상품코드',
                'TargetAmount': '목표금액',
                'TargetQuantity': '목표수량',
                'Notes': '비고'
            }

            internal_columns = list(column_map.keys())
            df = df[[col for col in internal_columns if col in df.columns]]
            df = df.rename(columns=column_map)

        # 안내 시트 데이터
        guide_data = [
            ['[행사 목표 업로드 안내]', ''],
            ['', ''],
            ['■ 업로드 방식', ''],
            ['ID가 있는 행', 'ID 기준으로 해당 데이터를 수정합니다.'],
            ['ID가 없는 행', '브랜드+행사유형+시작일 기준으로 행사ID가 자동 생성됩니다.'],
            ['', ''],
            ['■ 행사ID 자동 생성 규칙', ''],
            ['형식', 'BrandCode(2자리) + TypeCode(2자리) + YYMM(4자리) + 순번(2자리)'],
            ['예시', 'OREN250101 (오리온 + 에누리 + 25년01월 + 01번)'],
            ['참고', 'TypeCode는 PromotionType 테이블의 TypeCode 값 (2자리 알파벳)'],
            ['', ''],
            ['■ 컬럼 설명', ''],
            ['ID', '수정할 데이터의 ID (비워두면 신규 등록)'],
            ['행사명', '행사 이름'],
            ['행사유형', '아래 행사유형 목록 참조 (행사ID 생성에 필요)'],
            ['시작일', '행사 시작 날짜 (YYYY-MM-DD 형식)'],
            ['시작시간', 'HH:MM:SS 형식 (예: 09:00:00, 기본값: 00:00:00)'],
            ['종료일', '행사 종료 날짜 (YYYY-MM-DD 형식)'],
            ['종료시간', 'HH:MM:SS 형식 (예: 23:59:59, 기본값: 00:00:00)'],
            ['브랜드명', 'Brand 테이블에 등록된 브랜드명 (행사ID 생성에 필요)'],
            ['채널명', 'Channel 테이블에 등록된 채널명'],
            ['상품코드', 'Product 테이블에 등록된 상품코드 (UniqueCode)'],
            ['목표금액', '숫자 (예: 1000000)'],
            ['목표수량', '숫자 (예: 100)'],
            ['비고', '메모'],
            ['', ''],
            ['■ 수정 가능/불가 컬럼', ''],
            ['수정 가능', '행사명, 시작시간, 종료시간, 목표금액, 목표수량, 비고'],
            ['수정 불가 (검정)', '행사유형, 시작일, 종료일, 브랜드명, 채널명, 상품코드'],
            ['ID (빨간색)', '수정할 데이터 식별용 (비워두면 신규 등록)'],
            ['', ''],
            ['■ 행사유형 목록', ''],
            ['에누리', ''],
            ['쿠폰', ''],
            ['판매가+쿠폰', ''],
            ['판매가할인', ''],
            ['정산후보정', ''],
            ['기획상품', ''],
            ['원매가할인', ''],
            ['', ''],
            ['■ 주의사항', ''],
            ['1. ID 컬럼을 비워두면 신규 등록으로 처리됩니다.', ''],
            ['2. 행사ID는 자동 생성되며, 같은 조건(브랜드+행사유형+YYMM)에서 순번이 증가합니다.', ''],
            ['3. 브랜드명, 채널명, 상품코드, 행사유형은 반드시 DB에 등록된 값이어야 합니다.', ''],
            ['4. 검정색/빨간색 배경 컬럼은 수정해도 반영되지 않습니다.', ''],
        ]
        guide_df = pd.DataFrame(guide_data, columns=['항목', '설명'])

        # 드롭다운용 목록 조회
        channels = channel_repo.get_channel_list()
        brands = brand_repo.get_all_brands()
        channel_names = [ch['Name'] for ch in channels]
        brand_names = [br['Name'] for br in brands]
        promotion_types = ['에누리', '쿠폰', '판매가+쿠폰', '판매가할인', '정산후보정', '기획상품', '원매가할인']

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='행사목표')
            guide_df.to_excel(writer, index=False, sheet_name='안내')

            workbook = writer.book
            worksheet = writer.sheets['행사목표']

            # 목록 시트 생성 (드롭다운 소스용)
            list_sheet = workbook.add_worksheet('목록')
            list_sheet.hide()  # 숨김 처리

            # 채널 목록 작성 (A열)
            for i, name in enumerate(channel_names):
                list_sheet.write(i, 0, name)

            # 브랜드 목록 작성 (B열)
            for i, name in enumerate(brand_names):
                list_sheet.write(i, 1, name)

            # 행사유형 목록 작성 (C열)
            for i, name in enumerate(promotion_types):
                list_sheet.write(i, 2, name)

            # 드롭다운 적용 범위 (2행~1000행)
            max_row = max(len(df) + 100, 1000)  # 데이터 + 여유분

            # 채널명 드롭다운 (I열, 인덱스 8)
            if channel_names:
                worksheet.data_validation(1, 8, max_row, 8, {
                    'validate': 'list',
                    'source': f'=목록!$A$1:$A${len(channel_names)}',
                    'input_message': '채널을 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 브랜드명 드롭다운 (H열, 인덱스 7)
            if brand_names:
                worksheet.data_validation(1, 7, max_row, 7, {
                    'validate': 'list',
                    'source': f'=목록!$B$1:$B${len(brand_names)}',
                    'input_message': '브랜드를 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 행사유형 드롭다운 (C열, 인덱스 2)
            worksheet.data_validation(1, 2, max_row, 2, {
                'validate': 'list',
                'source': f'=목록!$C$1:$C${len(promotion_types)}',
                'input_message': '행사유형을 선택하세요',
                'error_message': '목록에서 선택해주세요'
            })

            # ID 컬럼 헤더 서식 (빨간색 배경 + 흰 글자)
            id_header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#dc2626',
                'border': 1
            })

            # 수정 불가 컬럼 헤더 서식 (검정 배경 + 흰 글자)
            readonly_header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#000000',
                'border': 1
            })

            # 수정 가능 컬럼 헤더 서식 (기본)
            editable_header_format = workbook.add_format({
                'bold': True,
                'border': 1
            })

            # 헤더 서식 적용
            for col_idx, col_name in enumerate(export_columns):
                if col_idx == id_column_idx:
                    worksheet.write(0, col_idx, col_name, id_header_format)
                elif col_idx in readonly_columns:
                    worksheet.write(0, col_idx, col_name, readonly_header_format)
                else:
                    worksheet.write(0, col_idx, col_name, editable_header_format)

            # ID 컬럼 데이터 서식 (빨간색 배경 + 흰 글자)
            id_data_format = workbook.add_format({
                'font_color': 'white',
                'bg_color': '#ef4444',
                'border': 1
            })

            # 데이터 행 서식 (수정 불가 컬럼)
            readonly_data_format = workbook.add_format({
                'font_color': 'white',
                'bg_color': '#333333',
                'border': 1
            })

            # 데이터 행에 서식 적용
            if len(df) > 0:
                for row_idx in range(len(df)):
                    # ID 컬럼 빨간색 적용
                    col_name = export_columns[id_column_idx]
                    if col_name in df.columns:
                        value = df.iloc[row_idx][col_name]
                        worksheet.write(row_idx + 1, id_column_idx, value, id_data_format)

                    # 수정 불가 컬럼 검정색 적용
                    for col_idx in readonly_columns:
                        if col_idx < len(export_columns):
                            col_name = export_columns[col_idx]
                            if col_name in df.columns:
                                value = df.iloc[row_idx][col_name]
                                worksheet.write(row_idx + 1, col_idx, value, readonly_data_format)

            # 컬럼 너비 설정
            for i in range(len(export_columns)):
                worksheet.set_column(i, i, 15)

            guide_sheet = writer.sheets['안내']
            guide_sheet.set_column(0, 0, 65)
            guide_sheet.set_column(1, 1, 40)

        output.seek(0)

        filename = f"target_promotion_{year_month or 'template'}.xlsx"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }

        return StreamingResponse(
            output,
            headers=headers,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"다운로드 실패: {str(e)}")


@promotion_router.get("/{target_id}")
async def get_target_promotion_item(target_id: int, user: CurrentUser = Depends(require_permission("Target", "READ"))):
    """행사 목표 단일 조회"""
    try:
        item = target_promotion_repo.get_by_id(target_id)
        if not item:
            raise HTTPException(404, "목표 데이터를 찾을 수 없습니다")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"목표 조회 실패: {str(e)}")


@promotion_router.post("")
@log_activity("CREATE", "TargetPromotionProduct", id_key="TargetPromotionID")
async def create_target_promotion(
    data: TargetPromotionCreate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Target", "CREATE"))
):
    """행사 목표 생성"""
    try:
        target_id = target_promotion_repo.create(data.dict(exclude_none=True))

        return {"TargetPromotionID": target_id, "PromotionID": data.PromotionID, "UniqueCode": data.UniqueCode}
    except Exception as e:
        raise HTTPException(500, f"목표 생성 실패: {str(e)}")


@promotion_router.put("/{target_id}")
@log_activity("UPDATE", "TargetPromotionProduct", id_key="TargetPromotionID")
async def update_target_promotion(
    target_id: int,
    data: TargetPromotionUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Target", "UPDATE"))
):
    """행사 목표 수정"""
    try:
        if not target_promotion_repo.exists(target_id):
            raise HTTPException(404, "목표 데이터를 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = target_promotion_repo.update(target_id, update_data)
        if not success:
            raise HTTPException(500, "목표 수정 실패")

        return {"TargetPromotionID": target_id, **update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"목표 수정 실패: {str(e)}")


@promotion_router.delete("/{target_id}")
@log_delete("TargetPromotionProduct", id_param="target_id")
async def delete_target_promotion(
    target_id: int,
    request: Request,
    user: CurrentUser = Depends(require_permission("Target", "DELETE"))
):
    """행사 목표 삭제"""
    try:
        if not target_promotion_repo.exists(target_id):
            raise HTTPException(404, "목표 데이터를 찾을 수 없습니다")

        success = target_promotion_repo.delete(target_id)
        if not success:
            raise HTTPException(500, "목표 삭제 실패")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"목표 삭제 실패: {str(e)}")


@promotion_router.post("/bulk-delete")
@log_bulk_delete("TargetPromotionProduct")
async def bulk_delete_target_promotion(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Target", "DELETE"))
):
    """행사 목표 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = target_promotion_repo.bulk_delete(request_body.ids)

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


@promotion_router.post("/filter-delete")
@log_activity("BULK_DELETE", "TargetPromotionProduct")
async def filter_delete_target_promotion(
    request_body: PromotionFilterDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Target", "DELETE"))
):
    """필터 조건으로 행사 목표 일괄 삭제"""
    try:
        deleted_count = target_promotion_repo.delete_by_filter(
            year_month=request_body.year_month,
            brand_id=request_body.brand_id,
            channel_id=request_body.channel_id,
            promotion_type=request_body.promotion_type
        )

        return {
            "deleted_count": deleted_count,
            "filter": request_body.dict()
        }
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ========== 행사 목표 엑셀 ==========

@promotion_router.post("/upload")
async def upload_target_promotion(
    file: UploadFile = File(...),
    request: Request = None,
    user: CurrentUser = Depends(require_permission("Target", "UPLOAD"))
):
    """행사 목표 엑셀 업로드"""
    try:
        upload_start_time = datetime.now()

        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, "엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        print(f"\n[행사 목표 업로드 시작] {file.filename}")

        content = await file.read()
        excel_file = io.BytesIO(content)
        df = pd.read_excel(excel_file)
        print(f"   총 {len(df):,}행 로드됨")

        # 컬럼 매핑 (엑셀 컬럼명 → 내부 컬럼명)
        column_map = {
            'ID': 'TargetPromotionID',
            '행사ID': 'PromotionID',
            '행사명': 'PromotionName',
            '행사유형': 'PromotionType',
            '시작일': 'StartDate',
            '시작시간': 'StartTime',
            '종료일': 'EndDate',
            '종료시간': 'EndTime',
            '브랜드명': 'BrandName',
            '채널명': 'ChannelName',
            '상품코드': 'UniqueCode',
            '목표금액': 'TargetAmount',
            '목표수량': 'TargetQuantity',
            '비고': 'Notes'
        }
        df = df.rename(columns=column_map)

        # 필수 컬럼 확인 (PromotionID 제거 - 자동 생성됨)
        required_cols = ['PromotionType', 'StartDate', 'EndDate', 'BrandName', 'ChannelName', 'UniqueCode']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(400, f"필수 컬럼이 없습니다: {missing_cols}")

        # 날짜 변환
        df['StartDate'] = pd.to_datetime(df['StartDate'], errors='coerce')
        df['EndDate'] = pd.to_datetime(df['EndDate'], errors='coerce')

        invalid_start_dates = df['StartDate'].isna().sum()
        invalid_end_dates = df['EndDate'].isna().sum()
        if invalid_start_dates > 0 or invalid_end_dates > 0:
            raise HTTPException(400, f"날짜 형식이 잘못된 행이 있습니다 (시작일: {invalid_start_dates}개, 종료일: {invalid_end_dates}개)")

        # 신규 행(ID 없음)에서 행사유형이 비어있는지 확인
        df['PromotionType'] = df['PromotionType'].astype(str).str.strip()
        empty_type_rows = []
        for idx, row in df.iterrows():
            # ID가 없는 신규 행에서만 행사유형 필수 체크
            has_id = 'TargetPromotionID' in row and pd.notna(row.get('TargetPromotionID'))
            has_promo_id = 'PromotionID' in row and pd.notna(row.get('PromotionID')) and str(row.get('PromotionID')).strip() not in ['', 'nan']
            promo_type = str(row.get('PromotionType', '')).strip()

            if not has_id and not has_promo_id and (not promo_type or promo_type == 'nan'):
                empty_type_rows.append(idx + 2)  # 엑셀 행 번호 (헤더 + 0-index)

        if empty_type_rows:
            raise HTTPException(400, f"신규 등록 행에 행사유형이 비어있습니다 (행 {', '.join(map(str, empty_type_rows[:10]))}{'...' if len(empty_type_rows) > 10 else ''})")

        # 시간 처리 (기본값 00:00)
        if 'StartTime' not in df.columns:
            df['StartTime'] = '00:00:00'
        if 'EndTime' not in df.columns:
            df['EndTime'] = '23:59:59'

        # 데이터 타입 변환
        df['TargetAmount'] = pd.to_numeric(df['TargetAmount'], errors='coerce').fillna(0)
        df['TargetQuantity'] = pd.to_numeric(df['TargetQuantity'], errors='coerce').fillna(0).astype(int)

        # 문자열 컬럼 공백 제거 (strip)
        df['BrandName'] = df['BrandName'].astype(str).str.strip()
        df['ChannelName'] = df['ChannelName'].astype(str).str.strip()
        df['UniqueCode'] = df['UniqueCode'].astype(str).str.strip()

        # 에러 수집용 딕셔너리
        errors = {
            'brand': {},          # {name: [행번호들]}
            'channel': {},        # {name: [행번호들]}
            'product': {},        # {code: [행번호들]}
            'promotion_type': {}  # {display_name: [행번호들]}
        }

        # 브랜드명 → BrandID, BrandCode 매핑 테이블 생성
        brand_names = df['BrandName'].dropna().unique().tolist()
        brand_names = [n for n in brand_names if n and n != 'nan']
        brand_map = {}
        missing_brand_codes = []
        for name in brand_names:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT BrandID, Name, BrandCode FROM Brand WHERE Name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    brand_code = row[2]
                    # BrandCode가 없으면 경고 추가
                    if not brand_code:
                        missing_brand_codes.append(name)
                    brand_map[name] = {'BrandID': row[0], 'BrandName': row[1], 'BrandCode': brand_code}
                else:
                    row_nums = df[df['BrandName'] == name].index.tolist()
                    errors['brand'][name] = [r + 2 for r in row_nums]

        # BrandCode가 없는 브랜드가 있으면 경고
        if missing_brand_codes:
            raise HTTPException(400, f"BrandCode가 설정되지 않은 브랜드가 있습니다: {', '.join(missing_brand_codes)}. 브랜드 설정에서 BrandCode를 입력해주세요.")

        # 채널명 → ChannelID 매핑 테이블 생성
        channel_names = df['ChannelName'].dropna().unique().tolist()
        channel_names = [n for n in channel_names if n and n != 'nan']
        channel_map = {}
        for name in channel_names:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT ChannelID, Name FROM Channel WHERE Name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    channel_map[name] = {'ChannelID': row[0], 'ChannelName': row[1]}
                else:
                    row_nums = df[df['ChannelName'] == name].index.tolist()
                    errors['channel'][name] = [r + 2 for r in row_nums]

        # 상품코드 → ProductName 매핑 테이블 생성
        unique_codes = df['UniqueCode'].dropna().unique().tolist()
        unique_codes = [c for c in unique_codes if c and c != 'nan']
        product_map = {}
        for code in unique_codes:
            with get_db_cursor() as cursor:
                cursor.execute("SELECT UniqueCode, Name FROM Product WHERE UniqueCode = ?", (code,))
                row = cursor.fetchone()
                if row:
                    product_map[code] = {'UniqueCode': row[0], 'ProductName': row[1]}
                else:
                    row_nums = df[df['UniqueCode'] == code].index.tolist()
                    errors['product'][code] = [r + 2 for r in row_nums]

        # 행사유형 검증 및 TypeCode 매핑 (PromotionType 테이블에서 조회)
        promotion_type_map = {}
        missing_type_codes = []  # TypeCode가 없는 행사유형
        if 'PromotionType' in df.columns:
            promotion_types = df['PromotionType'].dropna().unique().tolist()
            promotion_types = [t for t in promotion_types if t and str(t) != 'nan']
            for display_name in promotion_types:
                display_name_str = str(display_name).strip()
                # PromotionType 테이블에서 DisplayName으로 TypeCode 조회
                with get_db_cursor() as cursor:
                    cursor.execute("SELECT DisplayName, TypeCode FROM PromotionType WHERE DisplayName = ?", (display_name_str,))
                    row = cursor.fetchone()
                    if row:
                        type_code = row[1] if row[1] else ''
                        promotion_type_map[display_name_str] = {
                            'DisplayName': row[0],
                            'TypeCode': type_code
                        }
                        # TypeCode가 없으면 경고
                        if not type_code:
                            missing_type_codes.append(display_name_str)
                    else:
                        # DB에 없는 행사유형 - 에러 수집
                        row_nums = df[df['PromotionType'] == display_name].index.tolist()
                        errors['promotion_type'][display_name_str] = [r + 2 for r in row_nums]

        # TypeCode가 없는 행사유형이 있으면 에러
        if missing_type_codes:
            raise HTTPException(400, f"TypeCode가 설정되지 않은 행사유형이 있습니다: {', '.join(missing_type_codes)}. PromotionType 테이블에서 TypeCode를 설정해주세요.")

        # 에러가 있으면 모두 모아서 반환
        if errors['brand'] or errors['channel'] or errors['product'] or errors['promotion_type']:
            error_messages = []
            for name, rows in errors['brand'].items():
                error_messages.append(f"존재하지 않는 브랜드명: {name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for name, rows in errors['channel'].items():
                error_messages.append(f"존재하지 않는 채널명: {name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for code, rows in errors['product'].items():
                error_messages.append(f"존재하지 않는 상품코드: {code} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            for display_name, rows in errors['promotion_type'].items():
                error_messages.append(f"존재하지 않는 행사유형: {display_name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
            raise HTTPException(400, "\n".join(error_messages))

        # 신규 행 중복 체크 (복합키: BrandID + ChannelID + PromotionType + StartDate + UniqueCode)
        duplicate_rows = []
        for idx, row in df.iterrows():
            # ID가 있는 행은 수정이므로 중복 체크 불필요
            if 'TargetPromotionID' in df.columns and pd.notna(row.get('TargetPromotionID')):
                continue

            brand_name = str(row['BrandName']).strip() if pd.notna(row['BrandName']) else None
            channel_name = str(row['ChannelName']).strip() if pd.notna(row['ChannelName']) else None
            promo_type = str(row['PromotionType']).strip() if pd.notna(row.get('PromotionType')) else None
            unique_code = str(row['UniqueCode']).strip() if pd.notna(row['UniqueCode']) else None

            if brand_name and channel_name and promo_type and unique_code and pd.notna(row['StartDate']):
                brand_info = brand_map.get(brand_name, {})
                channel_info = channel_map.get(channel_name, {})
                type_info = promotion_type_map.get(promo_type, {})

                brand_id = brand_info.get('BrandID')
                channel_id_val = channel_info.get('ChannelID')
                promo_type_val = type_info.get('DisplayName')
                start_date = row['StartDate'].strftime('%Y-%m-%d') if hasattr(row['StartDate'], 'strftime') else str(row['StartDate'])[:10]

                if brand_id and channel_id_val and promo_type_val:
                    with get_db_cursor(commit=False) as cursor:
                        cursor.execute("""
                            SELECT 1 FROM [dbo].[TargetPromotionProduct]
                            WHERE BrandID = ? AND ChannelID = ? AND PromotionType = ?
                              AND StartDate = ? AND UniqueCode = ?
                        """, brand_id, channel_id_val, promo_type_val, start_date, unique_code)
                        if cursor.fetchone():
                            duplicate_rows.append(idx + 2)  # 엑셀 행 번호

        if duplicate_rows:
            raise HTTPException(400, f"이미 등록된 데이터가 있습니다. 동일 조건(브랜드+채널+행사유형+시작일+상품코드)의 데이터가 존재합니다. (행 {', '.join(map(str, duplicate_rows[:10]))}{'...' if len(duplicate_rows) > 10 else ''})")

        # PromotionID 자동 생성을 위한 접두사별 순번 관리
        # 형식: BrandCode(2) + TypeCode(2) + YYMM(4) + Sequence(2) = 10자리
        prefix_sequences = {}  # {prefix: current_sequence}

        # DB에서 기존 최대 순번 조회
        all_prefixes = set()
        for _, row in df.iterrows():
            # ID가 있는 행은 수정이므로 생성 불필요
            if 'TargetPromotionID' in row and pd.notna(row.get('TargetPromotionID')):
                continue

            brand_name = str(row['BrandName']).strip() if pd.notna(row['BrandName']) else None
            promo_type = str(row['PromotionType']).strip() if pd.notna(row.get('PromotionType')) else None

            if brand_name and promo_type and pd.notna(row['StartDate']):
                brand_info = brand_map.get(brand_name, {})
                type_info = promotion_type_map.get(promo_type, {})
                brand_code = brand_info.get('BrandCode', '')[:2] if brand_info.get('BrandCode') else ''
                type_code = type_info.get('TypeCode', '')

                if brand_code and type_code:
                    start_date = row['StartDate']
                    if hasattr(start_date, 'strftime'):
                        yymm = start_date.strftime('%y%m')
                    else:
                        yymm = pd.to_datetime(start_date).strftime('%y%m')
                    prefix = f"{brand_code}{type_code}{yymm}"
                    all_prefixes.add(prefix)

        # DB에서 각 접두사의 최대 순번 조회
        if all_prefixes:
            max_sequences = target_promotion_repo.get_max_sequences_by_prefixes(list(all_prefixes))
            for prefix, max_seq in max_sequences.items():
                prefix_sequences[prefix] = max_seq

        records = []
        for idx, row in df.iterrows():
            # 시간 포맷 처리 (HH:MM:SS)
            start_time_val = _format_time_value(row.get('StartTime', '00:00:00'))
            end_time_val = _format_time_value(row.get('EndTime', '23:59:59'))

            brand_name = row['BrandName'] if pd.notna(row['BrandName']) and row['BrandName'] != 'nan' else None
            channel_name = row['ChannelName'] if pd.notna(row['ChannelName']) and row['ChannelName'] != 'nan' else None
            unique_code = row['UniqueCode'] if pd.notna(row['UniqueCode']) and row['UniqueCode'] != 'nan' else None

            brand_info = brand_map.get(brand_name, {})
            channel_info = channel_map.get(channel_name, {})
            product_info = product_map.get(unique_code, {})

            # ID가 있으면 포함 (수정 양식인 경우)
            target_id = None
            if 'TargetPromotionID' in row and pd.notna(row['TargetPromotionID']):
                target_id = int(row['TargetPromotionID'])

            # 행사유형 처리
            promotion_type_val = None
            type_info = {}
            if 'PromotionType' in row and pd.notna(row.get('PromotionType')) and str(row['PromotionType']) != 'nan':
                promo_type_str = str(row['PromotionType']).strip()
                type_info = promotion_type_map.get(promo_type_str, {})
                promotion_type_val = type_info.get('DisplayName')

            # PromotionID 자동 생성 (신규 등록 시)
            promotion_id = None
            if 'PromotionID' in row and pd.notna(row.get('PromotionID')):
                promo_id_val = str(row['PromotionID']).strip()
                if promo_id_val and promo_id_val != 'nan':
                    # 기존 PromotionID가 있으면 사용
                    promotion_id = promo_id_val
            elif not target_id:
                # 신규 등록 시 PromotionID 자동 생성
                brand_code = brand_info.get('BrandCode', '')[:2] if brand_info.get('BrandCode') else ''
                type_code = type_info.get('TypeCode', '')

                if brand_code and type_code and pd.notna(row['StartDate']):
                    start_date = row['StartDate']
                    if hasattr(start_date, 'strftime'):
                        yymm = start_date.strftime('%y%m')
                    else:
                        yymm = pd.to_datetime(start_date).strftime('%y%m')

                    prefix = f"{brand_code}{type_code}{yymm}"

                    # 해당 접두사의 다음 순번 획득
                    current_seq = prefix_sequences.get(prefix, 0) + 1
                    prefix_sequences[prefix] = current_seq

                    # PromotionID 생성 (순번은 2자리 0-padding)
                    promotion_id = f"{prefix}{current_seq:02d}"
                    print(f"   [PromotionID 자동 생성] {promotion_id}")

            # 신규 등록인데 PromotionID가 없으면 에러 (안전장치)
            if not target_id and not promotion_id:
                row_num = int(idx) + 2  # 엑셀 행 번호 (헤더 + 0-index)
                raise HTTPException(400, f"행사ID를 생성할 수 없습니다. BrandCode, 행사유형, 시작일을 확인해주세요. (행 {row_num})")

            records.append({
                'TargetPromotionID': target_id,
                'PromotionID': promotion_id,
                'PromotionName': str(row['PromotionName']) if pd.notna(row.get('PromotionName')) else None,
                'PromotionType': promotion_type_val,
                'StartDate': row['StartDate'].strftime('%Y-%m-%d') if pd.notna(row['StartDate']) else None,
                'StartTime': start_time_val,
                'EndDate': row['EndDate'].strftime('%Y-%m-%d') if pd.notna(row['EndDate']) else None,
                'EndTime': end_time_val,
                'BrandID': brand_info.get('BrandID'),
                'BrandName': brand_info.get('BrandName'),
                'ChannelID': channel_info.get('ChannelID'),
                'ChannelName': channel_info.get('ChannelName'),
                'UniqueCode': unique_code,
                'ProductName': product_info.get('ProductName'),
                'TargetAmount': float(row['TargetAmount']) if pd.notna(row.get('TargetAmount')) else 0,
                'TargetQuantity': int(row['TargetQuantity']) if pd.notna(row.get('TargetQuantity')) else 0,
                'Notes': str(row['Notes']) if pd.notna(row.get('Notes')) else None,
            })

        result = target_promotion_repo.bulk_upsert(records)

        upload_end_time = datetime.now()
        duration = (upload_end_time - upload_start_time).total_seconds()

        # 중복 데이터 체크 - 에러 반환 (Repository 방어용)
        duplicates = result.get('duplicates', [])
        if duplicates:
            error_messages = []
            for dup in duplicates[:10]:
                error_messages.append(
                    f"행 {dup['row']}: 중복 데이터 (시작일: {dup['start_date']}, 상품코드: {dup['unique_code']}, 채널: {dup['channel_name']}, 행사유형: {dup['promotion_type']})"
                )
            if len(duplicates) > 10:
                error_messages.append(f"... 외 {len(duplicates) - 10}건 더 있음")
            raise HTTPException(400, "중복 데이터가 있습니다.\n" + "\n".join(error_messages))

        if user and request:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="TargetPromotionProduct",
                details={
                    "action": "EXCEL_UPLOAD",
                    "filename": file.filename,
                    "total_rows": len(df),
                    "inserted": result['inserted'],
                    "updated": result['updated'],
                    "duration_seconds": duration
                },
                ip_address=get_client_ip(request)
            )

        print(f"   업로드 완료: {result['inserted']}건 삽입, {result['updated']}건 수정")

        return {
            "message": "업로드 완료",
            "total_rows": len(df),
            "inserted": result['inserted'],
            "updated": result['updated'],
            "duration_seconds": duration
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"업로드 실패: {str(e)}")
