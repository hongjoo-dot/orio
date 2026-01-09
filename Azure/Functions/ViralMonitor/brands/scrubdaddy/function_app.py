"""
스크럽대디 바이럴 모니터링 - Azure Functions
"""
import azure.functions as func
import logging
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = func.FunctionApp()

@app.timer_trigger(
    schedule="0 0 */3 * * *",  # 3시간마다
    arg_name="myTimer",
    run_on_startup=False
)
def scrubdaddy_monitor(myTimer: func.TimerRequest) -> None:
    """스크럽대디 모니터링 타이머 함수"""
    utc_timestamp = datetime.utcnow().replace(tzinfo=None).isoformat()

    if myTimer.past_due:
        logging.info('타이머가 예정 시간보다 늦게 실행되었습니다')

    logging.info(f'스크럽대디 모니터링 시작: {utc_timestamp}')

    try:
        from scheduler import ScrubdaddyMonitoringScheduler

        scheduler = ScrubdaddyMonitoringScheduler()
        scheduler.run_once()

        logging.info(f'스크럽대디 모니터링 완료: {utc_timestamp}')

    except Exception as e:
        logging.error(f'스크럽대디 모니터링 실행 중 오류 발생: {e}', exc_info=True)
        raise
