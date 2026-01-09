"""
프로그 브랜드 모니터링 스케줄러
"""
import logging
from datetime import datetime, timedelta
from typing import List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.models import Mention
from common.notifiers.slack_notifier import SlackNotifier
from common.storage.duplicate_checker_azure import AzureDuplicateChecker
from frog_collector import FrogBlogCollector
import config


class FrogMonitoringScheduler:
    """프로그 브랜드 모니터링 워크플로우 관리"""

    def __init__(self):
        # 플랫폼별 수집기 (향후 Instagram, Twitter 등 확장 가능)
        self.collectors = [
            FrogBlogCollector(
                client_id=config.NAVER_CLIENT_ID,
                client_secret=config.NAVER_CLIENT_SECRET,
            ),
        ]

        self.notifier = SlackNotifier(webhook_url=config.SLACK_WEBHOOK_URL)
        self.duplicate_checker = AzureDuplicateChecker(
            connection_string=config.BLOB_CONNECTION_STRING,
            container_name=config.BLOB_CONTAINER_NAME
        )

    def run_once(self):
        """1회 수집 실행"""
        logging.info(f"=== {config.BRAND_NAME} 모니터링 시작 ===")
        start_time = datetime.now()

        all_mentions = []
        collection_stats = {}

        # 1. 각 플랫폼에서 데이터 수집
        for collector in self.collectors:
            try:
                platform_name = collector.__class__.__name__
                logging.info(f"[{platform_name}] 수집 시작...")

                mentions = collector.collect()
                logging.info(f"[{platform_name}] 수집 완료: {len(mentions)}건")

                all_mentions.extend(mentions)
                collection_stats[platform_name] = len(mentions)

            except Exception as e:
                logging.error(f"[{platform_name}] 수집 중 오류: {e}", exc_info=True)
                collection_stats[platform_name] = f"오류: {str(e)}"

        # 2. 당일 데이터만 필터링
        filtered_mentions = self._filter_by_date_today_only(all_mentions)
        logging.info(f"날짜 필터링 결과: {len(filtered_mentions)}건")

        # 3. 중복 제거
        new_mentions = self.duplicate_checker.filter_new_mentions(filtered_mentions)
        logging.info(f"중복 제거 후: {len(new_mentions)}건")

        # 4. Slack 알림 발송
        if not new_mentions:
            logging.info("새로운 게시글 없음")
            try:
                self.notifier.send_summary(
                    total_mentions=0,
                    success_count=0,
                    collection_stats=collection_stats,
                    scan_time=datetime.now(),
                    brand_name=config.BRAND_NAME
                )
            except Exception as e:
                logging.error(f"요약 알림 발송 실패: {e}")
        else:
            logging.info(f"새 게시글 {len(new_mentions)}건 발견, Slack 알림 전송 중...")
            success_count = 0
            for mention in new_mentions:
                try:
                    self.notifier.send_mention(mention)
                    logging.info(f"Slack 알림 발송 성공: {mention.title}")
                    success_count += 1
                except Exception as e:
                    logging.error(f"Slack 알림 발송 실패: {e}")

            # 5. 결과 요약 발송
            try:
                self.notifier.send_summary(
                    total_mentions=len(new_mentions),
                    success_count=success_count,
                    collection_stats=collection_stats,
                    scan_time=datetime.now(),
                    brand_name=config.BRAND_NAME
                )
            except Exception as e:
                logging.error(f"요약 알림 발송 실패: {e}")

        logging.info(f"=== {config.BRAND_NAME} 모니터링 완료 ===")
        logging.info(f"총 수집: {len(all_mentions)}건 → 날짜 필터링: {len(filtered_mentions)}건 → 신규: {len(new_mentions)}건")

    def _filter_by_date_today_only(self, mentions: List[Mention]) -> List[Mention]:
        """오늘 작성된 글만 필터링"""
        today = datetime.now().date()

        filtered = []
        for mention in mentions:
            if mention.posted_date.date() == today:
                filtered.append(mention)

        return filtered
