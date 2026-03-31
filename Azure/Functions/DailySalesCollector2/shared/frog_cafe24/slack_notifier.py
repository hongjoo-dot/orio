"""
Slack 알림 모듈 (Frog Cafe24)
"""

import requests
import os


def send_slack_notification(message, webhook_url=None):
    """Slack으로 알림 전송"""
    if not webhook_url:
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    if not webhook_url:
        print("[WARNING] SLACK_WEBHOOK_URL이 설정되지 않았습니다. 슬랙 알림을 건너뜁니다.")
        return False

    try:
        payload = {"text": message}
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
    """Frog Cafe24 업로드 결과를 슬랙 메시지 형식으로 포맷"""
    message = f"[Frog] *Cafe24 주문 데이터 업로드 완료*\n\n"
    message += f"*대상일*: {target_date}\n"
    message += f"*주문*: INSERT {result['inserted_orders']}건, UPDATE {result['updated_orders']}건\n"
    message += f"*상세*: INSERT {result['inserted_details']}건, UPDATE {result['updated_details']}건\n"
    message += f"*ProductID 매핑*: {result['product_id_mapped']}/{result['total_items']}건 성공\n"

    if result['product_id_not_mapped'] > 0:
        message += f"\n*[경고]* {result['product_id_not_mapped']}건의 아이템이 ProductID에 매핑되지 않았습니다!\n"

        if result['unmapped_codes']:
            unique_unmapped = list(set(result['unmapped_codes']))[:10]
            message += f"매핑 실패 코드: `{', '.join(unique_unmapped)}`"

    return message


def format_customer_result(result, total_customers):
    """Frog Cafe24 고객 데이터 업로드 결과를 슬랙 메시지 형식으로 포맷"""
    message = f"[Frog] *Cafe24 고객 데이터 업로드 완료*\n\n"
    message += f"*고객 수*: {total_customers}명\n"
    message += f"*INSERT*: {result['inserted']}건\n"
    message += f"*UPDATE*: {result['updated']}건\n"
    message += f"*총*: {result['total']}건 처리 완료\n"

    return message
