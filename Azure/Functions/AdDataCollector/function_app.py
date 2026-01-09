import azure.functions as func
import logging
import sys
import os
from datetime import datetime

# 공통 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

app = func.FunctionApp()

# ============================================================================
# Warm-up Function: 메인 수집 5분 전 실행하여 앱을 깨움
# ============================================================================
@app.timer_trigger(
    schedule="0 15 0 * * *",  # 00:15 UTC = 09:15 KST (메인 수집 5분 전)
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def warmup_ad_collector(timer: func.TimerRequest) -> None:
    """
    메인 수집기 실행 5분 전에 앱을 warm-up
    Cold Start로 인한 스케줄 실행 실패 방지
    """
    logging.info('=' * 80)
    logging.info('✓ Warmup completed - Main collector will run in 5 minutes')
    logging.info(f'Next scheduled run: 09:20 KST (00:20 UTC)')
    logging.info('=' * 80)


# ============================================================================
# Main Collector: Meta + Naver 광고 데이터 수집
# ============================================================================
@app.timer_trigger(
    schedule="0 20 0 * * *",  # 00:20 UTC = 09:20 KST
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def daily_ad_data_collector(timer: func.TimerRequest) -> None:
    """
    매일 오전 9시 20분 (KST) = 00:20 UTC
    Meta + Naver 광고 데이터 수집 및 Azure DB 업로드
    """
    from shared.slack_notifier import (
        send_meta_notification, send_naver_notification,
        format_meta_result, format_naver_result
    )

    logging.info('=' * 80)
    logging.info(f'광고 데이터 수집 시작: {datetime.utcnow().isoformat()}Z')
    logging.info('=' * 80)

    # 1. Meta Ads 수집
    meta_result = {'success': False, 'daily_count': 0, 'breakdown_count': 0, 'error': None}
    try:
        logging.info('[META] 수집 시작...')
        from shared.meta.pipeline import run_meta_pipeline
        result = run_meta_pipeline()
        meta_result['success'] = True
        meta_result['daily_count'] = result.get('daily_count', 0) if result else 0
        meta_result['breakdown_count'] = result.get('breakdown_count', 0) if result else 0
        logging.info('[META] 완료')
    except Exception as e:
        error_msg = str(e)
        logging.error(f'[META] 수집 실패: {error_msg}', exc_info=True)
        meta_result['error'] = error_msg

    # Meta 결과 알림
    send_meta_notification(format_meta_result(meta_result))

    # 2. Naver Ads 수집
    naver_result = {'success': False, 'count': 0, 'error': None}
    try:
        logging.info('[NAVER] 수집 시작...')
        from shared.naver.pipeline import run_naver_pipeline
        result = run_naver_pipeline()
        naver_result['success'] = True
        naver_result['count'] = result.get('count', 0) if result else 0
        logging.info('[NAVER] 완료')
    except Exception as e:
        error_msg = str(e)
        logging.error(f'[NAVER] 수집 실패: {error_msg}', exc_info=True)
        naver_result['error'] = error_msg

    # Naver 결과 알림
    send_naver_notification(format_naver_result(naver_result))

    logging.info('=' * 80)
    logging.info('광고 데이터 수집 종료')
    logging.info('=' * 80)
