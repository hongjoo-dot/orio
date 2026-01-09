"""
Admin API 라우터 - 사용자 관리, 역할 관리, 활동 로그
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from pydantic import BaseModel, EmailStr

from core.security import hash_password
from core.dependencies import get_current_user, require_admin, CurrentUser
from repositories.user_repository import user_repo, role_repo
from repositories.activity_log_repository import activity_log_repo, ActivityLogRepository

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ========================
# Pydantic Models
# ========================

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    role_id: int
    is_active: bool = True


class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None


class RoleAssign(BaseModel):
    role_id: int


class PasswordReset(BaseModel):
    new_password: str


# ========================
# Helper Functions
# ========================

def get_client_ip(request: Request) -> str:
    """클라이언트 IP 주소 추출"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ========================
# User Management APIs
# ========================

@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    email: Optional[str] = None,
    name: Optional[str] = None,
    role_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    admin: CurrentUser = Depends(require_admin)
):
    """
    사용자 목록 조회 (Admin만)
    """
    filters = {}
    if email:
        filters["Email"] = email
    if name:
        filters["Name"] = name
    if role_id:
        filters["RoleID"] = role_id
    if is_active is not None:
        filters["IsActive"] = is_active
    
    return user_repo.get_all_with_roles(page=page, limit=limit, filters=filters if filters else None)


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    admin: CurrentUser = Depends(require_admin)
):
    """
    사용자 상세 조회 (Admin만)
    """
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 비밀번호 해시 제거
    user.pop("PasswordHash", None)
    return user


@router.post("/users")
async def create_user(
    data: UserCreate,
    request: Request,
    admin: CurrentUser = Depends(require_admin)
):
    """
    사용자 생성 (Admin만)
    """
    ip_address = get_client_ip(request)
    
    # 비밀번호 해시
    password_hash = hash_password(data.password)
    
    try:
        user_id = user_repo.create_with_role(
            user_data={
                "Email": data.email,
                "PasswordHash": password_hash,
                "Name": data.name,
                "IsActive": data.is_active
            },
            role_id=data.role_id,
            created_by=admin.user_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # 활동 로그
    activity_log_repo.log_action(
        user_id=admin.user_id,
        action_type=ActivityLogRepository.ACTION_CREATE,
        target_table="User",
        target_id=str(user_id),
        details={"email": data.email, "name": data.name, "role_id": data.role_id},
        ip_address=ip_address
    )
    
    return {"UserID": user_id, "Email": data.email, "Name": data.name}


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request,
    admin: CurrentUser = Depends(require_admin)
):
    """
    사용자 정보 수정 (Admin만)
    """
    ip_address = get_client_ip(request)
    
    # 사용자 존재 확인
    if not user_repo.exists(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 수정할 데이터 구성
    update_data = {}
    if data.email is not None:
        update_data["Email"] = data.email
    if data.name is not None:
        update_data["Name"] = data.name
    if data.is_active is not None:
        update_data["IsActive"] = data.is_active
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 데이터가 없습니다"
        )
    
    success = user_repo.update(user_id, update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 수정 실패"
        )
    
    # 활동 로그
    activity_log_repo.log_action(
        user_id=admin.user_id,
        action_type=ActivityLogRepository.ACTION_UPDATE,
        target_table="User",
        target_id=str(user_id),
        details=update_data,
        ip_address=ip_address
    )
    
    return {"message": "사용자 정보가 수정되었습니다", "UserID": user_id}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    admin: CurrentUser = Depends(require_admin)
):
    """
    사용자 삭제 (Admin만)
    """
    ip_address = get_client_ip(request)
    
    # 자기 자신 삭제 방지
    if user_id == admin.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신은 삭제할 수 없습니다"
        )
    
    # 사용자 존재 확인
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    success = user_repo.delete(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 삭제 실패"
        )
    
    # 활동 로그
    activity_log_repo.log_action(
        user_id=admin.user_id,
        action_type=ActivityLogRepository.ACTION_DELETE,
        target_table="User",
        target_id=str(user_id),
        details={"deleted_email": user.get("Email")},
        ip_address=ip_address
    )
    
    return {"message": "사용자가 삭제되었습니다"}


@router.post("/users/{user_id}/role")
async def assign_role(
    user_id: int,
    data: RoleAssign,
    request: Request,
    admin: CurrentUser = Depends(require_admin)
):
    """
    역할 할당/변경 (Admin만)
    """
    ip_address = get_client_ip(request)
    
    # 사용자 존재 확인
    if not user_repo.exists(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 역할 존재 확인
    role = role_repo.get_by_id(data.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="존재하지 않는 역할입니다"
        )
    
    success = user_repo.update_role(user_id, data.role_id, admin.user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="역할 할당 실패"
        )
    
    # 활동 로그
    activity_log_repo.log_action(
        user_id=admin.user_id,
        action_type=ActivityLogRepository.ACTION_ROLE_CHANGE,
        target_table="UserRole",
        target_id=str(user_id),
        details={"new_role_id": data.role_id, "new_role_name": role["Name"]},
        ip_address=ip_address
    )
    
    return {"message": f"역할이 '{role['Name']}'로 변경되었습니다"}


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    data: PasswordReset,
    request: Request,
    admin: CurrentUser = Depends(require_admin)
):
    """
    비밀번호 초기화 (Admin만)
    """
    ip_address = get_client_ip(request)
    
    # 사용자 존재 확인
    if not user_repo.exists(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 새 비밀번호 해시
    new_hash = hash_password(data.new_password)
    
    success = user_repo.change_password(user_id, new_hash)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비밀번호 초기화 실패"
        )
    
    # 활동 로그
    activity_log_repo.log_action(
        user_id=admin.user_id,
        action_type=ActivityLogRepository.ACTION_PASSWORD_CHANGE,
        target_table="User",
        target_id=str(user_id),
        details={"action": "admin_reset"},
        ip_address=ip_address
    )
    
    return {"message": "비밀번호가 초기화되었습니다"}


# ========================
# Role APIs
# ========================

@router.get("/roles")
async def get_roles(admin: CurrentUser = Depends(require_admin)):
    """
    역할 목록 조회 (Admin만)
    """
    return role_repo.get_all()


# ========================
# Activity Log APIs
# ========================

@router.get("/activity-log")
async def get_activity_log(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    target_table: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    admin: CurrentUser = Depends(require_admin)
):
    """
    활동 이력 조회 (Admin만)
    """
    filters = {}
    if user_id:
        filters["user_id"] = user_id
    if action_type:
        filters["action_type"] = action_type
    if target_table:
        filters["target_table"] = target_table
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    
    return activity_log_repo.get_logs_with_user(
        page=page, 
        limit=limit, 
        filters=filters if filters else None
    )


@router.get("/activity-log/metadata")
async def get_activity_log_metadata(admin: CurrentUser = Depends(require_admin)):
    """
    활동 로그 필터용 메타데이터 (행동 유형, 테이블 목록)
    """
    return {
        "action_types": activity_log_repo.get_action_types(),
        "target_tables": activity_log_repo.get_target_tables()
    }


@router.get("/activity-log/user/{user_id}/summary")
async def get_user_activity_summary(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    admin: CurrentUser = Depends(require_admin)
):
    """
    사용자 활동 요약 (Admin만)
    """
    return activity_log_repo.get_user_activity_summary(user_id, days)
