"""
Cafe24 주문별 UTM 데이터 DB 업로드 모듈
MERGE 로직: OrderID 기준으로 INSERT or UPDATE
"""

import os
import pyodbc
import logging

logger = logging.getLogger(__name__)


class AnalyticsDatabaseUploader:
    """Cafe24 주문별 UTM 데이터 DB 업로더"""

    def __init__(self):
        connection_string = self._get_connection_string()
        self.connection = pyodbc.connect(connection_string)
        self.cursor = self.connection.cursor()

    def _get_connection_string(self):
        server = os.getenv('DB_SERVER')
        database = os.getenv('DB_DATABASE')
        username = os.getenv('DB_USERNAME')
        password = os.getenv('DB_PASSWORD')
        driver = os.getenv('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')

        if not all([server, database, username, password]):
            raise Exception("DB 연결 정보가 환경변수에 없습니다.")

        return (
            f"DRIVER={driver};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=60;"
        )

    def merge_order_utm(self, data: list) -> dict:
        """
        Cafe24OrderUTM 테이블 MERGE

        Args:
            data: [{order_id, order_date, ad, keyword, medium, campaign, content, payment_method, order_amount}, ...]

        Returns:
            dict: {inserted, updated}
        """
        inserted = 0
        updated = 0

        for row in data:
            order_id = row.get('order_id', '')
            if not order_id:
                continue

            order_date = row.get('order_date')
            ad = row.get('ad', '')
            keyword = row.get('keyword', '')
            medium = row.get('medium', '')
            campaign = row.get('campaign', '')
            content = row.get('content', '')
            payment_method = row.get('payment_method', '')
            order_amount = row.get('order_amount')

            self.cursor.execute(
                "SELECT ID FROM Cafe24OrderUTM WHERE OrderID = ?",
                (order_id,)
            )
            existing = self.cursor.fetchone()

            if existing:
                self.cursor.execute("""
                    UPDATE Cafe24OrderUTM SET
                        OrderDate = ?,
                        Ad = ?, Keyword = ?, Medium = ?,
                        Campaign = ?, Content = ?,
                        PaymentMethod = ?, OrderAmount = ?,
                        CollectedDate = GETDATE()
                    WHERE OrderID = ?
                """, (
                    order_date,
                    ad, keyword, medium,
                    campaign, content,
                    payment_method, order_amount,
                    order_id
                ))
                updated += 1
            else:
                self.cursor.execute("""
                    INSERT INTO Cafe24OrderUTM (
                        OrderID, OrderDate,
                        Ad, Keyword, Medium, Campaign, Content,
                        PaymentMethod, OrderAmount, CollectedDate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    order_id, order_date,
                    ad, keyword, medium, campaign, content,
                    payment_method, order_amount
                ))
                inserted += 1

        self.connection.commit()
        logger.info(f"[OrderUTM] INSERT {inserted}건, UPDATE {updated}건")
        return {"inserted": inserted, "updated": updated}

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
