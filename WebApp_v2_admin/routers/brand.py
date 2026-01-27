"""
Brand Router
- Brand CRUD API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from repositories import BrandRepository
from core.dependencies import get_client_ip, CurrentUser
from core import log_activity, log_delete, require_permission

router = APIRouter(prefix="/api/brands", tags=["Brand"])

# Repository 인스턴스
brand_repo = BrandRepository()


class BrandCreate(BaseModel):
    Name: str
    Title: Optional[str] = None


class BrandUpdate(BaseModel):
    Name: Optional[str] = None
    Title: Optional[str] = None


@router.get("")
async def get_brands(
    page: int = 1,
    limit: int = 50,
    user: CurrentUser = Depends(require_permission("Brand", "READ"))
):
    """Brand 목록 조회"""
    try:
        result = brand_repo.get_list(
            page=page,
            limit=limit,
            order_by="Title",
            order_dir="ASC"
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"브랜드 목록 조회 실패: {str(e)}")


@router.get("/all")
async def get_all_brands(user: CurrentUser = Depends(require_permission("Brand", "READ"))):
    """모든 브랜드 Title 조회 (중복 제거)"""
    try:
        brands = brand_repo.get_all_brands()
        return {"data": brands}
    except Exception as e:
        raise HTTPException(500, f"브랜드 조회 실패: {str(e)}")


@router.get("/{brand_id}")
async def get_brand(brand_id: int, user: CurrentUser = Depends(require_permission("Brand", "READ"))):
    """Brand 단일 조회"""
    try:
        brand = brand_repo.get_by_id(brand_id)
        if not brand:
            raise HTTPException(404, "브랜드를 찾을 수 없습니다")
        return brand
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"브랜드 조회 실패: {str(e)}")


@router.post("")
@log_activity("CREATE", "Brand", id_key="BrandID")
async def create_brand(
    data: BrandCreate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Brand", "CREATE"))
):
    """Brand 생성"""
    try:
        brand_id = brand_repo.create(data.dict(exclude_none=True))
        return {"BrandID": brand_id, "Name": data.Name, "Title": data.Title}
    except Exception as e:
        raise HTTPException(500, f"브랜드 생성 실패: {str(e)}")


@router.put("/{brand_id}")
@log_activity("UPDATE", "Brand", id_key="BrandID")
async def update_brand(
    brand_id: int,
    data: BrandUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Brand", "UPDATE"))
):
    """Brand 수정"""
    try:
        if not brand_repo.exists(brand_id):
            raise HTTPException(404, "브랜드를 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = brand_repo.update(brand_id, update_data)
        if not success:
            raise HTTPException(500, "브랜드 수정 실패")

        return {"BrandID": brand_id, **update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"브랜드 수정 실패: {str(e)}")


@router.delete("/{brand_id}")
@log_delete("Brand", id_param="brand_id")
async def delete_brand(
    brand_id: int,
    request: Request,
    user: CurrentUser = Depends(require_permission("Brand", "DELETE"))
):
    """Brand 삭제"""
    try:
        if not brand_repo.exists(brand_id):
            raise HTTPException(404, "브랜드를 찾을 수 없습니다")

        success = brand_repo.delete(brand_id)
        if not success:
            raise HTTPException(500, "브랜드 삭제 실패")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"브랜드 삭제 실패: {str(e)}")
