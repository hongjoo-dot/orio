# Database (`sql/`)

Azure SQL Server 기반. 스키마 파일: `sql/oriodatabase_schema.sql` (~1,500 LOC)

## 테이블 구조

### 제품 도메인

| 테이블 | PK | 주요 컬럼 | FK |
|--------|-----|----------|-----|
| `[dbo].[Product]` | ProductID | Name, BrandID, Specification, Unit, Status | Brand.BrandID |
| `[dbo].[ProductBox]` | ProductBoxID | ProductID, BoxName, Quantity, Status | Product.ProductID |
| `[dbo].[Brand]` | BrandID | Name, Status | - |
| `[dbo].[ProductBOM]` | BOMID | ProductID, MaterialName, Quantity, Unit | Product.ProductID |

### 매출 도메인

| 테이블 | PK | 주요 컬럼 | FK |
|--------|-----|----------|-----|
| `[dbo].[Sales]` | SalesID | ProductID, ChannelID, Revenue, Quantity, SalesDate | Product, Channel |
| `[dbo].[SalesChannel]` | ChannelID | Name, Type, Status | - |

### 프로모션 도메인

| 테이블 | PK | 주요 컬럼 | FK |
|--------|-----|----------|-----|
| `[dbo].[Promotion]` | PromotionID | Name, StartDate, EndDate, Status | - |
| `[dbo].[PromotionProduct]` | PromotionProductID | PromotionID, ProductID, TargetQuantity | Promotion, Product |

### 목표 도메인

| 테이블 | PK | 주요 컬럼 | FK |
|--------|-----|----------|-----|
| `[dbo].[TargetBaseProduct]` | TargetBaseProductID | ProductID, Year, Month, TargetQuantity | Product |
| `[dbo].[TargetPromotionProduct]` | TargetPromotionProductID | PromotionID, ProductID, TargetQuantity | Promotion, Product |

### 계획 도메인

| 테이블 | PK | 주요 컬럼 | FK |
|--------|-----|----------|-----|
| `[dbo].[WithdrawalPlan]` | WithdrawalPlanID | ProductID, ChannelID, PlanDate, Quantity | Product, Channel |

### 시스템/관리 도메인

| 테이블 | PK | 주요 컬럼 | 비고 |
|--------|-----|----------|------|
| `[dbo].[User]` | UserID | Email, Password, Name, Role, Status | 사용자 인증 |
| `[dbo].[Role]` | RoleID | Name, Description | Admin, Manager, Viewer |
| `[dbo].[Permission]` | PermissionID | Module, Action | Product:CREATE 등 |
| `[dbo].[RolePermission]` | RolePermissionID | RoleID, PermissionID | 역할별 기본 권한 |
| `[dbo].[UserPermission]` | UserPermissionID | UserID, PermissionID, Type | GRANT/DENY (개별) |
| `[dbo].[ActivityLog]` | LogID | UserID, Action, TableName, TargetID, Details, IP, CreatedDate | 감사 로그 |
| `[dbo].[SystemConfig]` | ConfigKey (문자열) | ConfigValue, Description | 시스템 설정 |

---

## DB 접근 패턴

### 1. Context Manager

```python
from core.database import get_db_cursor, get_db_transaction

# 읽기
with get_db_cursor(commit=False) as cursor:
    cursor.execute("SELECT * FROM [dbo].[Product] WHERE ProductID = ?", product_id)
    rows = cursor.fetchall()

# 쓰기
with get_db_cursor(commit=True) as cursor:
    cursor.execute("INSERT INTO [dbo].[Product] (Name) VALUES (?)", name)

# 트랜잭션 (여러 테이블)
with get_db_transaction() as (conn, cursor):
    cursor.execute("INSERT INTO ...")
    cursor.execute("UPDATE ...")
    conn.commit()
```

### 2. 파라미터 바인딩 (필수)

```python
# 올바름 - ? 플레이스홀더
cursor.execute("SELECT * FROM [dbo].[Product] WHERE Name = ?", name)

# 금지 - SQL Injection 위험
cursor.execute(f"SELECT * FROM [dbo].[Product] WHERE Name = '{name}'")
```

### 3. QueryBuilder 활용

```python
builder = QueryBuilder("[dbo].[Product] p")
builder.select("p.*", "b.Name AS BrandName")
builder.join("[dbo].[Brand] b", "p.BrandID = b.BrandID")
builder.where_like("p.Name", search)
builder.where_equals("p.Status", "ACTIVE")
builder.order_by("p.ProductID", "DESC")

query, params = builder.build_paginated(page=1, limit=20)
```

---

## 네이밍 규칙

| 대상 | 규칙 | 예시 |
|------|------|------|
| 테이블 | `[dbo].[PascalCase]` | `[dbo].[Product]` |
| PK 컬럼 | `{엔티티}ID` | `ProductID`, `BrandID` |
| FK 컬럼 | 참조 테이블의 PK명 동일 | `Product.BrandID → Brand.BrandID` |
| 일반 컬럼 | PascalCase | `Name`, `Status`, `CreatedDate` |
| 상태 컬럼 | 문자열 | `'ACTIVE'/'INACTIVE'` 또는 `'YES'/'NO'` |
| 감사 컬럼 | `CreatedDate`, `UpdatedDate` | datetime 타입 |

## 마이그레이션

- `sql/` 폴더에 마이그레이션 스크립트 작성
- 멱등성 보장 (`IF NOT EXISTS` 등)
- 필요한 인덱스 포함

```sql
-- 예시: sql/migration_new_entity.sql
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NewEntity')
BEGIN
    CREATE TABLE [dbo].[NewEntity] (
        NewEntityID INT IDENTITY(1,1) PRIMARY KEY,
        Name NVARCHAR(200) NOT NULL,
        Status NVARCHAR(20) DEFAULT 'ACTIVE',
        CreatedDate DATETIME DEFAULT GETDATE(),
        UpdatedDate DATETIME DEFAULT GETDATE()
    );
    CREATE INDEX IX_NewEntity_Status ON [dbo].[NewEntity](Status);
END
```
