"""
사방넷 주문 데이터 수집 메인 프로그램
Request XML 생성 → Blob 업로드 → API 호출 → Response 저장
"""
import logging
import sys
from datetime import datetime
from .config import get_date_range, get_current_timestamp
from .sabangnet_api import SabangnetAPI
from .azure_blob import AzureBlobManager

# 로깅 설정 (Azure Functions: 파일 시스템 읽기 전용이므로 StreamHandler만 사용)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SabangnetDataCollector:
    """사방넷 데이터 수집 통합 클래스"""
    
    def __init__(self):
        """초기화"""
        self.api = SabangnetAPI()
        self.blob_manager = AzureBlobManager()
    
    def collect_orders(self, days: int = 10) -> dict:
        """
        주문 데이터 수집 전체 프로세스
        
        Args:
            days: 수집할 기간 (일)
        
        Returns:
            dict: 수집 결과 정보
        """
        try:
            logger.info("=" * 80)
            logger.info(f"사방넷 주문 데이터 수집 시작 (최근 {days}일)")
            logger.info("=" * 80)
            
            # 1. 날짜 범위 생성
            start_date, end_date = get_date_range(days)
            logger.info(f"수집 기간: {start_date} ~ {end_date}")
            
            # 2. Request XML 생성
            logger.info("Step 1: Request XML 생성 중...")
            request_xml = self.api.create_request_xml(start_date, end_date)
            logger.info(f"Request XML 생성 완료 ({len(request_xml)} bytes)")
            
            # 3. Blob Storage에 Request XML 업로드
            logger.info("Step 2: Request XML을 Blob Storage에 업로드 중...")
            timestamp = get_current_timestamp()
            request_filename = f"request_{timestamp}.xml"
            request_url = self.blob_manager.upload_request_xml(request_xml, request_filename)
            logger.info(f"Request XML 업로드 완료: {request_url}")
            
            # 4. 사방넷 API 호출
            logger.info("Step 3: 사방넷 API 호출 중...")
            logger.info(f"API URL: {request_url}")
            orders_data = self.api.fetch_orders(start_date, end_date, request_url)
            logger.info(f"주문 데이터 수집 완료: {orders_data['header']['total_count']}건")
            
            # 5. Response JSON을 Blob Storage에 저장
            logger.info("Step 4: Response JSON을 Blob Storage에 저장 중...")
            response_filename = f"orders_{timestamp}.json"
            response_url = self.blob_manager.upload_response_json(orders_data, response_filename)
            logger.info(f"Response JSON 저장 완료: {response_url}")
            
            # 6. 결과 반환
            result = {
                'success': True,
                'timestamp': timestamp,
                'start_date': start_date,
                'end_date': end_date,
                'total_orders': orders_data['header']['total_count'],
                'request_url': request_url,
                'response_url': response_url,
                'request_filename': request_filename,
                'response_filename': response_filename,
            }
            
            logger.info("=" * 80)
            logger.info("✅ 주문 데이터 수집 완료!")
            logger.info(f"   - 수집 건수: {result['total_orders']}건")
            logger.info(f"   - Request XML: {result['request_filename']}")
            logger.info(f"   - Response JSON: {result['response_filename']}")
            logger.info("=" * 80)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 주문 데이터 수집 오류: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'timestamp': get_current_timestamp(),
            }


def main():
    """메인 함수"""
    try:
        # 데이터 수집기 생성
        collector = SabangnetDataCollector()
        
        # 5일치 주문 데이터 수집
        result = collector.collect_orders(days=5)
        
        # 결과 출력
        if result['success']:
            print("\n" + "=" * 80)
            print("🎉 수집 결과")
            print("=" * 80)
            print(f"수집 기간: {result['start_date']} ~ {result['end_date']}")
            print(f"수집 건수: {result['total_orders']}건")
            print(f"Request URL: {result['request_url']}")
            print(f"Response URL: {result['response_url']}")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("❌ 수집 실패")
            print("=" * 80)
            print(f"오류: {result['error']}")
            print("=" * 80)
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"프로그램 실행 오류: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
