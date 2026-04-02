"""
사방넷 재고 스냅샷 Repository
- 일별 재고 스냅샷 조회
- 로케이션별 재고 조회
"""

from core.database import get_db_cursor
from core.query_builder import QueryBuilder
import logging

logger = logging.getLogger(__name__)


class SabangnetInventoryRepository:
    """재고 스냅샷 조회 Repository"""

    def get_snapshots(self, snapshot_date: str, snapshot_time: str = None,
                      brand_id: int = None, search: str = None) -> list:
        """
        특정 날짜의 재고 스냅샷 조회 (Product JOIN)

        Args:
            snapshot_date: 조회 날짜 (YYYY-MM-DD)
            snapshot_time: 'AM' 또는 'PM' (None이면 최신)
            brand_id: 브랜드 필터
            search: 상품명/코드 검색
        """
        with get_db_cursor() as cursor:
            query = """
                SELECT
                    s.SnapshotID, s.SnapshotDate, s.SnapshotTime,
                    s.ShippingProductID, s.ProductID,
                    s.ProductCode, s.ProductName,
                    s.TotalStock, s.ReceivingStock, s.NormalStock,
                    s.OrderStock, s.ShippingStock, s.DamagedStock,
                    s.ReturnStock, s.KeepingStock,
                    p.Name AS ERPProductName,
                    p.UniqueCode AS ERPUniqueCode,
                    b.Name AS BrandName
                FROM [dbo].[SabangnetInventorySnapshot] s
                LEFT JOIN [dbo].[Product] p ON s.ProductID = p.ProductID
                LEFT JOIN [dbo].[Brand] b ON p.BrandID = b.BrandID
                WHERE s.SnapshotDate = ?
            """
            params = [snapshot_date]

            if snapshot_time:
                query += " AND s.SnapshotTime = ?"
                params.append(snapshot_time)

            if brand_id:
                query += " AND p.BrandID = ?"
                params.append(brand_id)

            if search:
                query += " AND (s.ProductName LIKE ? OR s.ProductCode LIKE ? OR p.Name LIKE ? OR p.UniqueCode LIKE ?)"
                like = f"%{search}%"
                params.extend([like, like, like, like])

            query += " ORDER BY COALESCE(b.Name, 'ZZZ'), s.ProductName"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_dict(row) for row in rows]

    def get_locations(self, snapshot_date: str, snapshot_time: str,
                      shipping_product_id: str) -> list:
        """특정 날짜+상품의 로케이션별 재고"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT
                    l.LocationSnapshotID, l.ShippingProductID,
                    l.LocationID, l.LocationName, l.LocType,
                    l.ExpireDate, l.Quantity
                FROM [dbo].[SabangnetLocationSnapshot] l
                WHERE l.SnapshotDate = ? AND l.SnapshotTime = ?
                  AND l.ShippingProductID = ?
                ORDER BY l.LocationName
            """, snapshot_date, snapshot_time, shipping_product_id)

            return [{
                'LocationID': row[2],
                'LocationName': row[3] or '',
                'LocType': row[4],
                'LocTypeName': self._loc_type_name(row[4]),
                'ExpireDate': row[5] or '',
                'Quantity': row[6] or 0
            } for row in cursor.fetchall()]

    def get_metadata(self) -> dict:
        """필터 메타데이터 (조회 가능 날짜, 브랜드)"""
        with get_db_cursor() as cursor:
            # 스냅샷 존재 날짜
            cursor.execute("""
                SELECT DISTINCT SnapshotDate
                FROM [dbo].[SabangnetInventorySnapshot]
                ORDER BY SnapshotDate DESC
            """)
            dates = [row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
                     for row in cursor.fetchall()]

            # 스냅샷 시간대
            cursor.execute("""
                SELECT DISTINCT SnapshotTime
                FROM [dbo].[SabangnetInventorySnapshot]
                ORDER BY SnapshotTime
            """)
            times = [row[0] for row in cursor.fetchall()]

            # 브랜드
            cursor.execute("""
                SELECT DISTINCT b.BrandID, b.Name
                FROM [dbo].[SabangnetInventorySnapshot] s
                JOIN [dbo].[Product] p ON s.ProductID = p.ProductID
                JOIN [dbo].[Brand] b ON p.BrandID = b.BrandID
                ORDER BY b.Name
            """)
            brands = [{'BrandID': row[0], 'Name': row[1]} for row in cursor.fetchall()]

            return {'dates': dates, 'times': times, 'brands': brands}

    def _row_to_dict(self, row) -> dict:
        return {
            'SnapshotID': row[0],
            'SnapshotDate': row[1].isoformat() if hasattr(row[1], 'isoformat') else str(row[1]),
            'SnapshotTime': row[2],
            'ShippingProductID': row[3],
            'ProductID': row[4],
            'ProductCode': row[5] or '',
            'ProductName': row[6] or '',
            'TotalStock': row[7] or 0,
            'ReceivingStock': row[8] or 0,
            'NormalStock': row[9] or 0,
            'OrderStock': row[10] or 0,
            'ShippingStock': row[11] or 0,
            'DamagedStock': row[12] or 0,
            'ReturnStock': row[13] or 0,
            'KeepingStock': row[14] or 0,
            'ERPProductName': row[15] or '',
            'ERPUniqueCode': row[16] or '',
            'BrandName': row[17] or '',
        }

    @staticmethod
    def _loc_type_name(loc_type) -> str:
        return {1: '입고', 2: '출고가능', 5: '반품', 6: '불량', 7: '보관'}.get(loc_type, str(loc_type or ''))
