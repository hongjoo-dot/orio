"""
보안 모듈 - 비밀번호 해시 및 JWT 토큰 관리
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# bcrypt for password hashing
import bcrypt

# JWT for token management
from jose import jwt, JWTError

# .env 파일 로드 (명시적 경로 지정)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# JWT 설정
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "orio-erp-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8  # 8시간


def hash_password(password: str) -> str:
    """
    비밀번호를 bcrypt로 해시
    
    Args:
        password: 평문 비밀번호
        
    Returns:
        str: bcrypt 해시된 비밀번호
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증
    
    Args:
        password: 평문 비밀번호
        hashed_password: 저장된 해시 비밀번호
        
    Returns:
        bool: 일치 여부
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def create_access_token(
    user_id: int,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    JWT 액세스 토큰 생성
    
    Args:
        user_id: 사용자 ID
        email: 사용자 이메일
        role: 사용자 역할
        expires_delta: 만료 시간 (기본값: 8시간)
        
    Returns:
        str: JWT 토큰
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    expire = datetime.utcnow() + expires_delta
    
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    JWT 토큰 디코딩 및 검증
    
    Args:
        token: JWT 토큰
        
    Returns:
        Dict | None: 토큰 페이로드 또는 None (유효하지 않은 경우)
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "user_id": int(payload.get("sub")),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "exp": payload.get("exp")
        }
    except JWTError:
        return None


def is_token_expired(token: str) -> bool:
    """
    토큰 만료 여부 확인
    
    Args:
        token: JWT 토큰
        
    Returns:
        bool: 만료 여부
    """
    payload = decode_token(token)
    if not payload:
        return True
    
    exp = payload.get("exp")
    if not exp:
        return True
    
    return datetime.utcnow().timestamp() > exp


# 초기 Admin 비밀번호 해시 생성 (SQL 스크립트용)
if __name__ == "__main__":
    # hongjoo 비밀번호의 해시 생성
    password = "hongjoo"
    hashed = hash_password(password)
    print(f"Password: {password}")
    print(f"Hash: {hashed}")
    print(f"\nSQL INSERT 문에서 사용하세요:")
    print(f"N'{hashed}'")
