"""
Frog Cafe24 Upload Pipeline - 설정 파일
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
    "mall_id": "frogstore01",
    "client_id": "jYJYuHUrEtolg5egal8FRD",
    "client_secret": "arf40GUJLCbdjTbQlsKsLB",
    "redirect_uri": "https://frogstore01.cafe24.com/"
}


def get_cafe24_config() -> dict:
    """
    Frog Cafe24 설정 로드 (SystemConfig → 환경변수 → 기본값 순서)
    """
    try:
        from system_config import get_config
        config = get_config()

        return {
            "mall_id": config.get('FrogCafe24', 'MALL_ID') or _DEFAULT_CONFIG['mall_id'],
            "client_id": config.get('FrogCafe24', 'CLIENT_ID') or _DEFAULT_CONFIG['client_id'],
            "client_secret": config.get('FrogCafe24', 'CLIENT_SECRET') or _DEFAULT_CONFIG['client_secret'],
            "redirect_uri": _DEFAULT_CONFIG['redirect_uri']
        }
    except Exception as e:
        logger.warning(f"[WARNING] SystemConfig 로드 실패, 기본값 fallback: {e}")
        return _DEFAULT_CONFIG.copy()


def get_api_version() -> str:
    """API 버전 로드"""
    try:
        from system_config import get_config
        config = get_config()
        return config.get('FrogCafe24', 'API_VERSION') or "2026-03-01"
    except Exception:
        return "2026-03-01"


# 모듈 레벨 상수 (다른 모듈에서 import용)
CAFE24_CONFIG = get_cafe24_config()
API_VERSION = get_api_version()
BASE_URL = f"https://{CAFE24_CONFIG['mall_id']}.cafe24api.com/api/v2"

# Azure Storage
BLOB_CONTAINER = "frog-cafe24-orders"
BLOB_PREFIX = ""
