"""
ProductBox Repository
- ProductBox 테이블 CRUD 작업
- Product와 1:N 관계
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


class ProductBoxRepository(BaseRepository):
    """ProductBox 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[ProductBox]", id_column="BoxID")

    def get_select_query(self) -> str:
        """ProductBox 조회 쿼리"""
        return """
            SELECT BoxID, ProductID, ERPCode, QuantityInBox
            FROM [dbo].[ProductBox]
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "BoxID": row[0],
            "ProductID": row[1],
            "ERPCode": row[2],
            "QuantityInBox": row[3]
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        ProductBox 전용 필터 로직

        지원하는 필터:
        - product_id: ProductID 완전 일치
        - erp_code: ERPCode LIKE 검색
        """
        if filters.get('product_id'):
            builder.where_equals("ProductID", filters['product_id'])

        if filters.get('erp_code'):
            builder.where_like("ERPCode", filters['erp_code'])

    def get_by_product_id(self, product_id: int) -> List[Dict[str, Any]]:
        """특정 Product의 모든 Box 조회"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT BoxID, ProductID, ERPCode, QuantityInBox
                FROM [dbo].[ProductBox]
                WHERE ProductID = ?
                ORDER BY BoxID
            """, product_id)

            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_by_erp_code(self, erp_code: str) -> Optional[Dict[str, Any]]:
        """ERPCode로 Box 조회"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT BoxID, ProductID, ERPCode, QuantityInBox
                FROM [dbo].[ProductBox]
                WHERE ERPCode = ?
            """, erp_code)

            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None

    def delete_by_product_id(self, product_id: int) -> int:
        """특정 Product의 모든 Box 삭제"""
        with get_db_cursor() as cursor:
            cursor.execute("""
                DELETE FROM [dbo].[ProductBox]
                WHERE ProductID = ?
            """, product_id)

            return cursor.rowcount

    def create_with_product(self, product_data: Dict[str, Any], box_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Product와 ProductBox를 한 번에 생성 (트랜잭션)
        - 같은 UniqueCode가 있으면 기존 Product에 Box만 추가 (Merge)
        - 같은 UniqueCode가 없으면 새 Product와 Box 생성
        - ERPCode 중복은 허용하지 않음 (에러 발생)

        Args:
            product_data: Product 데이터
            box_data: ProductBox 데이터 (ERPCode, QuantityInBox)

        Returns:
            Dict: 생성된/사용된 Product와 Box 정보
        """
        from core import get_db_cursor
        from core.query_builder import build_insert_query

        with get_db_cursor(commit=True) as cursor:
            # 1. ERPCode 중복 체크 (Box는 중복 불가)
            cursor.execute("""
                SELECT BoxID FROM [dbo].[ProductBox] WHERE ERPCode = ?
            """, box_data.get('ERPCode'))
            existing_box = cursor.fetchone()
            if existing_box:
                raise ValueError(f"중복된 ERPCode입니다: {box_data.get('ERPCode')}")

            # 2. 같은 UniqueCode의 Product가 있는지 확인
            cursor.execute("""
                SELECT ProductID FROM [dbo].[Product] WHERE UniqueCode = ?
            """, product_data.get('UniqueCode'))
            existing_product = cursor.fetchone()

            if existing_product:
                # 기존 Product 사용 (Merge)
                product_id = existing_product[0]
                print(f"[DEBUG] 기존 Product 사용 (Merge): ProductID={product_id}, UniqueCode={product_data.get('UniqueCode')}")
            else:
                # 새 Product 생성
                product_query, product_params = build_insert_query("[dbo].[Product]", product_data)
                cursor.execute(product_query, *product_params)

                # Product ID 가져오기
                cursor.execute("SELECT @@IDENTITY")
                product_id = int(cursor.fetchone()[0])
                print(f"[DEBUG] 새 Product 생성: ProductID={product_id}, UniqueCode={product_data.get('UniqueCode')}")

            # 3. ProductBox 생성
            box_data['ProductID'] = product_id
            box_query, box_params = build_insert_query("[dbo].[ProductBox]", box_data)
            cursor.execute(box_query, *box_params)

            # Box ID 가져오기
            cursor.execute("SELECT @@IDENTITY")
            box_id = int(cursor.fetchone()[0])

            print(f"[DEBUG] ProductBox 생성 완료: BoxID={box_id}, ERPCode={box_data.get('ERPCode')}")

            return {
                "ProductID": product_id,
                "BoxID": box_id,
                "merged": existing_product is not None,
                **product_data,
                **box_data
            }
