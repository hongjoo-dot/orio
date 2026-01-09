"""
Base Repository 패턴
- 모든 Repository의 기반 클래스
- CRUD 작업의 공통 로직 제공
- 상속을 통한 코드 재사용
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Dict, Any, Optional, Tuple
from .database import get_db_cursor, get_db_transaction
from .query_builder import QueryBuilder, build_insert_query, build_update_query, build_delete_query

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    모든 Repository의 Base 클래스

    Attributes:
        table_name: 테이블 이름
        id_column: Primary Key 컬럼 이름
    """

    def __init__(self, table_name: str, id_column: str = "ID"):
        self.table_name = table_name
        self.id_column = id_column

    @abstractmethod
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """
        DB Row를 Dictionary로 변환 (추상 메서드)
        각 Repository에서 구현 필요

        Args:
            row: pyodbc.Row 객체

        Returns:
            Dict: 변환된 딕셔너리
        """
        pass

    @abstractmethod
    def get_select_query(self) -> str:
        """
        기본 SELECT 쿼리 반환 (추상 메서드)
        JOIN 등이 필요한 경우 각 Repository에서 오버라이드

        Returns:
            str: SELECT 쿼리 (FROM 절까지)
        """
        pass

    def get_list(
        self,
        page: int = 1,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_dir: str = "DESC"
    ) -> Dict[str, Any]:
        """
        목록 조회 (페이지네이션 포함)

        Args:
            page: 페이지 번호
            limit: 페이지당 항목 수
            filters: 필터 조건 딕셔너리
            order_by: 정렬 컬럼
            order_dir: 정렬 방향 (ASC/DESC)

        Returns:
            Dict: {data, total, page, total_pages}
        """
        with get_db_cursor(commit=False) as cursor:
            # QueryBuilder 초기화
            builder = self._build_query_with_filters(filters)

            # 정렬 추가
            if order_by:
                builder.order_by(order_by, order_dir)
            else:
                # 기본 정렬 (ID 내림차순)
                builder.order_by(self.id_column, "DESC")

            # COUNT 쿼리 실행
            count_query, count_params = builder.build_count()
            cursor.execute(count_query, *count_params)
            total = cursor.fetchone()[0]

            # 데이터 쿼리 실행
            data_query, data_params = builder.build_paginated(page, limit)
            cursor.execute(data_query, *data_params)

            # 결과 변환
            data = [self._row_to_dict(row) for row in cursor.fetchall()]

            # 페이지네이션 응답
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            return {
                "data": data,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            }

    def get_by_id(self, id_value: Any) -> Optional[Dict[str, Any]]:
        """
        ID로 단일 레코드 조회

        Args:
            id_value: ID 값

        Returns:
            Dict | None: 레코드 딕셔너리 또는 None
        """
        with get_db_cursor(commit=False) as cursor:
            query = f"{self.get_select_query()} WHERE {self.id_column} = ?"
            cursor.execute(query, id_value)
            row = cursor.fetchone()

            return self._row_to_dict(row) if row else None

    def create(self, data: Dict[str, Any]) -> int:
        """
        새 레코드 생성

        Args:
            data: 생성할 데이터 딕셔너리

        Returns:
            int: 생성된 레코드의 ID
        """
        with get_db_cursor() as cursor:
            query, params = build_insert_query(self.table_name, data)
            cursor.execute(query, *params)

            # 생성된 ID 반환
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])

            return new_id

    def update(self, id_value: Any, data: Dict[str, Any]) -> bool:
        """
        레코드 수정

        Args:
            id_value: 수정할 레코드의 ID
            data: 수정할 데이터 딕셔너리

        Returns:
            bool: 수정 성공 여부
        """
        with get_db_cursor() as cursor:
            query, params = build_update_query(self.table_name, self.id_column, id_value, data)
            cursor.execute(query, *params)

            return cursor.rowcount > 0

    def delete(self, id_value: Any) -> bool:
        """
        레코드 삭제

        Args:
            id_value: 삭제할 레코드의 ID

        Returns:
            bool: 삭제 성공 여부
        """
        return self.bulk_delete([id_value]) > 0

    def bulk_delete(self, id_values: List[Any], batch_size: int = 1000) -> int:
        """
        일괄 삭제 (배치 처리)

        Args:
            id_values: 삭제할 ID 리스트
            batch_size: 배치 크기

        Returns:
            int: 삭제된 레코드 수
        """
        total_deleted = 0

        with get_db_cursor() as cursor:
            for i in range(0, len(id_values), batch_size):
                batch = id_values[i:i + batch_size]
                if not batch:
                    continue

                query, params = build_delete_query(self.table_name, self.id_column, batch)
                cursor.execute(query, *params)
                total_deleted += cursor.rowcount

        return total_deleted

    def exists(self, id_value: Any) -> bool:
        """
        레코드 존재 여부 확인

        Args:
            id_value: 확인할 ID

        Returns:
            bool: 존재 여부
        """
        with get_db_cursor(commit=False) as cursor:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {self.id_column} = ?"
            cursor.execute(query, id_value)
            count = cursor.fetchone()[0]

            return count > 0

    def check_duplicate(
        self,
        column: str,
        value: Any,
        exclude_id: Optional[Any] = None
    ) -> bool:
        """
        중복 여부 확인

        Args:
            column: 확인할 컬럼 이름
            value: 확인할 값
            exclude_id: 제외할 ID (수정 시 자기 자신 제외)

        Returns:
            bool: 중복 여부 (True: 중복됨)
        """
        with get_db_cursor(commit=False) as cursor:
            if exclude_id:
                query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {column} = ? AND {self.id_column} != ?"
                cursor.execute(query, value, exclude_id)
            else:
                query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {column} = ?"
                cursor.execute(query, value)

            count = cursor.fetchone()[0]
            return count > 0

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """
        필터가 적용된 QueryBuilder 생성 (내부 헬퍼)

        Args:
            filters: 필터 조건 딕셔너리

        Returns:
            QueryBuilder: 필터가 적용된 빌더 객체
        """
        # 기본 SELECT 쿼리에서 테이블명 추출
        select_query = self.get_select_query()

        # SELECT ... FROM table_name 형태에서 table_name 추출
        # 간단한 파싱 (복잡한 쿼리는 각 Repository에서 오버라이드)
        if "FROM" in select_query:
            table_part = select_query.split("FROM")[1].strip().split()[0]
        else:
            table_part = self.table_name

        builder = QueryBuilder(table_part)

        # 컬럼 추출 (SELECT와 FROM 사이)
        if "SELECT" in select_query and "FROM" in select_query:
            columns_part = select_query.split("SELECT")[1].split("FROM")[0].strip()
            if columns_part != "*":
                # 쉼표로 분리된 컬럼들
                columns = [col.strip() for col in columns_part.split(",")]
                builder.select(*columns)

        # 필터 적용
        if filters:
            self._apply_filters(builder, filters)

        return builder

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        필터 조건을 QueryBuilder에 적용
        각 Repository에서 오버라이드하여 커스텀 필터 로직 추가 가능

        Args:
            builder: QueryBuilder 객체
            filters: 필터 조건 딕셔너리
        """
        # 기본 구현: 등호 조건만 지원
        for column, value in filters.items():
            if value is not None:
                builder.where_equals(column, value)
