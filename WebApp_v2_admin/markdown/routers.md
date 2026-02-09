# Routers (`routers/`)

FastAPI API 엔드포인트 계층. 각 Router는 대응하는 Repository를 사용하여 데이터를 처리한다.

## 전체 Router 목록

| Router | prefix | 태그 | Repository | 서브라우터 |
|--------|--------|------|-----------|-----------|
| `pages.py` | `/` | Pages | - | - (HTML 라우팅) |
| `auth.py` | `/api/auth` | Auth | UserRepository | - |
| `admin.py` | `/api/admin` | Admin | User, Permission Repo | - |
| `product.py` | `/api/products` | Product | Product, ProductBox Repo | `productbox_router` |
| `bom.py` | `/api/bom` | BOM | BOMRepository | - |
| `brand.py` | `/api/brands` | Brand | BrandRepository | - |
| `channel.py` | `/api/channels` | Channel | ChannelRepository | `channeldetail_router` |
| `sales.py` | `/api/sales` | Sales | SalesRepository | - |
| `target.py` | `/api/targets` | Target | TargetBase, TargetPromotion Repo | - |
| `promotion.py` | `/api/promotions` | Promotion | Promotion, PromotionProduct Repo | `product_router` |
| `withdrawal_plan.py` | `/api/withdrawal-plans` | WithdrawalPlan | WithdrawalPlanRepository | - |
| `utility.py` | `/api/utility` | Utility | 다수 | - |
| `system_config.py` | `/api/system-config` | SystemConfig | SystemConfigRepository | - |

## 표준 엔드포인트 패턴

모든 엔티티 Router는 아래 패턴을 따른다:

| 동작 | 메서드 | 경로 | 권한 | 로깅 |
|------|--------|------|------|------|
| 목록 조회 | GET | `""` | READ | - |
| 단건 조회 | GET | `"/{id}"` | READ | - |
| 메타데이터 | GET | `"/metadata"` | READ | - |
| 생성 | POST | `""` | CREATE | `@log_activity` |
| 수정 | PUT | `"/{id}"` | UPDATE | `@log_activity` |
| 삭제 | DELETE | `"/{id}"` | DELETE | `@log_delete` |
| 일괄 삭제 | POST | `"/bulk-delete"` | DELETE | `@log_bulk_delete` |
| 엑셀 다운로드 | GET | `"/download/excel"` | EXPORT | - |
| 엑셀 업로드 | POST | `"/upload/excel"` | IMPORT | - |

## Router 작성 템플릿

```python
from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from repositories.new_entity_repository import NewEntityRepository
from core.dependencies import require_permission, CurrentUser
from core import log_activity, log_delete, log_bulk_delete

router = APIRouter(prefix="/api/new-entities", tags=["NewEntity"])
new_entity_repo = NewEntityRepository()

# 허용 정렬 컬럼 (SQL Injection 방지)
ALLOWED_SORT = {
    "EntityID": "t.EntityID",
    "Name": "t.Name",
}

# --- Pydantic 모델 ---
class EntityCreate(BaseModel):
    Name: str
    Status: Optional[str] = "ACTIVE"

class EntityUpdate(BaseModel):
    Name: Optional[str] = None
    Status: Optional[str] = None

class BulkDeleteRequest(BaseModel):
    ids: List[int]

# --- GET 목록 ---
@router.get("")
async def get_entities(
    page: int = 1, limit: int = 20,
    sort_by: Optional[str] = None, sort_dir: Optional[str] = "DESC",
    name: Optional[str] = None, status: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Entity", "READ"))
):
    filters = {}
    if name: filters['name'] = name
    if status: filters['status'] = status
    order_by = ALLOWED_SORT.get(sort_by, "t.EntityID")
    order_dir = sort_dir if sort_dir in ("ASC", "DESC") else "DESC"
    return new_entity_repo.get_list(page, limit, filters, order_by, order_dir)

# --- GET 단건 ---
@router.get("/{entity_id}")
async def get_entity(
    entity_id: int,
    user: CurrentUser = Depends(require_permission("Entity", "READ"))
):
    result = new_entity_repo.get_by_id(entity_id)
    if not result:
        raise HTTPException(404, "데이터를 찾을 수 없습니다")
    return result

# --- POST 생성 ---
@router.post("")
@log_activity("CREATE", "Entity", id_key="EntityID")
async def create_entity(
    data: EntityCreate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Entity", "CREATE"))
):
    entity_id = new_entity_repo.create(data.dict(exclude_none=True))
    return {"EntityID": entity_id, "message": "생성되었습니다"}

# --- PUT 수정 ---
@router.put("/{entity_id}")
@log_activity("UPDATE", "Entity", id_key="EntityID")
async def update_entity(
    entity_id: int, data: EntityUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Entity", "UPDATE"))
):
    update_data = data.dict(exclude_none=True)
    if not update_data:
        raise HTTPException(400, "수정할 데이터가 없습니다")
    success = new_entity_repo.update(entity_id, update_data)
    if not success:
        raise HTTPException(404, "데이터를 찾을 수 없습니다")
    return {"EntityID": entity_id, "message": "수정되었습니다"}

# --- DELETE 삭제 ---
@router.delete("/{entity_id}")
@log_delete("Entity", id_param="entity_id")
async def delete_entity(
    entity_id: int,
    request: Request,
    user: CurrentUser = Depends(require_permission("Entity", "DELETE"))
):
    success = new_entity_repo.delete(entity_id)
    if not success:
        raise HTTPException(404, "데이터를 찾을 수 없습니다")
    return {"message": "삭제되었습니다"}

# --- POST 일괄 삭제 ---
@router.post("/bulk-delete")
@log_bulk_delete("Entity")
async def bulk_delete(
    body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Entity", "DELETE"))
):
    deleted_count = new_entity_repo.bulk_delete(body.ids)
    return {"message": "삭제되었습니다", "deleted_count": deleted_count, "deleted_ids": body.ids}
```

## 서브라우터 패턴

마스터-디테일 관계에서 하위 엔티티용 서브라우터를 분리:

```python
# product.py 내부
router = APIRouter(prefix="/api/products", tags=["Product"])
productbox_router = APIRouter(prefix="/api/products/{product_id}/boxes", tags=["ProductBox"])

# app.py에서 둘 다 등록
app.include_router(product.router)
app.include_router(product.productbox_router)
```

## 에러 처리 패턴

```python
try:
    # 로직
except HTTPException:
    raise                                    # HTTP 에러는 그대로 전달
except ValueError as e:
    raise HTTPException(404, str(e))
except Exception as e:
    raise HTTPException(500, f"작업 실패: {str(e)}")
```

## API 응답 형식

```json
// 목록 조회 (GET)
{"data": [...], "total": 150, "page": 1, "limit": 20, "total_pages": 8}

// 생성 (POST) - id_key 포함 필수
{"EntityID": 1, "message": "생성되었습니다"}

// 수정 (PUT)
{"EntityID": 1, "message": "수정되었습니다"}

// 삭제 (DELETE)
{"message": "삭제되었습니다"}

// 일괄 삭제 - deleted_ids 필수
{"message": "삭제되었습니다", "deleted_count": 3, "deleted_ids": [1, 2, 3]}
```

## app.py 라우터 등록

```python
from routers import new_entity
app.include_router(new_entity.router)
# 서브라우터가 있는 경우:
app.include_router(new_entity.detail_router)
```

## pages.py (HTML 페이지 라우팅)

```python
@router.get("/entities", response_class=HTMLResponse)
async def entities_page(request: Request, redirect=Depends(require_login_for_page)):
    if redirect:
        return redirect
    return templates.TemplateResponse("entities.html", {
        "request": request,
        "active_page": "entities"    # 사이드바 활성화 키
    })
```
