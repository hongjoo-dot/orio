"""
Slack 알림 모듈
"""

import requests
import os
import logging


def send_slack_notification(message, webhook_url=None):
    if not webhook_url:
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    if not webhook_url:
        logging.warning("[Slack] SLACK_WEBHOOK_URL 미설정, 알림 건너뜀")
        return False

    try:
        response = requests.post(webhook_url, json={"text": message}, timeout=10)
        if response.status_code == 200:
            logging.info("[Slack] 알림 전송 성공")
            return True
        else:
            logging.warning(f"[Slack] 전송 실패 (상태: {response.status_code})")
            return False
    except Exception as e:
        logging.warning(f"[Slack] 전송 오류: {e}")
        return False
