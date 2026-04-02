"""
Azure Functions - 사방넷 풀필먼트 재고/입고 수집
하루 2회 (11:00 KST, 18:00 KST) 실행
"""
import azure.functions as func
import logging
import sys
import os
from datetime import datetime

# 공통 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

app = func.FunctionApp()


# ============================================================================
# 매일 오후 12시 30분 (KST) = 03:30 UTC: 오전 재고 스냅샷
# ============================================================================
@app.timer_trigger(
    schedule="0 30 3 * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def inventory_collector_am(timer: func.TimerRequest) -> None:
    """
    매일 오전 11시(KST) 재고/입고 수집
    오전 출고 전 재고 스냅샷
    """
    logging.info('=' * 80)
    logging.info('[풀필먼트] AM 재고/입고 수집 시작')
    logging.info(f'실행 시간: {datetime.utcnow().isoformat()}Z (UTC)')
    logging.info('=' * 80)

    try:
        from sabangnet_fulfillment.pipeline import run_inventory_pipeline
        result = run_inventory_pipeline(snapshot_time='AM')
        logging.info(f'[풀필먼트] AM 수집 완료: {result}')

    except Exception as e:
        logging.error(f'[풀필먼트] AM 수집 실패: {str(e)}', exc_info=True)
        try:
            from slack_notifier import send_slack_notification
            send_slack_notification(f"❌ *[풀필먼트] AM 수집 실패*\n\n```{str(e)}```")
        except:
            pass

    logging.info('=' * 80)


# ============================================================================
# 매일 오후 6시 (KST) = 09:00 UTC: 오후 재고 스냅샷
# ============================================================================
@app.timer_trigger(
    schedule="0 0 9 * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def inventory_collector_pm(timer: func.TimerRequest) -> None:
    """
    매일 오후 6시(KST) 재고/입고 수집
    오후 출고 후 재고 스냅샷
    """
    logging.info('=' * 80)
    logging.info('[풀필먼트] PM 재고/입고 수집 시작')
    logging.info(f'실행 시간: {datetime.utcnow().isoformat()}Z (UTC)')
    logging.info('=' * 80)

    try:
        from sabangnet_fulfillment.pipeline import run_inventory_pipeline
        result = run_inventory_pipeline(snapshot_time='PM')
        logging.info(f'[풀필먼트] PM 수집 완료: {result}')

    except Exception as e:
        logging.error(f'[풀필먼트] PM 수집 실패: {str(e)}', exc_info=True)
        try:
            from slack_notifier import send_slack_notification
            send_slack_notification(f"❌ *[풀필먼트] PM 수집 실패*\n\n```{str(e)}```")
        except:
            pass

    logging.info('=' * 80)
