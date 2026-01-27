"""
Permission Repository - 권한 관리
- Permission: 권한 정의
- RolePermission: 역할별 권한
- UserPermission: 사용자별 개별 권한 (GRANT/DENY)
"""

from typing import Dict, Any, Optional, List, Set
from core.database import get_db_cursor


class PermissionRepository:
    """Permission 테이블 - 권한 정의 조회"""

    def get_all(self) -> List[Dict[str, Any]]:
        """모든 권한 조회"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT PermissionID, Module, Action, Name, Description
                FROM [dbo].[Permission]
                ORDER BY Module, Action
            """)
            return [{
                "PermissionID": row[0],
                "Module": row[1],
                "Action": row[2],
                "Name": row[3],
                "Description": row[4],
                "Code": f"{row[1]}:{row[2]}"
            } for row in cursor.fetchall()]

    def get_grouped_by_module(self) -> Dict[str, List[Dict[str, Any]]]:
        """모듈별 그룹화된 권한 (UI용)"""
        permissions = self.get_all()
        grouped = {}
        for perm in permissions:
            module = perm["Module"]
            if module not in grouped:
                grouped[module] = []
            grouped[module].append(perm)
        return grouped

    def get_modules(self) -> List[str]:
        """모듈 목록"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT DISTINCT Module FROM [dbo].[Permission] ORDER BY Module")
            return [row[0] for row in cursor.fetchall()]


class RolePermissionRepository:
    """RolePermission 테이블 - 역할별 권한 관리"""

    def get_role_permissions(self, role_id: int) -> List[Dict[str, Any]]:
        """역할의 권한 목록"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT p.PermissionID, p.Module, p.Action, p.Name
                FROM [dbo].[RolePermission] rp
                JOIN [dbo].[Permission] p ON rp.PermissionID = p.PermissionID
                WHERE rp.RoleID = ?
                ORDER BY p.Module, p.Action
            """, role_id)
            return [{
                "PermissionID": row[0],
                "Module": row[1],
                "Action": row[2],
                "Name": row[3],
                "Code": f"{row[1]}:{row[2]}"
            } for row in cursor.fetchall()]

    def get_role_permission_ids(self, role_id: int) -> Set[int]:
        """역할의 권한 ID Set"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT PermissionID FROM [dbo].[RolePermission] WHERE RoleID = ?",
                role_id
            )
            return {row[0] for row in cursor.fetchall()}

    def update_role_permissions(
        self,
        role_id: int,
        permission_ids: List[int],
        updated_by: Optional[int] = None
    ) -> bool:
        """역할 권한 일괄 업데이트 (기존 삭제 후 새로 할당)"""
        with get_db_cursor() as cursor:
            # 기존 삭제
            cursor.execute("DELETE FROM [dbo].[RolePermission] WHERE RoleID = ?", role_id)

            # 새로 할당
            for perm_id in permission_ids:
                cursor.execute("""
                    INSERT INTO [dbo].[RolePermission] (RoleID, PermissionID, CreatedBy)
                    VALUES (?, ?, ?)
                """, role_id, perm_id, updated_by)

            return True

    def has_permission(self, role_id: int, module: str, action: str) -> bool:
        """역할이 특정 권한을 가지고 있는지 확인"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM [dbo].[RolePermission] rp
                JOIN [dbo].[Permission] p ON rp.PermissionID = p.PermissionID
                WHERE rp.RoleID = ? AND p.Module = ? AND p.Action = ?
            """, role_id, module, action)
            return cursor.fetchone()[0] > 0


class UserPermissionRepository:
    """UserPermission 테이블 - 사용자별 개별 권한 (GRANT/DENY)"""

    def get_user_permissions(self, user_id: int) -> List[Dict[str, Any]]:
        """사용자의 개별 권한 목록"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT up.UserPermissionID, p.PermissionID, p.Module, p.Action, p.Name, up.Type
                FROM [dbo].[UserPermission] up
                JOIN [dbo].[Permission] p ON up.PermissionID = p.PermissionID
                WHERE up.UserID = ?
                ORDER BY p.Module, p.Action
            """, user_id)
            return [{
                "UserPermissionID": row[0],
                "PermissionID": row[1],
                "Module": row[2],
                "Action": row[3],
                "Name": row[4],
                "Type": row[5],
                "Code": f"{row[2]}:{row[3]}"
            } for row in cursor.fetchall()]

    def get_user_grants(self, user_id: int) -> Set[int]:
        """사용자의 추가 권한 ID Set"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT PermissionID FROM [dbo].[UserPermission] WHERE UserID = ? AND Type = 'GRANT'",
                user_id
            )
            return {row[0] for row in cursor.fetchall()}

    def get_user_denies(self, user_id: int) -> Set[int]:
        """사용자의 제외 권한 ID Set"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT PermissionID FROM [dbo].[UserPermission] WHERE UserID = ? AND Type = 'DENY'",
                user_id
            )
            return {row[0] for row in cursor.fetchall()}

    def set_user_permission(
        self,
        user_id: int,
        permission_id: int,
        perm_type: str,  # 'GRANT' or 'DENY'
        created_by: Optional[int] = None
    ) -> bool:
        """사용자 개별 권한 설정 (upsert)"""
        with get_db_cursor() as cursor:
            # 기존 삭제
            cursor.execute(
                "DELETE FROM [dbo].[UserPermission] WHERE UserID = ? AND PermissionID = ?",
                user_id, permission_id
            )
            # 새로 추가
            cursor.execute("""
                INSERT INTO [dbo].[UserPermission] (UserID, PermissionID, Type, CreatedBy)
                VALUES (?, ?, ?, ?)
            """, user_id, permission_id, perm_type, created_by)
            return True

    def remove_user_permission(self, user_id: int, permission_id: int) -> bool:
        """사용자 개별 권한 제거 (역할 기본값으로 복원)"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM [dbo].[UserPermission] WHERE UserID = ? AND PermissionID = ?",
                user_id, permission_id
            )
            return cursor.rowcount > 0

    def update_user_permissions(
        self,
        user_id: int,
        grants: List[int],
        denies: List[int],
        updated_by: Optional[int] = None
    ) -> bool:
        """사용자 개별 권한 일괄 업데이트"""
        with get_db_cursor() as cursor:
            # 기존 전체 삭제
            cursor.execute("DELETE FROM [dbo].[UserPermission] WHERE UserID = ?", user_id)

            # GRANT 추가
            for perm_id in grants:
                cursor.execute("""
                    INSERT INTO [dbo].[UserPermission] (UserID, PermissionID, Type, CreatedBy)
                    VALUES (?, ?, 'GRANT', ?)
                """, user_id, perm_id, updated_by)

            # DENY 추가
            for perm_id in denies:
                cursor.execute("""
                    INSERT INTO [dbo].[UserPermission] (UserID, PermissionID, Type, CreatedBy)
                    VALUES (?, ?, 'DENY', ?)
                """, user_id, perm_id, updated_by)

            return True


class EffectivePermissionService:
    """사용자 최종 권한 계산 (역할 권한 + 개별 권한)"""

    def __init__(self):
        self.role_perm_repo = RolePermissionRepository()
        self.user_perm_repo = UserPermissionRepository()

    def get_user_effective_permissions(self, user_id: int, role_id: int) -> Set[int]:
        """
        사용자 최종 권한 ID Set
        = 역할 권한 + 개별 GRANT - 개별 DENY
        """
        role_perms = self.role_perm_repo.get_role_permission_ids(role_id)
        user_grants = self.user_perm_repo.get_user_grants(user_id)
        user_denies = self.user_perm_repo.get_user_denies(user_id)

        return (role_perms | user_grants) - user_denies

    def check_permission(self, user_id: int, role_id: int, module: str, action: str) -> bool:
        """사용자가 특정 권한을 가지고 있는지 확인"""
        with get_db_cursor(commit=False) as cursor:
            # 권한 ID 조회
            cursor.execute(
                "SELECT PermissionID FROM [dbo].[Permission] WHERE Module = ? AND Action = ?",
                module, action
            )
            row = cursor.fetchone()
            if not row:
                return False

            perm_id = row[0]
            effective_perms = self.get_user_effective_permissions(user_id, role_id)
            return perm_id in effective_perms

    def get_user_permission_codes(self, user_id: int, role_id: int) -> Set[str]:
        """사용자 최종 권한 코드 Set (Module:Action 형태)"""
        effective_ids = self.get_user_effective_permissions(user_id, role_id)

        if not effective_ids:
            return set()

        with get_db_cursor(commit=False) as cursor:
            placeholders = ','.join(['?' for _ in effective_ids])
            cursor.execute(f"""
                SELECT Module + ':' + Action
                FROM [dbo].[Permission]
                WHERE PermissionID IN ({placeholders})
            """, *effective_ids)
            return {row[0] for row in cursor.fetchall()}


# 싱글톤 인스턴스
permission_repo = PermissionRepository()
role_permission_repo = RolePermissionRepository()
user_permission_repo = UserPermissionRepository()
effective_permission_service = EffectivePermissionService()
