"""
Meta API 인증 모듈 (Azure Functions용)
SystemConfig 테이블을 사용하여 토큰 관리
"""

import requests
from datetime import datetime
from ..system_config import get_config, update_config

class MetaAPIAuth:
    """Meta API 인증 관리 클래스"""

    def __init__(self):
        self.base_url = "https://graph.facebook.com/v19.0"
        config = get_config()
        self.app_id = config.get('MetaAdAPI', 'APP_ID')
        self.app_secret = config.get('MetaAdAPI', 'APP_SECRET')
        self.access_token = config.get('MetaAdAPI', 'ACCESS_TOKEN')
        
        if not self.app_id or not self.app_secret or not self.access_token:
            raise ValueError("Meta API 설정이 SystemConfig에 없습니다. (APP_ID, APP_SECRET, ACCESS_TOKEN)")

    def get_current_token(self) -> str:
        """현재 토큰 반환 (필요시 갱신 로직 추가 가능)"""
        # 간단하게 현재 DB에 저장된 토큰 반환
        # 만료 임박 체크 및 갱신 로직은 복잡성을 줄이기 위해 생략하거나 필요시 추가
        return self.access_token

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
