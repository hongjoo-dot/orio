"""
Promotion Repository
- 행사 마스터 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


class PromotionRepository(BaseRepository):
    """Promotion 테이블 Repository"""

    # SELECT 컬럼 상수 (순서 변경 금지 - _row_to_dict 인덱스와 일치해야 함)
    SELECT_COLUMNS = (
        "p.PromotionID", "p.PromotionName", "p.PromotionType",
        "p.StartDate", "p.StartTime", "p.EndDate", "p.EndTime",
        "p.Status",
        "p.BrandID", "p.BrandName",
        "p.ChannelID", "p.ChannelName",
        "p.CommissionRate", "p.DiscountOwner",
        "p.CompanyShare", "p.ChannelShare",
        "p.ExpectedSalesAmount", "p.ExpectedQuantity",
        "p.Notes",
        "p.CreatedDate", "p.UpdatedDate"
    )

    def __init__(self):
        super().__init__(table_name="[dbo].[Promotion]", id_column="PromotionID")

    def get_select_query(self) -> str:
        """Promotion 조회 쿼리"""
        columns = ", ".join(self.SELECT_COLUMNS)
        return f"SELECT {columns} FROM [dbo].[Promotion] p"

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "PromotionID": row[0],
            "PromotionName": row[1],
            "PromotionType": row[2],
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
        Promotion 전용 필터 로직

        지원하는 필터:
        - year_month: 시작일 기준 년월 (YYYY-MM 형식)
        - brand_id: BrandID 정확히 매칭
        - channel_id: ChannelID 정확히 매칭
        - promotion_type: PromotionType 정확히 매칭
        - status: Status 정확히 매칭
        """
        if filters.get('year_month'):
            builder.where("FORMAT(p.StartDate, 'yyyy-MM') = ?", filters['year_month'])

        if filters.get('brand_id'):
            builder.where_equals("p.BrandID", filters['brand_id'])

        if filters.get('channel_id'):
            builder.where_equals("p.ChannelID", filters['channel_id'])

        if filters.get('promotion_type'):
            builder.where_equals("p.PromotionType", filters['promotion_type'])

        if filters.get('status'):
            builder.where_equals("p.Status", filters['status'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """Promotion 전용 QueryBuilder 생성"""
        builder = QueryBuilder("[dbo].[Promotion] p")
        builder.select(*self.SELECT_COLUMNS)

        if filters:
            self._apply_filters(builder, filters)

        return builder

    def create(self, data: Dict[str, Any]) -> str:
        """
        새 Promotion 레코드 생성
        PromotionID는 문자열 PK (IDENTITY 아님) → 직접 INSERT

        Args:
            data: 생성할 데이터 (PromotionID 포함)

        Returns:
            str: 생성된 PromotionID
        """
        with get_db_cursor() as cursor:
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            col_str = ', '.join(columns)
            query = f"INSERT INTO {self.table_name} ({col_str}) VALUES ({placeholders})"
            params = [data[col] for col in columns]
            cursor.execute(query, *params)
            return data.get('PromotionID')

    def bulk_upsert(self, records: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, Any]:
        """
        일괄 INSERT/UPDATE
        - PromotionID가 있으면: ID 기반 UPDATE
        - PromotionID가 없으면: 복합키 중복 체크 후 INSERT (중복 시 에러)
          * 복합키: BrandID + ChannelID + PromotionType + StartDate + PromotionName

        Returns:
            Dict: {"inserted": N, "updated": M, "duplicates": [...]}
        """
        total_inserted = 0
        total_updated = 0
        duplicates = []

        # 1단계: 신규 레코드(ID 없음)에 대해 중복 체크 먼저 수행
        with get_db_cursor(commit=False) as cursor:
            for idx, record in enumerate(records):
                promotion_id = record.get('PromotionID')
                row_num = idx + 2

                if not promotion_id:
                    check_query = """
                        SELECT PromotionID FROM [dbo].[Promotion]
                        WHERE BrandID = ? AND ChannelID = ? AND PromotionType = ?
                          AND StartDate = ? AND PromotionName = ?
                    """
                    cursor.execute(check_query,
                        record.get('BrandID'),
                        record.get('ChannelID'),
                        record.get('PromotionType'),
                        record.get('StartDate'),
                        record.get('PromotionName')
                    )
                    existing = cursor.fetchone()

                    if existing:
                        duplicates.append({
                            'row': row_num,
                            'promotion_name': record.get('PromotionName'),
                            'start_date': record.get('StartDate'),
                            'brand_name': record.get('BrandName'),
                            'channel_name': record.get('ChannelName'),
                            'promotion_type': record.get('PromotionType'),
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
                    promotion_id = record.get('PromotionID')

                    if promotion_id and self.exists(promotion_id):
                        # ID 기반 UPDATE (수정 가능 필드만)
                        update_query = """
                            UPDATE [dbo].[Promotion]
                            SET PromotionName = ?,
                                EndDate = ?,
                                EndTime = ?,
                                StartTime = ?,
                                Status = ?,
                                CommissionRate = ?,
                                DiscountOwner = ?,
                                CompanyShare = ?,
                                ChannelShare = ?,
                                ExpectedSalesAmount = ?,
                                ExpectedQuantity = ?,
                                Notes = ?,
                                UpdatedDate = GETDATE()
                            WHERE PromotionID = ?
                        """
                        params = [
                            record.get('PromotionName'),
                            record.get('EndDate'),
                            record.get('EndTime', '00:00:00'),
                            record.get('StartTime', '00:00:00'),
                            record.get('Status', 'SCHEDULED'),
                            record.get('CommissionRate'),
                            record.get('DiscountOwner'),
                            record.get('CompanyShare'),
                            record.get('ChannelShare'),
                            record.get('ExpectedSalesAmount'),
                            record.get('ExpectedQuantity'),
                            record.get('Notes'),
                            promotion_id
                        ]
                        cursor.execute(update_query, *params)
                        if cursor.rowcount > 0:
                            total_updated += 1
                    else:
                        # 신규 INSERT
                        insert_query = """
                            INSERT INTO [dbo].[Promotion]
                                (PromotionID, PromotionName, PromotionType,
                                 StartDate, StartTime, EndDate, EndTime,
                                 Status, BrandID, BrandName, ChannelID, ChannelName,
                                 CommissionRate, DiscountOwner, CompanyShare, ChannelShare,
                                 ExpectedSalesAmount, ExpectedQuantity, Notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        params = [
                            record.get('PromotionID'),
                            record.get('PromotionName'),
                            record.get('PromotionType'),
                            record.get('StartDate'),
                            record.get('StartTime', '00:00:00'),
                            record.get('EndDate'),
                            record.get('EndTime', '00:00:00'),
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
        """PromotionID 리스트로 데이터 조회"""
        if not ids:
            return []

        with get_db_cursor(commit=False) as cursor:
            placeholders = ','.join(['?' for _ in ids])
            columns = ", ".join(self.SELECT_COLUMNS)
            query = f"""
                SELECT {columns}
                FROM [dbo].[Promotion] p
                WHERE p.PromotionID IN ({placeholders})
                ORDER BY p.StartDate DESC
            """
            cursor.execute(query, *ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_year_months(self) -> List[str]:
        """저장된 데이터의 년월 목록 조회 (StartDate 기준)"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT FORMAT(StartDate, 'yyyy-MM') as YearMonth
                FROM [dbo].[Promotion]
                ORDER BY YearMonth DESC
            """
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def get_promotion_types(self) -> List[Dict[str, str]]:
        """PromotionType 테이블에서 행사유형 목록 조회"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT TypeCode, TypeName, DisplayName, Category
                FROM [dbo].[PromotionType]
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

    def get_promotion_type_display_names(self) -> List[str]:
        """행사유형 DisplayName 목록만 조회"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT DisplayName
                FROM [dbo].[PromotionType]
                WHERE DisplayName IS NOT NULL AND DisplayName != ''
                ORDER BY DisplayName
            """
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def get_statuses(self) -> List[str]:
        """상태 목록 반환"""
        return ['SCHEDULED', 'ACTIVE', 'ENDED', 'CANCELLED']

    def bulk_delete(self, id_values: List[Any], batch_size: int = 1000) -> int:
        """일괄 삭제 (PromotionProduct도 함께 삭제)"""
        total_deleted = 0

        with get_db_cursor() as cursor:
            for i in range(0, len(id_values), batch_size):
                batch = id_values[i:i + batch_size]
                if not batch:
                    continue

                placeholders = ','.join(['?' for _ in batch])

                # PromotionProduct 먼저 삭제 (FK 제약)
                cursor.execute(
                    f"DELETE FROM [dbo].[PromotionProduct] WHERE PromotionID IN ({placeholders})",
                    *batch
                )

                # Promotion 삭제
                cursor.execute(
                    f"DELETE FROM [dbo].[Promotion] WHERE PromotionID IN ({placeholders})",
                    *batch
                )
                total_deleted += cursor.rowcount

        return total_deleted

    def get_max_sequences_by_prefixes(self, prefixes: List[str]) -> Dict[str, int]:
        """
        여러 접두사에 대한 현재 최대 순번 일괄 조회

        Args:
            prefixes: PromotionID 접두사 리스트 (예: ["OREN2501"])

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
                    SELECT MAX(CAST(RIGHT(PromotionID, 2) AS INT))
                    FROM [dbo].[Promotion]
                    WHERE PromotionID LIKE ? + '%'
                      AND LEN(PromotionID) > 2
                """
                cursor.execute(query, prefix)
                row = cursor.fetchone()

                if row and row[0] is not None:
                    result[prefix] = row[0]

        return result
