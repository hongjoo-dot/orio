"""
Cafe24 Analytics API 수집 모듈
주문별 UTM 로우데이터 수집 (/sales/orderdetails)
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
    """Cafe24 Analytics API 수집기 - 주문별 UTM 로우데이터"""

    def __init__(self):
        self.base_url = ANALYTICS_BASE_URL
        self.mall_id = CAFE24_CONFIG["mall_id"]
        self._order_collector = Cafe24OrderCollector()

    def get_access_token(self):
        return self._order_collector.get_access_token()

    def _request(self, endpoint: str, params: dict) -> dict:
        """Analytics API 공통 호출"""
        access_token = self.get_access_token()
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
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
                    logger.warning("[Auth] 토큰 만료, 재발급 시도...")
                    access_token = self.get_access_token()
                    headers["Authorization"] = f"Bearer {access_token}"
                    continue

                raise Exception(f"API 호출 실패: {response.status_code}, {response.text}")

            except requests.exceptions.Timeout:
                logger.warning(f"[Timeout] {endpoint} (시도 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise

        raise Exception(f"API 호출 실패: {endpoint} (최대 재시도 초과)")

    def collect_orderdetails(self, start_date: str, end_date: str) -> list:
        """
        주문별 UTM 로우데이터 수집
        페이지네이션 처리 (offset/limit)

        Args:
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)

        Returns:
            list: [{order_id, order_date, ad, keyword, medium, campaign, content, payment_method, order_amount}, ...]
        """
        logger.info(f"[수집] 주문별 UTM: {start_date} ~ {end_date}")

        all_data = []
        offset = 0
        limit = 100

        while True:
            params = {
                "mall_id": self.mall_id,
                "shop_no": 1,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
                "offset": offset,
            }

            data = self._request("/sales/orderdetails", params)
            items = data.get("orderdetails", [])

            if not items:
                break

            all_data.extend(items)
            logger.info(f"  수집: {len(items)}건 (총 {len(all_data)}건)")

            if len(items) < limit:
                break

            offset += limit
            time.sleep(2)  # rate limit

        logger.info(f"[완료] 총 {len(all_data)}건 수집")
        return all_data
