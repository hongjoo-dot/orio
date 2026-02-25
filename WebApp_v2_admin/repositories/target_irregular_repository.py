"""
TargetIrregularProduct Repository
- 비정기 목표 Irregular 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor, log_changes_bulk
from utils.helpers import calculate_amount_ex_vat


class TargetIrregularRepository(BaseRepository):
    """TargetIrregularProduct 테이블 Repository"""

    # SELECT 컬럼 상수 (순서 변경 금지 - _row_to_dict 인덱스와 일치해야 함)
    SELECT_COLUMNS = (
        "t.TargetIrregularID",
        "t.IrregularID", "t.IrregularName",
        "t.StartDate", "t.StartTime", "t.EndDate", "t.EndTime",
        "t.BrandID", "t.BrandName",
        "t.ChannelID", "t.ChannelName",
        "t.ERPCode", "t.UniqueCode", "t.ProductName",
        "t.TargetAmount", "t.TargetAmountExVAT", "t.TargetQuantity",
        "t.Notes", "t.IrregularType",
        "t.CreatedDate", "t.UpdatedDate"
    )

    def __init__(self):
        super().__init__(table_name="[dbo].[TargetIrregularProduct]", id_column="TargetIrregularID")

    def get_select_query(self) -> str:
        """TargetIrregularProduct 조회 쿼리"""
        columns = ", ".join(self.SELECT_COLUMNS)
        return f"SELECT {columns} FROM [dbo].[TargetIrregularProduct] t"

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "TargetIrregularID": row[0],
            "IrregularID": row[1],
            "IrregularName": row[2],
            "StartDate": row[3].strftime('%Y-%m-%d') if row[3] else None,
            "StartTime": row[4].strftime('%H:%M:%S') if row[4] else None,
            "EndDate": row[5].strftime('%Y-%m-%d') if row[5] else None,
            "EndTime": row[6].strftime('%H:%M:%S') if row[6] else None,
            "BrandID": row[7],
            "BrandName": row[8],
            "ChannelID": row[9],
            "ChannelName": row[10],
            "ERPCode": row[11],
            "UniqueCode": row[12],
            "ProductName": row[13],
            "TargetAmount": float(row[14]) if row[14] else 0,
            "TargetAmountExVAT": float(row[15]) if row[15] else 0,
            "TargetQuantity": int(row[16]) if row[16] else 0,
            "Notes": row[17],
            "IrregularType": row[18],
            "CreatedDate": row[19].strftime('%Y-%m-%d %H:%M:%S') if row[19] else None,
            "UpdatedDate": row[20].strftime('%Y-%m-%d %H:%M:%S') if row[20] else None,
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        TargetIrregular 전용 필터 로직

        지원하는 필터:
        - year_month: 시작일 기준 년월 (YYYY-MM 형식)
        - brand_id: BrandID 정확히 매칭
        - channel_id: ChannelID 정확히 매칭
        - irregular_type: IrregularType 정확히 매칭
        """
        if filters.get('year_month'):
            year_month = filters['year_month']
            builder.where("FORMAT(t.StartDate, 'yyyy-MM') = ?", year_month)

        if 'brand_id' in filters:
            builder.where_equals("t.BrandID", filters['brand_id'])

        if 'channel_id' in filters:
            builder.where_equals("t.ChannelID", filters['channel_id'])

        if filters.get('irregular_type'):
            builder.where_equals("t.IrregularType", filters['irregular_type'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """TargetIrregular 전용 QueryBuilder 생성"""
        builder = QueryBuilder("[dbo].[TargetIrregularProduct] t")
        builder.select(*self.SELECT_COLUMNS)

        if filters:
            self._apply_filters(builder, filters)

        return builder

    def bulk_upsert(self, records: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, Any]:
        """
        일괄 INSERT/UPDATE
        - ID가 있으면: ID 기반 UPDATE
        - ID가 없으면: 복합키 중복 체크 후 INSERT (중복 시 에러)
          * 복합키: BrandID + ChannelID + IrregularType + StartDate + UniqueCode

        Args:
            records: 삽입/수정할 레코드 리스트
            batch_size: 배치 크기

        Returns:
            Dict: {"inserted": N, "updated": M, "duplicates": [...]}
        """
        total_inserted = 0
        total_updated = 0
        duplicates = []  # 중복된 레코드 정보

        # 1단계: 신규 레코드(ID 없음)에 대해 중복 체크 먼저 수행
        with get_db_cursor() as cursor:
            for idx, record in enumerate(records):
                target_id = record.get('TargetIrregularID')
                row_num = idx + 2  # 엑셀 행 번호 (헤더 제외)

                # ID가 없는 경우만 중복 체크
                if not target_id:
                    check_query = """
                        SELECT TargetIrregularID FROM [dbo].[TargetIrregularProduct]
                        WHERE BrandID = ? AND ChannelID = ? AND IrregularType = ?
                          AND StartDate = ? AND UniqueCode = ?
                    """
                    cursor.execute(check_query,
                        record.get('BrandID'),
                        record.get('ChannelID'),
                        record.get('IrregularType'),
                        record.get('StartDate'),
                        record.get('UniqueCode')
                    )
                    existing = cursor.fetchone()

                    if existing:
                        duplicates.append({
                            'row': row_num,
                            'start_date': record.get('StartDate'),
                            'unique_code': record.get('UniqueCode'),
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
                    target_id = record.get('TargetIrregularID')

                    # TargetAmountExVAT 자동 계산 (VAT 10% 제외)
                    target_amount = record.get('TargetAmount') or 0
                    target_amount_ex_vat = calculate_amount_ex_vat(target_amount)

                    if target_id:
                        # ID 기반 UPDATE (IrregularID는 변경 불가)
                        update_query = """
                            UPDATE [dbo].[TargetIrregularProduct]
                            SET IrregularName = ?,
                                StartTime = ?,
                                EndTime = ?,
                                TargetAmount = ?,
                                TargetAmountExVAT = ?,
                                TargetQuantity = ?,
                                Notes = ?,
                                UpdatedDate = GETDATE()
                            WHERE TargetIrregularID = ?
                        """
                        params = [
                            record.get('IrregularName'),
                            record.get('StartTime', '00:00:00'),
                            record.get('EndTime', '23:59:59'),
                            target_amount,
                            target_amount_ex_vat,
                            record.get('TargetQuantity'),
                            record.get('Notes'),
                            target_id
                        ]
                        cursor.execute(update_query, *params)
                        if cursor.rowcount > 0:
                            total_updated += 1
                    else:
                        # 신규 INSERT
                        insert_query = """
                            INSERT INTO [dbo].[TargetIrregularProduct]
                                (IrregularID, IrregularName, StartDate, StartTime, EndDate, EndTime,
                                 BrandID, BrandName, ChannelID, ChannelName,
                                 ERPCode, UniqueCode, ProductName, TargetAmount, TargetAmountExVAT, TargetQuantity, Notes, IrregularType)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        params = [
                            record.get('IrregularID'),
                            record.get('IrregularName'),
                            record.get('StartDate'),
                            record.get('StartTime', '00:00:00'),
                            record.get('EndDate'),
                            record.get('EndTime', '23:59:59'),
                            record.get('BrandID'),
                            record.get('BrandName'),
                            record.get('ChannelID'),
                            record.get('ChannelName'),
                            record.get('ERPCode'),
                            record.get('UniqueCode'),
                            record.get('ProductName'),
                            target_amount,
                            target_amount_ex_vat,
                            record.get('TargetQuantity'),
                            record.get('Notes'),
                            record.get('IrregularType'),
                        ]
                        cursor.execute(insert_query, *params)
                        if cursor.rowcount > 0:
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
                FROM [dbo].[TargetIrregularProduct] t
                WHERE t.TargetIrregularID IN ({placeholders})
                ORDER BY t.StartDate DESC
            """
            cursor.execute(query, *ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_year_months(self) -> List[str]:
        """저장된 데이터의 년월 목록 조회 (StartDate 기준, 위탁 3P 채널만)"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT FORMAT(t.StartDate, 'yyyy-MM') as YearMonth
                FROM [dbo].[TargetIrregularProduct] t
                INNER JOIN [dbo].[Channel] c ON t.ChannelID = c.ChannelID
                WHERE c.ContractType = '3P'
                ORDER BY YearMonth DESC
            """
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def get_groups_summary(self, year_month: str, brand_id: Optional[int] = None,
                           channel_id: Optional[int] = None,
                           irregular_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """그룹별 요약 조회 (채널+행사명+행사유형 기준, 마스터 패널용, 위탁 3P 채널만)"""
        with get_db_cursor(commit=False) as cursor:
            where_clauses = ["FORMAT(t.StartDate, 'yyyy-MM') = ?", "c.ContractType = '3P'"]
            params = [year_month]

            if brand_id is not None:
                where_clauses.append("t.BrandID = ?")
                params.append(brand_id)

            if channel_id is not None:
                where_clauses.append("t.ChannelID = ?")
                params.append(channel_id)

            if irregular_type:
                where_clauses.append("t.IrregularType = ?")
                params.append(irregular_type)

            where_sql = " AND ".join(where_clauses)

            query = f"""
                SELECT t.ChannelID, t.ChannelName, t.IrregularName, t.IrregularType,
                       COUNT(*) as ProductCount,
                       ISNULL(SUM(t.TargetAmount), 0) as TotalAmount,
                       ISNULL(SUM(t.TargetQuantity), 0) as TotalQuantity,
                       MIN(t.StartDate) as StartDate,
                       MAX(t.EndDate) as EndDate
                FROM [dbo].[TargetIrregularProduct] t
                INNER JOIN [dbo].[Channel] c ON t.ChannelID = c.ChannelID
                WHERE {where_sql}
                GROUP BY t.ChannelID, t.ChannelName, t.IrregularName, t.IrregularType
                ORDER BY t.ChannelName ASC, t.IrregularName ASC
            """
            cursor.execute(query, *params)
            results = []
            for row in cursor.fetchall():
                ch_id = row[0]
                irreg_name = row[2] or ''
                irreg_type = row[3] or ''
                group_key = f"{ch_id}|{irreg_name}|{irreg_type}"
                results.append({
                    "GroupKey": group_key,
                    "ChannelID": ch_id,
                    "ChannelName": row[1],
                    "IrregularName": irreg_name,
                    "IrregularType": irreg_type,
                    "ProductCount": row[4],
                    "TotalAmount": float(row[5]) if row[5] else 0,
                    "TotalQuantity": int(row[6]) if row[6] else 0,
                    "StartDate": row[7].strftime('%Y-%m-%d') if row[7] else None,
                    "EndDate": row[8].strftime('%Y-%m-%d') if row[8] else None,
                })
            return results

    def get_by_group(self, channel_id: int, irregular_name: str, irregular_type: str,
                     year_month: str, brand_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """특정 그룹의 상품 목록 조회 (디테일 패널용)"""
        with get_db_cursor(commit=False) as cursor:
            columns = ", ".join(self.SELECT_COLUMNS)
            where_clauses = [
                "t.ChannelID = ?",
                "t.IrregularName = ?",
                "t.IrregularType = ?",
                "FORMAT(t.StartDate, 'yyyy-MM') = ?"
            ]
            params = [channel_id, irregular_name, irregular_type, year_month]

            if brand_id is not None:
                where_clauses.append("t.BrandID = ?")
                params.append(brand_id)

            where_sql = " AND ".join(where_clauses)

            query = f"""
                SELECT {columns}
                FROM [dbo].[TargetIrregularProduct] t
                WHERE {where_sql}
                ORDER BY t.ERPCode ASC
            """
            cursor.execute(query, *params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def bulk_update_irregular_amounts(self, records: List[Dict[str, Any]], user_id: int = None) -> Dict[str, Any]:
        """인라인 편집 일괄 저장 (TargetAmount, TargetQuantity, Notes만 업데이트)"""
        total_updated = 0
        track_fields = ['TargetAmount', 'TargetQuantity', 'Notes']

        with get_db_cursor() as cursor:
            if user_id is not None:
                log_changes_bulk(cursor, self.table_name, 'TargetIrregularID', records, track_fields, user_id)

            for record in records:
                target_id = record.get('TargetIrregularID')
                if not target_id:
                    continue

                target_amount = record.get('TargetAmount', 0) or 0
                target_amount_ex_vat = calculate_amount_ex_vat(target_amount)

                query = """
                    UPDATE [dbo].[TargetIrregularProduct]
                    SET TargetAmount = ?,
                        TargetAmountExVAT = ?,
                        TargetQuantity = ?,
                        Notes = ?,
                        UpdatedDate = GETDATE()
                    WHERE TargetIrregularID = ?
                """
                cursor.execute(query,
                    float(target_amount),
                    target_amount_ex_vat,
                    int(record.get('TargetQuantity', 0) or 0),
                    record.get('Notes'),
                    target_id
                )
                if cursor.rowcount > 0:
                    total_updated += 1

        return {"updated": total_updated}

    def get_irregular_types(self) -> List[str]:
        """저장된 데이터의 행사유형 목록 조회"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT IrregularType
                FROM [dbo].[TargetIrregularProduct]
                WHERE IrregularType IS NOT NULL AND IrregularType != ''
                ORDER BY IrregularType
            """
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def delete_by_filter(self, year_month: str, brand_id: Optional[int] = None,
                         channel_id: Optional[int] = None,
                         irregular_type: Optional[str] = None) -> int:
        """필터 조건으로 일괄 삭제"""
        with get_db_cursor() as cursor:
            conditions = ["FORMAT(StartDate, 'yyyy-MM') = ?"]
            params = [year_month]

            if brand_id:
                conditions.append("BrandID = ?")
                params.append(brand_id)

            if channel_id:
                conditions.append("ChannelID = ?")
                params.append(channel_id)

            if irregular_type:
                conditions.append("IrregularType = ?")
                params.append(irregular_type)

            where_clause = " AND ".join(conditions)
            query = f"DELETE FROM [dbo].[TargetIrregularProduct] WHERE {where_clause}"

            cursor.execute(query, *params)
            return cursor.rowcount

    def get_max_sequences_by_prefixes(self, prefixes: List[str]) -> Dict[str, int]:
        """
        여러 접두사에 대한 현재 최대 순번 일괄 조회

        Args:
            prefixes: IrregularID 접두사 리스트

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
                    FROM [dbo].[TargetIrregularProduct]
                    WHERE IrregularID LIKE ? + '%'
                      AND LEN(IrregularID) > 2
                """
                cursor.execute(query, prefix)
                row = cursor.fetchone()

                if row and row[0] is not None:
                    result[prefix] = row[0]

        return result
