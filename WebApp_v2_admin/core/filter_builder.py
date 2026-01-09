"""
고급 필터 빌더
- 복잡한 필터 조건 생성
- OR 조건, NOT 조건 지원
- 중첩 필터 지원
"""

from typing import List, Any, Optional, Union
from enum import Enum


class FilterOperator(Enum):
    """필터 연산자"""
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    LIKE = "LIKE"
    NOT_LIKE = "NOT LIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"


class FilterCondition:
    """단일 필터 조건"""

    def __init__(self, column: str, operator: FilterOperator, value: Any = None):
        self.column = column
        self.operator = operator
        self.value = value

    def to_sql(self) -> tuple[str, List[Any]]:
        """SQL 조건문과 파라미터 반환"""
        if self.operator == FilterOperator.IS_NULL:
            return f"{self.column} IS NULL", []

        if self.operator == FilterOperator.IS_NOT_NULL:
            return f"{self.column} IS NOT NULL", []

        if self.operator == FilterOperator.LIKE or self.operator == FilterOperator.NOT_LIKE:
            return f"{self.column} {self.operator.value} ?", [f"%{self.value}%"]

        if self.operator == FilterOperator.IN or self.operator == FilterOperator.NOT_IN:
            if not isinstance(self.value, (list, tuple)):
                raise ValueError(f"IN/NOT IN requires list or tuple, got {type(self.value)}")
            placeholders = ','.join(['?'] * len(self.value))
            return f"{self.column} {self.operator.value} ({placeholders})", list(self.value)

        if self.operator == FilterOperator.BETWEEN:
            if not isinstance(self.value, (list, tuple)) or len(self.value) != 2:
                raise ValueError(f"BETWEEN requires [start, end] values")
            return f"{self.column} BETWEEN ? AND ?", list(self.value)

        # 기본 연산자 (=, !=, >, >=, <, <=)
        return f"{self.column} {self.operator.value} ?", [self.value]


class FilterGroup:
    """필터 그룹 (AND/OR 조합)"""

    def __init__(self, logic: str = "AND"):
        if logic not in ["AND", "OR"]:
            raise ValueError("Logic must be 'AND' or 'OR'")
        self.logic = logic
        self.conditions: List[Union[FilterCondition, 'FilterGroup']] = []

    def add(self, condition: Union[FilterCondition, 'FilterGroup']) -> 'FilterGroup':
        """조건 추가"""
        self.conditions.append(condition)
        return self

    def to_sql(self) -> tuple[str, List[Any]]:
        """SQL 조건문과 파라미터 반환"""
        if not self.conditions:
            return "", []

        sql_parts = []
        params = []

        for condition in self.conditions:
            sql, condition_params = condition.to_sql()
            sql_parts.append(f"({sql})")
            params.extend(condition_params)

        combined_sql = f" {self.logic} ".join(sql_parts)
        return combined_sql, params


class AdvancedFilterBuilder:
    """
    고급 필터 빌더

    사용 예시:
    ```python
    # 단순 필터
    builder = AdvancedFilterBuilder()
    builder.add(FilterCondition("Name", FilterOperator.LIKE, "Apple"))
    builder.add(FilterCondition("Price", FilterOperator.GREATER_THAN, 1000))

    # OR 조건
    or_group = FilterGroup("OR")
    or_group.add(FilterCondition("Status", FilterOperator.EQUALS, "Active"))
    or_group.add(FilterCondition("Status", FilterOperator.EQUALS, "Pending"))
    builder.add(or_group)

    # SQL 생성
    sql, params = builder.to_sql()
    ```
    """

    def __init__(self):
        self.root_group = FilterGroup("AND")

    def add(self, condition: Union[FilterCondition, FilterGroup]) -> 'AdvancedFilterBuilder':
        """조건 추가"""
        self.root_group.add(condition)
        return self

    def add_equals(self, column: str, value: Any) -> 'AdvancedFilterBuilder':
        """등호 조건 추가"""
        if value is not None:
            self.root_group.add(FilterCondition(column, FilterOperator.EQUALS, value))
        return self

    def add_like(self, column: str, value: str) -> 'AdvancedFilterBuilder':
        """LIKE 조건 추가"""
        if value:
            self.root_group.add(FilterCondition(column, FilterOperator.LIKE, value))
        return self

    def add_in(self, column: str, values: List[Any]) -> 'AdvancedFilterBuilder':
        """IN 조건 추가"""
        if values:
            self.root_group.add(FilterCondition(column, FilterOperator.IN, values))
        return self

    def add_between(self, column: str, start: Any, end: Any) -> 'AdvancedFilterBuilder':
        """BETWEEN 조건 추가"""
        if start and end:
            self.root_group.add(FilterCondition(column, FilterOperator.BETWEEN, [start, end]))
        elif start:
            self.root_group.add(FilterCondition(column, FilterOperator.GREATER_THAN_OR_EQUAL, start))
        elif end:
            self.root_group.add(FilterCondition(column, FilterOperator.LESS_THAN_OR_EQUAL, end))
        return self

    def add_or_group(self, *conditions: FilterCondition) -> 'AdvancedFilterBuilder':
        """OR 그룹 추가"""
        or_group = FilterGroup("OR")
        for condition in conditions:
            or_group.add(condition)
        self.root_group.add(or_group)
        return self

    def to_sql(self) -> tuple[str, List[Any]]:
        """SQL WHERE 조건문과 파라미터 반환"""
        return self.root_group.to_sql()

    def has_conditions(self) -> bool:
        """조건이 있는지 확인"""
        return len(self.root_group.conditions) > 0
