"""
사방넷 설정 파일 - 환경변수 및 설정 관리
SystemConfig DB에서 설정 로드 (환경변수 fallback 포함)
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일 로드 (fallback용)
load_dotenv()

# 상위 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

# 기본 설정 (fallback용)
_DEFAULT_CONFIG = {
    'company_id': 'vorio01',
    'auth_key': '3S200SM93ASbFJ3RR3u0Z1S1E9CSrHX0GCN',
    'api_url': 'https://sbadmin07.sabangnet.co.kr/RTL_API/xml_order_info.html'
}


def get_sabangnet_config() -> dict:
    """
    사방넷 설정 로드 (SystemConfig → 환경변수 → 기본값 순서)

    Returns:
        dict: 사방넷 설정
    """
    try:
        from system_config import get_config
        config = get_config()

        return {
            'company_id': config.get('Sabangnet', 'COMPANY_ID') or os.getenv('SABANGNET_COMPANY_ID', _DEFAULT_CONFIG['company_id']),
            'auth_key': config.get('Sabangnet', 'AUTH_KEY') or os.getenv('SABANGNET_AUTH_KEY', _DEFAULT_CONFIG['auth_key']),
            'api_url': config.get('Sabangnet', 'API_URL') or os.getenv('SABANGNET_API_URL', _DEFAULT_CONFIG['api_url']),
        }
    except Exception as e:
        logger.warning(f"[WARNING] SystemConfig 로드 실패, 환경변수 fallback: {e}")
        return {
            'company_id': os.getenv('SABANGNET_COMPANY_ID', _DEFAULT_CONFIG['company_id']),
            'auth_key': os.getenv('SABANGNET_AUTH_KEY', _DEFAULT_CONFIG['auth_key']),
            'api_url': os.getenv('SABANGNET_API_URL', _DEFAULT_CONFIG['api_url']),
        }


# 모듈 레벨 상수 (다른 모듈에서 import용)
SABANGNET_CONFIG = get_sabangnet_config()

# Azure Blob Storage 설정
AZURE_BLOB_CONFIG = {
    'connection_string': os.getenv('AZURE_STORAGE_CONNECTION_STRING'),
    'container_name': os.getenv('AZURE_BLOB_CONTAINER_NAME', 'sabangnet-orders'),
}

# Azure Database 설정
AZURE_DB_CONFIG = {
    'server': os.getenv('AZURE_DB_SERVER') or os.getenv('DB_SERVER'),
    'database': os.getenv('AZURE_DB_DATABASE') or os.getenv('DB_DATABASE'),
    'username': os.getenv('AZURE_DB_USERNAME') or os.getenv('DB_USERNAME'),
    'password': os.getenv('AZURE_DB_PASSWORD') or os.getenv('DB_PASSWORD'),
    'driver': os.getenv('AZURE_DB_DRIVER', '{ODBC Driver 18 for SQL Server}'),
}

# 주문 수집 설정
ORDER_CONFIG = {
    'default_days': 7,  # 기본 수집 기간 (일)
    'order_status': '',  # 주문 상태 코드 (빈 문자열 = 전체 수집)
    'order_fields': [
        'IDX', 'ORDER_ID', 'ORDER_DATE', 'ORDER_STATUS', 'MALL_ID',
        'USER_NAME', 'USER_TEL', 'RECEIVE_TEL',
        'MALL_PRODUCT_ID', 'PRODUCT_NAME', 'PRODUCT_ID', 'P_PRODUCT_NAME', 'SKU_ID', 'GOODS_NM_PR',
        'SET_GUBUN', 'ord_field2', 'BRAND_NM', 'SALE_CNT', 'PAY_COST', 'DELV_COST', 'DELIVERY_METHOD_STR',
        'DELIVERY_CONFIRM_DATE',  # 출고 완료일자
    ],
}

# 로그 설정
LOG_CONFIG = {
    'log_dir': 'logs',
    'log_file': 'sabangnet.log',
    'log_level': 'INFO',
}


def get_date_range(days: int = 10):
    """
    오늘부터 N일 전까지의 날짜 범위 반환

    Args:
        days: 수집할 기간 (일)

    Returns:
        tuple: (시작일, 종료일) YYYYMMDD 형식
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    return (
        start_date.strftime('%Y%m%d'),
        end_date.strftime('%Y%m%d')
    )


def get_current_timestamp():
    """
    현재 타임스탬프 반환 (파일명용)

    Returns:
        str: YYYYMMDD_HHmmss 형식
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S')
