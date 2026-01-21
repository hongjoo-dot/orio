"""
TargetSalesProduct Repository
- 목표매출(상품별) 테이블 CRUD 작업
- Promotion과 독립적으로 채널/브랜드별 월 목표 매출 관리
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


class TargetSalesProductRepository(BaseRepository):
    """TargetSalesProduct 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[TargetSalesProduct]", id_column="TargetID")

    def get_select_query(self) -> str:
        """TargetSalesProduct 조회 쿼리 (Brand, Channel, Product 조인 포함)"""
        return """
            SELECT
                t.TargetID, t.[Year], t.[Month],
                t.BrandID, b.Name as BrandName,
                t.ChannelID, c.Name as ChannelName,
                t.ProductID, p.Name as ProductName,
                t.TargetAmount, t.TargetQuantity,
                t.Notes, t.CreatedDate, t.UpdatedDate
            FROM [dbo].[TargetSalesProduct] t
            LEFT JOIN [dbo].[Brand] b ON t.BrandID = b.BrandID
            LEFT JOIN [dbo].[Channel] c ON t.ChannelID = c.ChannelID
            LEFT JOIN [dbo].[Product] p ON t.ProductID = p.ProductID
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "TargetID": row[0],
            "Year": row[1],
            "Month": row[2],
            "BrandID": row[3],
            "BrandName": row[4],
            "ChannelID": row[5],
            "ChannelName": row[6],
            "ProductID": row[7],
            "ProductName": row[8],
            "TargetAmount": float(row[9]) if row[9] else 0,
            "TargetQuantity": row[10],
            "Notes": row[11],
            "CreatedDate": row[12].strftime('%Y-%m-%d %H:%M:%S') if row[12] else None,
            "UpdatedDate": row[13].strftime('%Y-%m-%d %H:%M:%S') if row[13] else None
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        TargetSalesProduct 전용 필터 로직

        지원하는 필터:
        - brand_id: BrandID 완전 일치
        - channel_id: ChannelID 완전 일치
        - product_id: ProductID 완전 일치
        - year: 연도 필터
        - month: 월 필터
        """
        if filters.get('brand_id') is not None:
            builder.where_equals("t.BrandID", filters['brand_id'])

        if filters.get('channel_id'):
            builder.where_equals("t.ChannelID", filters['channel_id'])

        if filters.get('product_id'):
            builder.where_equals("t.ProductID", filters['product_id'])

        if filters.get('year'):
            builder.where_equals("t.[Year]", filters['year'])

        if filters.get('month'):
            builder.where_equals("t.[Month]", filters['month'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """TargetSalesProduct 전용 QueryBuilder 생성"""
        builder = QueryBuilder("[dbo].[TargetSalesProduct] t")

        # 조인 추가
        builder.join("[dbo].[Brand] b", "t.BrandID = b.BrandID", "LEFT JOIN")
        builder.join("[dbo].[Channel] c", "t.ChannelID = c.ChannelID", "LEFT JOIN")
        builder.join("[dbo].[Product] p", "t.ProductID = p.ProductID", "LEFT JOIN")

        # SELECT 컬럼 설정
        builder.select(
            "t.TargetID", "t.[Year]", "t.[Month]",
            "t.BrandID", "b.Name as BrandName",
            "t.ChannelID", "c.Name as ChannelName",
            "t.ProductID", "p.Name as ProductName",
            "t.TargetAmount", "t.TargetQuantity",
            "t.Notes", "t.CreatedDate", "t.UpdatedDate"
        )

        # 필터 적용
        if filters:
            self._apply_filters(builder, filters)

        return builder

    def bulk_insert(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        대량 INSERT/UPDATE 처리 (MERGE)
        유니크 키: Year + Month + BrandID + ChannelID + ProductID
        """
        inserted = 0
        updated = 0

        sql = """
            MERGE INTO [dbo].[TargetSalesProduct] AS target
            USING (SELECT ? AS [Year], ? AS [Month], ? AS BrandID, ? AS ChannelID, ? AS ProductID) AS source
            ON target.[Year] = source.[Year]
               AND target.[Month] = source.[Month]
               AND target.BrandID = source.BrandID
               AND target.ChannelID = source.ChannelID
               AND target.ProductID = source.ProductID
            WHEN MATCHED THEN
                UPDATE SET
                    TargetAmount = ?,
                    TargetQuantity = ?,
                    Notes = ?,
                    UpdatedDate = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT ([Year], [Month], BrandID, ChannelID, ProductID,
                        TargetAmount, TargetQuantity, Notes,
                        CreatedDate, UpdatedDate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            OUTPUT $action;
        """

        with get_db_cursor(commit=True) as cursor:
            for record in records:
                params = (
                    # USING (유니크 키)
                    record['Year'], record['Month'], record['BrandID'],
                    record['ChannelID'], record['ProductID'],
                    # UPDATE SET
                    record.get('TargetAmount'), record.get('TargetQuantity'),
                    record.get('Notes'),
                    # INSERT VALUES
                    record['Year'], record['Month'], record['BrandID'],
                    record['ChannelID'], record['ProductID'],
                    record.get('TargetAmount'), record.get('TargetQuantity'),
                    record.get('Notes')
                )
                cursor.execute(sql, params)
                result = cursor.fetchone()
                if result:
                    if result[0] == 'INSERT':
                        inserted += 1
                    else:
                        updated += 1

        return {'inserted': inserted, 'updated': updated}

    def get_summary_by_month(self, year: int) -> List[Dict[str, Any]]:
        """
        월별 목표매출 합계 조회

        Args:
            year: 연도

        Returns:
            [{'Month': 1, 'TotalAmount': 1000000, 'TotalQuantity': 100}, ...]
        """
        with get_db_cursor(commit=False) as cursor:
            sql = """
                SELECT
                    [Month],
                    SUM(TargetAmount) as TotalAmount,
                    SUM(TargetQuantity) as TotalQuantity
                FROM [dbo].[TargetSalesProduct]
                WHERE [Year] = ?
                GROUP BY [Month]
                ORDER BY [Month]
            """
            cursor.execute(sql, [year])
            return [
                {
                    'Month': row[0],
                    'TotalAmount': float(row[1]) if row[1] else 0,
                    'TotalQuantity': row[2] if row[2] else 0
                }
                for row in cursor.fetchall()
            ]

    def get_summary_by_channel(self, year: int, month: int = None) -> List[Dict[str, Any]]:
        """
        채널별 목표매출 합계 조회
        """
        with get_db_cursor(commit=False) as cursor:
            sql = """
                SELECT
                    t.ChannelID,
                    c.Name as ChannelName,
                    SUM(t.TargetAmount) as TotalAmount,
                    SUM(t.TargetQuantity) as TotalQuantity
                FROM [dbo].[TargetSalesProduct] t
                LEFT JOIN [dbo].[Channel] c ON t.ChannelID = c.ChannelID
                WHERE t.[Year] = ?
            """
            params = [year]

            if month:
                sql += " AND t.[Month] = ?"
                params.append(month)

            sql += " GROUP BY t.ChannelID, c.Name ORDER BY TotalAmount DESC"

            cursor.execute(sql, params)
            return [
                {
                    'ChannelID': row[0],
                    'ChannelName': row[1],
                    'TotalAmount': float(row[2]) if row[2] else 0,
                    'TotalQuantity': row[3] if row[3] else 0
                }
                for row in cursor.fetchall()
            ]

    def get_summary_by_brand(self, year: int, month: int = None) -> List[Dict[str, Any]]:
        """
        브랜드별 목표매출 합계 조회
        """
        with get_db_cursor(commit=False) as cursor:
            sql = """
                SELECT
                    t.BrandID,
                    b.Name as BrandName,
                    SUM(t.TargetAmount) as TotalAmount,
                    SUM(t.TargetQuantity) as TotalQuantity
                FROM [dbo].[TargetSalesProduct] t
                LEFT JOIN [dbo].[Brand] b ON t.BrandID = b.BrandID
                WHERE t.[Year] = ?
            """
            params = [year]

            if month:
                sql += " AND t.[Month] = ?"
                params.append(month)

            sql += " GROUP BY t.BrandID, b.Name ORDER BY TotalAmount DESC"

            cursor.execute(sql, params)
            return [
                {
                    'BrandID': row[0],
                    'BrandName': row[1],
                    'TotalAmount': float(row[2]) if row[2] else 0,
                    'TotalQuantity': row[3] if row[3] else 0
                }
                for row in cursor.fetchall()
            ]
