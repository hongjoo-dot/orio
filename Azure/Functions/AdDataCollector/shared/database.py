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

# 데이터베이스 연결 정보
DB_CONFIG = {
    'server': os.getenv('DB_SERVER'),
    'database': os.getenv('DB_DATABASE'),
    'username': os.getenv('DB_USERNAME'),
    'password': os.getenv('DB_PASSWORD'),
    'driver': os.getenv('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')
}


def get_db_connection(max_retries: int = 3, retry_delay: int = 10):
    """
    Azure SQL Database 연결을 반환 (Serverless DB 자동 재시도 지원)

    Args:
        max_retries: 최대 재시도 횟수 (기본값: 3)
        retry_delay: 재시도 간격 초 (기본값: 10)

    Returns:
        pyodbc.Connection: 데이터베이스 연결 객체
    """
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"  # ODBC Driver 18 호환성 (Azure SQL 연결 시 필수)
        f"Connection Timeout=90;"  # Cold Start 대비 타임아웃 증가
    )

    last_error = None
    for attempt in range(max_retries):
        try:
            conn = pyodbc.connect(conn_str, timeout=90)
            if attempt > 0:
                logging.info(f"[DB] 연결 성공 (재시도 {attempt}회 후)")
            return conn
        except pyodbc.Error as e:
            last_error = e
            error_msg = str(e)

            # Serverless DB가 일시 중지된 경우 또는 일시적 연결 오류
            if ("not currently available" in error_msg or
                "40613" in error_msg or  # Database unavailable
                "40197" in error_msg or  # Service error
                "40501" in error_msg or  # Service busy
                "10053" in error_msg or  # Connection broken
                "10054" in error_msg):   # Connection reset

                logging.warning(f"[DB] 일시적 연결 오류 - Serverless DB 깨우는 중... (시도 {attempt + 1}/{max_retries})")
                logging.warning(f"[DB] 에러 상세: {error_msg[:200]}")

                if attempt < max_retries - 1:
                    logging.info(f"[DB] {retry_delay}초 후 재시도...")
                    time.sleep(retry_delay)
                    continue
            else:
                # 재시도 불가능한 에러 (인증 실패 등)
                logging.error(f"[DB] 치명적 연결 오류: {error_msg}")
                raise

    # 모든 재시도 실패
    logging.error(f"[DB] 연결 최종 실패 - 모든 재시도 소진")
    raise last_error
