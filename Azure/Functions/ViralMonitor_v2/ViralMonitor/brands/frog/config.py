"""
프로그 브랜드 모니터링 설정
"""
import os
import sys

# shared 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared'))

from shared.keyword_config import get_keywords

# 브랜드 정보
BRAND_NAME = "프로그"

# 네이버 블로그 API 설정
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# ===== 키워드 설정 (DB 우선, fallback 하드코딩) =====
_DEFAULT_SEARCH_KEYWORDS = ["프로그", "FROG", "Frog", "frog"]
_DEFAULT_PRODUCT_KEYWORDS = [
    "고무장갑", "수세미", "설거지", "청소", "주방",
    "세제", "칫솔", "행주", "니트릴장갑", "지퍼백",
    "매직블럭", "핫딜", "특가", "쿠팡"
]

# 검색 키워드 (1단계: API 검색)
_db_search = get_keywords(BRAND_NAME, 'search')
NAVER_KEYWORDS = _db_search if _db_search else _DEFAULT_SEARCH_KEYWORDS

# 제품 키워드 (2단계: 결과 필터링)
_db_filter = get_keywords(BRAND_NAME, 'filter')
PRODUCT_KEYWORDS = _db_filter if _db_filter else _DEFAULT_PRODUCT_KEYWORDS

# 제외 키워드 (DB에서 로드, 없으면 빈 리스트)
EXCLUDE_KEYWORDS = get_keywords(BRAND_NAME, 'exclude')

# Azure Blob Storage 설정
BLOB_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
BLOB_CONTAINER_NAME = "viral-frog"

# Slack 설정
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL_FROG", "")
