"""
YouTube 비디오 수집기
YouTube Data API v3를 사용하여 키워드 관련 비디오 수집
"""
import requests
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from .base_collector import BaseCollector
from ..models import Mention

logger = logging.getLogger(__name__)


class YouTubeCollector(BaseCollector):
    """YouTube 비디오 수집기"""

    def __init__(self, keywords: List[str], api_key: str, max_results: int = 20, order: str = "date"):
        """
        Args:
            keywords: 모니터링할 키워드 리스트
            api_key: YouTube Data API v3 API Key
            max_results: 키워드당 수집할 비디오 수 (기본 20, 최대 50)
            order: 정렬 방식 ('date': 최신순, 'viewCount': 조회수순, 'relevance': 관련도순)
        """
        super().__init__(keywords)
        self.api_key = api_key
        self.max_results = min(max_results, 50)  # YouTube API 최대 50개
        self.order = order
        self.search_url = "https://www.googleapis.com/youtube/v3/search"
        self.videos_url = "https://www.googleapis.com/youtube/v3/videos"

    def collect(self) -> List[Mention]:
        """YouTube에서 키워드 검색"""
        url_to_mention = {}  # URL별로 Mention 저장 (중복 통합용)

        for keyword in self.keywords:
            try:
                mentions = self._search_keyword(keyword)

                # 같은 URL의 비디오는 키워드 합치기
                for mention in mentions:
                    if mention.url in url_to_mention:
                        # 이미 존재하면 키워드만 추가
                        existing = url_to_mention[mention.url]
                        existing.keyword_matched += f", {keyword}"
                    else:
                        # 새 비디오면 추가
                        url_to_mention[mention.url] = mention

                logger.info(f"YouTube: '{keyword}' 검색 완료 - {len(mentions)}건 발견")
            except Exception as e:
                logger.error(f"YouTube '{keyword}' 검색 오류: {e}")

        all_mentions = list(url_to_mention.values())
        return all_mentions

    def _search_keyword(self, keyword: str) -> List[Mention]:
        """특정 키워드로 YouTube 비디오 검색"""
        # 1단계: 검색 API로 비디오 ID 가져오기
        video_ids = self._search_videos(keyword)
        if not video_ids:
            return []

        # 2단계: 비디오 상세 정보 가져오기 (바이럴 지표 포함)
        mentions = self._get_video_details(video_ids, keyword)
        return mentions

    def _search_videos(self, keyword: str) -> List[str]:
        """YouTube 검색 API로 비디오 ID 목록 가져오기"""
        # 오늘 자정 (KST -> UTC 변환)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        published_after = today_start.isoformat() + "Z"

        params = {
            "part": "id",
            "q": keyword,
            "type": "video",
            "maxResults": self.max_results,
            "order": self.order,
            "publishedAfter": published_after,  # 오늘 이후
            "key": self.api_key,
        }

        try:
            response = requests.get(self.search_url, params=params)
            response.raise_for_status()
            data = response.json()

            video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
            return video_ids

        except requests.exceptions.RequestException as e:
            logger.error(f"YouTube Search API 요청 오류: {e}")
            return []

    def _get_video_details(self, video_ids: List[str], keyword: str) -> List[Mention]:
        """YouTube Videos API로 비디오 상세 정보 가져오기"""
        if not video_ids:
            return []

        params = {
            "part": "snippet,statistics",
            "id": ",".join(video_ids),
            "key": self.api_key,
        }

        try:
            response = requests.get(self.videos_url, params=params)
            response.raise_for_status()
            data = response.json()

            mentions = []
            for item in data.get("items", []):
                mention = self._parse_video(item, keyword)
                if mention:
                    mentions.append(mention)

            return mentions

        except requests.exceptions.RequestException as e:
            logger.error(f"YouTube Videos API 요청 오류: {e}")
            return []

    def _parse_video(self, item: dict, keyword: str) -> Optional[Mention]:
        """YouTube API 응답 파싱"""
        try:
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            video_id = item.get("id")

            # 날짜 파싱 (ISO 8601 형식)
            published_at = snippet.get("publishedAt", "")
            posted_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")

            # 썸네일 URL (중간 크기)
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url")
            )

            # 비디오 URL
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # 조회수, 좋아요, 댓글 (없을 수 있음)
            view_count = int(statistics.get("viewCount", 0))
            like_count = int(statistics.get("likeCount", 0))
            comment_count = int(statistics.get("commentCount", 0))

            return Mention(
                source="YouTube",
                title=snippet.get("title", "제목 없음"),
                url=video_url,
                author=snippet.get("channelTitle", "알 수 없음"),
                posted_date=posted_date,
                content_preview=snippet.get("description", "")[:300],  # 설명 300자
                keyword_matched=keyword,
                view_count=view_count,
                like_count=like_count,
                comment_count=comment_count,
                thumbnail_url=thumbnail_url,
            )

        except Exception as e:
            logger.error(f"YouTube 비디오 파싱 오류: {e}")
            return None
