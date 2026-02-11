"""
공통 Pydantic 모델
- 여러 Router에서 공유하는 요청/응답 모델
"""

from pydantic import BaseModel
from typing import List, Any


class BulkDeleteRequest(BaseModel):
    """일괄 삭제 요청 (int ID)"""
    ids: List[int]


class BulkDeleteAnyRequest(BaseModel):
    """일괄 삭제 요청 (문자열/혼합 ID)"""
    ids: List[Any]
