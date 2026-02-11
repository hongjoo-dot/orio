"""
TargetBaseProduct Repository
- 정기 목표 Regular 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


class TargetBaseRepository(BaseRepository):
    """TargetBaseProduct 테이블 Repository"""

    # SELECT 컬럼 상수 (순서 변경 금지 - _row_to_dict 인덱스와 일치해야 함)
    SELECT_COLUMNS = (
        "t.TargetBaseID", "t.[Date]",
        "t.BrandID", "t.BrandName",
        "t.ChannelID", "t.ChannelName",
        "t.ERPCode", "t.UniqueCode", "t.ProductName",
        "t.TargetAmount", "t.TargetAmountExVAT", "t.TargetQuantity",
        "t.Notes", "t.CreatedDate", "t.UpdatedDate"
    )

    def __init__(self):
        super().__init__(table_name="[dbo].[TargetBaseProduct]", id_column="TargetBaseID")

    def get_select_query(self) -> str:
        """TargetBaseProduct 조회 쿼리"""
        columns = ", ".join(self.SELECT_COLUMNS)
        return f"SELECT {columns} FROM [dbo].[TargetBaseProduct] t"

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "TargetBaseID": row[0],
            "Date": row[1].strftime('%Y-%m-%d') if row[1] else None,
            "BrandID": row[2],
            "BrandName": row[3],
            "ChannelID": row[4],
            "ChannelName": row[5],
            "ERPCode": row[6],
            "UniqueCode": row[7],
            "ProductName": row[8],
            "TargetAmount": float(row[9]) if row[9] else 0,
            "TargetAmountExVAT": float(row[10]) if row[10] else 0,
            "TargetQuantity": int(row[11]) if row[11] else 0,
            "Notes": row[12],
            "CreatedDate": row[13].strftime('%Y-%m-%d %H:%M:%S') if row[13] else None,
            "UpdatedDate": row[14].strftime('%Y-%m-%d %H:%M:%S') if row[14] else None,
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        TargetBase 전용 필터 로직

        지원하는 필터:
        - year_month: 년월 (YYYY-MM 형식)
        - brand_id: BrandID 정확히 매칭
        - channel_id: ChannelID 정확히 매칭
        """
        if filters.get('year_month'):
            year_month = filters['year_month']
            builder.where("FORMAT(t.[Date], 'yyyy-MM') = ?", year_month)

        if 'brand_id' in filters:
            builder.where_equals("t.BrandID", filters['brand_id'])

        if 'channel_id' in filters:
            builder.where_equals("t.ChannelID", filters['channel_id'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """TargetBase 전용 QueryBuilder 생성"""
        builder = QueryBuilder("[dbo].[TargetBaseProduct] t")
        builder.select(*self.SELECT_COLUMNS)

        if filters:
            self._apply_filters(builder, filters)

        return builder

    def bulk_upsert(self, records: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, Any]:
        """
        일괄 INSERT/UPDATE
        - ID가 있으면: ID 기반 UPDATE
        - ID가 없으면: 복합키 중복 체크 후 INSERT (중복 시 에러)

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
                target_id = record.get('TargetBaseID')
                row_num = idx + 2  # 엑셀 행 번호 (헤더 제외)

                # ID가 없는 경우만 중복 체크
                if not target_id:
                    check_query = """
                        SELECT TargetBaseID FROM [dbo].[TargetBaseProduct]
                        WHERE [Date] = ? AND UniqueCode = ? AND ChannelID = ?
                    """
                    cursor.execute(check_query,
                        record.get('Date'),
                        record.get('UniqueCode'),
                        record.get('ChannelID')
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

        # 중복이 있으면 INSERT/UPDATE 하지 않고 바로 반환
        if duplicates:
            return {"inserted": 0, "updated": 0, "duplicates": duplicates}

        # 2단계: 중복이 없으면 INSERT/UPDATE 실행
        with get_db_cursor() as cursor:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]

                for record in batch:
                    target_id = record.get('TargetBaseID')

                    # TargetAmountExVAT 자동 계산 (VAT 10% 제외)
                    target_amount = record.get('TargetAmount') or 0
                    target_amount_ex_vat = round(float(target_amount) / 1.1, 2) if target_amount else 0

                    if target_id:
                        # ID 기반 UPDATE
                        update_query = """
                            UPDATE [dbo].[TargetBaseProduct]
                            SET [Date] = ?,
                                BrandID = ?,
                                BrandName = ?,
                                ChannelID = ?,
                                ChannelName = ?,
                                ERPCode = ?,
                                UniqueCode = ?,
                                ProductName = ?,
                                TargetAmount = ?,
                                TargetAmountExVAT = ?,
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
                            record.get('ERPCode'),
                            record.get('UniqueCode'),
                            record.get('ProductName'),
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
                            INSERT INTO [dbo].[TargetBaseProduct]
                            ([Date], BrandID, BrandName, ChannelID, ChannelName,
                             ERPCode, UniqueCode, ProductName, TargetAmount, TargetAmountExVAT, TargetQuantity, Notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                            target_amount,
                            target_amount_ex_vat,
                            record.get('TargetQuantity'),
                            record.get('Notes'),
                        ]
                        cursor.execute(insert_query, *params)
                        total_inserted += 1

        return {"inserted": total_inserted, "updated": total_updated, "duplicates": []}

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
            columns = ", ".join(self.SELECT_COLUMNS)
            query = f"""
                SELECT {columns}
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
