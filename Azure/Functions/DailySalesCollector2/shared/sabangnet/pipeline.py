"""
Sabangnet 전체 파이프라인 실행 모듈
수집 → Blob → DB → OrdersRealtime
"""
import logging
import sys
import os

# 공통 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from system_config import get_config

logger = logging.getLogger(__name__)


def run_sabangnet_pipeline(days: int = None) -> dict:
    """
    Sabangnet 전체 파이프라인 실행

    Args:
        days: 수집 기간 (일) - None이면 DB 설정에서 로드

    Returns:
        dict: 실행 결과
            {
                'collected': 수집 건수,
                'detail_inserted': Detail INSERT 건수,
                'detail_updated': Detail UPDATE 건수,
                'orders_inserted': Orders INSERT 건수,
                'orders_updated': Orders UPDATE 건수,
                'realtime_uploaded': OrdersRealtime 업로드 건수,
                'mapping_failures': {
                    'single': 단품 매핑 실패,
                    'bom': BOM 매핑 실패
                },
                'blob_filename': Blob 파일명
            }
    """
    # DB에서 롤링 일수 로드 (파라미터가 없을 경우)
    if days is None:
        config = get_config()
        days = config.get('Sabangnet', 'ROLLING_DAYS', 10)
        logger.info(f'DB에서 롤링 일수 로드: {days}일')

    logger.info(f'Sabangnet 파이프라인 시작 (최근 {days}일)')

    result = {
        'collected': 0,
        'detail_inserted': 0,
        'detail_updated': 0,
        'orders_inserted': 0,
        'orders_updated': 0,
        'realtime_uploaded': 0,
        'mapping_failures': {'single': 0, 'bom': 0},
        'blob_filename': None
    }

    try:
        # ============================================================
        # 1. 데이터 수집 (main.py 로직)
        # ============================================================
        logger.info('Step 1: 데이터 수집 시작')

        from .main import SabangnetDataCollector

        collector = SabangnetDataCollector()
        collection_result = collector.collect_orders(days=days)

        result['collected'] = collection_result.get('order_count', 0)
        result['blob_filename'] = collection_result.get('blob_filename')

        logger.info(f'수집 완료: {result["collected"]}건, Blob: {result["blob_filename"]}')

        # ============================================================
        # 2. DB 업로드 (upload_to_db.py 로직)
        # ============================================================
        logger.info('Step 2: DB 업로드 시작')

        from .upload_to_db import SabangnetUploader
        from .azure_blob import AzureBlobManager

        blob_manager = AzureBlobManager()

        # 최신 JSON 파일 다운로드
        blobs = blob_manager.list_blobs(prefix='orders_')
        if not blobs:
            raise Exception("Blob에 주문 데이터가 없습니다.")

        latest_blob = max(blobs, key=lambda x: x['last_modified'])
        logger.info(f'최신 JSON 파일: {latest_blob["name"]}')

        json_data = blob_manager.download_json(latest_blob['name'])

        if not json_data:
            raise Exception("JSON 다운로드 실패")

        # DB 업로드
        uploader = SabangnetUploader()
        uploader.load_metadata()

        # upload_json은 내부적으로 슬랙 알림도 전송함
        # 반환값이 없으므로 로그로 확인
        uploader.upload_json(json_data, blob_filename=latest_blob['name'])

        logger.info('DB 업로드 완료')

        # NOTE: upload_to_db.py는 현재 upload_stats를 반환하지 않음
        # 필요하면 나중에 리팩토링하여 반환하도록 수정 가능

        # ============================================================
        # 3. OrdersRealtime 업로드 (upload_to_realtime.py 로직)
        # ============================================================
        logger.info('Step 3: OrdersRealtime 업로드 시작')

        from .upload_to_realtime import OrdersRealtimeUploader

        with OrdersRealtimeUploader() as realtime_uploader:
            realtime_result = realtime_uploader.merge_to_orders_realtime()
            result['realtime_uploaded'] = realtime_result.get('rows_affected', 0)

        logger.info(f'OrdersRealtime 업로드 완료: {result["realtime_uploaded"]}건')

        # ============================================================
        # 완료
        # ============================================================
        logger.info(f'Sabangnet 파이프라인 완료: {result}')
        return result

    except Exception as e:
        logger.error(f'Sabangnet 파이프라인 오류: {str(e)}', exc_info=True)
        raise
