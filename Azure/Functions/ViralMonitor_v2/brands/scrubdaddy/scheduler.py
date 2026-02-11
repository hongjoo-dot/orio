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
from common.collectors.youtube_collector import YouTubeCollector
from common.notifiers.slack_notifier import SlackNotifier
from common.storage.duplicate_checker_azure import AzureDuplicateChecker
from common.models import Mention
from common.summarizers.blog_crawler import crawl_blog_content
from common.summarizers.youtube_transcript import extract_transcript
from common.summarizers.gemini_summarizer import summarize_content

logger = logging.getLogger(__name__)


class ScrubdaddyMonitoringScheduler:
    """스크럽대디 브랜드 모니터링 스케줄러"""

    def __init__(self):
        """초기화"""
        # 플랫폼별 Collector 설정
        self.collectors = [
            # 네이버 블로그
            NaverBlogCollector(
                keywords=config.KEYWORDS,
                client_id=config.NAVER_CLIENT_ID,
                client_secret=config.NAVER_CLIENT_SECRET,
            ),
        ]

        # YouTube Collector 추가 (API Key가 있을 경우만)
        if config.YOUTUBE_API_KEY:
            self.collectors.append(
                YouTubeCollector(
                    keywords=config.KEYWORDS,
                    api_key=config.YOUTUBE_API_KEY,
                    max_results=config.YOUTUBE_MAX_RESULTS,
                    order=config.YOUTUBE_ORDER,
                )
            )
            logger.info("YouTube Collector 추가됨")
        else:
            logger.warning("YouTube API Key가 설정되지 않아 YouTube 수집을 건너뜁니다")

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

            # 2. 제외 키워드 필터링
            excluded_mentions = self._filter_by_exclude_keywords(all_mentions)
            logger.info(f"제외 키워드 필터링: {len(all_mentions)}개 → {len(excluded_mentions)}개")

            # 3. 날짜 필터링 (당일 글만)
            filtered_mentions = self._filter_by_date_today_only(excluded_mentions)
            logger.info(f"날짜 필터링: {len(excluded_mentions)}개 → {len(filtered_mentions)}개")

            # 4. 중복 제거
            new_mentions = self.duplicate_checker.filter_new_mentions(filtered_mentions)

            # 5. AI 요약 (크롤링 + Gemini)
            new_mentions = self._enrich_with_ai_summary(new_mentions)

            if not new_mentions:
                logger.info("새로운 게시글 없음")
                self.notifier.send_summary(
                    total_mentions=0,
                    success_by_channel={},
                    collection_stats=collection_stats,
                    scan_time=datetime.now(),
                    brand_name=config.BRAND_NAME,
                )
                return

            # 6. Slack 알림 전송
            logger.info(f"새 게시글 {len(new_mentions)}건 발견, Slack 알림 전송 중...")
            success_by_channel = self.notifier.send_mentions(new_mentions)

            # 7. 요약 알림
            self.notifier.send_summary(
                total_mentions=len(new_mentions),
                success_by_channel=success_by_channel,
                collection_stats=collection_stats,
                scan_time=datetime.now(),
                brand_name=config.BRAND_NAME,
            )

            # 로그 출력 (채널별 성공 건수)
            total_success = sum(success_by_channel.values())
            channel_log = ", ".join([f"{ch}: {cnt}" for ch, cnt in success_by_channel.items()])
            logger.info(f"알림 전송 완료: 총 {total_success}/{len(new_mentions)}건 성공 ({channel_log})")

        except Exception as e:
            error_msg = f"{config.BRAND_NAME} 모니터링 실행 중 오류 발생: {e}"
            logger.error(error_msg, exc_info=True)
            self.notifier.send_error(error_msg)

        logger.info("=" * 60)
        logger.info(f"{config.BRAND_NAME} 모니터링 완료")
        logger.info("=" * 60)

    def _enrich_with_ai_summary(self, mentions: List[Mention]) -> List[Mention]:
        """각 mention에 AI 요약 추가 (크롤링 → Gemini 요약)"""
        gemini_key = config.GEMINI_API_KEY
        if not gemini_key:
            logger.warning("GEMINI_API_KEY 미설정, AI 요약 건너뜀")
            return mentions

        for mention in mentions:
            try:
                # 소스별 텍스트 추출
                if "블로그" in mention.source or "카페" in mention.source:
                    text = crawl_blog_content(mention.url)
                elif "YouTube" in mention.source:
                    text = extract_transcript(mention.url, mention.content_preview or "")
                else:
                    text = mention.content_preview or ""

                # 텍스트가 없으면 기존 content_preview fallback
                if not text:
                    text = mention.content_preview or ""

                if not text:
                    logger.info(f"요약 스킵 (텍스트 없음): {mention.title[:30]}...")
                    continue

                # Gemini AI 요약
                summary, sentiment = summarize_content(text, config.BRAND_NAME, gemini_key)
                if summary:
                    mention.ai_summary = summary
                    mention.sentiment = sentiment
                    logger.info(f"AI 요약 완료 [{sentiment}]: {mention.title[:30]}...")

            except Exception as e:
                logger.error(f"AI 요약 실패 ({mention.title[:30]}...): {e}")

        return mentions

    def _filter_by_exclude_keywords(self, mentions: List[Mention]) -> List[Mention]:
        """제외 키워드 포함 게시글 필터링"""
        exclude_keywords = config.EXCLUDE_KEYWORDS
        if not exclude_keywords:
            return mentions

        filtered = []
        for mention in mentions:
            text = f"{mention.title} {mention.content_preview or ''}"
            if not any(kw in text for kw in exclude_keywords):
                filtered.append(mention)
            else:
                logger.debug(f"제외 키워드로 필터링됨: {mention.title[:30]}...")

        return filtered

    def _filter_by_date_today_only(self, mentions: List[Mention]) -> List[Mention]:
        """당일 글만 필터링"""
        today = datetime.now().date()
        logger.info(f"날짜 필터: 당일 글만 수집 ({today.strftime('%Y-%m-%d')})")

        filtered = []
        for mention in mentions:
            if mention.posted_date.date() == today:
                filtered.append(mention)

        return filtered
