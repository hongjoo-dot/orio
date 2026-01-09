"""
사용자 Repository - User, Role, UserRole 테이블 CRUD
"""

from typing import Dict, Any, Optional, List
from core.base_repository import BaseRepository
from core.database import get_db_cursor
from core.query_builder import build_insert_query, build_update_query


class UserRepository(BaseRepository):
    """User 테이블 Repository"""
    
    def __init__(self):
        super().__init__(table_name="[dbo].[User]", id_column="UserID")
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        return {
            "UserID": row[0],
            "Email": row[1],
            "PasswordHash": row[2],
            "Name": row[3],
            "IsActive": bool(row[4]) if row[4] is not None else True,
            "CreatedDate": row[5].isoformat() if row[5] else None,
            "LastLoginDate": row[6].isoformat() if row[6] else None,
            "CreatedBy": row[7]
        }
    
    def _row_to_dict_with_role(self, row) -> Dict[str, Any]:
        """역할 정보 포함 변환"""
        return {
            "UserID": row[0],
            "Email": row[1],
            "Name": row[2],
            "IsActive": bool(row[3]) if row[3] is not None else True,
            "CreatedDate": row[4].isoformat() if row[4] else None,
            "LastLoginDate": row[5].isoformat() if row[5] else None,
            "RoleName": row[6],
            "RoleID": row[7]
        }
    
    def get_select_query(self) -> str:
        return """
            SELECT UserID, Email, PasswordHash, Name, IsActive, 
                   CreatedDate, LastLoginDate, CreatedBy
            FROM [dbo].[User]
        """
    
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        이메일로 사용자 조회 (로그인용)
        
        Args:
            email: 사용자 이메일
            
        Returns:
            Dict | None: 사용자 정보 (비밀번호 해시 포함)
        """
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT u.UserID, u.Email, u.PasswordHash, u.Name, u.IsActive,
                       u.CreatedDate, u.LastLoginDate, r.Name as RoleName
                FROM [dbo].[User] u
                LEFT JOIN [dbo].[UserRole] ur ON u.UserID = ur.UserID
                LEFT JOIN [dbo].[Role] r ON ur.RoleID = r.RoleID
                WHERE u.Email = ?
            """
            cursor.execute(query, email)
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                "UserID": row[0],
                "Email": row[1],
                "PasswordHash": row[2],
                "Name": row[3],
                "IsActive": bool(row[4]) if row[4] is not None else True,
                "CreatedDate": row[5].isoformat() if row[5] else None,
                "LastLoginDate": row[6].isoformat() if row[6] else None,
                "RoleName": row[7] or "Viewer"  # 역할 없으면 기본 Viewer
            }
    
    def get_all_with_roles(
        self,
        page: int = 1,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        모든 사용자 조회 (역할 정보 포함)
        """
        with get_db_cursor(commit=False) as cursor:
            # WHERE 절 구성
            where_clauses = []
            params = []
            
            if filters:
                if filters.get("Email"):
                    where_clauses.append("u.Email LIKE ?")
                    params.append(f"%{filters['Email']}%")
                if filters.get("Name"):
                    where_clauses.append("u.Name LIKE ?")
                    params.append(f"%{filters['Name']}%")
                if filters.get("RoleID"):
                    where_clauses.append("ur.RoleID = ?")
                    params.append(filters["RoleID"])
                if filters.get("IsActive") is not None:
                    where_clauses.append("u.IsActive = ?")
                    params.append(1 if filters["IsActive"] else 0)
            
            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # COUNT 쿼리
            count_query = f"""
                SELECT COUNT(*)
                FROM [dbo].[User] u
                LEFT JOIN [dbo].[UserRole] ur ON u.UserID = ur.UserID
                {where_sql}
            """
            cursor.execute(count_query, *params)
            total = cursor.fetchone()[0]
            
            # 데이터 쿼리
            offset = (page - 1) * limit
            data_query = f"""
                SELECT u.UserID, u.Email, u.Name, u.IsActive, 
                       u.CreatedDate, u.LastLoginDate, r.Name as RoleName, r.RoleID
                FROM [dbo].[User] u
                LEFT JOIN [dbo].[UserRole] ur ON u.UserID = ur.UserID
                LEFT JOIN [dbo].[Role] r ON ur.RoleID = r.RoleID
                {where_sql}
                ORDER BY u.UserID DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            cursor.execute(data_query, *params, offset, limit)
            
            data = [self._row_to_dict_with_role(row) for row in cursor.fetchall()]
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            
            return {
                "data": data,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            }
    
    def update_last_login(self, user_id: int) -> bool:
        """마지막 로그인 시간 업데이트"""
        with get_db_cursor() as cursor:
            query = "UPDATE [dbo].[User] SET LastLoginDate = GETDATE() WHERE UserID = ?"
            cursor.execute(query, user_id)
            return cursor.rowcount > 0
    
    def create_with_role(self, user_data: Dict[str, Any], role_id: int, created_by: Optional[int] = None) -> int:
        """
        사용자 생성 및 역할 할당 (트랜잭션)
        """
        with get_db_cursor() as cursor:
            # 이메일 중복 체크
            cursor.execute("SELECT COUNT(*) FROM [dbo].[User] WHERE Email = ?", user_data["Email"])
            if cursor.fetchone()[0] > 0:
                raise ValueError(f"이미 존재하는 이메일입니다: {user_data['Email']}")
            
            # 사용자 생성
            insert_data = {
                "Email": user_data["Email"],
                "PasswordHash": user_data["PasswordHash"],
                "Name": user_data["Name"],
                "IsActive": user_data.get("IsActive", True),
                "CreatedBy": created_by
            }
            
            query, params = build_insert_query("[dbo].[User]", insert_data)
            cursor.execute(query, *params)
            
            cursor.execute("SELECT @@IDENTITY")
            user_id = int(cursor.fetchone()[0])
            
            # 역할 할당
            role_query = """
                INSERT INTO [dbo].[UserRole] (UserID, RoleID, AssignedBy)
                VALUES (?, ?, ?)
            """
            cursor.execute(role_query, user_id, role_id, created_by)
            
            return user_id
    
    def update_role(self, user_id: int, role_id: int, assigned_by: int) -> bool:
        """사용자 역할 변경"""
        with get_db_cursor() as cursor:
            # 기존 역할 삭제
            cursor.execute("DELETE FROM [dbo].[UserRole] WHERE UserID = ?", user_id)
            
            # 새 역할 할당
            query = """
                INSERT INTO [dbo].[UserRole] (UserID, RoleID, AssignedBy)
                VALUES (?, ?, ?)
            """
            cursor.execute(query, user_id, role_id, assigned_by)
            return True
    
    def change_password(self, user_id: int, new_password_hash: str) -> bool:
        """비밀번호 변경"""
        with get_db_cursor() as cursor:
            query = "UPDATE [dbo].[User] SET PasswordHash = ? WHERE UserID = ?"
            cursor.execute(query, new_password_hash, user_id)
            return cursor.rowcount > 0


class RoleRepository(BaseRepository):
    """Role 테이블 Repository"""
    
    def __init__(self):
        super().__init__(table_name="[dbo].[Role]", id_column="RoleID")
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        return {
            "RoleID": row[0],
            "Name": row[1],
            "Description": row[2],
            "CreatedDate": row[3].isoformat() if row[3] else None
        }
    
    def get_select_query(self) -> str:
        return "SELECT RoleID, Name, Description, CreatedDate FROM [dbo].[Role]"
    
    def get_all(self) -> List[Dict[str, Any]]:
        """모든 역할 조회"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(self.get_select_query() + " ORDER BY RoleID")
            return [self._row_to_dict(row) for row in cursor.fetchall()]


# 싱글톤 인스턴스
user_repo = UserRepository()
role_repo = RoleRepository()
