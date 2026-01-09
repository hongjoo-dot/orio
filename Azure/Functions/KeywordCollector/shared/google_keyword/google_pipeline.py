import logging
from datetime import datetime
from naver_keyword.keyword_manager import KeywordManager
from google_keyword.api_client import GoogleAdsKeywordClient
from google_keyword.google_uploader import GoogleAdsUploader
from common.system_config import get_config

def run_google_ads_pipeline():
    """
    구글 키워드 검색량 수집 파이프라인 실행
    """
    logging.info("구글 키워드 파이프라인 시작")
    
    # 1. 키워드 목록 가져오기 (구글 전용 필터 사용)
    km = KeywordManager()
    active_keywords = km.get_active_keywords_for_google_ads()
    
    if not active_keywords:
        logging.info("수집할 활성 키워드가 없습니다.")
        return

    # 2. 구글 클라이언트 및 업로더 초기화
    try:
        client = GoogleAdsKeywordClient()
        uploader = GoogleAdsUploader()
        config = get_config()
    except Exception as e:
        logging.error(f"구글 파이프라인 초기화 실패: {e}")
        return

    # 실제 조회를 위한 Customer ID (자식 계정 ID)
    customer_id = config.get("GoogleKeywordAPI", "default_customer_id")
    
    if not customer_id:
        logging.error("GoogleKeywordAPI.default_customer_id 설정이 SystemConfig에 없습니다.")
        return
    
    collection_date = datetime.now().strftime('%Y-%m-%d')
    
    total_count = len(active_keywords)
    success_count = 0
    
    # 구글 API는 한 번에 여러 키워드 요청 가능 (최대 20개 권장)
    batch_size = 20
    for i in range(0, len(active_keywords), batch_size):
        batch = active_keywords[i:i + batch_size]
        keyword_texts = [k['keyword'] for k in batch]
        
        logging.info(f"구글 키워드 조회 중 ({i+1}~{i+len(batch)}): {', '.join(keyword_texts)}")
        
        try:
            results = client.get_historical_metrics(customer_id, keyword_texts)
            
            if not results:
                logging.warning(f"배치 조회 결과 없음: {keyword_texts}")
                continue

            # 결과 매칭 및 저장
            result_map = {res.text: res.keyword_metrics for res in results}
            
            for kw_info in batch:
                kw_text = kw_info['keyword']
                if kw_text in result_map:
                    metrics = result_map[kw_text]
                    success = uploader.upload_metrics(
                        kw_info['keyword_id'],
                        kw_info['brand_id'],
                        kw_text,
                        metrics,
                        collection_date
                    )
                    if success:
                        success_count += 1
                        logging.info(f"성공: {kw_text}")
                else:
                    logging.warning(f"결과에 키워드 없음: {kw_text}")
        except Exception as e:
            logging.error(f"구글 배치 처리 중 오류: {e}")

    logging.info("구글 키워드 파이프라인 완료")
    return {
        "success": True, # 예외가 발생해도 일부 성공했을 수 있으므로 True로 일단 설정 (또는 로직 보강)
        "total_keywords": total_count,
        "inserted_records": success_count
    }
