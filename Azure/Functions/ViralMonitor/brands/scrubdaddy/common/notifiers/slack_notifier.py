"""
Slack 알림 전송
"""
import requests
import logging
from typing import List
from ..models import Mention

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Slack Webhook을 통한 알림 전송"""

    def __init__(self, webhook_url: str):
        """
        Args:
            webhook_url: Slack Incoming Webhook URL
        """
        self.webhook_url = webhook_url

    def send_mention(self, mention: Mention) -> bool:
        """
        단일 멘션 알림 전송

        Args:
            mention: Mention 객체

        Returns:
            성공 여부
        """
        if not self.webhook_url:
            logger.warning("Slack Webhook URL이 설정되지 않았습니다.")
            return False

        try:
            # Mention 객체를 Slack 포맷으로 변환
            payload = mention.format_for_slack()

            # Slack으로 POST 요청
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                logger.info(f"Slack 알림 전송 성공: {mention.title}")
                return True
            else:
                logger.error(f"Slack 알림 전송 실패: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Slack 알림 전송 오류: {e}")
            return False

    def send_mentions(self, mentions: List[Mention]) -> dict:
        """
        여러 멘션 알림 전송 (배치)

        Args:
            mentions: Mention 객체 리스트

        Returns:
            채널별 성공 건수 딕셔너리 (예: {"네이버 블로그": 5, "YouTube": 3})
        """
        success_by_channel = {}

        for mention in mentions:
            channel = mention.source
            if channel not in success_by_channel:
                success_by_channel[channel] = 0

            if self.send_mention(mention):
                success_by_channel[channel] += 1

        return success_by_channel

    def send_summary(self, total_mentions: int, success_by_channel: dict = None, collection_stats: dict = None, scan_time = None, brand_name: str = "스크럽대디"):
        """
        수집 결과 요약 알림

        Args:
            total_mentions: 총 발견한 멘션 개수
            success_by_channel: 채널별 성공 건수 딕셔너리 (예: {"네이버 블로그": 5, "YouTube": 3})
            collection_stats: 수집기별 통계 (dict)
            scan_time: 수집 시간
            brand_name: 브랜드명 (기본값: "스크럽대디")
        """
        if not self.webhook_url:
            return

        from datetime import datetime, timedelta

        # 수집 시간 포맷팅 (한국 시간 KST = UTC+9)
        if scan_time:
            kst_time = scan_time + timedelta(hours=9)
            time_str = kst_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            kst_time = datetime.now() + timedelta(hours=9)
            time_str = kst_time.strftime("%Y-%m-%d %H:%M:%S")

        # 채널별 성공 건수 텍스트 생성
        total_success = 0
        channel_text = ""
        if success_by_channel:
            for channel, count in success_by_channel.items():
                total_success += count
                channel_text += f"  • {channel}: {count}건\n"
        else:
            channel_text = "  • 없음\n"

        summary_message = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📊 *{brand_name} 모니터링 요약*\n\n"
                                f"🕐 *수집 시간:* {time_str}\n\n"
                                f"*새 게시글:* {total_mentions}건\n"
                                f"*알림 전송:* {total_success}건\n"
                                f"{channel_text}"
                    }
                }
            ]
        }

        try:
            requests.post(
                self.webhook_url,
                json=summary_message,
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            logger.error(f"요약 알림 전송 오류: {e}")

    def send_error(self, error_message: str):
        """
        에러 알림 전송

        Args:
            error_message: 에러 메시지
        """
        if not self.webhook_url:
            return

        error_payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚠️ *모니터링 오류 발생*\n\n```{error_message}```"
                    }
                }
            ]
        }

        try:
            requests.post(
                self.webhook_url,
                json=error_payload,
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            logger.error(f"에러 알림 전송 실패: {e}")
