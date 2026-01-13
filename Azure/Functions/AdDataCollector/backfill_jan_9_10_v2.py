"""
광고 데이터 Backfill 스크립트 - 1월 9일, 10일
Meta + Naver 광고 데이터 수집
"""

import os
import sys
import logging
from datetime import datetime

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


def backfill_meta(dates: list):
    """Meta 광고 데이터 Backfill"""
    print("\n" + "=" * 80)
    print("META ADS BACKFILL 시작")
    print("=" * 80)

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
            return {'daily': 0, 'breakdown': 0}

        # 인증
        auth = MetaAPIAuth()
        auth.refresh_long_lived_token()
        fetcher = MetaDataFetcher(auth.get_current_token())
        uploader = MetaDBUploader()

        total_daily = 0
        total_breakdown = 0

        for date in dates:
            print(f"\n{'='*80}")
            print(f"📅 날짜: {date} 처리 중...")
            print(f"{'='*80}")
            time_range = {'since': date, 'until': date}

            # 1. 기본 성과 데이터 (AdDataMeta)
            print(f"\n[1/2] AdDataMeta 테이블 수집 중...")
            all_daily_df = []
            for account in ad_accounts:
                try:
                    print(f"   📊 계정: {account['name']}")

                    creatives = fetcher.fetch_ad_creatives(account['id'])

                    fields = [
                        'date_start', 'campaign_id', 'campaign_name', 'adset_id', 'adset_name', 'ad_id', 'ad_name',
                        'impressions', 'reach', 'frequency', 'clicks', 'unique_clicks', 'spend', 'ctr', 'unique_ctr',
                        'cpm', 'cpc', 'actions', 'action_values', 'outbound_clicks',
                        'inline_link_clicks', 'inline_link_click_ctr', 'cost_per_inline_link_click',
                        'quality_ranking', 'engagement_rate_ranking', 'conversion_rate_ranking'
                    ]
                    raw_data = fetcher.fetch_insights_raw(
                        account['id'],
                        fields,
                        time_range=time_range,
                        action_breakdowns=['action_type']
                    )

                    if raw_data:
                        df = flatten_insights_data(raw_data, creatives, account['name'], usd_to_krw)
                        all_daily_df.append(df)
                        print(f"      ✓ {len(df)}건 수집")
                    else:
                        print(f"      ⚠️  데이터 없음")

                except Exception as e:
                    print(f"      ❌ 계정 {account['name']} 수집 실패: {e}")
                    continue

            if all_daily_df:
                combined_daily = pd.concat(all_daily_df)
                uploader.upload_daily_data(combined_daily)
                total_daily += len(combined_daily)
                print(f"\n   ✅ AdDataMeta DB 업로드 완료: {len(combined_daily)}건")
            else:
                print(f"\n   ⚠️  {date} AdDataMeta 데이터 없음")

            # 2. Breakdown 데이터 (AdDataMetaBreakdown)
            print(f"\n[2/2] AdDataMetaBreakdown 테이블 수집 중...")
            breakdowns_config = {
                'age_gender': ['age', 'gender'],
                'publisher_platform': ['publisher_platform']
            }

            for b_type, b_fields in breakdowns_config.items():
                print(f"\n   📈 Breakdown Type: {b_type}")
                all_breakdown_df = []
                for account in ad_accounts:
                    try:
                        print(f"      📊 계정: {account['name']}")

                        fields = [
                            'date_start', 'campaign_id', 'campaign_name', 'adset_id', 'adset_name', 'ad_id', 'ad_name',
                            'impressions', 'clicks', 'spend', 'reach', 'actions', 'action_values', 'ctr', 'cpm', 'cpc',
                            'outbound_clicks'
                        ]
                        raw_data = fetcher.fetch_insights_raw(
                            account['id'],
                            fields,
                            time_range=time_range,
                            breakdowns=b_fields,
                            action_breakdowns=['action_type']
                        )

                        if raw_data:
                            df = flatten_breakdown_data(raw_data, b_type, account['name'], usd_to_krw)
                            all_breakdown_df.append(df)
                            print(f"         ✓ {len(df)}건 수집")
                        else:
                            print(f"         ⚠️  데이터 없음")

                    except Exception as e:
                        print(f"         ❌ 계정 수집 실패: {e}")
                        continue

                if all_breakdown_df:
                    combined_breakdown = pd.concat(all_breakdown_df)
                    uploader.upload_breakdown_data(combined_breakdown)
                    total_breakdown += len(combined_breakdown)
                    print(f"      ✅ {b_type} 업로드 완료: {len(combined_breakdown)}건")
                else:
                    print(f"      ⚠️  {b_type} 데이터 없음")

        print(f"\n{'='*80}")
        print(f"✅ META 완료")
        print(f"   - AdDataMeta: {total_daily}건")
        print(f"   - AdDataMetaBreakdown: {total_breakdown}건")
        print(f"{'='*80}")
        return {'daily': total_daily, 'breakdown': total_breakdown}

    except Exception as e:
        print(f"\n❌ [META ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {'daily': 0, 'breakdown': 0}


def backfill_naver(dates: list):
    """Naver 광고 데이터 Backfill"""
    print("\n" + "=" * 80)
    print("NAVER ADS BACKFILL 시작")
    print("=" * 80)

    try:
        config = get_config()
        filter_enabled_only = config.get('NaverAdAPI', 'FILTER_ENABLED_ONLY', 'True')
        filter_enabled_only = str(filter_enabled_only).lower() in ('true', '1', 'yes')

        fetcher = NaverADReportFetcher()
        name_mapper = NaverNameMapper()
        uploader = NaverDBUploader()

        # 이름 매핑 구축
        print("\n[매핑 테이블 구축]")
        name_mapper.build_all_mappings()

        total_count = 0

        for date in dates:
            print(f"\n{'='*80}")
            print(f"📅 날짜: {date} 처리 중...")
            print(f"{'='*80}")

            try:
                raw_data = fetcher.fetch_ad_report_data(date)
                if not raw_data:
                    print(f"   ⚠️  {date} 데이터 없음 (API에서 리포트 생성 실패 또는 데이터 없음)")
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
                    print(f"   ⚠️  필터링 후 데이터 없음 (전체 {len(raw_data)}건 모두 비활성 캠페인)")
                    continue

                df = pd.DataFrame(rows)
                print(f"   📊 수집 건수: {len(df)}건 (필터링: {filtered_count}건)")

                uploader.upload_data(df)
                total_count += len(df)
                print(f"   ✅ AdDataNaver DB 업로드 완료")

            except Exception as e:
                print(f"   ❌ {date} 처리 실패: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"\n{'='*80}")
        print(f"✅ NAVER 완료")
        print(f"   - AdDataNaver: {total_count}건")
        print(f"{'='*80}")
        return {'count': total_count}

    except Exception as e:
        print(f"\n❌ [NAVER ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {'count': 0}


def main():
    """메인 실행"""
    TARGET_DATES = ['2026-01-11']

    print("=" * 80)
    print("🔄 광고 데이터 BACKFILL - 1월 9일, 10일")
    print("=" * 80)
    print(f"📆 대상 날짜: {', '.join(TARGET_DATES)}")
    print(f"📊 대상 테이블:")
    print(f"   1. AdDataMeta (Meta 기본 데이터)")
    print(f"   2. AdDataMetaBreakdown (Meta Breakdown 데이터)")
    print(f"   3. AdDataNaver (Naver 광고 데이터)")
    print("=" * 80)

    start_time = datetime.now()

    # Meta Backfill
    meta_result = backfill_meta(TARGET_DATES)

    # Naver Backfill
    naver_result = backfill_naver(TARGET_DATES)

    # 결과 요약
    end_time = datetime.now()
    print("\n" + "=" * 80)
    print("✅ BACKFILL 완료")
    print("=" * 80)
    print(f"Meta:")
    print(f"  - AdDataMeta: {meta_result['daily']}건")
    print(f"  - AdDataMetaBreakdown: {meta_result['breakdown']}건")
    print(f"Naver:")
    print(f"  - AdDataNaver: {naver_result['count']}건")
    print(f"\n소요 시간: {end_time - start_time}")
    print("=" * 80)


if __name__ == '__main__':
    main()
