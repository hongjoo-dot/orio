"""
Slack 알림 모듈
Webhook을 통해 메시지 전송
"""

import requests
import os


def send_slack_notification(message, webhook_url=None):
    """
    Slack으로 알림 전송

    Args:
        message: 전송할 메시지 (str)
        webhook_url: Slack Webhook URL (없으면 환경변수에서 로드)

    Returns:
        bool: 성공 여부
    """
    if not webhook_url:
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    if not webhook_url:
        print("[WARNING] SLACK_WEBHOOK_URL이 설정되지 않았습니다. 슬랙 알림을 건너뜁니다.")
        return False

    try:
        payload = {
            "text": message
        }

        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 200:
            print("[슬랙 알림] 전송 성공")
            return True
        else:
            print(f"[슬랙 알림] 전송 실패 (상태 코드: {response.status_code})")
            return False

    except Exception as e:
        print(f"[슬랙 알림] 전송 중 오류: {e}")
        return False


def format_cafe24_result(result, target_date):
    """
    Cafe24 업로드 결과를 슬랙 메시지 형식으로 포맷

    Args:
        result: merge_orders 결과 dict
        target_date: 대상 날짜 (YYYY-MM-DD)

    Returns:
        str: 포맷된 메시지
    """
    message = f"📦 *Cafe24 주문 데이터 업로드 완료*\n\n"
    message += f"📅 *대상일*: {target_date}\n"
    message += f"📊 *주문*: INSERT {result['inserted_orders']}건, UPDATE {result['updated_orders']}건\n"
    message += f"📋 *상세*: INSERT {result['inserted_details']}건, UPDATE {result['updated_details']}건\n"
    message += f"🔗 *ProductID 매핑*: {result['product_id_mapped']}/{result['total_items']}건 성공\n"

    # 매핑 실패 경고
    if result['product_id_not_mapped'] > 0:
        message += f"\n*[경고]* {result['product_id_not_mapped']}건의 아이템이 ProductID에 매핑되지 않았습니다!\n"

        # 실패 코드 목록 (최대 10개)
        if result['unmapped_codes']:
            unique_unmapped = list(set(result['unmapped_codes']))[:10]
            message += f"매핑 실패 코드: `{', '.join(unique_unmapped)}`"

    return message


def format_customer_result(result, total_customers):
    """
    Cafe24 고객 데이터 업로드 결과를 슬랙 메시지 형식으로 포맷

    Args:
        result: merge_customers 결과 dict
        total_customers: 수집된 고객 수

    Returns:
        str: 포맷된 메시지
    """
    message = f"[사용자] *Cafe24 고객 데이터 업로드 완료*\n\n"
    message += f"[수집] *고객 수*: {total_customers}명\n"
    message += f"[DB] *INSERT*: {result['inserted']}건\n"
    message += f"[DB] *UPDATE*: {result['updated']}건\n"
    message += f"[결과] *총*: {result['total']}건 처리 완료\n"

    return message
