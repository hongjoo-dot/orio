"""
Revenue Plan Repository
- RevenuePlan 테이블 CRUD 작업
- 예상매출(EXPECTED) + 목표매출(TARGET) 관리
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


class RevenuePlanRepository(BaseRepository):
    """RevenuePlan 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[RevenuePlan]", id_column="PlanID")

    def get_select_query(self) -> str:
        """RevenuePlan 조회 쿼리 (Brand, Channel 조인 포함)"""
        return """
            SELECT
                r.PlanID, r.[Date], r.BrandID, b.Name as BrandName,
                r.ChannelID, c.Name as ChannelName, r.ChannelDetail,
                r.PlanType, r.Amount,
                r.CreatedAt, r.UpdatedAt
            FROM [dbo].[RevenuePlan] r
            LEFT JOIN [dbo].[Brand] b ON r.BrandID = b.BrandID
            LEFT JOIN [dbo].[Channel] c ON r.ChannelID = c.ChannelID
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "PlanID": row[0],
            "Date": row[1].strftime('%Y-%m-%d') if row[1] else None,
            "BrandID": row[2],
            "BrandName": row[3],
            "ChannelID": row[4],
            "ChannelName": row[5],
            "ChannelDetail": row[6],
            "PlanType": row[7],
            "Amount": float(row[8]) if row[8] else 0,
            "CreatedAt": row[9].strftime('%Y-%m-%d %H:%M:%S') if row[9] else None,
            "UpdatedAt": row[10].strftime('%Y-%m-%d %H:%M:%S') if row[10] else None
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        RevenuePlan 전용 필터 로직

        지원하는 필터:
        - brand_id: BrandID 완전 일치
        - channel_id: ChannelID 완전 일치
        - plan_type: PlanType 완전 일치 ('TARGET' / 'EXPECTED')
        - year: 연도 필터
        - month: 월 필터
        - start_date: Date >= 검색
        - end_date: Date <= 검색
        """
        if filters.get('brand_id') is not None:
            builder.where_equals("r.BrandID", filters['brand_id'])

        if filters.get('channel_id'):
            builder.where_equals("r.ChannelID", filters['channel_id'])

        if filters.get('plan_type'):
            builder.where_equals("r.PlanType", filters['plan_type'])

        if filters.get('year'):
            builder.where("YEAR(r.[Date]) = ?", filters['year'])

        if filters.get('month'):
            builder.where("MONTH(r.[Date]) = ?", filters['month'])

        if filters.get('start_date'):
            builder.where("r.[Date] >= ?", filters['start_date'])

        if filters.get('end_date'):
            builder.where("r.[Date] <= ?", filters['end_date'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """RevenuePlan 전용 QueryBuilder 생성 (Brand, Channel 조인 포함)"""
        builder = QueryBuilder("[dbo].[RevenuePlan] r")

        # 조인 추가
        builder.join("[dbo].[Brand] b", "r.BrandID = b.BrandID", "LEFT JOIN")
        builder.join("[dbo].[Channel] c", "r.ChannelID = c.ChannelID", "LEFT JOIN")

        # SELECT 컬럼 설정
        builder.select(
            "r.PlanID", "r.[Date]", "r.BrandID", "b.Name as BrandName",
            "r.ChannelID", "c.Name as ChannelName", "r.ChannelDetail",
            "r.PlanType", "r.Amount",
            "r.CreatedAt", "r.UpdatedAt"
        )

        # 필터 적용
        if filters:
            self._apply_filters(builder, filters)

        return builder

    def bulk_insert(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        대량 INSERT 처리 (MERGE 대신 단순 INSERT)
        """
        inserted = 0
        sql = """
            INSERT INTO [dbo].[RevenuePlan] 
            ([Date], BrandID, ChannelID, ChannelDetail, PlanType, Amount, CreatedAt, UpdatedAt)
            VALUES (?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
        """

        with get_db_cursor(commit=True) as cursor:
            for record in records:
                cursor.execute(sql, (
                    record['Date'], record['BrandID'], record['ChannelID'], 
                    record.get('ChannelDetail'), record['PlanType'], record['Amount']
                ))
                inserted += 1

        return {'inserted': inserted, 'updated': 0}

    def get_summary_by_month(self, year: int, plan_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        월별 합계 조회

        Args:
            year: 연도
            plan_type: 'TARGET' / 'EXPECTED' / None (전체)

        Returns:
            [{'Month': 1, 'PlanType': 'TARGET', 'TotalAmount': 1000000}, ...]
        """
        with get_db_cursor(commit=False) as cursor:
            sql = """
                SELECT
                    MONTH([Date]) as [Month],
                    PlanType,
                    SUM(Amount) as TotalAmount
                FROM [dbo].[RevenuePlan]
                WHERE YEAR([Date]) = ?
            """
            params = [year]

            if plan_type:
                sql += " AND PlanType = ?"
                params.append(plan_type)

            sql += " GROUP BY MONTH([Date]), PlanType ORDER BY [Month], PlanType"

            cursor.execute(sql, params)
            return [
                {
                    'Month': row[0],
                    'PlanType': row[1],
                    'TotalAmount': float(row[2]) if row[2] else 0
                }
                for row in cursor.fetchall()
            ]

    def get_summary_by_channel(self, year: int, plan_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        채널별 합계 조회

        Args:
            year: 연도
            plan_type: 'TARGET' / 'EXPECTED' / None (전체)

        Returns:
            [{'ChannelID': 1, 'ChannelName': '이마트', 'PlanType': 'TARGET', 'TotalAmount': 1000000}, ...]
        """
        with get_db_cursor(commit=False) as cursor:
            sql = """
                SELECT
                    r.ChannelID,
                    c.Name as ChannelName,
                    r.PlanType,
                    SUM(r.Amount) as TotalAmount
                FROM [dbo].[RevenuePlan] r
                LEFT JOIN [dbo].[Channel] c ON r.ChannelID = c.ChannelID
                WHERE YEAR(r.[Date]) = ?
            """
            params = [year]

            if plan_type:
                sql += " AND r.PlanType = ?"
                params.append(plan_type)

            sql += " GROUP BY r.ChannelID, c.Name, r.PlanType ORDER BY TotalAmount DESC"

            cursor.execute(sql, params)
            return [
                {
                    'ChannelID': row[0],
                    'ChannelName': row[1],
                    'PlanType': row[2],
                    'TotalAmount': float(row[3]) if row[3] else 0
                }
                for row in cursor.fetchall()
            ]

    def bulk_delete_by_filter(self, year: int = None, plan_type: str = None) -> int:
        """
        조건에 맞는 데이터 일괄 삭제

        Args:
            year: 연도
            plan_type: 'TARGET' / 'EXPECTED'

        Returns:
            삭제된 행 수
        """
        with get_db_cursor(commit=True) as cursor:
            sql = "DELETE FROM [dbo].[RevenuePlan] WHERE 1=1"
            params = []

            if year:
                sql += " AND YEAR([Date]) = ?"
                params.append(year)

            if plan_type:
                sql += " AND PlanType = ?"
                params.append(plan_type)

            cursor.execute(sql, params)
            return cursor.rowcount
