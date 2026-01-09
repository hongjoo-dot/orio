import sys
import os
import logging

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared'))

from common.database import get_db_connection

def main():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT Category, ConfigKey, ConfigValue FROM SystemConfig WHERE ConfigKey = 'SLACK_WEBHOOK_URL'"
        cursor.execute(query)
        rows = cursor.fetchall()
        print("--- SLACK_WEBHOOK_URL in SystemConfig ---")
        for row in rows:
            print(f"Category: {row[0]}, Key: {row[1]}, Value: {row[2][:20]}...")
        if not rows:
            print("No SLACK_WEBHOOK_URL found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
