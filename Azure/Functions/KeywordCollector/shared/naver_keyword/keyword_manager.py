"""
키워드 설정 관리
Keyword 테이블에서 활성 키워드 조회
"""
import logging
from common.database import get_db_connection


class KeywordManager:
    """키워드 설정 관리 클래스"""

    def get_active_keywords_for_naver_ads(self):
        """
        네이버 검색광고 수집 대상 키워드 조회

        Returns:
            list: 키워드 딕셔너리 리스트
                [{
                    'keyword_id': int,
                    'keyword': str,
                    'brand_id': int,
                    'brand_name': str,
                    'category': str,
                    'priority': int
                }, ...]
        """
        conn = None
        keywords = []

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT
                k.KeywordID,
                k.Keyword,
                k.BrandID,
                b.Name AS BrandName,
                k.Category,
                k.Priority
            FROM Keyword k
            INNER JOIN Brand b ON k.BrandID = b.BrandID
            WHERE k.IsActive = 1
              AND k.CollectNaverAds = 1
              AND b.IsActive = 1
            ORDER BY k.Priority ASC, b.Name, k.Keyword
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                keywords.append({
                    'keyword_id': row[0],
                    'keyword': row[1],
                    'brand_id': row[2],
                    'brand_name': row[3],
                    'category': row[4] if row[4] else '',
                    'priority': row[5]
                })

            logging.info(f"네이버 검색광고 수집 대상 키워드: {len(keywords)}개")

        except Exception as e:
            logging.error(f"활성 키워드 조회 실패: {e}")
            raise

        finally:
            if conn:
                cursor.close()
                conn.close()

        return keywords

    def get_active_keywords_for_google_ads(self):
        """
        구글 검색광고 수집 대상 키워드 조회
        """
        conn = None
        keywords = []

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # CollectGoogleAds 칼럼을 사용하여 필터링
            query = """
            SELECT
                k.KeywordID,
                k.Keyword,
                k.BrandID,
                b.Name AS BrandName,
                k.Category,
                k.Priority
            FROM Keyword k
            INNER JOIN Brand b ON k.BrandID = b.BrandID
            WHERE k.IsActive = 1
              AND k.CollectGoogleAds = 1
              AND b.IsActive = 1
            ORDER BY k.Priority ASC, b.Name, k.Keyword
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                keywords.append({
                    'keyword_id': row[0],
                    'keyword': row[1],
                    'brand_id': row[2],
                    'brand_name': row[3],
                    'category': row[4] if row[4] else '',
                    'priority': row[5]
                })

            logging.info(f"구글 검색광고 수집 대상 키워드: {len(keywords)}개")

        except Exception as e:
            logging.error(f"구글 활성 키워드 조회 실패: {e}")
            # 만약 CollectGoogleAds 칼럼이 아직 없다면, 안전하게 네이버용을 반환하도록 예외 처리
            return self.get_active_keywords_for_naver_ads()

        finally:
            if conn:
                cursor.close()
                conn.close()

        return keywords

    def get_keywords_by_brand(self, brand_id):
        """
        특정 브랜드의 활성 키워드 조회

        Args:
            brand_id: 브랜드 ID

        Returns:
            list: 키워드 리스트
        """
        conn = None
        keywords = []

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT
                KeywordID,
                Keyword,
                Category,
                Priority
            FROM Keyword
            WHERE BrandID = ?
              AND IsActive = 1
            ORDER BY Priority ASC, Keyword
            """

            cursor.execute(query, (brand_id,))
            rows = cursor.fetchall()

            for row in rows:
                keywords.append({
                    'keyword_id': row[0],
                    'keyword': row[1],
                    'category': row[2] if row[2] else '',
                    'priority': row[3]
                })

        except Exception as e:
            logging.error(f"브랜드별 키워드 조회 실패 (BrandID: {brand_id}): {e}")

        finally:
            if conn:
                cursor.close()
                conn.close()

        return keywords

    def get_active_brands(self):
        """
        활성 브랜드 목록 조회

        Returns:
            list: 브랜드 딕셔너리 리스트
        """
        conn = None
        brands = []

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
            SELECT
                BrandID,
                Name,
                Title
            FROM Brand
            WHERE IsActive = 1
            ORDER BY Name
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                brands.append({
                    'brand_id': row[0],
                    'brand_name': row[1],
                    'brand_title': row[2] if row[2] else ''
                })

            logging.info(f"활성 브랜드: {len(brands)}개")

        except Exception as e:
            logging.error(f"활성 브랜드 조회 실패: {e}")

        finally:
            if conn:
                cursor.close()
                conn.close()

        return brands
