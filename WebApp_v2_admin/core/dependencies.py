"""
FastAPI 의존성 주입 모듈 - 인증 및 권한 체크
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse

from .security import decode_token
from .database import get_db_cursor

# HTTP Bearer 토큰 스키마 (옵션: 로그인 안 한 경우도 허용)
security = HTTPBearer(auto_error=False)


class CurrentUser:
    """현재 로그인한 사용자 정보"""
    def __init__(
        self,
        user_id: int,
        email: str,
        role: str
    ):
        self.user_id = user_id
        self.email = email
        self.role = role
    
    @property
    def is_admin(self) -> bool:
        return self.role == "Admin"
    
    @property
    def is_manager(self) -> bool:
        return self.role in ["Admin", "Manager"]
    
    @property
    def is_viewer(self) -> bool:
        return self.role == "Viewer"
    
    @property
    def can_write(self) -> bool:
        """생성/수정/삭제 권한"""
        return self.role in ["Admin", "Manager"]


def get_client_ip(request: Request) -> Optional[str]:
    """
    클라이언트 IP 주소 추출
    X-Forwarded-For 헤더 우선 확인 (프록시 환경)
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    if request.client:
        return request.client.host
    
    return None


def get_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    access_token: Optional[str] = Cookie(default=None)
) -> Optional[str]:
    """
    요청에서 JWT 토큰 추출
    우선순위: Authorization Header > Cookie
    """
    # 1. Authorization Header 확인
    if credentials and credentials.credentials:
        return credentials.credentials
    
    # 2. Cookie 확인
    if access_token:
        return access_token
    
    return None


async def get_current_user_optional(
    token: Optional[str] = Depends(get_token_from_request)
) -> Optional[CurrentUser]:
    """
    현재 사용자 조회 (옵션 - 로그인 안 해도 됨)
    
    Returns:
        CurrentUser | None
    """
    if not token:
        return None
    
    payload = decode_token(token)
    if not payload:
        return None
    
    return CurrentUser(
        user_id=payload["user_id"],
        email=payload["email"],
        role=payload["role"]
    )


async def get_current_user(
    user: Optional[CurrentUser] = Depends(get_current_user_optional)
) -> CurrentUser:
    """
    현재 사용자 조회 (필수 - 로그인 필요)
    
    Raises:
        HTTPException: 인증되지 않은 경우
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def require_admin(
    user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Admin 권한 체크
    
    Raises:
        HTTPException: Admin이 아닌 경우
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return user


async def require_write_permission(
    user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    쓰기 권한 체크 (Admin 또는 Manager)
    
    Raises:
        HTTPException: 쓰기 권한이 없는 경우
    """
    if not user.can_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="쓰기 권한이 없습니다. Viewer는 조회만 가능합니다."
        )
    return user


def require_roles(allowed_roles: List[str]):
    """
    특정 역할 요구 (데코레이터 팩토리)

    Args:
        allowed_roles: 허용된 역할 목록

    Example:
        @router.post("/")
        async def create_item(user: CurrentUser = Depends(require_roles(["Admin", "Manager"]))):
            ...
    """
    async def role_checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"권한이 없습니다. 필요한 역할: {', '.join(allowed_roles)}"
            )
        return user

    return role_checker


async def require_login_for_page(
    token: Optional[str] = Depends(get_token_from_request)
):
    """
    페이지 라우터용 인증 체크 (로그인 안 된 경우 로그인 페이지로 리다이렉트)

    Usage:
        @router.get("/dashboard")
        async def dashboard(redirect = Depends(require_login_for_page)):
            if redirect:
                return redirect
            ...
    """
    if not token:
        return RedirectResponse(url="/login", status_code=302)

    payload = decode_token(token)
    if not payload:
        return RedirectResponse(url="/login", status_code=302)

    return None


def _get_role_id(role_name: str) -> Optional[int]:
    """역할 이름으로 역할 ID 조회"""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT RoleID FROM [dbo].[Role] WHERE Name = ?", role_name)
        row = cursor.fetchone()
        return row[0] if row else None


def _check_effective_permission(user_id: int, role_id: int, module: str, action: str) -> bool:
    """
    사용자 최종 권한 확인
    = 역할 권한 + 개별 GRANT - 개별 DENY
    """
    with get_db_cursor(commit=False) as cursor:
        # 권한 ID 조회
        cursor.execute(
            "SELECT PermissionID FROM [dbo].[Permission] WHERE Module = ? AND Action = ?",
            module, action
        )
        row = cursor.fetchone()
        if not row:
            return False
        perm_id = row[0]

        # 개별 DENY 확인 (우선순위 최상)
        cursor.execute(
            "SELECT COUNT(*) FROM [dbo].[UserPermission] WHERE UserID = ? AND PermissionID = ? AND Type = 'DENY'",
            user_id, perm_id
        )
        if cursor.fetchone()[0] > 0:
            return False

        # 개별 GRANT 확인
        cursor.execute(
            "SELECT COUNT(*) FROM [dbo].[UserPermission] WHERE UserID = ? AND PermissionID = ? AND Type = 'GRANT'",
            user_id, perm_id
        )
        if cursor.fetchone()[0] > 0:
            return True

        # 역할 권한 확인
        cursor.execute(
            "SELECT COUNT(*) FROM [dbo].[RolePermission] WHERE RoleID = ? AND PermissionID = ?",
            role_id, perm_id
        )
        return cursor.fetchone()[0] > 0


def require_permission(module: str, action: str):
    """
    특정 권한 요구 (의존성 팩토리)

    Args:
        module: 모듈명 (Product, Channel, Sales 등)
        action: 액션 (CREATE, READ, UPDATE, DELETE 등)

    Example:
        @router.post("/")
        async def create_product(user: CurrentUser = Depends(require_permission("Product", "CREATE"))):
            ...
    """
    async def permission_checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        # 역할 ID 조회
        role_id = _get_role_id(user.role)
        if role_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="유효하지 않은 역할입니다"
            )

        # 권한 체크
        if not _check_effective_permission(user.user_id, role_id, module, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"권한이 없습니다: {module}:{action}"
            )

        return user

    return permission_checker
