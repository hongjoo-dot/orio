"""
ExpectedSalesProduct Repository
- 예상매출(상품별) 테이블 CRUD 작업
- BASE(비행사) + PROMOTION(행사) 매출 관리
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


class ExpectedSalesProductRepository(BaseRepository):
    """ExpectedSalesProduct 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[ExpectedSalesProduct]", id_column="ExpectedID")

    def get_select_query(self) -> str:
        """ExpectedSalesProduct 조회 쿼리 (Brand, Channel, Product 조인 포함)"""
        return """
            SELECT
                t.ExpectedID, t.[Year], t.[Month],
                t.BrandID, b.Name as BrandName,
                t.ChannelID, c.Name as ChannelName,
                t.ProductID, p.Name as ProductName,
                t.SalesType, t.PromotionID, t.PromotionProductID,
                t.ExpectedAmount, t.ExpectedQuantity,
                t.CreatedDate, t.UpdatedDate
            FROM [dbo].[ExpectedSalesProduct] t
            LEFT JOIN [dbo].[Brand] b ON t.BrandID = b.BrandID
            LEFT JOIN [dbo].[Channel] c ON t.ChannelID = c.ChannelID
            LEFT JOIN [dbo].[Product] p ON t.ProductID = p.ProductID
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "ExpectedID": row[0],
            "Year": row[1],
            "Month": row[2],
            "BrandID": row[3],
            "BrandName": row[4],
            "ChannelID": row[5],
            "ChannelName": row[6],
            "ProductID": row[7],
            "ProductName": row[8],
            "SalesType": row[9],
            "PromotionID": row[10],
            "PromotionProductID": row[11],
            "ExpectedAmount": float(row[12]) if row[12] else 0,
            "ExpectedQuantity": row[13],
            "CreatedDate": row[14].strftime('%Y-%m-%d %H:%M:%S') if row[14] else None,
            "UpdatedDate": row[15].strftime('%Y-%m-%d %H:%M:%S') if row[15] else None
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        ExpectedSalesProduct 전용 필터 로직

        지원하는 필터:
        - brand_id: BrandID 완전 일치
        - channel_id: ChannelID 완전 일치
        - product_id: ProductID 완전 일치
        - sales_type: SalesType 완전 일치 ('BASE' / 'PROMOTION')
        - promotion_id: PromotionID 완전 일치
        - year: 연도 필터
        - month: 월 필터
        """
        if filters.get('brand_id') is not None:
            builder.where_equals("t.BrandID", filters['brand_id'])

        if filters.get('channel_id'):
            builder.where_equals("t.ChannelID", filters['channel_id'])

        if filters.get('product_id'):
            builder.where_equals("t.ProductID", filters['product_id'])

        if filters.get('sales_type'):
            builder.where_equals("t.SalesType", filters['sales_type'])

        if filters.get('promotion_id'):
            builder.where_equals("t.PromotionID", filters['promotion_id'])

        if filters.get('year'):
            builder.where_equals("t.[Year]", filters['year'])

        if filters.get('month'):
            builder.where_equals("t.[Month]", filters['month'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """ExpectedSalesProduct 전용 QueryBuilder 생성"""
        builder = QueryBuilder("[dbo].[ExpectedSalesProduct] t")

        # 조인 추가
        builder.join("[dbo].[Brand] b", "t.BrandID = b.BrandID", "LEFT JOIN")
        builder.join("[dbo].[Channel] c", "t.ChannelID = c.ChannelID", "LEFT JOIN")
        builder.join("[dbo].[Product] p", "t.ProductID = p.ProductID", "LEFT JOIN")

        # SELECT 컬럼 설정
        builder.select(
            "t.ExpectedID", "t.[Year]", "t.[Month]",
            "t.BrandID", "b.Name as BrandName",
            "t.ChannelID", "c.Name as ChannelName",
            "t.ProductID", "p.Name as ProductName",
            "t.SalesType", "t.PromotionID", "t.PromotionProductID",
            "t.ExpectedAmount", "t.ExpectedQuantity",
            "t.CreatedDate", "t.UpdatedDate"
        )

        # 필터 적용
        if filters:
            self._apply_filters(builder, filters)

        return builder

    def bulk_insert(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        대량 INSERT/UPDATE 처리 (MERGE)
        유니크 키: Year + Month + BrandID + ChannelID + ProductID + SalesType + PromotionID
        """
        inserted = 0
        updated = 0

        sql = """
            MERGE INTO [dbo].[ExpectedSalesProduct] AS target
            USING (SELECT ? AS [Year], ? AS [Month], ? AS BrandID, ? AS ChannelID,
                          ? AS ProductID, ? AS SalesType, ? AS PromotionID) AS source
            ON target.[Year] = source.[Year]
               AND target.[Month] = source.[Month]
               AND target.BrandID = source.BrandID
               AND target.ChannelID = source.ChannelID
               AND target.ProductID = source.ProductID
               AND target.SalesType = source.SalesType
               AND (target.PromotionID = source.PromotionID OR (target.PromotionID IS NULL AND source.PromotionID IS NULL))
            WHEN MATCHED THEN
                UPDATE SET
                    PromotionProductID = ?,
                    ExpectedAmount = ?,
                    ExpectedQuantity = ?,
                    UpdatedDate = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT ([Year], [Month], BrandID, ChannelID, ProductID, SalesType,
                        PromotionID, PromotionProductID, ExpectedAmount, ExpectedQuantity,
                        CreatedDate, UpdatedDate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            OUTPUT $action;
        """

        with get_db_cursor(commit=True) as cursor:
            for record in records:
                params = (
                    # USING (유니크 키)
                    record['Year'], record['Month'], record['BrandID'], record['ChannelID'],
                    record['ProductID'], record['SalesType'], record.get('PromotionID'),
                    # UPDATE SET
                    record.get('PromotionProductID'),
                    record.get('ExpectedAmount'), record.get('ExpectedQuantity'),
                    # INSERT VALUES
                    record['Year'], record['Month'], record['BrandID'], record['ChannelID'],
                    record['ProductID'], record['SalesType'], record.get('PromotionID'),
                    record.get('PromotionProductID'), record.get('ExpectedAmount'), record.get('ExpectedQuantity')
                )
                cursor.execute(sql, params)
                result = cursor.fetchone()
                if result:
                    if result[0] == 'INSERT':
                        inserted += 1
                    else:
                        updated += 1

        return {'inserted': inserted, 'updated': updated}

    def delete_by_promotion_id(self, promotion_id: str) -> int:
        """특정 행사의 모든 예상매출 삭제"""
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "DELETE FROM [dbo].[ExpectedSalesProduct] WHERE PromotionID = ?",
                (promotion_id,)
            )
            return cursor.rowcount

    def get_summary_by_month(self, year: int, sales_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        월별 예상매출 합계 조회

        Args:
            year: 연도
            sales_type: 'BASE' / 'PROMOTION' / None (전체)

        Returns:
            [{'Month': 1, 'SalesType': 'BASE', 'TotalAmount': 1000000}, ...]
        """
        with get_db_cursor(commit=False) as cursor:
            sql = """
                SELECT
                    [Month],
                    SalesType,
                    SUM(ExpectedAmount) as TotalAmount,
                    SUM(ExpectedQuantity) as TotalQuantity
                FROM [dbo].[ExpectedSalesProduct]
                WHERE [Year] = ?
            """
            params = [year]

            if sales_type:
                sql += " AND SalesType = ?"
                params.append(sales_type)

            sql += " GROUP BY [Month], SalesType ORDER BY [Month], SalesType"

            cursor.execute(sql, params)
            return [
                {
                    'Month': row[0],
                    'SalesType': row[1],
                    'TotalAmount': float(row[2]) if row[2] else 0,
                    'TotalQuantity': row[3] if row[3] else 0
                }
                for row in cursor.fetchall()
            ]

    def get_summary_by_channel(self, year: int, month: int = None) -> List[Dict[str, Any]]:
        """
        채널별 예상매출 합계 조회
        """
        with get_db_cursor(commit=False) as cursor:
            sql = """
                SELECT
                    t.ChannelID,
                    c.Name as ChannelName,
                    t.SalesType,
                    SUM(t.ExpectedAmount) as TotalAmount,
                    SUM(t.ExpectedQuantity) as TotalQuantity
                FROM [dbo].[ExpectedSalesProduct] t
                LEFT JOIN [dbo].[Channel] c ON t.ChannelID = c.ChannelID
                WHERE t.[Year] = ?
            """
            params = [year]

            if month:
                sql += " AND t.[Month] = ?"
                params.append(month)

            sql += " GROUP BY t.ChannelID, c.Name, t.SalesType ORDER BY TotalAmount DESC"

            cursor.execute(sql, params)
            return [
                {
                    'ChannelID': row[0],
                    'ChannelName': row[1],
                    'SalesType': row[2],
                    'TotalAmount': float(row[3]) if row[3] else 0,
                    'TotalQuantity': row[4] if row[4] else 0
                }
                for row in cursor.fetchall()
            ]
