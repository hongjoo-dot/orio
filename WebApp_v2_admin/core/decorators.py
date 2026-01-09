"""
데코레이터 모듈
- 트랜잭션 관리
- 에러 핸들링
- 로깅
"""

from functools import wraps
from typing import Callable, Any
import logging
from .database import get_db_transaction

# 로거 설정
logger = logging.getLogger(__name__)


def transactional(func: Callable) -> Callable:
    """
    트랜잭션 데코레이터

    함수 실행 중 예외 발생 시 자동 롤백
    정상 완료 시 자동 커밋

    사용 예시:
    ```python
    @transactional
    def create_product_with_boxes(product_data, boxes_data):
        # 모든 작업이 성공하거나 모두 실패
        product_id = create_product(product_data)
        for box_data in boxes_data:
            create_box(product_id, box_data)
        return product_id
    ```
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_db_transaction() as cursor:
            try:
                result = func(*args, **kwargs, cursor=cursor)
                return result
            except Exception as e:
                logger.error(f"Transaction failed in {func.__name__}: {str(e)}")
                raise
    return wrapper


def with_error_handling(default_return: Any = None, log_error: bool = True):
    """
    에러 핸들링 데코레이터 (커스터마이징 가능)

    Args:
        default_return: 에러 발생 시 반환할 기본값
        log_error: 에러 로깅 여부

    사용 예시:
    ```python
    @with_error_handling(default_return=[], log_error=True)
    def get_products():
        # 에러 발생 시 빈 리스트 반환
        return product_repo.get_list()
    ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                return default_return
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    재시도 데코레이터

    Args:
        max_retries: 최대 재시도 횟수
        delay: 재시도 간격 (초)

    사용 예시:
    ```python
    @retry_on_failure(max_retries=3, delay=2.0)
    def fetch_external_data():
        # DB 연결 실패 시 3번까지 재시도
        return external_api.get_data()
    ```
    """
    import time

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}"
                    )

                    if attempt < max_retries - 1:
                        time.sleep(delay)

            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception

        return wrapper
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """
    실행 시간 로깅 데코레이터

    사용 예시:
    ```python
    @log_execution_time
    def expensive_operation():
        # 실행 시간이 로그에 기록됨
        return perform_calculation()
    ```
    """
    import time

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = end_time - start_time
        logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")

        return result

    return wrapper


def validate_input(**validations):
    """
    입력 검증 데코레이터

    Args:
        **validations: 파라미터명과 검증 함수 딕셔너리

    사용 예시:
    ```python
    def is_positive(x):
        return x > 0

    @validate_input(price=is_positive, quantity=is_positive)
    def create_order(price, quantity):
        # price와 quantity가 양수인지 검증
        return {"price": price, "quantity": quantity}
    ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # kwargs의 값 검증
            for param_name, validator in validations.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if not validator(value):
                        raise ValueError(
                            f"Validation failed for parameter '{param_name}' with value '{value}'"
                        )

            return func(*args, **kwargs)

        return wrapper
    return decorator
