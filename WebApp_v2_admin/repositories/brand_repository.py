"""
Brand Repository
- Brand 테이블 CRUD 작업
"""

from typing import Dict, Any
from core import BaseRepository, get_db_cursor


class BrandRepository(BaseRepository):
    """Brand 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[Brand]", id_column="BrandID")

    def get_select_query(self) -> str:
        """Brand 조회 쿼리"""
        return """
            SELECT BrandID, Name, Title, UpdatedDate
            FROM [dbo].[Brand]
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "BrandID": row[0],
            "Name": row[1],
            "Title": row[2],
            "UpdatedDate": row[3].strftime('%Y-%m-%d') if row[3] else None
        }

    def get_all_brands(self) -> list:
        """모든 브랜드 조회 (BrandID, Name, Title)"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT BrandID, Name, Title
                FROM [dbo].[Brand]
                WHERE Name IS NOT NULL AND Name != ''
                ORDER BY Name
            """)
            return [{"BrandID": row[0], "Name": row[1], "Title": row[2]} for row in cursor.fetchall()]
