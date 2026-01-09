"""
Slack 알림 모듈 (범용)
- 다양한 알림 유형 지원
- 포맷 템플릿 제공
"""

import os
import requests
from datetime import datetime
from typing import Optional, Dict, Any


def send_slack_notification(message: str, webhook_url: Optional[str] = None) -> bool:
    """
    Slack으로 메시지 전송 (범용)

    Args:
        message: 전송할 메시지 (Markdown 지원)
        webhook_url: Slack Webhook URL (없으면 환경변수에서 로드)

    Returns:
        bool: 전송 성공 여부
    """
    try:
        if not webhook_url:
            webhook_url = os.getenv('SLACK_WEBHOOK_URL')

        if not webhook_url:
            print("[경고] SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
            return False

        payload = {"text": message}
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 200:
            print(f"[Slack] 알림 전송 성공")
            return True
        else:
            print(f"[Slack] 알림 전송 실패: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"[Slack] 알림 전송 중 에러: {str(e)}")
        return False


def send_success_notification(title: str, details: Dict[str, Any], duration: Optional[float] = None) -> bool:
    """
    성공 알림 전송 (범용 템플릿)

    Args:
        title: 알림 제목
        details: 상세 정보 딕셔너리
        duration: 소요 시간 (초)

    Returns:
        bool: 전송 성공 여부

    Example:
        send_success_notification(
            title="데이터 업로드 완료",
            details={
                "총 행 수": "1,000건",
                "성공": "950건",
                "실패": "50건"
            },
            duration=12.5
        )
    """
    message = f"✅ *{title}*\n\n"

    for key, value in details.items():
        message += f"• *{key}*: {value}\n"

    if duration:
        message += f"\n⏱️ *소요 시간*: {duration:.1f}초"

    message += f"\n\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return send_slack_notification(message)


def send_error_notification(title: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    에러 알림 전송 (범용 템플릿)

    Args:
        title: 에러 제목
        error_message: 에러 메시지
        context: 추가 컨텍스트 정보

    Returns:
        bool: 전송 성공 여부

    Example:
        send_error_notification(
            title="데이터 동기화 실패",
            error_message="Connection timeout",
            context={"시작 날짜": "2024-01-01", "종료 날짜": "2024-12-31"}
        )
    """
    message = f"❌ *{title}*\n\n"
    message += f"⚠️ *에러*: {error_message}\n"

    if context:
        message += f"\n📋 *컨텍스트*:\n"
        for key, value in context.items():
            message += f"  • {key}: {value}\n"

    message += f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return send_slack_notification(message)


def send_warning_notification(title: str, warning_message: str, details: Optional[Dict[str, Any]] = None) -> bool:
    """
    경고 알림 전송 (범용 템플릿)

    Args:
        title: 경고 제목
        warning_message: 경고 메시지
        details: 상세 정보

    Returns:
        bool: 전송 성공 여부
    """
    message = f"⚠️ *{title}*\n\n"
    message += f"{warning_message}\n"

    if details:
        message += f"\n📋 *상세*:\n"
        for key, value in details.items():
            message += f"  • {key}: {value}\n"

    message += f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return send_slack_notification(message)


# ========== 특정 기능별 알림 템플릿 ==========

def send_erpsales_upload_notification(
    filename: str,
    total_rows: int,
    inserted: int,
    failed: int,
    unmapped_brands: int = 0,
    unmapped_products: int = 0,
    unmapped_channels: int = 0,
    unmapped_channel_details: int = 0,
    unmapped_warehouses: int = 0,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    date_range: Optional[str] = None
) -> bool:
    """
    ERPSales 업로드 완료 알림
    """
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time

    duration = (end_time - start_time).total_seconds()
    success_rate = (inserted / total_rows * 100) if total_rows > 0 else 0

    status_emoji = "✅" if failed == 0 and unmapped_brands == 0 and unmapped_products == 0 else "⚠️"

    message = f"""
{status_emoji} *ERPSales 업로드 완료*

📁 *파일명*: {filename}
📊 *전체 행 수*: {total_rows:,}건
✅ *성공*: {inserted:,}건 ({success_rate:.1f}%)
❌ *실패*: {failed}건
⏱️ *소요 시간*: {duration:.1f}초
"""

    if date_range:
        message += f"📅 *데이터 기간*: {date_range}\n"

    mapping_warnings = []
    if unmapped_brands > 0:
        mapping_warnings.append(f"  • 브랜드: {unmapped_brands}개")
    if unmapped_products > 0:
        mapping_warnings.append(f"  • 상품코드: {unmapped_products}개")
    if unmapped_channels > 0:
        mapping_warnings.append(f"  • 채널: {unmapped_channels}개")
    if unmapped_channel_details > 0:
        mapping_warnings.append(f"  • 거래처: {unmapped_channel_details}개")
    if unmapped_warehouses > 0:
        mapping_warnings.append(f"  • 창고: {unmapped_warehouses}개")

    if mapping_warnings:
        message += f"\n⚠️ *매핑 실패*:\n" + "\n".join(mapping_warnings)

    message += f"\n\n🕐 {end_time.strftime('%Y-%m-%d %H:%M:%S')}"

    return send_slack_notification(message)


def send_sync_notification(
    insert_count: int,
    update_count: int,
    error_count: int,
    status: str,
    duration: float,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> bool:
    """
    ERPSales → OrdersRealtime 동기화 완료 알림
    """
    status_emoji = "✅" if error_count == 0 else "❌"

    message = f"""
📊 *ERPSales → OrdersRealtime 동기화 완료*

{status_emoji} *상태*: {status}
➕ *INSERT*: {insert_count:,}건
🔄 *UPDATE*: {update_count:,}건
❌ *ERROR*: {error_count}건
⏱️ *소요 시간*: {duration:.1f}초
"""

    if start_date or end_date:
        message += f"\n📅 *기간*: {start_date or '시작'} ~ {end_date or '종료'}"

    message += f"\n\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return send_slack_notification(message)
