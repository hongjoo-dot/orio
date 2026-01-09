"""
프로그(FROG) 브랜드 전용 네이버 블로그 수집기
2단계 필터링: 브랜드 키워드 + 제품 키워드
"""
import requests
from datetime import datetime
from typing import List
import logging
from common.collectors.base_collector import BaseCollector
from common.models import Mention

logger = logging.getLogger(__name__)


class FrogBlogCollector(BaseCollector):
    """프로그 브랜드 네이버 블로그 수집기"""

    # 브랜드 키워드 (1단계 필터: API 검색용)
    BRAND_KEYWORDS = ["프로그", "FROG", "Frog", "frog"]

    # 제품 키워드 (2단계 필터: 코드 레벨)
    PRODUCT_KEYWORDS = [
        "고무장갑", "수세미", "설거지", "청소", "주방",
        "세제", "칫솔", "행주", "니트릴장갑", "지퍼백",
        "매직블럭", "핫딜", "특가", "쿠팡"
    ]

    def __init__(self, client_id: str, client_secret: str):
        # 브랜드 키워드만 API 검색에 사용
        super().__init__(self.BRAND_KEYWORDS)
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = "https://openapi.naver.com/v1/search/blog.json"

    def collect(self) -> List[Mention]:
        """네이버 블로그에서 프로그 브랜드 게시글 수집 및 필터링"""
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

                logger.info(f"프로그 블로그: '{keyword}' 검색 완료 - {len(mentions)}건 발견")
            except Exception as e:
                logger.error(f"프로그 블로그 '{keyword}' 검색 오류: {e}")

        all_mentions = list(url_to_mention.values())

        # 2단계 필터링: 제품 키워드 포함 여부 확인
        filtered_mentions = self._filter_by_product_keywords(all_mentions)

        logger.info(f"프로그 필터링: {len(all_mentions)}건 → {len(filtered_mentions)}건 (제품 키워드 필터 적용)")

        return filtered_mentions

    def _filter_by_product_keywords(self, mentions: List[Mention]) -> List[Mention]:
        """
        제품 키워드 필터링 (2단계)

        브랜드 키워드는 이미 API 검색으로 포함되어 있으므로,
        제품 키워드가 최소 1개 이상 있는 글만 통과
        """
        filtered = []

        for mention in mentions:
            # 제목 + 내용에서 제품 키워드 검색
            text = f"{mention.title} {mention.content_preview or ''}"

            # 제품 키워드가 최소 1개 있으면 포함
            has_product = any(keyword in text for keyword in self.PRODUCT_KEYWORDS)

            if has_product:
                filtered.append(mention)
                logger.debug(f"프로그 글 통과: {mention.title[:30]}...")
            else:
                logger.debug(f"프로그 글 제외 (제품 키워드 없음): {mention.title[:30]}...")

        return filtered

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
            source="네이버 블로그 (프로그)",
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

    def get_name(self) -> str:
        """수집기 이름 반환"""
        return "프로그 블로그"
