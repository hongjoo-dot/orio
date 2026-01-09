import pyodbc
import os
import logging
from typing import Optional, Any, Dict
from .database import get_db_connection


class SystemConfig:
    """SystemConfig 설정 관리 클래스"""

    def __init__(self):
        self._cache = {}
        self._load_all_configs()

    def _load_all_configs(self):
        """모든 설정을 캐시에 로드"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT Category, ConfigKey, ConfigValue, DataType
                FROM [dbo].[SystemConfig]
                WHERE IsActive = 1
            """)

            count = 0
            for row in cursor.fetchall():
                category, key, value, data_type = row[0], row[1], row[2], row[3]

                if category not in self._cache:
                    self._cache[category] = {}

                # 데이터 타입 변환
                if data_type == 'int':
                    self._cache[category][key] = int(value) if value else None
                elif data_type == 'bool':
                    self._cache[category][key] = value.lower() in ('true', '1', 'yes') if value else None
                elif data_type == 'json':
                    self._cache[category][key] = value
                else:
                    self._cache[category][key] = value

                count += 1

            cursor.close()
            conn.close()

            logging.info(f"[SystemConfig] 로드 완료: {count}건")
        except Exception as e:
            logging.error(f"[ERROR] SystemConfig 로드 실패: {e}")

    def get(self, category: str, key: str, default: Any = None) -> Optional[Any]:
        """설정값 조회"""
        return self._cache.get(category, {}).get(key, default)

    def reload(self):
        """설정 캐시 재로드"""
        self._cache = {}
        self._load_all_configs()


# 전역 인스턴스
_config_instance = None


def get_config() -> SystemConfig:
    """SystemConfig 인스턴스 반환 (싱글톤)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = SystemConfig()
    return _config_instance


def get_config_value(category: str, key: str, default: Any = None) -> Optional[Any]:
    """SystemConfig 테이블에서 설정값 조회"""
    config = get_config()
    return config.get(category, key, default)
