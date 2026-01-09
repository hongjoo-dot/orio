"""
Sales (ERPSales) Repository
- ERPSales 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional
from core import BaseRepository, QueryBuilder


class SalesRepository(BaseRepository):
    """ERPSales 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[ERPSales]", id_column="IDX")

    def get_select_query(self) -> str:
        """ERPSales 조회 쿼리 (Brand 조인 포함)"""
        return """
            SELECT
                e.IDX, e.[DATE], e.BRAND, e.BrandID, b.Title as BrandTitle,
                e.ProductID, e.PRODUCT_NAME, e.ERPCode,
                e.Quantity, e.UnitPrice, e.TaxableAmount,
                e.ChannelID, e.ChannelName, e.ChannelDetailID, e.ChannelDetailName, e.Owner
            FROM [dbo].[ERPSales] e
            LEFT JOIN [dbo].[Brand] b ON e.BrandID = b.BrandID
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "IDX": row[0],
            "DATE": row[1].strftime('%Y-%m-%d') if row[1] else None,
            "BRAND": row[2],
            "BrandID": row[3],
            "BrandTitle": row[4],
            "ProductID": row[5],
            "PRODUCT_NAME": row[6],
            "ERPCode": row[7],
            "Quantity": float(row[8]) if row[8] else 0,
            "UnitPrice": float(row[9]) if row[9] else 0,
            "TaxableAmount": float(row[10]) if row[10] else 0,
            "ChannelID": row[11],
            "ChannelName": row[12],
            "ChannelDetailID": row[13],
            "ChannelDetailName": row[14],
            "Owner": row[15]
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        Sales 전용 필터 로직

        지원하는 필터:
        - brand: Brand.Title LIKE 검색
        - product_name: PRODUCT_NAME LIKE 검색
        - erp_code: ERPCode LIKE 검색
        - channel_name: ChannelName LIKE 검색
        - start_date: DATE >= 검색
        - end_date: DATE <= 검색
        """
        if filters.get('brand'):
            builder.where_like("b.Title", filters['brand'])

        if filters.get('product_name'):
            builder.where_like("e.PRODUCT_NAME", filters['product_name'])

        if filters.get('erp_code'):
            builder.where_like("e.ERPCode", filters['erp_code'])

        if filters.get('channel_name'):
            builder.where_like("e.ChannelName", filters['channel_name'])

        if filters.get('start_date'):
            builder.where("e.[DATE] >= ?", filters['start_date'])

        if filters.get('end_date'):
            builder.where("e.[DATE] <= ?", filters['end_date'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """Sales 전용 QueryBuilder 생성 (Brand 조인 포함)"""
        builder = QueryBuilder("[dbo].[ERPSales] e")

        # Brand 조인 추가
        builder.join("[dbo].[Brand] b", "e.BrandID = b.BrandID", "LEFT JOIN")

        # SELECT 컬럼 설정
        builder.select(
            "e.IDX", "e.[DATE]", "e.BRAND", "e.BrandID", "b.Title as BrandTitle",
            "e.ProductID", "e.PRODUCT_NAME", "e.ERPCode",
            "e.Quantity", "e.UnitPrice", "e.TaxableAmount",
            "e.ChannelID", "e.ChannelName", "e.ChannelDetailID", "e.ChannelDetailName", "e.Owner"
        )

        # 필터 적용
        if filters:
            self._apply_filters(builder, filters)

        return builder

    def bulk_update(self, ids: list, updates: Dict[str, Any]) -> int:
        """
        일괄 수정

        Args:
            ids: 수정할 IDX 리스트
            updates: 수정할 필드와 값 (예: {"Quantity": 10, "UnitPrice": 5000})

        Returns:
            int: 수정된 레코드 수
        """
        from core import get_db_cursor

        if not updates:
            return 0

        total_updated = 0

        with get_db_cursor() as cursor:
            # SET 절 생성
            set_clauses = [f"{key} = ?" for key in updates.keys()]
            set_sql = ", ".join(set_clauses)

            # 배치 처리
            batch_size = 1000
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                if not batch_ids:
                    continue

                placeholders = ','.join(['?'] * len(batch_ids))
                query = f"""
                    UPDATE [dbo].[ERPSales]
                    SET {set_sql}
                    WHERE IDX IN ({placeholders})
                """

                # 파라미터: updates 값들 + batch_ids
                params = list(updates.values()) + batch_ids
                cursor.execute(query, *params)
                total_updated += cursor.rowcount

        return total_updated
