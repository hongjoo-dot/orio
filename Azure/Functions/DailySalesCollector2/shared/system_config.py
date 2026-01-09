"""
SystemConfig 설정 관리 모듈
DB의 SystemConfig 테이블에서 설정값을 조회/업데이트
AdDataCollector와 동일한 패턴 (싱글톤 + 캐싱 + update_config)
"""
import pyodbc
import os
import logging
from typing import Optional, Any, Dict

# common 모듈 경로 추가
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common'))
from common.database import get_db_connection


class SystemConfig:
    """SystemConfig 설정 관리 클래스 (싱글톤 + 캐싱)"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
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
                    import json
                    self._cache[category][key] = json.loads(value) if value else None
                else:
                    self._cache[category][key] = value

                count += 1

            cursor.close()
            conn.close()

            logging.info(f"[SystemConfig] 로드 완료: {count}건")
            logging.info(f"[SystemConfig] 카테고리: {list(self._cache.keys())}")
            for cat in self._cache:
                logging.info(f"  - {cat}: {list(self._cache[cat].keys())}")

        except Exception as e:
            logging.error(f"[ERROR] SystemConfig 로드 실패: {e}", exc_info=True)

    def get(self, category: str, key: str, default: Any = None) -> Optional[Any]:
        """설정값 조회 (캐시에서)"""
        return self._cache.get(category, {}).get(key, default)

    def reload(self):
        """설정 캐시 재로드"""
        self._cache = {}
        self._load_all_configs()


# 전역 싱글톤 인스턴스
_config_instance: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """SystemConfig 인스턴스 반환 (싱글톤)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = SystemConfig()
    return _config_instance


def get_config_value(category: str, key: str, default: Any = None) -> Optional[Any]:
    """
    SystemConfig 테이블에서 설정값 조회 (레거시 호환)

    Args:
        category: 설정 카테고리 (예: 'Cafe24', 'Sabangnet')
        key: 설정 키 (예: 'ACCESS_TOKEN', 'AUTH_KEY')
        default: 기본값

    Returns:
        설정값
    """
    config = get_config()
    return config.get(category, key, default)


def update_config(category: str, key: str, value: str, updated_by: str = 'AzureFunction'):
    """
    SystemConfig 테이블의 설정값 업데이트
    변경 이력도 SystemConfigHistory에 기록됨

    Args:
        category: 설정 카테고리
        key: 설정 키
        value: 새로운 값
        updated_by: 변경자 (기본값: AzureFunction)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 기존 값 조회
        cursor.execute("""
            SELECT ConfigID, ConfigValue
            FROM [dbo].[SystemConfig]
            WHERE Category = ? AND ConfigKey = ?
        """, category, key)

        row = cursor.fetchone()

        if row:
            config_id, old_value = row[0], row[1]

            # 값이 동일하면 스킵
            if old_value == value:
                logging.info(f"[SystemConfig] {category}.{key} - 값 동일, 스킵")
                cursor.close()
                conn.close()
                return

            # 설정값 업데이트
            cursor.execute("""
                UPDATE [dbo].[SystemConfig]
                SET ConfigValue = ?, UpdatedDate = GETDATE(), UpdatedBy = ?
                WHERE ConfigID = ?
            """, value, updated_by, config_id)

            # 변경 이력 기록
            cursor.execute("""
                INSERT INTO [dbo].[SystemConfigHistory]
                (ConfigID, Category, ConfigKey, OldValue, NewValue, ChangedBy)
                VALUES (?, ?, ?, ?, ?, ?)
            """, config_id, category, key, old_value, value, updated_by)

            conn.commit()
            logging.info(f"[SystemConfig] {category}.{key} 업데이트 완료")

            # 캐시도 업데이트
            global _config_instance
            if _config_instance and category in _config_instance._cache:
                _config_instance._cache[category][key] = value

        else:
            # 설정이 없으면 새로 INSERT (UPSERT 패턴)
            logging.info(f"[SystemConfig] {category}.{key} 신규 생성")
            cursor.execute("""
                INSERT INTO [dbo].[SystemConfig]
                (Category, ConfigKey, ConfigValue, DataType, Description, IsActive, CreatedDate, UpdatedDate, UpdatedBy)
                VALUES (?, ?, ?, 'string', 'Auto-created by AzureFunction', 1, GETDATE(), GETDATE(), ?)
            """, category, key, value, updated_by)

            conn.commit()
            logging.info(f"[SystemConfig] {category}.{key} INSERT 완료")

            # 캐시에도 추가
            if _config_instance:
                if category not in _config_instance._cache:
                    _config_instance._cache[category] = {}
                _config_instance._cache[category][key] = value

        cursor.close()
        conn.close()

    except Exception as e:
        logging.error(f"[ERROR] SystemConfig 업데이트 실패 ({category}.{key}): {e}")
        raise
