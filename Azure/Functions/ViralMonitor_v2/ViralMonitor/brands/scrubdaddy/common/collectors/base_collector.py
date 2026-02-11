"""
수집기 베이스 클래스
모든 채널별 collector는 이 클래스를 상속받아 구현
"""
from abc import ABC, abstractmethod
from typing import List
from ..models import Mention


class BaseCollector(ABC):
    """추상 베이스 수집기"""

    def __init__(self, keywords: List[str]):
        """
        Args:
            keywords: 모니터링할 키워드 리스트
        """
        self.keywords = keywords

    @abstractmethod
    def collect(self) -> List[Mention]:
        """
        해당 채널에서 키워드 관련 게시글 수집

        Returns:
            Mention 객체 리스트
        """
        raise NotImplementedError("Subclass must implement collect()")

    def get_name(self) -> str:
        """수집기 이름 반환"""
        return self.__class__.__name__
