"""
네이버 블로그/카페 수집기
네이버 검색 API를 사용하여 키워드 관련 게시글 수집
"""
import requests
from datetime import datetime
from typing import List
import logging
from .base_collector import BaseCollector
from ..models import Mention

logger = logging.getLogger(__name__)


class NaverBlogCollector(BaseCollector):
    """네이버 블로그 수집기"""

    def __init__(self, keywords: List[str], client_id: str, client_secret: str):
        super().__init__(keywords)
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = "https://openapi.naver.com/v1/search/blog.json"

    def collect(self) -> List[Mention]:
        """네이버 블로그에서 키워드 검색"""
        url_to_mention = {}  # URL별로 Mention 저장 (중복 통합용)

        for keyword in self.keywords:
            try:
                mentions = self._search_keyword(keyword)

                # 같은 URL의 게시글은 키워드 합치기
                for mention in mentions:
                    if mention.url in url_to_mention:
                        # 이미 존재하면 키워드만 추가
                        existing = url_to_mention[mention.url]
                        existing.keyword_matched += f", {keyword}"
                    else:
                        # 새 게시글이면 추가
                        url_to_mention[mention.url] = mention

                logger.info(f"네이버 블로그: '{keyword}' 검색 완료 - {len(mentions)}건 발견")
            except Exception as e:
                logger.error(f"네이버 블로그 '{keyword}' 검색 오류: {e}")

        all_mentions = list(url_to_mention.values())
        return all_mentions

    def _search_keyword(self, keyword: str) -> List[Mention]:
        """특정 키워드로 네이버 블로그 검색"""
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

        params = {
            "query": keyword,
            "display": 20,  # 최대 20개
            "sort": "date",  # 최신순
        }

        try:
            response = requests.get(self.api_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            mentions = []
            for item in data.get("items", []):
                mention = self._parse_item(item, keyword)
                mentions.append(mention)

            return mentions

        except requests.exceptions.RequestException as e:
            logger.error(f"네이버 API 요청 오류: {e}")
            return []

    def _parse_item(self, item: dict, keyword: str) -> Mention:
        """API 응답 파싱"""
        # HTML 태그 제거
        title = self._remove_html_tags(item["title"])
        description = self._remove_html_tags(item["description"])

        # 날짜 파싱 (YYYYMMDD 형식 - 시간 정보는 네이버 API에서 제공 안함)
        date_str = item["postdate"]
        posted_date = datetime.strptime(date_str, "%Y%m%d")

        return Mention(
            source="네이버 블로그",
            title=title,
            url=item["link"],
            author=item.get("bloggername", "알 수 없음"),
            posted_date=posted_date,
            content_preview=description,
            keyword_matched=keyword,
        )

    @staticmethod
    def _remove_html_tags(text: str) -> str:
        """HTML 태그 제거 (<b>, </b> 등)"""
        import re
        return re.sub(r"<[^>]+>", "", text)


class NaverCafeCollector(BaseCollector):
    """네이버 카페 수집기"""

    def __init__(self, keywords: List[str], client_id: str, client_secret: str):
        super().__init__(keywords)
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = "https://openapi.naver.com/v1/search/cafearticle.json"

    def collect(self) -> List[Mention]:
        """네이버 카페에서 키워드 검색"""
        all_mentions = []

        for keyword in self.keywords:
            try:
                mentions = self._search_keyword(keyword)
                all_mentions.extend(mentions)
                logger.info(f"네이버 카페: '{keyword}' 검색 완료 - {len(mentions)}건 발견")
            except Exception as e:
                logger.error(f"네이버 카페 '{keyword}' 검색 오류: {e}")

        return all_mentions

    def _search_keyword(self, keyword: str) -> List[Mention]:
        """특정 키워드로 네이버 카페 검색"""
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

        params = {
            "query": keyword,
            "display": 5,  # 테스트: 5개만
            "sort": "date",  # 최신순
        }

        try:
            response = requests.get(self.api_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            mentions = []
            for item in data.get("items", []):
                mention = self._parse_item(item, keyword)
                mentions.append(mention)

            return mentions

        except requests.exceptions.RequestException as e:
            logger.error(f"네이버 API 요청 오류: {e}")
            return []

    def _parse_item(self, item: dict, keyword: str) -> Mention:
        """API 응답 파싱"""
        # HTML 태그 제거
        title = self._remove_html_tags(item["title"])
        description = self._remove_html_tags(item["description"])

        # 네이버 카페 API는 작성일 정보를 제공하지 않음
        # 수집 시점의 날짜를 사용 (API 한계)
        posted_date = datetime.now()

        # 카페명 추출
        cafe_name = item.get("cafename", "알 수 없음")

        return Mention(
            source=f"네이버 카페 ({cafe_name})",
            title=title,
            url=item["link"],
            author="카페 회원",  # 네이버 카페 API는 작성자 정보 제공 안함
            posted_date=posted_date,
            content_preview=description,
            keyword_matched=keyword,
        )

    @staticmethod
    def _remove_html_tags(text: str) -> str:
        """HTML 태그 제거 (<b>, </b> 등)"""
        import re
        return re.sub(r"<[^>]+>", "", text)
