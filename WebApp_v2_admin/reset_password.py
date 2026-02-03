import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bcrypt
from core.database import get_db_cursor

email = 'hongjoo@orio.co.kr'

# 현재 상태 확인
with get_db_cursor(commit=False) as cursor:
    cursor.execute("SELECT UserID, Email, Name, IsActive FROM [User] WHERE Email = ?", email)
    user = cursor.fetchone()
    if not user:
        print(f"'{email}' 계정을 찾을 수 없습니다.")
        sys.exit(1)
    print(f"대상 계정: {user.Name} ({user.Email}), Active: {user.IsActive}")

# 새 비밀번호 입력 및 해시
new_password = input("\n새 비밀번호 입력: ")
hash_str = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

# DB 업데이트
with get_db_cursor(commit=True) as cursor:
    cursor.execute("UPDATE [User] SET PasswordHash = ? WHERE Email = ?", hash_str, email)
    print(f"\n비밀번호가 변경되었습니다. (affected rows: {cursor.rowcount})")
