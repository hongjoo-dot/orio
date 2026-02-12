"""
PromotionProduct Repository
- 행사 상품 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


class PromotionProductRepository(BaseRepository):
    """PromotionProduct 테이블 Repository"""

    # SELECT 컬럼 상수 (순서 변경 금지 - _row_to_dict 인덱스와 일치해야 함)
    SELECT_COLUMNS = (
        "pp.PromotionProductID", "pp.PromotionID",
        "pp.ERPCode", "pp.UniqueCode", "pp.ProductName",
        "pp.SellingPrice", "pp.PromotionPrice", "pp.SupplyPrice",
        "pp.CouponDiscountRate",
        "pp.UnitCost", "pp.LogisticsCost", "pp.ManagementCost",
        "pp.WarehouseCost", "pp.EDICost", "pp.MisCost",
        "pp.ExpectedSalesAmount", "pp.ExpectedQuantity",
        "pp.Notes",
        "pp.CreatedDate", "pp.UpdatedDate"
    )

    # JOIN 시 추가 컬럼 (행사 상품 탭에서 Promotion 정보 표시)
    JOIN_COLUMNS = (
        "p.PromotionName", "p.PromotionType",
        "p.StartDate", "p.EndDate",
        "p.BrandID", "p.BrandName",
        "p.ChannelID", "p.ChannelName",
        "p.Status"
    )

    def __init__(self):
        super().__init__(table_name="[dbo].[PromotionProduct]", id_column="PromotionProductID")

    def get_select_query(self) -> str:
        """PromotionProduct 조회 쿼리 (Promotion JOIN 포함)"""
        columns = ", ".join(self.SELECT_COLUMNS) + ", " + ", ".join(self.JOIN_COLUMNS)
        return (
            f"SELECT {columns} "
            f"FROM [dbo].[PromotionProduct] pp "
            f"JOIN [dbo].[Promotion] p ON pp.PromotionID = p.PromotionID"
        )

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환 (JOIN 컬럼 포함)"""
        return {
            "PromotionProductID": row[0],
            "PromotionID": row[1],
            "ERPCode": row[2],
            "UniqueCode": row[3],
            "ProductName": row[4],
            "SellingPrice": float(row[5]) if row[5] else 0,
            "PromotionPrice": float(row[6]) if row[6] else 0,
            "SupplyPrice": float(row[7]) if row[7] else 0,
            "CouponDiscountRate": float(row[8]) if row[8] else None,
            "UnitCost": float(row[9]) if row[9] else 0,
            "LogisticsCost": float(row[10]) if row[10] else 0,
            "ManagementCost": float(row[11]) if row[11] else 0,
            "WarehouseCost": float(row[12]) if row[12] else 0,
            "EDICost": float(row[13]) if row[13] else 0,
            "MisCost": float(row[14]) if row[14] else 0,
            "ExpectedSalesAmount": float(row[15]) if row[15] else 0,
            "ExpectedQuantity": int(row[16]) if row[16] else 0,
            "Notes": row[17],
            "CreatedDate": row[18].strftime('%Y-%m-%d %H:%M:%S') if row[18] else None,
            "UpdatedDate": row[19].strftime('%Y-%m-%d %H:%M:%S') if row[19] else None,
            # JOIN 컬럼
            "PromotionName": row[20],
            "PromotionType": row[21],
            "StartDate": row[22].strftime('%Y-%m-%d') if row[22] else None,
            "EndDate": row[23].strftime('%Y-%m-%d') if row[23] else None,
            "BrandID": row[24],
            "BrandName": row[25],
            "ChannelID": row[26],
            "ChannelName": row[27],
            "Status": row[28],
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        PromotionProduct 전용 필터 로직

        지원하는 필터:
        - promotion_id: PromotionID 정확히 매칭
        - year_month: Promotion.StartDate 기준 년월
        - brand_id: Promotion.BrandID
        - channel_id: Promotion.ChannelID
        - promotion_type: Promotion.PromotionType
        - status: Promotion.Status
        """
        if filters.get('promotion_id'):
            builder.where_equals("pp.PromotionID", filters['promotion_id'])

        if filters.get('year_month'):
            builder.where("FORMAT(p.StartDate, 'yyyy-MM') = ?", filters['year_month'])

        if filters.get('brand_id'):
            builder.where_equals("p.BrandID", filters['brand_id'])

        if filters.get('channel_id'):
            builder.where_equals("p.ChannelID", filters['channel_id'])

        if filters.get('promotion_type'):
            builder.where_equals("p.PromotionType", filters['promotion_type'])

        if filters.get('status'):
            builder.where_equals("p.Status", filters['status'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """PromotionProduct 전용 QueryBuilder 생성 (JOIN 포함)"""
        all_columns = list(self.SELECT_COLUMNS) + list(self.JOIN_COLUMNS)
        builder = QueryBuilder(
            "[dbo].[PromotionProduct] pp "
            "JOIN [dbo].[Promotion] p ON pp.PromotionID = p.PromotionID"
        )
        builder.select(*all_columns)

        if filters:
            self._apply_filters(builder, filters)

        return builder

    def bulk_upsert(self, records: List[Dict[str, Any]], batch_size: int = 1000) -> Dict[str, Any]:
        """
        일괄 INSERT/UPDATE
        - PromotionProductID가 있으면: ID 기반 UPDATE
        - PromotionProductID가 없으면: 복합키(PromotionID+UniqueCode) 중복 체크 후 INSERT

        Returns:
            Dict: {"inserted": N, "updated": M, "duplicates": [...]}
        """
        total_inserted = 0
        total_updated = 0
        duplicates = []

        # 1단계: 신규 레코드(ID 없음)에 대해 중복 체크 먼저 수행
        with get_db_cursor(commit=False) as cursor:
            for idx, record in enumerate(records):
                product_id = record.get('PromotionProductID')
                row_num = record.get('_row_num', idx + 2)

                if not product_id:
                    check_query = """
                        SELECT PromotionProductID FROM [dbo].[PromotionProduct]
                        WHERE PromotionID = ? AND UniqueCode = ?
                    """
                    cursor.execute(check_query,
                        record.get('PromotionID'),
                        record.get('UniqueCode')
                    )
                    existing = cursor.fetchone()

                    if existing:
                        duplicates.append({
                            'row': row_num,
                            'promotion_id': record.get('PromotionID'),
                            'unique_code': record.get('UniqueCode'),
                            'existing_id': existing[0]
                        })

        # 중복이 있으면 INSERT/UPDATE 하지 않고 바로 반환
        if duplicates:
            return {"inserted": 0, "updated": 0, "duplicates": duplicates}

        # 2단계: 중복이 없으면 INSERT/UPDATE 실행
        with get_db_cursor() as cursor:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]

                for record in batch:
                    product_id = record.get('PromotionProductID')

                    if product_id:
                        # ID 기반 UPDATE (가격/비용 + 예상매출/수량 + 비고)
                        update_query = """
                            UPDATE [dbo].[PromotionProduct]
                            SET ERPCode = ?,
                                ProductName = ?,
                                SellingPrice = ?,
                                PromotionPrice = ?,
                                SupplyPrice = ?,
                                CouponDiscountRate = ?,
                                UnitCost = ?,
                                LogisticsCost = ?,
                                ManagementCost = ?,
                                WarehouseCost = ?,
                                EDICost = ?,
                                MisCost = ?,
                                ExpectedSalesAmount = ?,
                                ExpectedQuantity = ?,
                                Notes = ?,
                                UpdatedDate = GETDATE()
                            WHERE PromotionProductID = ?
                        """
                        params = [
                            record.get('ERPCode'),
                            record.get('ProductName'),
                            record.get('SellingPrice'),
                            record.get('PromotionPrice'),
                            record.get('SupplyPrice'),
                            record.get('CouponDiscountRate'),
                            record.get('UnitCost'),
                            record.get('LogisticsCost'),
                            record.get('ManagementCost'),
                            record.get('WarehouseCost'),
                            record.get('EDICost'),
                            record.get('MisCost'),
                            record.get('ExpectedSalesAmount'),
                            record.get('ExpectedQuantity'),
                            record.get('Notes'),
                            product_id
                        ]
                        cursor.execute(update_query, *params)
                        if cursor.rowcount > 0:
                            total_updated += 1
                    else:
                        # 신규 INSERT
                        insert_query = """
                            INSERT INTO [dbo].[PromotionProduct]
                                (PromotionID, ERPCode, UniqueCode, ProductName,
                                 SellingPrice, PromotionPrice, SupplyPrice,
                                 CouponDiscountRate, UnitCost, LogisticsCost,
                                 ManagementCost, WarehouseCost, EDICost, MisCost,
                                 ExpectedSalesAmount, ExpectedQuantity, Notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        params = [
                            record.get('PromotionID'),
                            record.get('ERPCode'),
                            record.get('UniqueCode'),
                            record.get('ProductName'),
                            record.get('SellingPrice'),
                            record.get('PromotionPrice'),
                            record.get('SupplyPrice'),
                            record.get('CouponDiscountRate'),
                            record.get('UnitCost'),
                            record.get('LogisticsCost'),
                            record.get('ManagementCost'),
                            record.get('WarehouseCost'),
                            record.get('EDICost'),
                            record.get('MisCost'),
                            record.get('ExpectedSalesAmount'),
                            record.get('ExpectedQuantity'),
                            record.get('Notes'),
                        ]
                        cursor.execute(insert_query, *params)
                        if cursor.rowcount > 0:
                            total_inserted += 1

        return {"inserted": total_inserted, "updated": total_updated, "duplicates": []}

    def get_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        """ID 리스트로 데이터 조회"""
        if not ids:
            return []

        with get_db_cursor(commit=False) as cursor:
            placeholders = ','.join(['?' for _ in ids])
            all_columns = ", ".join(self.SELECT_COLUMNS) + ", " + ", ".join(self.JOIN_COLUMNS)
            query = f"""
                SELECT {all_columns}
                FROM [dbo].[PromotionProduct] pp
                JOIN [dbo].[Promotion] p ON pp.PromotionID = p.PromotionID
                WHERE pp.PromotionProductID IN ({placeholders})
                ORDER BY pp.PromotionID, pp.UniqueCode
            """
            cursor.execute(query, *ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_by_promotion_id(self, promotion_id: str) -> List[Dict[str, Any]]:
        """특정 행사의 전체 상품 목록 조회"""
        with get_db_cursor(commit=False) as cursor:
            all_columns = ", ".join(self.SELECT_COLUMNS) + ", " + ", ".join(self.JOIN_COLUMNS)
            query = f"""
                SELECT {all_columns}
                FROM [dbo].[PromotionProduct] pp
                JOIN [dbo].[Promotion] p ON pp.PromotionID = p.PromotionID
                WHERE pp.PromotionID = ?
                ORDER BY pp.UniqueCode
            """
            cursor.execute(query, promotion_id)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_by_promotion_ids(self, promotion_ids: List[str]) -> List[Dict[str, Any]]:
        """여러 행사의 상품 목록 조회"""
        if not promotion_ids:
            return []

        with get_db_cursor(commit=False) as cursor:
            placeholders = ','.join(['?' for _ in promotion_ids])
            all_columns = ", ".join(self.SELECT_COLUMNS) + ", " + ", ".join(self.JOIN_COLUMNS)
            query = f"""
                SELECT {all_columns}
                FROM [dbo].[PromotionProduct] pp
                JOIN [dbo].[Promotion] p ON pp.PromotionID = p.PromotionID
                WHERE pp.PromotionID IN ({placeholders})
                ORDER BY pp.PromotionID, pp.UniqueCode
            """
            cursor.execute(query, *promotion_ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def bulk_update_products(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """인라인 편집 일괄 저장 (PromotionPrice, ExpectedSalesAmount, ExpectedQuantity, Notes 업데이트)"""
        total_updated = 0

        with get_db_cursor() as cursor:
            for record in records:
                product_id = record.get('PromotionProductID')
                if not product_id:
                    continue

                query = """
                    UPDATE [dbo].[PromotionProduct]
                    SET PromotionPrice = ?,
                        ExpectedSalesAmount = ?,
                        ExpectedQuantity = ?,
                        Notes = ?,
                        UpdatedDate = GETDATE()
                    WHERE PromotionProductID = ?
                """
                cursor.execute(query,
                    float(record.get('PromotionPrice', 0) or 0),
                    float(record.get('ExpectedSalesAmount', 0) or 0),
                    int(record.get('ExpectedQuantity', 0) or 0),
                    record.get('Notes'),
                    product_id
                )
                if cursor.rowcount > 0:
                    total_updated += 1

        return {"updated": total_updated}

    def delete_by_promotion_id(self, promotion_id: str) -> int:
        """특정 행사의 전체 상품 삭제"""
        with get_db_cursor() as cursor:
            cursor.execute(
                "DELETE FROM [dbo].[PromotionProduct] WHERE PromotionID = ?",
                promotion_id
            )
            return cursor.rowcount
