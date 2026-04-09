"""
인플루언서 광고비 정산 Repository
- 검색어별 > UTM Content별 > 상품별 3단 Depth
"""

from core.database import get_db_cursor
import logging

logger = logging.getLogger(__name__)


class InfluencerSettlementRepository:
    """인플루언서 정산 조회 Repository"""

    def get_summary(self, start_date: str, end_date: str, influencers: list) -> list:
        """
        검색어별 > UTM Content별 주문 수, 매출 집계

        Returns:
            list: [{
                influencer: "eezy",
                total_order_count: 150,
                total_payment: 5200000,
                details: [
                    {content: "첫구매_eezy_0113", order_count: 45, payment: 1500000},
                    ...
                ]
            }, ...]
        """
        results = []

        with get_db_cursor(commit=False) as cursor:
            for name in influencers:
                name = name.strip()
                if not name:
                    continue

                # UTM Content별 집계
                cursor.execute("""
                    SELECT
                        u.Content,
                        COUNT(DISTINCT o.order_id) AS OrderCount,
                        ISNULL(SUM(CAST(o.payment_amount AS DECIMAL(18,2))), 0) AS TotalPayment
                    FROM Cafe24OrderUTM u
                    JOIN Cafe24Orders o ON u.OrderID = o.order_id
                    WHERE u.Content LIKE ?
                      AND u.OrderDate BETWEEN ? AND ?
                      AND o.canceled != 1
                    GROUP BY u.Content
                    ORDER BY TotalPayment DESC
                """, (f"%{name}%", start_date, end_date))

                details = []
                total_orders = 0
                total_payment = 0.0

                for row in cursor.fetchall():
                    order_count = row[1]
                    payment = float(row[2])
                    details.append({
                        'content': row[0] or '',
                        'order_count': order_count,
                        'payment': payment
                    })
                    total_orders += order_count
                    total_payment += payment

                results.append({
                    'influencer': name,
                    'total_order_count': total_orders,
                    'total_payment': total_payment,
                    'details': details
                })

        return results

    def get_influencer_items(self, start_date: str, end_date: str, influencer: str) -> list:
        """
        검색어(인플루언서) 전체의 상품별 합산 집계

        Args:
            start_date: 시작일
            end_date: 종료일
            influencer: 검색어 (LIKE 검색)
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT
                    d.product_name,
                    d.option_value,
                    SUM(d.quantity) AS TotalQuantity,
                    SUM(CAST(d.payment_amount AS DECIMAL(18,2))) AS TotalPayment
                FROM Cafe24OrderUTM u
                JOIN Cafe24Orders o ON u.OrderID = o.order_id
                JOIN Cafe24OrdersDetail d ON o.order_id = d.order_id
                WHERE u.Content LIKE ?
                  AND u.OrderDate BETWEEN ? AND ?
                  AND o.canceled != 1
                GROUP BY d.product_name, d.option_value
                ORDER BY TotalPayment DESC
            """, (f"%{influencer}%", start_date, end_date))

            return [{
                'product_name': row[0] or '',
                'option_value': row[1] or '',
                'total_quantity': row[2] or 0,
                'total_payment': float(row[3]) if row[3] else 0
            } for row in cursor.fetchall()]

    def get_content_items(self, start_date: str, end_date: str, content: str) -> list:
        """
        특정 UTM Content의 상품별 집계

        Args:
            start_date: 시작일
            end_date: 종료일
            content: UTM Content 값 (정확 일치)

        Returns:
            list: [{product_name, option_value, total_quantity, total_payment}, ...]
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT
                    d.product_name,
                    d.option_value,
                    SUM(d.quantity) AS TotalQuantity,
                    SUM(CAST(d.payment_amount AS DECIMAL(18,2))) AS TotalPayment
                FROM Cafe24OrderUTM u
                JOIN Cafe24Orders o ON u.OrderID = o.order_id
                JOIN Cafe24OrdersDetail d ON o.order_id = d.order_id
                WHERE u.Content = ?
                  AND u.OrderDate BETWEEN ? AND ?
                  AND o.canceled != 1
                GROUP BY d.product_name, d.option_value
                ORDER BY TotalPayment DESC
            """, (content, start_date, end_date))

            return [{
                'product_name': row[0] or '',
                'option_value': row[1] or '',
                'total_quantity': row[2] or 0,
                'total_payment': float(row[3]) if row[3] else 0
            } for row in cursor.fetchall()]
