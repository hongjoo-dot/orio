"""
Cafe24 Analytics 데이터 DB 업로드 모듈
MERGE 로직: Date + Key 기준으로 INSERT or UPDATE
"""

import os
import pyodbc
import logging

logger = logging.getLogger(__name__)


class AnalyticsDatabaseUploader:
    """Cafe24 Analytics 데이터 DB 업로더"""

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

    def merge_domains(self, data: list, date: str) -> dict:
        """
        Cafe24VisitpathDomains 테이블 MERGE
        유입(domains) + 매출(domainsales) 합친 데이터

        Args:
            data: [{domain, visit_count, order_count, order_amount}, ...]
            date: 수집 기준일 (YYYY-MM-DD)
        """
        inserted = 0
        updated = 0

        for row in data:
            domain = row.get('domain', '')
            visit_count = row.get('visit_count')
            order_count = row.get('order_count')
            order_amount = row.get('order_amount')

            # 기존 데이터 확인
            self.cursor.execute(
                "SELECT ID FROM Cafe24VisitpathDomains WHERE Date = ? AND Domain = ?",
                (date, domain)
            )
            existing = self.cursor.fetchone()

            if existing:
                self.cursor.execute("""
                    UPDATE Cafe24VisitpathDomains SET
                        VisitCount = ?, OrderCount = ?, OrderAmount = ?,
                        CollectedDate = GETDATE()
                    WHERE Date = ? AND Domain = ?
                """, (visit_count, order_count, order_amount, date, domain))
                updated += 1
            else:
                self.cursor.execute("""
                    INSERT INTO Cafe24VisitpathDomains
                        (Date, Domain, VisitCount, OrderCount, OrderAmount, CollectedDate)
                    VALUES (?, ?, ?, ?, ?, GETDATE())
                """, (date, domain, visit_count, order_count, order_amount))
                inserted += 1

        self.connection.commit()
        logger.info(f"[Domains] INSERT {inserted}건, UPDATE {updated}건")
        return {"inserted": inserted, "updated": updated}

    def merge_ads(self, data: list, date: str) -> dict:
        """
        Cafe24VisitpathAds 테이블 MERGE
        유입(ads) + 매출(adsales) 합친 데이터
        """
        inserted = 0
        updated = 0

        for row in data:
            ad = row.get('ad', '')
            visit_count = row.get('visit_count')
            order_count = row.get('order_count')
            order_amount = row.get('order_amount')
            join_count = row.get('join_count')

            self.cursor.execute(
                "SELECT ID FROM Cafe24VisitpathAds WHERE Date = ? AND Ad = ?",
                (date, ad)
            )
            existing = self.cursor.fetchone()

            if existing:
                self.cursor.execute("""
                    UPDATE Cafe24VisitpathAds SET
                        VisitCount = ?, OrderCount = ?, OrderAmount = ?,
                        JoinCount = ?, CollectedDate = GETDATE()
                    WHERE Date = ? AND Ad = ?
                """, (visit_count, order_count, order_amount, join_count, date, ad))
                updated += 1
            else:
                self.cursor.execute("""
                    INSERT INTO Cafe24VisitpathAds
                        (Date, Ad, VisitCount, OrderCount, OrderAmount, JoinCount, CollectedDate)
                    VALUES (?, ?, ?, ?, ?, ?, GETDATE())
                """, (date, ad, visit_count, order_count, order_amount, join_count))
                inserted += 1

        self.connection.commit()
        logger.info(f"[Ads] INSERT {inserted}건, UPDATE {updated}건")
        return {"inserted": inserted, "updated": updated}

    def merge_keywords(self, data: list, date: str) -> dict:
        """
        Cafe24VisitpathKeywords 테이블 MERGE
        유입(keywords) + 매출(keywordsales) 합친 데이터
        """
        inserted = 0
        updated = 0

        for row in data:
            keyword = row.get('keyword', '')
            visit_count = row.get('visit_count')
            order_count = row.get('order_count')
            order_amount = row.get('order_amount')

            self.cursor.execute(
                "SELECT ID FROM Cafe24VisitpathKeywords WHERE Date = ? AND Keyword = ?",
                (date, keyword)
            )
            existing = self.cursor.fetchone()

            if existing:
                self.cursor.execute("""
                    UPDATE Cafe24VisitpathKeywords SET
                        VisitCount = ?, OrderCount = ?, OrderAmount = ?,
                        CollectedDate = GETDATE()
                    WHERE Date = ? AND Keyword = ?
                """, (visit_count, order_count, order_amount, date, keyword))
                updated += 1
            else:
                self.cursor.execute("""
                    INSERT INTO Cafe24VisitpathKeywords
                        (Date, Keyword, VisitCount, OrderCount, OrderAmount, CollectedDate)
                    VALUES (?, ?, ?, ?, ?, GETDATE())
                """, (date, keyword, visit_count, order_count, order_amount))
                inserted += 1

        self.connection.commit()
        logger.info(f"[Keywords] INSERT {inserted}건, UPDATE {updated}건")
        return {"inserted": inserted, "updated": updated}

    def merge_visitors(self, data: list) -> dict:
        """
        Cafe24Visitors 테이블 MERGE
        일별 방문자 수 데이터
        """
        inserted = 0
        updated = 0

        for row in data:
            # date 형식: "2026-04-01T00:00+09:00" → "2026-04-01"
            date_raw = row.get('date', '')
            date = date_raw[:10] if date_raw else None
            if not date:
                continue

            visit_count = row.get('visit_count')
            first_visit_count = row.get('first_visit_count')
            re_visit_count = row.get('re_visit_count')

            self.cursor.execute(
                "SELECT ID FROM Cafe24Visitors WHERE Date = ?",
                (date,)
            )
            existing = self.cursor.fetchone()

            if existing:
                self.cursor.execute("""
                    UPDATE Cafe24Visitors SET
                        VisitCount = ?, FirstVisitCount = ?, ReVisitCount = ?,
                        CollectedDate = GETDATE()
                    WHERE Date = ?
                """, (visit_count, first_visit_count, re_visit_count, date))
                updated += 1
            else:
                self.cursor.execute("""
                    INSERT INTO Cafe24Visitors
                        (Date, VisitCount, FirstVisitCount, ReVisitCount, CollectedDate)
                    VALUES (?, ?, ?, ?, GETDATE())
                """, (date, visit_count, first_visit_count, re_visit_count))
                inserted += 1

        self.connection.commit()
        logger.info(f"[Visitors] INSERT {inserted}건, UPDATE {updated}건")
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
