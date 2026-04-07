"""
Cafe24 Analytics 파이프라인 진입점
SystemConfig DB에서 설정 로드 후 main 실행
"""
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from system_config import get_config

logger = logging.getLogger(__name__)


def run_analytics_pipeline(days: int = None) -> dict:
    """
    Cafe24 Analytics 전체 파이프라인 실행

    Args:
        days: 수집 기간 (일) - None이면 DB 설정에서 로드

    Returns:
        dict: 실행 결과
    """
    if days is None:
        config = get_config()
        days = int(config.get('Cafe24Analytics', 'ROLLING_DAYS', 7))
        logger.info(f'DB에서 롤링 일수 로드: {days}일')

    logger.info(f'Cafe24 Analytics 파이프라인 시작 (최근 {days}일)')

    try:
        from .main import main as analytics_main
        result = analytics_main(days=days)

        logger.info('Cafe24 Analytics 파이프라인 완료')
        return result

    except Exception as e:
        logger.error(f'Cafe24 Analytics 파이프라인 오류: {str(e)}', exc_info=True)
        raise
