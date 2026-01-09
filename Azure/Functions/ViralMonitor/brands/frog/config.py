"""
프로그 브랜드 모니터링 설정
"""
import os

# 브랜드 정보
BRAND_NAME = "프로그"

# 네이버 블로그 API 설정
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# Frog는 2단계 필터링을 사용하므로 여기서는 브랜드 키워드만 정의
# (제품 키워드는 frog_collector.py 내부에서 필터링)
NAVER_KEYWORDS = [
    "프로그", "FROG", "Frog", "frog"
]

# Azure Blob Storage 설정
BLOB_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
BLOB_CONTAINER_NAME = "viral-frog"

# Slack 설정
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL_FROG", "")
