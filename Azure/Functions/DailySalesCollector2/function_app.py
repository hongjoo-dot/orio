"""
Azure Functions - 일일 매출 데이터 수집
Cafe24, Sabangnet 파이프라인 자동 실행
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
# 매일 오후 6시: Cafe24 + Sabangnet 데이터 수집
# ============================================================================
@app.timer_trigger(
    schedule="0 0 9 * * *",  # 매일 오전 9시 (UTC 기준 - 한국시간 오후 6시)
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def daily_sales_collector(timer: func.TimerRequest) -> None:
    """
    매일 오후 6시(한국시간)에 Cafe24, Sabangnet 데이터 수집 실행

    파이프라인:
    1. Cafe24: 10일 롤링 수집 → Blob → DB → OrdersRealtime
    2. Sabangnet: 10일 롤링 수집 → Blob → DB → OrdersRealtime
    """
    logging.info('=' * 80)
    logging.info('일일 매출 데이터 수집 시작')
    logging.info(f'실행 시간: {datetime.utcnow().isoformat()}Z (UTC)')
    logging.info('=' * 80)

    results = {
        'cafe24': None,
        'sabangnet': None,
        'errors': []
    }

    # ---------------------------------------------------------
    # 1. Cafe24 파이프라인
    # ---------------------------------------------------------
    try:
        logging.info('-' * 80)
        logging.info('Cafe24 데이터 수집 시작')
        logging.info('-' * 80)

        from cafe24.pipeline import run_cafe24_pipeline
        cafe24_result = run_cafe24_pipeline()  # DB에서 롤링 일수 자동 로드
        results['cafe24'] = cafe24_result

        logging.info(f'Cafe24 완료: {cafe24_result}')

    except Exception as e:
        error_msg = f'Cafe24 수집 실패: {str(e)}'
        logging.error(error_msg, exc_info=True)
        results['errors'].append(error_msg)

        # Slack 오류 알림
        try:
            from cafe24.slack_notifier import send_slack_notification
            send_slack_notification(f"❌ *[ERROR] Cafe24 수집 실패*\n\n```{str(e)}```")
        except:
            pass

    # ---------------------------------------------------------
    # 2. Sabangnet 파이프라인
    # ---------------------------------------------------------
    try:
        logging.info('-' * 80)
        logging.info('Sabangnet 데이터 수집 시작')
        logging.info('-' * 80)

        from sabangnet.pipeline import run_sabangnet_pipeline
        sabangnet_result = run_sabangnet_pipeline()  # DB에서 롤링 일수 자동 로드
        results['sabangnet'] = sabangnet_result

        logging.info(f'Sabangnet 완료: {sabangnet_result}')

    except Exception as e:
        error_msg = f'Sabangnet 수집 실패: {str(e)}'
        logging.error(error_msg, exc_info=True)
        results['errors'].append(error_msg)

        # Slack 오류 알림
        try:
            from sabangnet.slack_notifier import send_slack_notification
            send_slack_notification(f"❌ *[ERROR] Sabangnet 수집 실패*\n\n```{str(e)}```")
        except:
            pass

    # ---------------------------------------------------------
    # 결과 요약
    # ---------------------------------------------------------
    logging.info('=' * 80)
    logging.info('일일 매출 데이터 수집 완료')
    logging.info(f'Cafe24: {results["cafe24"]}')
    logging.info(f'Sabangnet: {results["sabangnet"]}')

    if results['errors']:
        logging.warning(f'오류 발생: {len(results["errors"])}건')
        for error in results['errors']:
            logging.warning(f'  - {error}')
    else:
        logging.info('모든 파이프라인 정상 완료!')

    logging.info('=' * 80)


# ============================================================================
# 매일 오후 6시(한국시간): Cafe24 고객 데이터 수집
# ============================================================================
@app.timer_trigger(
    schedule="0 10 9 * * *",  # 매일 오전 9시 10분 (UTC) = 한국시간 오후 6시 10분
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def daily_customer_collector(timer: func.TimerRequest) -> None:
    """
    매일 오후 6시(한국시간)에 Cafe24 고객 데이터 전체 수집

    파이프라인:
    1. Cafe24 customersprivacy 수집 (자동 날짜 범위 분할)
    2. Cafe24Customers 테이블 MERGE (member_id 기준)
    3. Slack 알림
    """
    logging.info('=' * 80)
    logging.info('Cafe24 고객 데이터 수집 시작')
    logging.info(f'실행 시간: {datetime.utcnow().isoformat()}Z (UTC)')
    logging.info('=' * 80)

    try:
        from cafe24.main_customers import main as run_customer_pipeline

        # 고객 수집 파이프라인 실행
        run_customer_pipeline()

        logging.info('=' * 80)
        logging.info('Cafe24 고객 데이터 수집 완료!')
        logging.info('=' * 80)

    except Exception as e:
        error_msg = f'Cafe24 고객 수집 실패: {str(e)}'
        logging.error(error_msg, exc_info=True)

        # Slack 오류 알림
        try:
            from cafe24.slack_notifier import send_slack_notification
            send_slack_notification(f"[ERROR] {error_msg}")
        except:
            pass

        raise


# ============================================================================
# 향후 추가 예정 함수 (주석 처리)
# ============================================================================

# @app.timer_trigger(schedule="0 0 3 * * *", arg_name="timer", run_on_startup=False)
# def daily_naver_collector(timer: func.TimerRequest) -> None:
#     """매일 새벽 3시: NaverAPI 수집"""
#     logging.info('NaverAPI 수집 시작')
#     # TODO: NaverAPI 파이프라인 구현
#     pass

# @app.timer_trigger(schedule="0 0 9 * * *", arg_name="timer", run_on_startup=False)
# def daily_report_generator(timer: func.TimerRequest) -> None:
#     """매일 오전 9시: 일일 리포트 생성"""
#     logging.info('일일 리포트 생성 시작')
#     # TODO: 리포트 생성 + Slack 전송
#     pass

# @app.timer_trigger(schedule="0 0 10 * * MON", arg_name="timer", run_on_startup=False)
# def weekly_inventory_check(timer: func.TimerRequest) -> None:
#     """매주 월요일 오전 10시: 주간 재고 체크"""
#     logging.info('주간 재고 체크 시작')
#     # TODO: 재고 체크 로직
#     pass
