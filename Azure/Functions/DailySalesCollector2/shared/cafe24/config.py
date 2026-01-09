"""
Cafe24 Upload Pipeline - 설정 파일
SystemConfig DB에서 설정 로드 (환경변수 fallback 포함)
"""
import os
import sys
import logging

# 상위 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

# 기본 설정 (fallback용)
_DEFAULT_CONFIG = {
    "mall_id": "vorio01",
    "client_id": "DF3fUZHlPqyYfnK7o8VViI",
    "client_secret": "dIOYk6ZHL1sogRqndsfmnG",
    "redirect_uri": "https://vorio01.cafe24.com"
}


def get_cafe24_config() -> dict:
    """
    Cafe24 설정 로드 (SystemConfig → 환경변수 → 기본값 순서)

    Returns:
        dict: Cafe24 설정
    """
    try:
        from system_config import get_config
        config = get_config()

        return {
            "mall_id": config.get('Cafe24', 'MALL_ID') or os.getenv('CAFE24_MALL_ID', _DEFAULT_CONFIG['mall_id']),
            "client_id": config.get('Cafe24', 'CLIENT_ID') or os.getenv('CAFE24_CLIENT_ID', _DEFAULT_CONFIG['client_id']),
            "client_secret": config.get('Cafe24', 'CLIENT_SECRET') or os.getenv('CAFE24_CLIENT_SECRET', _DEFAULT_CONFIG['client_secret']),
            "redirect_uri": _DEFAULT_CONFIG['redirect_uri']
        }
    except Exception as e:
        logger.warning(f"[WARNING] SystemConfig 로드 실패, 환경변수 fallback: {e}")
        return {
            "mall_id": os.getenv('CAFE24_MALL_ID', _DEFAULT_CONFIG['mall_id']),
            "client_id": os.getenv('CAFE24_CLIENT_ID', _DEFAULT_CONFIG['client_id']),
            "client_secret": os.getenv('CAFE24_CLIENT_SECRET', _DEFAULT_CONFIG['client_secret']),
            "redirect_uri": _DEFAULT_CONFIG['redirect_uri']
        }


def get_api_version() -> str:
    """API 버전 로드"""
    try:
        from system_config import get_config
        config = get_config()
        return config.get('Cafe24', 'API_VERSION') or "2025-12-01"
    except Exception:
        return "2025-12-01"


# 모듈 레벨 상수 (다른 모듈에서 import용)
CAFE24_CONFIG = get_cafe24_config()
API_VERSION = get_api_version()
BASE_URL = f"https://{CAFE24_CONFIG['mall_id']}.cafe24api.com/api/v2"

# 토큰 파일 경로 (legacy, 더 이상 사용하지 않음)
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "cafe24_tokens.json")

# Azure Storage
BLOB_CONTAINER = "cafe24-orders"
BLOB_PREFIX = ""  # YYYY-MM-DD.json (루트 디렉토리)
