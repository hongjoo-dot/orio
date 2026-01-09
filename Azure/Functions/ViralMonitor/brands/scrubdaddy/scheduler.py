"""
스크럽대디 브랜드 모니터링 스케줄러
"""
import logging
from datetime import datetime
from typing import List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from common.collectors.naver_collector import NaverBlogCollector
from common.notifiers.slack_notifier import SlackNotifier
from common.storage.duplicate_checker_azure import AzureDuplicateChecker
from common.models import Mention

logger = logging.getLogger(__name__)


class ScrubdaddyMonitoringScheduler:
    """스크럽대디 브랜드 모니터링 스케줄러"""

    def __init__(self):
        """초기화"""
        # 플랫폼별 Collector 설정
        self.collectors = [
            # 네이버 블로그
            NaverBlogCollector(
                keywords=config.NAVER_KEYWORDS,
                client_id=config.NAVER_CLIENT_ID,
                client_secret=config.NAVER_CLIENT_SECRET,
            ),
        ]

        # Notifier 초기화
        self.notifier = SlackNotifier(webhook_url=config.SLACK_WEBHOOK_URL)

        # Azure Blob Storage 기반 중복 체크
        self.duplicate_checker = AzureDuplicateChecker(
            connection_string=config.BLOB_CONNECTION_STRING,
            container_name=config.BLOB_CONTAINER_NAME,
        )

        logger.info(f"{config.BRAND_NAME} 모니터링 스케줄러 초기화 완료: {len(self.collectors)}개 플랫폼")

    def run_once(self):
        """1회 모니터링 실행"""
        logger.info("=" * 60)
        logger.info(f"{config.BRAND_NAME} 모니터링 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        try:
            # 1. 모든 플랫폼에서 데이터 수집
            all_mentions: List[Mention] = []
            collection_stats = {}

            for collector in self.collectors:
                try:
                    mentions = collector.collect()
                    all_mentions.extend(mentions)
                    collection_stats[collector.get_name()] = len(mentions)
                except Exception as e:
                    error_msg = f"{collector.get_name()} 수집 오류: {e}"
                    logger.error(error_msg)
                    self.notifier.send_error(error_msg)
                    collection_stats[collector.get_name()] = 0

            logger.info(f"총 {len(all_mentions)}개 게시글 수집 완료")

            # 2. 날짜 필터링 (당일 글만)
            filtered_mentions = self._filter_by_date_today_only(all_mentions)
            logger.info(f"날짜 필터링: {len(all_mentions)}개 → {len(filtered_mentions)}개")

            # 3. 중복 제거
            new_mentions = self.duplicate_checker.filter_new_mentions(filtered_mentions)

            if not new_mentions:
                logger.info("새로운 게시글 없음")
                self.notifier.send_summary(
                    total_mentions=0,
                    success_count=0,
                    collection_stats=collection_stats,
                    scan_time=datetime.now(),
                    brand_name=config.BRAND_NAME,
                )
                return

            # 4. Slack 알림 전송
            logger.info(f"새 게시글 {len(new_mentions)}건 발견, Slack 알림 전송 중...")
            success_count = self.notifier.send_mentions(new_mentions)

            # 5. 요약 알림
            self.notifier.send_summary(
                total_mentions=len(new_mentions),
                success_count=success_count,
                collection_stats=collection_stats,
                scan_time=datetime.now(),
                brand_name=config.BRAND_NAME,
            )

            logger.info(f"알림 전송 완료: {success_count}/{len(new_mentions)}건 성공")

        except Exception as e:
            error_msg = f"{config.BRAND_NAME} 모니터링 실행 중 오류 발생: {e}"
            logger.error(error_msg, exc_info=True)
            self.notifier.send_error(error_msg)

        logger.info("=" * 60)
        logger.info(f"{config.BRAND_NAME} 모니터링 완료")
        logger.info("=" * 60)

    def _filter_by_date_today_only(self, mentions: List[Mention]) -> List[Mention]:
        """당일 글만 필터링"""
        today = datetime.now().date()
        logger.info(f"날짜 필터: 당일 글만 수집 ({today.strftime('%Y-%m-%d')})")

        filtered = []
        for mention in mentions:
            if mention.posted_date.date() == today:
                filtered.append(mention)

        return filtered
