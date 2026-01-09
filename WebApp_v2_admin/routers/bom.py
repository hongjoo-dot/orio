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
from repositories import BOMRepository, ActivityLogRepository
from core.dependencies import get_current_user, get_client_ip, CurrentUser

router = APIRouter(prefix="/api/bom", tags=["BOM"])

# Repository 인스턴스
bom_repo = BOMRepository()
activity_log_repo = ActivityLogRepository()


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
    child_name: Optional[str] = None
):
    """부모 제품 목록 조회 (세트 제품)"""
    try:
        result = bom_repo.get_parents(
            page=page,
            limit=limit,
            parent_erp=parent_erp,
            parent_name=parent_name,
            child_erp=child_erp,
            child_name=child_name
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"부모 제품 조회 실패: {str(e)}")


@router.get("/children/{parent_box_id}")
async def get_bom_children(parent_box_id: int):
    """특정 부모 제품의 구성품 목록 조회"""
    try:
        children = bom_repo.get_children(parent_box_id)
        return {"data": children, "total": len(children)}
    except Exception as e:
        raise HTTPException(500, f"구성품 조회 실패: {str(e)}")


@router.get("/metadata")
async def get_bom_metadata():
    """BOM 메타데이터 조회 (필터용)"""
    try:
        metadata = bom_repo.get_metadata()
        return metadata
    except Exception as e:
        raise HTTPException(500, f"메타데이터 조회 실패: {str(e)}")


@router.get("/{bom_id}")
async def get_bom(bom_id: int):
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
async def create_bom(
    data: BOMCreateByERP,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """BOM 생성 (ERPCode로 생성)"""
    try:
        bom_id = bom_repo.create_by_erp_code(
            parent_erp=data.ParentERPCode,
            child_erp=data.ChildERPCode,
            quantity=data.QuantityRequired
        )

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="ProductBOM",
                target_id=str(bom_id),
                details={"ParentERPCode": data.ParentERPCode, "ChildERPCode": data.ChildERPCode},
                ip_address=get_client_ip(request)
            )

        return {"BOMID": bom_id, **data.dict()}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"BOM 생성 실패: {str(e)}")


@router.post("/by-boxid")
async def create_bom_by_boxid(
    data: BOMCreate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """BOM 생성 (BoxID 직접 지정)"""
    try:
        bom_id = bom_repo.create(data.dict(exclude_none=True))

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="ProductBOM",
                target_id=str(bom_id),
                details={"ParentBoxID": data.ParentProductBoxID, "ChildBoxID": data.ChildProductBoxID},
                ip_address=get_client_ip(request)
            )

        return {"BOMID": bom_id, **data.dict()}
    except Exception as e:
        raise HTTPException(500, f"BOM 생성 실패: {str(e)}")


# ========== BOM 수정/삭제 엔드포인트 ==========

@router.put("/{bom_id}")
async def update_bom(
    bom_id: int,
    data: BOMUpdate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
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

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="UPDATE",
                target_table="ProductBOM",
                target_id=str(bom_id),
                details=update_data,
                ip_address=get_client_ip(request)
            )

        return {"message": "수정되었습니다", "BOMID": bom_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"BOM 수정 실패: {str(e)}")


@router.delete("/{bom_id}")
async def delete_bom(
    bom_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """BOM 삭제"""
    try:
        if not bom_repo.exists(bom_id):
            raise HTTPException(404, "BOM을 찾을 수 없습니다")

        success = bom_repo.delete(bom_id)
        if not success:
            raise HTTPException(500, "BOM 삭제 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="DELETE",
                target_table="ProductBOM",
                target_id=str(bom_id),
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"BOM 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
async def bulk_delete_bom(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """BOM 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = bom_repo.bulk_delete(request_body.ids)

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="BULK_DELETE",
                target_table="ProductBOM",
                details={"deleted_ids": request_body.ids, "count": deleted_count},
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")
