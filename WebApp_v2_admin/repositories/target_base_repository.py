"""
TargetBaseProduct Repository
- 기본 목표 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


class TargetBaseRepository(BaseRepository):
    """TargetBaseProduct 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[TargetBaseProduct]", id_column="TargetBaseID")

    def get_select_query(self) -> str:
        """TargetBaseProduct 조회 쿼리"""
        return """
            SELECT
                t.TargetBaseID, t.[Date],
                t.BrandID, t.BrandName,
                t.ChannelID, t.ChannelName,
                t.UniqueCode, t.ProductName,
                t.TargetAmount, t.TargetQuantity,
                t.Notes, t.CreatedDate, t.UpdatedDate
            FROM [dbo].[TargetBaseProduct] t
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "TargetBaseID": row[0],
            "Date": row[1].strftime('%Y-%m-%d') if row[1] else None,
            "BrandID": row[2],
            "BrandName": row[3],
            "ChannelID": row[4],
            "ChannelName": row[5],
            "UniqueCode": row[6],
            "ProductName": row[7],
            "TargetAmount": float(row[8]) if row[8] else 0,
            "TargetQuantity": int(row[9]) if row[9] else 0,
            "Notes": row[10],
            "CreatedDate": row[11].strftime('%Y-%m-%d %H:%M:%S') if row[11] else None,
            "UpdatedDate": row[12].strftime('%Y-%m-%d %H:%M:%S') if row[12] else None,
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        TargetBase 전용 필터 로직

        지원하는 필터:
        - year_month: 년월 (YYYY-MM 형식)
        - brand_id: BrandID 정확히 매칭
        - channel_id: ChannelID 정확히 매칭
        - unique_code: UniqueCode LIKE 검색
        - product_name: ProductName LIKE 검색
        """
        if filters.get('year_month'):
            # YYYY-MM 형식으로 필터링
            year_month = filters['year_month']
            builder.where("FORMAT(t.[Date], 'yyyy-MM') = ?", year_month)

        if filters.get('brand_id'):
            builder.where_equals("t.BrandID", filters['brand_id'])

        if filters.get('channel_id'):
            builder.where_equals("t.ChannelID", filters['channel_id'])

        if filters.get('unique_code'):
            builder.where_like("t.UniqueCode", filters['unique_code'])

        if filters.get('product_name'):
            builder.where_like("t.ProductName", filters['product_name'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """TargetBase 전용 QueryBuilder 생성"""
        builder = QueryBuilder("[dbo].[TargetBaseProduct] t")

        # SELECT 컬럼 설정
        builder.select(
            "t.TargetBaseID", "t.[Date]",
            "t.BrandID", "t.BrandName",
            "t.ChannelID", "t.ChannelName",
            "t.UniqueCode", "t.ProductName",
            "t.TargetAmount", "t.TargetQuantity",
            "t.Notes", "t.CreatedDate", "t.UpdatedDate"
        )

        # 필터 적용
        if filters:
            self._apply_filters(builder, filters)

        return builder

    def bulk_upsert(self, records: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, int]:
        """
        일괄 INSERT/UPDATE
        - ID가 있으면: ID 기반 UPDATE
        - ID가 없으면: 복합키 기반 MERGE (INSERT/UPDATE)

        Args:
            records: 삽입/수정할 레코드 리스트
            batch_size: 배치 크기

        Returns:
            Dict: {"inserted": N, "updated": M}
        """
        total_inserted = 0
        total_updated = 0

        with get_db_cursor() as cursor:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]

                for record in batch:
                    target_id = record.get('TargetBaseID')

                    # ID가 있으면 ID 기반 UPDATE
                    if target_id:
                        update_query = """
                            UPDATE [dbo].[TargetBaseProduct]
                            SET [Date] = ?,
                                BrandID = ?,
                                BrandName = ?,
                                ChannelID = ?,
                                ChannelName = ?,
                                UniqueCode = ?,
                                ProductName = ?,
                                TargetAmount = ?,
                                TargetQuantity = ?,
                                Notes = ?,
                                UpdatedDate = GETDATE()
                            WHERE TargetBaseID = ?
                        """
                        params = [
                            record.get('Date'),
                            record.get('BrandID'),
                            record.get('BrandName'),
                            record.get('ChannelID'),
                            record.get('ChannelName'),
                            record.get('UniqueCode'),
                            record.get('ProductName'),
                            record.get('TargetAmount'),
                            record.get('TargetQuantity'),
                            record.get('Notes'),
                            target_id
                        ]
                        cursor.execute(update_query, *params)
                        if cursor.rowcount > 0:
                            total_updated += 1
                    else:
                        # ID가 없으면 복합키 기반 MERGE
                        merge_query = """
                            MERGE [dbo].[TargetBaseProduct] AS target
                            USING (SELECT ? AS [Date], ? AS UniqueCode, ? AS ChannelID) AS source
                            ON target.[Date] = source.[Date]
                               AND target.UniqueCode = source.UniqueCode
                               AND target.ChannelID = source.ChannelID
                            WHEN MATCHED THEN
                                UPDATE SET
                                    BrandID = ?,
                                    BrandName = ?,
                                    ChannelName = ?,
                                    ProductName = ?,
                                    TargetAmount = ?,
                                    TargetQuantity = ?,
                                    Notes = ?,
                                    UpdatedDate = GETDATE()
                            WHEN NOT MATCHED THEN
                                INSERT ([Date], BrandID, BrandName, ChannelID, ChannelName,
                                        UniqueCode, ProductName, TargetAmount, TargetQuantity, Notes)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            OUTPUT $action;
                        """

                        params = [
                            # source 파라미터
                            record.get('Date'),
                            record.get('UniqueCode'),
                            record.get('ChannelID'),
                            # UPDATE 파라미터
                            record.get('BrandID'),
                            record.get('BrandName'),
                            record.get('ChannelName'),
                            record.get('ProductName'),
                            record.get('TargetAmount'),
                            record.get('TargetQuantity'),
                            record.get('Notes'),
                            # INSERT 파라미터
                            record.get('Date'),
                            record.get('BrandID'),
                            record.get('BrandName'),
                            record.get('ChannelID'),
                            record.get('ChannelName'),
                            record.get('UniqueCode'),
                            record.get('ProductName'),
                            record.get('TargetAmount'),
                            record.get('TargetQuantity'),
                            record.get('Notes'),
                        ]

                        cursor.execute(merge_query, *params)
                        result = cursor.fetchone()

                        if result:
                            action = result[0]
                            if action == 'INSERT':
                                total_inserted += 1
                            elif action == 'UPDATE':
                                total_updated += 1

        return {"inserted": total_inserted, "updated": total_updated}

    def get_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        """
        ID 리스트로 데이터 조회

        Args:
            ids: 조회할 ID 리스트

        Returns:
            List[Dict]: 조회된 데이터 리스트
        """
        if not ids:
            return []

        with get_db_cursor(commit=False) as cursor:
            placeholders = ','.join(['?' for _ in ids])
            query = f"""
                SELECT
                    t.TargetBaseID, t.[Date],
                    t.BrandID, t.BrandName,
                    t.ChannelID, t.ChannelName,
                    t.UniqueCode, t.ProductName,
                    t.TargetAmount, t.TargetQuantity,
                    t.Notes, t.CreatedDate, t.UpdatedDate
                FROM [dbo].[TargetBaseProduct] t
                WHERE t.TargetBaseID IN ({placeholders})
                ORDER BY t.[Date] DESC
            """
            cursor.execute(query, *ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_year_months(self) -> List[str]:
        """저장된 데이터의 년월 목록 조회"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT FORMAT([Date], 'yyyy-MM') as YearMonth
                FROM [dbo].[TargetBaseProduct]
                ORDER BY YearMonth DESC
            """
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def delete_by_filter(self, year_month: str, brand_id: Optional[int] = None,
                         channel_id: Optional[int] = None) -> int:
        """
        필터 조건으로 일괄 삭제

        Args:
            year_month: 년월 (YYYY-MM)
            brand_id: 브랜드 ID (선택)
            channel_id: 채널 ID (선택)

        Returns:
            int: 삭제된 레코드 수
        """
        with get_db_cursor() as cursor:
            conditions = ["FORMAT([Date], 'yyyy-MM') = ?"]
            params = [year_month]

            if brand_id:
                conditions.append("BrandID = ?")
                params.append(brand_id)

            if channel_id:
                conditions.append("ChannelID = ?")
                params.append(channel_id)

            where_clause = " AND ".join(conditions)
            query = f"DELETE FROM [dbo].[TargetBaseProduct] WHERE {where_clause}"

            cursor.execute(query, *params)
            return cursor.rowcount
