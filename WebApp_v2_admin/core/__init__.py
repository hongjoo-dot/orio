"""Core 모듈"""

from .database import get_db_connection, get_db_cursor, get_db_transaction, test_connection
from .query_builder import QueryBuilder, build_insert_query, build_update_query, build_delete_query
from .base_repository import BaseRepository
from .filter_builder import (
    AdvancedFilterBuilder, FilterCondition, FilterGroup, FilterOperator
)
from .decorators import (
    transactional, with_error_handling, retry_on_failure,
    log_execution_time, validate_input
)
from .exceptions import (
    BaseRepositoryError, DatabaseConnectionError, RecordNotFoundError,
    DuplicateRecordError, ValidationError, ForeignKeyError,
    TransactionError, QueryBuildError, PermissionError, BusinessLogicError,
    ErrorCode, get_error_response
)

__all__ = [
    # Database
    'get_db_connection',
    'get_db_cursor',
    'get_db_transaction',
    'test_connection',
    # Query Builder
    'QueryBuilder',
    'build_insert_query',
    'build_update_query',
    'build_delete_query',
    # Base Repository
    'BaseRepository',
    # Advanced Filter
    'AdvancedFilterBuilder',
    'FilterCondition',
    'FilterGroup',
    'FilterOperator',
    # Decorators
    'transactional',
    'with_error_handling',
    'retry_on_failure',
    'log_execution_time',
    'validate_input',
    # Exceptions
    'BaseRepositoryError',
    'DatabaseConnectionError',
    'RecordNotFoundError',
    'DuplicateRecordError',
    'ValidationError',
    'ForeignKeyError',
    'TransactionError',
    'QueryBuildError',
    'PermissionError',
    'BusinessLogicError',
    'ErrorCode',
    'get_error_response',
]
