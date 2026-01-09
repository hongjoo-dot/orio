"""
인증 API 라우터 - 로그인, 로그아웃, 비밀번호 변경
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from pydantic import BaseModel, EmailStr

from core.security import verify_password, create_access_token, hash_password
from core.dependencies import get_current_user, CurrentUser
from repositories.user_repository import user_repo
from repositories.activity_log_repository import activity_log_repo, ActivityLogRepository

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ========================
# Pydantic Models
# ========================

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class UserInfo(BaseModel):
    user_id: int
    email: str
    name: str
    role: str


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
# API Endpoints
# ========================

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, request: Request, response: Response):
    """
    로그인 - JWT 토큰 발급
    """
    ip_address = get_client_ip(request)
    
    # 사용자 조회
    user = user_repo.get_by_email(data.email)
    
    if not user:
        # 로그인 실패 기록 (사용자 없음 - UserID=0으로 기록)
        try:
            # 로그인 실패용 특수 처리 (UserID가 없으므로 details에 이메일 저장)
            activity_log_repo.log_action(
                user_id=0,  # 시스템 사용자 또는 존재하지 않는 사용자
                action_type=ActivityLogRepository.ACTION_LOGIN_FAILED,
                details={"attempted_email": data.email, "reason": "user_not_found"},
                ip_address=ip_address
            )
        except:
            pass  # 로그 실패해도 진행
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )
    
    # 계정 활성화 확인
    if not user.get("IsActive", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 계정입니다. 관리자에게 문의하세요."
        )
    
    # 비밀번호 검증
    if not verify_password(data.password, user["PasswordHash"]):
        # 로그인 실패 기록
        activity_log_repo.log_action(
            user_id=user["UserID"],
            action_type=ActivityLogRepository.ACTION_LOGIN_FAILED,
            details={"reason": "invalid_password"},
            ip_address=ip_address
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )
    
    # JWT 토큰 생성
    access_token = create_access_token(
        user_id=user["UserID"],
        email=user["Email"],
        role=user["RoleName"]
    )
    
    # 마지막 로그인 시간 업데이트
    user_repo.update_last_login(user["UserID"])
    
    # 로그인 성공 기록
    activity_log_repo.log_action(
        user_id=user["UserID"],
        action_type=ActivityLogRepository.ACTION_LOGIN,
        ip_address=ip_address
    )
    
    # 쿠키에 토큰 저장 (옵션)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=8 * 60 * 60,  # 8시간
        samesite="lax"
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user["UserID"],
            "email": user["Email"],
            "name": user["Name"],
            "role": user["RoleName"]
        }
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    로그아웃 - 쿠키 삭제
    """
    ip_address = get_client_ip(request)
    
    # 로그아웃 기록
    activity_log_repo.log_action(
        user_id=current_user.user_id,
        action_type=ActivityLogRepository.ACTION_LOGOUT,
        ip_address=ip_address
    )
    
    # 쿠키 삭제
    response.delete_cookie(key="access_token")
    
    return {"message": "로그아웃되었습니다"}


@router.get("/me")
async def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회
    """
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role,
        "can_write": current_user.can_write,
        "is_admin": current_user.is_admin
    }


@router.put("/password")
async def change_password(
    data: PasswordChangeRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    비밀번호 변경
    """
    ip_address = get_client_ip(request)
    
    # 현재 사용자 정보 조회
    user = user_repo.get_by_email(current_user.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 현재 비밀번호 확인
    if not verify_password(data.current_password, user["PasswordHash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다"
        )
    
    # 새 비밀번호 해시
    new_hash = hash_password(data.new_password)
    
    # 비밀번호 업데이트
    success = user_repo.change_password(current_user.user_id, new_hash)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비밀번호 변경 실패"
        )
    
    # 비밀번호 변경 기록
    activity_log_repo.log_action(
        user_id=current_user.user_id,
        action_type=ActivityLogRepository.ACTION_PASSWORD_CHANGE,
        ip_address=ip_address
    )
    
    return {"message": "비밀번호가 변경되었습니다"}
