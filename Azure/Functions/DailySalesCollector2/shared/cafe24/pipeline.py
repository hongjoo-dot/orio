"""
Cafe24 전체 파이프라인 실행 모듈
수집 -> Blob -> DB -> OrdersRealtime
"""
import logging
import sys
import os

# 공통 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from system_config import get_config

logger = logging.getLogger(__name__)


def run_cafe24_pipeline(days: int = None) -> dict:
    """
    Cafe24 전체 파이프라인 실행

    Args:
        days: 수집 기간 (일) - None이면 DB 설정에서 로드

    Returns:
        dict: 실행 결과
    """
    # DB에서 롤링 일수 로드 (파라미터가 없을 경우)
    if days is None:
        config = get_config()
        days = config.get('Cafe24', 'ROLLING_DAYS', 10)
        logger.info(f'DB에서 롤링 일수 로드: {days}일')

    logger.info(f'Cafe24 파이프라인 시작 (최근 {days}일)')

    result = {
        'collected': 0,
        'orders_inserted': 0,
        'orders_updated': 0,
        'detail_inserted': 0,
        'detail_updated': 0,
        'realtime_uploaded': 0,
        'blob_filename': None
    }

    try:
        logger.info('Step 1: Cafe24 데이터 수집 시작')

        from .main import main as cafe24_main
        cafe24_main(days=days)

        logger.info('Cafe24 전체 파이프라인 완료 (main 실행)')

        return result

    except Exception as e:
        logger.error(f'Cafe24 파이프라인 오류: {str(e)}', exc_info=True)
        raise
