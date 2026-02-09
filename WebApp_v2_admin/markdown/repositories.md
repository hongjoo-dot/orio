# Repositories (`repositories/`)

데이터 접근 계층. 모든 DB 쿼리는 Repository를 통해 실행한다.
`BaseRepository`를 상속하고, SELECT 쿼리와 필터를 커스터마이징하는 방식.

## Repository 작성 템플릿

```python
from core.base_repository import BaseRepository
from core.query_builder import QueryBuilder
from typing import Dict, Any

class NewEntityRepository(BaseRepository):
    def __init__(self):
        super().__init__(
            table_name="[dbo].[TableName]",    # 스키마 + 브라켓 필수
            id_column="TableNameID"             # PK 컬럼
        )

    def get_select_query(self) -> str:
        """SELECT 컬럼 순서 = _row_to_dict 인덱스 순서"""
        return """
            SELECT t.TableNameID, t.Name, t.Status, r.RefName
            FROM [dbo].[TableName] t
            LEFT JOIN [dbo].[RefTable] r ON t.RefID = r.RefID
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        return {
            "TableNameID": row[0],   # SELECT 순서와 정확히 일치
            "Name": row[1],
            "Status": row[2],
            "RefName": row[3],
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict) -> None:
        if filters.get('name'):
            builder.where_like("t.Name", filters['name'])
        if filters.get('status'):
            builder.where_equals("t.Status", filters['status'])

    def _build_query_with_filters(self, filters) -> QueryBuilder:
        """JOIN이 있을 때 오버라이드"""
        builder = QueryBuilder(self.table_name + " t")
        builder.select("t.*", "r.RefName")
        builder.join("[dbo].[RefTable] r", "t.RefID = r.RefID")
        self._apply_filters(builder, filters)
        return builder
```

## 전체 Repository 목록

### 마스터 데이터

| Repository | 테이블 | PK | JOIN | 비고 |
|-----------|--------|-----|------|------|
| `ProductRepository` | `[dbo].[Product]` | ProductID | Brand (LEFT JOIN) | 브랜드명 포함 |
| `BrandRepository` | `[dbo].[Brand]` | BrandID | - | 단순 CRUD |
| `ChannelRepository` | `[dbo].[SalesChannel]` | ChannelID | - | 채널 마스터 |
| `BOMRepository` | `[dbo].[ProductBOM]` | BOMID | Product, Brand (LEFT JOIN) | 제품명/브랜드명 포함 |

### 하위 데이터 (1:N 관계)

| Repository | 테이블 | PK | 상위 엔티티 | 비고 |
|-----------|--------|-----|------------|------|
| `ProductBoxRepository` | `[dbo].[ProductBox]` | ProductBoxID | Product | `get_by_parent_id()` 메서드 |
| `PromotionProductRepository` | `[dbo].[PromotionProduct]` | PromotionProductID | Promotion | 프로모션별 제품 |

### 매출/목표

| Repository | 테이블 | PK | JOIN | 비고 |
|-----------|--------|-----|------|------|
| `SalesRepository` | `[dbo].[Sales]` | SalesID | Product, Brand, Channel | 다중 JOIN |
| `PromotionRepository` | `[dbo].[Promotion]` | PromotionID | - | 캠페인 관리 |
| `TargetBaseRepository` | `[dbo].[TargetBaseProduct]` | TargetBaseProductID | Product, Brand | 기본 목표 |
| `TargetPromotionRepository` | `[dbo].[TargetPromotionProduct]` | TargetPromotionProductID | Promotion, Product | 프로모션 목표 |
| `WithdrawalPlanRepository` | `[dbo].[WithdrawalPlan]` | WithdrawalPlanID | Product, Brand, Channel | 불출 계획 |

### 시스템/관리

| Repository | 테이블 | PK | 비고 |
|-----------|--------|-----|------|
| `UserRepository` | `[dbo].[User]` | UserID | 인증, 비밀번호 검증 |
| `PermissionRepository` | 다중 테이블 | - | Permission, RolePermission, UserPermission |
| `ActivityLogRepository` | `[dbo].[ActivityLog]` | LogID | 감사 로그 |
| `SystemConfigRepository` | `[dbo].[SystemConfig]` | ConfigKey (문자열) | 시스템 설정 |

## BaseRepository 제공 메서드

```python
# 조회
repo.get_list(page=1, limit=20, filters={}, sort_by=None, sort_dir="DESC")
# → {data: [...], total: 150, page: 1, limit: 20, total_pages: 8}

repo.get_by_id(id)           # → Dict 또는 None
repo.exists("Name", "Apple") # → bool
repo.check_duplicate("Name", "Apple", exclude_id=5)  # → bool

# CUD
repo.create({"Name": "A", "BrandID": 1})  # → int (생성된 ID)
repo.update(id, {"Name": "B"})             # → bool
repo.delete(id)                             # → bool
repo.bulk_delete([1, 2, 3])                # → int (삭제 건수)
```

## 특수 Repository 기능

### ProductBoxRepository
```python
# 상위 Product 기준으로 하위 Box 목록 조회
boxes = product_box_repo.get_by_parent_id(product_id)
```

### UserRepository
```python
# 이메일로 사용자 조회 (로그인용)
user = user_repo.get_by_email(email)
# 비밀번호 변경
user_repo.change_password(user_id, hashed_password)
```

### PermissionRepository
```python
# 역할별 권한 조회
permissions = permission_repo.get_role_permissions(role_id)
# 사용자 개별 권한 설정
permission_repo.set_user_permission(user_id, permission_id, "GRANT")
```

### SystemConfigRepository
```python
# 키-값 기반 설정 (PK가 문자열)
config = system_config_repo.get_by_key("SYSTEM_NAME")
system_config_repo.upsert("SYSTEM_NAME", "Orio ERP")
```

## 핵심 규칙

1. **`_row_to_dict()` 인덱스 = `get_select_query()` SELECT 순서** (불일치 시 데이터 꼬임)
2. 테이블명은 항상 `[dbo].[PascalCase]` 브라켓 표기
3. JOIN 있으면 `_build_query_with_filters()` 반드시 오버라이드
4. 필터 값이 None이면 조건 추가하지 않음 (선택적 필터)
5. 정렬 컬럼은 Router에서 화이트리스트로 관리
