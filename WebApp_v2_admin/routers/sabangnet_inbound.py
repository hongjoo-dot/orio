"""
사방넷 입고 조회 Router (조회 전용)
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from core.dependencies import require_permission
from repositories.sabangnet_inbound_repository import SabangnetInboundRepository

router = APIRouter(prefix="/api/sabangnet/inbound", tags=["Sabangnet Inbound"])

repo = SabangnetInboundRepository()


@router.get("/plans")
async def get_receiving_plans(
    plan_date: Optional[str] = None,
    plan_status: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
    user=Depends(require_permission("SabangnetInbound", "READ"))
):
    """입고예정 목록"""
    return repo.get_receiving_plans(plan_date, plan_status, page, limit)


@router.get("/plans/{plan_id}")
async def get_receiving_plan_detail(
    plan_id: int,
    user=Depends(require_permission("SabangnetInbound", "READ"))
):
    """입고예정 상세 + 상품 목록"""
    result = repo.get_receiving_plan_detail(plan_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="입고예정을 찾을 수 없습니다")
    return result


@router.get("/works")
async def get_receiving_works(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    work_type: Optional[int] = None,
    page: int = 1,
    limit: int = 50,
    user=Depends(require_permission("SabangnetInbound", "READ"))
):
    """입고작업내역"""
    return repo.get_receiving_works(start_date, end_date, work_type, page, limit)
