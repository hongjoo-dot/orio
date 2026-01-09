"""
스크럽대디 브랜드 모니터링 설정
"""
import os

# ===== Slack 설정 =====
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# ===== 네이버 API 설정 =====
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# ===== 브랜드 정보 =====
BRAND_NAME = "스크럽대디"

# ===== 키워드 설정 =====
NAVER_KEYWORDS = [
    "스크럽대디",
    "스크럽 대디",
    "스크랩대디",  # 오타 포함
    "스크럽daddy",
    "Scrub Daddy",
    "ScrubDaddy",
    "scrubdaddy",
]

# ===== Azure Blob Storage 설정 =====
BLOB_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
BLOB_CONTAINER_NAME = "viral-scrubdaddy"

# ===== 로그 설정 =====
LOG_LEVEL = "INFO"
