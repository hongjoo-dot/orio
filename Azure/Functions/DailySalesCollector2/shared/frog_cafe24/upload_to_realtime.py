"""
FrogCafe24OrdersDetail → OrdersRealtime 업로드 모듈
"""

import os
import pyodbc
from datetime import datetime
from dotenv import load_dotenv


class OrdersRealtimeUploader:
    """Frog Cafe24 주문 데이터를 OrdersRealtime 테이블로 업로드"""

    def __init__(self):
        load_dotenv()
        self.connection = None
        self.cursor = None
        self._connect()

    def _connect(self):
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
        FrogCafe24OrdersDetail → OrdersRealtime MERGE

        매핑:
        - SourceChannel = '자사몰' (고정)
        - ContractType = '3P' (고정)
        - ChannelID = 45 (고정)
        - BrandID = 0 (고정)
        """

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
                    ROUND(d.payment_amount / 1.1, 0) AS OrderAmountExVAT,
                    d.payment_amount AS OrderAmountInVAT,
                    d.order_status AS OrderStatus,
                    d.CollectedDate,
                    o.canceled AS Canceled
                FROM FrogCafe24OrdersDetail d
                INNER JOIN FrogCafe24Orders o ON d.Cafe24OrderID = o.Cafe24OrderID
                WHERE o.shipped_date IS NOT NULL
            ) AS source
            ON target.SourceChannel = N'자사몰'
               AND target.SourceOrderID = source.SourceOrderID

            WHEN MATCHED AND source.Canceled = 1 THEN
                DELETE

            WHEN MATCHED AND (source.Canceled IS NULL OR source.Canceled = 0) THEN
                UPDATE SET
                    OrderDate = source.OrderDate,
                    shippedDate = source.shippedDate,
                    ProductID = source.ProductID,
                    CustomerName = source.CustomerName,
                    OrderQuantity = source.OrderQuantity,
                    OrderPrice = source.OrderPrice,
                    OrderAmountExVAT = source.OrderAmountExVAT,
                    OrderAmountInVAT = source.OrderAmountInVAT,
                    OrderStatus = source.OrderStatus,
                    UpdatedDate = GETDATE()

            WHEN NOT MATCHED AND (source.Canceled IS NULL OR source.Canceled = 0) THEN
                INSERT (
                    SourceChannel, SourceOrderID, ContractType,
                    OrderDate, shippedDate, ChannelID, ProductID, CustomerName,
                    OrderQuantity, OrderPrice, OrderAmountExVAT, OrderAmountInVAT, OrderStatus,
                    CollectedDate, UpdatedDate, BrandID
                )
                VALUES (
                    N'자사몰', source.SourceOrderID, N'3P',
                    source.OrderDate, source.shippedDate, 45, source.ProductID, source.CustomerName,
                    source.OrderQuantity, source.OrderPrice, source.OrderAmountExVAT, source.OrderAmountInVAT, source.OrderStatus,
                    source.CollectedDate, GETDATE(), 0
                );
        """

        try:
            print("\n[Frog Cafe24 → OrdersRealtime MERGE 시작]")
            print("-" * 70)

            self.cursor.execute(merge_sql)
            rows_affected = self.cursor.rowcount
            self.connection.commit()

            print(f"  처리 완료: {rows_affected}건")

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
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
