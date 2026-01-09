"""
BOM (ProductBOM) Repository
- ProductBOM 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


class BOMRepository(BaseRepository):
    """ProductBOM 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[ProductBOM]", id_column="BOMID")

    def get_select_query(self) -> str:
        """BOM 조회 쿼리"""
        return """
            SELECT BOMID, ParentProductBoxID, ChildProductBoxID, QuantityRequired
            FROM [dbo].[ProductBOM]
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "BOMID": row[0],
            "ParentProductBoxID": row[1],
            "ChildProductBoxID": row[2],
            "QuantityRequired": float(row[3]) if row[3] else 0
        }

    def get_by_id(self, bom_id: int) -> Optional[Dict[str, Any]]:
        """
        BOM 단일 조회 (ChildERPCode 포함)

        Args:
            bom_id: BOM ID

        Returns:
            Dict: BOM 정보 (ChildERPCode 포함)
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT
                    bom.BOMID,
                    bom.ParentProductBoxID,
                    bom.ChildProductBoxID,
                    bom.QuantityRequired,
                    pb_child.ERPCode as ChildERPCode,
                    p_child.Name as ChildName
                FROM [dbo].[ProductBOM] bom
                JOIN [dbo].[ProductBox] pb_child ON bom.ChildProductBoxID = pb_child.BoxID
                JOIN [dbo].[Product] p_child ON pb_child.ProductID = p_child.ProductID
                WHERE bom.BOMID = ?
            """, bom_id)

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "BOMID": row[0],
                "ParentProductBoxID": row[1],
                "ChildProductBoxID": row[2],
                "QuantityRequired": float(row[3]) if row[3] else 0,
                "ChildERPCode": row[4],
                "ChildName": row[5]
            }

    def get_parents(
        self,
        page: int = 1,
        limit: int = 20,
        parent_erp: Optional[str] = None,
        parent_name: Optional[str] = None,
        child_erp: Optional[str] = None,
        child_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        부모 제품 목록 조회 (세트 제품)

        Args:
            page: 페이지 번호
            limit: 페이지당 항목 수
            parent_erp: 부모 ERPCode 필터
            parent_name: 부모 제품명 필터
            child_erp: 자식 ERPCode 필터
            child_name: 자식 제품명 필터

        Returns:
            Dict: 페이지네이션된 부모 제품 목록
        """
        with get_db_cursor(commit=False) as cursor:
            # WHERE 조건 생성
            where_clauses = []
            params = []

            if parent_erp:
                where_clauses.append("pb.ERPCode LIKE ?")
                params.append(f"%{parent_erp}%")

            if parent_name:
                where_clauses.append("p.Name LIKE ?")
                params.append(f"%{parent_name}%")

            # 자식 필터 (서브쿼리)
            if child_erp or child_name:
                child_subquery = """
                    EXISTS (
                        SELECT 1 FROM [dbo].[ProductBOM] bom_sub
                        JOIN [dbo].[ProductBox] pb_child ON bom_sub.ChildProductBoxID = pb_child.BoxID
                        JOIN [dbo].[Product] p_child ON pb_child.ProductID = p_child.ProductID
                        WHERE bom_sub.ParentProductBoxID = pb.BoxID
                """
                if child_erp:
                    child_subquery += " AND pb_child.ERPCode LIKE ?"
                    params.append(f"%{child_erp}%")
                if child_name:
                    child_subquery += " AND p_child.Name LIKE ?"
                    params.append(f"%{child_name}%")
                child_subquery += ")"
                where_clauses.append(child_subquery)

            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # COUNT 쿼리
            count_query = f"""
                SELECT COUNT(DISTINCT pb.BoxID)
                FROM [dbo].[ProductBox] pb
                JOIN [dbo].[Product] p ON pb.ProductID = p.ProductID
                JOIN [dbo].[ProductBOM] bom ON pb.BoxID = bom.ParentProductBoxID
                {where_sql}
            """
            cursor.execute(count_query, *params)
            total = cursor.fetchone()[0]

            # 데이터 쿼리
            offset = (page - 1) * limit
            data_query = f"""
                SELECT DISTINCT
                    pb.BoxID,
                    pb.ERPCode,
                    p.Name,
                    p.BrandID,
                    (SELECT COUNT(*) FROM [dbo].[ProductBOM] WHERE ParentProductBoxID = pb.BoxID) as ChildCount,
                    (SELECT MIN(BOMID) FROM [dbo].[ProductBOM] WHERE ParentProductBoxID = pb.BoxID) as FirstBOMID
                FROM [dbo].[ProductBox] pb
                JOIN [dbo].[Product] p ON pb.ProductID = p.ProductID
                JOIN [dbo].[ProductBOM] bom ON pb.BoxID = bom.ParentProductBoxID
                {where_sql}
                ORDER BY p.Name
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            cursor.execute(data_query, *params, offset, limit)

            data = []
            for row in cursor.fetchall():
                data.append({
                    "BoxID": row[0],
                    "ERPCode": row[1],
                    "Name": row[2],
                    "BrandID": row[3],
                    "ChildCount": row[4],
                    "FirstBOMID": row[5]
                })

            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            return {
                "data": data,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            }

    def get_children(self, parent_box_id: int) -> List[Dict[str, Any]]:
        """
        특정 부모 제품의 구성품 목록 조회

        Args:
            parent_box_id: 부모 ProductBox ID

        Returns:
            List: 구성품 목록
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT
                    bom.BOMID,
                    bom.ParentProductBoxID,
                    bom.ChildProductBoxID,
                    bom.QuantityRequired,
                    pb_child.ERPCode as ChildERPCode,
                    p_child.Name as ChildName
                FROM [dbo].[ProductBOM] bom
                JOIN [dbo].[ProductBox] pb_child ON bom.ChildProductBoxID = pb_child.BoxID
                JOIN [dbo].[Product] p_child ON pb_child.ProductID = p_child.ProductID
                WHERE bom.ParentProductBoxID = ?
                ORDER BY bom.BOMID
            """, parent_box_id)

            return [{
                "BOMID": row[0],
                "ParentProductBoxID": row[1],
                "ChildProductBoxID": row[2],
                "QuantityRequired": float(row[3]) if row[3] else 0,
                "ChildERPCode": row[4],
                "ChildName": row[5]
            } for row in cursor.fetchall()]

    def create_by_erp_code(self, parent_erp: str, child_erp: str, quantity: float = 1) -> int:
        """
        ERPCode로 BOM 생성
        - 같은 부모-자식 조합이 이미 있으면 중복 방지 (에러 발생)

        Args:
            parent_erp: 부모 ERPCode
            child_erp: 자식 ERPCode
            quantity: 소요수량

        Returns:
            int: 생성된 BOMID
        """
        with get_db_cursor(commit=True) as cursor:
            # ERPCode로 BoxID와 ProductID 조회
            cursor.execute("""
                SELECT BoxID, ProductID FROM [dbo].[ProductBox] WHERE ERPCode = ?
            """, parent_erp)
            parent_row = cursor.fetchone()
            if not parent_row:
                raise ValueError(f"등록되지 않은 세트 제품입니다. 품목코드: '{parent_erp}'\n먼저 제품을 등록한 후 BOM을 추가하세요.")
            parent_box_id = parent_row[0]
            parent_product_id = parent_row[1]

            cursor.execute("""
                SELECT BoxID, ProductID FROM [dbo].[ProductBox] WHERE ERPCode = ?
            """, child_erp)
            child_row = cursor.fetchone()
            if not child_row:
                raise ValueError(f"등록되지 않은 구성품입니다. 품목코드: '{child_erp}'\n먼저 제품을 등록한 후 BOM을 추가하세요.")
            child_box_id = child_row[0]
            child_product_id = child_row[1]

            # 중복 체크: 같은 부모-자식 조합이 이미 있는지 확인
            cursor.execute("""
                SELECT BOMID FROM [dbo].[ProductBOM]
                WHERE ParentProductBoxID = ? AND ChildProductBoxID = ?
            """, parent_box_id, child_box_id)
            existing_bom = cursor.fetchone()
            if existing_bom:
                raise ValueError(f"이미 등록된 BOM입니다. 세트: '{parent_erp}', 구성품: '{child_erp}'")

            # BOM 생성 - INSERT 쿼리 직접 실행 (ParentProductID, ChildProductID, UpdatedDate 포함)
            print(f"[DEBUG] BOM 생성 시도: Parent={parent_box_id}, Child={child_box_id}, Quantity={quantity}")
            cursor.execute("""
                INSERT INTO [dbo].[ProductBOM] (
                    ParentProductBoxID,
                    ChildProductBoxID,
                    ParentProductID,
                    ChildProductID,
                    QuantityRequired,
                    UpdatedDate
                )
                VALUES (?, ?, ?, ?, ?, GETDATE())
            """, parent_box_id, child_box_id, parent_product_id, child_product_id, quantity)

            # 생성된 ID 조회
            cursor.execute("SELECT @@IDENTITY")
            bom_id = cursor.fetchone()[0]
            print(f"[DEBUG] BOM 생성 완료: BOMID={bom_id}")

            return int(bom_id)

    def update(self, id_value: Any, data: Dict[str, Any]) -> bool:
        """
        BOM 수정 (UpdatedDate 자동 갱신)

        Args:
            id_value: 수정할 BOMID
            data: 수정할 데이터 딕셔너리

        Returns:
            bool: 수정 성공 여부
        """
        # UpdatedDate 자동 추가
        data['UpdatedDate'] = 'GETDATE()'

        with get_db_cursor(commit=True) as cursor:
            # UPDATE 쿼리 생성
            set_clauses = []
            params = []

            for column, value in data.items():
                if column == 'UpdatedDate' and value == 'GETDATE()':
                    set_clauses.append(f"{column} = GETDATE()")
                else:
                    set_clauses.append(f"{column} = ?")
                    params.append(value)

            params.append(id_value)

            query = f"""
                UPDATE {self.table_name}
                SET {', '.join(set_clauses)}
                WHERE {self.id_column} = ?
            """

            cursor.execute(query, *params)
            return cursor.rowcount > 0

    def get_metadata(self) -> Dict[str, list]:
        """BOM 메타데이터 조회 (필터용 + 추가용)"""
        with get_db_cursor(commit=False) as cursor:
            metadata = {}

            # 부모 ERPCode 목록 - 모든 ProductBox에서 조회 (BOM 등록 여부 무관)
            cursor.execute("""
                SELECT DISTINCT pb.ERPCode
                FROM [dbo].[ProductBox] pb
                WHERE pb.ERPCode IS NOT NULL
                ORDER BY pb.ERPCode
            """)
            metadata['parent_erp_codes'] = [row[0] for row in cursor.fetchall()]

            # 부모 제품명 목록 - 모든 Product에서 조회
            cursor.execute("""
                SELECT DISTINCT p.Name
                FROM [dbo].[Product] p
                WHERE p.Name IS NOT NULL
                ORDER BY p.Name
            """)
            metadata['parent_names'] = [row[0] for row in cursor.fetchall()]

            # 자식 ERPCode 목록 - 모든 ProductBox에서 조회 (BOM 등록 여부 무관)
            cursor.execute("""
                SELECT DISTINCT pb.ERPCode
                FROM [dbo].[ProductBox] pb
                WHERE pb.ERPCode IS NOT NULL
                ORDER BY pb.ERPCode
            """)
            metadata['child_erp_codes'] = [row[0] for row in cursor.fetchall()]

            # 자식 제품명 목록 - 모든 Product에서 조회
            cursor.execute("""
                SELECT DISTINCT p.Name
                FROM [dbo].[Product] p
                WHERE p.Name IS NOT NULL
                ORDER BY p.Name
            """)
            metadata['child_names'] = [row[0] for row in cursor.fetchall()]

            return metadata
