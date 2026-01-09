"""
커스텀 예외 클래스
- 표준화된 에러 처리
- 명확한 에러 타입 분류
"""


class BaseRepositoryError(Exception):
    """Repository 베이스 예외"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseConnectionError(BaseRepositoryError):
    """데이터베이스 연결 오류"""
    pass


class RecordNotFoundError(BaseRepositoryError):
    """레코드를 찾을 수 없음"""
    def __init__(self, table: str, id_value: any):
        message = f"Record not found in {table} with ID: {id_value}"
        super().__init__(message, {"table": table, "id": id_value})


class DuplicateRecordError(BaseRepositoryError):
    """중복 레코드 오류"""
    def __init__(self, table: str, column: str, value: any):
        message = f"Duplicate record in {table}: {column}={value}"
        super().__init__(message, {"table": table, "column": column, "value": value})


class ValidationError(BaseRepositoryError):
    """데이터 검증 오류"""
    def __init__(self, field: str, message: str):
        super().__init__(f"Validation error for {field}: {message}", {"field": field})


class ForeignKeyError(BaseRepositoryError):
    """외래 키 제약 위반"""
    def __init__(self, table: str, foreign_key: str, referenced_table: str):
        message = f"Foreign key constraint failed: {table}.{foreign_key} -> {referenced_table}"
        super().__init__(
            message,
            {"table": table, "foreign_key": foreign_key, "referenced_table": referenced_table}
        )


class TransactionError(BaseRepositoryError):
    """트랜잭션 오류"""
    pass


class QueryBuildError(BaseRepositoryError):
    """쿼리 생성 오류"""
    pass


class PermissionError(BaseRepositoryError):
    """권한 오류"""
    def __init__(self, action: str, resource: str):
        message = f"Permission denied: {action} on {resource}"
        super().__init__(message, {"action": action, "resource": resource})


class BusinessLogicError(BaseRepositoryError):
    """비즈니스 로직 오류"""
    pass


# 에러 코드 상수
class ErrorCode:
    """표준화된 에러 코드"""

    # 일반 에러 (1xxx)
    UNKNOWN_ERROR = 1000
    INVALID_INPUT = 1001
    VALIDATION_FAILED = 1002

    # DB 에러 (2xxx)
    DB_CONNECTION_FAILED = 2000
    DB_QUERY_FAILED = 2001
    DB_TRANSACTION_FAILED = 2002

    # 레코드 에러 (3xxx)
    RECORD_NOT_FOUND = 3000
    DUPLICATE_RECORD = 3001
    FOREIGN_KEY_VIOLATION = 3002

    # 권한 에러 (4xxx)
    UNAUTHORIZED = 4000
    FORBIDDEN = 4001

    # 비즈니스 로직 에러 (5xxx)
    BUSINESS_RULE_VIOLATION = 5000
    INVALID_STATE = 5001


def get_error_response(exception: Exception, status_code: int = 500) -> dict:
    """
    예외를 표준화된 에러 응답으로 변환

    Args:
        exception: 발생한 예외
        status_code: HTTP 상태 코드

    Returns:
        dict: 표준화된 에러 응답
    """
    if isinstance(exception, BaseRepositoryError):
        return {
            "error": True,
            "message": exception.message,
            "details": exception.details,
            "type": exception.__class__.__name__
        }

    # 일반 예외
    return {
        "error": True,
        "message": str(exception),
        "details": {},
        "type": "Exception"
    }
