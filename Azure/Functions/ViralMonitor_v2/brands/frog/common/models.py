"""
데이터 모델 정의
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Mention:
    """브랜드 언급 데이터 모델"""

    # 필수 필드
    source: str              # 출처 (예: "네이버 블로그", "네이버 카페")
    title: str               # 게시글 제목
    url: str                 # 게시글 링크
    author: str              # 작성자
    posted_date: datetime    # 작성일

    # 선택 필드
    content_preview: Optional[str] = None  # 내용 미리보기 (150자)
    keyword_matched: Optional[str] = None   # 매칭된 키워드

    # AI 요약 (V2)
    ai_summary: Optional[str] = None        # Gemini AI 요약문
    sentiment: Optional[str] = None         # 감성 분석 ('긍정', '부정', '중립')

    def __post_init__(self):
        """게시글 고유 ID 생성 (중복 체크용)"""
        self.unique_id = f"{self.source}_{self.url}"

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "source": self.source,
            "title": self.title,
            "url": self.url,
            "author": self.author,
            "posted_date": self.posted_date.isoformat(),
            "content_preview": self.content_preview,
            "keyword_matched": self.keyword_matched,
            "unique_id": self.unique_id,
        }

    def format_for_slack(self) -> dict:
        """Slack 메시지 포맷으로 변환"""
        # 날짜 포맷팅
        date_str = self.posted_date.strftime("%Y-%m-%d %H:%M")

        # 감성 이모지
        sentiment_emoji = {"긍정": "👍", "부정": "👎", "중립": "➖"}.get(self.sentiment, "")
        sentiment_text = f" {sentiment_emoji} {self.sentiment}" if self.sentiment else ""

        # Slack Block Kit 형식
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔍 {self.source} - 새 언급 발견{sentiment_text}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*제목:*\n{self.title}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*작성자:*\n{self.author}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*작성일:*\n{date_str}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*매칭 키워드:*\n`{self.keyword_matched}`"
                        }
                    ]
                }
            ]
        }

        # AI 요약이 있으면 표시, 없으면 기존 미리보기 fallback
        if self.ai_summary:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🤖 AI 요약:*\n> {self.ai_summary}"
                }
            })
        elif self.content_preview:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*내용 미리보기:*\n> {self.content_preview[:150]}..."
                }
            })

        # 링크 버튼 추가
        message["blocks"].append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "게시글 보기",
                        "emoji": True
                    },
                    "url": self.url,
                    "style": "primary"
                }
            ]
        })

        return message
