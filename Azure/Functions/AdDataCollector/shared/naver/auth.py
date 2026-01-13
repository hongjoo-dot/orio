"""
네이버 검색광고 API 인증 모듈 (Azure Functions용)
SystemConfig 테이블에서 인증정보 로드
"""

import hashlib
import hmac
import base64
import time
from ..system_config import get_config


class NaverAuth:
    """네이버 검색광고 API 인증 처리 클래스"""

    def __init__(self):
        config = get_config()
        self.customer_id = config.get('NaverAdAPI', 'CUSTOMER_ID')
        self.access_license = config.get('NaverAdAPI', 'ACCESS_LICENSE')
        self.secret_key = config.get('NaverAdAPI', 'SECRET_KEY')

        print(f"[Naver Auth] 인증 정보 로드:")
        print(f"  - CUSTOMER_ID: {'있음' if self.customer_id else '❌ 없음'}")
        print(f"  - ACCESS_LICENSE: {'있음' if self.access_license else '❌ 없음'}")
        print(f"  - SECRET_KEY: {'있음' if self.secret_key else '❌ 없음'}")

        if not self.customer_id or not self.access_license or not self.secret_key:
            raise ValueError("❌ Naver API 설정이 SystemConfig에 없습니다. (CUSTOMER_ID, ACCESS_LICENSE, SECRET_KEY)")

    def generate_signature(self, timestamp: str, method: str, uri: str) -> str:
        """API 요청에 필요한 서명 생성"""
        message = f"{timestamp}.{method}.{uri}"
        
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()

        return base64.b64encode(signature).decode('utf-8')

    def get_headers(self, method: str, uri: str) -> dict:
        """API 요청 헤더 생성"""
        timestamp = str(int(time.time() * 1000))
        signature = self.generate_signature(timestamp, method, uri)

        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Timestamp': timestamp,
            'X-API-KEY': self.access_license,
            'X-Customer': self.customer_id,
            'X-Signature': signature
        }

        return headers
