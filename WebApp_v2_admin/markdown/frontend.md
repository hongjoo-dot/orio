# Frontend (Templates + JS + CSS)

Jinja2 서버사이드 렌더링 + Vanilla JS 모듈 기반 프론트엔드.
프레임워크 없이 공통 모듈(TableManager, ApiClient 등)을 조립하는 Orchestrator 패턴.

---

## 1. HTML 템플릿 (`templates/`)

### 구조
- `base.html`: 마스터 레이아웃 (CSS/JS 공통 로드, 사이드바 포함)
- `components/sidebar.html`: 네비게이션 사이드바
- `{page}.html`: 각 페이지 (base.html 상속)

### 템플릿 상속 구조
```html
{% extends "base.html" %}

{% block title %}페이지 제목{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="/static/css/pages/entity.css">
{% endblock %}

{% block content %}
<!-- 1. 페이지 헤더 -->
<div class="page-header">
    <h1 class="page-title"><i class="fa-solid fa-icon"></i> 제목</h1>
    <p class="page-subtitle">설명</p>
</div>

<!-- 2. 검색 필터 카드 -->
<div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
        <div class="card-title" style="margin:0;"><i class="fa-solid fa-filter"></i> 검색 필터</div>
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
    </div>
</div>

<!-- 3. 데이터 테이블 카드 -->
<div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <h2 class="card-title" style="margin:0;">
            목록 <span id="totalCount" class="text-muted" style="font-size:14px;font-weight:400;"></span>
        </h2>
        <div style="display:flex;gap:8px;">
            <button class="btn btn-primary btn-sm" onclick="showAddModal()">
                <i class="fa-solid fa-plus"></i> 추가
            </button>
            <button class="btn btn-danger btn-sm" id="bulkDeleteBtn" disabled onclick="bulkDelete()">
                <i class="fa-solid fa-trash"></i> 선택 삭제
            </button>
        </div>
    </div>
    <div class="table-container">
        <table class="table" id="master-table"><thead><tr></tr></thead><tbody></tbody></table>
    </div>
    <div id="pagination" style="display:flex;justify-content:center;gap:8px;margin-top:20px;"></div>
</div>

<!-- 4. 모달 -->
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

### Master-Detail 레이아웃 (해당 시)
```html
<div style="display:grid;grid-template-columns:1.7fr 1fr;gap:24px;">
    <div class="card"><!-- 좌측: 마스터 테이블 --></div>
    <div class="card">
        <div id="detailPlaceholder">좌측에서 항목을 선택하세요</div>
        <div id="detailContainer" style="display:none;">
            <!-- 선택 후 디테일 테이블 -->
        </div>
    </div>
</div>
```

### 사이드바 메뉴 추가
```html
<!-- templates/components/sidebar.html -->
<a href="/entities" class="nav-item {{ 'active' if active_page == 'entities' else '' }}">
    <i class="fa-solid fa-icon-name"></i>
    <span>메뉴 이름</span>
</a>
```

---

## 2. JavaScript 모듈 (`static/js/`)

### 공통 모듈 (base.html에서 전역 로드)

| 모듈 | 전역 변수/클래스 | 주요 메서드 |
|------|-----------------|-------------|
| `api-client.js` | `api` (인스턴스) | `api.get()`, `api.post()`, `api.put()`, `api.delete()`, `api.buildQueryString()` |
| `table-manager.js` | `TableManager` | `renderHeader()`, `render()`, `showLoading()`, `getSelectedRows()`, `clearSelection()` |
| `pagination-manager.js` | `PaginationManager` | `render()`, `getCurrentPage()`, `getLimit()` |
| `modal-manager.js` | `ModalManager` | `show()`, `hide()`, `toggle()`, `isVisible()`, `resetForm()` |
| `ui-utils.js` | `showAlert()`, `showConfirm()` | type: success/error/warning/info |

### ApiClient (`api-client.js`)
```javascript
// JWT 토큰 자동 포함 (localStorage)
const res = await api.get('/api/products?page=1&limit=20');
await api.post('/api/products', { Name: "A", BrandID: 1 });
await api.put('/api/products/1', { Name: "B" });
await api.delete('/api/products/1');

// 쿼리 파라미터 빌더
const query = api.buildQueryString({ page: 1, limit: 20, name: "Apple" });
// → "?page=1&limit=20&name=Apple"
```

### TableManager (`table-manager.js`)
```javascript
const tableManager = new TableManager('table-id', {
    selectable: true,                    // 체크박스 선택
    idKey: 'ProductID',                  // 선택 시 ID 기준
    onSelectionChange: (ids) => { ... }, // 선택 변경 콜백
    onRowClick: (row, tr) => { ... },    // 행 클릭 콜백
    onSort: (sortKey, sortDir) => { ... }, // 정렬 콜백
    emptyMessage: '데이터가 없습니다.'
});

// 컬럼 정의
const columns = [
    { key: 'ProductID', header: 'ID', sortKey: 'ProductID' },
    { key: 'Name', header: '이름', sortKey: 'Name' },
    {
        key: 'Status', header: '상태',
        render: (row) => `<span class="badge badge-${row.Status === 'ACTIVE' ? 'success' : 'danger'}">${row.Status}</span>`
    }
];

tableManager.renderHeader(columns);          // 헤더 렌더링
tableManager.render(res.data, columns);      // 데이터 렌더링
tableManager.showLoading(columns.length);    // 로딩 상태
const selectedIds = tableManager.getSelectedRows(); // 선택된 ID 배열
```

### PaginationManager (`pagination-manager.js`)
```javascript
const paginationManager = new PaginationManager('pagination', {
    onPageChange: (page, limit) => loadData(page, limit),
    onLimitChange: (page, limit) => loadData(page, limit)
});

paginationManager.render({ page: 1, limit: 20, total: 150, total_pages: 8 });
```

### ModalManager (`modal-manager.js`)
```javascript
const addModal = new ModalManager('addModal');
addModal.show();
addModal.hide();
addModal.resetForm();  // 폼 필드 초기화
```

### Page Orchestrator 패턴 (`pages/*.js`)

```javascript
// 1. 상태 변수
let masterTableManager, paginationManager, addModal;
let currentFilters = {}, currentSortBy = null, currentSortDir = null;

// 2. 컬럼 정의
const masterColumns = [ ... ];

// 3. DOMContentLoaded - 초기화
document.addEventListener('DOMContentLoaded', async function() {
    addModal = new ModalManager('addModal');
    masterTableManager = new TableManager('master-table', { ... });
    masterTableManager.renderHeader(masterColumns);
    paginationManager = new PaginationManager('pagination', { ... });
    await loadData(1, 20);

    // 필터 Enter 키 지원
    ['filterName', 'filterStatus'].forEach(id => {
        document.getElementById(id)?.addEventListener('keypress', e => {
            if (e.key === 'Enter') applyFilters();
        });
    });
});

// 4. 데이터 로드
async function loadData(page = 1, limit = 20) {
    masterTableManager.showLoading(masterColumns.length);
    const params = { page, limit, sort_by: currentSortBy, sort_dir: currentSortDir, ...currentFilters };
    const res = await api.get(`/api/entities${api.buildQueryString(params)}`);
    document.getElementById('totalCount').textContent = `총 ${res.total}개`;
    masterTableManager.render(res.data, masterColumns);
    paginationManager.render({ page, limit, total: res.total, total_pages: Math.ceil(res.total / limit) });
}

// 5. 필터
function applyFilters() { currentFilters = { ... }; loadData(1, paginationManager.getLimit()); }
function resetFilters() { /* 초기화 */ loadData(1, 20); }

// 6. CRUD
async function saveEntity() {
    const data = { Name: document.getElementById('addName')?.value };
    await api.post('/api/entities', data);
    showAlert('저장 완료', 'success');
    addModal.hide();
    loadData(1, paginationManager.getLimit());
}
```

---

## 3. CSS (`static/css/`)

### 다크 테마 디자인 시스템

```css
/* 주요 CSS 변수 */
--bg-body: #0a0e1a;        --bg-card: #1a1f2e;        --bg-input: #0f1419;
--text-main: #e2e8f0;      --text-muted: #94a3b8;
--accent: #6366f1;         --accent-hover: #5558e3;
--success: #10b981;        --warning: #f59e0b;         --danger: #ef4444;
--border: rgba(148, 163, 184, 0.2);
--spacing-xs: 4px; --spacing-sm: 8px; --spacing-md: 16px; --spacing-lg: 24px;
--radius-sm: 8px;  --radius-md: 12px;
```

### 사용 가능한 CSS 클래스

| 카테고리 | 클래스 |
|---------|--------|
| 버튼 | `.btn`, `.btn-primary`, `.btn-success`, `.btn-danger`, `.btn-secondary`, `.btn-sm`, `.btn-lg` |
| 폼 | `.form-group`, `.form-label`, `.form-label.required`, `.form-input`, `.form-select` |
| 테이블 | `.table-container`, `.table` |
| 카드 | `.card`, `.card-title` |
| 배지 | `.badge`, `.badge-success`, `.badge-warning`, `.badge-danger`, `.badge-info` |
| 알림 | `.alert`, `.alert-success`, `.alert-warning`, `.alert-danger` |
| 텍스트 | `.text-muted`, `.text-success`, `.text-warning`, `.text-danger` |
| 모달 | `.modal`, `.modal-content`, `.modal-header`, `.modal-body`, `.modal-footer` |

### 파일 구성

| 파일 | 내용 | 라인 수 |
|------|------|---------|
| `base.css` | CSS 변수, 리셋, 기본 타이포그래피 | ~165 |
| `layout.css` | 레이아웃, 사이드바, 그리드, 카드, 페이지 헤더 | ~338 |
| `components.css` | 버튼, 폼, 테이블, 모달, 배지, 알림 | ~527 |

### 규칙
- 하드코딩된 색상 금지 → CSS 변수 사용
- 페이지 전용 스타일은 `static/css/pages/{entity}.css`에 분리
- 새 컴포넌트 스타일은 `components.css`에 추가
