"""
SystemConfig Router
시스템 설정 관리 API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from repositories.system_config_repository import SystemConfigRepository
from core.dependencies import get_current_user

router = APIRouter(prefix="/api/system-config", tags=["SystemConfig"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ConfigUpdateRequest(BaseModel):
    """설정값 업데이트 요청"""
    config_id: int
    new_value: str


class ConfigToggleRequest(BaseModel):
    """설정 활성화 토글 요청"""
    config_id: int


class ConfigCreateRequest(BaseModel):
    """설정 추가 요청"""
    category: str
    config_key: str
    config_value: str
    data_type: str = "string"
    description: Optional[str] = None
    is_active: bool = True


class ConfigDeleteRequest(BaseModel):
    """설정 삭제 요청"""
    config_id: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/configs")
def get_all_configs(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    모든 시스템 설정 조회

    Args:
        category: 카테고리 필터 (옵션)

    Returns:
        설정 목록
    """
    try:
        repo = SystemConfigRepository()
        configs = repo.get_all_configs(category=category)
        return {"configs": configs, "count": len(configs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
def get_categories(current_user: dict = Depends(get_current_user)):
    """
    모든 카테고리 조회

    Returns:
        카테고리 목록
    """
    try:
        repo = SystemConfigRepository()
        categories = repo.get_categories()
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{config_id}")
def get_config_by_id(
    config_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    ID로 설정 조회

    Args:
        config_id: 설정 ID

    Returns:
        설정 정보
    """
    try:
        repo = SystemConfigRepository()
        config = repo.get_config_by_id(config_id)

        if not config:
            raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다.")

        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{category}/{config_key}")
def get_config_by_key(
    category: str,
    config_key: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Category와 Key로 설정 조회

    Args:
        category: 카테고리
        config_key: 설정 키

    Returns:
        설정 정보
    """
    try:
        repo = SystemConfigRepository()
        config = repo.get_config_by_key(category, config_key)

        if not config:
            raise HTTPException(status_code=404, detail="설정을 찾을 수 없습니다.")

        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
def create_config(
    request: ConfigCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    새 설정 추가

    Args:
        request: 설정 추가 요청

    Returns:
        생성된 설정 ID
    """
    try:
        repo = SystemConfigRepository()
        username = current_user.get('username', 'ADMIN')

        config_id = repo.create_config(
            category=request.category,
            config_key=request.config_key,
            config_value=request.config_value,
            data_type=request.data_type,
            description=request.description,
            is_active=request.is_active,
            created_by=username
        )

        return {"config_id": config_id, "message": "설정이 추가되었습니다."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update")
def update_config_value(
    request: ConfigUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    설정값 업데이트

    Args:
        request: 설정 업데이트 요청

    Returns:
        업데이트 결과
    """
    try:
        repo = SystemConfigRepository()
        username = current_user.get('username', 'ADMIN')

        result = repo.update_config_value(
            config_id=request.config_id,
            new_value=request.new_value,
            updated_by=username
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/toggle")
def toggle_config_status(
    request: ConfigToggleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    설정 활성/비활성 토글

    Args:
        request: 토글 요청

    Returns:
        토글 결과
    """
    try:
        repo = SystemConfigRepository()
        username = current_user.get('username', 'ADMIN')

        result = repo.toggle_config_status(
            config_id=request.config_id,
            updated_by=username
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete")
def delete_config(
    request: ConfigDeleteRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    설정 삭제

    Args:
        request: 삭제 요청

    Returns:
        삭제 결과
    """
    try:
        repo = SystemConfigRepository()
        username = current_user.get('username', 'ADMIN')

        result = repo.delete_config(
            config_id=request.config_id,
            deleted_by=username
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{config_id}")
def get_config_history(
    config_id: int,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    설정 변경 이력 조회

    Args:
        config_id: 설정 ID
        limit: 조회 개수

    Returns:
        변경 이력 목록
    """
    try:
        repo = SystemConfigRepository()
        history = repo.get_config_history(config_id, limit=limit)
        return {"history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
