"""
데이터베이스 연결 관리 모듈
- Context Manager를 활용한 자동 연결 관리
- Connection Pooling 지원
"""

import os
import pyodbc
from contextlib import contextmanager
from dotenv import load_dotenv
from typing import Generator
from pathlib import Path

# .env 파일 로드 (명시적 경로 지정)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# 데이터베이스 연결 정보
DB_CONFIG = {
    'server': os.getenv('DB_SERVER'),
    'database': os.getenv('DB_DATABASE'),
    'username': os.getenv('DB_USERNAME'),
    'password': os.getenv('DB_PASSWORD'),
    'driver': os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}')
}


def get_connection_string() -> str:
    """연결 문자열 생성"""
    return (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
    )


def get_db_connection():
    """
    기본 DB 연결 반환 (하위 호환성)

    Returns:
        pyodbc.Connection: 데이터베이스 연결 객체
    """
    return pyodbc.connect(get_connection_string(), timeout=600)  # 대용량 처리를 위해 타임아웃 600초(10분)로 증가


@contextmanager
def get_db_cursor(commit: bool = True) -> Generator:
    """
    DB 커서를 자동으로 관리하는 Context Manager

    Args:
        commit: True일 경우 자동 커밋, False일 경우 롤백만

    Yields:
        pyodbc.Cursor: 데이터베이스 커서

    Example:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM Table")
            data = cursor.fetchall()
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


@contextmanager
def get_db_transaction() -> Generator:
    """
    트랜잭션을 명시적으로 관리하는 Context Manager

    Yields:
        tuple: (connection, cursor)

    Example:
        with get_db_transaction() as (conn, cursor):
            cursor.execute("INSERT INTO Table ...")
            cursor.execute("UPDATE Table ...")
            conn.commit()  # 명시적 커밋
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield conn, cursor
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            return True, version[:100]
    except Exception as e:
        return False, str(e)
