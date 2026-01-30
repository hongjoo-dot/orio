"""
BOM (ProductBOM) Router
- ProductBOM CRUD API 엔드포인트
- 부모-자식 제품 관계 관리
- Repository 패턴 활용
- 활동 로그 기록
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, List
from repositories import BOMRepository
from core.dependencies import get_client_ip, CurrentUser
from core import log_activity, log_delete, log_bulk_delete, require_permission

router = APIRouter(prefix="/api/bom", tags=["BOM"])

# Repository 인스턴스
bom_repo = BOMRepository()


# Pydantic Models
class BOMCreate(BaseModel):
    ParentProductBoxID: int
    ChildProductBoxID: int
    QuantityRequired: Optional[float] = 1.0


class BOMCreateByERP(BaseModel):
    """ERPCode로 BOM 생성"""
    ParentERPCode: str
    ChildERPCode: str
    QuantityRequired: Optional[float] = 1.0


class BOMUpdate(BaseModel):
    ParentProductBoxID: Optional[int] = None
    ChildProductBoxID: Optional[int] = None
    QuantityRequired: Optional[float] = None


class BulkDeleteRequest(BaseModel):
    ids: List[int]


# ========== BOM 조회 엔드포인트 ==========

@router.get("/parents")
async def get_bom_parents(
    page: int = 1,
    limit: int = 20,
    parent_erp: Optional[str] = None,
    parent_name: Optional[str] = None,
    child_erp: Optional[str] = None,
    child_name: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "DESC",
    user: CurrentUser = Depends(require_permission("BOM", "READ"))
):
    """부모 제품 목록 조회 (세트 제품)"""
    try:
        ALLOWED_SORT = {
            "BoxID": "pb.BoxID",
            "ERPCode": "pb.ERPCode",
            "Name": "p.Name",
            "ChildCount": "ChildCount",
        }
        order_by = ALLOWED_SORT.get(sort_by, "pb.BoxID")
        order_dir = sort_dir if sort_dir in ("ASC", "DESC") else "DESC"

        result = bom_repo.get_parents(
            page=page,
            limit=limit,
            parent_erp=parent_erp,
            parent_name=parent_name,
            child_erp=child_erp,
            child_name=child_name,
            order_by=order_by,
            order_dir=order_dir
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"부모 제품 조회 실패: {str(e)}")


@router.get("/children/{parent_box_id}")
async def get_bom_children(parent_box_id: int, user: CurrentUser = Depends(require_permission("BOM", "READ"))):
    """특정 부모 제품의 구성품 목록 조회"""
    try:
        children = bom_repo.get_children(parent_box_id)
        return {"data": children, "total": len(children)}
    except Exception as e:
        raise HTTPException(500, f"구성품 조회 실패: {str(e)}")


@router.get("/metadata")
async def get_bom_metadata(user: CurrentUser = Depends(require_permission("BOM", "READ"))):
    """BOM 메타데이터 조회 (필터용)"""
    try:
        metadata = bom_repo.get_metadata()
        return metadata
    except Exception as e:
        raise HTTPException(500, f"메타데이터 조회 실패: {str(e)}")


@router.get("/{bom_id}")
async def get_bom(bom_id: int, user: CurrentUser = Depends(require_permission("BOM", "READ"))):
    """BOM 단일 조회"""
    try:
        bom = bom_repo.get_by_id(bom_id)
        if not bom:
            raise HTTPException(404, "BOM을 찾을 수 없습니다")
        return bom
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"BOM 조회 실패: {str(e)}")


# ========== BOM 생성 엔드포인트 ==========

@router.post("")
@log_activity("CREATE", "ProductBOM", id_key="BOMID")
async def create_bom(
    data: BOMCreateByERP,
    request: Request,
    user: CurrentUser = Depends(require_permission("BOM", "CREATE"))
):
    """BOM 생성 (ERPCode로 생성)"""
    try:
        bom_id = bom_repo.create_by_erp_code(
            parent_erp=data.ParentERPCode,
            child_erp=data.ChildERPCode,
            quantity=data.QuantityRequired
        )

        return {"BOMID": bom_id, "ParentERPCode": data.ParentERPCode, "ChildERPCode": data.ChildERPCode}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"BOM 생성 실패: {str(e)}")


@router.post("/by-boxid")
@log_activity("CREATE", "ProductBOM", id_key="BOMID")
async def create_bom_by_boxid(
    data: BOMCreate,
    request: Request,
    user: CurrentUser = Depends(require_permission("BOM", "CREATE"))
):
    """BOM 생성 (BoxID 직접 지정)"""
    try:
        bom_id = bom_repo.create(data.dict(exclude_none=True))

        return {"BOMID": bom_id, "ParentBoxID": data.ParentProductBoxID, "ChildBoxID": data.ChildProductBoxID}
    except Exception as e:
        raise HTTPException(500, f"BOM 생성 실패: {str(e)}")


# ========== BOM 수정/삭제 엔드포인트 ==========

@router.put("/{bom_id}")
@log_activity("UPDATE", "ProductBOM", id_key="BOMID")
async def update_bom(
    bom_id: int,
    data: BOMUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("BOM", "UPDATE"))
):
    """BOM 수정"""
    try:
        if not bom_repo.exists(bom_id):
            raise HTTPException(404, "BOM을 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = bom_repo.update(bom_id, update_data)
        if not success:
            raise HTTPException(500, "BOM 수정 실패")

        return {"BOMID": bom_id, **update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"BOM 수정 실패: {str(e)}")


@router.delete("/{bom_id}")
@log_delete("ProductBOM", id_param="bom_id")
async def delete_bom(
    bom_id: int,
    request: Request,
    user: CurrentUser = Depends(require_permission("BOM", "DELETE"))
):
    """BOM 삭제"""
    try:
        if not bom_repo.exists(bom_id):
            raise HTTPException(404, "BOM을 찾을 수 없습니다")

        success = bom_repo.delete(bom_id)
        if not success:
            raise HTTPException(500, "BOM 삭제 실패")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"BOM 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
@log_bulk_delete("ProductBOM")
async def bulk_delete_bom(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("BOM", "DELETE"))
):
    """BOM 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = bom_repo.bulk_delete(request_body.ids)

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")
