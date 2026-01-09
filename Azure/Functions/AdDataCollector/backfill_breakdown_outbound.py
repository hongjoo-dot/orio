"""
AdDataMetaBreakdown outbound_clicks 수정 백필 스크립트
기간: 2025-09-01 ~ 2025-12-28
"""

import sys
import os
import time
import json
import pandas as pd
from datetime import datetime, timedelta

# 로컬 실행을 위한 환경변수 설정 (local.settings.json에서 로드)
def load_local_settings():
    settings_path = r'C:\Python\Azure\Functions\AdDataCollector\local.settings.json'
    if os.path.exists(settings_path):
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            for key, value in settings.get('Values', {}).items():
                if key not in os.environ:
                    os.environ[key] = str(value)
        print("[INFO] local.settings.json 환경변수 로드 완료")
    else:
        print("[WARNING] local.settings.json 파일을 찾을 수 없습니다.")

load_local_settings()

# 모듈 경로 추가
sys.path.insert(0, r'C:\Python\Azure\Functions\AdDataCollector')

from shared.meta.auth import MetaAPIAuth
from shared.meta.data_fetcher import MetaDataFetcher
from shared.meta.db_uploader import MetaDBUploader
from shared.system_config import get_config


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


def flatten_breakdown_data(insights_raw, breakdown_type, account_name, usd_to_krw):
    """Breakdown Raw 데이터를 DB 스키마에 맞게 변환 (outbound_clicks 수정 버전)"""
    rows = []
    USD_TO_KRW = usd_to_krw

    for insight in insights_raw:
        actions = {a['action_type']: int(a['value']) for a in insight.get('actions', [])}
        action_values = {a['action_type']: float(a['value']) for a in insight.get('action_values', [])}

        impressions = int(insight.get('impressions', 0))
        clicks = int(insight.get('clicks', 0))
        spend = float(insight.get('spend', 0))
        purchase = actions.get('purchase', 0) or actions.get('omni_purchase', 0)
        purchase_value = action_values.get('purchase', 0) or action_values.get('omni_purchase', 0)

        # outbound_clicks 처리 (수정된 로직)
        outbound_val = insight.get('outbound_clicks', 0)
        outbound_clicks = int(outbound_val[0]['value']) if isinstance(outbound_val, list) and outbound_val else int(outbound_val or 0)
        outbound_clicks = max(outbound_clicks, actions.get('outbound_click', 0))

        # Calculated
        aov = purchase_value / purchase if purchase > 0 else 0
        cpa = spend / purchase if purchase > 0 else 0
        roas = purchase_value / spend if spend > 0 else 0
        cvr = purchase / clicks if clicks > 0 else 0

        # KRW
        spend_krw = spend * USD_TO_KRW
        purchase_value_krw = purchase_value * USD_TO_KRW
        aov_krw = aov * USD_TO_KRW
        cpa_krw = cpa * USD_TO_KRW

        row = {
            'AccountName': account_name,
            'Date': insight.get('date_start'),
            'CampaignID': insight.get('campaign_id'),
            'CampaignName': insight.get('campaign_name'),
            'AdSetID': insight.get('adset_id'),
            'AdSetName': insight.get('adset_name'),
            'AdID': insight.get('ad_id'),
            'AdName': insight.get('ad_name'),

            'BreakdownType': breakdown_type,
            'Age': insight.get('age'),
            'Gender': insight.get('gender'),
            'PublisherPlatform': insight.get('publisher_platform'),
            'DevicePlatform': insight.get('device_platform'),
            'ImpressionDevice': insight.get('impression_device'),

            'Impressions': impressions,
            'Reach': int(insight.get('reach', 0)),
            'Frequency': float(insight.get('frequency', 0)),
            'Clicks': clicks,
            'CTR': float(insight.get('ctr', 0)),
            'Spend': spend,
            'CPM': float(insight.get('cpm', 0)),
            'CPC': float(insight.get('cpc', 0)),

            'LandingPageViews': actions.get('landing_page_view', 0),
            'AddToCart': actions.get('add_to_cart', 0),
            'InitiateCheckout': actions.get('initiate_checkout', 0),
            'Purchase': purchase,
            'CompleteRegistration': actions.get('complete_registration', 0),
            'OutboundClicks': outbound_clicks,
            'LinkClicks': actions.get('link_click', 0),

            'PurchaseValue': purchase_value,
            'AOV': aov, 'CPA': cpa, 'ROAS': roas, 'CVR': cvr,
            'SpendKRW': spend_krw, 'PurchaseValueKRW': purchase_value_krw,
            'AOVKRW': aov_krw, 'CPAKRW': cpa_krw
        }
        rows.append(row)

    return pd.DataFrame(rows)


def backfill_breakdown():
    """AdDataMetaBreakdown 백필 실행"""
    START_DATE = '2025-09-01'
    END_DATE = '2025-12-28'
    DAYS_PER_BATCH = 7

    print("=" * 70)
    print(f"AdDataMetaBreakdown OutboundClicks 백필 시작")
    print(f"기간: {START_DATE} ~ {END_DATE}")
    print(f"배치 크기: {DAYS_PER_BATCH}일")
    print(f"시작 시간: {datetime.now()}")
    print("=" * 70)

    # 설정 로드
    config = get_config()
    usd_to_krw = int(config.get('Common', 'USD_TO_KRW_RATE', 1400))
    print(f"\n[CONFIG] 환율: USD 1 = KRW {usd_to_krw}")

    ad_accounts_json = config.get('MetaAdAPI', 'AD_ACCOUNTS')
    if not ad_accounts_json:
        print("[ERROR] Meta 광고 계정 정보가 없습니다.")
        return
    ad_accounts = json.loads(ad_accounts_json)
    print(f"[CONFIG] 광고 계정: {len(ad_accounts)}개")

    # 인증
    auth = MetaAPIAuth()
    auth.refresh_long_lived_token()
    fetcher = MetaDataFetcher(auth.get_current_token())
    uploader = MetaDBUploader()

    # 날짜 배치 생성
    date_ranges = generate_date_ranges(START_DATE, END_DATE, DAYS_PER_BATCH)
    print(f"[INFO] 총 배치 수: {len(date_ranges)}개\n")

    total_count = 0
    breakdowns_config = {
        'age_gender': ['age', 'gender'],
        'publisher_platform': ['publisher_platform']
    }

    for i, time_range in enumerate(date_ranges):
        print(f"\n[{i+1}/{len(date_ranges)}] {time_range['since']} ~ {time_range['until']}")

        for b_type, b_fields in breakdowns_config.items():
            all_breakdown_df = []

            for account in ad_accounts:
                print(f"   [{b_type}] 계정: {account['name']}", end=" ")

                fields = [
                    'date_start', 'campaign_id', 'campaign_name', 'adset_id', 'adset_name',
                    'ad_id', 'ad_name', 'impressions', 'clicks', 'spend', 'reach',
                    'actions', 'action_values', 'ctr', 'cpm', 'cpc',
                    'outbound_clicks'  # 핵심: outbound_clicks 필드 추가
                ]

                raw_data = fetcher.fetch_insights_raw(
                    account['id'], fields,
                    time_range=time_range,
                    breakdowns=b_fields,
                    time_increment=1  # 일별 데이터
                )

                if raw_data:
                    df = flatten_breakdown_data(raw_data, b_type, account['name'], usd_to_krw)
                    all_breakdown_df.append(df)
                    print(f"-> {len(df)}건")
                else:
                    print("-> 0건")

            if all_breakdown_df:
                combined = pd.concat(all_breakdown_df)
                uploader.upload_breakdown_data(combined)
                total_count += len(combined)
                print(f"   [{b_type}] 업로드 완료: {len(combined)}건")

        # Rate Limit 방지 대기 (배치 간)
        if i < len(date_ranges) - 1:
            print("   대기 중 (10초)...")
            time.sleep(10)

    print("\n" + "=" * 70)
    print(f"백필 완료!")
    print(f"총 업데이트: {total_count}건")
    print(f"종료 시간: {datetime.now()}")
    print("=" * 70)


if __name__ == '__main__':
    backfill_breakdown()
