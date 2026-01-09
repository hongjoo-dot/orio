"""
네이버 검색광고 API 키워드 검색량 수집 파이프라인 (멀티 브랜드)
자동완성 API를 통한 복합키워드 수집 포함
"""
import logging
import time
from datetime import datetime
from .keyword_manager import KeywordManager
from .api_client import NaverKeywordAPIClient
from .autocomplete_client import NaverAutocompleteClient
from .naver_uploader import NaverAdsUploader


def call_api_with_retry(api_client, keyword, max_retries=3, retry_delay=5):
    """
    API 호출 재시도 로직

    Args:
        api_client: NaverKeywordAPIClient 인스턴스
        keyword: 조회할 키워드
        max_retries: 최대 재시도 횟수 (기본값: 3)
        retry_delay: 재시도 간격 초 (기본값: 5)

    Returns:
        tuple: (result, error_message) - 성공 시 (result, None), 실패 시 (None, error_message)
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            result = api_client.get_keyword_stats(keyword, include_related=False)
            if result:
                return result, None
            else:
                last_error = "Empty response"
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                logging.warning(f"  API 재시도 {attempt + 1}/{max_retries} (키워드: {keyword}): {e}")
                time.sleep(retry_delay)
            continue

    return None, last_error


def run_naver_ads_pipeline():
    """
    네이버 검색광고 API 키워드 검색량 수집 파이프라인 실행

    프로세스:
    1. Keyword 테이블에서 활성 키워드 조회 (CollectNaverAds=1)
    2. 각 키워드에 대해 API 호출
    3. NaverAdsSearchVolume 테이블에 저장
    """
    logging.info("=" * 80)
    logging.info("네이버 검색광고 키워드 검색량 수집 파이프라인 시작")
    logging.info("=" * 80)

    start_time = time.time()
    collection_date = datetime.now().strftime('%Y-%m-%d')

    # 초기화
    keyword_mgr = KeywordManager()
    api_client = NaverKeywordAPIClient()
    autocomplete_client = NaverAutocompleteClient()
    uploader = NaverAdsUploader()

    # 활성 키워드 조회
    keywords = keyword_mgr.get_active_keywords_for_naver_ads()

    if not keywords:
        logging.warning("수집할 활성 키워드가 없습니다")
        return

    logging.info(f"수집 대상: {len(keywords)}개 키워드")

    # 브랜드별 그룹화 (로깅용)
    brands_count = {}
    for kw in keywords:
        brand = kw['brand_name']
        brands_count[brand] = brands_count.get(brand, 0) + 1

    logging.info("브랜드별 키워드 수:")
    for brand, count in brands_count.items():
        logging.info(f"  - {brand}: {count}개")

    # 통계
    total_keywords_collected = 0
    total_records_inserted = 0
    success_count = 0
    failed_count = 0

    # 실패한 키워드 추적
    failed_keywords = []
    # Main 키워드 누락 추적
    missing_main_keywords = []

    # 각 키워드 처리
    for idx, kw_info in enumerate(keywords, 1):
        keyword_id = kw_info['keyword_id']
        base_keyword = kw_info['keyword']  # Keyword 테이블의 기본 키워드
        brand_id = kw_info['brand_id']
        brand_name = kw_info['brand_name']
        category = kw_info['category']
        priority = kw_info['priority']

        # Priority 1만 자동완성 복합키워드 수집
        collect_autocomplete = (priority == 1)

        keyword_type = "복합키워드 수집" if collect_autocomplete else "단일어만"
        logging.info(f"[{idx}/{len(keywords)}] {brand_name} - {base_keyword} (카테고리: {category}, {keyword_type})")

        api_start_time = time.time()

        try:
            # 수집할 키워드 리스트 준비
            keywords_to_collect = [base_keyword]  # 기본 키워드는 항상 수집

            # Priority 1이면 자동완성으로 복합키워드 추가 (최대 2개)
            if collect_autocomplete:
                autocomplete_keywords = autocomplete_client.get_autocomplete_keywords(base_keyword, max_results=2)

                # 기본 키워드와 중복 제거
                for ac_kw in autocomplete_keywords:
                    if ac_kw.lower() != base_keyword.lower() and ac_kw not in keywords_to_collect:
                        keywords_to_collect.append(ac_kw)

                logging.info(f"  자동완성: {len(autocomplete_keywords)}개 발견, {len(keywords_to_collect)-1}개 추가 수집")

            # 각 키워드(기본 + 복합)에 대해 검색량 조회
            total_inserted_for_keyword = 0
            keyword_failed = False
            main_keyword_saved = False  # Main 키워드 저장 여부 추적

            for compound_keyword in keywords_to_collect:
                is_main = (compound_keyword.replace(' ', '').lower() == base_keyword.replace(' ', '').lower())
                # API 호출용 키워드 (공백 제거)
                # 네이버 KeywordTool API는 공백 포함 키워드를 지원하지 않음
                api_keyword = compound_keyword.replace(' ', '')

                # KeywordTool API 호출 (재시도 로직 포함)
                result, error = call_api_with_retry(api_client, api_keyword)

                if result and 'keywordList' in result:
                    keyword_list = result['keywordList']

                    # DB 업로드 시에는 원본 복합키워드 전달 (공백 포함)
                    # uploader에서 CompoundKeyword는 원본 유지, API 응답의 relKeyword와 비교
                    inserted_count = uploader.upload_search_volume(
                        keyword_id=keyword_id,
                        brand_id=brand_id,
                        base_keyword=base_keyword,  # Keyword 테이블의 키워드
                        compound_keyword=compound_keyword,  # 원본 복합키워드 (공백 포함)
                        keyword_list=keyword_list,
                        collection_date=collection_date,
                        hint_only=True  # 항상 hint만 저장 (연관키워드 제외)
                    )

                    total_inserted_for_keyword += inserted_count

                    # Main 키워드 저장 확인
                    if is_main and inserted_count > 0:
                        main_keyword_saved = True
                    elif is_main and inserted_count == 0:
                        logging.warning(f"  [경고] Main 키워드 '{base_keyword}' DB 저장 실패 (검색량 부족 또는 API 응답 불일치)")
                else:
                    # 재시도 후에도 실패
                    logging.error(f"  API 최종 실패 (키워드: {compound_keyword}): {error}")
                    failed_keywords.append({
                        'base_keyword': base_keyword,
                        'compound_keyword': compound_keyword,
                        'brand_name': brand_name,
                        'error': error
                    })
                    keyword_failed = True

                    # Main 키워드 API 실패
                    if is_main:
                        main_keyword_saved = False

                # API Rate Limiting 방지
                time.sleep(1)

            # Main 키워드 누락 체크
            if not main_keyword_saved:
                missing_main_keywords.append({
                    'keyword': base_keyword,
                    'brand_name': brand_name,
                    'keyword_id': keyword_id
                })
                logging.error(f"  [심각] Main 키워드 '{base_keyword}' 최종 누락!")

            # 실행 시간
            execution_time_ms = int((time.time() - api_start_time) * 1000)

            # 통계 업데이트
            total_keywords_collected += len(keywords_to_collect)
            total_records_inserted += total_inserted_for_keyword

            if keyword_failed:
                failed_count += 1
            else:
                success_count += 1

            logging.info(f"  성공: {len(keywords_to_collect)}개 복합키워드, {total_inserted_for_keyword}개 레코드 업로드 ({execution_time_ms}ms)")

        except Exception as e:
            failed_count += 1
            failed_keywords.append({
                'base_keyword': base_keyword,
                'compound_keyword': base_keyword,
                'brand_name': brand_name,
                'error': str(e)
            })
            logging.error(f"  에러: {e}")

        # Rate limiting 방지 (키워드 간 간격)
        if idx < len(keywords):
            time.sleep(1)

    # 총 실행 시간
    total_time = time.time() - start_time

    # 최종 결과 로그
    logging.info("=" * 80)
    logging.info("파이프라인 완료")
    logging.info("=" * 80)
    logging.info(f"처리 키워드: {len(keywords)}개")
    logging.info(f"성공: {success_count}개")
    logging.info(f"실패: {failed_count}개")
    logging.info(f"수집된 총 키워드: {total_keywords_collected}개")
    logging.info(f"DB 삽입 레코드: {total_records_inserted}개")
    logging.info(f"총 실행 시간: {total_time:.2f}초")

    if missing_main_keywords:
        logging.error(f"[심각] Main 키워드 누락 목록:")
        for mk in missing_main_keywords:
            logging.error(f"  - {mk['brand_name']}: {mk['keyword']}")

    if failed_keywords:
        logging.warning(f"API 실패 키워드 목록:")
        for fk in failed_keywords:
            logging.warning(f"  - {fk['brand_name']}: {fk['compound_keyword']} ({fk['error']})")

    logging.info("=" * 80)

    return {
        "success": failed_count == 0 and len(missing_main_keywords) == 0,
        "total_keywords": len(keywords),
        "inserted_records": total_records_inserted,
        "failed_count": failed_count,
        "failed_keywords": failed_keywords,
        "missing_main_keywords": missing_main_keywords
    }
