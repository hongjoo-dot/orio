# 개발 지침서 - WebApp_v2_admin

이 문서는 AI가 새로운 섹션(페이지)이나 기능을 추가할 때 **반드시 따라야 하는 규칙**입니다.
코드 작성 전에 이 문서를 읽고, 모든 체크리스트를 충족해야 합니다.

---

## 1. 새 섹션(페이지) 추가 시 체크리스트

새로운 메뉴/페이지를 추가할 때 아래 파일들을 **모두** 생성·수정해야 합니다.

### 필수 생성 파일

| # | 파일 | 설명 |
|---|------|------|
| 1 | `repositories/{entity}_repository.py` | 데이터 접근 계층 |
| 2 | `routers/{entity}.py` | API 엔드포인트 |
| 3 | `templates/{entity}.html` | HTML 템플릿 |
| 4 | `static/js/pages/{entity}.js` | 프론트엔드 로직 |
| 5 | `static/css/pages/{entity}.css` | (필요 시) 페이지 전용 스타일 |
| 6 | `sql/migration_{entity}.sql` | (필요 시) DB 스키마 변경 |

### 필수 수정 파일

| # | 파일 | 작업 |
|---|------|------|
| 1 | `app.py` | `include_router()` 등록 |
| 2 | `routers/pages.py` | HTML 페이지 라우트 추가 |
| 3 | `templates/base.html` | 사이드바 메뉴 항목 추가 |

---

## 2. Backend 규칙

### 2-1. Repository 작성 규칙

`BaseRepository`를 상속하여 작성합니다.

```python
from core.base_repository import BaseRepository
from core.database import get_db_cursor
from typing import Dict, Any, Optional, List

class NewEntityRepository(BaseRepository):
    def __init__(self):
        super().__init__(
            table_name="[dbo].[TableName]",   # 스키마 포함 브라켓 표기
            id_column="TableNameID"             # PK 컬럼명
        )

    def get_select_query(self) -> str:
        """SELECT 쿼리 정의. JOIN 포함 가능."""
        return """
            SELECT t.TableNameID, t.Name, t.Status,
                   r.RefName
            FROM [dbo].[TableName] t
            LEFT JOIN [dbo].[RefTable] r ON t.RefID = r.RefID
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """get_select_query()의 컬럼 순서와 정확히 일치해야 함."""
        return {
            "TableNameID": row[0],
            "Name": row[1],
            "Status": row[2],
            "RefName": row[3],
        }

    def _apply_filters(self, builder, filters: Dict[str, Any]) -> None:
        """필터 조건 정의."""
        if filters.get('name'):
            builder.where_like("t.Name", filters['name'])
        if filters.get('status'):
            builder.where_equals("t.Status", filters['status'])
```

**규칙:**
- `_row_to_dict()`의 인덱스 순서는 `get_select_query()`의 SELECT 컬럼 순서와 **반드시 일치**
- 테이블명은 `[dbo].[TableName]` 브라켓 표기 사용
- JOIN이 필요하면 `_build_query_with_filters()`도 오버라이드
- BaseRepository가 제공하는 메서드: `get_list()`, `get_by_id()`, `create()`, `update()`, `delete()`, `bulk_delete()`, `exists()`, `check_duplicate()`

### 2-2. Router 작성 규칙

```python
from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from repositories.new_entity_repository import NewEntityRepository
from core.dependencies import require_permission
from core import log_activity, log_delete, log_bulk_delete

router = APIRouter(
    prefix="/api/new-entities",    # 복수형, 케밥 표기
    tags=["NewEntity"]             # PascalCase
)

new_entity_repo = NewEntityRepository()
```

**엔드포인트별 필수 패턴:**

| 동작 | 메서드 | 경로 | 권한 | 활동 로깅 |
|------|--------|------|------|-----------|
| 목록 조회 | GET | `""` | READ | 불필요 |
| 단건 조회 | GET | `"/{id}"` | READ | 불필요 |
| 메타데이터 | GET | `"/metadata"` | READ | 불필요 |
| 생성 | POST | `""` | CREATE | **필수** `@log_activity` |
| 수정 | PUT | `"/{id}"` | UPDATE | **필수** `@log_activity` |
| 삭제 | DELETE | `"/{id}"` | DELETE | **필수** `@log_delete` |
| 일괄 삭제 | POST | `"/bulk-delete"` | DELETE | **필수** `@log_bulk_delete` |
| 엑셀 다운로드 | GET | `"/download/excel"` | EXPORT | 불필요 |
| 엑셀 업로드 | POST | `"/upload/excel"` | IMPORT | 불필요 |

### 2-3. 활동 로깅 (Activity Logging) - 필수

**CUD 작업에는 반드시 활동 로깅 데코레이터를 적용합니다.**

```python
# CREATE - @log_activity
@router.post("")
@log_activity("CREATE", "TableName", id_key="TableNameID")
async def create_entity(
    data: EntityCreate,
    request: Request,                                              # 필수
    user: CurrentUser = Depends(require_permission("Entity", "CREATE"))  # 필수
):
    entity_id = new_entity_repo.create(data.dict(exclude_none=True))
    return {"TableNameID": entity_id, "message": "생성되었습니다"}
    #        ↑ id_key와 일치해야 함

# UPDATE - @log_activity
@router.put("/{entity_id}")
@log_activity("UPDATE", "TableName", id_key="TableNameID")
async def update_entity(
    entity_id: int,
    data: EntityUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Entity", "UPDATE"))
):
    update_data = data.dict(exclude_none=True)
    if not update_data:
        raise HTTPException(400, "수정할 데이터가 없습니다")
    success = new_entity_repo.update(entity_id, update_data)
    if not success:
        raise HTTPException(404, "데이터를 찾을 수 없습니다")
    return {"TableNameID": entity_id, "message": "수정되었습니다"}

# DELETE - @log_delete
@router.delete("/{entity_id}")
@log_delete("TableName", id_param="entity_id")
async def delete_entity(
    entity_id: int,
    request: Request,
    user: CurrentUser = Depends(require_permission("Entity", "DELETE"))
):
    success = new_entity_repo.delete(entity_id)
    if not success:
        raise HTTPException(404, "데이터를 찾을 수 없습니다")
    return {"message": "삭제되었습니다"}

# BULK DELETE - @log_bulk_delete
@router.post("/bulk-delete")
@log_bulk_delete("TableName")
async def bulk_delete_entities(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Entity", "DELETE"))
):
    deleted_count = new_entity_repo.bulk_delete(request_body.ids)
    return {
        "message": "삭제되었습니다",
        "deleted_count": deleted_count,
        "deleted_ids": request_body.ids    # 필수: 로깅에 사용됨
    }
```

**로깅 데코레이터 필수 조건:**
- 함수 파라미터에 `request: Request`가 **반드시** 있어야 함
- 함수 파라미터에 `user: CurrentUser`가 **반드시** 있어야 함 (변수명은 user, admin, current_user 가능)
- `@log_activity`의 `id_key`는 반환 dict의 키와 **일치**해야 함
- `@log_delete`의 `id_param`은 경로 파라미터 이름과 **일치**해야 함
- `@log_bulk_delete` 사용 시 반환 dict에 `deleted_ids` 키가 **필수**

### 2-4. 권한 (Permission) - 필수

모든 API 엔드포인트에 권한 체크를 적용합니다.

```python
from core.dependencies import require_permission

# 기본 사용법 - 모듈명과 액션을 지정
user = Depends(require_permission("ModuleName", "READ"))
user = Depends(require_permission("ModuleName", "CREATE"))
user = Depends(require_permission("ModuleName", "UPDATE"))
user = Depends(require_permission("ModuleName", "DELETE"))
user = Depends(require_permission("ModuleName", "EXPORT"))
user = Depends(require_permission("ModuleName", "IMPORT"))
```

**권한 체크 순서:** UserPermission(DENY) → UserPermission(GRANT) → RolePermission

**역할별 기본 권한:**
- Admin: 전체 접근
- Manager: 읽기/쓰기 (시스템 설정 제외)
- Viewer: 읽기 전용

### 2-5. Pydantic 모델 규칙

```python
from pydantic import BaseModel
from typing import Optional, List

# CREATE: 필수 필드만 required, 나머지 Optional
class EntityCreate(BaseModel):
    Name: str                          # 필수
    RefID: Optional[int] = None        # 선택
    Status: Optional[str] = "ACTIVE"   # 기본값

# UPDATE: 모든 필드 Optional (부분 수정 지원)
class EntityUpdate(BaseModel):
    Name: Optional[str] = None
    RefID: Optional[int] = None
    Status: Optional[str] = None

# BULK DELETE
class BulkDeleteRequest(BaseModel):
    ids: List[int]         # int PK인 경우
    # ids: List[str]       # string PK인 경우
```

### 2-6. 정렬 (Sorting) 규칙

```python
# 허용된 컬럼만 화이트리스트로 관리 (SQL Injection 방지)
ALLOWED_SORT = {
    "TableNameID": "t.TableNameID",
    "Name": "t.Name",
    "RefName": "r.RefName",
}
order_by = ALLOWED_SORT.get(sort_by, "t.TableNameID")
order_dir = sort_dir if sort_dir in ("ASC", "DESC") else "DESC"
```

### 2-7. 에러 처리 패턴

```python
try:
    # 로직
except HTTPException:
    raise                    # HTTP 에러는 그대로 전달
except ValueError as e:
    raise HTTPException(404, str(e))
except Exception as e:
    raise HTTPException(500, f"작업 실패: {str(e)}")
```

### 2-8. app.py 라우터 등록

```python
# app.py에 추가
from routers import new_entity

app.include_router(new_entity.router)
# 서브 라우터가 있는 경우:
app.include_router(new_entity.detail_router)
```

---

## 3. Frontend 규칙

### 3-1. HTML 템플릿 구조

`base.html`을 상속하며, 4개의 블록을 사용합니다.

```html
{% extends "base.html" %}

{% block title %}페이지 제목{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="/static/css/pages/entity.css">
{% endblock %}

{% block content %}
<!-- 페이지 헤더 -->
<div class="page-header">
    <h1 class="page-title">
        <i class="fa-solid fa-icon-name"></i> 페이지 제목
    </h1>
    <p class="page-subtitle">설명 텍스트</p>
</div>

<!-- 검색 필터 카드 -->
<div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
        <div class="card-title" style="margin:0;">
            <i class="fa-solid fa-filter"></i> 검색 필터
        </div>
        <div style="display:flex;gap:12px;">
            <button class="btn btn-secondary btn-sm" onclick="resetFilters()">초기화</button>
            <button class="btn btn-primary btn-sm" onclick="applyFilters()">검색</button>
        </div>
    </div>
    <div class="search-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;">
        <div class="form-group">
            <label class="form-label">필터명</label>
            <input type="text" id="filterName" class="form-input" placeholder="검색어">
        </div>
        <div class="form-group">
            <label class="form-label">상태</label>
            <select id="filterStatus" class="form-select">
                <option value="">전체</option>
            </select>
        </div>
    </div>
</div>

<!-- 데이터 테이블 카드 -->
<div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px;">
        <h2 class="card-title" style="margin:0;white-space:nowrap;">
            목록 <span id="totalCount" class="text-muted" style="font-size:14px;font-weight:400;"></span>
        </h2>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button class="btn btn-primary btn-sm" onclick="showAddModal()">
                <i class="fa-solid fa-plus"></i> 추가
            </button>
            <button class="btn btn-danger btn-sm" id="bulkDeleteBtn" disabled onclick="bulkDelete()">
                <i class="fa-solid fa-trash"></i> 선택 삭제
            </button>
        </div>
    </div>
    <div class="table-container">
        <table class="table" id="master-table">
            <thead><tr></tr></thead>
            <tbody></tbody>
        </table>
    </div>
    <div id="pagination" style="display:flex;justify-content:center;gap:8px;margin-top:20px;"></div>
</div>

<!-- 모달 -->
<div id="addModal" class="modal">
    <div class="modal-content" style="max-width:600px;">
        <div class="modal-header">
            <h2 class="modal-title">추가</h2>
            <button class="modal-close" data-modal-close>&times;</button>
        </div>
        <div class="modal-body">
            <div class="form-group">
                <label class="form-label required">이름</label>
                <input type="text" id="addName" class="form-input">
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" data-modal-close>취소</button>
            <button class="btn btn-primary" onclick="saveEntity()">저장</button>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="/static/js/pages/entity.js"></script>
{% endblock %}
```

### 3-2. 마스터-디테일 레이아웃 (해당 시)

마스터(목록)와 디테일(하위 데이터)을 좌우로 배치합니다.

```html
<div style="display:grid;grid-template-columns:1.7fr 1fr;gap:24px;">
    <!-- 좌측: 마스터 -->
    <div class="card">
        <!-- 테이블 + 페이지네이션 -->
    </div>

    <!-- 우측: 디테일 -->
    <div class="card">
        <div id="detailPlaceholder" style="text-align:center;padding:60px 20px;color:var(--text-muted);">
            <i class="fa-solid fa-hand-pointer" style="font-size:48px;margin-bottom:16px;opacity:0.3;"></i>
            <p>좌측에서 항목을 선택하세요</p>
        </div>
        <div id="detailContainer" style="display:none;">
            <!-- 선택 후 표시되는 디테일 테이블 -->
        </div>
    </div>
</div>
```

### 3-3. Page JS 작성 규칙 (Orchestrator 패턴)

```javascript
// ==========================================
// 1. 상태 변수 선언
// ==========================================
let masterTableManager, detailTableManager, paginationManager;
let addModal, editModal;
let currentFilters = {};
let currentSelectedId = null;
let currentSortBy = null;
let currentSortDir = null;

// ==========================================
// 2. 컬럼 정의
// ==========================================
const masterColumns = [
    { key: 'ID', header: 'ID', sortKey: 'ID' },
    { key: 'Name', header: '이름', sortKey: 'Name' },
    {
        key: 'Status',
        header: '상태',
        render: (row) => {
            const labels = { ACTIVE: '활성', INACTIVE: '비활성' };
            return `<span class="badge badge-${row.Status === 'ACTIVE' ? 'success' : 'danger'}">${labels[row.Status] || row.Status}</span>`;
        }
    }
];

// ==========================================
// 3. 초기화 (DOMContentLoaded)
// ==========================================
document.addEventListener('DOMContentLoaded', async function() {
    // 모달 초기화
    addModal = new ModalManager('addModal');
    editModal = new ModalManager('editModal');

    // 테이블 매니저 초기화
    masterTableManager = new TableManager('master-table', {
        selectable: true,
        idKey: 'EntityID',
        onSelectionChange: (ids) => {
            document.getElementById('bulkDeleteBtn').disabled = ids.length === 0;
        },
        onRowClick: (row, tr) => selectEntity(row, tr),
        onSort: (sortKey, sortDir) => {
            currentSortBy = sortKey;
            currentSortDir = sortDir;
            loadEntities(1, paginationManager.getLimit());
        },
        emptyMessage: '데이터가 없습니다.'
    });
    masterTableManager.renderHeader(masterColumns);

    // 페이지네이션 초기화
    paginationManager = new PaginationManager('pagination', {
        onPageChange: (page, limit) => loadEntities(page, limit),
        onLimitChange: (page, limit) => loadEntities(page, limit)
    });

    // 드롭다운 데이터 로드 (병렬)
    await Promise.all([
        loadDropdown1(),
        loadDropdown2()
    ]);

    // 초기 데이터 로드
    loadEntities(1, 20);

    // 필터 Enter 키 지원
    ['filterName', 'filterStatus'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('keypress', e => {
            if (e.key === 'Enter') applyFilters();
        });
    });
});

// ==========================================
// 4. 데이터 로드
// ==========================================
async function loadEntities(page = 1, limit = 20) {
    try {
        masterTableManager.showLoading(masterColumns.length);

        const params = {
            page, limit,
            sort_by: currentSortBy,
            sort_dir: currentSortDir,
            ...currentFilters
        };
        const query = api.buildQueryString(params);
        const res = await api.get(`/api/entities${query}`);

        document.getElementById('totalCount').textContent = `총 ${res.total}개`;
        masterTableManager.render(res.data, masterColumns);
        paginationManager.render({
            page, limit,
            total: res.total,
            total_pages: Math.ceil(res.total / limit)
        });
    } catch (e) {
        showAlert('데이터 로드 실패: ' + e.message, 'error');
        masterTableManager.render([], masterColumns);
    }
}

// ==========================================
// 5. 필터
// ==========================================
function applyFilters() {
    currentFilters = {};
    const name = document.getElementById('filterName')?.value;
    const status = document.getElementById('filterStatus')?.value;
    if (name) currentFilters.name = name;
    if (status) currentFilters.status = status;
    loadEntities(1, paginationManager.getLimit());
}

function resetFilters() {
    document.getElementById('filterName').value = '';
    document.getElementById('filterStatus').value = '';
    currentFilters = {};
    loadEntities(1, 20);
}

// ==========================================
// 6. CRUD 동작
// ==========================================
function showAddModal() {
    document.getElementById('addName').value = '';
    addModal.show();
}

async function saveEntity() {
    const data = {
        Name: document.getElementById('addName')?.value
    };
    if (!data.Name) {
        showAlert('이름을 입력하세요', 'warning');
        return;
    }
    try {
        await api.post('/api/entities', data);
        showAlert('저장 완료', 'success');
        addModal.hide();
        loadEntities(1, paginationManager.getLimit());
    } catch (e) {
        showAlert('저장 실패: ' + e.message, 'error');
    }
}

async function bulkDelete() {
    const ids = masterTableManager.getSelectedRows();
    if (ids.length === 0) return;
    if (!confirm(`${ids.length}건을 삭제하시겠습니까?`)) return;
    try {
        await api.post('/api/entities/bulk-delete', { ids });
        showAlert('삭제 완료', 'success');
        loadEntities(1, paginationManager.getLimit());
    } catch (e) {
        showAlert('삭제 실패: ' + e.message, 'error');
    }
}
```

### 3-4. 사용 가능한 공통 모듈

| 모듈 | 전역 변수/클래스 | 주요 메서드 |
|------|-----------------|-------------|
| `api-client.js` | `api` (ApiClient 인스턴스) | `api.get()`, `api.post()`, `api.put()`, `api.delete()`, `api.buildQueryString()` |
| `table-manager.js` | `TableManager` | `renderHeader()`, `render()`, `showLoading()`, `getSelectedRows()`, `clearSelection()` |
| `pagination-manager.js` | `PaginationManager` | `render()`, `getCurrentPage()`, `getLimit()` |
| `modal-manager.js` | `ModalManager` | `show()`, `hide()`, `toggle()`, `isVisible()`, `resetForm()` |
| `ui-utils.js` | `showAlert()`, `showConfirm()` | `showAlert(msg, type)` type: success/error/warning/info |

### 3-5. CSS 사용 가능한 클래스

**버튼:** `.btn`, `.btn-primary`, `.btn-success`, `.btn-danger`, `.btn-secondary`, `.btn-sm`, `.btn-lg`
**폼:** `.form-group`, `.form-label`, `.form-label.required`, `.form-input`, `.form-select`
**테이블:** `.table-container`, `.table`
**카드:** `.card`, `.card-title`
**배지:** `.badge`, `.badge-success`, `.badge-warning`, `.badge-danger`, `.badge-info`
**알림:** `.alert`, `.alert-success`, `.alert-warning`, `.alert-danger`
**텍스트:** `.text-muted`, `.text-success`, `.text-warning`, `.text-danger`

### 3-6. CSS 변수 (커스텀 스타일 시)

```css
/* 색상 */
--bg-body: #0a0e1a;        --bg-card: #1a1f2e;        --bg-input: #0f1419;
--text-main: #e2e8f0;      --text-muted: #94a3b8;
--accent: #6366f1;         --accent-hover: #5558e3;
--success: #10b981;        --warning: #f59e0b;         --danger: #ef4444;
--border: rgba(148, 163, 184, 0.2);

/* 간격 */
--spacing-xs: 4px;  --spacing-sm: 8px;  --spacing-md: 16px;  --spacing-lg: 24px;  --spacing-xl: 32px;

/* 둥글기 */
--radius-sm: 8px;   --radius-md: 12px;  --radius-lg: 16px;
```

---

## 4. Pages 라우터 등록

`routers/pages.py`에 페이지 라우트를 추가합니다.

```python
@router.get("/entities", response_class=HTMLResponse)
async def entities_page(request: Request, redirect=Depends(require_login_for_page)):
    """엔티티 관리 페이지"""
    if redirect:
        return redirect
    return templates.TemplateResponse("entities.html", {
        "request": request,
        "active_page": "entities"    # 사이드바 활성화 키
    })
```

---

## 5. 사이드바 메뉴 추가

`templates/base.html`의 사이드바 네비게이션에 항목을 추가합니다.

```html
<a href="/entities"
   class="nav-item {{ 'active' if active_page == 'entities' else '' }}">
    <i class="fa-solid fa-icon-name"></i>
    <span>메뉴 이름</span>
</a>
```

---

## 6. API 응답 형식 규칙

모든 API는 아래 형식을 따릅니다.

```javascript
// 목록 조회 (GET)
{
    "data": [...],
    "total": 150,
    "page": 1,
    "limit": 20,
    "total_pages": 8
}

// 생성 (POST) - id_key 포함 필수
{ "EntityID": 1, "message": "생성되었습니다" }

// 수정 (PUT)
{ "EntityID": 1, "message": "수정되었습니다" }

// 삭제 (DELETE)
{ "message": "삭제되었습니다" }

// 일괄 삭제 - deleted_ids 포함 필수
{ "message": "삭제되었습니다", "deleted_count": 3, "deleted_ids": [1, 2, 3] }

// 메타데이터 (GET /metadata)
{ "statuses": [...], "types": [...] }
```

---

## 7. DB 작업 규칙

### 읽기 전용

```python
from core.database import get_db_cursor

with get_db_cursor(commit=False) as cursor:
    cursor.execute("SELECT ...", param1, param2)
    rows = cursor.fetchall()
```

### 쓰기 (자동 커밋)

```python
with get_db_cursor(commit=True) as cursor:
    cursor.execute("INSERT INTO ...", param1, param2)
```

### 트랜잭션 (여러 테이블 동시 수정)

```python
from core.database import get_db_transaction

with get_db_transaction() as (conn, cursor):
    cursor.execute("INSERT INTO Table1 ...")
    cursor.execute("INSERT INTO Table2 ...")
    conn.commit()
```

### SQL 파라미터 바인딩 (필수)

```python
# 올바른 방법 - 파라미터 바인딩
cursor.execute("SELECT * FROM [dbo].[Table] WHERE Name = ?", name)

# 금지 - 문자열 포맷팅 (SQL Injection 위험)
cursor.execute(f"SELECT * FROM [dbo].[Table] WHERE Name = '{name}'")
```

---

## 8. 기존 기능에 추가 작업 시 체크리스트

기존 섹션에 기능을 추가할 때 확인할 항목입니다.

### 새 API 엔드포인트 추가 시

- [ ] `require_permission()` 적용했는가
- [ ] CUD 작업에 활동 로깅 데코레이터 적용했는가
- [ ] 에러 처리 패턴(try/except HTTPException/except Exception) 적용했는가
- [ ] 정렬 파라미터에 화이트리스트 적용했는가
- [ ] Pydantic 모델로 요청 본문을 정의했는가

### 새 DB 테이블/컬럼 추가 시

- [ ] `sql/` 폴더에 마이그레이션 스크립트 작성했는가
- [ ] 마이그레이션 스크립트가 멱등성을 보장하는가 (IF NOT EXISTS 등)
- [ ] 필요한 인덱스를 추가했는가

### 프론트엔드 변경 시

- [ ] 공통 모듈(TableManager, ApiClient 등)을 활용했는가
- [ ] 새로운 유틸리티를 만들지 않고 기존 것을 사용했는가
- [ ] CSS 변수를 사용했는가 (하드코딩된 색상 금지)
- [ ] 컬럼 정의 객체를 사용하여 테이블을 렌더링했는가

---

## 9. 네이밍 규칙 요약

| 대상 | 규칙 | 예시 |
|------|------|------|
| API 경로 | `/api/{복수형-케밥}` | `/api/new-entities` |
| 라우터 태그 | PascalCase | `"NewEntity"` |
| Python 파일 | snake_case | `new_entity_repository.py` |
| Python 클래스 | PascalCase | `NewEntityRepository` |
| Python 함수 | snake_case | `get_entities()` |
| JS 파일 | kebab-case (모듈), snake_case (pages) | `table-manager.js`, `new_entity.js` |
| JS 함수 | camelCase | `loadEntities()` |
| CSS 클래스 | kebab-case | `.btn-primary` |
| DB 테이블 | PascalCase + 브라켓 | `[dbo].[NewEntity]` |
| DB 컬럼 | PascalCase | `EntityID`, `CreatedDate` |
| HTML id | camelCase | `filterName`, `addModal` |
| 환경변수 | UPPER_SNAKE | `DB_SERVER` |