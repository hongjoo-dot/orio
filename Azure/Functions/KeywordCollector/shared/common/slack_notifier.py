import requests
import logging
from datetime import datetime
from common.system_config import get_config

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

def send_keyword_notification(category, result):
    """키워드 수집 결과 Slack 알림"""
    config = get_config()
    webhook_url = config.get(category, 'SLACK_WEBHOOK_URL')

    if not webhook_url:
        logging.warning(f"[SLACK] {category}.SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
        return False

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    api_name = "Naver" if "Naver" in category else "Google"

    failed_keywords = result.get('failed_keywords', [])
    failed_count = result.get('failed_count', 0)
    missing_main = result.get('missing_main_keywords', [])

    if result.get('success'):
        message = f"[OK] *{api_name} 키워드 검색량 수집 완료*\n\n"
        message += f"*실행 시간*: {now}\n"
        message += f"*처리 키워드*: {result.get('total_keywords', 0)}개\n"
        message += f"*DB 저장*: {result.get('inserted_records', 0)}건\n"
    else:
        # Main 키워드 누락이 있는 경우 (심각)
        if missing_main:
            message = f"[CRITICAL] *{api_name} Main 키워드 누락 발생!*\n\n"
            message += f"*실행 시간*: {now}\n"
            message += f"*처리 키워드*: {result.get('total_keywords', 0)}개\n"
            message += f"*DB 저장*: {result.get('inserted_records', 0)}건\n"
            message += f"*Main 키워드 누락*: {len(missing_main)}개\n\n"
            message += "*누락된 Main 키워드:*\n"
            for mk in missing_main[:10]:
                message += f"  ⚠️ {mk['brand_name']}: *{mk['keyword']}*\n"
            if len(missing_main) > 10:
                message += f"  ... 외 {len(missing_main) - 10}개\n"

        # API 실패 키워드가 있는 경우
        if failed_keywords:
            if not missing_main:
                message = f"[WARN] *{api_name} 키워드 검색량 수집 일부 실패*\n\n"
                message += f"*실행 시간*: {now}\n"
                message += f"*처리 키워드*: {result.get('total_keywords', 0)}개\n"
                message += f"*DB 저장*: {result.get('inserted_records', 0)}건\n"
            message += f"\n*API 실패*: {len(failed_keywords)}개\n"
            message += "*실패한 키워드:*\n"
            for fk in failed_keywords[:5]:
                message += f"  • {fk['brand_name']}: {fk['compound_keyword']}\n"
            if len(failed_keywords) > 5:
                message += f"  ... 외 {len(failed_keywords) - 5}개\n"

        # 둘 다 없는데 실패한 경우
        if not missing_main and not failed_keywords:
            message = f"[ERROR] *{api_name} 키워드 검색량 수집 실패*\n\n"
            message += f"*실행 시간*: {now}\n"
            message += f"*에러*:\n```{result.get('error', 'Unknown error')}```"

    return _send_to_webhook(message, webhook_url)
