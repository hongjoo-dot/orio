"""
SQL 쿼리 빌더
- 동적 쿼리 생성
- WHERE, JOIN, ORDER BY 절 자동 구성
"""

from typing import List, Tuple, Optional, Any, Dict


class QueryBuilder:
    """SQL 쿼리를 동적으로 생성하는 빌더 클래스"""

    def __init__(self, table: str):
        self.table = table
        self.select_columns: List[str] = ["*"]
        self.joins: List[str] = []
        self.where_conditions: List[str] = []
        self.params: List[Any] = []
        self.order_clauses: List[str] = []
        self.group_clauses: List[str] = []

    def select(self, *columns: str) -> 'QueryBuilder':
        """SELECT 컬럼 지정"""
        self.select_columns = list(columns)
        return self

    def join(self, table: str, on_condition: str, join_type: str = "LEFT JOIN") -> 'QueryBuilder':
        """JOIN 절 추가"""
        self.joins.append(f"{join_type} {table} ON {on_condition}")
        return self

    def where(self, condition: str, *params: Any) -> 'QueryBuilder':
        """WHERE 조건 추가"""
        self.where_conditions.append(condition)
        self.params.extend(params)
        return self

    def where_equals(self, column: str, value: Any) -> 'QueryBuilder':
        """WHERE 등호 조건 추가"""
        if value is not None:
            self.where_conditions.append(f"{column} = ?")
            self.params.append(value)
        return self

    def where_like(self, column: str, value: str) -> 'QueryBuilder':
        """WHERE LIKE 조건 추가"""
        if value:
            self.where_conditions.append(f"{column} LIKE ?")
            self.params.append(f"%{value}%")
        return self

    def where_in(self, column: str, values: List[Any]) -> 'QueryBuilder':
        """WHERE IN 조건 추가"""
        if values:
            placeholders = ','.join(['?'] * len(values))
            self.where_conditions.append(f"{column} IN ({placeholders})")
            self.params.extend(values)
        return self

    def where_between(self, column: str, start: Any, end: Any) -> 'QueryBuilder':
        """WHERE BETWEEN 조건 추가"""
        if start and end:
            self.where_conditions.append(f"{column} BETWEEN ? AND ?")
            self.params.extend([start, end])
        elif start:
            self.where_conditions.append(f"{column} >= ?")
            self.params.append(start)
        elif end:
            self.where_conditions.append(f"{column} <= ?")
            self.params.append(end)
        return self

    def order_by(self, column: str, direction: str = "ASC") -> 'QueryBuilder':
        """ORDER BY 절 추가"""
        self.order_clauses.append(f"{column} {direction}")
        return self

    def group_by(self, *columns: str) -> 'QueryBuilder':
        """GROUP BY 절 추가"""
        self.group_clauses.extend(columns)
        return self

    def build(self) -> Tuple[str, List[Any]]:
        """
        최종 쿼리와 파라미터 반환

        Returns:
            (query, params): SQL 쿼리 문자열과 파라미터 리스트
        """
        query_parts = [f"SELECT {', '.join(self.select_columns)}"]
        query_parts.append(f"FROM {self.table}")

        # JOIN
        if self.joins:
            query_parts.extend(self.joins)

        # WHERE
        if self.where_conditions:
            query_parts.append(f"WHERE {' AND '.join(self.where_conditions)}")

        # GROUP BY
        if self.group_clauses:
            query_parts.append(f"GROUP BY {', '.join(self.group_clauses)}")

        # ORDER BY
        if self.order_clauses:
            query_parts.append(f"ORDER BY {', '.join(self.order_clauses)}")

        return " ".join(query_parts), self.params

    def build_count(self) -> Tuple[str, List[Any]]:
        """
        COUNT 쿼리 생성

        Returns:
            (query, params): COUNT 쿼리와 파라미터
        """
        query_parts = ["SELECT COUNT(*)"]
        query_parts.append(f"FROM {self.table}")

        # JOIN
        if self.joins:
            query_parts.extend(self.joins)

        # WHERE
        if self.where_conditions:
            query_parts.append(f"WHERE {' AND '.join(self.where_conditions)}")

        return " ".join(query_parts), self.params

    def build_paginated(self, page: int, limit: int) -> Tuple[str, List[Any]]:
        """
        페이지네이션이 적용된 쿼리 생성

        Args:
            page: 페이지 번호 (1부터 시작)
            limit: 페이지당 항목 수

        Returns:
            (query, params): 페이지네이션 쿼리와 파라미터
        """
        offset = (page - 1) * limit
        query, params = self.build()

        # ORDER BY가 없으면 기본 정렬 추가 (OFFSET 사용을 위해 필수)
        if not self.order_clauses:
            query += " ORDER BY (SELECT NULL)"

        query += f" OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])

        return query, params


def build_insert_query(table: str, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """
    INSERT 쿼리 생성

    Args:
        table: 테이블 이름
        data: 삽입할 데이터 딕셔너리

    Returns:
        (query, params): INSERT 쿼리와 파라미터
    """
    columns = list(data.keys())
    placeholders = ','.join(['?'] * len(columns))
    # 컬럼명을 대괄호로 감싸서 SQL 예약어 문제 방지
    column_names = ','.join([f'[{col}]' for col in columns])

    query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
    params = list(data.values())

    return query, params


def build_update_query(table: str, id_column: str, id_value: Any, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
    """
    UPDATE 쿼리 생성

    Args:
        table: 테이블 이름
        id_column: ID 컬럼 이름
        id_value: ID 값
        data: 업데이트할 데이터 딕셔너리

    Returns:
        (query, params): UPDATE 쿼리와 파라미터
    """
    # 컬럼명을 대괄호로 감싸서 SQL 예약어 문제 방지
    set_clauses = [f"[{col}] = ?" for col in data.keys()]
    query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE [{id_column}] = ?"
    params = list(data.values()) + [id_value]

    return query, params


def build_delete_query(table: str, id_column: str, id_values: List[Any]) -> Tuple[str, List[Any]]:
    """
    DELETE 쿼리 생성 (일괄 삭제 지원)

    Args:
        table: 테이블 이름
        id_column: ID 컬럼 이름
        id_values: 삭제할 ID 리스트

    Returns:
        (query, params): DELETE 쿼리와 파라미터
    """
    placeholders = ','.join(['?'] * len(id_values))
    query = f"DELETE FROM {table} WHERE {id_column} IN ({placeholders})"

    return query, id_values
