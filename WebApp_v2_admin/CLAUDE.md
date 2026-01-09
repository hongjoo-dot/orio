# CLAUDE.md - WebApp_v2_admin

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 개요

FastAPI 기반의 ERP 관리 시스템입니다. Repository 패턴을 적용하여 데이터 접근 로직과 비즈니스 로직을 분리했으며, JWT 인증 및 활동 로깅 기능을 포함합니다.

### 주요 특징

- **Repository Pattern**: 데이터 접근 계층 분리
- **Query Builder**: 동적 SQL 쿼리 생성 및 SQL Injection 방지
- **Context Manager**: DB 연결 자동 관리 및 트랜잭션 처리
- **JWT 인증**: 사용자 인증 및 역할 기반 권한 관리 (RBAC)
- **Activity Logging**: 모든 CUD 작업 로그 기록 (IP 추적 포함)
- **Master-Detail UI**: 직관적인 데이터 관리 인터페이스

### 기술 스택

- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **Database**: SQL Server (Azure SQL Database)
- **Authentication**: JWT (HS256), bcrypt
- **Frontend**: Jinja2 Templates, Vanilla JS
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
│   ├── __init__.py
│   ├── base_repository.py      # BaseRepository 추상 클래스
│   ├── database.py             # DB 연결 관리 (Context Manager)
│   ├── query_builder.py        # 동적 SQL 쿼리 빌더
│   ├── filter_builder.py       # 필터 조건 빌더
│   ├── exceptions.py           # 커스텀 예외 및 에러 코드
│   ├── decorators.py           # 데코레이터 (트랜잭션, 로깅, 재시도)
│   ├── security.py             # JWT 인증, 비밀번호 해싱
│   └── dependencies.py         # FastAPI 의존성 주입 (인증, 권한)
│
├── repositories/               # 데이터 접근 계층 (10개 Repository)
│   ├── __init__.py
│   ├── product_repository.py   # Product 테이블 CRUD
│   ├── product_box_repository.py # ProductBox 테이블 CRUD
│   ├── brand_repository.py     # Brand 테이블 CRUD
│   ├── channel_repository.py   # Channel + ChannelDetail CRUD
│   ├── bom_repository.py       # ProductBOM 테이블 CRUD
│   ├── sales_repository.py     # ERPSales 테이블 CRUD
│   ├── user_repository.py      # User + UserRole CRUD
│   ├── activity_log_repository.py # ActivityLog 테이블
│   ├── system_config_repository.py # SystemConfig + History CRUD
│   └── revenue_plan_repository.py # RevenuePlan 테이블 CRUD
│
├── routers/                    # API 라우터 (11개 Router)
│   ├── __init__.py
│   ├── pages.py                # HTML 페이지 라우팅
│   ├── auth.py                 # 인증 API (로그인/로그아웃)
│   ├── admin.py                # 관리자 API (사용자/역할/로그)
│   ├── product.py              # Product + ProductBox API
│   ├── brand.py                # Brand API
│   ├── channel.py              # Channel + ChannelDetail API
│   ├── bom.py                  # BOM API
│   ├── sales.py                # ERPSales API + Excel 업로드
│   ├── system_config.py        # SystemConfig API
│   └── revenue_plan.py         # RevenuePlan API
│
├── templates/                  # Jinja2 HTML 템플릿 (13개)
│   ├── base.html               # 기본 레이아웃
│   ├── login.html              # 로그인 페이지
│   ├── dashboard.html          # 대시보드
│   ├── products.html           # 제품 관리 (Master-Detail)
│   ├── channels.html           # 채널 관리 (Master-Detail)
│   ├── bom.html                # BOM 관리
│   ├── sales.html              # 매출 관리
│   ├── revenue_plan.html       # 매출 계획
│   ├── admin.html              # 사용자 관리 (Admin 전용)
│   ├── activity_log.html       # 활동 로그 (Admin 전용)
│   ├── system_config.html      # 시스템 설정 (Admin 전용)
│   └── components/             # 재사용 가능 컴포넌트
│       ├── sidebar.html        # 사이드바 네비게이션
│       └── search-filter.html  # 검색/필터 컴포넌트
│
├── static/                     # 정적 파일
│   ├── css/
│   │   ├── base.css            # CSS 변수, 기본 스타일
│   │   ├── layout.css          # 그리드, 레이아웃
│   │   └── components.css      # 버튼, 테이블, 모달 등
│   └── js/
│       ├── api-client.js       # REST API 래퍼
│       ├── modal-manager.js    # 모달 다이얼로그
│       ├── pagination-manager.js # 페이지네이션
│       └── table-manager.js    # 동적 테이블
│
├── sql/                        # SQL 스크립트
│   ├── create_admin_tables.sql # User, Role, ActivityLog, SystemConfig
│   ├── create_revenue_plan_table.sql # RevenuePlan 테이블
│   └── sp_merge_erpsales_to_orders_fixed.sql # ERP 동기화 SP
│
├── scripts/                    # 유틸리티 스크립트
│   └── upload_revenue_plan.py  # 매출 계획 일괄 업로드
│
└── utils/                      # 공통 유틸리티
    └── slack_notifier.py       # Slack 알림 전송
```

## 아키텍처 패턴

### 1. Repository Pattern

모든 데이터 접근은 Repository를 통해 이루어집니다.

#### BaseRepository 추상 클래스

```python
from abc import ABC, abstractmethod

class BaseRepository(ABC):
    def __init__(self, table_name: str, id_column: str):
        self.table_name = table_name
        self.id_column = id_column

    # 필수 구현 메서드
    @abstractmethod
    def _row_to_dict(self, row) -> Dict:
        """DB Row를 Dictionary로 변환"""
        pass

    @abstractmethod
    def get_select_query(self) -> str:
        """SELECT 쿼리 반환"""
        pass

    # 공통 메서드 (자동 제공)
    def get_list(self, page=1, limit=20, filters=None, order_by=None, order_dir='ASC') -> Dict
    def get_by_id(self, id) -> Dict
    def create(self, data: Dict) -> int
    def update(self, id, data: Dict) -> bool
    def delete(self, id) -> bool
    def bulk_delete(self, ids: List[int]) -> int
    def exists(self, id) -> bool
    def check_duplicate(self, column, value) -> bool
```

#### Repository 구현 예시

```python
# repositories/product_repository.py
from core.base_repository import BaseRepository

class ProductRepository(BaseRepository):
    def __init__(self):
        super().__init__(
            table_name="[dbo].[Product]",
            id_column="ProductID"
        )

    def _row_to_dict(self, row) -> Dict:
        return {
            "ProductID": row[0],
            "BrandID": row[1],
            "Name": row[2],
            "UniqueCode": row[3],
        }

    def get_select_query(self) -> str:
        return """
            SELECT p.ProductID, p.BrandID, p.Name, p.UniqueCode,
                   b.Title as BrandName
            FROM [dbo].[Product] p
            LEFT JOIN [dbo].[Brand] b ON p.BrandID = b.BrandID
        """

    def _apply_filters(self, builder, filters: Dict):
        """커스텀 필터 적용"""
        if filters.get('brand'):
            builder.where_equals('b.Title', filters['brand'])
        if filters.get('name'):
            builder.where_like('p.Name', filters['name'])
```

#### Repository 사용법

```python
from repositories.product_repository import ProductRepository

product_repo = ProductRepository()

# 목록 조회 (페이지네이션 + 필터)
result = product_repo.get_list(
    page=1,
    limit=20,
    filters={'brand': 'Samsung', 'name': 'Phone'},
    order_by='ProductID',
    order_dir='DESC'
)
# 반환: {'data': [...], 'total': 100, 'page': 1, 'limit': 20, 'total_pages': 5}

# 단일 조회
product = product_repo.get_by_id(123)

# 생성
new_id = product_repo.create({
    'Name': 'New Product',
    'BrandID': 1,
    'UniqueCode': 'PROD-001'
})

# 수정
success = product_repo.update(123, {'Name': 'Updated Name'})

# 삭제
success = product_repo.delete(123)

# 일괄 삭제 (배치 처리)
deleted_count = product_repo.bulk_delete([1, 2, 3, 4, 5])
```

### 2. Query Builder Pattern

동적 SQL 쿼리 생성 및 SQL Injection 방지를 위한 패턴입니다.

```python
from core.query_builder import QueryBuilder

builder = QueryBuilder("[dbo].[Product]")
builder.select("ProductID", "Name", "BrandID")
builder.where_equals("BrandID", 1)
builder.where_like("Name", "Samsung")
builder.where_in("TypeERP", [1, 2, 3])
builder.where_between("CreatedDate", "2024-01-01", "2024-12-31")
builder.order_by("Name", "ASC")

# 페이지네이션 쿼리 생성
query, params = builder.build_paginated(page=1, limit=20)
```

#### 헬퍼 함수

```python
from core.query_builder import (
    build_insert_query,
    build_update_query,
    build_delete_query
)

# INSERT (SQL 예약어 자동 대괄호 처리)
query, params = build_insert_query("[dbo].[Channel]", {
    "Name": "New Channel",
    "Group": "A",      # → [Group]
    "Type": "Online"   # → [Type]
})

# UPDATE
query, params = build_update_query(
    "[dbo].[Product]", "ProductID", 123,
    {"Name": "Updated", "BrandID": 2}
)

# DELETE (배치)
query, params = build_delete_query(
    "[dbo].[Product]", "ProductID", [1, 2, 3]
)
```

### 3. Context Manager Pattern (DB 연결)

```python
from core.database import get_db_cursor

# 읽기 전용 (commit=False) - 자동 rollback
with get_db_cursor(commit=False) as cursor:
    cursor.execute("SELECT * FROM [dbo].[Product]")
    rows = cursor.fetchall()

# 쓰기 작업 (commit=True) - 성공 시 commit, 실패 시 rollback
with get_db_cursor(commit=True) as cursor:
    cursor.execute(
        "INSERT INTO [dbo].[Product] (Name) VALUES (?)",
        "Test Product"
    )
    cursor.execute("SELECT @@IDENTITY")
    new_id = cursor.fetchone()[0]
```

### 4. Master-Detail UI Pattern

```
┌─────────────────────────────────────────────┐
│ 검색 필터 (전체 너비)                        │
├─────────────────┬───────────────────────────┤
│ Master (50%)    │ Detail (50%)              │
│                 │                           │
│ - 목록 표시     │ - Master 선택 시 표시     │
│ - 페이지네이션  │ - 연관 데이터             │
│ - 체크박스 선택 │ - CRUD 가능               │
│ - 일괄 작업     │                           │
└─────────────────┴───────────────────────────┘
```

**적용 페이지:**
- Products: Product ↔ ProductBox
- Channels: Channel ↔ ChannelDetail
- BOM: Parent Products ↔ Child Products

## 인증 및 권한

### 역할 기반 접근 제어 (RBAC)

| 역할 | 권한 |
|------|------|
| **Admin** | 전체 접근 - 모든 CRUD, 사용자 관리, 시스템 설정 |
| **Manager** | CRUD 가능, 제한된 관리 기능 |
| **Viewer** | 읽기 전용 - 검색, 필터, 조회만 가능 |

### JWT 인증

```python
from core.security import create_access_token, verify_password, hash_password

# 비밀번호 해싱 (bcrypt, 12 rounds)
hashed = hash_password("plain_password")

# 비밀번호 검증
if verify_password("plain_password", hashed):
    # 토큰 생성 (8시간 유효)
    token = create_access_token(
        user_id=1,
        email="user@company.com",
        role="Admin"
    )
```

### 보호된 라우트

```python
from fastapi import Depends
from core.dependencies import (
    get_current_user,
    require_admin,
    require_write_permission,
    require_roles
)

@router.get("/protected")
async def protected_route(current_user: CurrentUser = Depends(get_current_user)):
    """로그인 필요"""
    return {"user": current_user.email}

@router.post("/admin-only")
async def admin_route(current_user: CurrentUser = Depends(require_admin)):
    """관리자 전용"""
    return {"message": "Admin access"}

@router.put("/write-action")
async def write_route(current_user: CurrentUser = Depends(require_write_permission)):
    """Admin 또는 Manager만 가능"""
    return {"can_write": current_user.can_write}
```

### CurrentUser 객체

```python
class CurrentUser:
    user_id: int
    email: str
    role: str

    @property
    def is_admin(self) -> bool
    @property
    def is_manager(self) -> bool
    @property
    def is_viewer(self) -> bool
    @property
    def can_write(self) -> bool  # Admin or Manager
```

## 활동 로깅

모든 CUD 작업은 ActivityLog에 자동 기록됩니다:

```python
from repositories.activity_log_repository import ActivityLogRepository

log_repo = ActivityLogRepository()

# 활동 기록
log_repo.log_action(
    user_id=current_user.user_id,
    action_type="CREATE",  # CREATE, UPDATE, DELETE, BULK_DELETE, LOGIN, LOGOUT 등
    target_table="Product",
    target_id=new_id,
    details={"Name": "New Product"},
    ip_address=request.client.host
)
```

**기록되는 액션 타입:**
- `CREATE`, `UPDATE`, `DELETE`, `BULK_DELETE`
- `LOGIN`, `LOGOUT`, `LOGIN_FAILED`
- `PASSWORD_CHANGE`, `ROLE_CHANGE`

## API 엔드포인트

### 인증 API (`/api/auth`)

| Method | Endpoint | Auth | 설명 |
|--------|----------|------|------|
| POST | `/login` | - | JWT 토큰 발급 |
| POST | `/logout` | Required | 세션 종료 |
| GET | `/me` | Required | 현재 사용자 정보 |
| PUT | `/password` | Required | 비밀번호 변경 |

### 관리자 API (`/api/admin`)

| Method | Endpoint | Auth | 설명 |
|--------|----------|------|------|
| GET | `/users` | Admin | 사용자 목록 |
| POST | `/users` | Admin | 사용자 생성 |
| PUT | `/users/{id}` | Admin | 사용자 수정 |
| DELETE | `/users/{id}` | Admin | 사용자 비활성화 |
| PUT | `/users/{id}/role` | Admin | 역할 변경 |
| POST | `/users/{id}/password-reset` | Admin | 비밀번호 초기화 |
| GET | `/activity-log` | Admin | 활동 로그 조회 |
| GET | `/roles` | Admin | 역할 목록 |

### Product API (`/api/products`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | 제품 목록 (필터: brand, unique_code, name, bundle_type) |
| GET | `/{id}` | 제품 상세 |
| POST | `/` | 제품 생성 |
| POST | `/integrated` | 제품+박스 통합 생성 (Merge) |
| PUT | `/{id}` | 제품 수정 |
| DELETE | `/{id}` | 제품 삭제 |
| POST | `/bulk-delete` | 일괄 삭제 |

### Channel API (`/api/channels`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | 채널 목록 |
| POST | `/` | 채널 생성 |
| POST | `/integrated` | 채널+상세 통합 생성 |
| PUT | `/{id}` | 채널 수정 |
| DELETE | `/{id}` | 채널 삭제 |

### Sales API (`/api/erpsales`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | ERPSales 목록 |
| POST | `/` | ERPSales 생성 |
| PUT | `/{id}` | ERPSales 수정 |
| DELETE | `/{id}` | ERPSales 삭제 |
| POST | `/upload` | Excel 파일 업로드 (MERGE) |
| POST | `/sync-to-orders` | OrdersRealtime 동기화 |
| POST | `/export` | Excel 내보내기 |

### SystemConfig API (`/api/system-config`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | 전체 설정 목록 |
| GET | `/{id}` | 설정 상세 |
| POST | `/` | 설정 추가 |
| PUT | `/{id}` | 설정 수정 |
| DELETE | `/{id}` | 설정 삭제 |
| GET | `/{id}/history` | 변경 이력 조회 |

### RevenuePlan API (`/api/revenue-plan`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | 매출 계획 목록 |
| POST | `/` | 매출 계획 생성 |
| PUT | `/{id}` | 매출 계획 수정 |
| DELETE | `/{id}` | 매출 계획 삭제 |

### 페이지 라우트

| Route | Template | Auth | 설명 |
|-------|----------|------|------|
| `/login` | login.html | - | 로그인 페이지 |
| `/` | dashboard.html | Required | 대시보드 |
| `/products` | products.html | Required | 제품 관리 |
| `/channels` | channels.html | Required | 채널 관리 |
| `/bom` | bom.html | Required | BOM 관리 |
| `/sales` | sales.html | Required | 매출 관리 |
| `/revenue-plan` | revenue_plan.html | Required | 매출 계획 |
| `/admin/users` | admin.html | Admin | 사용자 관리 |
| `/admin/activity-log` | activity_log.html | Admin | 활동 로그 |
| `/admin/system-config` | system_config.html | Admin | 시스템 설정 |

## 새 기능 추가 방법

### 1. Repository 작성

```python
# repositories/new_repository.py
from core.base_repository import BaseRepository

class NewRepository(BaseRepository):
    def __init__(self):
        super().__init__(
            table_name="[dbo].[NewTable]",
            id_column="ID"
        )

    def _row_to_dict(self, row):
        return {
            "ID": row[0],
            "Name": row[1],
            "CreatedDate": row[2]
        }

    def get_select_query(self):
        return "SELECT ID, Name, CreatedDate FROM [dbo].[NewTable]"
```

### 2. Router 작성

```python
# routers/new.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from repositories.new_repository import NewRepository
from repositories.activity_log_repository import ActivityLogRepository
from core.dependencies import get_current_user, CurrentUser

router = APIRouter(prefix="/api/new", tags=["New"])
new_repo = NewRepository()
log_repo = ActivityLogRepository()

class NewCreate(BaseModel):
    Name: str

@router.get("")
async def get_list(page: int = 1, limit: int = 20):
    return new_repo.get_list(page=page, limit=limit)

@router.post("")
async def create(
    data: NewCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    new_id = new_repo.create(data.dict())
    log_repo.log_action(
        user_id=current_user.user_id,
        action_type="CREATE",
        target_table="NewTable",
        target_id=new_id,
        details=data.dict()
    )
    return {"id": new_id}
```

### 3. app.py에 라우터 등록

```python
from routers import new
app.include_router(new.router)
```

### 4. 템플릿 작성

```html
<!-- templates/new.html -->
{% extends "base.html" %}
{% block content %}
<div class="container">
    <h1>New Management</h1>
    <!-- 테이블 또는 Master-Detail 구조 -->
</div>
{% endblock %}
```

## 데코레이터

```python
from core.decorators import (
    transactional,           # 트랜잭션 래핑
    with_error_handling,     # 에러 처리 + 기본값 반환
    retry_on_failure,        # 재시도 로직
    log_execution_time,      # 실행 시간 측정
    validate_input           # 입력 검증
)

@transactional
def create_with_transaction(data):
    # 자동 commit/rollback
    pass

@retry_on_failure(max_retries=3, delay=1)
def call_external_api():
    # 실패 시 재시도
    pass
```

## 예외 처리

```python
from core.exceptions import (
    RecordNotFoundError,
    DuplicateRecordError,
    ValidationError,
    PermissionError,
    ErrorCode
)

# 사용 예시
if not record:
    raise RecordNotFoundError(f"ID {id} not found")

# 에러 코드 참조
# 1xxx: 일반 에러
# 2xxx: 데이터베이스 에러
# 3xxx: 레코드 에러
# 4xxx: 인증 에러
# 5xxx: 비즈니스 로직 에러
```

## 디버깅

### Health Check

```bash
curl http://localhost:8002/api/health
# 응답: {"status": "healthy", "version": "2.0.0", "database": {...}}
```

### 백엔드 로그

```python
import logging
logging.info(f"제품 생성: ID={new_id}")
logging.error(f"에러 발생: {e}", exc_info=True)
```

### 프론트엔드 디버그

```javascript
// api-client.js에서 자동 로깅
console.log('API Response:', response);
console.error('API Error:', error);
```

## 참고 문서

- **ARCHITECTURE.md**: WebApp 아키텍처 상세 문서
- **sql/create_admin_tables.sql**: 관리 테이블 스키마
- **../DATA_PIPELINE_ARCHITECTURE.md**: 데이터 파이프라인 아키텍처
- **API 문서**: http://localhost:8002/docs (Swagger UI)
