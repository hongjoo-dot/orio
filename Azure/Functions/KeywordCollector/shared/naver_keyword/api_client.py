"""
네이버 검색광고 API 클라이언트
키워드 검색량 조회 기능
"""
import requests
import hmac
import hashlib
import base64
import time
import logging
from .config import CUSTOMER_ID, ACCESS_LICENSE, SECRET_KEY, BASE_URL, KEYWORDSTOOL_PATH


class NaverKeywordAPIClient:
    """네이버 검색광고 API 키워드 도구 클라이언트"""

    def __init__(self):
        self.customer_id = CUSTOMER_ID
        self.access_license = ACCESS_LICENSE
        self.secret_key = SECRET_KEY
        self.base_url = BASE_URL
        self.keywordstool_path = KEYWORDSTOOL_PATH

    def generate_signature(self, timestamp, method, path):
        """
        API 서명 생성

        Args:
            timestamp: 현재 timestamp (밀리초)
            method: HTTP 메서드 (GET, POST 등)
            path: API 경로

        Returns:
            str: Base64 encoded HMAC SHA256 서명
        """
        message = f"{timestamp}.{method}.{path}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')

    def get_keyword_stats(self, keyword, include_related=True):
        """
        키워드 검색량 조회

        Args:
            keyword: 조회할 키워드
            include_related: 연관 키워드 포함 여부 (기본값: True)

        Returns:
            dict: API 응답 데이터 또는 None
        """
        timestamp = str(int(time.time() * 1000))
        method = "GET"

        # 서명 생성
        signature = self.generate_signature(timestamp, method, self.keywordstool_path)

        # 헤더 설정
        headers = {
            "X-Timestamp": timestamp,
            "X-API-KEY": self.access_license,
            "X-Customer": self.customer_id,
            "X-Signature": signature
        }

        # 파라미터 설정
        params = {
            "hintKeywords": keyword,
            "showDetail": "1",
            "includeHintKeywords": "1"  # hint 키워드 항상 포함
        }

        try:
            response = requests.get(
                f"{self.base_url}{self.keywordstool_path}",
                headers=headers,
                params=params,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            logging.info(f"키워드 '{keyword}' 조회 성공: {len(result.get('keywordList', []))}개")
            return result

        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP 에러 (키워드: {keyword}): {e}")
            logging.error(f"Response: {response.text}")
            return None
        except Exception as e:
            logging.error(f"API 호출 에러 (키워드: {keyword}): {e}")
            return None
