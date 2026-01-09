"""
Cafe24 고객 데이터 수집 파이프라인
수집 → DB(Cafe24Customers) → Slack (단순화 버전)
"""
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from .customer_collector import Cafe24CustomerCollector
from .upload_customers_to_db import CustomerDatabaseUploader
from .slack_notifier import send_slack_notification, format_customer_result


def main():
    """메인 실행 함수 (전체 수집 후 배치 업로드)"""
    logging.info("=" * 70)
    logging.info(f"Cafe24 고객 데이터 수집 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 70)

    # 환경변수 로드
    load_dotenv()

    try:
        # Step 1: 전체 고객 데이터 수집
        collector = Cafe24CustomerCollector()
        all_customers = collector.collect_all_customers()

        if not all_customers:
            logging.warning("수집된 고객 데이터 없음")
            return

        total_collected = len(all_customers)
        logging.info(f"API 수집 완료: {total_collected}명")

        # Step 2: 배치로 DB 업로드 (타임아웃 방지)
        batch_size = 7000  # 7000명씩 처리
        total_inserted = 0
        total_updated = 0

        total_batches = (total_collected + batch_size - 1) // batch_size
        logging.info(f"DB 업로드 시작: {total_batches}개 배치로 분할")

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_collected)
            batch_customers = all_customers[start_idx:end_idx]

            logging.info(f"[배치 {batch_num + 1}/{total_batches}] {len(batch_customers)}명 업로드 중...")

            # 배치별 DB 연결 생성 및 업로드
            with CustomerDatabaseUploader() as db_uploader:
                result = db_uploader.merge_customers(batch_customers)

            total_inserted += result['inserted']
            total_updated += result['updated']

            logging.info(f"  완료: INSERT {result['inserted']}건, UPDATE {result['updated']}건")

        # Step 3: 최종 결과
        logging.info("=" * 70)
        logging.info("Cafe24 고객 데이터 처리 완료!")
        logging.info(f"  수집: {total_collected}명")
        logging.info(f"  INSERT: {total_inserted}건")
        logging.info(f"  UPDATE: {total_updated}건")
        logging.info(f"  총 처리: {total_inserted + total_updated}건")
        logging.info("=" * 70)

        # Step 4: Slack 알림 전송
        result = {
            'inserted': total_inserted,
            'updated': total_updated,
            'total': total_inserted + total_updated
        }
        slack_message = format_customer_result(result, total_collected)
        send_slack_notification(slack_message)

    except Exception as e:
        logging.error(f"처리 중 오류 발생: {e}", exc_info=True)

        # Slack 오류 알림
        error_message = f"[ERROR] Cafe24 고객 데이터 수집 실패\n오류: {str(e)}"
        send_slack_notification(error_message)
        raise




if __name__ == "__main__":
    main()
