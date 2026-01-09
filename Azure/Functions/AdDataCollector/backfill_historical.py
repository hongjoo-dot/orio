"""
과거 광고 데이터 대량 업로드 스크립트
기간: 2025-09-01 ~ 2025-12-23
7일씩 나눠서 수집 (API Rate Limit 방지)
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timedelta

# 현재 디렉토리를 패키지로 인식하도록 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# local.settings.json에서 환경 변수 로드
settings_path = os.path.join(current_dir, 'local.settings.json')
if os.path.exists(settings_path):
    with open(settings_path, 'r') as f:
        settings = json.load(f)
        for key, value in settings.get('Values', {}).items():
            if not key.startswith('COMMENT'):
                os.environ[key] = value
    print("[OK] local.settings.json 환경 변수 로드 완료")

# shared 모듈 직접 import
from shared.meta.auth import MetaAPIAuth
from shared.meta.data_fetcher import MetaDataFetcher
from shared.meta.db_uploader import MetaDBUploader
from shared.naver.data_fetcher import NaverADReportFetcher
from shared.naver.name_mapper import NaverNameMapper
from shared.naver.db_uploader import NaverDBUploader
from shared.system_config import get_config
from shared.meta.pipeline import flatten_insights_data, flatten_breakdown_data
import pandas as pd


def generate_date_ranges(start_date: str, end_date: str, days_per_batch: int = 7):
    """날짜 범위를 N일 단위로 분할"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    ranges = []
    current = start

    while current <= end:
        batch_end = min(current + timedelta(days=days_per_batch - 1), end)
        ranges.append({
            'since': current.strftime('%Y-%m-%d'),
            'until': batch_end.strftime('%Y-%m-%d')
        })
        current = batch_end + timedelta(days=1)

    return ranges


def backfill_meta(date_ranges: list):
    """Meta 광고 데이터 백필"""
    print("\n" + "=" * 60)
    print("META 광고 데이터 백필 시작")
    print("=" * 60)

    config = get_config()
    usd_to_krw = int(config.get('Common', 'USD_TO_KRW_RATE', 1400))

    import json
    ad_accounts_json = config.get('MetaAdAPI', 'AD_ACCOUNTS')
    if not ad_accounts_json:
        print("[ERROR] Meta 광고 계정 정보가 없습니다.")
        return
    ad_accounts = json.loads(ad_accounts_json)

    auth = MetaAPIAuth()
    auth.refresh_long_lived_token()
    fetcher = MetaDataFetcher(auth.get_current_token())
    uploader = MetaDBUploader()

    total_daily = 0
    total_breakdown = 0

    for i, time_range in enumerate(date_ranges):
        print(f"\n[{i+1}/{len(date_ranges)}] {time_range['since']} ~ {time_range['until']}")

        # 크리에이티브는 한 번만 수집
        if i == 0:
            all_creatives = {}
            for account in ad_accounts:
                creatives = fetcher.fetch_ad_creatives(account['id'])
                all_creatives.update(creatives)
            print(f"   크리에이티브 수집 완료: {len(all_creatives)}개")

        # Daily 데이터
        all_daily_df = []
        for account in ad_accounts:
            fields = [
                'date_start', 'campaign_id', 'campaign_name', 'adset_id', 'adset_name',
                'ad_id', 'ad_name', 'impressions', 'reach', 'frequency', 'clicks',
                'unique_clicks', 'spend', 'ctr', 'unique_ctr', 'cpm', 'cpc',
                'actions', 'action_values', 'outbound_clicks',
                'inline_link_clicks', 'inline_link_click_ctr', 'cost_per_inline_link_click',
                'quality_ranking', 'engagement_rate_ranking', 'conversion_rate_ranking'
            ]
            raw_data = fetcher.fetch_insights_raw(
                account['id'], fields,
                time_range=time_range,
                time_increment=1  # 일별 데이터
            )
            if raw_data:
                df = flatten_insights_data(raw_data, all_creatives, account['name'], usd_to_krw)
                all_daily_df.append(df)

        if all_daily_df:
            combined = pd.concat(all_daily_df)
            uploader.upload_daily_data(combined)
            total_daily += len(combined)
            print(f"   Daily: {len(combined)}건 업로드")

        # Breakdown 데이터
        breakdowns_config = {
            'age_gender': ['age', 'gender'],
            'publisher_platform': ['publisher_platform']
        }

        for b_type, b_fields in breakdowns_config.items():
            all_breakdown_df = []
            for account in ad_accounts:
                fields = [
                    'date_start', 'campaign_id', 'campaign_name', 'adset_id', 'adset_name',
                    'ad_id', 'ad_name', 'impressions', 'clicks', 'spend', 'reach',
                    'actions', 'action_values', 'ctr', 'cpm', 'cpc'
                ]
                raw_data = fetcher.fetch_insights_raw(
                    account['id'], fields,
                    time_range=time_range,
                    breakdowns=b_fields,
                    time_increment=1
                )
                if raw_data:
                    df = flatten_breakdown_data(raw_data, b_type, account['name'], usd_to_krw)
                    all_breakdown_df.append(df)

            if all_breakdown_df:
                combined = pd.concat(all_breakdown_df)
                uploader.upload_breakdown_data(combined)
                total_breakdown += len(combined)
                print(f"   {b_type}: {len(combined)}건 업로드")

        # Rate Limit 방지 대기
        if i < len(date_ranges) - 1:
            print("   대기 중 (10초)...")
            time.sleep(10)

    print(f"\n[META 완료] Daily: {total_daily}건, Breakdown: {total_breakdown}건")


def backfill_naver(start_date: str, end_date: str):
    """Naver 광고 데이터 백필 (일별 수집)"""
    print("\n" + "=" * 60)
    print("NAVER 광고 데이터 백필 시작")
    print("=" * 60)

    config = get_config()
    target_campaign_name = config.get('NaverAdAPI', 'TARGET_CAMPAIGN_NAME')

    fetcher = NaverADReportFetcher()
    name_mapper = NaverNameMapper()
    uploader = NaverDBUploader()

    # 이름 매핑 테이블 구축
    print("이름 매핑 테이블 구축 중...")
    name_mapper.build_all_mappings()

    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    total_count = 0
    current = start
    day_num = 0
    total_days = (end - start).days + 1

    while current <= end:
        day_num += 1
        date_str = current.strftime('%Y-%m-%d')
        print(f"\n[{day_num}/{total_days}] {date_str}")

        raw_data = fetcher.fetch_ad_report_data(date_str)

        if not raw_data:
            print("   데이터 없음")
            current += timedelta(days=1)
            continue

        rows = []
        for item in raw_data:
            campaign_name = name_mapper.get_name('campaign', item['CampaignID'])

            # if target_campaign_name and campaign_name != target_campaign_name:
            #     continue

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

        if rows:
            df = pd.DataFrame(rows)
            uploader.upload_data(df)
            total_count += len(df)
            print(f"   {len(df)}건 업로드")

        current += timedelta(days=1)

        # 7일마다 잠시 대기 (Rate Limit 방지)
        if day_num % 7 == 0 and current <= end:
            print("   대기 중 (5초)...")
            time.sleep(5)

    print(f"\n[NAVER 완료] 총 {total_count}건")


def main():
    START_DATE = '2026-01-02'
    END_DATE = '2026-01-04'
    DAYS_PER_BATCH = 4

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("=" * 60)
    print(f"광고 데이터 백필 시작")
    print(f"기간: {START_DATE} ~ {END_DATE}")
    print(f"배치 크기: {DAYS_PER_BATCH}일")
    print("=" * 60)

    config = get_config()
    if not config._cache:
        print("[CRITICAL] SystemConfig가 로드되지 않았습니다. DB 연결을 확인하세요.")
        return

    # Meta 백필
    # date_ranges = generate_date_ranges(START_DATE, END_DATE, DAYS_PER_BATCH)
    # print(f"\nMeta 배치 수: {len(date_ranges)}개")

    # try:
    #     backfill_meta(date_ranges)
    # except Exception as e:
    #     print(f"[META ERROR] {e}")
    #     import traceback
    #     traceback.print_exc()

    print("\n" + "-" * 60)
    # print("Meta 완료. Naver 시작 전 30초 대기...")
    # time.sleep(30)

    # Naver 백필
    try:
        backfill_naver(START_DATE, END_DATE)
    except Exception as e:
        print(f"[NAVER ERROR] {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("백필 완료!")
    print("=" * 60)


if __name__ == '__main__':
    main()
