# WebApp_v2_admin - 프로젝트 개요

## 한줄 요약
FastAPI 기반 ERP 관리 시스템. Repository 패턴 + 커스텀 QueryBuilder로 SQL Server에 접근하며, Vanilla JS 모듈 기반 다크 테마 프론트엔드를 제공한다.

## 기술 스택

| 계층 | 기술 |
|------|------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Database | SQL Server (Azure SQL), ODBC Driver 17 |
| 인증 | JWT (HS256), bcrypt (12 rounds) |
| Frontend | Jinja2 Templates, Vanilla JS (ES6+), CSS Variables |
| 데이터 처리 | Pandas (Excel import/export) |
| 포트 | 8002 |

## 디렉토리 구조

```
WebApp_v2_admin/
├── app.py                        # FastAPI 진입점
├── .env                          # 환경변수 (DB, JWT, Azure Blob)
│
├── core/                         # 핵심 인프라 (~1,800 LOC)
│   ├── database.py               # DB 연결 (Context Manager)
│   ├── query_builder.py          # 동적 SQL 빌더
│   ├── base_repository.py        # 추상 Repository
│   ├── security.py               # JWT + bcrypt
│   ├── dependencies.py           # FastAPI DI + RBAC
│   ├── activity_decorator.py     # CUD 활동 로깅 데코레이터
│   ├── decorators.py             # 유틸 데코레이터 (트랜잭션, 재시도 등)
│   ├── exceptions.py             # 커스텀 예외 계층
│   └── filter_builder.py         # 고급 필터 (AND/OR 조합)
│
├── repositories/                 # 데이터 접근 계층 (~3,900 LOC, 15개)
│   ├── product_repository.py     # 제품 (Brand JOIN)
│   ├── product_box_repository.py # 제품 박스 (Product 하위)
│   ├── bom_repository.py         # BOM
│   ├── brand_repository.py       # 브랜드
│   ├── channel_repository.py     # 채널
│   ├── sales_repository.py       # 매출
│   ├── promotion_repository.py   # 프로모션
│   ├── promotion_product_repo.py # 프로모션 제품 (하위)
│   ├── target_base_repository.py # 목표 (기본)
│   ├── target_promotion_repo.py  # 목표 (프로모션)
│   ├── withdrawal_plan_repo.py   # 불출 계획
│   ├── user_repository.py        # 사용자
│   ├── permission_repository.py  # 권한 (RBAC)
│   ├── activity_log_repository.py# 활동 로그
│   └── system_config_repository.py# 시스템 설정
│
├── routers/                      # API 엔드포인트 (~7,400 LOC, 13개)
│   ├── pages.py                  # HTML 페이지 라우팅
│   ├── auth.py                   # 인증 (로그인/로그아웃/비밀번호)
│   ├── admin.py                  # 관리자 (사용자/권한)
│   ├── product.py                # 제품 + ProductBox 서브라우터
│   ├── bom.py                    # BOM
│   ├── brand.py                  # 브랜드
│   ├── channel.py                # 채널 + ChannelDetail 서브라우터
│   ├── sales.py                  # 매출
│   ├── target.py                 # 목표 (기본 + 프로모션)
│   ├── promotion.py              # 프로모션 + Product 서브라우터
│   ├── withdrawal_plan.py        # 불출 계획
│   ├── utility.py                # 유틸리티 (엑셀 다운로드 등)
│   └── system_config.py          # 시스템 설정
│
├── utils/                        # 유틸리티
│   ├── excel/                    # Excel Handler System
│   │   ├── base_handler.py       # 공통 엑셀 처리 (부모)
│   │   ├── product_handler.py    # 제품 엑셀
│   │   └── sales_handler.py      # 매출 엑셀
│   └── slack_notifier.py         # Slack 알림
│
├── templates/                    # Jinja2 HTML (17개)
│   ├── base.html                 # 마스터 레이아웃
│   ├── components/sidebar.html   # 사이드바 네비게이션
│   └── {page}.html               # 각 페이지 템플릿
│
├── static/
│   ├── css/                      # 다크 테마 CSS (~1,030 LOC)
│   │   ├── base.css              # CSS 변수 + 기본 스타일
│   │   ├── layout.css            # 레이아웃
│   │   └── components.css        # 컴포넌트
│   └── js/                       # Vanilla JS 모듈 (~5,400 LOC)
│       ├── api-client.js         # REST API 래퍼 (JWT 자동)
│       ├── table-manager.js      # 테이블 렌더링/선택/정렬
│       ├── pagination-manager.js # 페이지네이션
│       ├── modal-manager.js      # 모달 관리
│       ├── ui-utils.js           # showAlert(), showConfirm()
│       └── pages/                # 페이지별 Orchestrator
│
└── sql/
    └── oriodatabase_schema.sql   # DB 스키마 (~1,500 LOC)
```

## 핵심 아키텍처 패턴

1. **Repository Pattern**: Router → Repository → QueryBuilder → Database
2. **Master-Detail UI**: 좌측 목록 + 우측 상세 (Products/Box, Channels/Detail)
3. **RBAC**: Permission → RolePermission → UserPermission (DENY 우선)
4. **Activity Logging**: `@log_activity`, `@log_delete`, `@log_bulk_delete` 데코레이터
5. **Modular Frontend**: ApiClient + TableManager + PaginationManager + ModalManager

## 데이터 흐름

```
[사용자] → HTML Page → JS Orchestrator → ApiClient
    → FastAPI Router (@log_activity, require_permission)
    → Repository (BaseRepository 상속)
    → QueryBuilder (파라미터 바인딩)
    → SQL Server
```

## 새 기능 추가 시 필수 파일

| 생성 | 수정 |
|------|------|
| `repositories/{entity}_repository.py` | `app.py` (라우터 등록) |
| `routers/{entity}.py` | `routers/pages.py` (페이지 라우트) |
| `templates/{entity}.html` | `templates/components/sidebar.html` (메뉴) |
| `static/js/pages/{entity}.js` | |

## 네이밍 규칙

| 대상 | 규칙 | 예시 |
|------|------|------|
| API 경로 | `/api/{복수형-케밥}` | `/api/products` |
| Python 파일/함수 | snake_case | `product_repository.py` |
| Python 클래스 | PascalCase | `ProductRepository` |
| JS 함수 | camelCase | `loadProducts()` |
| DB 테이블/컬럼 | `[dbo].[PascalCase]` | `[dbo].[Product]` |
| HTML id | camelCase | `filterName` |
| CSS 클래스 | kebab-case | `.btn-primary` |
