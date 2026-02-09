# Core 모듈 (`core/`)

핵심 인프라 모듈. 데이터베이스 연결, 인증, 쿼리 빌더, 데코레이터 등 전체 시스템의 기반.

## 파일 구조

| 파일 | 역할 | 주요 API |
|------|------|----------|
| `database.py` | DB 연결 관리 | `get_db_cursor()`, `get_db_transaction()` |
| `query_builder.py` | 동적 SQL 생성 | `QueryBuilder`, `build_insert_query()` |
| `base_repository.py` | 추상 Repository | `BaseRepository` (get_list, create, update, delete) |
| `security.py` | JWT + bcrypt | `create_access_token()`, `hash_password()` |
| `dependencies.py` | FastAPI DI + RBAC | `require_permission()`, `CurrentUser` |
| `activity_decorator.py` | CUD 활동 로깅 | `@log_activity`, `@log_delete`, `@log_bulk_delete` |
| `decorators.py` | 유틸 데코레이터 | `@transactional`, `@retry_on_failure` |
| `exceptions.py` | 예외 계층 | `BaseRepositoryError` 및 하위 클래스 |
| `filter_builder.py` | 고급 필터 | `AdvancedFilterBuilder`, `FilterGroup` |

---

## 1. database.py - DB 연결 관리

Context Manager 패턴으로 연결/커서 자동 관리.

```python
# 읽기 전용
with get_db_cursor(commit=False) as cursor:
    cursor.execute("SELECT * FROM [dbo].[Product] WHERE ProductID = ?", product_id)
    row = cursor.fetchone()

# 쓰기 (자동 커밋)
with get_db_cursor(commit=True) as cursor:
    cursor.execute("INSERT INTO [dbo].[Product] (Name) VALUES (?)", name)

# 트랜잭션 (여러 테이블 동시)
with get_db_transaction() as (conn, cursor):
    cursor.execute("INSERT INTO Table1 ...")
    cursor.execute("INSERT INTO Table2 ...")
    conn.commit()
```

- 설정: `.env` 파일에서 DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD 로드
- 드라이버: ODBC Driver 17 for SQL Server
- 타임아웃: 600초 (대용량 작업 고려)
- 예외 시 자동 롤백 + 연결 해제

---

## 2. query_builder.py - 동적 SQL 빌더

Fluent API로 SQL 생성. 파라미터 바인딩으로 SQL Injection 방지.

```python
builder = QueryBuilder("[dbo].[Product] p")
builder.select("p.*", "b.Name AS BrandName")
builder.join("[dbo].[Brand] b", "p.BrandID = b.BrandID")
builder.where_like("p.Name", search_term)
builder.where_equals("p.Status", "ACTIVE")
builder.order_by("p.ProductID", "DESC")

# 페이지네이션 쿼리 (OFFSET/FETCH)
query, params = builder.build_paginated(page=1, limit=20)
count_query, count_params = builder.build_count()
```

**헬퍼 함수:**
```python
query, params = build_insert_query("[dbo].[Product]", {"Name": "A", "BrandID": 1})
# → INSERT INTO [dbo].[Product] ([Name], [BrandID]) VALUES (?, ?)

query, params = build_update_query("[dbo].[Product]", {"Name": "B"}, "ProductID", 1)
# → UPDATE [dbo].[Product] SET [Name] = ? WHERE [ProductID] = ?
```

---

## 3. base_repository.py - 추상 Repository

모든 Repository의 부모 클래스. Template Method 패턴.

```python
class BaseRepository:
    def __init__(self, table_name, id_column): ...

    # 상속 시 필수 구현
    def get_select_query(self) -> str: ...       # SELECT 쿼리 (JOIN 포함)
    def _row_to_dict(self, row) -> Dict: ...     # row 인덱스 → dict 변환
    def _apply_filters(self, builder, filters): ... # 필터 조건 적용

    # 기본 제공 메서드
    def get_list(page, limit, filters, sort_by, sort_dir) -> Dict  # 페이지네이션 목록
    def get_by_id(id) -> Optional[Dict]
    def create(data: Dict) -> int               # @@IDENTITY 반환
    def update(id, data: Dict) -> bool
    def delete(id) -> bool
    def bulk_delete(ids: List) -> int            # 삭제 건수 반환
    def exists(column, value) -> bool
    def check_duplicate(column, value, exclude_id=None) -> bool
```

**핵심 규칙:**
- `_row_to_dict()`의 인덱스 순서 = `get_select_query()`의 SELECT 컬럼 순서
- 정렬 컬럼은 화이트리스트로 관리 (SQL Injection 방지)
- `get_list()` 반환: `{data, total, page, limit, total_pages}`

---

## 4. security.py - 인증

```python
hashed = hash_password("plaintext")          # bcrypt 12 rounds
is_valid = verify_password("plaintext", hashed)

token = create_access_token(user_id=1, email="a@b.com", role="Admin")
payload = decode_token(token)                # {user_id, email, role, exp, iat}
```

- JWT: HS256 알고리즘, 8시간 만료
- 설정: `.env`의 JWT_SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS

---

## 5. dependencies.py - 인증/권한 의존성

```python
# CurrentUser 클래스
class CurrentUser:
    user_id: int
    email: str
    role: str
    is_admin -> bool     # role == "Admin"
    is_manager -> bool   # role == "Manager"
    can_write -> bool    # Admin 또는 Manager

# 사용법 (Router에서)
user = Depends(require_permission("Product", "CREATE"))
user = Depends(require_permission("Product", "READ"))

# 페이지 보호 (HTML)
redirect = Depends(require_login_for_page)
```

**권한 체크 순서:**
1. UserPermission에서 DENY → 즉시 거부
2. UserPermission에서 GRANT → 허용
3. RolePermission에서 확인 → 허용/거부

---

## 6. activity_decorator.py - 활동 로깅

CUD 작업에 **필수** 적용. ActivityLog 테이블에 기록.

```python
# CREATE/UPDATE
@router.post("")
@log_activity("CREATE", "Product", id_key="ProductID")
async def create_product(data, request: Request, user: CurrentUser = Depends(...)):
    product_id = repo.create(data.dict())
    return {"ProductID": product_id, "message": "생성되었습니다"}
    #        ↑ id_key와 일치 필수

# DELETE
@router.delete("/{product_id}")
@log_delete("Product", id_param="product_id")
async def delete_product(product_id: int, request: Request, user = Depends(...)):
    ...

# BULK DELETE
@router.post("/bulk-delete")
@log_bulk_delete("Product")
async def bulk_delete(body: BulkDeleteRequest, request: Request, user = Depends(...)):
    ...
    return {"deleted_ids": body.ids, ...}  # deleted_ids 필수
```

**필수 조건:**
- 함수 파라미터에 `request: Request` 필수
- 함수 파라미터에 `user: CurrentUser` 필수 (변수명: user, admin, current_user)
- `@log_activity`의 `id_key` = 반환 dict의 키
- `@log_delete`의 `id_param` = 경로 파라미터명
- `@log_bulk_delete` 반환에 `deleted_ids` 키 필수

---

## 7. decorators.py - 유틸리티 데코레이터

```python
@transactional           # 트랜잭션 래핑 (자동 커밋/롤백)
@with_error_handling(default_return=[], log_error=True)  # 에러 시 기본값 반환
@retry_on_failure(max_retries=3, delay=1.0)              # 재시도
@log_execution_time      # 실행 시간 로깅
@validate_input(price=is_positive)                       # 입력 검증
```

---

## 8. exceptions.py - 예외 계층

```
BaseRepositoryError (message, details)
├── DatabaseConnectionError    # DB 연결 실패
├── RecordNotFoundError        # 레코드 없음
├── DuplicateRecordError       # 중복
├── ValidationError            # 검증 실패
├── ForeignKeyError            # FK 제약 위반
├── TransactionError           # 트랜잭션 실패
├── QueryBuildError            # 쿼리 빌드 오류
├── PermissionError            # 권한 부족
└── BusinessLogicError         # 비즈니스 로직 오류
```

에러 코드: 1xxx(일반), 2xxx(DB), 3xxx(레코드), 4xxx(인증), 5xxx(비즈니스)

---

## 9. filter_builder.py - 고급 필터

```python
builder = AdvancedFilterBuilder()
builder.add_equals("Status", "ACTIVE")
builder.add_like("Name", "Apple")
builder.add_between("Price", 1000, 5000)
builder.add_in("CategoryID", [1, 2, 3])

# OR 조건
or_group = FilterGroup("OR")
or_group.add(FilterCondition("Status", FilterOperator.EQUALS, "Active"))
or_group.add(FilterCondition("Status", FilterOperator.EQUALS, "Pending"))
builder.add(or_group)

sql, params = builder.to_sql()
```
