"""
광고 데이터 Backfill 스크립트
날짜 범위를 지정하여 Meta + Naver 광고 데이터를 수집
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# 환경변수 설정 (로컬 실행용)
os.environ['DB_SERVER'] = 'oriodatabase.database.windows.net'
os.environ['DB_DATABASE'] = 'oriodatabase'
os.environ['DB_USERNAME'] = 'oriodatabase'
os.environ['DB_PASSWORD'] = 'orio2025!@'
os.environ['DB_DRIVER'] = '{ODBC Driver 17 for SQL Server}'

# 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

import pandas as pd
from shared.system_config import get_config
from shared.meta.auth import MetaAPIAuth
from shared.meta.data_fetcher import MetaDataFetcher
from shared.meta.db_uploader import MetaDBUploader
from shared.meta.pipeline import flatten_insights_data, flatten_breakdown_data
from shared.naver.data_fetcher import NaverADReportFetcher
from shared.naver.name_mapper import NaverNameMapper
from shared.naver.db_uploader import NaverDBUploader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_date_range(start_date: str, end_date: str) -> list:
    """날짜 범위 생성"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)

    return dates


def backfill_meta(dates: list):
    """Meta 광고 데이터 Backfill"""
    print("\n" + "=" * 60)
    print("META ADS BACKFILL 시작")
    print("=" * 60)

    try:
        config = get_config()
        usd_to_krw = int(config.get('Common', 'USD_TO_KRW_RATE', 1400))
        print(f"[CONFIG] 환율: USD 1 = KRW {usd_to_krw}")

        import json
        ad_accounts_json = config.get('MetaAdAPI', 'AD_ACCOUNTS')
        if ad_accounts_json:
            ad_accounts = json.loads(ad_accounts_json)
            print(f"[CONFIG] 광고 계정: {len(ad_accounts)}개")
        else:
            print("[ERROR] Meta 광고 계정 정보가 없습니다.")
            return

        # 인증
        auth = MetaAPIAuth()
        auth.refresh_long_lived_token()
        fetcher = MetaDataFetcher(auth.get_current_token())
        uploader = MetaDBUploader()

        total_daily = 0
        total_breakdown = 0

        for date in dates:
            print(f"\n>>> 날짜: {date} 처리 중...")
            time_range = {'since': date, 'until': date}

            # 1. 기본 성과 데이터
            all_daily_df = []
            for account in ad_accounts:
                print(f"   [Daily] 계정: {account['name']}")

                creatives = fetcher.fetch_ad_creatives(account['id'])

                fields = [
                    'date_start', 'campaign_id', 'campaign_name', 'adset_id', 'adset_name', 'ad_id', 'ad_name',
                    'impressions', 'reach', 'frequency', 'clicks', 'unique_clicks', 'spend', 'ctr', 'unique_ctr',
                    'cpm', 'cpc', 'actions', 'action_values', 'outbound_clicks',
                    'inline_link_clicks', 'inline_link_click_ctr', 'cost_per_inline_link_click',
                    'quality_ranking', 'engagement_rate_ranking', 'conversion_rate_ranking'
                ]
                raw_data = fetcher.fetch_insights_raw(account['id'], fields, time_range=time_range)

                if raw_data:
                    df = flatten_insights_data(raw_data, creatives, account['name'], usd_to_krw)
                    all_daily_df.append(df)
                    print(f"      -> {len(df)}건")

            if all_daily_df:
                combined_daily = pd.concat(all_daily_df)
                uploader.upload_daily_data(combined_daily)
                total_daily += len(combined_daily)
                print(f"   [Daily] DB 업로드 완료: {len(combined_daily)}건")

            # 2. Breakdown 데이터
            breakdowns_config = {
                'age_gender': ['age', 'gender'],
                'publisher_platform': ['publisher_platform']
            }

            for b_type, b_fields in breakdowns_config.items():
                all_breakdown_df = []
                for account in ad_accounts:
                    print(f"   [{b_type}] 계정: {account['name']}")

                    fields = [
                        'date_start', 'campaign_id', 'campaign_name', 'adset_id', 'adset_name', 'ad_id', 'ad_name',
                        'impressions', 'clicks', 'spend', 'reach', 'actions', 'action_values', 'ctr', 'cpm', 'cpc',
                        'outbound_clicks'
                    ]
                    raw_data = fetcher.fetch_insights_raw(
                        account['id'], fields, time_range=time_range, breakdowns=b_fields
                    )

                    if raw_data:
                        df = flatten_breakdown_data(raw_data, b_type, account['name'], usd_to_krw)
                        all_breakdown_df.append(df)

                if all_breakdown_df:
                    combined_breakdown = pd.concat(all_breakdown_df)
                    uploader.upload_breakdown_data(combined_breakdown)
                    total_breakdown += len(combined_breakdown)

        print(f"\n[META 완료] Daily: {total_daily}건, Breakdown: {total_breakdown}건")
        return {'daily': total_daily, 'breakdown': total_breakdown}

    except Exception as e:
        print(f"[META ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


def backfill_naver(dates: list):
    """Naver 광고 데이터 Backfill"""
    print("\n" + "=" * 60)
    print("NAVER ADS BACKFILL 시작")
    print("=" * 60)

    try:
        config = get_config()
        filter_enabled_only = config.get('NaverAdAPI', 'FILTER_ENABLED_ONLY', 'True')
        filter_enabled_only = str(filter_enabled_only).lower() in ('true', '1', 'yes')

        fetcher = NaverADReportFetcher()
        name_mapper = NaverNameMapper()
        uploader = NaverDBUploader()

        # 이름 매핑 구축
        print("[INFO] 이름 매핑 테이블 구축 중...")
        name_mapper.build_all_mappings()

        total_count = 0

        for date in dates:
            print(f"\n>>> 날짜: {date} 처리 중...")

            raw_data = fetcher.fetch_ad_report_data(date)
            if not raw_data:
                print(f"   [WARNING] {date} 데이터 없음")
                continue

            rows = []
            filtered_count = 0

            for item in raw_data:
                campaign_id = item['CampaignID']
                campaign_name = name_mapper.get_name('campaign', campaign_id)
                campaign_status = name_mapper.get_campaign_status(campaign_id)

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
                print(f"   [WARNING] 필터링 후 데이터 없음")
                continue

            df = pd.DataFrame(rows)
            print(f"   [OK] {len(df)}건 (필터링: {filtered_count}건)")

            uploader.upload_data(df)
            total_count += len(df)

        print(f"\n[NAVER 완료] 총 {total_count}건")
        return {'count': total_count}

    except Exception as e:
        print(f"[NAVER ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """메인 실행"""
    # Backfill 날짜 범위 설정
    START_DATE = '2025-12-30'
    END_DATE = '2026-01-01'

    print("=" * 60)
    print(f"광고 데이터 BACKFILL")
    print(f"기간: {START_DATE} ~ {END_DATE}")
    print("=" * 60)

    dates = get_date_range(START_DATE, END_DATE)
    print(f"대상 날짜: {dates}")

    # Meta Backfill
    meta_result = backfill_meta(dates)

    # Naver Backfill
    naver_result = backfill_naver(dates)

    # 결과 요약
    print("\n" + "=" * 60)
    print("BACKFILL 완료")
    print("=" * 60)
    if meta_result:
        print(f"Meta: Daily {meta_result['daily']}건, Breakdown {meta_result['breakdown']}건")
    if naver_result:
        print(f"Naver: {naver_result['count']}건")


if __name__ == '__main__':
    main()
