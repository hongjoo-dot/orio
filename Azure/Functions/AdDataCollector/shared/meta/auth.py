"""
Meta API 인증 모듈 (Azure Functions용)
SystemConfig 테이블을 사용하여 토큰 관리
"""

import requests
import logging
from datetime import datetime
from ..system_config import get_config, update_config

class MetaAPIAuth:
    """Meta API 인증 관리 클래스"""

    # 만료 임박 기준 (7일)
    TOKEN_EXPIRY_WARNING_DAYS = 7

    def __init__(self):
        self.base_url = "https://graph.facebook.com/v19.0"
        config = get_config()
        self.app_id = config.get('MetaAdAPI', 'APP_ID')
        self.app_secret = config.get('MetaAdAPI', 'APP_SECRET')
        self.access_token = config.get('MetaAdAPI', 'ACCESS_TOKEN')

        if not self.app_id or not self.app_secret or not self.access_token:
            raise ValueError("Meta API 설정이 SystemConfig에 없습니다. (APP_ID, APP_SECRET, ACCESS_TOKEN)")

    def get_current_token(self) -> str:
        """현재 토큰 반환"""
        return self.access_token

    def check_token_expiry(self) -> dict:
        """토큰 만료 상태 점검. 반환: {'is_valid': bool, 'days_left': int or None, 'warning': bool}"""
        url = f"{self.base_url}/debug_token"
        params = {
            'input_token': self.access_token,
            'access_token': f"{self.app_id}|{self.app_secret}"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json().get('data', {})

            is_valid = data.get('is_valid', False)
            expires_at = data.get('expires_at', 0)

            if not is_valid:
                logging.error("[MetaAPI] 토큰이 유효하지 않습니다.")
                return {'is_valid': False, 'days_left': None, 'warning': True}

            if expires_at == 0:
                # 만료 없는 토큰 (System User 등)
                logging.info("[MetaAPI] 토큰 만료 없음 (영구 토큰)")
                return {'is_valid': True, 'days_left': None, 'warning': False}

            days_left = (datetime.fromtimestamp(expires_at) - datetime.now()).days
            warning = days_left <= self.TOKEN_EXPIRY_WARNING_DAYS

            logging.info(f"[MetaAPI] 토큰 잔여일: {days_left}일")
            if warning:
                logging.warning(f"[MetaAPI] 토큰 만료 임박! {days_left}일 남음")

            return {'is_valid': True, 'days_left': days_left, 'warning': warning}

        except Exception as e:
            logging.error(f"[MetaAPI] 토큰 상태 점검 실패: {e}")
            return {'is_valid': False, 'days_left': None, 'warning': True}

    def refresh_long_lived_token(self) -> bool:
        """토큰 갱신 및 DB 업데이트"""
        url = f"{self.base_url}/oauth/access_token"
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'fb_exchange_token': self.access_token
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            new_token = data.get('access_token')
            if new_token:
                self.access_token = new_token
                update_config('MetaAdAPI', 'ACCESS_TOKEN', new_token, updated_by='AzureFunction')
                print(f"[MetaAPI] 토큰 갱신 완료 (유효기간: {data.get('expires_in')}초)")
                return True
            return False

        except Exception as e:
            print(f"[ERROR] 토큰 갱신 실패: {e}")
            return False
