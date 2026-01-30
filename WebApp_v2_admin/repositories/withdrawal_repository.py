"""
Withdrawal Repository
- 불출 계획 (WithdrawalPlan) + 불출 상품 (WithdrawalPlanItem) CRUD
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


class WithdrawalPlanRepository(BaseRepository):
    """WithdrawalPlan 테이블 Repository"""

    SELECT_COLUMNS = (
        "w.PlanID", "w.OrderNo", "w.Title", "w.Type", "w.Status",
        "w.OrdererName", "w.RecipientName",
        "w.Phone1", "w.Phone2", "w.Address1", "w.Address2",
        "w.DeliveryMethod", "w.DeliveryMessage",
        "w.DesiredDate", "w.TrackingNo", "w.Notes",
        "w.RequestedBy", "w.ApprovedBy", "w.ApprovalDate", "w.RejectionReason",
        "w.CreatedDate", "w.UpdatedDate"
    )

    def __init__(self):
        super().__init__(table_name="[dbo].[WithdrawalPlan]", id_column="PlanID")

    def get_select_query(self) -> str:
        columns = ", ".join(self.SELECT_COLUMNS)
        return f"SELECT {columns} FROM [dbo].[WithdrawalPlan] w"

    def _row_to_dict(self, row) -> Dict[str, Any]:
        return {
            "PlanID": row[0],
            "OrderNo": row[1],
            "Title": row[2],
            "Type": row[3],
            "Status": row[4],
            "OrdererName": row[5],
            "RecipientName": row[6],
            "Phone1": row[7],
            "Phone2": row[8],
            "Address1": row[9],
            "Address2": row[10],
            "DeliveryMethod": row[11],
            "DeliveryMessage": row[12],
            "DesiredDate": row[13].strftime('%Y-%m-%d') if row[13] else None,
            "TrackingNo": row[14],
            "Notes": row[15],
            "RequestedBy": row[16],
            "ApprovedBy": row[17],
            "ApprovalDate": row[18].strftime('%Y-%m-%d %H:%M:%S') if row[18] else None,
            "RejectionReason": row[19],
            "CreatedDate": row[20].strftime('%Y-%m-%d %H:%M:%S') if row[20] else None,
            "UpdatedDate": row[21].strftime('%Y-%m-%d %H:%M:%S') if row[21] else None,
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        if filters.get('status'):
            builder.where_equals("w.Status", filters['status'])
        if filters.get('type'):
            builder.where_equals("w.Type", filters['type'])
        if filters.get('year_month'):
            builder.where("FORMAT(w.DesiredDate, 'yyyy-MM') = ?", filters['year_month'])
        if filters.get('order_no'):
            builder.where("w.OrderNo LIKE ?", f"%{filters['order_no']}%")
        if filters.get('requested_by'):
            builder.where_equals("w.RequestedBy", filters['requested_by'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        builder = QueryBuilder("[dbo].[WithdrawalPlan] w")
        builder.select(*self.SELECT_COLUMNS)
        if filters:
            self._apply_filters(builder, filters)
        return builder

    def create(self, data: Dict[str, Any]) -> int:
        """새 WithdrawalPlan 생성, 생성된 PlanID 반환"""
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
        - PlanID가 없으면: OrderNo 중복 체크 후 INSERT
        """
        total_inserted = 0
        total_updated = 0
        duplicates = []
        created_plan_ids = {}  # {OrderNo: PlanID}

        # 1단계: 신규 레코드 중복 체크
        with get_db_cursor(commit=False) as cursor:
            for idx, record in enumerate(records):
                plan_id = record.get('PlanID')
                row_num = record.get('_row_num', idx + 2)

                if not plan_id:
                    check_query = """
                        SELECT PlanID FROM [dbo].[WithdrawalPlan]
                        WHERE OrderNo = ?
                    """
                    cursor.execute(check_query, record.get('OrderNo'))
                    existing = cursor.fetchone()
                    if existing:
                        duplicates.append({
                            'row': row_num,
                            'order_no': record.get('OrderNo'),
                            'existing_id': existing[0]
                        })

        if duplicates:
            return {"inserted": 0, "updated": 0, "duplicates": duplicates, "plan_ids": {}}

        # 2단계: INSERT/UPDATE 실행
        with get_db_cursor() as cursor:
            for record in records:
                plan_id = record.get('PlanID')

                if plan_id and self.exists(plan_id):
                    # UPDATE
                    update_query = """
                        UPDATE [dbo].[WithdrawalPlan]
                        SET Title = ?, Type = ?, OrdererName = ?, RecipientName = ?,
                            Phone1 = ?, Phone2 = ?, Address1 = ?, Address2 = ?,
                            DeliveryMethod = ?, DeliveryMessage = ?,
                            DesiredDate = ?, TrackingNo = ?, Notes = ?,
                            UpdatedDate = GETDATE()
                        WHERE PlanID = ?
                    """
                    params = [
                        record.get('Title'), record.get('Type'),
                        record.get('OrdererName'), record.get('RecipientName'),
                        record.get('Phone1'), record.get('Phone2'),
                        record.get('Address1'), record.get('Address2'),
                        record.get('DeliveryMethod'), record.get('DeliveryMessage'),
                        record.get('DesiredDate'), record.get('TrackingNo'),
                        record.get('Notes'), plan_id
                    ]
                    cursor.execute(update_query, *params)
                    if cursor.rowcount > 0:
                        total_updated += 1
                    created_plan_ids[record.get('OrderNo')] = plan_id
                else:
                    # INSERT
                    insert_query = """
                        INSERT INTO [dbo].[WithdrawalPlan]
                            (OrderNo, Title, Type, Status,
                             OrdererName, RecipientName,
                             Phone1, Phone2, Address1, Address2,
                             DeliveryMethod, DeliveryMessage,
                             DesiredDate, TrackingNo, Notes, RequestedBy)
                        OUTPUT INSERTED.PlanID
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    params = [
                        record.get('OrderNo'), record.get('Title'),
                        record.get('Type'), record.get('Status', 'DRAFT'),
                        record.get('OrdererName'), record.get('RecipientName'),
                        record.get('Phone1'), record.get('Phone2'),
                        record.get('Address1'), record.get('Address2'),
                        record.get('DeliveryMethod'), record.get('DeliveryMessage'),
                        record.get('DesiredDate'), record.get('TrackingNo'),
                        record.get('Notes'), record.get('RequestedBy'),
                    ]
                    cursor.execute(insert_query, *params)
                    row = cursor.fetchone()
                    if row:
                        total_inserted += 1
                        created_plan_ids[record.get('OrderNo')] = row[0]

        return {
            "inserted": total_inserted,
            "updated": total_updated,
            "duplicates": [],
            "plan_ids": created_plan_ids
        }

    def update_status(self, plan_id: int, status: str, user_id: int = None,
                      rejection_reason: str = None) -> bool:
        """상태 변경"""
        with get_db_cursor() as cursor:
            if status == 'APPROVED':
                query = """
                    UPDATE [dbo].[WithdrawalPlan]
                    SET Status = ?, ApprovedBy = ?, ApprovalDate = GETDATE(),
                        RejectionReason = NULL, UpdatedDate = GETDATE()
                    WHERE PlanID = ?
                """
                cursor.execute(query, status, user_id, plan_id)
            elif status == 'REJECTED':
                query = """
                    UPDATE [dbo].[WithdrawalPlan]
                    SET Status = ?, ApprovedBy = ?, ApprovalDate = GETDATE(),
                        RejectionReason = ?, UpdatedDate = GETDATE()
                    WHERE PlanID = ?
                """
                cursor.execute(query, status, user_id, rejection_reason, plan_id)
            else:
                query = """
                    UPDATE [dbo].[WithdrawalPlan]
                    SET Status = ?, UpdatedDate = GETDATE()
                    WHERE PlanID = ?
                """
                cursor.execute(query, status, plan_id)
            return cursor.rowcount > 0

    def get_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        if not ids:
            return []
        with get_db_cursor(commit=False) as cursor:
            placeholders = ','.join(['?' for _ in ids])
            columns = ", ".join(self.SELECT_COLUMNS)
            query = f"""
                SELECT {columns}
                FROM [dbo].[WithdrawalPlan] w
                WHERE w.PlanID IN ({placeholders})
                ORDER BY w.CreatedDate DESC
            """
            cursor.execute(query, *ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_types(self) -> List[str]:
        """사용유형 목록 (하드코딩)"""
        return ['업체샘플', '증정', '인플루언서', '직원복지', '기타']

    def get_statuses(self) -> List[str]:
        """상태 목록"""
        return ['DRAFT', 'PENDING', 'APPROVED', 'REJECTED']

    def get_year_months(self) -> List[str]:
        """출고희망일 기준 년월 목록"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT FORMAT(DesiredDate, 'yyyy-MM') as YearMonth
                FROM [dbo].[WithdrawalPlan]
                WHERE DesiredDate IS NOT NULL
                ORDER BY YearMonth DESC
            """
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def bulk_delete(self, id_values: List[Any], batch_size: int = 1000) -> int:
        """일괄 삭제 (WithdrawalPlanItem도 CASCADE 삭제)"""
        total_deleted = 0
        with get_db_cursor() as cursor:
            for i in range(0, len(id_values), batch_size):
                batch = id_values[i:i + batch_size]
                if not batch:
                    continue
                placeholders = ','.join(['?' for _ in batch])
                # CASCADE 설정이므로 Item은 자동 삭제
                cursor.execute(
                    f"DELETE FROM [dbo].[WithdrawalPlan] WHERE PlanID IN ({placeholders})",
                    *batch
                )
                total_deleted += cursor.rowcount
        return total_deleted


class WithdrawalPlanItemRepository(BaseRepository):
    """WithdrawalPlanItem 테이블 Repository"""

    SELECT_COLUMNS = (
        "wi.ItemID", "wi.PlanID",
        "wi.ProductName", "wi.BaseBarcode", "wi.UniqueCode",
        "wi.Quantity", "wi.Notes", "wi.CreatedDate"
    )

    def __init__(self):
        super().__init__(table_name="[dbo].[WithdrawalPlanItem]", id_column="ItemID")

    def get_select_query(self) -> str:
        columns = ", ".join(self.SELECT_COLUMNS)
        return f"SELECT {columns} FROM [dbo].[WithdrawalPlanItem] wi"

    def _row_to_dict(self, row) -> Dict[str, Any]:
        return {
            "ItemID": row[0],
            "PlanID": row[1],
            "ProductName": row[2],
            "BaseBarcode": row[3],
            "UniqueCode": row[4],
            "Quantity": row[5],
            "Notes": row[6],
            "CreatedDate": row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None,
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        if filters.get('plan_id'):
            builder.where_equals("wi.PlanID", filters['plan_id'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        builder = QueryBuilder("[dbo].[WithdrawalPlanItem] wi")
        builder.select(*self.SELECT_COLUMNS)
        if filters:
            self._apply_filters(builder, filters)
        return builder

    def get_by_plan_id(self, plan_id: int) -> List[Dict[str, Any]]:
        """특정 계획의 전체 상품 목록"""
        with get_db_cursor(commit=False) as cursor:
            columns = ", ".join(self.SELECT_COLUMNS)
            query = f"""
                SELECT {columns}
                FROM [dbo].[WithdrawalPlanItem] wi
                WHERE wi.PlanID = ?
                ORDER BY wi.ItemID
            """
            cursor.execute(query, plan_id)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_by_plan_ids(self, plan_ids: List[int]) -> List[Dict[str, Any]]:
        """여러 계획의 상품 목록"""
        if not plan_ids:
            return []
        with get_db_cursor(commit=False) as cursor:
            placeholders = ','.join(['?' for _ in plan_ids])
            columns = ", ".join(self.SELECT_COLUMNS)
            query = f"""
                SELECT {columns}
                FROM [dbo].[WithdrawalPlanItem] wi
                WHERE wi.PlanID IN ({placeholders})
                ORDER BY wi.PlanID, wi.ItemID
            """
            cursor.execute(query, *plan_ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def bulk_insert(self, records: List[Dict[str, Any]]) -> int:
        """일괄 INSERT"""
        total_inserted = 0
        with get_db_cursor() as cursor:
            for record in records:
                insert_query = """
                    INSERT INTO [dbo].[WithdrawalPlanItem]
                        (PlanID, ProductName, BaseBarcode, UniqueCode, Quantity, Notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                params = [
                    record.get('PlanID'),
                    record.get('ProductName'),
                    record.get('BaseBarcode'),
                    record.get('UniqueCode'),
                    record.get('Quantity', 1),
                    record.get('Notes'),
                ]
                cursor.execute(insert_query, *params)
                if cursor.rowcount > 0:
                    total_inserted += 1
        return total_inserted

    def delete_by_plan_id(self, plan_id: int) -> int:
        """특정 계획의 전체 상품 삭제"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM [dbo].[WithdrawalPlanItem] WHERE PlanID = ?",
                plan_id
            )
            return cursor.rowcount