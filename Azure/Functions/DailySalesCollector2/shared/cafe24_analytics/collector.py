"""
Cafe24 Analytics API 수집 모듈
유입경로(도메인/광고/키워드) + 매출 전환 + 방문자 수 수집
"""

import requests
import time
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from cafe24.collector import Cafe24OrderCollector
from cafe24.config import CAFE24_CONFIG

logger = logging.getLogger(__name__)

ANALYTICS_BASE_URL = "https://ca-api.cafe24data.com"


class Cafe24AnalyticsCollector:
    """Cafe24 Analytics API 수집기"""

    def __init__(self):
        self.base_url = ANALYTICS_BASE_URL
        self.mall_id = CAFE24_CONFIG["mall_id"]
        # 기존 Cafe24OrderCollector의 토큰 관리 재사용
        self._order_collector = Cafe24OrderCollector()

    def get_access_token(self):
        """기존 Cafe24OrderCollector의 토큰 관리 재사용"""
        return self._order_collector.get_access_token()

    def _request(self, endpoint: str, start_date: str, end_date: str) -> dict:
        """
        Analytics API 공통 호출

        Args:
            endpoint: API 엔드포인트 (예: /visitpaths/domains)
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)

        Returns:
            dict: API 응답 JSON
        """
        access_token = self.get_access_token()
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        params = {
            "mall_id": self.mall_id,
            "shop_no": 1,
            "start_date": start_date,
            "end_date": end_date,
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 429:
                    logger.warning(f"[Rate Limit] {endpoint}, 3초 대기...")
                    time.sleep(3)
                    continue

                if response.status_code == 401:
                    logger.warning(f"[Auth] 토큰 만료, 재발급 시도...")
                    self._order_collector._refresh_access_token(
                        self._order_collector.get_access_token()
                    )
                    continue

                raise Exception(f"API 호출 실패: {response.status_code}, {response.text}")

            except requests.exceptions.Timeout:
                logger.warning(f"[Timeout] {endpoint} (시도 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise

        raise Exception(f"API 호출 실패: {endpoint} (최대 재시도 초과)")

    def collect_domains(self, start_date: str, end_date: str) -> list:
        """도메인별 유입 수집"""
        logger.info(f"[수집] 도메인별 유입: {start_date} ~ {end_date}")
        data = self._request("/visitpaths/domains", start_date, end_date)
        result = data.get("domains", [])
        logger.info(f"  → {len(result)}건")
        time.sleep(2)
        return result

    def collect_domainsales(self, start_date: str, end_date: str) -> list:
        """도메인별 매출 수집"""
        logger.info(f"[수집] 도메인별 매출: {start_date} ~ {end_date}")
        data = self._request("/visitpaths/domainsales", start_date, end_date)
        result = data.get("domainsales", [])
        logger.info(f"  → {len(result)}건")
        time.sleep(2)
        return result

    def collect_ads(self, start_date: str, end_date: str) -> list:
        """광고별 유입 수집"""
        logger.info(f"[수집] 광고별 유입: {start_date} ~ {end_date}")
        data = self._request("/visitpaths/ads", start_date, end_date)
        result = data.get("ads", [])
        logger.info(f"  → {len(result)}건")
        time.sleep(2)
        return result

    def collect_adsales(self, start_date: str, end_date: str) -> list:
        """광고별 매출 수집"""
        logger.info(f"[수집] 광고별 매출: {start_date} ~ {end_date}")
        data = self._request("/visitpaths/adsales", start_date, end_date)
        result = data.get("adsales", [])
        logger.info(f"  → {len(result)}건")
        time.sleep(2)
        return result

    def collect_keywords(self, start_date: str, end_date: str) -> list:
        """키워드별 유입 수집"""
        logger.info(f"[수집] 키워드별 유입: {start_date} ~ {end_date}")
        data = self._request("/visitpaths/keywords", start_date, end_date)
        result = data.get("keywords", [])
        logger.info(f"  → {len(result)}건")
        time.sleep(2)
        return result

    def collect_keywordsales(self, start_date: str, end_date: str) -> list:
        """키워드별 매출 수집"""
        logger.info(f"[수집] 키워드별 매출: {start_date} ~ {end_date}")
        data = self._request("/visitpaths/keywordsales", start_date, end_date)
        result = data.get("keywordsales", [])
        logger.info(f"  → {len(result)}건")
        time.sleep(2)
        return result

    def collect_visitors(self, start_date: str, end_date: str) -> list:
        """일별 방문자 수 수집"""
        logger.info(f"[수집] 일별 방문자: {start_date} ~ {end_date}")
        data = self._request("/visitors/view", start_date, end_date)
        result = data.get("view", [])
        logger.info(f"  → {len(result)}건")
        time.sleep(2)
        return result
