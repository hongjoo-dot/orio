"""
Slack 알림 모듈 (범용)
- 다양한 알림 유형 지원
- 포맷 템플릿 제공
- SystemConfig에서 webhook URL 조회 지원
"""

import os
import requests
from datetime import datetime
from typing import Optional, Dict, Any


def _get_webhook_url_from_config() -> Optional[str]:
    """SystemConfig에서 Slack Webhook URL 조회 (실패 시 None)"""
    try:
        from repositories.system_config_repository import SystemConfigRepository
        repo = SystemConfigRepository()
        config = repo.get_config_by_key('Notification', 'SlackWebhookURL')
        if config and config.get('IsActive') and config.get('ConfigValue'):
            return config['ConfigValue']
    except Exception:
        pass
    return None


def _is_notification_enabled(config_key: str = 'ExpectedSalesNotification') -> bool:
    """SystemConfig에서 알림 활성화 여부 확인"""
    try:
        from repositories.system_config_repository import SystemConfigRepository
        repo = SystemConfigRepository()
        config = repo.get_config_by_key('Notification', config_key)
        if config:
            if not config.get('IsActive'):
                return False
            return config.get('ConfigValue', '').lower() in ('true', '1', 'yes', 'on')
    except Exception:
        pass
    return True  # 기본값: 활성


def send_slack_notification(message: str, webhook_url: Optional[str] = None) -> bool:
    """
    Slack으로 메시지 전송 (범용)

    Args:
        message: 전송할 메시지 (Markdown 지원)
        webhook_url: Slack Webhook URL (없으면 SystemConfig → 환경변수 순서로 로드)

    Returns:
        bool: 전송 성공 여부
    """
    try:
        if not webhook_url:
            webhook_url = _get_webhook_url_from_config()

        if not webhook_url:
            webhook_url = os.getenv('SLACK_WEBHOOK_URL')

        if not webhook_url:
            print("[경고] Slack Webhook URL이 설정되지 않았습니다. (SystemConfig 또는 환경변수)")
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


# ========== 예상 매출 업로드/수정 알림 ==========

def send_expected_upload_notification(
    sales_type: str,
    data_type: str,
    total_rows: int,
    inserted: int,
    updated: int,
    year_month: Optional[str] = None,
    input_month: Optional[str] = None,
    username: Optional[str] = None,
    change_summary: Optional[Dict[str, Any]] = None,
    action: str = "업로드"
) -> bool:
    """
    예상 매출 업로드 완료 알림

    Args:
        sales_type: '위탁(3P)' 또는 '사입(1P)'
        data_type: '정기' 또는 '비정기'
        total_rows: 총 행 수
        inserted: 신규 삽입 수
        updated: 수정 수
        year_month: 대상 년월
        input_month: 입력월(Round)
        username: 업로드한 사용자
        change_summary: 변동 요약 {'before_amount': ..., 'after_amount': ..., 'before_qty': ..., 'after_qty': ...}

    Returns:
        bool: 전송 성공 여부
    """
    if not _is_notification_enabled('ExpectedSalesNotification'):
        print("[Slack] 예상 매출 알림이 비활성화되어 있습니다.")
        return False

    label = f"{sales_type} {data_type}"
    message = f"📊 *[{label}] 예상매출 {action}*\n"

    # 년월 / 입력월
    meta_parts = []
    if year_month:
        meta_parts.append(f"년월: {year_month}")
    if input_month:
        meta_parts.append(f"입력월: {input_month}")
    if meta_parts:
        message += " | ".join(meta_parts) + "\n"

    # 건수
    message += f"신규 {inserted:,} / 수정 {updated:,} / 총 {total_rows:,}건\n"

    # 변동률
    if change_summary:
        before_amt = change_summary.get('before_amount', 0) or 0
        after_amt = change_summary.get('after_amount', 0) or 0
        before_qty = change_summary.get('before_qty', 0) or 0
        after_qty = change_summary.get('after_qty', 0) or 0

        parts = []
        if before_amt > 0:
            amt_change = ((after_amt - before_amt) / before_amt) * 100
            sign = "+" if amt_change >= 0 else ""
            parts.append(f"예상금액 {sign}{amt_change:.1f}%")
        elif after_amt > 0:
            parts.append(f"예상금액 신규({after_amt:,.0f})")

        if before_qty > 0:
            qty_change = ((after_qty - before_qty) / before_qty) * 100
            sign = "+" if qty_change >= 0 else ""
            parts.append(f"예상수량 {sign}{qty_change:.1f}%")
        elif after_qty > 0:
            parts.append(f"예상수량 신규({after_qty:,.0f})")

        if parts:
            message += "변동: " + ", ".join(parts) + "\n"

    # 담당자 + 시간
    who = username or "시스템"
    message += f"담당: {who} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    return send_slack_notification(message)


def send_expected_upload_notification_async(
    sales_type: str,
    data_type: str,
    total_rows: int,
    inserted: int,
    updated: int,
    year_month: Optional[str] = None,
    input_month: Optional[str] = None,
    username: Optional[str] = None,
    change_summary: Optional[Dict[str, Any]] = None,
    action: str = "업로드"
) -> None:
    """
    예상 매출 업로드/수정 알림 (비동기, 실패해도 무시)
    응답을 지연시키지 않기 위해 threading 사용
    """
    import threading
    thread = threading.Thread(
        target=send_expected_upload_notification,
        args=(sales_type, data_type, total_rows, inserted, updated),
        kwargs={
            'year_month': year_month,
            'input_month': input_month,
            'username': username,
            'change_summary': change_summary,
            'action': action
        },
        daemon=True
    )
    thread.start()


# ==================== SKU 인라인 수정 알림 ====================

def send_sku_inline_update_notification(
    unique_code: str,
    product_name: str,
    changes: list,
    username: Optional[str] = None,
) -> bool:
    """
    SKU 인라인 수정 알림 (채널별 변동 상세)

    Args:
        unique_code: SKU 고유 코드
        product_name: 상품명
        changes: [{'channel': ..., 'source_type': ..., 'year_month': ...,
                    'old_amount': ..., 'new_amount': ..., 'old_qty': ..., 'new_qty': ...}, ...]
        username: 수정한 사용자

    Returns:
        bool: 전송 성공 여부
    """
    if not _is_notification_enabled('ExpectedSalesNotification'):
        return False

    message = f"📦 *[SKU 수정] 예상 판매량 변경*\n"
    message += f"상품: {unique_code} ({product_name})\n\n"

    for ch in changes:
        channel = ch.get('channel', '')
        source_type = ch.get('source_type', '')
        year_month = ch.get('year_month', '')
        old_amt = float(ch.get('old_amount', 0) or 0)
        new_amt = float(ch.get('new_amount', 0) or 0)
        old_qty = int(ch.get('old_qty', 0) or 0)
        new_qty = int(ch.get('new_qty', 0) or 0)

        label = f"{channel} {source_type}" if channel != '불출' else "불출"
        parts = []

        # 예상매출 변동
        if old_amt != new_amt:
            if old_amt > 0:
                pct = ((new_amt - old_amt) / old_amt) * 100
                sign = "+" if pct >= 0 else ""
                parts.append(f"예상매출 {old_amt:,.0f} → {new_amt:,.0f} ({sign}{pct:.1f}%)")
            else:
                parts.append(f"예상매출 0 → {new_amt:,.0f}")

        # 수량 변동
        if old_qty != new_qty:
            if old_qty > 0:
                pct = ((new_qty - old_qty) / old_qty) * 100
                sign = "+" if pct >= 0 else ""
                parts.append(f"수량 {old_qty:,} → {new_qty:,} ({sign}{pct:.1f}%)")
            else:
                parts.append(f"수량 0 → {new_qty:,}")

        if parts:
            message += f"  {label} ({year_month}) | {' / '.join(parts)}\n"

    message += f"\n수정 건수: {len(changes)}건\n"
    who = username or "시스템"
    message += f"담당: {who} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    return send_slack_notification(message)


def send_sku_inline_update_notification_async(
    unique_code: str,
    product_name: str,
    changes: list,
    username: Optional[str] = None,
) -> None:
    """SKU 인라인 수정 알림 (비동기)"""
    import threading
    thread = threading.Thread(
        target=send_sku_inline_update_notification,
        args=(unique_code, product_name, changes),
        kwargs={'username': username},
        daemon=True
    )
    thread.start()


# ==================== 엑셀 업로드 변동 감지 알림 ====================

def send_upload_diff_notification(
    sales_type: str,
    data_type: str,
    current_input_month: str,
    previous_input_month: str,
    diffs: list,
    username: Optional[str] = None,
) -> bool:
    """
    엑셀 업로드 시 이전 입력월 대비 변동 감지 알림

    Args:
        sales_type: '위탁(3P)' 또는 '사입(1P)'
        data_type: '정기' 또는 '비정기'
        current_input_month: 현재 입력월 (e.g. '2026-04')
        previous_input_month: 이전 입력월 (e.g. '2026-03')
        diffs: [{'unique_code': ..., 'product_name': ..., 'channel': ..., 'year_month': ...,
                 'prev_amount': ..., 'curr_amount': ..., 'prev_qty': ..., 'curr_qty': ...}, ...]
        username: 업로드한 사용자
    """
    if not _is_notification_enabled('ExpectedSalesNotification'):
        return False

    if not diffs:
        return False

    label = f"{sales_type} {data_type}"
    message = f"⚠️ *[{label}] 예상 판매량 변동 감지*\n"
    message += f"입력월: {previous_input_month} → {current_input_month}\n\n"

    for d in diffs[:15]:
        code = d.get('unique_code', '')
        channel = d.get('channel', '')
        ym = d.get('year_month', '')
        prev_amt = float(d.get('prev_amount', 0) or 0)
        curr_amt = float(d.get('curr_amount', 0) or 0)
        prev_qty = int(d.get('prev_qty', 0) or 0)
        curr_qty = int(d.get('curr_qty', 0) or 0)

        parts = []
        if prev_amt != curr_amt:
            if prev_amt > 0:
                pct = ((curr_amt - prev_amt) / prev_amt) * 100
                sign = "+" if pct >= 0 else ""
                parts.append(f"예상매출 {sign}{pct:.0f}%")
            else:
                parts.append(f"예상매출 신규")
        if prev_qty != curr_qty:
            if prev_qty > 0:
                pct = ((curr_qty - prev_qty) / prev_qty) * 100
                sign = "+" if pct >= 0 else ""
                parts.append(f"수량 {sign}{pct:.0f}%")
            else:
                parts.append(f"수량 신규")

        if parts:
            message += f"  {code} | {channel} {ym} | {', '.join(parts)}\n"

    if len(diffs) > 15:
        message += f"  ... 외 {len(diffs) - 15}건\n"

    message += f"\n변동 총 {len(diffs)}건\n"
    who = username or "시스템"
    message += f"담당: {who} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    return send_slack_notification(message)


def send_upload_diff_notification_async(
    sales_type: str,
    data_type: str,
    current_input_month: str,
    previous_input_month: str,
    diffs: list,
    username: Optional[str] = None,
) -> None:
    """엑셀 업로드 변동 감지 알림 (비동기)"""
    import threading
    thread = threading.Thread(
        target=send_upload_diff_notification,
        args=(sales_type, data_type, current_input_month, previous_input_month, diffs),
        kwargs={'username': username},
        daemon=True
    )
    thread.start()
