"""
Slack 알림 모듈 (AdDataCollector)
SystemConfig 테이블에서 Webhook URL 로드
Meta / Naver 각각 별도 채널로 알림
"""

import requests
import logging
from datetime import datetime
from .system_config import get_config


def _send_to_webhook(message, webhook_url):
    """실제 Slack Webhook 전송"""
    if not webhook_url:
        return False

    try:
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 200:
            return True
        else:
            logging.warning(f"[SLACK] 전송 실패 (상태 코드: {response.status_code})")
            return False

    except Exception as e:
        logging.error(f"[SLACK] 전송 중 오류: {e}")
        return False


def send_meta_notification(message):
    """Meta 전용 Slack 알림"""
    config = get_config()
    webhook_url = config.get('MetaAdAPI', 'SLACK_WEBHOOK_URL')

    if not webhook_url:
        logging.warning("[SLACK] MetaAdAPI.SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
        return False

    return _send_to_webhook(message, webhook_url)


def send_naver_notification(message):
    """Naver 전용 Slack 알림"""
    config = get_config()
    webhook_url = config.get('NaverAdAPI', 'SLACK_WEBHOOK_URL')

    if not webhook_url:
        logging.warning("[SLACK] NaverAdAPI.SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
        return False

    return _send_to_webhook(message, webhook_url)


def format_meta_result(result):
    """Meta 수집 결과 포맷"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if result.get('success'):
        message = f"[OK] *Meta 광고 데이터 수집 완료*\n\n"
        message += f"*실행 시간*: {now}\n"
        message += f"*Daily*: {result.get('daily_count', 0)}건\n"
        message += f"*Breakdown*: {result.get('breakdown_count', 0)}건\n"
    else:
        message = f"[ERROR] *Meta 광고 데이터 수집 실패*\n\n"
        message += f"*실행 시간*: {now}\n"
        message += f"*에러*:\n```{result.get('error', 'Unknown error')}```"

    return message


def format_naver_result(result):
    """Naver 수집 결과 포맷"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if result.get('success'):
        message = f"[OK] *Naver 광고 데이터 수집 완료*\n\n"
        message += f"*실행 시간*: {now}\n"
        message += f"*수집 건수*: {result.get('count', 0)}건\n"
    else:
        message = f"[ERROR] *Naver 광고 데이터 수집 실패*\n\n"
        message += f"*실행 시간*: {now}\n"
        message += f"*에러*:\n```{result.get('error', 'Unknown error')}```"

    return message
