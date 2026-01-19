"""
Product Repository
- Product 테이블 CRUD 작업
- Brand 조인을 통한 브랜드 정보 포함
"""

from typing import Dict, Any, Optional
from core import BaseRepository, QueryBuilder


class ProductRepository(BaseRepository):
    """Product 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[Product]", id_column="ProductID")

    def get_select_query(self) -> str:
        """Product 조회 쿼리 (Brand 조인 포함)"""
        return """
            SELECT
                p.ProductID, p.BrandID, b.Name as BrandName, b.Title as BrandTitle,
                p.UniqueCode, p.Name, p.TypeERP, p.TypeDB,
                p.BaseBarcode, p.Barcode2, p.SabangnetCode, p.SabangnetUniqueCode,
                p.BundleType, p.CategoryMid, p.CategorySub, p.Status, p.ReleaseDate
            FROM [dbo].[Product] p
            LEFT JOIN [dbo].[Brand] b ON p.BrandID = b.BrandID
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "ProductID": row[0],
            "BrandID": row[1],
            "BrandName": row[2],
            "BrandTitle": row[3],
            "UniqueCode": row[4],
            "Name": row[5],
            "TypeERP": row[6],
            "TypeDB": row[7],
            "BaseBarcode": row[8],
            "Barcode2": row[9],
            "SabangnetCode": row[10],
            "SabangnetUniqueCode": row[11],
            "BundleType": row[12],
            "CategoryMid": row[13],
            "CategorySub": row[14],
            "Status": row[15],
            "ReleaseDate": row[16].isoformat() if row[16] else None
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        Product 전용 필터 로직

        지원하는 필터:
        - brand: Brand.Title로 검색
        - unique_code: UniqueCode LIKE 검색
        - name: Name LIKE 검색
        - bundle_type: BundleType 완전 일치
        """
        # Brand 필터 (Title 기준)
        if filters.get('brand'):
            builder.where("b.Title = ?", filters['brand'])

        # UniqueCode 필터 (LIKE)
        if filters.get('unique_code'):
            builder.where_like("p.UniqueCode", filters['unique_code'])

        # Name 필터 (LIKE)
        if filters.get('name'):
            builder.where_like("p.Name", filters['name'])

        # BundleType 필터 (완전 일치)
        if filters.get('bundle_type'):
            builder.where_equals("p.BundleType", filters['bundle_type'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """Product 전용 QueryBuilder 생성 (Brand 조인 포함)"""
        builder = QueryBuilder("[dbo].[Product] p")

        # Brand 조인 추가
        builder.join("[dbo].[Brand] b", "p.BrandID = b.BrandID", "LEFT JOIN")

        # SELECT 컬럼 설정
        builder.select(
            "p.ProductID", "p.BrandID", "b.Name as BrandName", "b.Title as BrandTitle",
            "p.UniqueCode", "p.Name", "p.TypeERP", "p.TypeDB",
            "p.BaseBarcode", "p.Barcode2", "p.SabangnetCode", "p.SabangnetUniqueCode",
            "p.BundleType", "p.CategoryMid", "p.CategorySub", "p.Status", "p.ReleaseDate"
        )

        # 필터 적용
        if filters:
            self._apply_filters(builder, filters)

        return builder

    def get_bundle_types(self) -> list:
        """BundleType 목록 조회 (메타데이터)"""
        from core import get_db_cursor

        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT DISTINCT BundleType
                FROM [dbo].[Product]
                WHERE BundleType IS NOT NULL AND BundleType != ''
                ORDER BY BundleType
            """)
            return [row[0] for row in cursor.fetchall()]

    def get_unique_codes(self) -> list:
        """UniqueCode 목록 조회 (자동완성용)"""
        from core import get_db_cursor

        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT DISTINCT UniqueCode
                FROM [dbo].[Product]
                WHERE UniqueCode IS NOT NULL AND UniqueCode != ''
                ORDER BY UniqueCode
            """)
            return [row[0] for row in cursor.fetchall()]

    def get_product_names(self) -> list:
        """제품명 목록 조회 (자동완성용)"""
        from core import get_db_cursor

        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT DISTINCT Name
                FROM [dbo].[Product]
                WHERE Name IS NOT NULL AND Name != ''
                ORDER BY Name
            """)
            return [row[0] for row in cursor.fetchall()]

    def get_by_unique_code(self, unique_code: str) -> Optional[Dict[str, Any]]:
        """UniqueCode로 제품 조회"""
        builder = self._build_query_with_filters()
        builder.where("p.UniqueCode = ?", unique_code)
        
        from core import get_db_cursor
        with get_db_cursor(commit=False) as cursor:
            query, params = builder.build()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
