"""
Channel Router
- Channel 및 ChannelDetail CRUD API 엔드포인트
- Repository 패턴 활용
- 활동 로그 기록
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, List
from repositories import ChannelRepository, ChannelDetailRepository, ActivityLogRepository
from core.dependencies import get_current_user, get_client_ip, CurrentUser

router = APIRouter(prefix="/api/channels", tags=["Channel"])

# Repository 인스턴스
channel_repo = ChannelRepository()
detail_repo = ChannelDetailRepository()
activity_log_repo = ActivityLogRepository()


# Pydantic Models
class ChannelCreate(BaseModel):
    Name: str
    Group: Optional[str] = None
    Type: Optional[str] = None
    ContractType: Optional[str] = None
    Owner: Optional[str] = None
    LiveSource: Optional[str] = None
    SabangnetMallID: Optional[str] = None


class ChannelUpdate(BaseModel):
    Name: Optional[str] = None
    Group: Optional[str] = None
    Type: Optional[str] = None
    ContractType: Optional[str] = None
    Owner: Optional[str] = None
    LiveSource: Optional[str] = None
    SabangnetMallID: Optional[str] = None


class ChannelDetailCreate(BaseModel):
    BizNumber: str
    DetailName: str


class ChannelDetailUpdate(BaseModel):
    ChannelID: Optional[int] = None
    BizNumber: Optional[str] = None
    DetailName: Optional[str] = None


class ChannelIntegratedCreate(BaseModel):
    """Channel과 ChannelDetails 통합 생성"""
    channel: ChannelCreate
    details: List[ChannelDetailCreate]


class BulkDeleteRequest(BaseModel):
    ids: List[int]


# ========== Channel CRUD 엔드포인트 ==========

@router.get("")
async def get_channels(
    page: int = 1,
    limit: int = 20,
    name: Optional[str] = None,
    detail_name: Optional[str] = None,
    group: Optional[str] = None,
    type: Optional[str] = None,
    contract_type: Optional[str] = None
):
    """Channel 목록 조회 (페이지네이션 및 필터링)"""
    try:
        filters = {}
        if name:
            filters['name'] = name
        if detail_name:
            filters['detail_name'] = detail_name
        if group:
            filters['group'] = group
        if type:
            filters['type'] = type
        if contract_type:
            filters['contract_type'] = contract_type

        result = channel_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by="ChannelID",
            order_dir="DESC"
        )

        return result
    except Exception as e:
        raise HTTPException(500, f"채널 목록 조회 실패: {str(e)}")


@router.get("/metadata")
async def get_channel_metadata():
    """Channel 메타데이터 조회 (필터용)"""
    try:
        metadata = channel_repo.get_metadata()
        metadata['detail_names'] = detail_repo.get_detail_names()
        return metadata
    except Exception as e:
        raise HTTPException(500, f"메타데이터 조회 실패: {str(e)}")


@router.get("/list")
async def get_channel_list():
    """채널 목록 조회 (드롭다운용) - ChannelID와 Name만 반환"""
    try:
        return channel_repo.get_channel_list()
    except Exception as e:
        raise HTTPException(500, f"채널 목록 조회 실패: {str(e)}")


@router.get("/{channel_id}")
async def get_channel(channel_id: int):
    """Channel 단일 조회"""
    try:
        channel = channel_repo.get_by_id(channel_id)
        if not channel:
            raise HTTPException(404, "채널을 찾을 수 없습니다")
        return channel
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"채널 조회 실패: {str(e)}")


@router.post("")
async def create_channel(
    data: ChannelCreate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """Channel 생성"""
    try:
        if channel_repo.check_duplicate("Name", data.Name):
            raise HTTPException(400, f"중복된 채널명입니다: {data.Name}")

        channel_id = channel_repo.create(data.dict(exclude_none=True))

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="Channel",
                target_id=str(channel_id),
                details={"Name": data.Name},
                ip_address=get_client_ip(request)
            )

        return {"ChannelID": channel_id, **data.dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"채널 생성 실패: {str(e)}")


@router.post("/integrated")
async def create_channel_integrated(
    data: ChannelIntegratedCreate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """Channel과 ChannelDetails를 한 번에 생성 (트랜잭션)"""
    try:
        result = detail_repo.create_with_channel(
            channel_data=data.channel.dict(exclude_none=True),
            details=[d.dict(exclude_none=True) for d in data.details]
        )

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="Channel+ChannelDetail",
                target_id=str(result.get("ChannelID")),
                details={"Name": data.channel.Name, "details_count": len(data.details)},
                ip_address=get_client_ip(request)
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"통합 생성 실패: {str(e)}")


@router.put("/{channel_id}")
async def update_channel(
    channel_id: int,
    data: ChannelUpdate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """Channel 수정"""
    try:
        if not channel_repo.exists(channel_id):
            raise HTTPException(404, "채널을 찾을 수 없습니다")

        if data.Name and channel_repo.check_duplicate("Name", data.Name, exclude_id=channel_id):
            raise HTTPException(400, f"중복된 채널명입니다: {data.Name}")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = channel_repo.update(channel_id, update_data)
        if not success:
            raise HTTPException(500, "채널 수정 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="UPDATE",
                target_table="Channel",
                target_id=str(channel_id),
                details=update_data,
                ip_address=get_client_ip(request)
            )

        return {"message": "수정되었습니다", "ChannelID": channel_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"채널 수정 실패: {str(e)}")


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """Channel 삭제 (연관된 ChannelDetail도 함께 삭제)"""
    try:
        if not channel_repo.exists(channel_id):
            raise HTTPException(404, "채널을 찾을 수 없습니다")

        detail_repo.delete_by_channel_id(channel_id)
        success = channel_repo.delete(channel_id)

        if not success:
            raise HTTPException(500, "채널 삭제 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="DELETE",
                target_table="Channel",
                target_id=str(channel_id),
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"채널 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
async def bulk_delete_channels(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """Channel 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        for channel_id in request_body.ids:
            detail_repo.delete_by_channel_id(channel_id)

        deleted_count = channel_repo.bulk_delete(request_body.ids)

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="BULK_DELETE",
                target_table="Channel",
                details={"deleted_ids": request_body.ids, "count": deleted_count},
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ========== ChannelDetail 관련 엔드포인트 ==========

@router.get("/{channel_id}/details")
async def get_channel_details(channel_id: int):
    """특정 Channel의 모든 Detail 조회"""
    try:
        details = detail_repo.get_by_channel_id(channel_id)
        return {"data": details, "total": len(details)}
    except Exception as e:
        raise HTTPException(500, f"채널 상세 조회 실패: {str(e)}")


@router.post("/{channel_id}/details")
async def create_channel_detail(
    channel_id: int,
    data: ChannelDetailCreate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ChannelDetail 생성"""
    try:
        if not channel_repo.exists(channel_id):
            raise HTTPException(404, "채널을 찾을 수 없습니다")

        detail_data = data.dict()
        detail_data['ChannelID'] = channel_id
        detail_id = detail_repo.create(detail_data)

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="ChannelDetail",
                target_id=str(detail_id),
                details={"DetailName": data.DetailName, "ChannelID": channel_id},
                ip_address=get_client_ip(request)
            )

        return {"ChannelDetailID": detail_id, **detail_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"채널 상세 생성 실패: {str(e)}")


@router.put("/details/{detail_id}")
async def update_channel_detail(
    detail_id: int,
    data: ChannelDetailUpdate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ChannelDetail 수정"""
    try:
        if not detail_repo.exists(detail_id):
            raise HTTPException(404, "채널 상세를 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = detail_repo.update(detail_id, update_data)
        if not success:
            raise HTTPException(500, "채널 상세 수정 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="UPDATE",
                target_table="ChannelDetail",
                target_id=str(detail_id),
                details=update_data,
                ip_address=get_client_ip(request)
            )

        return {"message": "수정되었습니다", "ChannelDetailID": detail_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"채널 상세 수정 실패: {str(e)}")


@router.delete("/details/{detail_id}")
async def delete_channel_detail(
    detail_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ChannelDetail 삭제"""
    try:
        success = detail_repo.delete(detail_id)
        if not success:
            raise HTTPException(404, "채널 상세를 찾을 수 없습니다")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="DELETE",
                target_table="ChannelDetail",
                target_id=str(detail_id),
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"채널 상세 삭제 실패: {str(e)}")


# ========== ChannelDetail 독립 라우터 (호환성) ==========

channeldetail_router = APIRouter(prefix="/api/channeldetails", tags=["ChannelDetail"])


@channeldetail_router.get("")
async def get_channeldetails(
    page: int = 1,
    limit: int = 50,
    channel_id: Optional[int] = None,
    detail_name: Optional[str] = None
):
    """ChannelDetail 목록 조회"""
    try:
        filters = {}
        if channel_id:
            filters['channel_id'] = channel_id
        if detail_name:
            filters['detail_name'] = detail_name

        result = detail_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by="ChannelDetailID",
            order_dir="DESC"
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"상세정보 목록 조회 실패: {str(e)}")


@channeldetail_router.get("/{detail_id}")
async def get_channeldetail_by_id(detail_id: int):
    """ChannelDetail 단일 조회"""
    try:
        detail = detail_repo.get_by_id(detail_id)
        if not detail:
            raise HTTPException(404, "상세정보를 찾을 수 없습니다")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"상세정보 조회 실패: {str(e)}")


class ChannelDetailFull(BaseModel):
    """ChannelDetail 전체 생성 (ChannelID 포함)"""
    ChannelID: int
    BizNumber: str
    DetailName: str


@channeldetail_router.post("")
async def create_channeldetail_direct(
    data: ChannelDetailFull,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ChannelDetail 직접 생성"""
    try:
        if not channel_repo.exists(data.ChannelID):
            raise HTTPException(404, "채널을 찾을 수 없습니다")

        if data.BizNumber and detail_repo.check_duplicate("BizNumber", data.BizNumber):
            raise HTTPException(400, f"중복된 사업자번호입니다: {data.BizNumber}")

        detail_id = detail_repo.create(data.dict(exclude_none=True))

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="ChannelDetail",
                target_id=str(detail_id),
                details={"DetailName": data.DetailName, "ChannelID": data.ChannelID},
                ip_address=get_client_ip(request)
            )

        return {"ChannelDetailID": detail_id, **data.dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"상세정보 생성 실패: {str(e)}")


@channeldetail_router.put("/{detail_id}")
async def update_channeldetail_direct(
    detail_id: int,
    data: ChannelDetailFull,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ChannelDetail 수정"""
    try:
        if not detail_repo.exists(detail_id):
            raise HTTPException(404, "상세정보를 찾을 수 없습니다")

        if not channel_repo.exists(data.ChannelID):
            raise HTTPException(404, "채널을 찾을 수 없습니다")

        if data.BizNumber and detail_repo.check_duplicate("BizNumber", data.BizNumber, exclude_id=detail_id):
            raise HTTPException(400, f"중복된 사업자번호입니다: {data.BizNumber}")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = detail_repo.update(detail_id, update_data)
        if not success:
            raise HTTPException(500, "상세정보 수정 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="UPDATE",
                target_table="ChannelDetail",
                target_id=str(detail_id),
                details=update_data,
                ip_address=get_client_ip(request)
            )

        return {"message": "수정되었습니다", "ChannelDetailID": detail_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"상세정보 수정 실패: {str(e)}")


@channeldetail_router.delete("/{detail_id}")
async def delete_channeldetail_direct(
    detail_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ChannelDetail 삭제"""
    try:
        success = detail_repo.delete(detail_id)
        if not success:
            raise HTTPException(404, "상세정보를 찾을 수 없습니다")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="DELETE",
                target_table="ChannelDetail",
                target_id=str(detail_id),
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"상세정보 삭제 실패: {str(e)}")


@channeldetail_router.post("/bulk-delete")
async def bulk_delete_channeldetails(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ChannelDetail 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = 0
        for detail_id in request_body.ids:
            if detail_repo.delete(detail_id):
                deleted_count += 1

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="BULK_DELETE",
                target_table="ChannelDetail",
                details={"deleted_ids": request_body.ids, "count": deleted_count},
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")
