# CLAUDE.md - WebApp_v2_admin

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 개요

FastAPI 기반의 ERP 관리 시스템입니다. Repository 패턴을 적용하여 데이터 접근 로직과 비즈니스 로직을 분리했으며, JWT 인증 및 활동 로깅 기능을 포함합니다.
최근 리팩토링을 통해 프론트엔드는 모듈화된 JS 유틸리티를, 백엔드는 계층화된 엑셀 핸들러를 도입하여 유지보수성을 대폭 향상시켰습니다.

### 주요 특징

- **Repository Pattern**: 데이터 접근 계층 분리
- **Query Builder**: 동적 SQL 쿼리 생성 및 SQL Injection 방지
- **Excel Handler System**: 도메인별 엑셀 처리 로직 분리 및 상속 구조
- **Modular Frontend**: TableManager, PaginationManager 등 공통 모듈 기반 UI
- **Context Manager**: DB 연결 자동 관리 및 트랜잭션 처리
- **JWT 인증**: 사용자 인증 및 역할 기반 권한 관리 (RBAC)
- **Activity Logging**: 모든 CUD 작업 로그 기록 (IP 추적 포함)

### 기술 스택

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pandas
- **Database**: SQL Server (Azure SQL Database)
- **Authentication**: JWT (HS256), bcrypt
- **Frontend**: Jinja2 Templates, Vanilla JS (ES6+ Modules)
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
```

## 프로젝트 구조

```
WebApp_v2_admin/
├── app.py                      # FastAPI 메인 애플리케이션
├── .env                        # 환경 변수
├── requirements.txt            # Python 패키지 의존성
├── CLAUDE.md                   # 개발 가이드 (이 문서)
├── ARCHITECTURE.md             # 아키텍처 상세 문서
│
├── core/                       # 핵심 유틸리티 및 공통 모듈
│   ├── base_repository.py      # BaseRepository 추상 클래스
│   ├── database.py             # DB 연결 관리 (Context Manager)
│   ├── query_builder.py        # 동적 SQL 쿼리 빌더
│   ├── security.py             # JWT 인증, 비밀번호 해싱
│   └── dependencies.py         # FastAPI 의존성 주입
│
├── repositories/               # 데이터 접근 계층 (11개 Repository)
│   ├── product_repository.py   # Product 테이블 CRUD
│   ├── bom_repository.py       # ProductBOM 테이블 CRUD
│   ├── promotion_expected_repository.py # Promotion/PromotionProduct/ExpectedSales CRUD (예상매출)
│   ├── promotion_target_repository.py   # TargetSalesProduct CRUD (목표매출)
│   └── ...
│
├── routers/                    # API 라우터 (11개 Router)
│   ├── product.py              # Product API (ExcelHandler 사용)
│   ├── bom.py                  # BOM API
│   └── ...
│
├── utils/                      # 공통 유틸리티
│   ├── excel/                  # Excel Handler System
│   │   ├── base_handler.py     # 공통 엑셀 처리 로직 (부모)
│   │   ├── product_handler.py  # 제품 엑셀 처리
│   │   ├── sales_handler.py    # 매출 엑셀 처리
│   │   ├── promotion_expected_handler.py # 예상매출 엑셀 처리 (통합시트/2시트 지원)
│   │   ├── promotion_target_handler.py   # 목표매출 엑셀 처리
│   │   └── ...
│   └── slack_notifier.py       # Slack 알림
│
├── templates/                  # Jinja2 HTML 템플릿
│   ├── base.html               # 기본 레이아웃 (공통 JS 포함)
│   ├── products.html           # 제품 관리 (TableManager 적용)
│   ├── bom.html                # BOM 관리 (TableManager 적용)
│   └── ...
│
├── static/                     # 정적 파일
│   ├── css/
│   │   ├── base.css            # 기본 스타일
│   │   ├── components.css      # 공통 컴포넌트 스타일
│   │   └── pages/              # 페이지별 전용 CSS (신규)
│   │       └── promotions.css
│   └── js/
│       ├── api-client.js       # REST API 래퍼
│       ├── table-manager.js    # 테이블 렌더링/선택 관리
│       ├── pagination-manager.js # 페이지네이션 관리
│       ├── modal-manager.js    # 모달 관리
│       ├── ui-utils.js         # Alert, Confirm 등 UI 유틸
│       └── pages/              # 페이지별 로직 (Orchestrator)
│           ├── products.js
│           ├── bom.js
│           └── ...
│
└── sql/                        # SQL 스크립트
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
모든 CUD 작업은 `ActivityLogRepository`를 통해 DB에 기록됩니다.

## API 엔드포인트 요약
- `/api/auth`: 인증
- `/api/admin`: 관리자 기능
- `/api/products`: 제품 관리
- `/api/bom`: BOM 관리
- `/api/sales`: 매출 관리
- `/api/promotions`: 프로모션 관리
- `/api/channels`: 채널 관리
- `/api/revenue-plan`: 매출 계획
- `/api/system-config`: 시스템 설정

## 새 기능 추가 가이드

1.  **Backend**:
    *   `repositories/`에 Repository 클래스 작성 (`BaseRepository` 상속).
    *   `routers/`에 Router 작성 (`APIRouter` 사용).
    *   필요 시 `utils/excel/`에 Handler 작성.
    *   `app.py`에 라우터 등록.

2.  **Frontend**:
    *   `templates/`에 HTML 작성 (`base.html` 상속). `TableManager` 호환 테이블 구조 사용.
    *   `static/js/pages/`에 JS 작성. `ApiClient`, `TableManager` 등 활용.
    *   필요 시 `static/css/pages/`에 전용 CSS 작성.

## 디버깅

- **Health Check**: `http://localhost:8002/api/health`
- **Backend Log**: `logging` 모듈 사용.
- **Frontend Log**: 브라우저 콘솔 확인 (`api-client.js`가 에러 로깅).
