"""
SystemConfig Repository
시스템 설정 CRUD 및 변경 이력 관리
"""

from typing import List, Optional, Dict, Any
from core.base_repository import BaseRepository
from core.database import get_db_cursor


class SystemConfigRepository(BaseRepository):
    """SystemConfig 테이블 관리"""

    def __init__(self):
        super().__init__(table_name="SystemConfig", id_column="ConfigID")

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """DB Row를 Dictionary로 변환"""
        return {
            "ConfigID": row[0],
            "Category": row[1],
            "ConfigKey": row[2],
            "ConfigValue": row[3],
            "DataType": row[4],
            "Description": row[5],
            "IsActive": row[6],
            "UpdatedDate": row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None,
            "UpdatedBy": row[8]
        }

    def get_select_query(self) -> str:
        """기본 SELECT 쿼리"""
        return """
            SELECT
                ConfigID,
                Category,
                ConfigKey,
                ConfigValue,
                DataType,
                Description,
                IsActive,
                UpdatedDate,
                UpdatedBy
            FROM [dbo].[SystemConfig]
        """

    def get_all_configs(self, category: Optional[str] = None) -> List[dict]:
        """
        모든 설정 조회 (카테고리 필터 옵션)

        Args:
            category: 카테고리 필터 (None이면 전체 조회)

        Returns:
            설정 목록
        """
        with get_db_cursor(commit=False) as cursor:
            if category:
                cursor.execute("""
                    SELECT
                        ConfigID,
                        Category,
                        ConfigKey,
                        ConfigValue,
                        DataType,
                        Description,
                        IsActive,
                        UpdatedDate,
                        UpdatedBy
                    FROM [dbo].[SystemConfig]
                    WHERE Category = ?
                    ORDER BY Category, ConfigKey
                """, category)
            else:
                cursor.execute("""
                    SELECT
                        ConfigID,
                        Category,
                        ConfigKey,
                        ConfigValue,
                        DataType,
                        Description,
                        IsActive,
                        UpdatedDate,
                        UpdatedBy
                    FROM [dbo].[SystemConfig]
                    ORDER BY Category, ConfigKey
                """)

            return [
                {
                    "ConfigID": row[0],
                    "Category": row[1],
                    "ConfigKey": row[2],
                    "ConfigValue": row[3],
                    "DataType": row[4],
                    "Description": row[5],
                    "IsActive": row[6],
                    "UpdatedDate": row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None,
                    "UpdatedBy": row[8]
                }
                for row in cursor.fetchall()
            ]

    def get_config_by_id(self, config_id: int) -> Optional[dict]:
        """
        ID로 설정 조회

        Args:
            config_id: 설정 ID

        Returns:
            설정 정보 (없으면 None)
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT
                    ConfigID,
                    Category,
                    ConfigKey,
                    ConfigValue,
                    DataType,
                    Description,
                    IsActive,
                    CreatedDate,
                    UpdatedDate,
                    UpdatedBy
                FROM [dbo].[SystemConfig]
                WHERE ConfigID = ?
            """, config_id)

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "ConfigID": row[0],
                "Category": row[1],
                "ConfigKey": row[2],
                "ConfigValue": row[3],
                "DataType": row[4],
                "Description": row[5],
                "IsActive": row[6],
                "CreatedDate": row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None,
                "UpdatedDate": row[8].strftime('%Y-%m-%d %H:%M:%S') if row[8] else None,
                "UpdatedBy": row[9]
            }

    def create_config(
        self,
        category: str,
        config_key: str,
        config_value: str,
        data_type: str = "string",
        description: Optional[str] = None,
        is_active: bool = True,
        created_by: str = "ADMIN"
    ) -> int:
        """
        새 설정 추가

        Args:
            category: 카테고리
            config_key: 설정 키
            config_value: 설정 값
            data_type: 데이터 타입 (string, int, bool, json)
            description: 설명
            is_active: 활성 상태
            created_by: 생성자

        Returns:
            생성된 ConfigID
        """
        with get_db_cursor(commit=True) as cursor:
            # 중복 확인
            cursor.execute("""
                SELECT ConfigID
                FROM [dbo].[SystemConfig]
                WHERE Category = ? AND ConfigKey = ?
            """, category, config_key)

            if cursor.fetchone():
                raise ValueError(f"이미 존재하는 설정입니다: {category}.{config_key}")

            # 설정 추가
            cursor.execute("""
                INSERT INTO [dbo].[SystemConfig]
                (Category, ConfigKey, ConfigValue, DataType, Description, IsActive, CreatedDate, UpdatedDate, UpdatedBy)
                VALUES (?, ?, ?, ?, ?, ?, GETDATE(), GETDATE(), ?)
            """, category, config_key, config_value, data_type, description, is_active, created_by)

            # 생성된 ID 조회
            cursor.execute("SELECT @@IDENTITY")
            config_id = int(cursor.fetchone()[0])

            return config_id

    def get_config_by_key(self, category: str, config_key: str) -> Optional[dict]:
        """
        Category와 Key로 설정 조회

        Args:
            category: 카테고리
            config_key: 설정 키

        Returns:
            설정 정보 (없으면 None)
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT
                    ConfigID,
                    Category,
                    ConfigKey,
                    ConfigValue,
                    DataType,
                    Description,
                    IsActive,
                    UpdatedDate,
                    UpdatedBy
                FROM [dbo].[SystemConfig]
                WHERE Category = ? AND ConfigKey = ?
            """, category, config_key)

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "ConfigID": row[0],
                "Category": row[1],
                "ConfigKey": row[2],
                "ConfigValue": row[3],
                "DataType": row[4],
                "Description": row[5],
                "IsActive": row[6],
                "UpdatedDate": row[7].strftime('%Y-%m-%d %H:%M:%S') if row[7] else None,
                "UpdatedBy": row[8]
            }

    def update_config_value(self, config_id: int, new_value: str, updated_by: str = 'ADMIN') -> dict:
        """
        설정값 업데이트 (변경 이력 자동 기록)

        Args:
            config_id: 설정 ID
            new_value: 새로운 값
            updated_by: 변경자

        Returns:
            업데이트 결과
        """
        with get_db_cursor(commit=True) as cursor:
            # 기존 값 조회
            cursor.execute("""
                SELECT Category, ConfigKey, ConfigValue
                FROM [dbo].[SystemConfig]
                WHERE ConfigID = ?
            """, config_id)

            row = cursor.fetchone()
            if not row:
                raise ValueError(f"ConfigID {config_id}를 찾을 수 없습니다.")

            category, config_key, old_value = row[0], row[1], row[2]

            # 값이 동일하면 업데이트하지 않음
            if old_value == new_value:
                return {
                    "updated": False,
                    "message": "값이 동일하여 업데이트하지 않았습니다."
                }

            # 설정값 업데이트
            cursor.execute("""
                UPDATE [dbo].[SystemConfig]
                SET ConfigValue = ?,
                    UpdatedDate = GETDATE(),
                    UpdatedBy = ?
                WHERE ConfigID = ?
            """, new_value, updated_by, config_id)

            # 변경 이력 기록
            cursor.execute("""
                INSERT INTO [dbo].[SystemConfigHistory]
                (ConfigID, Category, ConfigKey, OldValue, NewValue, ChangedBy)
                VALUES (?, ?, ?, ?, ?, ?)
            """, config_id, category, config_key, old_value, new_value, updated_by)

            return {
                "updated": True,
                "config_id": config_id,
                "category": category,
                "config_key": config_key,
                "old_value": old_value,
                "new_value": new_value,
                "updated_by": updated_by
            }

    def toggle_config_status(self, config_id: int, updated_by: str = 'ADMIN') -> dict:
        """
        설정 활성/비활성 토글

        Args:
            config_id: 설정 ID
            updated_by: 변경자

        Returns:
            토글 결과
        """
        with get_db_cursor(commit=True) as cursor:
            # 현재 상태 조회
            cursor.execute("""
                SELECT IsActive
                FROM [dbo].[SystemConfig]
                WHERE ConfigID = ?
            """, config_id)

            row = cursor.fetchone()
            if not row:
                raise ValueError(f"ConfigID {config_id}를 찾을 수 없습니다.")

            current_status = row[0]
            new_status = not current_status

            # 상태 업데이트
            cursor.execute("""
                UPDATE [dbo].[SystemConfig]
                SET IsActive = ?,
                    UpdatedDate = GETDATE(),
                    UpdatedBy = ?
                WHERE ConfigID = ?
            """, new_status, updated_by, config_id)

            return {
                "toggled": True,
                "config_id": config_id,
                "new_status": new_status,
                "updated_by": updated_by
            }

    def get_config_history(self, config_id: int, limit: int = 50) -> List[dict]:
        """
        설정 변경 이력 조회

        Args:
            config_id: 설정 ID
            limit: 조회 개수

        Returns:
            변경 이력 목록
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(f"""
                SELECT TOP {limit}
                    HistoryID,
                    Category,
                    ConfigKey,
                    OldValue,
                    NewValue,
                    ChangedDate,
                    ChangedBy
                FROM [dbo].[SystemConfigHistory]
                WHERE ConfigID = ?
                ORDER BY ChangedDate DESC
            """, config_id)

            return [
                {
                    "HistoryID": row[0],
                    "Category": row[1],
                    "ConfigKey": row[2],
                    "OldValue": row[3],
                    "NewValue": row[4],
                    "ChangedDate": row[5].strftime('%Y-%m-%d %H:%M:%S') if row[5] else None,
                    "ChangedBy": row[6]
                }
                for row in cursor.fetchall()
            ]

    def delete_config(self, config_id: int, deleted_by: str = "ADMIN") -> dict:
        """
        설정 삭제

        Args:
            config_id: 설정 ID
            deleted_by: 삭제자

        Returns:
            삭제 결과
        """
        with get_db_cursor(commit=True) as cursor:
            # 존재 여부 확인
            cursor.execute("""
                SELECT Category, ConfigKey
                FROM [dbo].[SystemConfig]
                WHERE ConfigID = ?
            """, config_id)

            row = cursor.fetchone()
            if not row:
                raise ValueError(f"ConfigID {config_id}를 찾을 수 없습니다.")

            category, config_key = row[0], row[1]

            # 삭제
            cursor.execute("""
                DELETE FROM [dbo].[SystemConfig]
                WHERE ConfigID = ?
            """, config_id)

            return {
                "deleted": True,
                "config_id": config_id,
                "category": category,
                "config_key": config_key,
                "deleted_by": deleted_by
            }

    def get_categories(self) -> List[str]:
        """
        사용 가능한 모든 카테고리 조회

        Returns:
            카테고리 목록
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT DISTINCT Category
                FROM [dbo].[SystemConfig]
                ORDER BY Category
            """)

            return [row[0] for row in cursor.fetchall()]
