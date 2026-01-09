"""
활동 로그 Repository - ActivityLog 테이블 CRUD
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from core.base_repository import BaseRepository
from core.database import get_db_cursor
from core.query_builder import build_insert_query


class ActivityLogRepository(BaseRepository):
    """ActivityLog 테이블 Repository"""
    
    # 행동 유형 상수
    ACTION_CREATE = "CREATE"
    ACTION_UPDATE = "UPDATE"
    ACTION_DELETE = "DELETE"
    ACTION_BULK_DELETE = "BULK_DELETE"
    ACTION_LOGIN = "LOGIN"
    ACTION_LOGOUT = "LOGOUT"
    ACTION_LOGIN_FAILED = "LOGIN_FAILED"
    ACTION_PASSWORD_CHANGE = "PASSWORD_CHANGE"
    ACTION_ROLE_CHANGE = "ROLE_CHANGE"
    
    def __init__(self):
        super().__init__(table_name="[dbo].[ActivityLog]", id_column="LogID")
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        return {
            "LogID": row[0],
            "UserID": row[1],
            "ActionType": row[2],
            "TargetTable": row[3],
            "TargetID": row[4],
            "Details": row[5],
            "IPAddress": row[6],
            "CreatedDate": row[7].isoformat() if row[7] else None
        }
    
    def _row_to_dict_with_user(self, row) -> Dict[str, Any]:
        """사용자 정보 포함 변환"""
        return {
            "LogID": row[0],
            "UserID": row[1],
            "UserName": row[2],
            "UserEmail": row[3],
            "ActionType": row[4],
            "TargetTable": row[5],
            "TargetID": row[6],
            "Details": row[7],
            "IPAddress": row[8],
            "CreatedDate": row[9].isoformat() if row[9] else None
        }
    
    def get_select_query(self) -> str:
        return """
            SELECT LogID, UserID, ActionType, TargetTable, TargetID, 
                   Details, IPAddress, CreatedDate
            FROM [dbo].[ActivityLog]
        """
    
    def log_action(
        self,
        user_id: int,
        action_type: str,
        target_table: Optional[str] = None,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> int:
        """
        활동 로그 기록
        
        Args:
            user_id: 사용자 ID
            action_type: 행동 유형 (CREATE, UPDATE, DELETE 등)
            target_table: 대상 테이블명
            target_id: 대상 레코드 ID
            details: 상세 정보 (JSON으로 저장)
            ip_address: 클라이언트 IP
            
        Returns:
            int: 생성된 로그 ID
        """
        with get_db_cursor() as cursor:
            insert_data = {
                "UserID": user_id,
                "ActionType": action_type,
                "TargetTable": target_table,
                "TargetID": str(target_id) if target_id else None,
                "Details": json.dumps(details, ensure_ascii=False) if details else None,
                "IPAddress": ip_address
            }
            
            query, params = build_insert_query("[dbo].[ActivityLog]", insert_data)
            cursor.execute(query, *params)
            
            cursor.execute("SELECT @@IDENTITY")
            return int(cursor.fetchone()[0])
    
    def get_logs_with_user(
        self,
        page: int = 1,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        활동 로그 조회 (사용자 정보 포함)
        
        Args:
            page: 페이지 번호
            limit: 페이지당 항목 수
            filters: 필터 조건
                - user_id: 특정 사용자
                - action_type: 행동 유형
                - target_table: 대상 테이블
                - date_from: 시작 날짜
                - date_to: 종료 날짜
        """
        with get_db_cursor(commit=False) as cursor:
            # WHERE 절 구성
            where_clauses = []
            params = []
            
            if filters:
                if filters.get("user_id"):
                    where_clauses.append("l.UserID = ?")
                    params.append(filters["user_id"])
                if filters.get("action_type"):
                    where_clauses.append("l.ActionType = ?")
                    params.append(filters["action_type"])
                if filters.get("target_table"):
                    where_clauses.append("l.TargetTable = ?")
                    params.append(filters["target_table"])
                if filters.get("date_from"):
                    where_clauses.append("l.CreatedDate >= ?")
                    params.append(filters["date_from"])
                if filters.get("date_to"):
                    where_clauses.append("l.CreatedDate <= ?")
                    params.append(filters["date_to"])
            
            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # COUNT 쿼리
            count_query = f"""
                SELECT COUNT(*)
                FROM [dbo].[ActivityLog] l
                {where_sql}
            """
            cursor.execute(count_query, *params)
            total = cursor.fetchone()[0]
            
            # 데이터 쿼리
            offset = (page - 1) * limit
            data_query = f"""
                SELECT l.LogID, l.UserID, u.Name as UserName, u.Email as UserEmail,
                       l.ActionType, l.TargetTable, l.TargetID, l.Details, 
                       l.IPAddress, l.CreatedDate
                FROM [dbo].[ActivityLog] l
                LEFT JOIN [dbo].[User] u ON l.UserID = u.UserID
                {where_sql}
                ORDER BY l.CreatedDate DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            cursor.execute(data_query, *params, offset, limit)
            
            data = [self._row_to_dict_with_user(row) for row in cursor.fetchall()]
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            
            return {
                "data": data,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            }
    
    def get_user_activity_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        사용자 활동 요약 (최근 N일)
        """
        with get_db_cursor(commit=False) as cursor:
            date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            query = """
                SELECT ActionType, COUNT(*) as Count
                FROM [dbo].[ActivityLog]
                WHERE UserID = ? AND CreatedDate >= ?
                GROUP BY ActionType
            """
            cursor.execute(query, user_id, date_from)
            
            summary = {}
            for row in cursor.fetchall():
                summary[row[0]] = row[1]
            
            return {
                "user_id": user_id,
                "period_days": days,
                "actions": summary
            }
    
    def get_action_types(self) -> List[str]:
        """모든 행동 유형 목록"""
        return [
            self.ACTION_CREATE,
            self.ACTION_UPDATE,
            self.ACTION_DELETE,
            self.ACTION_BULK_DELETE,
            self.ACTION_LOGIN,
            self.ACTION_LOGOUT,
            self.ACTION_LOGIN_FAILED,
            self.ACTION_PASSWORD_CHANGE,
            self.ACTION_ROLE_CHANGE
        ]
    
    def get_target_tables(self) -> List[str]:
        """로그에 기록된 테이블 목록"""
        with get_db_cursor(commit=False) as cursor:
            query = """
                SELECT DISTINCT TargetTable 
                FROM [dbo].[ActivityLog] 
                WHERE TargetTable IS NOT NULL
                ORDER BY TargetTable
            """
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]


# 싱글톤 인스턴스
activity_log_repo = ActivityLogRepository()
