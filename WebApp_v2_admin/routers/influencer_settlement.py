"""
인플루언서 광고비 정산 Router
- 검색어별 > UTM Content별 집계
- UTM Content별 상품 내역
"""

from fastapi import APIRouter, Query, Depends
from core.dependencies import require_permission

router = APIRouter(
    prefix="/api/influencer-settlement",
    tags=["InfluencerSettlement"]
)

from repositories.influencer_settlement_repository import InfluencerSettlementRepository
repo = InfluencerSettlementRepository()


@router.get("/summary")
async def get_summary(
    start_date: str = Query(..., description="시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료일 (YYYY-MM-DD)"),
    influencers: str = Query(..., description="인플루언서 이름 (쉼표 구분)"),
    user = Depends(require_permission("InfluencerSettlement", "READ"))
):
    """검색어별 > UTM Content별 주문 수/매출 집계"""
    influencer_list = [name.strip() for name in influencers.split(",") if name.strip()]

    if not influencer_list:
        return {"data": []}

    data = repo.get_summary(start_date, end_date, influencer_list)
    return {"data": data}


@router.get("/influencer-items")
async def get_influencer_items(
    start_date: str = Query(...),
    end_date: str = Query(...),
    influencer: str = Query(..., description="검색어 (LIKE 검색)"),
    user = Depends(require_permission("InfluencerSettlement", "READ"))
):
    """검색어(인플루언서) 전체의 상품별 합산 집계"""
    data = repo.get_influencer_items(start_date, end_date, influencer.strip())
    return {"data": data}


@router.get("/content-items")
async def get_content_items(
    start_date: str = Query(...),
    end_date: str = Query(...),
    content: str = Query(..., description="UTM Content 값 (정확 일치)"),
    user = Depends(require_permission("InfluencerSettlement", "READ"))
):
    """특정 UTM Content의 상품별 집계"""
    data = repo.get_content_items(start_date, end_date, content)
    return {"data": data}
