"""
Meta Ads 데이터 수집 파이프라인 (Updated)
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from .auth import MetaAPIAuth
from .data_fetcher import MetaDataFetcher
from .db_uploader import MetaDBUploader
from ..system_config import get_config
from ..slack_notifier import send_meta_notification


def flatten_insights_data(insights_raw, ad_creatives_map, account_name, usd_to_krw):
    """Daily Raw 데이터를 DB 스키마에 맞게 변환"""
    rows = []
    USD_TO_KRW = usd_to_krw

    for insight in insights_raw:
        actions = {a['action_type']: int(a['value']) for a in insight.get('actions', [])}
        action_values = {a['action_type']: float(a['value']) for a in insight.get('action_values', [])}

        # 기본 지표
        impressions = int(insight.get('impressions', 0))
        clicks = int(insight.get('clicks', 0))
        spend = float(insight.get('spend', 0))
        purchase = actions.get('purchase', 0) or actions.get('omni_purchase', 0)
        purchase_value = action_values.get('purchase', 0) or action_values.get('omni_purchase', 0)

        # inline_link_clicks 처리
        inline_val = insight.get('inline_link_clicks', 0)
        inline_clicks = int(inline_val[0]['value']) if isinstance(inline_val, list) and inline_val else int(inline_val or 0)

        # outbound_clicks 처리
        outbound_val = insight.get('outbound_clicks', 0)
        outbound_clicks = int(outbound_val[0]['value']) if isinstance(outbound_val, list) and outbound_val else int(outbound_val or 0)
        outbound_clicks = max(outbound_clicks, actions.get('outbound_click', 0))

        # Calculated Metrics
        aov = purchase_value / purchase if purchase > 0 else 0
        cpa = spend / purchase if purchase > 0 else 0
        roas = purchase_value / spend if spend > 0 else 0
        cvr = purchase / clicks if clicks > 0 else 0

        # KRW Conversion
        spend_krw = spend * USD_TO_KRW
        purchase_value_krw = purchase_value * USD_TO_KRW
        aov_krw = aov * USD_TO_KRW
        cpa_krw = cpa * USD_TO_KRW

        # Creative Info
        ad_id = insight.get('ad_id')
        creative = ad_creatives_map.get(ad_id, {})

        row = {
            'AccountName': account_name,
            'Date': insight.get('date_start'),
            'CampaignID': insight.get('campaign_id'),
            'CampaignName': insight.get('campaign_name'),
            'AdSetID': insight.get('adset_id'),
            'AdSetName': insight.get('adset_name'),
            'AdID': ad_id,
            'AdName': insight.get('ad_name'),

            'Impressions': impressions,
            'Reach': int(insight.get('reach', 0)),
            'Frequency': float(insight.get('frequency', 0)),
            'Clicks': clicks,
            'UniqueClicks': int(insight.get('unique_clicks', 0)),
            'CTR': float(insight.get('ctr', 0)),
            'UniqueCTR': float(insight.get('unique_ctr', 0)),
            'Spend': spend,
            'CPM': float(insight.get('cpm', 0)),
            'CPC': float(insight.get('cpc', 0)),

            'InlineLinkClicks': inline_clicks,
            'InlineLinkClickCTR': float(insight.get('inline_link_click_ctr', 0)),
            'CostPerInlineLinkClick': float(insight.get('cost_per_inline_link_click', 0)),
            'QualityRanking': insight.get('quality_ranking'),
            'EngagementRateRanking': insight.get('engagement_rate_ranking'),
            'ConversionRateRanking': insight.get('conversion_rate_ranking'),

            'LinkClicks': actions.get('link_click', 0),
            'OutboundClicks': outbound_clicks,
            'LandingPageViews': actions.get('landing_page_view', 0),
            'CompleteRegistration': actions.get('complete_registration', 0),
            'AddToCart': actions.get('add_to_cart', 0),
            'InitiateCheckout': actions.get('initiate_checkout', 0),
            'Purchase': purchase,
            'WebsitePurchase': purchase,

            'PostEngagement': actions.get('post_engagement', 0),
            'PostReaction': actions.get('post_reaction', 0),
            'Comment': actions.get('comment', 0),
            'VideoView': actions.get('video_view', 0),
            'PostSave': actions.get('post', 0),  # 'post' action is save
            'PageEngagement': actions.get('page_engagement', 0),
            'PostClick': actions.get('post_click', 0),

            'PurchaseValue': purchase_value,
            'WebsitePurchaseValue': purchase_value,

            'AOV': aov, 'CPA': cpa, 'ROAS': roas, 'CVR': cvr,

            'EngagementRate': actions.get('post_engagement', 0) / impressions if impressions > 0 else 0,
            'ReactionRate': actions.get('post_reaction', 0) / impressions if impressions > 0 else 0,
            'CommentRate': actions.get('comment', 0) / impressions if impressions > 0 else 0,
            'VideoViewRate': actions.get('video_view', 0) / impressions if impressions > 0 else 0,
            'SaveRate': actions.get('post', 0) / impressions if impressions > 0 else 0,

            'SpendKRW': spend_krw,
            'PurchaseValueKRW': purchase_value_krw,
            'AOVKRW': aov_krw,
            'CPAKRW': cpa_krw,

            'CreativeID': creative.get('creative_id'),
            'AdTitle': creative.get('title'),
            'AdBody': creative.get('body'),
            'CTAType': creative.get('cta'),
            'LinkURL': creative.get('link_url'),
            'ImageURL': creative.get('image_url'),
            'VideoID': creative.get('video_id'),
            'ThumbnailURL': creative.get('thumbnail_url'),
            'PreviewURL': creative.get('preview_url')
        }
        rows.append(row)

    return pd.DataFrame(rows)


def flatten_breakdown_data(insights_raw, breakdown_type, account_name, usd_to_krw):
    """Breakdown Raw 데이터를 DB 스키마에 맞게 변환"""
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

        # outbound_clicks 처리
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


def run_meta_pipeline():
    """메인 실행 함수"""
    print("=" * 60)
    print(f"Meta Ads 파이프라인 시작: {datetime.now()}")
    print("=" * 60)

    result = {'daily_count': 0, 'breakdown_count': 0}

    try:
        # 1. 설정 로드
        config = get_config()

        # 환율 조회 (기본값 1400)
        usd_to_krw = int(config.get('Common', 'USD_TO_KRW_RATE', 1400))
        print(f"[CONFIG] 환율: USD 1 = KRW {usd_to_krw}")

        # 광고 계정 조회 (JSON 형식)
        import json
        ad_accounts_json = config.get('MetaAdAPI', 'AD_ACCOUNTS')
        if ad_accounts_json:
            ad_accounts = json.loads(ad_accounts_json)
            print(f"[CONFIG] 광고 계정: {len(ad_accounts)}개")
        else:
            print("[ERROR] Meta 광고 계정 정보가 SystemConfig에 없습니다.")
            return

        # 2. 인증 및 토큰 관리
        auth = MetaAPIAuth()
        refresh_ok = auth.refresh_long_lived_token()

        # 토큰 만료 상태 점검
        token_status = auth.check_token_expiry()
        if not token_status['is_valid']:
            msg = "[CRITICAL] Meta API 토큰이 만료되었습니다. 즉시 새 토큰을 발급해주세요."
            logging.error(msg)
            send_meta_notification(msg)
        elif token_status['warning']:
            days_left = token_status['days_left']
            msg = f"[WARNING] Meta API 토큰이 {days_left}일 후 만료됩니다. 갱신이 필요합니다."
            if not refresh_ok:
                msg += "\n토큰 자동 갱신도 실패했습니다. 수동으로 새 토큰을 발급해주세요."
            logging.warning(msg)
            send_meta_notification(msg)

        fetcher = MetaDataFetcher(auth.get_current_token())
        uploader = MetaDBUploader()

        # 3. 어제 날짜 계산
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        logging.info(f"[INFO] 수집 대상 날짜: {yesterday} (어제)")

        for date in [yesterday]:
            print(f"\n>>> 날짜: {date} 처리 중...")
            time_range = {'since': date, 'until': date}

            # --- 1. 기본 성과 데이터 ---
            all_daily_df = []
            for account in ad_accounts:
                print(f"   [Main] 계정: {account['name']}")

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

            if all_daily_df:
                combined_daily = pd.concat(all_daily_df)
                uploader.upload_daily_data(combined_daily)
                result['daily_count'] += len(combined_daily)

            # --- 2. Breakdown 데이터 ---
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
                    result['breakdown_count'] += len(combined_breakdown)

        print("\n[SUCCESS] 모든 작업 완료")
        return result

    except Exception as e:
        print(f"[ERROR] 파이프라인 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise
