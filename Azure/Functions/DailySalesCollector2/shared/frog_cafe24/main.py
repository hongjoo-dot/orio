"""
Frog Cafe24 주문 자동 수집 파이프라인
N일 롤링 수집 → Blob → DB(Orders/Detail) → OrdersRealtime
"""

import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from .collector import Cafe24OrderCollector
from .upload_to_blob import BlobUploader
from .upload_to_db import DatabaseUploader
from .upload_to_realtime import OrdersRealtimeUploader
from .slack_notifier import send_slack_notification, format_cafe24_result

logger = logging.getLogger(__name__)


def main(days: int = 10):
    """메인 실행 함수"""
    logger.info("=" * 70)
    logger.info(f"Frog Cafe24 주문 수집 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    load_dotenv()

    rolling_days = days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=rolling_days)).strftime("%Y-%m-%d")
    logger.info(f"수집 기간: {start_date} ~ {end_date} ({rolling_days}일 롤링)")

    try:
        # Step 1: 주문 수집
        logger.info(f"Step 1: Frog Cafe24 주문 수집 ({rolling_days}일 롤링)")
        collector = Cafe24OrderCollector()
        orders = collector.get_rolling_orders(days=rolling_days)

        if not orders:
            logger.info("수집된 주문이 없습니다.")
            return

        logger.info(f"수집 완료: {len(orders)}건")

        # Step 2: Blob 업로드
        logger.info("Step 2: Azure Blob Storage 업로드")
        blob_uploader = BlobUploader()
        blob_url = blob_uploader.upload_shipped_orders(orders, end_date)

        # Step 3: DB 업로드
        logger.info("Step 3: FrogCafe24Orders/Detail 업로드 (MERGE)")
        with DatabaseUploader() as db_uploader:
            result = db_uploader.merge_orders(orders)

        # Step 4: OrdersRealtime 업로드
        logger.info("Step 4: OrdersRealtime 업로드 (MERGE)")
        with OrdersRealtimeUploader() as realtime_uploader:
            realtime_result = realtime_uploader.merge_to_orders_realtime()

        # 최종 결과
        logger.info("=" * 70)
        logger.info("Frog Cafe24 주문 처리 완료!")
        logger.info("=" * 70)
        logger.info(f"수집 기간: {start_date} ~ {end_date}")
        logger.info(f"수집 건수: {len(orders)}건")
        logger.info(f"Blob URL: {blob_url}")
        logger.info(f"FrogCafe24Orders: INSERT {result['inserted_orders']}건, UPDATE {result['updated_orders']}건")
        logger.info(f"FrogCafe24OrdersDetail: INSERT {result['inserted_details']}건, UPDATE {result['updated_details']}건")
        logger.info(f"ProductID 매핑: {result['product_id_mapped']}/{result['total_items']}건 성공")
        logger.info(f"OrdersRealtime: {realtime_result['rows_affected']}건 처리")

        if result['product_id_not_mapped'] > 0:
            logger.warning(f"{result['product_id_not_mapped']}건 매핑 실패")

        logger.info("=" * 70)

        # Slack 알림 전송
        slack_message = format_cafe24_result(result, f"{start_date} ~ {end_date}")
        slack_message += f"\n*OrdersRealtime*: {realtime_result['rows_affected']}건 처리"
        send_slack_notification(slack_message)

    except Exception as e:
        logger.error(f"처리 중 오류 발생: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
