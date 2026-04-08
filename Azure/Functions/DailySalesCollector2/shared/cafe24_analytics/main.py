"""
Cafe24 주문별 UTM 수집 메인 오케스트레이션
수집 → DB 업로드 → Slack 알림
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def main(days: int = 7):
    """
    Cafe24 주문별 UTM 수집 파이프라인

    Args:
        days: 수집 기간 (기본 7일)
    """
    from .collector import Cafe24AnalyticsCollector
    from .upload_to_db import AnalyticsDatabaseUploader

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    logger.info("=" * 70)
    logger.info(f"Cafe24 주문별 UTM 수집 시작: {start_date} ~ {end_date}")
    logger.info("=" * 70)

    # Step 1: 데이터 수집
    logger.info("Step 1: orderdetails API 수집")
    collector = Cafe24AnalyticsCollector()
    order_utm_data = collector.collect_orderdetails(start_date, end_date)

    if not order_utm_data:
        logger.info("수집된 데이터가 없습니다.")
        return {"inserted": 0, "updated": 0}

    # Step 2: DB 업로드
    logger.info("Step 2: DB 업로드")
    with AnalyticsDatabaseUploader() as db:
        result = db.merge_order_utm(order_utm_data)

    # Step 3: Slack 알림
    logger.info("Step 3: Slack 알림")
    try:
        from cafe24.slack_notifier import send_slack_notification

        message = (
            f"✅ *[Cafe24 UTM] 주문별 유입경로 수집 완료*\n\n"
            f"📅 기간: {start_date} ~ {end_date}\n"
            f"📊 수집: {len(order_utm_data)}건 "
            f"(INSERT {result['inserted']}, UPDATE {result['updated']})"
        )
        send_slack_notification(message)
    except Exception as e:
        logger.warning(f"Slack 알림 실패: {e}")

    logger.info("=" * 70)
    logger.info("Cafe24 주문별 UTM 수집 완료!")
    logger.info("=" * 70)

    return result


def backfill(start_date: str, end_date: str, chunk_days: int = 30):
    """
    과거 데이터 백필 (월 단위 청크)

    Args:
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        chunk_days: 청크 크기 (기본 30일)
    """
    from .collector import Cafe24AnalyticsCollector
    from .upload_to_db import AnalyticsDatabaseUploader

    logger.info("=" * 70)
    logger.info(f"Cafe24 UTM 백필 시작: {start_date} ~ {end_date} ({chunk_days}일 단위)")
    logger.info("=" * 70)

    collector = Cafe24AnalyticsCollector()

    current_start = datetime.strptime(start_date, "%Y-%m-%d")
    final_end = datetime.strptime(end_date, "%Y-%m-%d")
    total_inserted = 0
    total_updated = 0

    while current_start < final_end:
        current_end = min(current_start + timedelta(days=chunk_days), final_end)
        s = current_start.strftime("%Y-%m-%d")
        e = current_end.strftime("%Y-%m-%d")

        logger.info(f"\n[청크] {s} ~ {e}")
        data = collector.collect_orderdetails(s, e)

        if data:
            with AnalyticsDatabaseUploader() as db:
                result = db.merge_order_utm(data)
            total_inserted += result['inserted']
            total_updated += result['updated']

        current_start = current_end

    logger.info("=" * 70)
    logger.info(f"백필 완료! 총 INSERT {total_inserted}건, UPDATE {total_updated}건")
    logger.info("=" * 70)

    return {"inserted": total_inserted, "updated": total_updated}
