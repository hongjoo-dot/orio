"""
데이터베이스 연결 관리
- 환경 변수에서 DB 정보 읽기
- pyodbc 연결 제공
- 재시도 로직 포함 (Cold Start 대응)
"""

import os
import time
import logging
import pyodbc
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

# 데이터베이스 연결 정보
DB_CONFIG = {
    'server': os.getenv('DB_SERVER'),
    'database': os.getenv('DB_DATABASE'),
    'username': os.getenv('DB_USERNAME'),
    'password': os.getenv('DB_PASSWORD'),
    'driver': os.getenv('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')
}

# 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def get_db_connection(max_retries: int = MAX_RETRIES, retry_delay: int = RETRY_DELAY_SECONDS):
    """
    Azure SQL Database 연결을 반환 (재시도 로직 포함)

    Args:
        max_retries: 최대 재시도 횟수 (기본값: 3)
        retry_delay: 재시도 간 대기 시간(초) (기본값: 5)

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
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=60;"
    )

    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            conn = pyodbc.connect(conn_str)
            if attempt > 1:
                logger.info(f"[DB] 연결 성공 (시도 {attempt}/{max_retries})")
            return conn
        except pyodbc.Error as e:
            last_exception = e
            logger.warning(f"[DB] 연결 실패 (시도 {attempt}/{max_retries}): {e}")

            if attempt < max_retries:
                logger.info(f"[DB] {retry_delay}초 후 재시도...")
                time.sleep(retry_delay)

    # 모든 재시도 실패
    logger.error(f"[DB] 연결 실패 - 모든 재시도 소진 ({max_retries}회)")
    raise last_exception


def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, version[:100]
    except Exception as e:
        return False, str(e)
