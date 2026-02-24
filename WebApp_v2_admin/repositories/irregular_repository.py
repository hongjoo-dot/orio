"""
Irregular Repository
- 비정기 마스터 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor, log_changes


class IrregularRepository(BaseRepository):
    """Irregular 테이블 Repository"""

    # SELECT 컬럼 상수 (순서 변경 금지 - _row_to_dict 인덱스와 일치해야 함)
    SELECT_COLUMNS = (
        "p.IrregularID", "p.IrregularName", "p.IrregularType",
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
        "p.CreatedDate", "p.UpdatedDate"
    )

    def __init__(self):
        super().__init__(table_name="[dbo].[Irregular]", id_column="IrregularID")

    def get_select_query(self) -> str:
        """Irregular 조회 쿼리"""
        columns = ", ".join(self.SELECT_COLUMNS)
        return f"SELECT {columns} FROM [dbo].[Irregular] p"

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "IrregularID": row[0],
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
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        Irregular 전용 필터 로직

        지원하는 필터:
        - year_month: 시작일 기준 년월 (YYYY-MM 형식)
        - brand_id: BrandID 정확히 매칭
        - channel_id: ChannelID 정확히 매칭
        - irregular_type: IrregularType 정확히 매칭
        - status: Status 정확히 매칭
        """
        if filters.get('year_month'):
            builder.where("FORMAT(p.StartDate, 'yyyy-MM') = ?", filters['year_month'])

        if filters.get('brand_id'):
            builder.where_equals("p.BrandID", filters['brand_id'])

        if filters.get('channel_id'):
            builder.where_equals("p.ChannelID", filters['channel_id'])

        if filters.get('irregular_type'):
            builder.where_equals("p.IrregularType", filters['irregular_type'])

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
        """Irregular 전용 QueryBuilder 생성"""
        builder = QueryBuilder("[dbo].[Irregular] p")
        builder.select(*self.SELECT_COLUMNS)

        if filters:
            self._apply_filters(builder, filters)

        return builder

    def create(self, data: Dict[str, Any], user_id: Optional[int] = None) -> str:
        """
        새 Irregular 레코드 생성
        IrregularID는 문자열 PK (IDENTITY 아님) → 직접 INSERT

        Args:
            data: 생성할 데이터 (IrregularID 포함)
            user_id: 변경 이력 기록용 사용자 ID

        Returns:
            str: 생성된 IrregularID
        """
        with get_db_cursor() as cursor:
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            col_str = ', '.join(columns)
            query = f"INSERT INTO {self.table_name} ({col_str}) VALUES ({placeholders})"
            params = [data[col] for col in columns]
            cursor.execute(query, *params)

            irregular_id = data.get('IrregularID')
            if user_id is not None:
                log_changes(cursor, self.table_name, irregular_id, None, data, user_id)

            return irregular_id

    def bulk_upsert(self, records: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, Any]:
        """
        일괄 INSERT/UPDATE
        - IrregularID가 있으면: ID 기반 UPDATE
        - IrregularID가 없으면: 복합키 중복 체크 후 INSERT (중복 시 에러)
          * 복합키: BrandID + ChannelID + IrregularType + StartDate + IrregularName

        Returns:
            Dict: {"inserted": N, "updated": M, "duplicates": [...]}
        """
        total_inserted = 0
        total_updated = 0
        duplicates = []

        # 1단계: 신규 레코드(ID 없음)에 대해 중복 체크 먼저 수행
        with get_db_cursor(commit=False) as cursor:
            for idx, record in enumerate(records):
                irregular_id = record.get('IrregularID')
                row_num = idx + 2

                if not irregular_id:
                    check_query = """
                        SELECT IrregularID FROM [dbo].[Irregular]
                        WHERE BrandID = ? AND ChannelID = ? AND IrregularType = ?
                          AND StartDate = ? AND IrregularName = ?
                    """
                    cursor.execute(check_query,
                        record.get('BrandID'),
                        record.get('ChannelID'),
                        record.get('IrregularType'),
                        record.get('StartDate'),
                        record.get('IrregularName')
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

        # 중복이 있으면 INSERT/UPDATE 하지 않고 바로 반환
        if duplicates:
            return {"inserted": 0, "updated": 0, "duplicates": duplicates}

        # 2단계: 중복이 없으면 INSERT/UPDATE 실행
        with get_db_cursor() as cursor:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]

                for record in batch:
                    irregular_id = record.get('IrregularID')

                    if irregular_id and self.exists(irregular_id):
                        # ID 기반 UPDATE (수정 가능 필드만)
                        update_query = """
                            UPDATE [dbo].[Irregular]
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
                                UpdatedDate = GETDATE()
                            WHERE IrregularID = ?
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
                            irregular_id
                        ]
                        cursor.execute(update_query, *params)
                        if cursor.rowcount > 0:
                            total_updated += 1
                    else:
                        # 신규 INSERT
                        insert_query = """
                            INSERT INTO [dbo].[Irregular]
                                (IrregularID, IrregularName, IrregularType,
                                 StartDate, StartTime, EndDate, EndTime,
                                 Status, BrandID, BrandName, ChannelID, ChannelName,
                                 CommissionRate, DiscountOwner, CompanyShare, ChannelShare,
                                 ExpectedSalesAmount, ExpectedQuantity, Notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        params = [
                            record.get('IrregularID'),
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
                        ]
                        cursor.execute(insert_query, *params)
                        if cursor.rowcount > 0:
                            total_inserted += 1

        return {"inserted": total_inserted, "updated": total_updated, "duplicates": []}

    def get_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        """IrregularID 리스트로 데이터 조회"""
        if not ids:
            return []

        with get_db_cursor(commit=False) as cursor:
            placeholders = ','.join(['?' for _ in ids])
            columns = ", ".join(self.SELECT_COLUMNS)
            query = f"""
                SELECT {columns}
                FROM [dbo].[Irregular] p
                WHERE p.IrregularID IN ({placeholders})
                ORDER BY p.StartDate DESC
            """
            cursor.execute(query, *ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_year_months(self) -> List[str]:
        """저장된 데이터의 년월 목록 조회 (StartDate 기준)"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT FORMAT(StartDate, 'yyyy-MM') as YearMonth
                FROM [dbo].[Irregular]
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
                    f"DELETE FROM [dbo].[IrregularProduct] WHERE IrregularID IN ({placeholders})",
                    *batch
                )

                # Irregular 삭제
                cursor.execute(
                    f"DELETE FROM [dbo].[Irregular] WHERE IrregularID IN ({placeholders})",
                    *batch
                )
                total_deleted += cursor.rowcount

        return total_deleted

    def get_master_summary(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """마스터 패널용 - 비정기 목록 + 상품 수 + 상품 예상매출/수량 합계"""
        with get_db_cursor(commit=False) as cursor:
            where_clauses = []
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
                SELECT p.IrregularID, p.IrregularName, p.IrregularType,
                       p.StartDate, p.EndDate,
                       p.BrandID, p.BrandName, p.ChannelID, p.ChannelName,
                       {status_case} AS ComputedStatus,
                       p.CommissionRate, p.DiscountOwner,
                       ISNULL(cnt.ProductCount, 0) AS ProductCount,
                       ISNULL(cnt.TotalSalesAmount, 0) AS TotalSalesAmount,
                       ISNULL(cnt.TotalQuantity, 0) AS TotalQuantity
                FROM [dbo].[Irregular] p
                LEFT JOIN (
                    SELECT IrregularID,
                           COUNT(*) AS ProductCount,
                           SUM(ISNULL(ExpectedSalesAmount, 0)) AS TotalSalesAmount,
                           SUM(ISNULL(ExpectedQuantity, 0)) AS TotalQuantity
                    FROM [dbo].[IrregularProduct]
                    GROUP BY IrregularID
                ) cnt ON p.IrregularID = cnt.IrregularID
                WHERE {where_sql}
                ORDER BY p.StartDate DESC, p.IrregularName ASC
            """
            cursor.execute(query, *params)
            return [{
                "IrregularID": row[0],
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
        """
        여러 접두사에 대한 현재 최대 순번 일괄 조회

        Args:
            prefixes: IrregularID 접두사 리스트 (예: ["OREN2501"])

        Returns:
            Dict[str, int]: {prefix: max_sequence} 매핑
        """
        if not prefixes:
            return {}

        result = {prefix: 0 for prefix in prefixes}

        with get_db_cursor(commit=False) as cursor:
            unique_prefixes = list(set(prefixes))

            for prefix in unique_prefixes:
                query = """
                    SELECT MAX(CAST(RIGHT(IrregularID, 2) AS INT))
                    FROM [dbo].[Irregular]
                    WHERE IrregularID LIKE ? + '%'
                      AND LEN(IrregularID) > 2
                """
                cursor.execute(query, prefix)
                row = cursor.fetchone()

                if row and row[0] is not None:
                    result[prefix] = row[0]

        return result
