"""
Slack 알림 모듈
Sabangnet 매핑 실패 알림
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


def format_upload_result(upload_stats, single_product_failures, bom_failures):
    """
    업로드 결과를 슬랙 메시지 형식으로 포맷 (MERGE 방식)

    Args:
        upload_stats: 업로드 통계 dict
            - total_detail: 전체 Detail 건수
            - detail_inserted: Detail INSERT 건수
            - detail_updated: Detail UPDATE 건수
            - total_master: 전체 Master 건수
            - master_inserted: Master INSERT 건수
            - master_updated: Master UPDATE 건수
        single_product_failures: 단품 매핑 실패 건수
        bom_failures: BOM 매핑 실패 건수

    Returns:
        str: 포맷된 메시지
    """
    total_failures = single_product_failures + bom_failures

    if total_failures == 0:
        message = f"✅ *사방넷 주문 업로드 완료*\n\n"
    else:
        message = f"⚠️ *사방넷 주문 업로드 완료 (매핑 실패 있음)*\n\n"

    # Detail 통계
    message += f"📋 *Detail (구성품)*\n"
    message += f"   전체: {upload_stats['total_detail']}건\n"
    message += f"   INSERT: {upload_stats['detail_inserted']}건\n"
    message += f"   UPDATE: {upload_stats['detail_updated']}건\n\n"

    # Master 통계
    message += f"📦 *Master (주문)*\n"
    message += f"   전체: {upload_stats['total_master']}건\n"
    message += f"   INSERT: {upload_stats['master_inserted']}건\n"
    message += f"   UPDATE: {upload_stats['master_updated']}건\n\n"

    # 매핑 실패
    if total_failures > 0:
        message += f"❌ *매핑 실패*\n"
        if single_product_failures > 0:
            message += f"   단품: {single_product_failures}건\n"
        if bom_failures > 0:
            message += f"   BOM: {bom_failures}건\n"
        message += f"\n💡 *조치사항*:\n"
        message += f"1. Product/BOM 데이터 등록\n"
        message += f"2. `python retry_failed.py` 실행\n"
    else:
        message += f"🎉 *매핑 성공*: 100%\n"

    return message


def format_retry_result(retried_orders, success_count, remaining_failures):
    """
    재처리 결과를 슬랙 메시지 형식으로 포맷

    Args:
        retried_orders: 재처리 시도 건수
        success_count: 재처리 성공 건수
        remaining_failures: 여전히 실패한 건수

    Returns:
        str: 포맷된 메시지
    """
    message = f"🔄 *사방넷 실패 주문 재처리 완료*\n\n"
    message += f"📊 *재처리 시도*: {retried_orders}건\n"
    message += f"✅ *성공*: {success_count}건\n"

    if remaining_failures > 0:
        message += f"❌ *여전히 실패*: {remaining_failures}건\n"
        message += f"\n💡 추가 Product/BOM 등록 후 다시 시도하세요.\n"
    else:
        message += f"\n🎉 모든 주문이 성공적으로 매핑되었습니다!\n"

    return message
