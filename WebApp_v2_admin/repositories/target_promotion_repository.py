"""
TargetPromotionProduct Repository
- 행사 목표 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


class TargetPromotionRepository(BaseRepository):
    """TargetPromotionProduct 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[TargetPromotionProduct]", id_column="TargetPromotionID")

    def get_select_query(self) -> str:
        """TargetPromotionProduct 조회 쿼리"""
        return """
            SELECT
                t.TargetPromotionID,
                t.PromotionID, t.PromotionName,
                t.StartDate, t.StartTime, t.EndDate, t.EndTime,
                t.BrandID, t.BrandName,
                t.ChannelID, t.ChannelName,
                t.UniqueCode, t.ProductName,
                t.TargetAmount, t.TargetQuantity,
                t.Notes, t.PromotionType,
                t.CreatedDate, t.UpdatedDate
            FROM [dbo].[TargetPromotionProduct] t
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "TargetPromotionID": row[0],
            "PromotionID": row[1],
            "PromotionName": row[2],
            "StartDate": row[3].strftime('%Y-%m-%d') if row[3] else None,
            "StartTime": row[4].strftime('%H:%M:%S') if row[4] else None,
            "EndDate": row[5].strftime('%Y-%m-%d') if row[5] else None,
            "EndTime": row[6].strftime('%H:%M:%S') if row[6] else None,
            "BrandID": row[7],
            "BrandName": row[8],
            "ChannelID": row[9],
            "ChannelName": row[10],
            "UniqueCode": row[11],
            "ProductName": row[12],
            "TargetAmount": float(row[13]) if row[13] else 0,
            "TargetQuantity": int(row[14]) if row[14] else 0,
            "Notes": row[15],
            "PromotionType": row[16],
            "CreatedDate": row[17].strftime('%Y-%m-%d %H:%M:%S') if row[17] else None,
            "UpdatedDate": row[18].strftime('%Y-%m-%d %H:%M:%S') if row[18] else None,
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        TargetPromotion 전용 필터 로직

        지원하는 필터:
        - year_month: 시작일 기준 년월 (YYYY-MM 형식)
        - brand_id: BrandID 정확히 매칭
        - channel_id: ChannelID 정확히 매칭
        - promotion_id: PromotionID 정확히 매칭
        - unique_code: UniqueCode LIKE 검색
        - product_name: ProductName LIKE 검색
        """
        if filters.get('year_month'):
            year_month = filters['year_month']
            builder.where("FORMAT(t.StartDate, 'yyyy-MM') = ?", year_month)

        if filters.get('brand_id'):
            builder.where_equals("t.BrandID", filters['brand_id'])

        if filters.get('channel_id'):
            builder.where_equals("t.ChannelID", filters['channel_id'])

        if filters.get('promotion_id'):
            builder.where_equals("t.PromotionID", filters['promotion_id'])

        if filters.get('unique_code'):
            builder.where_like("t.UniqueCode", filters['unique_code'])

        if filters.get('product_name'):
            builder.where_like("t.ProductName", filters['product_name'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """TargetPromotion 전용 QueryBuilder 생성"""
        builder = QueryBuilder("[dbo].[TargetPromotionProduct] t")

        # SELECT 컬럼 설정
        builder.select(
            "t.TargetPromotionID",
            "t.PromotionID", "t.PromotionName",
            "t.StartDate", "t.StartTime", "t.EndDate", "t.EndTime",
            "t.BrandID", "t.BrandName",
            "t.ChannelID", "t.ChannelName",
            "t.UniqueCode", "t.ProductName",
            "t.TargetAmount", "t.TargetQuantity",
            "t.Notes", "t.PromotionType",
            "t.CreatedDate", "t.UpdatedDate"
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
                    target_id = record.get('TargetPromotionID')

                    # ID가 있으면 ID 기반 UPDATE (PromotionID는 변경 불가)
                    if target_id:
                        update_query = """
                            UPDATE [dbo].[TargetPromotionProduct]
                            SET PromotionName = ?,
                                StartTime = ?,
                                EndTime = ?,
                                TargetAmount = ?,
                                TargetQuantity = ?,
                                Notes = ?,
                                UpdatedDate = GETDATE()
                            WHERE TargetPromotionID = ?
                        """
                        params = [
                            record.get('PromotionName'),
                            record.get('StartTime', '00:00:00'),
                            record.get('EndTime', '00:00:00'),
                            record.get('TargetAmount'),
                            record.get('TargetQuantity'),
                            record.get('Notes'),
                            target_id
                        ]
                        cursor.execute(update_query, *params)
                        if cursor.rowcount > 0:
                            total_updated += 1
                    else:
                        # ID가 없으면 복합키로 중복 체크 후 INSERT
                        # 복합키: BrandID + ChannelID + PromotionType + StartDate + UniqueCode
                        check_query = """
                            SELECT 1 FROM [dbo].[TargetPromotionProduct]
                            WHERE BrandID = ? AND ChannelID = ? AND PromotionType = ?
                              AND StartDate = ? AND UniqueCode = ?
                        """
                        cursor.execute(check_query,
                            record.get('BrandID'),
                            record.get('ChannelID'),
                            record.get('PromotionType'),
                            record.get('StartDate'),
                            record.get('UniqueCode')
                        )

                        if cursor.fetchone():
                            # 중복 존재 - 스킵
                            continue

                        # 중복 없음 - INSERT
                        insert_query = """
                            INSERT INTO [dbo].[TargetPromotionProduct]
                                (PromotionID, PromotionName, StartDate, StartTime, EndDate, EndTime,
                                 BrandID, BrandName, ChannelID, ChannelName,
                                 UniqueCode, ProductName, TargetAmount, TargetQuantity, Notes, PromotionType)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        params = [
                            record.get('PromotionID'),
                            record.get('PromotionName'),
                            record.get('StartDate'),
                            record.get('StartTime', '00:00:00'),
                            record.get('EndDate'),
                            record.get('EndTime', '00:00:00'),
                            record.get('BrandID'),
                            record.get('BrandName'),
                            record.get('ChannelID'),
                            record.get('ChannelName'),
                            record.get('UniqueCode'),
                            record.get('ProductName'),
                            record.get('TargetAmount'),
                            record.get('TargetQuantity'),
                            record.get('Notes'),
                            record.get('PromotionType'),
                        ]
                        cursor.execute(insert_query, *params)
                        if cursor.rowcount > 0:
                            total_inserted += 1

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
                    t.TargetPromotionID,
                    t.PromotionID, t.PromotionName,
                    t.StartDate, t.StartTime, t.EndDate, t.EndTime,
                    t.BrandID, t.BrandName,
                    t.ChannelID, t.ChannelName,
                    t.UniqueCode, t.ProductName,
                    t.TargetAmount, t.TargetQuantity,
                    t.Notes, t.PromotionType,
                    t.CreatedDate, t.UpdatedDate
                FROM [dbo].[TargetPromotionProduct] t
                WHERE t.TargetPromotionID IN ({placeholders})
                ORDER BY t.StartDate DESC
            """
            cursor.execute(query, *ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_year_months(self) -> List[str]:
        """저장된 데이터의 년월 목록 조회 (StartDate 기준)"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT FORMAT(StartDate, 'yyyy-MM') as YearMonth
                FROM [dbo].[TargetPromotionProduct]
                ORDER BY YearMonth DESC
            """
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def delete_by_filter(self, year_month: str, brand_id: Optional[int] = None,
                         channel_id: Optional[int] = None,
                         promotion_id: Optional[str] = None) -> int:
        """
        필터 조건으로 일괄 삭제

        Args:
            year_month: 년월 (YYYY-MM, StartDate 기준)
            brand_id: 브랜드 ID (선택)
            channel_id: 채널 ID (선택)
            promotion_id: 행사 ID (선택)

        Returns:
            int: 삭제된 레코드 수
        """
        with get_db_cursor() as cursor:
            conditions = ["FORMAT(StartDate, 'yyyy-MM') = ?"]
            params = [year_month]

            if brand_id:
                conditions.append("BrandID = ?")
                params.append(brand_id)

            if channel_id:
                conditions.append("ChannelID = ?")
                params.append(channel_id)

            if promotion_id:
                conditions.append("PromotionID = ?")
                params.append(promotion_id)

            where_clause = " AND ".join(conditions)
            query = f"DELETE FROM [dbo].[TargetPromotionProduct] WHERE {where_clause}"

            cursor.execute(query, *params)
            return cursor.rowcount

    def get_promotions(self, year_month: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        행사 목록 조회 (드롭다운용)

        Args:
            year_month: 년월 필터 (선택)

        Returns:
            List: 행사 ID와 이름 목록
        """
        with get_db_cursor(commit=False) as cursor:
            if year_month:
                query = """
                    SELECT DISTINCT PromotionID, PromotionName
                    FROM [dbo].[TargetPromotionProduct]
                    WHERE FORMAT(StartDate, 'yyyy-MM') = ?
                    ORDER BY PromotionID
                """
                cursor.execute(query, year_month)
            else:
                query = """
                    SELECT DISTINCT PromotionID, PromotionName
                    FROM [dbo].[TargetPromotionProduct]
                    ORDER BY PromotionID
                """
                cursor.execute(query)

            return [{"PromotionID": row[0], "PromotionName": row[1]} for row in cursor.fetchall()]

    def get_next_sequence(self, prefix: str) -> int:
        """
        PromotionID 접두사 기반 다음 순번 조회

        Args:
            prefix: PromotionID 접두사 (BrandCode + TypeCode + YYMM)

        Returns:
            int: 다음 순번 (1부터 시작, 최대 99)
        """
        with get_db_cursor(commit=False) as cursor:
            # 해당 접두사로 시작하는 PromotionID 중 가장 큰 순번 조회
            query = """
                SELECT MAX(CAST(RIGHT(PromotionID, 2) AS INT))
                FROM [dbo].[TargetPromotionProduct]
                WHERE PromotionID LIKE ? + '%'
                  AND LEN(PromotionID) > 2
            """
            cursor.execute(query, prefix)
            row = cursor.fetchone()

            if row and row[0] is not None:
                return min(row[0] + 1, 99)  # 최대 99까지
            return 1

    def get_max_sequences_by_prefixes(self, prefixes: List[str]) -> Dict[str, int]:
        """
        여러 접두사에 대한 현재 최대 순번 일괄 조회

        Args:
            prefixes: PromotionID 접두사 리스트

        Returns:
            Dict[str, int]: {prefix: max_sequence} 매핑
        """
        if not prefixes:
            return {}

        result = {prefix: 0 for prefix in prefixes}

        with get_db_cursor(commit=False) as cursor:
            # 모든 PromotionID 조회 후 접두사별로 그룹화
            unique_prefixes = list(set(prefixes))

            for prefix in unique_prefixes:
                query = """
                    SELECT MAX(CAST(RIGHT(PromotionID, 2) AS INT))
                    FROM [dbo].[TargetPromotionProduct]
                    WHERE PromotionID LIKE ? + '%'
                      AND LEN(PromotionID) > 2
                """
                cursor.execute(query, prefix)
                row = cursor.fetchone()

                if row and row[0] is not None:
                    result[prefix] = row[0]

        return result
