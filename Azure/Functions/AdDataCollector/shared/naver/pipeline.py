"""
네이버 검색광고 데이터 수집 파이프라인
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from .data_fetcher import NaverADReportFetcher
from .name_mapper import NaverNameMapper
from .db_uploader import NaverDBUploader
from ..system_config import get_config


def run_naver_pipeline():
    """메인 실행 함수"""
    print("=" * 60)
    print(f"Naver Ads 파이프라인 시작: {datetime.now()}")
    print("=" * 60)

    result = {'count': 0}

    try:
        # 1. 설정 로드
        config = get_config()

        # 활성 캠페인만 수집할지 여부 (기본값: True)
        filter_enabled_only = config.get('NaverAdAPI', 'FILTER_ENABLED_ONLY', 'True')
        filter_enabled_only = str(filter_enabled_only).lower() in ('true', '1', 'yes')

        if filter_enabled_only:
            print("[CONFIG] 활성(ENABLED) 캠페인만 수집")
        else:
            print("[CONFIG] 전체 캠페인 수집 (활성/비활성 무관)")

        # 2. 초기화
        fetcher = NaverADReportFetcher()
        name_mapper = NaverNameMapper()
        uploader = NaverDBUploader()

        # 3. 전날 날짜 계산
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        logging.info(f"[INFO] 수집 대상 날짜: {yesterday} (전날)")

        # 4. 이름 매핑 테이블 구축 (한 번만)
        name_mapper.build_all_mappings()

        # 5. 전날 데이터 수집
        for date in [yesterday]:
            print(f"\n>>> 날짜: {date} 처리 중...")

            # 데이터 수집
            raw_data = fetcher.fetch_ad_report_data(date)
            if not raw_data:
                print(f"   [WARNING] {date} 데이터 없음")
                continue

            # 데이터 변환 및 필터링
            rows = []
            filtered_count = 0

            for item in raw_data:
                campaign_id = item['CampaignID']
                campaign_name = name_mapper.get_name('campaign', campaign_id)
                campaign_status = name_mapper.get_campaign_status(campaign_id)

                # 활성 캠페인만 필터링 (ON + 노출가능 상태)
                if filter_enabled_only and campaign_status != 'ACTIVE':
                    filtered_count += 1
                    continue

                row = {
                    'Date': item['Date'],
                    'CampaignID': item['CampaignID'],
                    'CampaignName': campaign_name,
                    'AdGroupID': item['AdGroupID'],
                    'AdGroupName': name_mapper.get_name('adgroup', item['AdGroupID']),
                    'KeywordID': item['KeywordID'],
                    'Keyword': name_mapper.get_name('keyword', item['KeywordID']),
                    'AdID': item['AdID'],
                    'AdName': name_mapper.get_name('ad', item['AdID']),
                    'Device': item['Device'],
                    'Impressions': item['Impressions'],
                    'Clicks': item['Clicks'],
                    'Conversions': item['Conversions'],
                    'ConversionValue': item['ConversionValue'],
                }
                rows.append(row)

            if not rows:
                print(f"   [WARNING] 필터링 후 데이터 없음 (전체 {len(raw_data)}건 중 비활성 캠페인 {filtered_count}건 제외)")
                continue

            df = pd.DataFrame(rows)
            print(f"   [OK] {len(df)}건 데이터 변환 완료 (필터링: {filtered_count}건)")

            # DB 업로드
            uploader.upload_data(df)
            result['count'] += len(df)

        print("\n[SUCCESS] 모든 작업 완료")
        return result

    except Exception as e:
        print(f"[ERROR] 파이프라인 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise
