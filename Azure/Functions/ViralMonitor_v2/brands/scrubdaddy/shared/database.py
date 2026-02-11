"""
데이터베이스 연결 관리
- 환경 변수에서 DB 정보 읽기
- pyodbc 연결 제공
"""

import os
import pyodbc

# 데이터베이스 연결 정보
DB_CONFIG = {
    'server': os.getenv('DB_SERVER'),
    'database': os.getenv('DB_DATABASE'),
    'username': os.getenv('DB_USERNAME'),
    'password': os.getenv('DB_PASSWORD'),
    'driver': os.getenv('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')
}


def get_db_connection():
    """
    Azure SQL Database 연결을 반환

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
        f"Connection Timeout=60;"
    )
    return pyodbc.connect(conn_str, timeout=60)
