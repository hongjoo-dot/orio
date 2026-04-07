"""
Cafe24 Analytics 수집 메인 오케스트레이션
수집 → 유입+매출 매핑 → DB 업로드 → Slack 알림
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def _merge_visit_and_sales(visit_data: list, sales_data: list, key_field: str) -> list:
    """
    유입 데이터와 매출 데이터를 key_field 기준으로 합침

    Args:
        visit_data: [{key_field: "xxx", visit_count: 100}, ...]
        sales_data: [{key_field: "xxx", order_count: 10, order_amount: "50000"}, ...]
        key_field: 매핑 키 (domain, ad, keyword)

    Returns:
        list: 합쳐진 데이터 [{key_field, visit_count, order_count, order_amount, ...}, ...]
    """
    # 매출 데이터를 dict로 변환
    sales_map = {}
    for item in sales_data:
        key = item.get(key_field, '')
        sales_map[key] = item

    # 유입 데이터 기준으로 매출 데이터 합침
    merged = {}
    for item in visit_data:
        key = item.get(key_field, '')
        merged[key] = {
            key_field: key,
            'visit_count': item.get('visit_count'),
            'order_count': sales_map.get(key, {}).get('order_count'),
            'order_amount': sales_map.get(key, {}).get('order_amount'),
        }
        # adsales에만 있는 join_count
        if 'join_count' in sales_map.get(key, {}):
            merged[key]['join_count'] = sales_map[key]['join_count']

    # 매출에만 있고 유입에는 없는 데이터 추가
    for key, item in sales_map.items():
        if key not in merged:
            merged[key] = {
                key_field: key,
                'visit_count': None,
                'order_count': item.get('order_count'),
                'order_amount': item.get('order_amount'),
            }
            if 'join_count' in item:
                merged[key]['join_count'] = item['join_count']

    return list(merged.values())


def main(days: int = 7):
    """
    Cafe24 Analytics 전체 수집 파이프라인

    Args:
        days: 수집 기간 (기본 7일)
    """
    from .collector import Cafe24AnalyticsCollector
    from .upload_to_db import AnalyticsDatabaseUploader

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    logger.info("=" * 70)
    logger.info(f"Cafe24 Analytics 수집 시작: {start_date} ~ {end_date}")
    logger.info("=" * 70)

    collector = Cafe24AnalyticsCollector()

    # Step 1: 데이터 수집 (7개 엔드포인트)
    logger.info("Step 1: API 데이터 수집")

    domains = collector.collect_domains(start_date, end_date)
    domainsales = collector.collect_domainsales(start_date, end_date)
    ads = collector.collect_ads(start_date, end_date)
    adsales = collector.collect_adsales(start_date, end_date)
    keywords = collector.collect_keywords(start_date, end_date)
    keywordsales = collector.collect_keywordsales(start_date, end_date)
    visitors = collector.collect_visitors(start_date, end_date)

    # Step 2: 유입 + 매출 데이터 매핑
    logger.info("Step 2: 유입 + 매출 데이터 매핑")

    merged_domains = _merge_visit_and_sales(domains, domainsales, 'domain')
    merged_ads = _merge_visit_and_sales(ads, adsales, 'ad')
    merged_keywords = _merge_visit_and_sales(keywords, keywordsales, 'keyword')

    logger.info(f"  Domains: {len(merged_domains)}건")
    logger.info(f"  Ads: {len(merged_ads)}건")
    logger.info(f"  Keywords: {len(merged_keywords)}건")
    logger.info(f"  Visitors: {len(visitors)}건")

    # Step 3: DB 업로드
    logger.info("Step 3: DB 업로드")

    result = {
        'domains': {'inserted': 0, 'updated': 0},
        'ads': {'inserted': 0, 'updated': 0},
        'keywords': {'inserted': 0, 'updated': 0},
        'visitors': {'inserted': 0, 'updated': 0},
    }

    with AnalyticsDatabaseUploader() as db:
        result['domains'] = db.merge_domains(merged_domains, end_date)
        result['ads'] = db.merge_ads(merged_ads, end_date)
        result['keywords'] = db.merge_keywords(merged_keywords, end_date)
        result['visitors'] = db.merge_visitors(visitors)

    # Step 4: Slack 알림
    logger.info("Step 4: Slack 알림")
    try:
        from cafe24.slack_notifier import send_slack_notification

        total_inserted = sum(r['inserted'] for r in result.values())
        total_updated = sum(r['updated'] for r in result.values())

        message = (
            f"✅ *[Cafe24 Analytics] 유입경로 수집 완료*\n\n"
            f"📅 기간: {start_date} ~ {end_date}\n\n"
            f"*도메인별 유입:* {len(merged_domains)}건 "
            f"(INSERT {result['domains']['inserted']}, UPDATE {result['domains']['updated']})\n"
            f"*광고별 유입:* {len(merged_ads)}건 "
            f"(INSERT {result['ads']['inserted']}, UPDATE {result['ads']['updated']})\n"
            f"*키워드별 유입:* {len(merged_keywords)}건 "
            f"(INSERT {result['keywords']['inserted']}, UPDATE {result['keywords']['updated']})\n"
            f"*일별 방문자:* {len(visitors)}건 "
            f"(INSERT {result['visitors']['inserted']}, UPDATE {result['visitors']['updated']})\n\n"
            f"📊 총 INSERT {total_inserted}건, UPDATE {total_updated}건"
        )

        send_slack_notification(message)
    except Exception as e:
        logger.warning(f"Slack 알림 실패: {e}")

    logger.info("=" * 70)
    logger.info("Cafe24 Analytics 수집 완료!")
    logger.info("=" * 70)

    return result
