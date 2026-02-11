"""
스크럽대디 브랜드 모니터링 설정
"""
import os
import sys

# shared 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared'))

from shared.system_config import get_config
from shared.keyword_config import get_keywords

# SystemConfig 로드
_system_config = get_config()

# ===== Slack 설정 =====
SLACK_WEBHOOK_URL = _system_config.get('Slack', 'WEBHOOK_URL', os.getenv("SLACK_WEBHOOK_URL", ""))

# ===== 네이버 API 설정 =====
NAVER_CLIENT_ID = _system_config.get('API', 'NAVER_CLIENT_ID', os.getenv("NAVER_CLIENT_ID", ""))
NAVER_CLIENT_SECRET = _system_config.get('API', 'NAVER_CLIENT_SECRET', os.getenv("NAVER_CLIENT_SECRET", ""))

# ===== YouTube API 설정 =====
YOUTUBE_API_KEY = _system_config.get('API', 'YOUTUBE_API_KEY', os.getenv("YOUTUBE_API_KEY", ""))

# ===== Gemini API 설정 (AI 요약용) =====
GEMINI_API_KEY = _system_config.get('API', 'GEMINI_API_KEY', os.getenv("GEMINI_API_KEY", ""))

# ===== 브랜드 정보 =====
BRAND_NAME = "스크럽대디"

# ===== 키워드 설정 (DB 우선, fallback 하드코딩) =====
_DEFAULT_KEYWORDS = [
    "스크럽대디", "스크럽 대디", "스크랩대디",
    "스크럽daddy", "Scrub Daddy", "ScrubDaddy", "scrubdaddy",
]

_db_keywords = get_keywords(BRAND_NAME, 'search')
KEYWORDS = _db_keywords if _db_keywords else _DEFAULT_KEYWORDS

# 제외 키워드 (DB에서 로드, 없으면 빈 리스트)
EXCLUDE_KEYWORDS = get_keywords(BRAND_NAME, 'exclude')

# 하위 호환성을 위해 유지
NAVER_KEYWORDS = KEYWORDS

# ===== YouTube 수집 설정 =====
YOUTUBE_MAX_RESULTS = 20  # 키워드당 수집할 비디오 수
YOUTUBE_ORDER = "date"  # 정렬: 'date' (최신순) 또는 'viewCount' (조회수순)

# ===== Azure Blob Storage 설정 =====
BLOB_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
BLOB_CONTAINER_NAME = "viral-scrubdaddy"

# ===== 로그 설정 =====
LOG_LEVEL = "INFO"
