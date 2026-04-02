"""
사방넷 입고 데이터 Repository (조회 전용)
- 입고예정 목록/상세 조회
- 입고작업내역 조회
"""

from core.database import get_db_cursor
import logging

logger = logging.getLogger(__name__)


class SabangnetInboundRepository:
    """입고 데이터 조회 Repository"""

    def get_receiving_plans(self, plan_date: str = None, plan_status: int = None,
                            page: int = 1, limit: int = 20) -> dict:
        """입고예정 목록 조회"""
        with get_db_cursor() as cursor:
            where_clauses = []
            params = []

            if plan_date:
                where_clauses.append("rp.PlanDate = ?")
                params.append(plan_date)
            if plan_status is not None:
                where_clauses.append("rp.PlanStatus = ?")
                params.append(plan_status)

            where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            # 총 건수
            cursor.execute(f"SELECT COUNT(*) FROM [dbo].[SabangnetReceivingPlan] rp{where_sql}", params)
            total = cursor.fetchone()[0]

            # 데이터
            offset = (page - 1) * limit
            cursor.execute(f"""
                SELECT
                    rp.ReceivingPlanID, rp.ReceivingPlanCode,
                    rp.PlanDate, rp.PlanStatus, rp.CompleteDt,
                    rp.Memo, rp.LastSyncedAt,
                    (SELECT COUNT(*) FROM [dbo].[SabangnetReceivingPlanProduct]
                     WHERE ReceivingPlanID = rp.ReceivingPlanID) AS ProductCount
                FROM [dbo].[SabangnetReceivingPlan] rp
                {where_sql}
                ORDER BY rp.PlanDate DESC, rp.ReceivingPlanID DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, *params, offset, limit)

            data = [{
                'ReceivingPlanID': row[0],
                'ReceivingPlanCode': row[1] or '',
                'PlanDate': row[2] or '',
                'PlanStatus': row[3],
                'PlanStatusName': self._plan_status_name(row[3]),
                'CompleteDt': row[4] or '',
                'Memo': row[5] or '',
                'LastSyncedAt': row[6].isoformat() if row[6] else '',
                'ProductCount': row[7] or 0,
            } for row in cursor.fetchall()]

            return {
                'data': data,
                'total': total,
                'page': page,
                'total_pages': (total + limit - 1) // limit if limit else 1
            }

    def get_receiving_plan_detail(self, plan_id: int) -> dict:
        """입고예정 상세 + 상품 목록"""
        with get_db_cursor() as cursor:
            # 마스터
            cursor.execute("""
                SELECT ReceivingPlanID, ReceivingPlanCode, PlanDate,
                       PlanStatus, CompleteDt, Memo
                FROM [dbo].[SabangnetReceivingPlan]
                WHERE ReceivingPlanID = ?
            """, plan_id)
            row = cursor.fetchone()
            if not row:
                return None

            plan = {
                'ReceivingPlanID': row[0],
                'ReceivingPlanCode': row[1] or '',
                'PlanDate': row[2] or '',
                'PlanStatus': row[3],
                'PlanStatusName': self._plan_status_name(row[3]),
                'CompleteDt': row[4] or '',
                'Memo': row[5] or '',
            }

            # 상품 목록
            cursor.execute("""
                SELECT
                    rpp.ShippingProductID, rpp.ProductID,
                    rpp.Quantity, rpp.ReceivingQuantity,
                    rpp.PlanProductStatus, rpp.ExpireDate, rpp.MakeDate,
                    p.Name AS ProductName, p.UniqueCode,
                    b.Name AS BrandName
                FROM [dbo].[SabangnetReceivingPlanProduct] rpp
                LEFT JOIN [dbo].[Product] p ON rpp.ProductID = p.ProductID
                LEFT JOIN [dbo].[Brand] b ON p.BrandID = b.BrandID
                WHERE rpp.ReceivingPlanID = ?
                ORDER BY p.Name
            """, plan_id)

            plan['products'] = [{
                'ShippingProductID': r[0],
                'ProductID': r[1],
                'Quantity': r[2] or 0,
                'ReceivingQuantity': r[3],
                'PlanProductStatus': r[4],
                'PlanProductStatusName': self._plan_product_status_name(r[4]),
                'ExpireDate': r[5] or '',
                'MakeDate': r[6] or '',
                'ProductName': r[7] or '',
                'UniqueCode': r[8] or '',
                'BrandName': r[9] or '',
            } for r in cursor.fetchall()]

            return plan

    def get_receiving_works(self, start_date: str = None, end_date: str = None,
                            work_type: int = None, page: int = 1, limit: int = 50) -> dict:
        """입고작업내역 조회"""
        with get_db_cursor() as cursor:
            where_clauses = []
            params = []

            if start_date:
                where_clauses.append("rw.WorkDate >= ?")
                params.append(start_date)
            if end_date:
                where_clauses.append("rw.WorkDate <= ? + ' 23:59:59'")
                params.append(end_date)
            if work_type is not None:
                where_clauses.append("rw.WorkType = ?")
                params.append(work_type)

            where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            cursor.execute(f"SELECT COUNT(*) FROM [dbo].[SabangnetReceivingWork] rw{where_sql}", params)
            total = cursor.fetchone()[0]

            offset = (page - 1) * limit
            cursor.execute(f"""
                SELECT
                    rw.WorkHistoryID, rw.WorkDate, rw.WorkType, rw.ReceivingType,
                    rw.ReceivingPlanID, rw.ShippingProductID, rw.ProductID,
                    rw.Quantity, rw.ExpireDate, rw.LocationID,
                    rw.BoxQuantity, rw.PalletQuantity,
                    p.Name AS ProductName, p.UniqueCode,
                    b.Name AS BrandName
                FROM [dbo].[SabangnetReceivingWork] rw
                LEFT JOIN [dbo].[Product] p ON rw.ProductID = p.ProductID
                LEFT JOIN [dbo].[Brand] b ON p.BrandID = b.BrandID
                {where_sql}
                ORDER BY rw.WorkDate DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, *params, offset, limit)

            data = [{
                'WorkHistoryID': r[0],
                'WorkDate': r[1] or '',
                'WorkType': r[2],
                'WorkTypeName': self._work_type_name(r[2]),
                'ReceivingType': r[3],
                'ReceivingTypeName': self._receiving_type_name(r[3]),
                'ReceivingPlanID': r[4],
                'ShippingProductID': r[5] or '',
                'ProductID': r[6],
                'Quantity': r[7] or 0,
                'ExpireDate': r[8] or '',
                'LocationID': r[9],
                'BoxQuantity': r[10],
                'PalletQuantity': r[11],
                'ProductName': r[12] or '',
                'UniqueCode': r[13] or '',
                'BrandName': r[14] or '',
            } for r in cursor.fetchall()]

            return {
                'data': data,
                'total': total,
                'page': page,
                'total_pages': (total + limit - 1) // limit if limit else 1
            }

    @staticmethod
    def _plan_status_name(status) -> str:
        return {1: '입고예정', 2: '입고검수중', 3: '입고완료', 4: '입고취소'}.get(status, str(status or ''))

    @staticmethod
    def _plan_product_status_name(status) -> str:
        return {1: '미입고', 3: '부분입고', 5: '입고완료', 9: '취소'}.get(status, str(status or ''))

    @staticmethod
    def _work_type_name(wt) -> str:
        return {1: '입고', 3: '적치', 5: '회송', 7: '반품입고', 9: '입고취소'}.get(wt, str(wt or ''))

    @staticmethod
    def _receiving_type_name(rt) -> str:
        return {1: '예정검수', 3: '개별입고', 5: '간편입고', 7: '전수검사', 9: '엑셀입고'}.get(rt, str(rt or ''))
