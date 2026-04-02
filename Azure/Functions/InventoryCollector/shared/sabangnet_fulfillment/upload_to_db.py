"""
사방넷 풀필먼트 데이터 DB 업로드
- 재고 스냅샷 MERGE
- 로케이션 스냅샷 INSERT (날짜+시간 기준 삭제 후 재삽입)
- 입고예정/작업내역 MERGE
"""

import logging
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from common.database import get_db_connection

logger = logging.getLogger(__name__)


class InventoryUploader:
    """재고/입고 데이터 DB 업로드"""

    def __init__(self):
        self.product_mapping = {}  # ShippingProductID → ProductID

    def load_product_mapping(self):
        """Product 테이블에서 SabangnetUniqueCode → ProductID 매핑 로드"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SabangnetUniqueCode, ProductID, SabangnetCode, Name
            FROM [dbo].[Product]
            WHERE SabangnetUniqueCode IS NOT NULL AND SabangnetUniqueCode != ''
        """)
        for row in cursor.fetchall():
            self.product_mapping[str(row[0])] = {
                'ProductID': row[1],
                'ProductCode': row[2],
                'ProductName': row[3]
            }
        cursor.close()
        conn.close()
        logger.info(f"[매핑] Product 매핑 로드: {len(self.product_mapping)}건")

    def get_shipping_product_ids(self) -> list:
        """매핑된 shipping_product_id 리스트 반환"""
        return list(self.product_mapping.keys())

    # ============================================================
    # 재고 스냅샷 업로드
    # ============================================================
    def upload_inventory_snapshots(self, stocks: list, snapshot_date: str, snapshot_time: str) -> dict:
        """
        재고 스냅샷 MERGE

        Args:
            stocks: API 응답 리스트 [{shipping_product_id, total_stock, ...}]
            snapshot_date: 스냅샷 날짜 (YYYY-MM-DD)
            snapshot_time: 'AM' 또는 'PM'

        Returns:
            dict: {inserted, updated, total}
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        inserted = 0
        updated = 0

        try:
            for stock in stocks:
                spid = str(stock.get('shipping_product_id', ''))
                mapping = self.product_mapping.get(spid, {})

                cursor.execute("""
                    MERGE INTO [dbo].[SabangnetInventorySnapshot] AS target
                    USING (SELECT ? AS SnapshotDate, ? AS SnapshotTime, ? AS ShippingProductID) AS source
                    ON target.SnapshotDate = source.SnapshotDate
                       AND target.SnapshotTime = source.SnapshotTime
                       AND target.ShippingProductID = source.ShippingProductID
                    WHEN MATCHED THEN UPDATE SET
                        ProductID = ?,
                        ProductCode = ?,
                        ProductName = ?,
                        TotalStock = ?,
                        ReceivingStock = ?,
                        NormalStock = ?,
                        OrderStock = ?,
                        ShippingStock = ?,
                        DamagedStock = ?,
                        ReturnStock = ?,
                        KeepingStock = ?
                    WHEN NOT MATCHED THEN INSERT (
                        SnapshotDate, SnapshotTime, ShippingProductID, ProductID,
                        ProductCode, ProductName,
                        TotalStock, ReceivingStock, NormalStock, OrderStock,
                        ShippingStock, DamagedStock, ReturnStock, KeepingStock
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    OUTPUT $action;
                """,
                    # MERGE ON
                    snapshot_date, snapshot_time, spid,
                    # WHEN MATCHED UPDATE
                    mapping.get('ProductID'),
                    mapping.get('ProductCode', ''),
                    mapping.get('ProductName', stock.get('product_name', '')),
                    int(stock.get('total_stock', 0)),
                    int(stock.get('receiving_stock', 0)),
                    int(stock.get('normal_stock', 0)),
                    int(stock.get('order_stock', 0)),
                    int(stock.get('shipping_stock', 0)),
                    int(stock.get('damaged_stock', 0)),
                    int(stock.get('return_stock', 0)),
                    int(stock.get('keeping_stock', 0)),
                    # WHEN NOT MATCHED INSERT
                    snapshot_date, snapshot_time, spid, mapping.get('ProductID'),
                    mapping.get('ProductCode', ''),
                    mapping.get('ProductName', stock.get('product_name', '')),
                    int(stock.get('total_stock', 0)),
                    int(stock.get('receiving_stock', 0)),
                    int(stock.get('normal_stock', 0)),
                    int(stock.get('order_stock', 0)),
                    int(stock.get('shipping_stock', 0)),
                    int(stock.get('damaged_stock', 0)),
                    int(stock.get('return_stock', 0)),
                    int(stock.get('keeping_stock', 0)),
                )

                action = cursor.fetchone()
                if action and action[0] == 'INSERT':
                    inserted += 1
                else:
                    updated += 1

            conn.commit()
            logger.info(f"[재고스냅샷] INSERT: {inserted}, UPDATE: {updated}")

        except Exception as e:
            conn.rollback()
            logger.error(f"[재고스냅샷] 업로드 실패: {e}", exc_info=True)
            raise
        finally:
            cursor.close()
            conn.close()

        return {'inserted': inserted, 'updated': updated, 'total': len(stocks)}

    # ============================================================
    # 로케이션 스냅샷 업로드
    # ============================================================
    def upload_location_snapshots(self, locations: list, snapshot_date: str, snapshot_time: str) -> dict:
        """
        로케이션별 재고 스냅샷 (삭제 후 재삽입)

        Args:
            locations: API 응답 리스트
            snapshot_date: 스냅샷 날짜
            snapshot_time: 'AM' 또는 'PM'

        Returns:
            dict: {deleted, inserted}
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 해당 날짜+시간 기존 데이터 삭제
            cursor.execute("""
                DELETE FROM [dbo].[SabangnetLocationSnapshot]
                WHERE SnapshotDate = ? AND SnapshotTime = ?
            """, snapshot_date, snapshot_time)
            deleted = cursor.rowcount

            # 새로 삽입
            inserted = 0
            for loc in locations:
                spid = str(loc.get('shipping_product_id', ''))
                mapping = self.product_mapping.get(spid, {})

                cursor.execute("""
                    INSERT INTO [dbo].[SabangnetLocationSnapshot]
                    (SnapshotDate, SnapshotTime, ShippingProductID, ProductID,
                     LocationID, LocationName, LocType, ExpireDate, Quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    snapshot_date, snapshot_time, spid,
                    mapping.get('ProductID'),
                    loc.get('location_id'),
                    loc.get('location_name', ''),
                    loc.get('loc_type'),
                    loc.get('expire_date', ''),
                    int(loc.get('quantity', 0))
                )
                inserted += 1

            conn.commit()
            logger.info(f"[로케이션스냅샷] 삭제: {deleted}, INSERT: {inserted}")

        except Exception as e:
            conn.rollback()
            logger.error(f"[로케이션스냅샷] 업로드 실패: {e}", exc_info=True)
            raise
        finally:
            cursor.close()
            conn.close()

        return {'deleted': deleted, 'inserted': inserted}

    # ============================================================
    # 입고예정 업로드
    # ============================================================
    def upload_receiving_plans(self, plans: list) -> dict:
        """입고예정 MERGE"""
        conn = get_db_connection()
        cursor = conn.cursor()
        inserted = 0
        updated = 0

        try:
            for plan in plans:
                plan_id = plan.get('receiving_plan_id')
                if not plan_id:
                    continue

                cursor.execute("""
                    MERGE INTO [dbo].[SabangnetReceivingPlan] AS target
                    USING (SELECT ? AS ReceivingPlanID) AS source
                    ON target.ReceivingPlanID = source.ReceivingPlanID
                    WHEN MATCHED THEN UPDATE SET
                        PlanDate = ?, PlanStatus = ?, CompleteDt = ?,
                        Memo = ?, LastSyncedAt = GETDATE()
                    WHEN NOT MATCHED THEN INSERT (
                        ReceivingPlanID, MemberID, ReceivingPlanCode,
                        PlanDate, PlanStatus, CompleteDt, Memo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    OUTPUT $action;
                """,
                    plan_id,
                    # UPDATE
                    plan.get('plan_date', ''),
                    plan.get('plan_status'),
                    plan.get('complete_dt', ''),
                    plan.get('memo', ''),
                    # INSERT
                    plan_id,
                    plan.get('member_id', ''),
                    plan.get('receiving_plan_code', ''),
                    plan.get('plan_date', ''),
                    plan.get('plan_status'),
                    plan.get('complete_dt', ''),
                    plan.get('memo', ''),
                )

                action = cursor.fetchone()
                if action and action[0] == 'INSERT':
                    inserted += 1
                else:
                    updated += 1

                # 하위 상품 처리 (plan_product_list)
                products = plan.get('plan_product_list', [])
                if products:
                    # 기존 하위 삭제 후 재삽입
                    cursor.execute("""
                        DELETE FROM [dbo].[SabangnetReceivingPlanProduct]
                        WHERE ReceivingPlanID = ?
                    """, plan_id)

                    for prod in products:
                        spid = str(prod.get('shipping_product_id', ''))
                        mapping = self.product_mapping.get(spid, {})

                        cursor.execute("""
                            INSERT INTO [dbo].[SabangnetReceivingPlanProduct]
                            (ReceivingPlanID, ShippingProductID, ProductID,
                             Quantity, ExpireDate, MakeDate)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """,
                            plan_id, spid, mapping.get('ProductID'),
                            int(prod.get('quantity', 0)),
                            prod.get('expire_date', ''),
                            prod.get('make_date', '')
                        )

            conn.commit()
            logger.info(f"[입고예정] INSERT: {inserted}, UPDATE: {updated}")

        except Exception as e:
            conn.rollback()
            logger.error(f"[입고예정] 업로드 실패: {e}", exc_info=True)
            raise
        finally:
            cursor.close()
            conn.close()

        return {'inserted': inserted, 'updated': updated, 'total': len(plans)}

    # ============================================================
    # 예정대비입고현황 업데이트
    # ============================================================
    def update_receiving_quantities(self, plan_id: int, plan_result: dict) -> int:
        """입고예정 상품의 실제 입고 수량 업데이트"""
        products = plan_result.get('receiving_plan_product', [])
        if not products:
            return 0

        conn = get_db_connection()
        cursor = conn.cursor()
        updated = 0

        try:
            for prod in products:
                spid = str(prod.get('shipping_product_id', ''))
                cursor.execute("""
                    UPDATE [dbo].[SabangnetReceivingPlanProduct]
                    SET ReceivingQuantity = ?, PlanProductStatus = ?
                    WHERE ReceivingPlanID = ? AND ShippingProductID = ?
                """,
                    prod.get('receiving_quantity', 0),
                    prod.get('plan_product_status'),
                    plan_id, spid
                )
                updated += cursor.rowcount

            conn.commit()
            logger.info(f"[예정대비입고] plan_id={plan_id}: {updated}건 업데이트")

        except Exception as e:
            conn.rollback()
            logger.error(f"[예정대비입고] 업데이트 실패: {e}", exc_info=True)
        finally:
            cursor.close()
            conn.close()

        return updated

    # ============================================================
    # 입고작업내역 업로드
    # ============================================================
    def upload_receiving_works(self, works: list) -> dict:
        """입고작업내역 MERGE"""
        conn = get_db_connection()
        cursor = conn.cursor()
        inserted = 0
        updated = 0

        try:
            for work in works:
                work_id = work.get('receiving_work_history_id')
                if not work_id:
                    continue

                spid = str(work.get('shipping_product_id', ''))
                mapping = self.product_mapping.get(spid, {})

                cursor.execute("""
                    MERGE INTO [dbo].[SabangnetReceivingWork] AS target
                    USING (SELECT ? AS WorkHistoryID) AS source
                    ON target.WorkHistoryID = source.WorkHistoryID
                    WHEN MATCHED THEN UPDATE SET
                        LastSyncedAt = GETDATE()
                    WHEN NOT MATCHED THEN INSERT (
                        WorkHistoryID, WorkDate, WorkType, ReceivingType,
                        ReceivingPlanID, ShippingProductID, ProductID,
                        Quantity, ExpireDate, MakeDate,
                        LocationID, BoxQuantity, PalletQuantity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    OUTPUT $action;
                """,
                    work_id,
                    # INSERT
                    work_id,
                    work.get('work_date', ''),
                    work.get('work_type'),
                    work.get('receiving_type'),
                    work.get('receiving_plan_id'),
                    spid,
                    mapping.get('ProductID'),
                    int(work.get('quantity', 0)),
                    work.get('expire_date', ''),
                    work.get('make_date', ''),
                    work.get('location_id'),
                    work.get('box_quantity'),
                    work.get('pallet_quantity'),
                )

                action = cursor.fetchone()
                if action and action[0] == 'INSERT':
                    inserted += 1
                else:
                    updated += 1

            conn.commit()
            logger.info(f"[입고작업내역] INSERT: {inserted}, UPDATE: {updated}")

        except Exception as e:
            conn.rollback()
            logger.error(f"[입고작업내역] 업로드 실패: {e}", exc_info=True)
            raise
        finally:
            cursor.close()
            conn.close()

        return {'inserted': inserted, 'updated': updated, 'total': len(works)}
