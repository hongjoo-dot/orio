"""
ViralKeywords 테이블 기반 키워드 관리
- search: API 검색 키워드
- filter: 결과 필터링 키워드 (포함 필수)
- exclude: 제외 키워드 (포함 시 결과에서 제거)
"""
import logging
from typing import List
from .database import get_db_connection

logger = logging.getLogger(__name__)


def get_keywords(brand_name: str, keyword_type: str = 'search') -> List[str]:
    """
    ViralKeywords 테이블에서 활성 키워드 조회

    Args:
        brand_name: 브랜드명 (예: '스크럽대디', '프로그')
        keyword_type: 키워드 타입 ('search', 'filter', 'exclude')

    Returns:
        키워드 문자열 리스트
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Keyword
            FROM dbo.ViralKeywords
            WHERE BrandName = ? AND KeywordType = ? AND IsActive = 1
            ORDER BY KeywordID
        """, brand_name, keyword_type)
        keywords = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        logger.info(f"[ViralKeywords] {brand_name}/{keyword_type}: {len(keywords)}건 로드")
        return keywords

    except Exception as e:
        logger.error(f"[ViralKeywords] 키워드 로드 실패 ({brand_name}/{keyword_type}): {e}")
        return []
