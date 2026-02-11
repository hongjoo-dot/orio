"""Core 모듈"""

from .database import get_db_connection, get_db_cursor, get_db_transaction, test_connection
from .query_builder import QueryBuilder, build_insert_query, build_update_query, build_delete_query
from .base_repository import BaseRepository
from .decorators import (
    transactional, with_error_handling, retry_on_failure,
    log_execution_time, validate_input
)
from .activity_decorator import log_activity, log_delete, log_bulk_delete
from .dependencies import require_permission
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
    # Decorators
    'transactional',
    'with_error_handling',
    'retry_on_failure',
    'log_execution_time',
    'validate_input',
    # Activity Logging
    'log_activity',
    'log_delete',
    'log_bulk_delete',
    # Permission
    'require_permission',
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
