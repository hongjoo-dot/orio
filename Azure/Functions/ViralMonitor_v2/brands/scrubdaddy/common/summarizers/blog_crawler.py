"""
네이버 블로그 본문 크롤링
- 블로그 URL에서 실제 본문 텍스트 추출
- iframe 구조 처리 (네이버 블로그 특성)
"""
import re
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def crawl_blog_content(url: str, max_length: int = 2000) -> str:
    """
    네이버 블로그 URL에서 본문 텍스트 추출

    Args:
        url: 네이버 블로그 게시글 URL
        max_length: 반환할 최대 문자 수

    Returns:
        본문 텍스트 (실패 시 빈 문자열)
    """
    try:
        # 네이버 블로그 URL → 모바일 URL 변환 (크롤링 용이)
        mobile_url = _convert_to_mobile_url(url)
        if not mobile_url:
            logger.warning(f"블로그 URL 변환 실패: {url}")
            return ""

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        response = requests.get(mobile_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 본문 영역 추출
        text = _extract_text(soup)

        if not text:
            logger.warning(f"본문 추출 실패: {url}")
            return ""

        # 공백 정리 및 길이 제한
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:max_length]

    except Exception as e:
        logger.error(f"블로그 크롤링 오류 ({url}): {e}")
        return ""


def _convert_to_mobile_url(url: str) -> str:
    """
    네이버 블로그 URL을 모바일 URL로 변환
    모바일 버전이 iframe 없이 본문을 직접 포함
    """
    # blog.naver.com/PostView.naver?blogId=xxx&logNo=yyy
    # blog.naver.com/xxx/yyy
    # → m.blog.naver.com/xxx/yyy

    if "blog.naver.com" not in url:
        return url  # 네이버 블로그가 아니면 원본 반환

    # PostView 형식 처리
    if "PostView" in url:
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        blog_id = params.get("blogId", [None])[0]
        log_no = params.get("logNo", [None])[0]
        if blog_id and log_no:
            return f"https://m.blog.naver.com/{blog_id}/{log_no}"

    # 일반 형식: blog.naver.com/xxx/yyy → m.blog.naver.com/xxx/yyy
    return url.replace("://blog.naver.com", "://m.blog.naver.com")


def _extract_text(soup: BeautifulSoup) -> str:
    """BeautifulSoup에서 본문 텍스트 추출"""

    # 스크립트, 스타일 태그 제거
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()

    # 네이버 블로그 모바일 본문 셀렉터 (우선순위 순)
    selectors = [
        "div.se-main-container",      # 스마트에디터 ONE
        "div.__se_component_area",     # 스마트에디터 2.0
        "div.post_ct",                 # 구형 에디터
        "div#postViewArea",            # 레거시
    ]

    for selector in selectors:
        content = soup.select_one(selector)
        if content:
            return content.get_text(separator=" ", strip=True)

    # fallback: meta description
    meta = soup.find("meta", attrs={"property": "og:description"})
    if meta and meta.get("content"):
        return meta["content"]

    return ""
