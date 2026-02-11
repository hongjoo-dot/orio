"""
Azure Functions - USD/KRW 환율 자동 수집
한국은행 Open API → SystemConfig 테이블 업데이트
"""
import azure.functions as func
import logging
import sys
import os
from datetime import datetime

# 공통 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

app = func.FunctionApp()


@app.timer_trigger(
    schedule="0 0 1 * * *",  # 매일 01:00 UTC = 10:00 KST
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def exchange_rate_collector(timer: func.TimerRequest) -> None:
    """
    매일 10:00 KST에 USD/KRW 환율 수집

    1. SystemConfig에서 한국은행 API 키 조회
    2. 한국은행 Open API로 당일 매매기준율 조회
    3. 데이터 있으면 SystemConfig.USD_TO_KRW_RATE 업데이트 + 이력 기록
    4. 주말/공휴일은 데이터 없으므로 skip
    """
    logging.info('=' * 60)
    logging.info('USD/KRW 환율 수집 시작')
    logging.info(f'실행 시간: {datetime.utcnow().isoformat()}Z (UTC)')
    logging.info('=' * 60)

    try:
        from exchange_rate_service import collect_exchange_rate

        result = collect_exchange_rate()

        logging.info(f'결과: {result}')

        if result["status"] == "updated":
            logging.info(f'환율 업데이트 완료: {result["rate"]} (원본: {result["rate_raw"]})')
        elif result["status"] == "unchanged":
            logging.info(f'환율 변경 없음: {result["rate"]}')
        elif result["status"] == "skipped":
            logging.info(f'수집 생략: {result["reason"]}')

    except Exception as e:
        logging.error(f'환율 수집 실패: {str(e)}', exc_info=True)
        raise

    logging.info('=' * 60)
    logging.info('USD/KRW 환율 수집 종료')
    logging.info('=' * 60)
