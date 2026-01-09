"""
SabangnetOrders → OrdersRealtime 업로드 모듈
"""

import sys
import os
from datetime import datetime

# common의 database.py 사용
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))
from common.database import get_db_connection


class OrdersRealtimeUploader:
    """사방넷 주문 데이터를 OrdersRealtime 테이블로 업로드"""

    def __init__(self):
        self.connection = None
        self.cursor = None
        self._connect()

    def _connect(self):
        """DB 연결"""
        self.connection = get_db_connection()
        self.cursor = self.connection.cursor()

    def merge_to_orders_realtime(self):
        """
        SabangnetOrders → OrdersRealtime MERGE

        Returns:
            dict: 처리 결과 통계
        """
        # 매핑 정보
        # SourceChannel = 'Sabangnet' (고정)
        # ContractType = '3P' (고정)
        # SourceOrderID = SabangnetOrders.ORDER_ID (주문번호)
        # SabangnetIDX = SabangnetOrders.IDX (사방넷 원본 ID, Merge 기준)
        # OrderDate = SabangnetOrders.ORDER_DATE (주문일)
        # shippedDate = SabangnetOrders.DELIVERY_CONFIRM_DATE (출고 완료일)
        # ChannelID = SabangnetOrders.ChannelID (채널별)
        # ProductID = SabangnetOrders.ProductID (부모 제품)
        # CustomerName = SabangnetOrders.USER_NAME (주문자명)
        # OrderQuantity = SabangnetOrders.SALE_CNT (수량)
        # OrderPrice = SabangnetOrders.PAY_COST / SALE_CNT (단가 계산)
        # OrderAmount = SabangnetOrders.PAY_COST (총액)
        # OrderStatus = SabangnetOrders.ORDER_STATUS (주문 상태)
        # CollectedDate = SabangnetOrders.CollectedDate (수집일시)
        # BrandID = Brand.BrandID (SabangnetOrders.BRAND_NM과 Brand.Name 매핑, 실패 시 0)

        merge_sql = """
            MERGE INTO OrdersRealtime AS target
            USING (
                SELECT
                    o.ORDER_ID AS SourceOrderID,
                    o.IDX AS SabangnetIDX,
                    o.ORDER_DATE AS OrderDate,
                    o.DELIVERY_CONFIRM_DATE AS shippedDate,
                    o.ProductID,
                    o.USER_NAME AS CustomerName,
                    o.SALE_CNT AS OrderQuantity,
                    CASE WHEN o.SALE_CNT > 0 THEN o.PAY_COST / o.SALE_CNT ELSE 0 END AS OrderPrice,
                    o.PAY_COST AS OrderAmount,
                    o.ORDER_STATUS AS OrderStatus,
                    o.ChannelID,
                    o.CollectedDate,
                    ISNULL(b.BrandID, 0) AS BrandID
                FROM SabangnetOrders o
                LEFT JOIN Brand b ON o.BRAND_NM = b.Name
                WHERE o.DELIVERY_CONFIRM_DATE IS NOT NULL  -- 출고 완료된 건만
            ) AS source
            ON target.SourceChannel = N'Sabangnet'
               AND target.SabangnetIDX = source.SabangnetIDX

            WHEN MATCHED THEN
                UPDATE SET
                    SabangnetIDX = source.SabangnetIDX,
                    OrderDate = source.OrderDate,
                    shippedDate = source.shippedDate,
                    ProductID = source.ProductID,
                    CustomerName = source.CustomerName,
                    OrderQuantity = source.OrderQuantity,
                    OrderPrice = source.OrderPrice,
                    OrderAmount = source.OrderAmount,
                    OrderStatus = source.OrderStatus,
                    ChannelID = source.ChannelID,
                    BrandID = source.BrandID,
                    UpdatedDate = GETDATE()

            WHEN NOT MATCHED THEN
                INSERT (
                    SourceChannel, SourceOrderID, SabangnetIDX, ContractType,
                    OrderDate, shippedDate, ChannelID, ProductID, CustomerName,
                    OrderQuantity, OrderPrice, OrderAmount, OrderStatus,
                    CollectedDate, UpdatedDate, BrandID
                )
                VALUES (
                    N'Sabangnet', source.SourceOrderID, source.SabangnetIDX, N'3P',
                    source.OrderDate, source.shippedDate, source.ChannelID, source.ProductID, source.CustomerName,
                    source.OrderQuantity, source.OrderPrice, source.OrderAmount, source.OrderStatus,
                    source.CollectedDate, GETDATE(), source.BrandID
                );
        """

        try:
            print("\n[OrdersRealtime MERGE 시작]")
            print("-" * 70)

            # MERGE 실행
            self.cursor.execute(merge_sql)
            rows_affected = self.cursor.rowcount
            self.connection.commit()

            print(f"  처리 완료: {rows_affected}건")

            # 통계 조회
            self.cursor.execute("""
                SELECT COUNT(*) FROM OrdersRealtime WHERE SourceChannel = N'Sabangnet'
            """)
            total_count = self.cursor.fetchone()[0]

            result = {
                "rows_affected": rows_affected,
                "total_sabangnet_in_realtime": total_count
            }

            print(f"  OrdersRealtime 내 Sabangnet 총 건수: {total_count}건")
            print("-" * 70)

            return result

        except Exception as e:
            print(f"[ERROR] OrdersRealtime MERGE 실패: {e}")
            self.connection.rollback()
            raise

    def close(self):
        """연결 종료"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # 단독 실행 테스트
    print("=" * 70)
    print("Sabangnet → OrdersRealtime 업로드 테스트")
    print("=" * 70)

    with OrdersRealtimeUploader() as uploader:
        result = uploader.merge_to_orders_realtime()
        print(f"\n결과: {result}")
