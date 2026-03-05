# CLAUDE.md - WebApp_v2_admin

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 개요

FastAPI 기반의 Orio ERP 관리 시스템 v2.0입니다. Repository 패턴을 적용하여 데이터 접근 로직과 비즈니스 로직을 분리했으며, JWT 인증 및 활동 로깅 기능을 포함합니다.
최근 리팩토링을 통해 프론트엔드는 모듈화된 JS 유틸리티를, 백엔드는 계층화된 엑셀 핸들러를 도입하여 유지보수성을 대폭 향상시켰습니다.

### 주요 특징

- **Repository Pattern**: 데이터 접근 계층 분리
- **Query Builder**: 동적 SQL 쿼리 생성 및 SQL Injection 방지
- **Excel Handler System**: 도메인별 엑셀 처리 로직 분리 및 상속 구조
- **Modular Frontend**: TableManager, PaginationManager 등 공통 모듈 기반 UI
- **Context Manager**: DB 연결 자동 관리 및 트랜잭션 처리
- **JWT 인증**: 사용자 인증 및 역할 기반 권한 관리 (RBAC)
- **Activity Logging**: 모든 CUD 작업 로그 기록 (IP 추적 포함)
- **Changelog**: 변경 로그 기록 기능 (수정 전/후 비교)
- **Slack 알림**: 주요 변동사항 Slack 채널 자동 알림
- **예상 매출 관리**: 사입/위탁 × 정기/비정기 4종 예측 + 통합 조회

### 기술 스택

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pandas
- **Database**: SQL Server (Azure SQL Database)
- **Authentication**: JWT (HS256), bcrypt
- **Frontend**: Jinja2 Templates, Vanilla JS (ES6+ Modules)
- **Storage**: Azure Blob Storage (파일 업로드)
- **Notification**: Slack Webhook 연동
- **Driver**: ODBC Driver 17 for SQL Server

## 개발 환경 설정

### 사전 요구사항

- Python 3.10+
- SQL Server (Azure)
- ODBC Driver 17 for SQL Server

### 로컬 개발 환경 구축

```bash
# 1. 프로젝트 디렉토리로 이동
cd Azure/WebApp_v2_admin

# 2. 가상환경 생성 (선택사항)
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. 패키지 설치
pip install -r requirements.txt

# 4. .env 파일 설정
# 아래 "환경 설정" 섹션 참조

# 5. 애플리케이션 실행
python app.py
# 또는
uvicorn app:app --host 0.0.0.0 --port 8002 --reload
```

### 접속 URL

- **Web UI**: http://localhost:8002
- **API 문서 (Swagger)**: http://localhost:8002/docs
- **API 문서 (ReDoc)**: http://localhost:8002/redoc
- **Health Check**: http://localhost:8002/api/health

## 환경 설정

### .env 파일

```ini
# 데이터베이스 연결
DB_SERVER=your-server.database.windows.net
DB_DATABASE=your-database
DB_USERNAME=your-username
DB_PASSWORD=your-password
DB_DRIVER={ODBC Driver 17 for SQL Server}

# JWT 인증
JWT_SECRET_KEY=your-secret-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=8

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key
```

## 프로젝트 구조

```
WebApp_v2_admin/
├── app.py                      # FastAPI 메인 애플리케이션
├── .env                        # 환경 변수
├── requirements.txt            # Python 패키지 의존성
├── CLAUDE.md                   # 개발 가이드 (이 문서)
├── DEVELOPMENT_RULES.md        # 필수 개발 규칙 및 체크리스트
│
├── core/                       # 핵심 유틸리티 및 공통 모듈
│   ├── base_repository.py      # BaseRepository 추상 클래스 (generic CRUD)
│   ├── database.py             # DB 연결 관리 (Context Manager, Azure 재시도)
│   ├── query_builder.py        # 동적 SQL 쿼리 빌더
│   ├── security.py             # JWT 인증, 비밀번호 해싱
│   ├── dependencies.py         # FastAPI 의존성 주입 (인증, 권한)
│   ├── decorators.py           # 함수 데코레이터 (@transactional, @retry 등)
│   ├── activity_decorator.py   # 감사 로깅 데코레이터 (@log_activity)
│   ├── changelog.py            # 변경 이력 추적
│   ├── models.py               # 공유 Pydantic 모델
│   └── exceptions.py           # 커스텀 예외 클래스
│
├── repositories/               # 데이터 접근 계층 (18개 Repository)
│   ├── product_repository.py           # Product CRUD
│   ├── product_box_repository.py       # ProductBox (포장 SKU) CRUD
│   ├── brand_repository.py             # Brand CRUD
│   ├── channel_repository.py           # Channel CRUD
│   ├── sales_repository.py             # ERPSales CRUD
│   ├── bom_repository.py               # ProductBOM CRUD
│   ├── user_repository.py              # User & Role CRUD
│   ├── activity_log_repository.py      # 감사 로그 조회
│   ├── permission_repository.py        # 권한(RBAC) 관리
│   ├── expected_1p_regular_repository.py        # 사입 정기 예상매출
│   ├── expected_1p_irregular_repository.py      # 사입 비정기 예상매출
│   ├── expected_1p_irregular_product_repository.py  # 사입 비정기 하위상품
│   ├── expected_3p_regular_repository.py        # 위탁 정기 예상매출
│   ├── expected_3p_irregular_repository.py      # 위탁 비정기 예상매출
│   ├── expected_3p_irregular_product_repository.py  # 위탁 비정기 하위상품
│   ├── withdrawal_plan_repository.py   # 불출 계획
│   └── system_config_repository.py     # 시스템 설정
│
├── routers/                    # API 라우터 (16개 Router)
│   ├── pages.py                # HTML 페이지 라우트 핸들러
│   ├── auth.py                 # /api/auth (로그인, 로그아웃, 비밀번호 변경)
│   ├── admin.py                # /api/admin (사용자 관리, 권한, 감사)
│   ├── product.py              # /api/products (CRUD + 엑셀)
│   ├── brand.py                # /api/brands (브랜드 관리)
│   ├── channel.py              # /api/channels (채널 및 상세)
│   ├── sales.py                # /api/erpsales (매출 데이터)
│   ├── bom.py                  # /api/bom (BOM 관리)
│   ├── expected_1p_regular.py  # /api/expected/1p/regular (사입 정기)
│   ├── expected_1p_irregular.py # /api/expected/1p/irregular (사입 비정기)
│   ├── expected_3p_regular.py  # /api/expected/3p/regular (위탁 정기)
│   ├── expected_3p_irregular.py # /api/expected/3p/irregular (위탁 비정기)
│   ├── expected_sales_integration.py  # /api/expected/sales/integration (통합 조회)
│   ├── withdrawal_plan.py      # /api/withdrawal-plans (불출 계획)
│   ├── utility.py              # /api/utilities (구성품 쪼개기 등 유틸)
│   └── system_config.py        # /api/system-config (시스템 설정)
│
├── utils/                      # 공통 유틸리티
│   ├── helpers.py              # 헬퍼 함수
│   ├── slack_notifier.py       # Slack 알림 (변동사항 자동 알림)
│   └── excel/                  # Excel Handler System
│       ├── base_handler.py     # 공통 엑셀 처리 로직 (부모)
│       ├── product_handler.py  # 제품 엑셀 처리
│       └── sales_handler.py    # 매출 엑셀 처리
│
├── templates/                  # Jinja2 HTML 템플릿
│   ├── base.html               # 기본 레이아웃 (공통 JS 포함)
│   ├── login.html              # 로그인 (glassmorphism 디자인)
│   ├── dashboard.html          # 대시보드
│   ├── products.html           # 제품 관리 (Master-Detail)
│   ├── sales.html              # 매출 데이터
│   ├── channels.html           # 채널 관리 (Master-Detail)
│   ├── bom.html                # BOM 관리 (Master-Detail)
│   ├── expected_1p_regular.html        # 사입 정기 예상매출
│   ├── expected_3p_regular.html        # 위탁 정기 예상매출
│   ├── expected_sales_integration.html # 예상 매출 통합 조회
│   ├── withdrawal_plan.html    # 불출 계획
│   ├── utilities.html          # 유틸리티 (구성품 쪼개기)
│   ├── admin.html              # 사용자 관리
│   ├── activity_log.html       # 활동 로그 조회
│   ├── permissions.html        # 권한 관리
│   ├── system_config.html      # 시스템 설정
│   └── components/             # 재사용 컴포넌트
│       ├── sidebar.html        # 네비게이션 사이드바
│       └── search-filter.html  # 검색/필터 컴포넌트
│
├── static/                     # 정적 파일
│   ├── css/
│   │   ├── base.css            # 기본 스타일 및 CSS 변수
│   │   ├── layout.css          # 레이아웃 그리드
│   │   ├── components.css      # 공통 컴포넌트 스타일
│   │   └── pages/              # 페이지별 전용 CSS
│   └── js/
│       ├── api-client.js       # REST API 래퍼 (JWT 토큰 자동 주입)
│       ├── table-manager.js    # 테이블 렌더링/선택 관리
│       ├── pagination-manager.js # 페이지네이션 관리
│       ├── modal-manager.js    # 모달 관리
│       ├── ui-utils.js         # Alert, Confirm 등 UI 유틸
│       └── pages/              # 페이지별 로직 (Orchestrator)
│           ├── products.js
│           ├── sales.js
│           ├── channels.js
│           ├── bom.js
│           ├── expected_1p_regular.js
│           ├── expected_3p_regular.js
│           ├── expected_sales_integration.js
│           ├── withdrawal_plan.js
│           └── utilities.js
│
└── sql/                        # SQL 스크립트
    └── oriodatabase_schema.sql # 전체 DB 스키마 정의
```

## 아키텍처 패턴

### 1. Repository Pattern (Backend)
모든 데이터 접근은 Repository를 통해 이루어집니다. `BaseRepository`를 상속받아 구현합니다.

### 2. Excel Handler System (Backend)
복잡한 엑셀 처리 로직을 라우터에서 분리하여 전담 핸들러 클래스로 관리합니다.
- **`ExcelBaseHandler`**: 파일 검증, 시트 읽기, 매핑 로드 등 공통 기능 제공.
- **`ProductExcelHandler` 등**: 도메인별 검증 및 데이터 처리 로직 구현.

```python
# 사용 예시 (Router)
@router.post("/upload")
async def upload_excel(file: UploadFile):
    handler = ProductExcelHandler()
    result = handler.process_upload(await file.read())
    return result
```

### 3. Modular Frontend Architecture
프론트엔드 로직은 공통 유틸리티 모듈에 위임하고, 페이지별 JS는 이를 조립(Orchestration)하는 역할만 수행합니다.

#### 주요 모듈:
- **`ApiClient`**: `api.get()`, `api.post()` 등으로 API 호출. JWT 토큰 자동 처리.
- **`TableManager`**: 테이블 렌더링, 로딩 상태, 체크박스 선택 관리.
- **`PaginationManager`**: 페이지네이션 UI 및 이벤트 처리.
- **`ModalManager`**: 모달 열기/닫기 관리.
- **`ui-utils.js`**: `showAlert()`, `showConfirm()` 등 표준화된 알림창.

```javascript
// 사용 예시 (pages/products.js)
const tableManager = new TableManager('table-id');
const paginationManager = new PaginationManager('pagination-id');

async function loadData() {
    tableManager.showLoading();
    const res = await api.get('/api/products');
    tableManager.render(res.data, columns);
    paginationManager.render(res.pagination);
}
```

### 4. Master-Detail UI Pattern
화면을 좌우로 나누어 Master(목록)와 Detail(상세/하위) 정보를 동시에 관리하는 패턴입니다.
- **Master**: 검색 필터, 목록 조회, 일괄 작업.
- **Detail**: 선택된 항목의 하위 데이터 조회 및 편집.
- **적용**: Products(Box), Channels(Detail), BOM(Child).

## 인증 및 권한

### 역할 기반 접근 제어 (RBAC)
- **Admin**: 전체 접근 권한.
- **Manager**: 쓰기 권한 (시스템 설정 제외).
- **Viewer**: 읽기 전용.

### JWT 인증
`core/security.py` 및 `core/dependencies.py`에서 처리. `api-client.js`가 자동으로 헤더에 토큰을 포함합니다.

## 활동 로깅
모든 CUD 작업은 `ActivityLogRepository`를 통해 DB에 기록됩니다. `core/activity_decorator.py`의 `@log_activity` 데코레이터로 자동 적용 가능합니다.

## 예상 매출 관리 (Expected Sales)

4가지 유형의 예상 매출을 관리합니다:

| 유형 | 설명 | 라우터 |
|------|------|--------|
| **1P 정기 (사입 Regular)** | 정기 사입 매출 예측 | `expected_1p_regular.py` |
| **1P 비정기 (사입 Irregular)** | 비정기 사입 매출 예측 | `expected_1p_irregular.py` |
| **3P 정기 (위탁 Regular)** | 정기 위탁 매출 예측 | `expected_3p_regular.py` |
| **3P 비정기 (위탁 Irregular)** | 비정기 위탁 매출 예측 | `expected_3p_irregular.py` |
| **통합 조회** | 전체 예상 매출 통합 뷰 | `expected_sales_integration.py` |

### 주요 기능
- 입력월 필터링 (월별 조회)
- 브랜드/채널별 필터
- 엑셀 양식 선택 및 다운로드 (정기/비정기/쿠팡/올리브영 등 채널별 양식)
- 일괄 삭제 기능
- 올리브영 온라인/오프라인 구분 지원
- 쿠팡 SKU 칼럼 지원
- 수정 시 Slack 자동 알림
- 비정기 항목의 하위 상품(Product) 관리

## API 엔드포인트 요약

- `/api/auth`: 인증 (로그인, 로그아웃, 비밀번호 변경)
- `/api/admin`: 관리자 기능 (사용자, 권한, 감사 로그)
- `/api/products`: 제품 관리 (CRUD + 엑셀 임포트/익스포트)
- `/api/brands`: 브랜드 관리
- `/api/bom`: BOM 관리
- `/api/erpsales`: 매출 데이터 (CRUD + 엑셀 업로드)
- `/api/channels`: 채널 관리 (채널 + 상세)
- `/api/expected/1p/regular`: 사입 정기 예상매출
- `/api/expected/1p/irregular`: 사입 비정기 예상매출
- `/api/expected/3p/regular`: 위탁 정기 예상매출
- `/api/expected/3p/irregular`: 위탁 비정기 예상매출
- `/api/expected/sales/integration`: 예상 매출 통합 조회
- `/api/withdrawal-plans`: 불출 계획
- `/api/utilities`: 유틸리티 (구성품 쪼개기 등)
- `/api/system-config`: 시스템 설정

## 페이지 라우트 (pages.py)

```
GET /                           → dashboard.html
GET /login                      → login.html (public)
GET /products                   → products.html
GET /sales                      → sales.html
GET /channels                   → channels.html
GET /bom                        → bom.html
GET /expected-1p                → expected_1p_regular.html
GET /expected-3p                → expected_3p_regular.html
GET /expected-sales-integration → expected_sales_integration.html
GET /withdrawal-plans           → withdrawal_plan.html
GET /utilities                  → utilities.html
GET /admin/users                → admin.html
GET /admin/activity-log         → activity_log.html
GET /admin/permissions          → permissions.html
GET /admin/system-config        → system_config.html
```

## 새 기능 추가 가이드

> **반드시 `DEVELOPMENT_RULES.md` 체크리스트를 따라야 합니다.**

1.  **Backend**:
    *   `repositories/`에 Repository 클래스 작성 (`BaseRepository` 상속).
    *   `routers/`에 Router 작성 (`APIRouter` 사용).
    *   필요 시 `utils/excel/`에 Handler 작성.
    *   `app.py`에 라우터 등록.
    *   `routers/pages.py`에 페이지 라우트 추가.

2.  **Frontend**:
    *   `templates/`에 HTML 작성 (`base.html` 상속). `TableManager` 호환 테이블 구조 사용.
    *   `static/js/pages/`에 JS 작성. `ApiClient`, `TableManager` 등 활용.
    *   필요 시 `static/css/pages/`에 전용 CSS 작성.
    *   `templates/components/sidebar.html`에 메뉴 항목 추가.

## 디버깅

- **Health Check**: `http://localhost:8002/api/health`
- **Backend Log**: `logging` 모듈 사용.
- **Frontend Log**: 브라우저 콘솔 확인 (`api-client.js`가 에러 로깅).
