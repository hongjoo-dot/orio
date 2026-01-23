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
from repositories import ActivityLogRepository, BrandRepository, ChannelRepository
from core import get_db_cursor
from core.dependencies import get_current_user, get_client_ip, CurrentUser

# ========== 기본 목표 Router ==========
router = APIRouter(prefix="/api/targets/base", tags=["TargetBase"])

# Repository 인스턴스
target_base_repo = TargetBaseRepository()
activity_log_repo = ActivityLogRepository()
brand_repo = BrandRepository()
channel_repo = ChannelRepository()


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
    unique_code: Optional[str] = None,
    product_name: Optional[str] = None
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
        if unique_code:
            filters['unique_code'] = unique_code
        if product_name:
            filters['product_name'] = product_name

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
async def get_target_base_year_months():
    """기본 목표 년월 목록 조회"""
    try:
        year_months = target_base_repo.get_year_months()
        return {"year_months": year_months}
    except Exception as e:
        raise HTTPException(500, f"년월 목록 조회 실패: {str(e)}")


@router.get("/{target_id}")
async def get_target_base_item(target_id: int):
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
async def create_target_base(
    data: TargetBaseCreate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """기본 목표 생성"""
    try:
        target_id = target_base_repo.create(data.dict(exclude_none=True))

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="TargetBaseProduct",
                target_id=str(target_id),
                details={"UniqueCode": data.UniqueCode, "Date": data.Date},
                ip_address=get_client_ip(request)
            )

        return {"TargetBaseID": target_id, **data.dict()}
    except Exception as e:
        raise HTTPException(500, f"목표 생성 실패: {str(e)}")


@router.put("/{target_id}")
async def update_target_base(
    target_id: int,
    data: TargetBaseUpdate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
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

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="UPDATE",
                target_table="TargetBaseProduct",
                target_id=str(target_id),
                details=update_data,
                ip_address=get_client_ip(request)
            )

        return {"message": "수정되었습니다", "TargetBaseID": target_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"목표 수정 실패: {str(e)}")


@router.delete("/{target_id}")
async def delete_target_base(
    target_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """기본 목표 삭제"""
    try:
        if not target_base_repo.exists(target_id):
            raise HTTPException(404, "목표 데이터를 찾을 수 없습니다")

        success = target_base_repo.delete(target_id)
        if not success:
            raise HTTPException(500, "목표 삭제 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="DELETE",
                target_table="TargetBaseProduct",
                target_id=str(target_id),
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"목표 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
async def bulk_delete_target_base(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """기본 목표 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = target_base_repo.bulk_delete(request_body.ids)

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="BULK_DELETE",
                target_table="TargetBaseProduct",
                details={"deleted_ids": request_body.ids, "count": deleted_count},
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


@router.post("/filter-delete")
async def filter_delete_target_base(
    request_body: FilterDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """필터 조건으로 기본 목표 일괄 삭제"""
    try:
        deleted_count = target_base_repo.delete_by_filter(
            year_month=request_body.year_month,
            brand_id=request_body.brand_id,
            channel_id=request_body.channel_id
        )

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="BULK_DELETE",
                target_table="TargetBaseProduct",
                details={
                    "filter": request_body.dict(),
                    "deleted_count": deleted_count
                },
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ========== 기본 목표 엑셀 ==========

@router.get("/download/template")
async def download_target_base_template():
    """기본 목표 신규 등록용 양식 다운로드"""
    columns = ['날짜', '브랜드ID', '브랜드명', '채널ID', '채널명', '상품코드', '상품명', '목표금액', '목표수량', '비고']

    df = pd.DataFrame(columns=columns)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='기본목표_양식')

        worksheet = writer.sheets['기본목표_양식']
        for i, col in enumerate(columns):
            worksheet.set_column(i, i, 15)

    output.seek(0)

    headers = {
        'Content-Disposition': 'attachment; filename="target_base_template.xlsx"'
    }

    return StreamingResponse(
        output,
        headers=headers,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@router.get("/download/data")
async def download_target_base_data(
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None
):
    """기본 목표 데이터 다운로드 (수정용)"""
    try:
        filters = {}
        if year_month:
            filters['year_month'] = year_month
        if brand_id:
            filters['brand_id'] = brand_id
        if channel_id:
            filters['channel_id'] = channel_id

        # 전체 데이터 조회 (페이지네이션 없이)
        result = target_base_repo.get_list(page=1, limit=100000, filters=filters)
        data = result['data']

        if not data:
            raise HTTPException(404, "다운로드할 데이터가 없습니다")

        # DataFrame 생성
        df = pd.DataFrame(data)

        # 컬럼 순서 및 이름 변경
        column_map = {
            'TargetBaseID': 'ID',
            'Date': '날짜',
            'BrandID': '브랜드ID',
            'BrandName': '브랜드명',
            'ChannelID': '채널ID',
            'ChannelName': '채널명',
            'UniqueCode': '상품코드',
            'ProductName': '상품명',
            'TargetAmount': '목표금액',
            'TargetQuantity': '목표수량',
            'Notes': '비고'
        }

        # 필요한 컬럼만 선택
        export_columns = list(column_map.keys())
        df = df[[col for col in export_columns if col in df.columns]]
        df = df.rename(columns=column_map)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='기본목표_데이터')

            worksheet = writer.sheets['기본목표_데이터']
            for i in range(len(df.columns)):
                worksheet.set_column(i, i, 15)

        output.seek(0)

        filename = f"target_base_data_{year_month or 'all'}.xlsx"
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


@router.post("/upload")
async def upload_target_base(
    file: UploadFile = File(...),
    request: Request = None,
    user: CurrentUser = Depends(get_current_user)
):
    """기본 목표 엑셀 업로드"""
    try:
        start_time = datetime.now()

        # 파일 확장자 검증
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, "엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        print(f"\n[기본 목표 업로드 시작] {file.filename}")

        # 파일 읽기
        content = await file.read()
        excel_file = io.BytesIO(content)
        df = pd.read_excel(excel_file)
        print(f"   총 {len(df):,}행 로드됨")

        # 컬럼 매핑
        column_map = {
            'ID': 'TargetBaseID',
            '날짜': 'Date',
            '브랜드ID': 'BrandID',
            '브랜드명': 'BrandName',
            '채널ID': 'ChannelID',
            '채널명': 'ChannelName',
            '상품코드': 'UniqueCode',
            '상품명': 'ProductName',
            '목표금액': 'TargetAmount',
            '목표수량': 'TargetQuantity',
            '비고': 'Notes'
        }
        df = df.rename(columns=column_map)

        # 필수 컬럼 확인
        required_cols = ['Date', 'BrandID', 'ChannelID', 'UniqueCode']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(400, f"필수 컬럼이 없습니다: {missing_cols}")

        # 날짜 변환
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        invalid_dates = df['Date'].isna().sum()
        if invalid_dates > 0:
            print(f"   [경고] 날짜 파싱 실패: {invalid_dates:,}행")
            df = df[df['Date'].notna()]

        # 데이터 타입 변환
        df['BrandID'] = pd.to_numeric(df['BrandID'], errors='coerce').fillna(0).astype(int)
        df['ChannelID'] = pd.to_numeric(df['ChannelID'], errors='coerce').fillna(0).astype(int)
        df['TargetAmount'] = pd.to_numeric(df['TargetAmount'], errors='coerce').fillna(0)
        df['TargetQuantity'] = pd.to_numeric(df['TargetQuantity'], errors='coerce').fillna(0).astype(int)

        # 레코드 준비
        records = []
        for _, row in df.iterrows():
            records.append({
                'Date': row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else None,
                'BrandID': int(row['BrandID']) if pd.notna(row['BrandID']) else None,
                'BrandName': str(row['BrandName']) if pd.notna(row.get('BrandName')) else None,
                'ChannelID': int(row['ChannelID']) if pd.notna(row['ChannelID']) else None,
                'ChannelName': str(row['ChannelName']) if pd.notna(row.get('ChannelName')) else None,
                'UniqueCode': str(row['UniqueCode']) if pd.notna(row['UniqueCode']) else None,
                'ProductName': str(row['ProductName']) if pd.notna(row.get('ProductName')) else None,
                'TargetAmount': float(row['TargetAmount']) if pd.notna(row.get('TargetAmount')) else 0,
                'TargetQuantity': int(row['TargetQuantity']) if pd.notna(row.get('TargetQuantity')) else 0,
                'Notes': str(row['Notes']) if pd.notna(row.get('Notes')) else None,
            })

        # UPSERT 실행
        result = target_base_repo.bulk_upsert(records)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

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
    StartTime: Optional[str] = "00:00"
    EndDate: str
    EndTime: Optional[str] = "00:00"
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
    promotion_id: Optional[str] = None


# ========== 행사 목표 CRUD ==========

@promotion_router.get("")
async def get_target_promotion_list(
    page: int = 1,
    limit: int = 20,
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    promotion_id: Optional[str] = None,
    unique_code: Optional[str] = None,
    product_name: Optional[str] = None
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
        if promotion_id:
            filters['promotion_id'] = promotion_id
        if unique_code:
            filters['unique_code'] = unique_code
        if product_name:
            filters['product_name'] = product_name

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
async def get_target_promotion_year_months():
    """행사 목표 년월 목록 조회"""
    try:
        year_months = target_promotion_repo.get_year_months()
        return {"year_months": year_months}
    except Exception as e:
        raise HTTPException(500, f"년월 목록 조회 실패: {str(e)}")


@promotion_router.get("/promotions")
async def get_promotions_list(year_month: Optional[str] = None):
    """행사 목록 조회 (드롭다운용)"""
    try:
        promotions = target_promotion_repo.get_promotions(year_month)
        return {"promotions": promotions}
    except Exception as e:
        raise HTTPException(500, f"행사 목록 조회 실패: {str(e)}")


@promotion_router.get("/{target_id}")
async def get_target_promotion_item(target_id: int):
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
async def create_target_promotion(
    data: TargetPromotionCreate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """행사 목표 생성"""
    try:
        target_id = target_promotion_repo.create(data.dict(exclude_none=True))

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="TargetPromotionProduct",
                target_id=str(target_id),
                details={"PromotionID": data.PromotionID, "UniqueCode": data.UniqueCode},
                ip_address=get_client_ip(request)
            )

        return {"TargetPromotionID": target_id, **data.dict()}
    except Exception as e:
        raise HTTPException(500, f"목표 생성 실패: {str(e)}")


@promotion_router.put("/{target_id}")
async def update_target_promotion(
    target_id: int,
    data: TargetPromotionUpdate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
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

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="UPDATE",
                target_table="TargetPromotionProduct",
                target_id=str(target_id),
                details=update_data,
                ip_address=get_client_ip(request)
            )

        return {"message": "수정되었습니다", "TargetPromotionID": target_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"목표 수정 실패: {str(e)}")


@promotion_router.delete("/{target_id}")
async def delete_target_promotion(
    target_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """행사 목표 삭제"""
    try:
        if not target_promotion_repo.exists(target_id):
            raise HTTPException(404, "목표 데이터를 찾을 수 없습니다")

        success = target_promotion_repo.delete(target_id)
        if not success:
            raise HTTPException(500, "목표 삭제 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="DELETE",
                target_table="TargetPromotionProduct",
                target_id=str(target_id),
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"목표 삭제 실패: {str(e)}")


@promotion_router.post("/bulk-delete")
async def bulk_delete_target_promotion(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """행사 목표 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = target_promotion_repo.bulk_delete(request_body.ids)

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="BULK_DELETE",
                target_table="TargetPromotionProduct",
                details={"deleted_ids": request_body.ids, "count": deleted_count},
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


@promotion_router.post("/filter-delete")
async def filter_delete_target_promotion(
    request_body: PromotionFilterDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """필터 조건으로 행사 목표 일괄 삭제"""
    try:
        deleted_count = target_promotion_repo.delete_by_filter(
            year_month=request_body.year_month,
            brand_id=request_body.brand_id,
            channel_id=request_body.channel_id,
            promotion_id=request_body.promotion_id
        )

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="BULK_DELETE",
                target_table="TargetPromotionProduct",
                details={
                    "filter": request_body.dict(),
                    "deleted_count": deleted_count
                },
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ========== 행사 목표 엑셀 ==========

@promotion_router.get("/download/template")
async def download_target_promotion_template():
    """행사 목표 신규 등록용 양식 다운로드"""
    columns = [
        '행사ID', '행사명', '시작일', '시작시간', '종료일', '종료시간',
        '브랜드ID', '브랜드명', '채널ID', '채널명',
        '상품코드', '상품명', '목표금액', '목표수량', '비고'
    ]

    df = pd.DataFrame(columns=columns)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='행사목표_양식')

        worksheet = writer.sheets['행사목표_양식']
        for i, col in enumerate(columns):
            worksheet.set_column(i, i, 15)

    output.seek(0)

    headers = {
        'Content-Disposition': 'attachment; filename="target_promotion_template.xlsx"'
    }

    return StreamingResponse(
        output,
        headers=headers,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@promotion_router.get("/download/data")
async def download_target_promotion_data(
    year_month: Optional[str] = None,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    promotion_id: Optional[str] = None
):
    """행사 목표 데이터 다운로드 (수정용)"""
    try:
        filters = {}
        if year_month:
            filters['year_month'] = year_month
        if brand_id:
            filters['brand_id'] = brand_id
        if channel_id:
            filters['channel_id'] = channel_id
        if promotion_id:
            filters['promotion_id'] = promotion_id

        result = target_promotion_repo.get_list(page=1, limit=100000, filters=filters)
        data = result['data']

        if not data:
            raise HTTPException(404, "다운로드할 데이터가 없습니다")

        df = pd.DataFrame(data)

        column_map = {
            'TargetPromotionID': 'ID',
            'PromotionID': '행사ID',
            'PromotionName': '행사명',
            'StartDate': '시작일',
            'StartTime': '시작시간',
            'EndDate': '종료일',
            'EndTime': '종료시간',
            'BrandID': '브랜드ID',
            'BrandName': '브랜드명',
            'ChannelID': '채널ID',
            'ChannelName': '채널명',
            'UniqueCode': '상품코드',
            'ProductName': '상품명',
            'TargetAmount': '목표금액',
            'TargetQuantity': '목표수량',
            'Notes': '비고'
        }

        export_columns = list(column_map.keys())
        df = df[[col for col in export_columns if col in df.columns]]
        df = df.rename(columns=column_map)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='행사목표_데이터')

            worksheet = writer.sheets['행사목표_데이터']
            for i in range(len(df.columns)):
                worksheet.set_column(i, i, 15)

        output.seek(0)

        filename = f"target_promotion_data_{year_month or 'all'}.xlsx"
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


@promotion_router.post("/upload")
async def upload_target_promotion(
    file: UploadFile = File(...),
    request: Request = None,
    user: CurrentUser = Depends(get_current_user)
):
    """행사 목표 엑셀 업로드"""
    try:
        start_time = datetime.now()

        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, "엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        print(f"\n[행사 목표 업로드 시작] {file.filename}")

        content = await file.read()
        excel_file = io.BytesIO(content)
        df = pd.read_excel(excel_file)
        print(f"   총 {len(df):,}행 로드됨")

        column_map = {
            'ID': 'TargetPromotionID',
            '행사ID': 'PromotionID',
            '행사명': 'PromotionName',
            '시작일': 'StartDate',
            '시작시간': 'StartTime',
            '종료일': 'EndDate',
            '종료시간': 'EndTime',
            '브랜드ID': 'BrandID',
            '브랜드명': 'BrandName',
            '채널ID': 'ChannelID',
            '채널명': 'ChannelName',
            '상품코드': 'UniqueCode',
            '상품명': 'ProductName',
            '목표금액': 'TargetAmount',
            '목표수량': 'TargetQuantity',
            '비고': 'Notes'
        }
        df = df.rename(columns=column_map)

        required_cols = ['PromotionID', 'StartDate', 'EndDate', 'BrandID', 'ChannelID', 'UniqueCode']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(400, f"필수 컬럼이 없습니다: {missing_cols}")

        # 날짜 변환
        df['StartDate'] = pd.to_datetime(df['StartDate'], errors='coerce')
        df['EndDate'] = pd.to_datetime(df['EndDate'], errors='coerce')

        # 시간 처리 (기본값 00:00)
        if 'StartTime' not in df.columns:
            df['StartTime'] = '00:00'
        if 'EndTime' not in df.columns:
            df['EndTime'] = '00:00'

        # 데이터 타입 변환
        df['BrandID'] = pd.to_numeric(df['BrandID'], errors='coerce').fillna(0).astype(int)
        df['ChannelID'] = pd.to_numeric(df['ChannelID'], errors='coerce').fillna(0).astype(int)
        df['TargetAmount'] = pd.to_numeric(df['TargetAmount'], errors='coerce').fillna(0)
        df['TargetQuantity'] = pd.to_numeric(df['TargetQuantity'], errors='coerce').fillna(0).astype(int)

        records = []
        for _, row in df.iterrows():
            # 시간 포맷 처리
            start_time_val = row.get('StartTime', '00:00')
            end_time_val = row.get('EndTime', '00:00')

            if pd.isna(start_time_val):
                start_time_val = '00:00'
            elif hasattr(start_time_val, 'strftime'):
                start_time_val = start_time_val.strftime('%H:%M')
            else:
                start_time_val = str(start_time_val)[:5] if start_time_val else '00:00'

            if pd.isna(end_time_val):
                end_time_val = '00:00'
            elif hasattr(end_time_val, 'strftime'):
                end_time_val = end_time_val.strftime('%H:%M')
            else:
                end_time_val = str(end_time_val)[:5] if end_time_val else '00:00'

            records.append({
                'PromotionID': str(row['PromotionID']) if pd.notna(row['PromotionID']) else None,
                'PromotionName': str(row['PromotionName']) if pd.notna(row.get('PromotionName')) else None,
                'StartDate': row['StartDate'].strftime('%Y-%m-%d') if pd.notna(row['StartDate']) else None,
                'StartTime': start_time_val,
                'EndDate': row['EndDate'].strftime('%Y-%m-%d') if pd.notna(row['EndDate']) else None,
                'EndTime': end_time_val,
                'BrandID': int(row['BrandID']) if pd.notna(row['BrandID']) else None,
                'BrandName': str(row['BrandName']) if pd.notna(row.get('BrandName')) else None,
                'ChannelID': int(row['ChannelID']) if pd.notna(row['ChannelID']) else None,
                'ChannelName': str(row['ChannelName']) if pd.notna(row.get('ChannelName')) else None,
                'UniqueCode': str(row['UniqueCode']) if pd.notna(row['UniqueCode']) else None,
                'ProductName': str(row['ProductName']) if pd.notna(row.get('ProductName')) else None,
                'TargetAmount': float(row['TargetAmount']) if pd.notna(row.get('TargetAmount')) else 0,
                'TargetQuantity': int(row['TargetQuantity']) if pd.notna(row.get('TargetQuantity')) else 0,
                'Notes': str(row['Notes']) if pd.notna(row.get('Notes')) else None,
            })

        result = target_promotion_repo.bulk_upsert(records)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

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
