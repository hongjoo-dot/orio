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

    # YouTube 바이럴 지표 (선택)
    view_count: Optional[int] = None        # 조회수
    like_count: Optional[int] = None        # 좋아요 수
    comment_count: Optional[int] = None     # 댓글 수
    thumbnail_url: Optional[str] = None     # 썸네일 URL

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
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "thumbnail_url": self.thumbnail_url,
            "unique_id": self.unique_id,
        }

    def format_for_slack(self) -> dict:
        """Slack 메시지 포맷으로 변환"""
        # 날짜 포맷팅
        date_str = self.posted_date.strftime("%Y-%m-%d %H:%M")

        # 미리보기 텍스트 (있으면 표시)
        preview = ""
        if self.content_preview:
            preview = f"\n> {self.content_preview[:150]}..."

        # Slack Block Kit 형식
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔍 {self.source} - 새 언급 발견",
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

        # 미리보기가 있으면 추가
        if preview:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*내용 미리보기:*{preview}"
                }
            })

        # YouTube 바이럴 지표 추가 (있으면)
        if self.view_count is not None or self.like_count is not None:
            viral_fields = []
            if self.view_count is not None:
                viral_fields.append({
                    "type": "mrkdwn",
                    "text": f"*조회수:*\n{self.view_count:,}회"
                })
            if self.like_count is not None:
                viral_fields.append({
                    "type": "mrkdwn",
                    "text": f"*좋아요:*\n{self.like_count:,}개"
                })
            if self.comment_count is not None:
                viral_fields.append({
                    "type": "mrkdwn",
                    "text": f"*댓글:*\n{self.comment_count:,}개"
                })

            message["blocks"].append({
                "type": "section",
                "fields": viral_fields
            })

        # 썸네일 추가 (YouTube용)
        if self.thumbnail_url:
            message["blocks"].append({
                "type": "image",
                "image_url": self.thumbnail_url,
                "alt_text": "Video Thumbnail"
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
