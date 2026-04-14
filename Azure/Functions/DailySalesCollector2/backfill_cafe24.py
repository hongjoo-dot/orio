"""
스크럽대디 Cafe24 payment_amount backfill 스크립트
- 7일 단위 청크 처리
- 구간별 재시도 (최대 3회)
- 진행 상태 파일로 중단/재개 지원
- DB 연결/토큰 문제 대응
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(r'C:\Python\WebApp_v2_admin\.env')
os.environ['DB_DRIVER'] = '{ODBC Driver 17 for SQL Server}'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('backfill_cafe24.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

START_DATE = datetime(2024, 7, 1)
CHUNK_DAYS = 7
MAX_RETRIES = 3
STATE_FILE = 'backfill_cafe24_state.json'


def load_state():
    """진행 상태 로드"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'completed_chunks': [], 'failed_chunks': []}


def save_state(state):
    """진행 상태 저장"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def reset_config_cache():
    """SystemConfig 싱글턴 캐시 초기화 (토큰 갱신 반영)"""
    import system_config
    system_config._config_instance = None


def process_chunk(start_str, end_str):
    """
    한 구간 처리: API 수집 → DB MERGE
    실패 시 예외 발생 (호출자가 재시도)
    """
    # 매 시도마다 토큰 캐시 초기화 + 인스턴스 재생성
    reset_config_cache()

    # import를 함수 안에서 해야 fresh config 사용
    from cafe24.collector import Cafe24OrderCollector
    from cafe24.upload_to_db import DatabaseUploader

    collector = Cafe24OrderCollector()
    orders = collector.get_orders_by_date_range(start_str, end_str)

    if not orders:
        return {'collected': 0, 'merged': True}

    with DatabaseUploader() as db:
        result = db.merge_orders(orders)

    return {
        'collected': len(orders),
        'inserted_orders': result.get('inserted_orders', 0),
        'updated_orders': result.get('updated_orders', 0),
        'inserted_details': result.get('inserted_details', 0),
        'updated_details': result.get('updated_details', 0),
        'merged': True
    }


def backfill():
    state = load_state()
    completed = set(state['completed_chunks'])

    current_start = START_DATE
    end = datetime.now()
    chunk_num = 0
    total_chunks = ((end - START_DATE).days // CHUNK_DAYS) + 1

    logger.info(f"=== Backfill 시작: {START_DATE.date()} ~ {end.date()} ===")
    logger.info(f"청크 크기: {CHUNK_DAYS}일, 총 {total_chunks}개 구간")
    logger.info(f"이미 완료된 구간: {len(completed)}개 (건너뜀)")

    while current_start < end:
        chunk_num += 1
        current_end = min(current_start + timedelta(days=CHUNK_DAYS), end)
        start_str = current_start.strftime("%Y-%m-%d")
        end_str = current_end.strftime("%Y-%m-%d")
        chunk_key = f"{start_str}_{end_str}"

        # 이미 완료된 구간 건너뛰기
        if chunk_key in completed:
            logger.info(f"[{chunk_num}/{total_chunks}] {start_str} ~ {end_str} - 이미 완료, 건너뜀")
            current_start = current_end
            continue

        logger.info(f"\n[{chunk_num}/{total_chunks}] {start_str} ~ {end_str}")

        # 재시도 루프
        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = process_chunk(start_str, end_str)
                if result['collected'] == 0:
                    logger.info(f"  주문 없음")
                else:
                    logger.info(
                        f"  성공: 수집 {result['collected']}건, "
                        f"Orders I/U {result.get('inserted_orders', 0)}/{result.get('updated_orders', 0)}, "
                        f"Details I/U {result.get('inserted_details', 0)}/{result.get('updated_details', 0)}"
                    )
                success = True
                break

            except Exception as e:
                err_msg = str(e)[:300]
                logger.warning(f"  [시도 {attempt}/{MAX_RETRIES}] 실패: {err_msg}")
                if attempt < MAX_RETRIES:
                    wait = 15 * attempt  # 15s → 30s → 45s
                    logger.info(f"  {wait}초 대기 후 재시도...")
                    time.sleep(wait)

        # 결과 기록
        if success:
            state['completed_chunks'].append(chunk_key)
            # failed에 있었다면 제거
            if chunk_key in state['failed_chunks']:
                state['failed_chunks'].remove(chunk_key)
        else:
            logger.error(f"  [FAIL] {chunk_key} 최종 실패, 다음 구간으로")
            if chunk_key not in state['failed_chunks']:
                state['failed_chunks'].append(chunk_key)

        save_state(state)
        current_start = current_end
        time.sleep(1)

    # 전체 완료 후 OrdersRealtime MERGE
    logger.info("\n=== OrdersRealtime MERGE 시작 ===")
    try:
        reset_config_cache()
        from cafe24.upload_to_realtime import OrdersRealtimeUploader
        with OrdersRealtimeUploader() as realtime:
            realtime_result = realtime.merge_to_orders_realtime()
        logger.info(f"OrdersRealtime: {realtime_result['rows_affected']}건 처리")
    except Exception as e:
        logger.error(f"OrdersRealtime MERGE 실패: {e}")

    # 최종 요약
    logger.info("\n=== Backfill 완료 ===")
    logger.info(f"완료 구간: {len(state['completed_chunks'])}개")
    logger.info(f"실패 구간: {len(state['failed_chunks'])}개")
    if state['failed_chunks']:
        logger.warning(f"실패 구간 목록: {state['failed_chunks']}")
        logger.warning("실패 구간은 스크립트 재실행 시 다시 시도됩니다.")


if __name__ == "__main__":
    backfill()
