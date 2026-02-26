"""
Expected1PRegularProduct Repository
- 사입(1P) 정기 예상 매출 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor, log_changes_bulk
from utils.helpers import calculate_amount_ex_vat


class Expected1PRegularRepository(BaseRepository):
    """Expected1PRegularProduct 테이블 Repository"""

    # SELECT 컬럼 상수 (순서 변경 금지 - _row_to_dict 인덱스와 일치해야 함)
    SELECT_COLUMNS = (
        "t.Expected1PRegularID", "t.[Date]",
        "t.BrandID", "t.BrandName",
        "t.ChannelID", "t.ChannelName",
        "t.ERPCode", "t.UniqueCode", "t.ProductName",
        "t.ExpectedAmount", "t.ExpectedAmountExVAT", "t.ExpectedQuantity",
        "t.Notes", "t.CreatedDate", "t.UpdatedDate",
        "t.InputMonth",
        "t.OliveyoungType"
    )

    def __init__(self):
        super().__init__(table_name="[dbo].[Expected1PRegularProduct]", id_column="Expected1PRegularID")

    def get_select_query(self) -> str:
        """Expected1PRegularProduct 조회 쿼리"""
        columns = ", ".join(self.SELECT_COLUMNS)
        return f"SELECT {columns} FROM [dbo].[Expected1PRegularProduct] t"

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "Expected1PRegularID": row[0],
            "Date": row[1].strftime('%Y-%m-%d') if row[1] else None,
            "BrandID": row[2],
            "BrandName": row[3],
            "ChannelID": row[4],
            "ChannelName": row[5],
            "ERPCode": row[6],
            "UniqueCode": row[7],
            "ProductName": row[8],
            "ExpectedAmount": float(row[9]) if row[9] else 0,
            "ExpectedAmountExVAT": float(row[10]) if row[10] else 0,
            "ExpectedQuantity": int(row[11]) if row[11] else 0,
            "Notes": row[12],
            "CreatedDate": row[13].strftime('%Y-%m-%d %H:%M:%S') if row[13] else None,
            "UpdatedDate": row[14].strftime('%Y-%m-%d %H:%M:%S') if row[14] else None,
            "InputMonth": row[15],
            "OliveyoungType": row[16],
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        Expected1PRegular 전용 필터 로직

        지원하는 필터:
        - year_month: 년월 (YYYY-MM 형식)
        - brand_id: BrandID 정확히 매칭
        - channel_id: ChannelID 정확히 매칭
        - input_month: InputMonth 정확히 매칭 (YYYY-MM 형식)
        """
        if filters.get('year_month'):
            year_month = filters['year_month']
            builder.where("FORMAT(t.[Date], 'yyyy-MM') = ?", year_month)

        if 'brand_id' in filters:
            builder.where_equals("t.BrandID", filters['brand_id'])

        if 'channel_id' in filters:
            builder.where_equals("t.ChannelID", filters['channel_id'])

        if filters.get('input_month'):
            builder.where_equals("t.InputMonth", filters['input_month'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """Expected1PRegular 전용 QueryBuilder 생성"""
        builder = QueryBuilder("[dbo].[Expected1PRegularProduct] t")
        builder.select(*self.SELECT_COLUMNS)

        if filters:
            self._apply_filters(builder, filters)

        return builder

    def bulk_upsert(self, records: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, Any]:
        """
        일괄 INSERT/UPDATE
        - ID가 있으면: ID 기반 UPDATE
        - ID가 없으면: 복합키 중복 체크 후 INSERT (중복 시 에러)
        """
        total_inserted = 0
        total_updated = 0
        duplicates = []

        # 1단계: 신규 레코드(ID 없음)에 대해 중복 체크 먼저 수행
        with get_db_cursor() as cursor:
            for idx, record in enumerate(records):
                record_id = record.get('Expected1PRegularID')
                row_num = idx + 2

                if not record_id:
                    check_query = """
                        SELECT Expected1PRegularID FROM [dbo].[Expected1PRegularProduct]
                        WHERE [Date] = ? AND UniqueCode = ? AND ChannelID = ? AND InputMonth = ?
                          AND ISNULL(OliveyoungType, '') = ISNULL(?, '')
                    """
                    cursor.execute(check_query,
                        record.get('Date'),
                        record.get('UniqueCode'),
                        record.get('ChannelID'),
                        record.get('InputMonth'),
                        record.get('OliveyoungType')
                    )
                    existing = cursor.fetchone()

                    if existing:
                        duplicates.append({
                            'row': row_num,
                            'date': record.get('Date'),
                            'unique_code': record.get('UniqueCode'),
                            'channel_name': record.get('ChannelName'),
                            'existing_id': existing[0]
                        })

        if duplicates:
            return {"inserted": 0, "updated": 0, "duplicates": duplicates}

        # 2단계: 중복이 없으면 INSERT/UPDATE 실행
        with get_db_cursor() as cursor:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]

                for record in batch:
                    record_id = record.get('Expected1PRegularID')

                    expected_amount = record.get('ExpectedAmount') or 0
                    expected_amount_ex_vat = calculate_amount_ex_vat(expected_amount)

                    if record_id:
                        update_query = """
                            UPDATE [dbo].[Expected1PRegularProduct]
                            SET [Date] = ?,
                                BrandID = ?,
                                BrandName = ?,
                                ChannelID = ?,
                                ChannelName = ?,
                                ERPCode = ?,
                                UniqueCode = ?,
                                ProductName = ?,
                                ExpectedAmount = ?,
                                ExpectedAmountExVAT = ?,
                                ExpectedQuantity = ?,
                                Notes = ?,
                                InputMonth = ?,
                                OliveyoungType = ?,
                                UpdatedDate = GETDATE()
                            WHERE Expected1PRegularID = ?
                        """
                        params = [
                            record.get('Date'),
                            record.get('BrandID'),
                            record.get('BrandName'),
                            record.get('ChannelID'),
                            record.get('ChannelName'),
                            record.get('ERPCode'),
                            record.get('UniqueCode'),
                            record.get('ProductName'),
                            expected_amount,
                            expected_amount_ex_vat,
                            record.get('ExpectedQuantity'),
                            record.get('Notes'),
                            record.get('InputMonth'),
                            record.get('OliveyoungType'),
                            record_id
                        ]
                        cursor.execute(update_query, *params)
                        if cursor.rowcount > 0:
                            total_updated += 1
                    else:
                        insert_query = """
                            INSERT INTO [dbo].[Expected1PRegularProduct]
                            ([Date], BrandID, BrandName, ChannelID, ChannelName,
                             ERPCode, UniqueCode, ProductName, ExpectedAmount, ExpectedAmountExVAT,
                             ExpectedQuantity, Notes, InputMonth, OliveyoungType)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        params = [
                            record.get('Date'),
                            record.get('BrandID'),
                            record.get('BrandName'),
                            record.get('ChannelID'),
                            record.get('ChannelName'),
                            record.get('ERPCode'),
                            record.get('UniqueCode'),
                            record.get('ProductName'),
                            expected_amount,
                            expected_amount_ex_vat,
                            record.get('ExpectedQuantity'),
                            record.get('Notes'),
                            record.get('InputMonth'),
                            record.get('OliveyoungType'),
                        ]
                        cursor.execute(insert_query, *params)
                        total_inserted += 1

        return {"inserted": total_inserted, "updated": total_updated, "duplicates": []}

    def get_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        """ID 리스트로 데이터 조회"""
        if not ids:
            return []

        with get_db_cursor(commit=False) as cursor:
            placeholders = ','.join(['?' for _ in ids])
            columns = ", ".join(self.SELECT_COLUMNS)
            query = f"""
                SELECT {columns}
                FROM [dbo].[Expected1PRegularProduct] t
                WHERE t.Expected1PRegularID IN ({placeholders})
                ORDER BY t.[Date] DESC
            """
            cursor.execute(query, *ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_year_months(self) -> List[str]:
        """저장된 데이터의 년월 목록 조회 (사입 1P/2P 채널만)"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT FORMAT(t.[Date], 'yyyy-MM') as YearMonth
                FROM [dbo].[Expected1PRegularProduct] t
                INNER JOIN [dbo].[Channel] c ON t.ChannelID = c.ChannelID
                WHERE c.ContractType IN ('1P', '2P')
                ORDER BY YearMonth DESC
            """
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def get_channels_summary(self, year_month: str, brand_id: Optional[int] = None, input_month: Optional[str] = None) -> List[Dict[str, Any]]:
        """채널별 예상 매출 요약 조회 (마스터 패널용, 사입 1P/2P 채널만)"""
        with get_db_cursor(commit=False) as cursor:
            where_clauses = ["FORMAT(t.[Date], 'yyyy-MM') = ?", "c.ContractType IN ('1P', '2P')"]
            params = [year_month]

            if brand_id is not None:
                where_clauses.append("t.BrandID = ?")
                params.append(brand_id)

            if input_month:
                where_clauses.append("t.InputMonth = ?")
                params.append(input_month)

            where_sql = " AND ".join(where_clauses)

            query = f"""
                SELECT t.ChannelID, t.ChannelName,
                       COUNT(*) as ProductCount,
                       ISNULL(SUM(t.ExpectedAmount), 0) as TotalAmount,
                       ISNULL(SUM(t.ExpectedQuantity), 0) as TotalQuantity
                FROM [dbo].[Expected1PRegularProduct] t
                INNER JOIN [dbo].[Channel] c ON t.ChannelID = c.ChannelID
                WHERE {where_sql}
                GROUP BY t.ChannelID, t.ChannelName
                ORDER BY t.ChannelName ASC
            """
            cursor.execute(query, *params)
            return [{
                "ChannelID": row[0],
                "ChannelName": row[1],
                "ProductCount": row[2],
                "TotalAmount": float(row[3]) if row[3] else 0,
                "TotalQuantity": int(row[4]) if row[4] else 0,
            } for row in cursor.fetchall()]

    def get_by_channel(self, channel_id: int, year_month: str, brand_id: Optional[int] = None, input_month: Optional[str] = None) -> List[Dict[str, Any]]:
        """특정 채널의 예상 매출 상품 목록 조회 (디테일 패널용)"""
        with get_db_cursor(commit=False) as cursor:
            columns = ", ".join(self.SELECT_COLUMNS)
            where_clauses = ["t.ChannelID = ?", "FORMAT(t.[Date], 'yyyy-MM') = ?"]
            params = [channel_id, year_month]

            if brand_id is not None:
                where_clauses.append("t.BrandID = ?")
                params.append(brand_id)

            if input_month:
                where_clauses.append("t.InputMonth = ?")
                params.append(input_month)

            where_sql = " AND ".join(where_clauses)

            query = f"""
                SELECT {columns}
                FROM [dbo].[Expected1PRegularProduct] t
                WHERE {where_sql}
                ORDER BY t.ERPCode ASC
            """
            cursor.execute(query, *params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_input_months(self, year_month: Optional[str] = None) -> List[str]:
        """InputMonth 목록 조회 (사입 1P/2P 채널만)"""
        with get_db_cursor(commit=False) as cursor:
            where_clauses = ["c.ContractType IN ('1P', '2P')"]
            params = []

            if year_month:
                where_clauses.append("FORMAT(t.[Date], 'yyyy-MM') = ?")
                params.append(year_month)

            where_sql = " AND ".join(where_clauses)
            query = f"""
                SELECT DISTINCT t.InputMonth
                FROM [dbo].[Expected1PRegularProduct] t
                INNER JOIN [dbo].[Channel] c ON t.ChannelID = c.ChannelID
                WHERE {where_sql}
                ORDER BY t.InputMonth DESC
            """
            cursor.execute(query, *params)
            return [row[0] for row in cursor.fetchall()]

    def get_previous_round_data(self, year_month: str, input_month: str,
                                 channel_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """이전 라운드 데이터 조회 (변동 비교용)

        Args:
            year_month: 대상 년월 (YYYY-MM)
            input_month: 현재 InputMonth
            channel_id: 채널 ID (선택)

        Returns:
            List[Dict]: 직전 InputMonth의 데이터 (UniqueCode+ChannelID 기준 매핑용)
        """
        with get_db_cursor(commit=False) as cursor:
            where_clauses = [
                "FORMAT(t.[Date], 'yyyy-MM') = ?",
                "t.InputMonth < ?",
            ]
            params = [year_month, input_month]

            if channel_id:
                where_clauses.append("t.ChannelID = ?")
                params.append(channel_id)

            where_sql = " AND ".join(where_clauses)
            columns = ", ".join(self.SELECT_COLUMNS)

            simple_query = f"""
                SELECT {columns}
                FROM [dbo].[Expected1PRegularProduct] t
                WHERE {where_sql}
                  AND t.InputMonth = (
                      SELECT MAX(t2.InputMonth)
                      FROM [dbo].[Expected1PRegularProduct] t2
                      WHERE FORMAT(t2.[Date], 'yyyy-MM') = ?
                        AND t2.InputMonth < ?
                  )
            """
            params_simple = [year_month, input_month, year_month, input_month]
            if channel_id:
                params_simple = [year_month, input_month, channel_id, year_month, input_month]

            cursor.execute(simple_query, *params_simple)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def bulk_update_amounts(self, records: List[Dict[str, Any]], user_id: int = None) -> Dict[str, Any]:
        """인라인 편집 일괄 저장 (ExpectedAmount, ExpectedQuantity, Notes만 업데이트)"""
        total_updated = 0
        track_fields = ['ExpectedAmount', 'ExpectedQuantity', 'Notes']

        with get_db_cursor() as cursor:
            if user_id is not None:
                log_changes_bulk(cursor, self.table_name, 'Expected1PRegularID', records, track_fields, user_id)

            for record in records:
                record_id = record.get('Expected1PRegularID')
                if not record_id:
                    continue

                expected_amount = record.get('ExpectedAmount', 0) or 0
                expected_amount_ex_vat = calculate_amount_ex_vat(expected_amount)

                query = """
                    UPDATE [dbo].[Expected1PRegularProduct]
                    SET ExpectedAmount = ?,
                        ExpectedAmountExVAT = ?,
                        ExpectedQuantity = ?,
                        Notes = ?,
                        UpdatedDate = GETDATE()
                    WHERE Expected1PRegularID = ?
                """
                cursor.execute(query,
                    float(expected_amount),
                    expected_amount_ex_vat,
                    int(record.get('ExpectedQuantity', 0) or 0),
                    record.get('Notes'),
                    record_id
                )
                if cursor.rowcount > 0:
                    total_updated += 1

        return {"updated": total_updated}

    def delete_by_filter(self, year_month: str, brand_id: Optional[int] = None,
                         channel_id: Optional[int] = None,
                         input_month: Optional[str] = None) -> int:
        """필터 조건으로 일괄 삭제"""
        with get_db_cursor() as cursor:
            conditions = ["FORMAT([Date], 'yyyy-MM') = ?"]
            params = [year_month]

            if brand_id:
                conditions.append("BrandID = ?")
                params.append(brand_id)

            if channel_id:
                conditions.append("ChannelID = ?")
                params.append(channel_id)

            if input_month:
                conditions.append("InputMonth = ?")
                params.append(input_month)

            where_clause = " AND ".join(conditions)
            query = f"DELETE FROM [dbo].[Expected1PRegularProduct] WHERE {where_clause}"

            cursor.execute(query, *params)
            return cursor.rowcount
