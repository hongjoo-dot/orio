"""
사방넷 재고 조회 Router
- DB 스냅샷 기반 재고 조회 (조회 전용)
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from core.dependencies import require_permission
from repositories.sabangnet_inventory_repository import SabangnetInventoryRepository

router = APIRouter(prefix="/api/sabangnet/inventory", tags=["Sabangnet Inventory"])

repo = SabangnetInventoryRepository()


@router.get("")
async def get_inventory_snapshots(
    snapshot_date: str = Query(..., description="조회 날짜 (YYYY-MM-DD)"),
    snapshot_time: Optional[str] = Query(None, description="AM 또는 PM"),
    brand_id: Optional[int] = None,
    search: Optional[str] = None,
    user=Depends(require_permission("SabangnetInventory", "READ"))
):
    """재고 스냅샷 조회"""
    data = repo.get_snapshots(
        snapshot_date=snapshot_date,
        snapshot_time=snapshot_time,
        brand_id=brand_id,
        search=search
    )
    return {"data": data, "total": len(data)}


@router.get("/metadata")
async def get_inventory_metadata(
    user=Depends(require_permission("SabangnetInventory", "READ"))
):
    """필터 메타데이터 (날짜, 시간대, 브랜드)"""
    return repo.get_metadata()


@router.get("/locations")
async def get_location_snapshots(
    snapshot_date: str = Query(...),
    snapshot_time: str = Query(...),
    shipping_product_id: str = Query(...),
    user=Depends(require_permission("SabangnetInventory", "READ"))
):
    """특정 상품의 로케이션별 재고"""
    data = repo.get_locations(snapshot_date, snapshot_time, shipping_product_id)
    return {"data": data, "total": len(data)}
