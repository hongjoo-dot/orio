"""
Revenue Plan Router
- 매출 계획 (예상매출/목표매출) API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import io
from datetime import datetime
from repositories.revenue_plan_repository import RevenuePlanRepository
from repositories import ActivityLogRepository
from core import get_db_cursor
from core.dependencies import get_current_user, get_client_ip, CurrentUser

router = APIRouter(prefix="/api/revenue-plan", tags=["Revenue Plan"])

# Repository 인스턴스
revenue_plan_repo = RevenuePlanRepository()
activity_log_repo = ActivityLogRepository()


# Pydantic Models
class RevenuePlanCreate(BaseModel):
    Date: str
    BrandID: int
    ChannelID: int
    ChannelDetail: Optional[str] = None
    PlanType: str  # 'TARGET' or 'EXPECTED'
    Amount: float


class RevenuePlanUpdate(BaseModel):
    Date: Optional[str] = None
    BrandID: Optional[int] = None
    ChannelID: Optional[int] = None
    ChannelDetail: Optional[str] = None
    PlanType: Optional[str] = None
    Amount: Optional[float] = None


class BulkDeleteRequest(BaseModel):
    ids: List[int]


# ========== CRUD 엔드포인트 ==========

@router.get("")
async def get_revenue_plans(
    page: int = 1,
    limit: int = 20,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    plan_type: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """매출 계획 목록 조회 (페이지네이션 및 필터링)"""
    try:
        filters = {}
        if brand_id is not None:
            filters['brand_id'] = brand_id
        if channel_id:
            filters['channel_id'] = channel_id
        if plan_type:
            filters['plan_type'] = plan_type
        if year:
            filters['year'] = year
        if month:
            filters['month'] = month
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date

        result = revenue_plan_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by="r.[Date]",
            order_dir="DESC"
        )

        return result
    except Exception as e:
        raise HTTPException(500, f"매출 계획 조회 실패: {str(e)}")


@router.get("/summary/monthly")
async def get_monthly_summary(
    year: int,
    plan_type: Optional[str] = None
):
    """월별 합계 조회"""
    try:
        result = revenue_plan_repo.get_summary_by_month(year, plan_type)
        return {"data": result}
    except Exception as e:
        raise HTTPException(500, f"월별 합계 조회 실패: {str(e)}")


@router.get("/summary/channel")
async def get_channel_summary(
    year: int,
    plan_type: Optional[str] = None
):
    """채널별 합계 조회"""
    try:
        result = revenue_plan_repo.get_summary_by_channel(year, plan_type)
        return {"data": result}
    except Exception as e:
        raise HTTPException(500, f"채널별 합계 조회 실패: {str(e)}")


@router.get("/{plan_id}")
async def get_revenue_plan(plan_id: int):
    """매출 계획 단일 조회"""
    try:
        item = revenue_plan_repo.get_by_id(plan_id)
        if not item:
            raise HTTPException(404, "매출 계획을 찾을 수 없습니다")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"매출 계획 조회 실패: {str(e)}")


@router.post("")
async def create_revenue_plan(
    data: RevenuePlanCreate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """매출 계획 생성"""
    try:
        plan_id = revenue_plan_repo.create(data.dict())

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="RevenuePlan",
                target_id=str(plan_id),
                details=data.dict(),
                ip_address=get_client_ip(request)
            )

        return {"PlanID": plan_id, **data.dict()}
    except Exception as e:
        raise HTTPException(500, f"매출 계획 생성 실패: {str(e)}")


@router.put("/{plan_id}")
async def update_revenue_plan(
    plan_id: int,
    data: RevenuePlanUpdate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """매출 계획 수정"""
    try:
        if not revenue_plan_repo.exists(plan_id):
            raise HTTPException(404, "매출 계획을 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        # UpdatedAt 자동 갱신
        update_data['UpdatedAt'] = datetime.now()

        success = revenue_plan_repo.update(plan_id, update_data)
        if not success:
            raise HTTPException(500, "매출 계획 수정 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="UPDATE",
                target_table="RevenuePlan",
                target_id=str(plan_id),
                details=update_data,
                ip_address=get_client_ip(request)
            )

        return {"message": "수정되었습니다", "PlanID": plan_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"매출 계획 수정 실패: {str(e)}")


@router.delete("/{plan_id}")
async def delete_revenue_plan(
    plan_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """매출 계획 삭제"""
    try:
        if not revenue_plan_repo.exists(plan_id):
            raise HTTPException(404, "매출 계획을 찾을 수 없습니다")

        success = revenue_plan_repo.delete(plan_id)
        if not success:
            raise HTTPException(500, "매출 계획 삭제 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="DELETE",
                target_table="RevenuePlan",
                target_id=str(plan_id),
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"매출 계획 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
async def bulk_delete_revenue_plans(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """매출 계획 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = revenue_plan_repo.bulk_delete(request_body.ids)

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="BULK_DELETE",
                target_table="RevenuePlan",
                details={"deleted_ids": request_body.ids, "count": deleted_count},
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ========== 엑셀 업로드/다운로드 ==========

@router.get("/download/template")
async def download_template():
    """엑셀 업로드용 양식 다운로드"""
    columns = ['DATE', 'BRAND', 'CHANNEL', 'CHANNEL_DETAIL', 'PLAN_TYPE', 'AMOUNT']

    # 샘플 데이터
    sample_data = [
        {'DATE': '2025-01-01', 'BRAND': '스크럽대디', 'CHANNEL': '이마트', 'CHANNEL_DETAIL': '이마트 성수점', 'PLAN_TYPE': 'TARGET', 'AMOUNT': 100000000},
        {'DATE': '2025-01-01', 'BRAND': '프로그', 'CHANNEL': '쿠팡', 'CHANNEL_DETAIL': '쿠팡(로켓)', 'PLAN_TYPE': 'EXPECTED', 'AMOUNT': 500000000},
    ]

    df = pd.DataFrame(sample_data, columns=columns)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='RevenuePlan_Template')

        worksheet = writer.sheets['RevenuePlan_Template']
        for i, col in enumerate(columns):
            worksheet.set_column(i, i, 18)

    output.seek(0)

    headers = {
        'Content-Disposition': 'attachment; filename="revenue_plan_template.xlsx"'
    }

    return StreamingResponse(
        output,
        headers=headers,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    request: Request = None,
    user: CurrentUser = Depends(get_current_user)
):
    """
    엑셀 파일 업로드 및 RevenuePlan에 UPSERT
    - DATE + BRAND + CHANNEL + PLAN_TYPE 조합이 같으면 UPDATE
    - 없으면 INSERT
    """
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, "엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.")

        start_time = datetime.now()
        print(f"\n[매출 계획 업로드 시작] {file.filename}")

        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        print(f"   총 {len(df):,}행 로드됨")

        # 컬럼명 정규화
        df.columns = [col.upper().strip() for col in df.columns]

        # 필수 컬럼 확인
        required_columns = ['DATE', 'BRAND', 'CHANNEL', 'PLAN_TYPE', 'AMOUNT']

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(400, f"필수 컬럼 누락: {', '.join(missing_columns)}")

        # 날짜 변환
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        invalid_dates = df['DATE'].isna().sum()
        if invalid_dates > 0:
            print(f"   [경고] 날짜 파싱 실패: {invalid_dates:,}행 제거")
            df = df[df['DATE'].notna()]

        # PLAN_TYPE 정규화
        df['PLAN_TYPE'] = df['PLAN_TYPE'].str.upper().str.strip()
        valid_types = df['PLAN_TYPE'].isin(['TARGET', 'EXPECTED'])
        invalid_types = (~valid_types).sum()
        if invalid_types > 0:
            print(f"   [경고] 잘못된 PLAN_TYPE: {invalid_types:,}행 제거")
            df = df[valid_types]

        # 매핑 테이블 로드
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT Name, BrandID FROM [dbo].[Brand]")
            brand_map = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT Name, ChannelID FROM [dbo].[Channel]")
            channel_map = {row[0]: row[1] for row in cursor.fetchall()}

        print(f"   매핑 테이블 로드 완료 (Brand: {len(brand_map)}, Channel: {len(channel_map)})")

        # 매핑 실패 추적
        unmapped_brands = set()
        unmapped_channels = set()

        # 레코드 준비 (집계 없이 모든 행 INSERT)
        records = []
        for idx, row in df.iterrows():
            brand_name = str(row['BRAND']).strip() if pd.notna(row['BRAND']) else None
            channel_name = str(row['CHANNEL']).strip() if pd.notna(row['CHANNEL']) else None
            channel_detail = str(row['CHANNEL_DETAIL']).strip() if 'CHANNEL_DETAIL' in df.columns and pd.notna(row['CHANNEL_DETAIL']) else None

            brand_id = brand_map.get(brand_name)
            channel_id = channel_map.get(channel_name)

            if brand_name and brand_id is None:
                unmapped_brands.add(brand_name)
                continue

            if channel_name and channel_id is None:
                unmapped_channels.add(channel_name)
                continue

            if brand_id is None or channel_id is None:
                continue

            records.append({
                'Date': row['DATE'],
                'BrandID': brand_id,
                'ChannelID': channel_id,
                'ChannelDetail': channel_detail,
                'PlanType': row['PLAN_TYPE'],
                'Amount': float(row['AMOUNT']) if pd.notna(row['AMOUNT']) else 0
            })

        print(f"   유효 레코드: {len(records):,}건")

        # INSERT 실행
        result = revenue_plan_repo.bulk_insert(records)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 활동 로그
        if user and request:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="RevenuePlan",
                details={
                    "action": "EXCEL_UPLOAD",
                    "filename": file.filename,
                    "total_rows": len(df),
                    "inserted": result['inserted'],
                    "updated": result['updated'],
                    "unmapped_brands": len(unmapped_brands),
                    "unmapped_channels": len(unmapped_channels),
                    "duration_seconds": duration
                },
                ip_address=get_client_ip(request)
            )

        print(f"\n{'='*60}")
        print(f"업로드 완료: INSERT {result['inserted']:,}건, UPDATE {result['updated']:,}건")
        if unmapped_brands:
            print(f"   [경고] 매핑 안 된 브랜드: {sorted(unmapped_brands)}")
        if unmapped_channels:
            print(f"   [경고] 매핑 안 된 채널: {sorted(unmapped_channels)}")
        print(f"{'='*60}")

        return {
            "message": "Upload completed",
            "total_rows": len(df),
            "valid_records": len(records),
            "inserted": result['inserted'],
            "updated": result['updated'],
            "unmapped_brands": len(unmapped_brands),
            "unmapped_channels": len(unmapped_channels),
            "unmapped_brands_list": sorted(list(unmapped_brands)),
            "unmapped_channels_list": sorted(list(unmapped_channels))
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"업로드 실패: {str(e)}")
