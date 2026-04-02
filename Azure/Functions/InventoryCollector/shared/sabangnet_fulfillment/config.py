"""
사방넷 풀필먼트 API 설정 관리
- SystemConfig DB → 환경변수 → 기본값 순서로 로드
"""

import os
import logging
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)


def get_fulfillment_config() -> dict:
    """
    사방넷 풀필먼트 API 설정 로드

    Returns:
        dict: {api_access_key, api_secret_key, company_code, member_id, api_host}
    """
    config = {}

    # SystemConfig DB에서 먼저 시도
    try:
        from system_config import get_config
        sys_config = get_config()

        config = {
            'api_access_key': sys_config.get('SabangnetFBS', 'API_ACCESS_KEY'),
            'api_secret_key': sys_config.get('SabangnetFBS', 'API_SECRET_KEY'),
            'company_code': sys_config.get('SabangnetFBS', 'COMPANY_CODE'),
            'member_id': sys_config.get('SabangnetFBS', 'MEMBER_ID'),
            'api_host': sys_config.get('SabangnetFBS', 'API_HOST'),
        }
        logger.info("[Config] SystemConfig DB에서 로드 완료")
    except Exception as e:
        logger.warning(f"[Config] SystemConfig DB 로드 실패, 환경변수 사용: {e}")

    # 환경변수로 fallback (기본값 없음 - DB 또는 환경변수 필수)
    config['api_access_key'] = config.get('api_access_key') or os.getenv('SABANGNET_FBS_API_ACCESS_KEY', '')
    config['api_secret_key'] = config.get('api_secret_key') or os.getenv('SABANGNET_FBS_API_SECRET_KEY', '')
    config['company_code'] = config.get('company_code') or os.getenv('SABANGNET_FBS_COMPANY_CODE', '')
    config['member_id'] = config.get('member_id') or os.getenv('SABANGNET_FBS_MEMBER_ID', '')
    config['api_host'] = config.get('api_host') or os.getenv('SABANGNET_FBS_API_HOST', 'https://napi.sbfulfillment.co.kr')

    logger.info(f"[Config] company_code={config['company_code']}, member_id={config['member_id']}")

    return config
