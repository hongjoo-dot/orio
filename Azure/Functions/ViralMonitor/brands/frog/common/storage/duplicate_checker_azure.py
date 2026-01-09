"""
Azure Blob Storage 기반 중복 체크 관리
seen_posts.json을 Azure Blob Storage에 영구 저장
날짜 기반 자동 정리 (35일 지난 항목 삭제)
"""
import json
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from ..models import Mention
from azure.storage.blob import BlobServiceClient
import os

logger = logging.getLogger(__name__)


class AzureDuplicateChecker:
    """Azure Blob Storage 기반 중복 게시글 체크 (날짜 추적)"""

    def __init__(
        self,
        connection_string: str = None,
        container_name: str = "viral-scrubdaddy",
        blob_name: str = "seen_posts.json",
        retention_days: int = 35
    ):
        """
        Args:
            connection_string: Azure Storage 연결 문자열 (환경 변수에서 자동 로드)
            container_name: Blob Container 이름
            blob_name: Blob 파일 이름
            retention_days: 보관 기간 (일), 기본 35일
        """
        # 환경 변수에서 연결 문자열 가져오기
        self.connection_string = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING 환경 변수가 설정되지 않았습니다")

        self.container_name = container_name
        self.blob_name = blob_name
        self.retention_days = retention_days
        self.seen_posts: Dict[str, str] = {}  # {url: date_string}

        # Blob Service Client 초기화
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)

        # Container가 없으면 생성
        try:
            self.container_client.create_container()
            logger.info(f"Container '{self.container_name}' 생성됨")
        except Exception:
            # 이미 존재하면 무시
            pass

        self.blob_client = self.container_client.get_blob_client(self.blob_name)

        # seen_posts 로드 및 자동 정리
        self._load_seen_posts()
        self._cleanup_old_entries()

    def _load_seen_posts(self):
        """Azure Blob Storage에서 seen_posts 로드"""
        try:
            # Blob 다운로드
            blob_data = self.blob_client.download_blob()
            content = blob_data.readall().decode('utf-8')
            data = json.loads(content)

            # 기존 형식(seen_ids) 호환성 처리
            if "seen_ids" in data and isinstance(data["seen_ids"], list):
                # 구 형식: URL만 있음 -> 오늘 날짜로 변환
                today = datetime.now().strftime("%Y-%m-%d")
                self.seen_posts = {url: today for url in data["seen_ids"]}
                logger.info(f"구 형식에서 변환: {len(self.seen_posts)}개 게시글")
            elif "seen_posts" in data and isinstance(data["seen_posts"], dict):
                # 신 형식: {url: date}
                self.seen_posts = data["seen_posts"]
                logger.info(f"Azure Blob에서 {len(self.seen_posts)}개 게시글 로드됨")
            else:
                self.seen_posts = {}

        except Exception as e:
            # Blob이 없거나 오류 시 빈 dict로 시작
            logger.info(f"seen_posts 로드 실패 (새로 시작): {e}")
            self.seen_posts = {}

    def _save_seen_posts(self):
        """Azure Blob Storage에 seen_posts 저장"""
        try:
            # JSON 데이터 생성
            data = {
                "seen_posts": self.seen_posts,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            content = json.dumps(data, ensure_ascii=False, indent=2)

            # Blob 업로드 (덮어쓰기)
            self.blob_client.upload_blob(
                content.encode('utf-8'),
                overwrite=True
            )
            logger.info(f"Azure Blob에 {len(self.seen_posts)}개 게시글 저장 완료")
        except Exception as e:
            logger.error(f"seen_posts Azure Blob 저장 오류: {e}")

    def _cleanup_old_entries(self):
        """보관 기간 지난 항목 자동 삭제"""
        if not self.seen_posts:
            return

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")

        # 오래된 항목 필터링
        old_count = len(self.seen_posts)
        self.seen_posts = {
            url: date for url, date in self.seen_posts.items()
            if date >= cutoff_str
        }

        removed_count = old_count - len(self.seen_posts)
        if removed_count > 0:
            logger.info(f"오래된 항목 정리: {removed_count}개 삭제 (cutoff: {cutoff_str})")
            self._save_seen_posts()

    def is_new(self, mention: Mention) -> bool:
        """
        새로운 게시글인지 확인

        Args:
            mention: Mention 객체

        Returns:
            새 게시글이면 True, 이미 본 게시글이면 False
        """
        return mention.unique_id not in self.seen_posts

    def mark_as_seen(self, mention: Mention):
        """
        게시글을 '이미 봄' 상태로 표시 (날짜 기록)

        Args:
            mention: Mention 객체
        """
        today = datetime.now().strftime("%Y-%m-%d")
        self.seen_posts[mention.unique_id] = today

    def filter_new_mentions(self, mentions: List[Mention]) -> List[Mention]:
        """
        새로운 게시글만 필터링하고, 본 것으로 표시

        Args:
            mentions: Mention 객체 리스트

        Returns:
            새로운 Mention만 담긴 리스트
        """
        new_mentions = []

        for mention in mentions:
            if self.is_new(mention):
                new_mentions.append(mention)
                self.mark_as_seen(mention)

        # 변경사항을 Azure Blob에 저장
        if new_mentions:
            self._save_seen_posts()

        logger.info(f"중복 체크 (Azure Blob): 전체 {len(mentions)}건 중 {len(new_mentions)}건이 새 게시글")
        return new_mentions
