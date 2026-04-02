"""
SystemConfig 설정 관리 모듈
DailySalesCollector2와 동일한 패턴 (싱글톤 + 캐싱)
"""
import logging
import os
import sys
import time
from typing import Optional, Any, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common'))
from common.database import get_db_connection


class SystemConfig:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_all_configs()

    def _load_all_configs(self):
        max_retries = 3
        retry_delay = 10

        for attempt in range(max_retries):
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
                return

            except Exception as e:
                logging.error(f"[SystemConfig] 로드 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

    def get(self, category: str, key: str, default: Any = None) -> Optional[Any]:
        return self._cache.get(category, {}).get(key, default)

    def reload(self):
        self._cache = {}
        self._load_all_configs()


_config_instance: Optional[SystemConfig] = None

def get_config() -> SystemConfig:
    global _config_instance
    if _config_instance is None:
        _config_instance = SystemConfig()
    return _config_instance
