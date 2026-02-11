"""
WithdrawalPlan Repository
- 불출 계획 CRUD
- 캠페인 단위 그룹핑 (Title + GroupID)
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


class WithdrawalPlanRepository(BaseRepository):
    """WithdrawalPlan 테이블 Repository"""

    # SELECT 컬럼 상수 (순서 변경 금지 - _row_to_dict 인덱스와 일치해야 함)
    SELECT_COLUMNS = (
        "p.PlanID", "p.GroupID", "p.Title", "p.[Date]", "p.Type",
        "p.ProductName", "p.UniqueCode", "p.PlannedQty",
        "p.Notes", "p.CreatedBy", "p.CreatedDate", "p.UpdatedDate"
    )

    def __init__(self):
        super().__init__(table_name="[dbo].[WithdrawalPlan]", id_column="PlanID")

    def get_select_query(self) -> str:
        """WithdrawalPlan 조회 쿼리"""
        columns = ", ".join(self.SELECT_COLUMNS)
        return f"SELECT {columns} FROM [dbo].[WithdrawalPlan] p"

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "PlanID": row[0],
            "GroupID": row[1],
            "Title": row[2],
            "Date": row[3].strftime('%Y-%m-%d') if row[3] else None,
            "Type": row[4],
            "ProductName": row[5],
            "UniqueCode": row[6],
            "PlannedQty": int(row[7]) if row[7] else 0,
            "Notes": row[8],
            "CreatedBy": row[9],
            "CreatedDate": row[10].strftime('%Y-%m-%d %H:%M:%S') if row[10] else None,
            "UpdatedDate": row[11].strftime('%Y-%m-%d %H:%M:%S') if row[11] else None,
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """필터 적용"""
        if filters.get('year_month'):
            builder.where("FORMAT(p.[Date], 'yyyy-MM') = ?", filters['year_month'])
        if filters.get('type'):
            builder.where_equals("p.Type", filters['type'])
        if filters.get('title'):
            builder.where("p.Title LIKE ?", f"%{filters['title']}%")
        if filters.get('group_id'):
            builder.where_equals("p.GroupID", filters['group_id'])
        if filters.get('unique_code'):
            builder.where("p.UniqueCode LIKE ?", f"%{filters['unique_code']}%")

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """WithdrawalPlan 전용 QueryBuilder 생성"""
        builder = QueryBuilder("[dbo].[WithdrawalPlan] p")
        builder.select(*self.SELECT_COLUMNS)
        if filters:
            self._apply_filters(builder, filters)
        return builder

    # ========== 그룹(캠페인) 관련 메서드 ==========

    def get_groups(self, filters: Optional[Dict[str, Any]] = None,
                   order_by: str = "MAX(p.[Date])", order_dir: str = "DESC") -> List[Dict[str, Any]]:
        """
        캠페인 그룹 목록 조회 (마스터용)
        Title 기준으로 그룹핑하여 반환
        """
        with get_db_cursor(commit=False) as cursor:
            where_clauses = []
            params = []

            if filters:
                if filters.get('year_month'):
                    where_clauses.append("FORMAT(p.[Date], 'yyyy-MM') = ?")
                    params.append(filters['year_month'])
                if filters.get('type'):
                    where_clauses.append("p.Type = ?")
                    params.append(filters['type'])
                if filters.get('title'):
                    where_clauses.append("p.Title LIKE ?")
                    params.append(f"%{filters['title']}%")

            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            query = f"""
                SELECT
                    p.GroupID,
                    p.Title,
                    MAX(p.Type) as Type,
                    MIN(p.[Date]) as StartDate,
                    MAX(p.[Date]) as EndDate,
                    COUNT(*) as ItemCount,
                    SUM(p.PlannedQty) as TotalQty
                FROM [dbo].[WithdrawalPlan] p
                {where_sql}
                GROUP BY p.GroupID, p.Title
                ORDER BY {order_by} {order_dir}
            """

            cursor.execute(query, *params)
            rows = cursor.fetchall()

            return [{
                "GroupID": row[0],
                "Title": row[1],
                "Type": row[2],
                "StartDate": row[3].strftime('%Y-%m-%d') if row[3] else None,
                "EndDate": row[4].strftime('%Y-%m-%d') if row[4] else None,
                "ItemCount": row[5],
                "TotalQty": row[6],
            } for row in rows]

    def get_by_group_id(self, group_id: int) -> List[Dict[str, Any]]:
        """특정 그룹의 상품 목록 조회 (디테일용)"""
        with get_db_cursor(commit=False) as cursor:
            columns = ", ".join(self.SELECT_COLUMNS)
            query = f"""
                SELECT {columns}
                FROM [dbo].[WithdrawalPlan] p
                WHERE p.GroupID = ?
                ORDER BY p.PlanID
            """
            cursor.execute(query, group_id)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_next_group_id(self) -> int:
        """새 GroupID 생성 (MAX + 1)"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT ISNULL(MAX(GroupID), 0) + 1 FROM [dbo].[WithdrawalPlan]")
            row = cursor.fetchone()
            return row[0] if row else 1

    def get_group_id_by_title(self, title: str) -> Optional[int]:
        """Title로 기존 GroupID 조회"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT TOP 1 GroupID FROM [dbo].[WithdrawalPlan] WHERE Title = ?",
                title
            )
            row = cursor.fetchone()
            return row[0] if row else None

    # ========== CRUD 메서드 ==========

    def create(self, data: Dict[str, Any]) -> int:
        """새 WithdrawalPlan 생성"""
        with get_db_cursor() as cursor:
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            col_str = ', '.join(columns)
            query = f"INSERT INTO {self.table_name} ({col_str}) OUTPUT INSERTED.PlanID VALUES ({placeholders})"
            params = [data[col] for col in columns]
            cursor.execute(query, *params)
            row = cursor.fetchone()
            return row[0] if row else None

    def bulk_upsert(self, records: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, Any]:
        """
        일괄 INSERT/UPDATE
        - PlanID가 있으면: UPDATE
        - PlanID가 없으면: INSERT (GroupID는 Title 기준으로 설정)
        """
        total_inserted = 0
        total_updated = 0

        # Title별 GroupID 캐시
        title_group_map = {}

        with get_db_cursor() as cursor:
            for record in records:
                plan_id = record.get('PlanID')
                title = record.get('Title')

                # GroupID 결정
                if 'GroupID' not in record or not record.get('GroupID'):
                    if title in title_group_map:
                        record['GroupID'] = title_group_map[title]
                    else:
                        existing_group_id = self.get_group_id_by_title(title)
                        if existing_group_id:
                            record['GroupID'] = existing_group_id
                        else:
                            record['GroupID'] = self.get_next_group_id()
                        title_group_map[title] = record['GroupID']

                if plan_id and self.exists(plan_id):
                    # UPDATE
                    update_query = """
                        UPDATE [dbo].[WithdrawalPlan]
                        SET GroupID = ?, Title = ?, [Date] = ?, Type = ?,
                            ProductName = ?, UniqueCode = ?, PlannedQty = ?,
                            Notes = ?, UpdatedDate = GETDATE()
                        WHERE PlanID = ?
                    """
                    params = [
                        record.get('GroupID'),
                        record.get('Title'),
                        record.get('Date'),
                        record.get('Type'),
                        record.get('ProductName'),
                        record.get('UniqueCode'),
                        record.get('PlannedQty', 1),
                        record.get('Notes'),
                        plan_id
                    ]
                    cursor.execute(update_query, *params)
                    if cursor.rowcount > 0:
                        total_updated += 1
                else:
                    # INSERT
                    insert_query = """
                        INSERT INTO [dbo].[WithdrawalPlan]
                            (GroupID, Title, [Date], Type, ProductName, UniqueCode, PlannedQty, Notes, CreatedBy)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    params = [
                        record.get('GroupID'),
                        record.get('Title'),
                        record.get('Date'),
                        record.get('Type'),
                        record.get('ProductName'),
                        record.get('UniqueCode'),
                        record.get('PlannedQty', 1),
                        record.get('Notes'),
                        record.get('CreatedBy'),
                    ]
                    cursor.execute(insert_query, *params)
                    total_inserted += 1

        return {"inserted": total_inserted, "updated": total_updated}

    def get_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        """ID 리스트로 데이터 조회"""
        if not ids:
            return []
        with get_db_cursor(commit=False) as cursor:
            placeholders = ','.join(['?' for _ in ids])
            columns = ", ".join(self.SELECT_COLUMNS)
            query = f"""
                SELECT {columns}
                FROM [dbo].[WithdrawalPlan] p
                WHERE p.PlanID IN ({placeholders})
                ORDER BY p.PlanID
            """
            cursor.execute(query, *ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def bulk_update_items(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """인라인 편집 일괄 저장 (PlannedQty, Notes 업데이트)"""
        total_updated = 0

        with get_db_cursor() as cursor:
            for record in records:
                plan_id = record.get('PlanID')
                if not plan_id:
                    continue

                query = """
                    UPDATE [dbo].[WithdrawalPlan]
                    SET PlannedQty = ?,
                        Notes = ?,
                        UpdatedDate = GETDATE()
                    WHERE PlanID = ?
                """
                cursor.execute(query,
                    int(record.get('PlannedQty', 0) or 0),
                    record.get('Notes'),
                    plan_id
                )
                if cursor.rowcount > 0:
                    total_updated += 1

        return {"updated": total_updated}

    def delete_by_group_id(self, group_id: int) -> int:
        """그룹 전체 삭제"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM [dbo].[WithdrawalPlan] WHERE GroupID = ?",
                group_id
            )
            return cursor.rowcount

    # ========== 메타데이터 메서드 ==========

    def get_types(self) -> List[str]:
        """사용유형 목록"""
        return ['인플루언서', '증정', '업체샘플', '직원복지', '기타']

    def get_year_months(self) -> List[str]:
        """저장된 데이터의 년월 목록 조회"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT FORMAT([Date], 'yyyy-MM') as YearMonth
                FROM [dbo].[WithdrawalPlan]
                WHERE [Date] IS NOT NULL
                ORDER BY YearMonth DESC
            """
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]
