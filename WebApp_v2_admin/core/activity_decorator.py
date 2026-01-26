"""
활동 로그 데코레이터 - CRUD 작업 자동 로깅
"""

from functools import wraps
from typing import Optional, List, Callable
from fastapi import Request

from repositories.activity_log_repository import activity_log_repo, ActivityLogRepository
from core.dependencies import get_client_ip, CurrentUser


def log_activity(
    action: str,
    table: str,
    id_key: Optional[str] = None,
    exclude_keys: Optional[List[str]] = None
):
    """
    CRUD 작업 활동 로그 자동 기록 데코레이터

    Args:
        action: 액션 타입 (CREATE, UPDATE, DELETE, BULK_DELETE)
        table: 대상 테이블명
        id_key: 반환값에서 ID를 추출할 키 (예: "BrandID", "IDX")
        exclude_keys: details에서 제외할 키 목록 (기본: ["message"])

    사용 예시:
        @router.post("")
        @log_activity("CREATE", "Brand", id_key="BrandID")
        async def create_brand(data: BrandCreate, request: Request, user: CurrentUser = Depends(get_current_user)):
            brand_id = brand_repo.create(data.dict())
            return {"BrandID": brand_id, "Name": data.Name}

    주의사항:
        - 함수에 request: Request 파라미터 필요
        - 함수에 user: CurrentUser 파라미터 필요 (Depends(get_current_user))
        - 반환값은 dict 형태여야 함
    """

    if exclude_keys is None:
        exclude_keys = ["message"]

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 함수 실행
            result = await func(*args, **kwargs)

            # request, user 추출 (admin 파라미터도 지원)
            request: Request = kwargs.get("request")
            user: CurrentUser = kwargs.get("user") or kwargs.get("current_user") or kwargs.get("admin")

            # user가 없으면 로깅 스킵
            if not user:
                return result

            # IP 주소 추출
            ip_address = get_client_ip(request) if request else None

            # target_id 추출
            target_id = None
            if id_key and isinstance(result, dict):
                target_id = result.get(id_key)

            # details 추출 (반환값에서 제외 키 제거)
            details = None
            if isinstance(result, dict):
                details = {
                    k: v for k, v in result.items()
                    if k not in exclude_keys and k != id_key
                }
                # 빈 dict면 None으로
                if not details:
                    details = None

            # 활동 로그 기록
            try:
                activity_log_repo.log_action(
                    user_id=user.user_id,
                    action_type=action,
                    target_table=table,
                    target_id=str(target_id) if target_id else None,
                    details=details,
                    ip_address=ip_address
                )
            except Exception:
                # 로깅 실패해도 원래 작업은 성공으로 처리
                pass

            return result

        return wrapper
    return decorator


def log_delete(table: str, id_param: str = None):
    """
    DELETE 작업 전용 데코레이터
    - URL 경로에서 ID를 추출

    Args:
        table: 대상 테이블명
        id_param: 경로 파라미터명 (예: "brand_id", "idx")

    사용 예시:
        @router.delete("/{brand_id}")
        @log_delete("Brand", id_param="brand_id")
        async def delete_brand(brand_id: int, request: Request, user: CurrentUser = Depends(get_current_user)):
            brand_repo.delete(brand_id)
            return {"message": "삭제되었습니다"}
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 삭제 전에 ID 추출
            target_id = kwargs.get(id_param) if id_param else None

            # 함수 실행
            result = await func(*args, **kwargs)

            # request, user 추출 (admin 파라미터도 지원)
            request: Request = kwargs.get("request")
            user: CurrentUser = kwargs.get("user") or kwargs.get("current_user") or kwargs.get("admin")

            if not user:
                return result

            ip_address = get_client_ip(request) if request else None

            # 활동 로그 기록
            try:
                activity_log_repo.log_action(
                    user_id=user.user_id,
                    action_type=ActivityLogRepository.ACTION_DELETE,
                    target_table=table,
                    target_id=str(target_id) if target_id else None,
                    ip_address=ip_address
                )
            except Exception:
                pass

            return result

        return wrapper
    return decorator


def log_bulk_delete(table: str):
    """
    BULK_DELETE 작업 전용 데코레이터
    - 반환값에서 deleted_ids 또는 ids 추출

    사용 예시:
        @router.post("/bulk-delete")
        @log_bulk_delete("ERPSales")
        async def bulk_delete_sales(request_body: BulkDeleteRequest, request: Request, user: CurrentUser = Depends(get_current_user)):
            deleted_count = sales_repo.bulk_delete(request_body.ids)
            return {"message": "삭제되었습니다", "deleted_count": deleted_count, "deleted_ids": request_body.ids}
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # request_body에서 ids 추출 (함수 실행 전)
            request_body = kwargs.get("request_body")
            ids = getattr(request_body, "ids", None) if request_body else None

            # 함수 실행
            result = await func(*args, **kwargs)

            # request, user 추출 (admin 파라미터도 지원)
            request: Request = kwargs.get("request")
            user: CurrentUser = kwargs.get("user") or kwargs.get("current_user") or kwargs.get("admin")

            if not user:
                return result

            ip_address = get_client_ip(request) if request else None

            # details 구성
            details = {}
            if ids:
                details["deleted_ids"] = ids
                details["count"] = len(ids) if isinstance(ids, list) else None
            if isinstance(result, dict) and "deleted_count" in result:
                details["count"] = result["deleted_count"]

            # 활동 로그 기록
            try:
                activity_log_repo.log_action(
                    user_id=user.user_id,
                    action_type=ActivityLogRepository.ACTION_BULK_DELETE,
                    target_table=table,
                    details=details if details else None,
                    ip_address=ip_address
                )
            except Exception:
                pass

            return result

        return wrapper
    return decorator
