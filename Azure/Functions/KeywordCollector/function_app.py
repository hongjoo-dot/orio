import azure.functions as func
import logging
import sys
import os
from datetime import datetime

# 공통 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

app = func.FunctionApp()

@app.timer_trigger(schedule="0 0 5 * * *", arg_name="timer", run_on_startup=False,
              use_monitor=True)
def daily_keyword_collector(timer: func.TimerRequest) -> None:
    """
    매일 오후 2시 (KST) = 05:00 UTC
    네이버 키워드 검색량 수집 및 Azure DB 업로드
    """
    logging.info('=' * 80)
    logging.info(f'키워드 검색량 수집 시작: {datetime.utcnow().isoformat()}Z')
    logging.info('=' * 80)

    try:
        from common.slack_notifier import send_keyword_notification
        
        # 1. 네이버 수집
        from naver_keyword.naver_pipeline import run_naver_ads_pipeline
        naver_result = run_naver_ads_pipeline()
        send_keyword_notification("NaverKeywordAPI", naver_result)

        # 2. 구글 수집 (비활성화 - 토큰 만료)
        # from google_keyword.google_pipeline import run_google_ads_pipeline
        # google_result = run_google_ads_pipeline()
        # send_keyword_notification("GoogleKeywordAPI", google_result)

        logging.info('=' * 80)
        logging.info('키워드 검색량 수집 완료')
        logging.info('=' * 80)

    except Exception as e:
        logging.error(f'키워드 검색량 수집 실패: {e}', exc_info=True)
        try:
            from common.slack_notifier import send_keyword_notification
            send_keyword_notification("NaverKeywordAPI", {"success": False, "error": str(e)})
        except:
            pass
        raise
