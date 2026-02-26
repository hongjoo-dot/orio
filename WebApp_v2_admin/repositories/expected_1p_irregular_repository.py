"""
Expected1PIrregular Repository
- 사입 비정기 마스터 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor, log_changes


class Expected1PIrregularRepository(BaseRepository):
    """Expected1PIrregular 테이블 Repository"""

    # SELECT 컬럼 상수 (순서 변경 금지 - _row_to_dict 인덱스와 일치해야 함)
    SELECT_COLUMNS = (
        "p.Expected1PIrregularID", "p.IrregularName", "p.IrregularType",
        "p.StartDate", "p.StartTime", "p.EndDate", "p.EndTime",
        """CASE
            WHEN p.Status = 'CANCELLED' THEN 'CANCELLED'
            WHEN CAST(p.StartDate AS DATETIME) + CAST(ISNULL(p.StartTime, '00:00:00') AS DATETIME) > GETDATE() THEN 'SCHEDULED'
            WHEN CAST(p.EndDate AS DATETIME) + CAST(ISNULL(p.EndTime, '23:59:59') AS DATETIME) < GETDATE() THEN 'ENDED'
            ELSE 'ACTIVE'
        END AS Status""",
        "p.BrandID", "p.BrandName",
        "p.ChannelID", "p.ChannelName",
        "p.CommissionRate", "p.DiscountOwner",
        "p.CompanyShare", "p.ChannelShare",
        "p.ExpectedSalesAmount", "p.ExpectedQuantity",
        "p.Notes",
        "p.CreatedDate", "p.UpdatedDate",
        "p.InputMonth",
        "p.OliveyoungType"
    )

    def __init__(self):
        super().__init__(table_name="[dbo].[Expected1PIrregular]", id_column="Expected1PIrregularID")

    def get_select_query(self) -> str:
        """Expected1PIrregular 조회 쿼리"""
        columns = ", ".join(self.SELECT_COLUMNS)
        return f"SELECT {columns} FROM [dbo].[Expected1PIrregular] p"

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "Expected1PIrregularID": row[0],
            "IrregularName": row[1],
            "IrregularType": row[2],
            "StartDate": row[3].strftime('%Y-%m-%d') if row[3] else None,
            "StartTime": row[4].strftime('%H:%M:%S') if row[4] else None,
            "EndDate": row[5].strftime('%Y-%m-%d') if row[5] else None,
            "EndTime": row[6].strftime('%H:%M:%S') if row[6] else None,
            "Status": row[7],
            "BrandID": row[8],
            "BrandName": row[9],
            "ChannelID": row[10],
            "ChannelName": row[11],
            "CommissionRate": float(row[12]) if row[12] else None,
            "DiscountOwner": row[13],
            "CompanyShare": float(row[14]) if row[14] else None,
            "ChannelShare": float(row[15]) if row[15] else None,
            "ExpectedSalesAmount": float(row[16]) if row[16] else 0,
            "ExpectedQuantity": int(row[17]) if row[17] else 0,
            "Notes": row[18],
            "CreatedDate": row[19].strftime('%Y-%m-%d %H:%M:%S') if row[19] else None,
            "UpdatedDate": row[20].strftime('%Y-%m-%d %H:%M:%S') if row[20] else None,
            "InputMonth": row[21],
            "OliveyoungType": row[22],
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """Expected1PIrregular 전용 필터 로직"""
        if filters.get('year_month'):
            builder.where("FORMAT(p.StartDate, 'yyyy-MM') = ?", filters['year_month'])

        if filters.get('brand_id'):
            builder.where_equals("p.BrandID", filters['brand_id'])

        if filters.get('channel_id'):
            builder.where_equals("p.ChannelID", filters['channel_id'])

        if filters.get('irregular_type'):
            builder.where_equals("p.IrregularType", filters['irregular_type'])

        if filters.get('input_month'):
            builder.where_equals("p.InputMonth", filters['input_month'])

        if filters.get('status'):
            status_val = filters['status']
            if status_val == 'CANCELLED':
                builder.where_equals("p.Status", 'CANCELLED')
            elif status_val == 'SCHEDULED':
                builder.where("p.Status != 'CANCELLED'")
                builder.where("CAST(p.StartDate AS DATETIME) + CAST(ISNULL(p.StartTime, '00:00:00') AS DATETIME) > GETDATE()")
            elif status_val == 'ENDED':
                builder.where("p.Status != 'CANCELLED'")
                builder.where("CAST(p.EndDate AS DATETIME) + CAST(ISNULL(p.EndTime, '23:59:59') AS DATETIME) < GETDATE()")
            elif status_val == 'ACTIVE':
                builder.where("p.Status != 'CANCELLED'")
                builder.where("CAST(p.StartDate AS DATETIME) + CAST(ISNULL(p.StartTime, '00:00:00') AS DATETIME) <= GETDATE()")
                builder.where("CAST(p.EndDate AS DATETIME) + CAST(ISNULL(p.EndTime, '23:59:59') AS DATETIME) >= GETDATE()")

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """Expected1PIrregular 전용 QueryBuilder 생성 (사입 1P/2P 채널만)"""
        builder = QueryBuilder("[dbo].[Expected1PIrregular] p")
        builder.select(*self.SELECT_COLUMNS)
        builder.join("[dbo].[Channel] c", "p.ChannelID = c.ChannelID", "INNER JOIN")
        builder.where("c.ContractType IN ('1P', '2P')")

        if filters:
            self._apply_filters(builder, filters)

        return builder

    def create(self, data: Dict[str, Any], user_id: Optional[int] = None) -> str:
        """새 Expected1PIrregular 레코드 생성"""
        with get_db_cursor() as cursor:
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            col_str = ', '.join(columns)
            query = f"INSERT INTO {self.table_name} ({col_str}) VALUES ({placeholders})"
            params = [data[col] for col in columns]
            cursor.execute(query, *params)

            expected_1p_irregular_id = data.get('Expected1PIrregularID')
            if user_id is not None:
                log_changes(cursor, self.table_name, expected_1p_irregular_id, None, data, user_id)

            return expected_1p_irregular_id

    def bulk_upsert(self, records: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, Any]:
        """일괄 INSERT/UPDATE"""
        total_inserted = 0
        total_updated = 0
        duplicates = []

        # 1단계: 신규 레코드(ID 없음)에 대해 중복 체크
        with get_db_cursor(commit=False) as cursor:
            for idx, record in enumerate(records):
                expected_1p_irregular_id = record.get('Expected1PIrregularID')
                row_num = idx + 2

                if not expected_1p_irregular_id:
                    check_query = """
                        SELECT Expected1PIrregularID FROM [dbo].[Expected1PIrregular]
                        WHERE BrandID = ? AND ChannelID = ? AND IrregularType = ?
                          AND StartDate = ? AND IrregularName = ?
                          AND ISNULL(OliveyoungType, '') = ISNULL(?, '')
                    """
                    cursor.execute(check_query,
                        record.get('BrandID'),
                        record.get('ChannelID'),
                        record.get('IrregularType'),
                        record.get('StartDate'),
                        record.get('IrregularName'),
                        record.get('OliveyoungType')
                    )
                    existing = cursor.fetchone()

                    if existing:
                        duplicates.append({
                            'row': row_num,
                            'irregular_name': record.get('IrregularName'),
                            'start_date': record.get('StartDate'),
                            'brand_name': record.get('BrandName'),
                            'channel_name': record.get('ChannelName'),
                            'irregular_type': record.get('IrregularType'),
                            'existing_id': existing[0]
                        })

        if duplicates:
            return {"inserted": 0, "updated": 0, "duplicates": duplicates}

        # 2단계: INSERT/UPDATE 실행
        with get_db_cursor() as cursor:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]

                for record in batch:
                    expected_1p_irregular_id = record.get('Expected1PIrregularID')

                    if expected_1p_irregular_id and self.exists(expected_1p_irregular_id):
                        update_query = """
                            UPDATE [dbo].[Expected1PIrregular]
                            SET IrregularName = ?,
                                EndDate = ?,
                                EndTime = ?,
                                StartTime = ?,
                                CommissionRate = ?,
                                DiscountOwner = ?,
                                CompanyShare = ?,
                                ChannelShare = ?,
                                ExpectedSalesAmount = ?,
                                ExpectedQuantity = ?,
                                Notes = ?,
                                InputMonth = ?,
                                OliveyoungType = ?,
                                UpdatedDate = GETDATE()
                            WHERE Expected1PIrregularID = ?
                        """
                        params = [
                            record.get('IrregularName'),
                            record.get('EndDate'),
                            record.get('EndTime', '23:59:59'),
                            record.get('StartTime', '00:00:00'),
                            record.get('CommissionRate'),
                            record.get('DiscountOwner'),
                            record.get('CompanyShare'),
                            record.get('ChannelShare'),
                            record.get('ExpectedSalesAmount'),
                            record.get('ExpectedQuantity'),
                            record.get('Notes'),
                            record.get('InputMonth'),
                            record.get('OliveyoungType'),
                            expected_1p_irregular_id
                        ]
                        cursor.execute(update_query, *params)
                        if cursor.rowcount > 0:
                            total_updated += 1
                    else:
                        insert_query = """
                            INSERT INTO [dbo].[Expected1PIrregular]
                                (Expected1PIrregularID, IrregularName, IrregularType,
                                 StartDate, StartTime, EndDate, EndTime,
                                 Status, BrandID, BrandName, ChannelID, ChannelName,
                                 CommissionRate, DiscountOwner, CompanyShare, ChannelShare,
                                 ExpectedSalesAmount, ExpectedQuantity, Notes, InputMonth, OliveyoungType)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        params = [
                            record.get('Expected1PIrregularID'),
                            record.get('IrregularName'),
                            record.get('IrregularType'),
                            record.get('StartDate'),
                            record.get('StartTime', '00:00:00'),
                            record.get('EndDate'),
                            record.get('EndTime', '23:59:59'),
                            record.get('Status', 'SCHEDULED'),
                            record.get('BrandID'),
                            record.get('BrandName'),
                            record.get('ChannelID'),
                            record.get('ChannelName'),
                            record.get('CommissionRate'),
                            record.get('DiscountOwner'),
                            record.get('CompanyShare'),
                            record.get('ChannelShare'),
                            record.get('ExpectedSalesAmount'),
                            record.get('ExpectedQuantity'),
                            record.get('Notes'),
                            record.get('InputMonth'),
                            record.get('OliveyoungType'),
                        ]
                        cursor.execute(insert_query, *params)
                        if cursor.rowcount > 0:
                            total_inserted += 1

        return {"inserted": total_inserted, "updated": total_updated, "duplicates": []}

    def get_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Expected1PIrregularID 리스트로 데이터 조회"""
        if not ids:
            return []

        with get_db_cursor(commit=False) as cursor:
            placeholders = ','.join(['?' for _ in ids])
            columns = ", ".join(self.SELECT_COLUMNS)
            query = f"""
                SELECT {columns}
                FROM [dbo].[Expected1PIrregular] p
                WHERE p.Expected1PIrregularID IN ({placeholders})
                ORDER BY p.StartDate DESC
            """
            cursor.execute(query, *ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_year_months(self) -> List[str]:
        """저장된 데이터의 년월 목록 조회 (사입 1P/2P 채널만)"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT FORMAT(p.StartDate, 'yyyy-MM') as YearMonth
                FROM [dbo].[Expected1PIrregular] p
                INNER JOIN [dbo].[Channel] c ON p.ChannelID = c.ChannelID
                WHERE c.ContractType IN ('1P', '2P')
                ORDER BY YearMonth DESC
            """
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def get_irregular_types(self) -> List[Dict[str, str]]:
        """IrregularType 테이블에서 행사유형 목록 조회"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT TypeCode, TypeName, DisplayName, Category
                FROM [dbo].[IrregularType]
                ORDER BY DisplayName
            """
            cursor.execute(query)
            return [
                {
                    "TypeCode": row[0],
                    "TypeName": row[1],
                    "DisplayName": row[2],
                    "Category": row[3]
                }
                for row in cursor.fetchall()
            ]

    def get_irregular_type_display_names(self) -> List[str]:
        """행사유형 DisplayName 목록만 조회"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT DisplayName
                FROM [dbo].[IrregularType]
                WHERE DisplayName IS NOT NULL AND DisplayName != ''
                ORDER BY DisplayName
            """
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def get_statuses(self) -> List[str]:
        """상태 목록 반환"""
        return ['SCHEDULED', 'ACTIVE', 'ENDED', 'CANCELLED']

    def bulk_delete(self, id_values: List[Any], batch_size: int = 1000) -> int:
        """일괄 삭제 (IrregularProduct도 함께 삭제)"""
        total_deleted = 0

        with get_db_cursor() as cursor:
            for i in range(0, len(id_values), batch_size):
                batch = id_values[i:i + batch_size]
                if not batch:
                    continue

                placeholders = ','.join(['?' for _ in batch])

                # IrregularProduct 먼저 삭제 (FK 제약)
                cursor.execute(
                    f"DELETE FROM [dbo].[Expected1PIrregularProduct] WHERE Expected1PIrregularID IN ({placeholders})",
                    *batch
                )

                # Irregular 삭제
                cursor.execute(
                    f"DELETE FROM [dbo].[Expected1PIrregular] WHERE Expected1PIrregularID IN ({placeholders})",
                    *batch
                )
                total_deleted += cursor.rowcount

        return total_deleted

    def get_input_months(self, year_month: Optional[str] = None) -> List[str]:
        """InputMonth 목록 조회 (사입 1P/2P 채널만)"""
        with get_db_cursor(commit=False) as cursor:
            where_clauses = ["c.ContractType IN ('1P', '2P')"]
            params = []

            if year_month:
                where_clauses.append("FORMAT(p.StartDate, 'yyyy-MM') = ?")
                params.append(year_month)

            where_sql = " AND ".join(where_clauses)
            query = f"""
                SELECT DISTINCT p.InputMonth
                FROM [dbo].[Expected1PIrregular] p
                INNER JOIN [dbo].[Channel] c ON p.ChannelID = c.ChannelID
                WHERE {where_sql}
                ORDER BY p.InputMonth DESC
            """
            cursor.execute(query, *params)
            return [row[0] for row in cursor.fetchall() if row[0]]

    def get_master_summary(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """마스터 패널용 - 비정기 목록 + 상품 수 + 상품 예상매출/수량 합계 (사입 1P/2P 채널만)"""
        with get_db_cursor(commit=False) as cursor:
            where_clauses = ["c.ContractType IN ('1P', '2P')"]
            params = []

            if filters:
                if filters.get('year_month'):
                    where_clauses.append("FORMAT(p.StartDate, 'yyyy-MM') = ?")
                    params.append(filters['year_month'])
                if filters.get('brand_id'):
                    where_clauses.append("p.BrandID = ?")
                    params.append(filters['brand_id'])
                if filters.get('channel_id'):
                    where_clauses.append("p.ChannelID = ?")
                    params.append(filters['channel_id'])
                if filters.get('irregular_type'):
                    where_clauses.append("p.IrregularType = ?")
                    params.append(filters['irregular_type'])
                if filters.get('input_month'):
                    where_clauses.append("p.InputMonth = ?")
                    params.append(filters['input_month'])
                if filters.get('status'):
                    status_val = filters['status']
                    if status_val == 'CANCELLED':
                        where_clauses.append("p.Status = 'CANCELLED'")
                    elif status_val == 'SCHEDULED':
                        where_clauses.append("p.Status != 'CANCELLED'")
                        where_clauses.append("CAST(p.StartDate AS DATETIME) + CAST(ISNULL(p.StartTime, '00:00:00') AS DATETIME) > GETDATE()")
                    elif status_val == 'ENDED':
                        where_clauses.append("p.Status != 'CANCELLED'")
                        where_clauses.append("CAST(p.EndDate AS DATETIME) + CAST(ISNULL(p.EndTime, '23:59:59') AS DATETIME) < GETDATE()")
                    elif status_val == 'ACTIVE':
                        where_clauses.append("p.Status != 'CANCELLED'")
                        where_clauses.append("CAST(p.StartDate AS DATETIME) + CAST(ISNULL(p.StartTime, '00:00:00') AS DATETIME) <= GETDATE()")
                        where_clauses.append("CAST(p.EndDate AS DATETIME) + CAST(ISNULL(p.EndTime, '23:59:59') AS DATETIME) >= GETDATE()")

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            status_case = """CASE
                WHEN p.Status = 'CANCELLED' THEN 'CANCELLED'
                WHEN CAST(p.StartDate AS DATETIME) + CAST(ISNULL(p.StartTime, '00:00:00') AS DATETIME) > GETDATE() THEN 'SCHEDULED'
                WHEN CAST(p.EndDate AS DATETIME) + CAST(ISNULL(p.EndTime, '23:59:59') AS DATETIME) < GETDATE() THEN 'ENDED'
                ELSE 'ACTIVE'
            END"""

            query = f"""
                SELECT p.Expected1PIrregularID, p.IrregularName, p.IrregularType,
                       p.StartDate, p.EndDate,
                       p.BrandID, p.BrandName, p.ChannelID, p.ChannelName,
                       {status_case} AS ComputedStatus,
                       p.CommissionRate, p.DiscountOwner,
                       ISNULL(cnt.ProductCount, 0) AS ProductCount,
                       ISNULL(cnt.TotalSalesAmount, 0) AS TotalSalesAmount,
                       ISNULL(cnt.TotalQuantity, 0) AS TotalQuantity
                FROM [dbo].[Expected1PIrregular] p
                INNER JOIN [dbo].[Channel] c ON p.ChannelID = c.ChannelID
                LEFT JOIN (
                    SELECT Expected1PIrregularID,
                           COUNT(*) AS ProductCount,
                           SUM(ISNULL(ExpectedSalesAmount, 0)) AS TotalSalesAmount,
                           SUM(ISNULL(ExpectedQuantity, 0)) AS TotalQuantity
                    FROM [dbo].[Expected1PIrregularProduct]
                    GROUP BY Expected1PIrregularID
                ) cnt ON p.Expected1PIrregularID = cnt.Expected1PIrregularID
                WHERE {where_sql}
                ORDER BY p.StartDate DESC, p.IrregularName ASC
            """
            cursor.execute(query, *params)
            return [{
                "Expected1PIrregularID": row[0],
                "IrregularName": row[1],
                "IrregularType": row[2],
                "StartDate": row[3].strftime('%Y-%m-%d') if row[3] else None,
                "EndDate": row[4].strftime('%Y-%m-%d') if row[4] else None,
                "BrandID": row[5],
                "BrandName": row[6],
                "ChannelID": row[7],
                "ChannelName": row[8],
                "Status": row[9],
                "CommissionRate": float(row[10]) if row[10] else None,
                "DiscountOwner": row[11],
                "ProductCount": row[12],
                "TotalSalesAmount": float(row[13]) if row[13] else 0,
                "TotalQuantity": int(row[14]) if row[14] else 0,
            } for row in cursor.fetchall()]

    def get_max_sequences_by_prefixes(self, prefixes: List[str]) -> Dict[str, int]:
        """여러 접두사에 대한 현재 최대 순번 일괄 조회"""
        if not prefixes:
            return {}

        result = {prefix: 0 for prefix in prefixes}

        with get_db_cursor(commit=False) as cursor:
            unique_prefixes = list(set(prefixes))

            for prefix in unique_prefixes:
                query = """
                    SELECT MAX(CAST(RIGHT(Expected1PIrregularID, 2) AS INT))
                    FROM [dbo].[Expected1PIrregular]
                    WHERE Expected1PIrregularID LIKE ? + '%'
                      AND LEN(Expected1PIrregularID) > 2
                """
                cursor.execute(query, prefix)
                row = cursor.fetchone()

                if row and row[0] is not None:
                    result[prefix] = row[0]

        return result
