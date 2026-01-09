"""
Channel Repository
- Channel 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional
from core import BaseRepository, QueryBuilder, get_db_cursor


class ChannelRepository(BaseRepository):
    """Channel 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[Channel]", id_column="ChannelID")

    def get_select_query(self) -> str:
        """Channel 조회 쿼리"""
        return """
            SELECT ChannelID, Name, [Group], [Type], ContractType, Owner, LiveSource, SabangnetMallID
            FROM [dbo].[Channel]
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "ChannelID": row[0],
            "Name": row[1],
            "Group": row[2],
            "Type": row[3],
            "ContractType": row[4],
            "Owner": row[5],
            "LiveSource": row[6],
            "SabangnetMallID": row[7]
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        Channel 전용 필터 로직

        지원하는 필터:
        - name: Name LIKE 검색
        - detail_name: ChannelDetail.DetailName LIKE 검색 (JOIN 필요)
        - group: Group 완전 일치
        - type: Type 완전 일치
        - contract_type: ContractType 완전 일치
        """
        if filters.get('name'):
            builder.where_like("c.Name", filters['name'])

        if filters.get('detail_name'):
            # ChannelDetail과 조인하여 DetailName 검색
            builder.where_like("d.DetailName", filters['detail_name'])

        if filters.get('group'):
            builder.where_equals("c.[Group]", filters['group'])

        if filters.get('type'):
            builder.where_equals("c.[Type]", filters['type'])

        if filters.get('contract_type'):
            builder.where_equals("c.ContractType", filters['contract_type'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """Channel 전용 QueryBuilder 생성 (detail_name 필터 시 ChannelDetail 조인)"""

        # detail_name 필터가 있으면 JOIN 사용
        if filters and filters.get('detail_name'):
            builder = QueryBuilder("[dbo].[Channel] c")
            builder.join("[dbo].[ChannelDetail] d", "c.ChannelID = d.ChannelID", "INNER JOIN")
            builder.select(
                "DISTINCT c.ChannelID", "c.Name", "c.[Group]", "c.[Type]",
                "c.ContractType", "c.Owner", "c.LiveSource", "c.SabangnetMallID"
            )
        else:
            builder = QueryBuilder(self.table_name + " c")
            builder.select(
                "c.ChannelID", "c.Name", "c.[Group]", "c.[Type]",
                "c.ContractType", "c.Owner", "c.LiveSource", "c.SabangnetMallID"
            )

        # 필터 적용
        if filters:
            self._apply_filters(builder, filters)

        return builder

    def get_metadata(self) -> Dict[str, list]:
        """Channel 메타데이터 조회 (필터용)"""
        with get_db_cursor(commit=False) as cursor:
            metadata = {}

            # Groups
            cursor.execute("""
                SELECT DISTINCT [Group]
                FROM [dbo].[Channel]
                WHERE [Group] IS NOT NULL AND [Group] != ''
                ORDER BY [Group]
            """)
            metadata['groups'] = [row[0] for row in cursor.fetchall()]

            # Types
            cursor.execute("""
                SELECT DISTINCT [Type]
                FROM [dbo].[Channel]
                WHERE [Type] IS NOT NULL AND [Type] != ''
                ORDER BY [Type]
            """)
            metadata['types'] = [row[0] for row in cursor.fetchall()]

            # Contract Types
            cursor.execute("""
                SELECT DISTINCT ContractType
                FROM [dbo].[Channel]
                WHERE ContractType IS NOT NULL AND ContractType != ''
                ORDER BY ContractType
            """)
            metadata['contract_types'] = [row[0] for row in cursor.fetchall()]

            # Channel Names (자동완성용)
            cursor.execute("""
                SELECT DISTINCT Name
                FROM [dbo].[Channel]
                WHERE Name IS NOT NULL AND Name != ''
                ORDER BY Name
            """)
            metadata['names'] = [row[0] for row in cursor.fetchall()]

            # Owners (담당자)
            cursor.execute("""
                SELECT DISTINCT Owner
                FROM [dbo].[Channel]
                WHERE Owner IS NOT NULL AND Owner != ''
                ORDER BY Owner
            """)
            metadata['owners'] = [row[0] for row in cursor.fetchall()]

            # LiveSources (실시간 데이터소스)
            cursor.execute("""
                SELECT DISTINCT LiveSource
                FROM [dbo].[Channel]
                WHERE LiveSource IS NOT NULL AND LiveSource != ''
                ORDER BY LiveSource
            """)
            metadata['live_sources'] = [row[0] for row in cursor.fetchall()]

            # SabangnetMallIDs
            cursor.execute("""
                SELECT DISTINCT SabangnetMallID
                FROM [dbo].[Channel]
                WHERE SabangnetMallID IS NOT NULL AND SabangnetMallID != ''
                ORDER BY SabangnetMallID
            """)
            metadata['sabangnet_mall_ids'] = [row[0] for row in cursor.fetchall()]

            return metadata


class ChannelDetailRepository(BaseRepository):
    """ChannelDetail 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[ChannelDetail]", id_column="ChannelDetailID")

    def get_select_query(self) -> str:
        """ChannelDetail 조회 쿼리"""
        return """
            SELECT ChannelDetailID, ChannelID, BizNumber, DetailName
            FROM [dbo].[ChannelDetail]
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "ChannelDetailID": row[0],
            "ChannelID": row[1],
            "BizNumber": row[2],
            "DetailName": row[3]
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        ChannelDetail 전용 필터 로직

        지원하는 필터:
        - channel_id: ChannelID 완전 일치
        - detail_name: DetailName LIKE 검색
        """
        if filters.get('channel_id'):
            builder.where_equals("ChannelID", filters['channel_id'])

        if filters.get('detail_name'):
            builder.where_like("DetailName", filters['detail_name'])

    def get_by_channel_id(self, channel_id: int) -> list:
        """특정 Channel의 모든 Detail 조회"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT ChannelDetailID, ChannelID, BizNumber, DetailName
                FROM [dbo].[ChannelDetail]
                WHERE ChannelID = ?
                ORDER BY ChannelDetailID
            """, channel_id)

            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def delete_by_channel_id(self, channel_id: int) -> int:
        """특정 Channel의 모든 Detail 삭제"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                DELETE FROM [dbo].[ChannelDetail]
                WHERE ChannelID = ?
            """, channel_id)

            return cursor.rowcount

    def get_detail_names(self) -> list:
        """DetailName 목록 조회 (자동완성용)"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT DISTINCT DetailName
                FROM [dbo].[ChannelDetail]
                WHERE DetailName IS NOT NULL AND DetailName != ''
                ORDER BY DetailName
            """)
            return [row[0] for row in cursor.fetchall()]

    def create_with_channel(self, channel_data: Dict[str, Any], details: list) -> Dict[str, Any]:
        """
        Channel과 ChannelDetail을 한 번에 생성 (트랜잭션)
        - 같은 채널명이 있으면 기존 채널에 상세정보 추가 (Merge)
        - 같은 채널명이 없으면 새 채널과 상세정보 생성

        Args:
            channel_data: Channel 데이터
            details: ChannelDetail 리스트

        Returns:
            Dict: 생성된/사용된 Channel와 Details 정보
        """
        from core import get_db_cursor
        from core.query_builder import build_insert_query

        with get_db_cursor(commit=True) as cursor:
            # 1. 같은 이름의 채널이 있는지 확인
            cursor.execute("""
                SELECT ChannelID FROM [dbo].[Channel] WHERE [Name] = ?
            """, channel_data.get('Name'))
            existing_channel = cursor.fetchone()

            if existing_channel:
                # 기존 채널 사용 (Merge)
                channel_id = existing_channel[0]
                print(f"[DEBUG] 기존 Channel 사용 (Merge): ChannelID={channel_id}, Name={channel_data.get('Name')}")
            else:
                # 새 채널 생성
                channel_query, channel_params = build_insert_query("[dbo].[Channel]", channel_data)
                cursor.execute(channel_query, *channel_params)

                # Channel ID 가져오기
                cursor.execute("SELECT @@IDENTITY")
                channel_id = int(cursor.fetchone()[0])
                print(f"[DEBUG] 새 Channel 생성: ChannelID={channel_id}, Name={channel_data.get('Name')}")

            # 2. ChannelDetails 생성
            detail_ids = []
            for detail in details:
                detail['ChannelID'] = channel_id
                detail_query, detail_params = build_insert_query("[dbo].[ChannelDetail]", detail)
                cursor.execute(detail_query, *detail_params)

                # Detail ID 가져오기
                cursor.execute("SELECT @@IDENTITY")
                detail_id = int(cursor.fetchone()[0])
                detail_ids.append(detail_id)

            print(f"[DEBUG] ChannelDetail 생성 완료: {len(detail_ids)}개")

            return {
                "ChannelID": channel_id,
                "ChannelDetailIDs": detail_ids,
                "merged": existing_channel is not None,
                **channel_data
            }
