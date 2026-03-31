"""
Frog Cafe24 주문 수집 모듈
SystemConfig DB 기반 토큰 관리
"""

import requests
import json
import time
import os
import sys
import logging
from datetime import datetime, timedelta

# 상위 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from system_config import get_config, update_config
from .config import get_cafe24_config, CAFE24_CONFIG, API_VERSION, BASE_URL

logger = logging.getLogger(__name__)


class Cafe24OrderCollector:
    """Frog Cafe24 주문 수집기 (SystemConfig DB 기반 토큰 관리)"""

    def __init__(self):
        self.base_url = BASE_URL

        # SystemConfig에서 설정 로드
        config = get_cafe24_config()
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.mall_id = config['mall_id']

    def get_access_token(self):
        """
        Access Token 가져오기 (SystemConfig DB 기반 자동 갱신)
        """
        access_token = None
        refresh_token = None
        token_source = None

        # 1. SystemConfig DB에서 토큰 로드 시도
        try:
            config = get_config()
            access_token = config.get('FrogCafe24', 'ACCESS_TOKEN')
            refresh_token = config.get('FrogCafe24', 'REFRESH_TOKEN')

            if access_token:
                token_source = 'SystemConfig'
                logger.info("[INFO] SystemConfig DB에서 Frog Cafe24 Access Token 로드 완료")
        except Exception as e:
            logger.warning(f"[WARNING] SystemConfig 로드 실패: {e}")

        # 2. 둘 다 없으면 에러
        if not access_token:
            raise Exception("토큰 로드 실패: SystemConfig에서 FrogCafe24 ACCESS_TOKEN을 찾을 수 없습니다.")

        # 3. Refresh Token으로 자동 갱신 시도 (항상 갱신하여 최신 토큰 유지)
        if refresh_token:
            logger.info("[INFO] Refresh Token으로 Access Token 갱신 시도")
            new_token = self._refresh_access_token(refresh_token)
            if new_token:
                logger.info("[INFO] Access Token 갱신 성공")
                return new_token
            else:
                logger.warning("[WARNING] Access Token 갱신 실패, 기존 토큰 사용")

        return access_token

    def _refresh_access_token(self, refresh_token: str) -> str:
        """
        Refresh Token으로 Access Token 갱신
        갱신된 토큰은 SystemConfig DB에 저장
        """
        url = f"{self.base_url}/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        auth = (self.client_id, self.client_secret)

        try:
            response = requests.post(url, data=data, auth=auth, timeout=30)

            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data.get('access_token')
                new_refresh_token = token_data.get('refresh_token')
                expires_in = token_data.get('expires_in', 7200)

                if new_access_token:
                    expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

                    # SystemConfig DB에 저장
                    update_config('FrogCafe24', 'ACCESS_TOKEN', new_access_token, 'FrogCafe24Collector')
                    update_config('FrogCafe24', 'TOKEN_EXPIRES_AT', expires_at, 'FrogCafe24Collector')

                    if new_refresh_token and new_refresh_token != refresh_token:
                        update_config('FrogCafe24', 'REFRESH_TOKEN', new_refresh_token, 'FrogCafe24Collector')
                        refresh_expires_at = (datetime.now() + timedelta(days=14)).isoformat()
                        update_config('FrogCafe24', 'REFRESH_TOKEN_EXPIRES_AT', refresh_expires_at, 'FrogCafe24Collector')

                    logger.info(f"[INFO] 토큰 갱신 완료 (유효기간: {expires_in}초)")
                    return new_access_token

            else:
                logger.warning(f"[WARNING] 토큰 갱신 실패: {response.status_code}, {response.text}")
                return None

        except Exception as e:
            logger.warning(f"[WARNING] 토큰 갱신 중 오류: {e}")
            return None

    def get_orders_by_date_range(self, start_date: str, end_date: str, access_token: str = None):
        """
        날짜 범위의 주문 수집
        """
        if not access_token:
            access_token = self.get_access_token()

        url = f"{self.base_url}/admin/orders"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Cafe24-Api-Version": API_VERSION
        }

        all_orders = []
        offset = 0
        limit = 100

        print(f"\n[Frog Cafe24 수집 시작] 기간: {start_date} ~ {end_date}")
        print("-" * 70)

        while True:
            params = {
                "limit": limit,
                "offset": offset,
                "start_date": start_date,
                "end_date": end_date,
                "embed": "items"
            }

            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)

                if response.status_code == 401:
                    print("[인증] 토큰 만료, 자동 갱신 중...")
                    access_token = self.get_access_token()
                    headers["Authorization"] = f"Bearer {access_token}"
                    continue

                if response.status_code == 429:
                    print("[대기] API 호출 제한, 2초 대기...")
                    time.sleep(2)
                    continue

                if response.status_code != 200:
                    raise Exception(f"주문 조회 실패: {response.status_code}, {response.text}")

                data = response.json()
                orders = data.get("orders", [])

                if not orders:
                    break

                all_orders.extend(orders)
                print(f"   수집 완료: {len(orders)}건 (총 {len(all_orders)}건)")

                offset += limit
                time.sleep(0.3)

            except Exception as e:
                print(f"[ERROR] 수집 중 오류: {e}")
                raise

        print(f"[완료] 총 {len(all_orders)}건 수집")
        return all_orders

    def get_rolling_orders(self, days: int = 10):
        """최근 N일간 주문 롤링 수집"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self.get_orders_by_date_range(start_date, end_date)
