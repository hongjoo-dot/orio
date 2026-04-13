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

                # UTM Content별 집계 (상품단위 매출 합산 = 배송비 제외)
                cursor.execute("""
                    SELECT
                        u.Content,
                        COUNT(DISTINCT o.order_id) AS OrderCount,
                        ISNULL(SUM(CAST(d.payment_amount AS DECIMAL(18,2))), 0) AS TotalPayment
                    FROM Cafe24OrderUTM u
                    JOIN Cafe24Orders o ON u.OrderID = o.order_id
                    JOIN Cafe24OrdersDetail d ON o.order_id = d.order_id
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

    def get_excel_data(self, start_date: str, end_date: str, influencers: list) -> list:
        """
        엑셀 다운로드용 플랫 데이터 조회
        주문 1건 + 상품 1개 = 1행, 주문 단위 금액 정보 포함
        """
        results = []

        with get_db_cursor(commit=False) as cursor:
            for name in influencers:
                name = name.strip()
                if not name:
                    continue

                cursor.execute("""
                    SELECT
                        u.Content,
                        o.order_id,
                        u.OrderDate,
                        o.billing_name,
                        u.Ad,
                        u.Medium,
                        u.Campaign,
                        d.product_name,
                        d.option_value,
                        d.quantity,
                        d.product_price,
                        d.payment_amount,
                        o.payment_amount AS order_payment_amount,
                        o.shipping_fee,
                        o.coupon_discount_price,
                        o.points_spent_amount,
                        o.order_price_amount
                    FROM Cafe24OrderUTM u
                    JOIN Cafe24Orders o ON u.OrderID = o.order_id
                    JOIN Cafe24OrdersDetail d ON o.order_id = d.order_id
                    WHERE u.Content LIKE ?
                      AND u.OrderDate BETWEEN ? AND ?
                      AND o.canceled != 1
                    ORDER BY u.Content, u.OrderDate, o.order_id, d.item_no
                """, (f"%{name}%", start_date, end_date))

                for row in cursor.fetchall():
                    results.append({
                        '검색어': name,
                        'UTM Content': row[0] or '',
                        '주문번호': row[1] or '',
                        '주문일': row[2].isoformat() if hasattr(row[2], 'isoformat') else str(row[2]),
                        '고객명': row[3] or '',
                        '광고매체': row[4] or '',
                        '광고형태': row[5] or '',
                        '캠페인': row[6] or '',
                        '상품명': row[7] or '',
                        '옵션': row[8] or '',
                        '수량': row[9] or 0,
                        '상품단가': float(row[10]) if row[10] else 0,
                        '상품결제금액': float(row[11]) if row[11] else 0,
                        '주문결제금액': float(row[12]) if row[12] else 0,
                        '배송비': float(row[13]) if row[13] else 0,
                        '쿠폰할인금액': float(row[14]) if row[14] else 0,
                        '적립금사용금액': float(row[15]) if row[15] else 0,
                        '주문상품금액': float(row[16]) if row[16] else 0,
                    })

        return results
