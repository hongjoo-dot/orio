"""
Cafe24OrdersDetail → OrdersRealtime 업로드 모듈
"""

import os
import pyodbc
from datetime import datetime
from dotenv import load_dotenv


class OrdersRealtimeUploader:
    """Cafe24 주문 데이터를 OrdersRealtime 테이블로 업로드"""

    def __init__(self):
        load_dotenv()
        self.connection = None
        self.cursor = None
        self._connect()

    def _connect(self):
        """DB 연결"""
        driver = os.getenv('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_DATABASE')};"
            f"UID={os.getenv('DB_USERNAME')};"
            f"PWD={os.getenv('DB_PASSWORD')};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=60;"
        )
        self.connection = pyodbc.connect(conn_str)
        self.cursor = self.connection.cursor()

    def merge_to_orders_realtime(self):
        """
        Cafe24OrdersDetail → OrdersRealtime MERGE
        
        Returns:
            dict: 처리 결과 통계
        """
        # 매핑 정보
        # SourceChannel = '자사몰' (고정)
        # ContractType = '3P' (고정)
        # SourceOrderID = Cafe24OrdersDetail.order_item_code (주문 항목 코드)
        # OrderDate = Cafe24Orders.order_date (주문일)
        # shippedDate = Cafe24Orders.shipped_date (출고일)
        # ChannelID = 45 (고정)
        # ProductID = Cafe24OrdersDetail.ProductID (구성품 ID)
        # CustomerName = Cafe24Orders.billing_name (주문자명)
        # OrderQuantity = Cafe24OrdersDetail.quantity (수량)
        # OrderPrice = Cafe24OrdersDetail.product_price (단가)
        # OrderAmount = Cafe24OrdersDetail.payment_amount (총액)
        # OrderStatus = Cafe24OrdersDetail.order_status (주문 상태)
        # CollectedDate = Cafe24OrdersDetail.CollectedDate (수집일시)
        # BrandID = 3 (고정)

        merge_sql = """
            MERGE INTO OrdersRealtime AS target
            USING (
                SELECT
                    d.order_item_code AS SourceOrderID,
                    o.order_date AS OrderDate,
                    o.shipped_date AS shippedDate,
                    d.ProductID,
                    o.billing_name AS CustomerName,
                    d.quantity AS OrderQuantity,
                    d.product_price AS OrderPrice,
                    d.payment_amount AS OrderAmount,
                    d.order_status AS OrderStatus,
                    d.CollectedDate
                FROM Cafe24OrdersDetail d
                INNER JOIN Cafe24Orders o ON d.Cafe24OrderID = o.Cafe24OrderID
                WHERE o.shipped_date IS NOT NULL  -- 출고된 건만
            ) AS source
            ON target.SourceChannel = N'자사몰'
               AND target.SourceOrderID = source.SourceOrderID

            WHEN MATCHED THEN
                UPDATE SET
                    OrderDate = source.OrderDate,
                    shippedDate = source.shippedDate,
                    ProductID = source.ProductID,
                    CustomerName = source.CustomerName,
                    OrderQuantity = source.OrderQuantity,
                    OrderPrice = source.OrderPrice,
                    OrderAmount = source.OrderAmount,
                    OrderStatus = source.OrderStatus,
                    UpdatedDate = GETDATE()

            WHEN NOT MATCHED THEN
                INSERT (
                    SourceChannel, SourceOrderID, ContractType,
                    OrderDate, shippedDate, ChannelID, ProductID, CustomerName,
                    OrderQuantity, OrderPrice, OrderAmount, OrderStatus,
                    CollectedDate, UpdatedDate, BrandID
                )
                VALUES (
                    N'자사몰', source.SourceOrderID, N'3P',
                    source.OrderDate, source.shippedDate, 45, source.ProductID, source.CustomerName,
                    source.OrderQuantity, source.OrderPrice, source.OrderAmount, source.OrderStatus,
                    source.CollectedDate, GETDATE(), 3
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
                SELECT COUNT(*) FROM OrdersRealtime WHERE SourceChannel = N'자사몰'
            """)
            total_count = self.cursor.fetchone()[0]

            result = {
                "rows_affected": rows_affected,
                "total_cafe24_in_realtime": total_count
            }

            print(f"  OrdersRealtime 내 자사몰 총 건수: {total_count}건")
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
    print("Cafe24 → OrdersRealtime 업로드 테스트")
    print("=" * 70)

    with OrdersRealtimeUploader() as uploader:
        result = uploader.merge_to_orders_realtime()
        print(f"\n결과: {result}")
