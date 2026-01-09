"""
데이터베이스 연결 관리
- 환경 변수에서 DB 정보 읽기
- pyodbc 연결 제공
- Azure SQL Serverless 자동 재시도 지원
"""

import os
import pyodbc
import logging
import time


def get_db_connection(max_retries: int = 3, retry_delay: int = 15):
    """
    Azure SQL Database 연결을 반환 (Serverless 자동 재시도)

    Args:
        max_retries: 최대 재시도 횟수 (기본값: 3)
        retry_delay: 재시도 간격 초 (기본값: 15)

    Returns:
        pyodbc.Connection: 데이터베이스 연결 객체
    """
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_DATABASE')};"
        f"UID={os.getenv('DB_USERNAME')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
    )

    last_error = None
    for attempt in range(max_retries):
        try:
            conn = pyodbc.connect(conn_str, timeout=60)
            if attempt > 0:
                logging.info(f"[DB] 연결 성공 (재시도 {attempt}회 후)")
            return conn
        except pyodbc.Error as e:
            last_error = e
            error_msg = str(e)
            # Serverless DB가 일시 중지된 경우 재시도
            if "not currently available" in error_msg or "40613" in error_msg:
                logging.warning(f"[DB] Serverless DB 깨우는 중... (시도 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                continue
            else:
                raise

    raise last_error


def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        logging.info(f"DB 연결 성공: {version[:100]}")
        return True, version[:100]
    except Exception as e:
        logging.error(f"DB 연결 실패: {e}")
        return False, str(e)
