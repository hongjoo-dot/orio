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
    1. Cafe24: N일 롤링 수집 → Blob → DB → OrdersRealtime
    2. Sabangnet: N일 롤링 수집 → Blob → DB → OrdersRealtime
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
# 매일 오후 6시 5분(한국시간): Frog Cafe24 주문 데이터 수집
# ============================================================================
@app.timer_trigger(
    schedule="0 5 9 * * *",  # 매일 오전 9시 5분 (UTC) = 한국시간 오후 6시 5분
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def daily_frog_cafe24_collector(timer: func.TimerRequest) -> None:
    """
    매일 오후 6시 5분(한국시간)에 Frog Cafe24 주문 데이터 수집 실행

    파이프라인:
    1. Frog Cafe24: N일 롤링 수집 → Blob → DB → OrdersRealtime
    """
    logging.info('=' * 80)
    logging.info('Frog Cafe24 주문 데이터 수집 시작')
    logging.info(f'실행 시간: {datetime.utcnow().isoformat()}Z (UTC)')
    logging.info('=' * 80)

    try:
        from frog_cafe24.pipeline import run_frog_cafe24_pipeline
        result = run_frog_cafe24_pipeline()

        logging.info(f'Frog Cafe24 완료: {result}')

    except Exception as e:
        error_msg = f'Frog Cafe24 수집 실패: {str(e)}'
        logging.error(error_msg, exc_info=True)

        try:
            from frog_cafe24.slack_notifier import send_slack_notification
            send_slack_notification(f"[ERROR] *Frog Cafe24 수집 실패*\n\n```{str(e)}```")
        except:
            pass

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
# 매일 오후 6시 15분(한국시간): Frog Cafe24 고객 데이터 수집
# ============================================================================
@app.timer_trigger(
    schedule="0 15 9 * * *",  # 매일 오전 9시 15분 (UTC) = 한국시간 오후 6시 15분
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def daily_frog_customer_collector(timer: func.TimerRequest) -> None:
    """
    매일 오후 6시 15분(한국시간)에 Frog Cafe24 고객 데이터 전체 수집

    파이프라인:
    1. Frog Cafe24 customersprivacy 수집
    2. FrogCafe24Customers 테이블 MERGE
    3. Slack 알림
    """
    logging.info('=' * 80)
    logging.info('Frog Cafe24 고객 데이터 수집 시작')
    logging.info(f'실행 시간: {datetime.utcnow().isoformat()}Z (UTC)')
    logging.info('=' * 80)

    try:
        from frog_cafe24.main_customers import main as run_frog_customer_pipeline
        run_frog_customer_pipeline()

        logging.info('=' * 80)
        logging.info('Frog Cafe24 고객 데이터 수집 완료!')
        logging.info('=' * 80)

    except Exception as e:
        error_msg = f'Frog Cafe24 고객 수집 실패: {str(e)}'
        logging.error(error_msg, exc_info=True)

        try:
            from frog_cafe24.slack_notifier import send_slack_notification
            send_slack_notification(f"[ERROR] {error_msg}")
        except:
            pass

        raise


# ============================================================================
# 매일 오후 6시 20분(한국시간): Cafe24 Analytics 유입경로 수집
# ============================================================================
@app.timer_trigger(
    schedule="0 20 9 * * *",  # 매일 오전 9시 20분 (UTC) = 한국시간 오후 6시 20분
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def daily_analytics_collector(timer: func.TimerRequest) -> None:
    """
    매��� 오후 6시 20분(��국시간)에 Cafe24 주문별 UTM 유입경로 수집

    파이프라인:
    1. Analytics API /sales/orderdetails 호출 (주문별 UTM 로우데이터)
    2. Cafe24OrderUTM 테이블 MERGE
    3. Slack 알림
    """
    logging.info('=' * 80)
    logging.info('Cafe24 주문별 UTM 수집 시작')
    logging.info(f'실행 시간: {datetime.utcnow().isoformat()}Z (UTC)')
    logging.info('=' * 80)

    try:
        from cafe24_analytics.pipeline import run_analytics_pipeline
        result = run_analytics_pipeline()

        logging.info(f'Cafe24 UTM 수집 완료: {result}')

    except Exception as e:
        error_msg = f'Cafe24 UTM 수집 실패: {str(e)}'
        logging.error(error_msg, exc_info=True)

        try:
            from cafe24.slack_notifier import send_slack_notification
            send_slack_notification(f"❌ *[ERROR] Cafe24 UTM 수집 실패*\n\n```{str(e)}```")
        except:
            pass

    logging.info('=' * 80)


# ============================================================================
# UTM 백필용 HTTP Trigger (일회성 사용 후 제거)
# ============================================================================
@app.route(route="backfill-utm", auth_level=func.AuthLevel.FUNCTION)
def backfill_utm(req: func.HttpRequest) -> func.HttpResponse:
    """
    UTM 과거 데이터 백필 (HTTP 트리거)
    호출: POST /api/backfill-utm?start_date=2024-01-01&end_date=2026-04-08
    """
    start_date = req.params.get('start_date', '2024-01-01')
    end_date = req.params.get('end_date', datetime.utcnow().strftime('%Y-%m-%d'))

    logging.info(f'UTM 백필 시작: {start_date} ~ {end_date}')

    try:
        from cafe24_analytics.main import backfill
        result = backfill(start_date=start_date, end_date=end_date, chunk_days=30)

        msg = f"백필 완료: INSERT {result['inserted']}건, UPDATE {result['updated']}건"
        logging.info(msg)
        return func.HttpResponse(msg, status_code=200)

    except Exception as e:
        error_msg = f'백필 실패: {str(e)}'
        logging.error(error_msg, exc_info=True)
        return func.HttpResponse(error_msg, status_code=500)


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
