"""
Promotion Repository
- Promotion(행사 마스터) 테이블 CRUD 작업
- PromotionProduct(행사 상품) 테이블 CRUD 작업
"""

from typing import Dict, Any, Optional, List
from core import BaseRepository, QueryBuilder, get_db_cursor


# PromotionType 한글 매핑
PROMOTION_TYPE_MAP = {
    'ONLINE_PRICE_DISCOUNT': '판매가할인',
    'ONLINE_COUPON': '쿠폰',
    'ONLINE_PRICE_COUPON': '판매가+쿠폰',
    'ONLINE_POST_SETTLEMENT': '정산후보정',
    'OFFLINE_WHOLESALE_DISCOUNT': '원매가할인',
    'OFFLINE_SPECIAL_PRODUCT': '기획상품',
    'OFFLINE_BUNDLE_DISCOUNT': '에누리',
}

PROMOTION_TYPE_REVERSE_MAP = {v: k for k, v in PROMOTION_TYPE_MAP.items()}

# Status 한글 매핑
STATUS_MAP = {
    'SCHEDULED': '예정',
    'ACTIVE': '진행중',
    'COMPLETED': '완료',
    'CANCELLED': '취소',
}

STATUS_REVERSE_MAP = {v: k for k, v in STATUS_MAP.items()}


class PromotionRepository(BaseRepository):
    """Promotion(행사 마스터) 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[Promotion]", id_column="PromotionID")

    def get_select_query(self) -> str:
        """Promotion 조회 쿼리 (Brand 조인 포함)"""
        return """
            SELECT
                p.PromotionID, p.PromotionName, p.PromotionType,
                p.StartDate, p.EndDate, p.Status,
                p.BrandID, b.Name as BrandName,
                p.ChannelID, p.ChannelName, p.CommissionRate,
                p.DiscountOwner, p.CompanyShare, p.ChannelShare,
                p.TargetSalesAmount, p.TargetQuantity,
                p.Notes, p.CreatedDate, p.UpdatedDate
            FROM [dbo].[Promotion] p
            LEFT JOIN [dbo].[Brand] b ON p.BrandID = b.BrandID
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        promotion_type = row[2]
        status = row[5]
        return {
            "PromotionID": row[0],
            "PromotionName": row[1],
            "PromotionType": promotion_type,
            "PromotionTypeDisplay": PROMOTION_TYPE_MAP.get(promotion_type, promotion_type),
            "StartDate": row[3].strftime('%Y-%m-%d') if row[3] else None,
            "EndDate": row[4].strftime('%Y-%m-%d') if row[4] else None,
            "Status": status,
            "StatusDisplay": STATUS_MAP.get(status, status),
            "BrandID": row[6],
            "BrandName": row[7],
            "ChannelID": row[8],
            "ChannelName": row[9],
            "CommissionRate": float(row[10]) if row[10] else None,
            "DiscountOwner": row[11],
            "CompanyShare": float(row[12]) if row[12] else None,
            "ChannelShare": float(row[13]) if row[13] else None,
            "TargetSalesAmount": float(row[14]) if row[14] else 0,
            "TargetQuantity": row[15],
            "Notes": row[16],
            "CreatedDate": row[17].strftime('%Y-%m-%d %H:%M:%S') if row[17] else None,
            "UpdatedDate": row[18].strftime('%Y-%m-%d %H:%M:%S') if row[18] else None
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """
        Promotion 전용 필터 로직

        지원하는 필터:
        - promotion_type: PromotionType 완전 일치
        - status: Status 완전 일치
        - channel_name: ChannelName LIKE 검색
        - brand_id: BrandID 완전 일치
        - year: 연도 필터 (StartDate 기준)
        - start_date: StartDate >= 검색
        - end_date: EndDate <= 검색
        - search: PromotionID 또는 PromotionName 검색
        """
        if filters.get('promotion_type'):
            builder.where_equals("p.PromotionType", filters['promotion_type'])

        if filters.get('status'):
            builder.where_equals("p.Status", filters['status'])

        if filters.get('channel_name'):
            builder.where_like("p.ChannelName", filters['channel_name'])

        if filters.get('brand_id'):
            builder.where_equals("p.BrandID", filters['brand_id'])

        if filters.get('year'):
            builder.where("YEAR(p.StartDate) = ?", filters['year'])

        if filters.get('start_date'):
            builder.where("p.StartDate >= ?", filters['start_date'])

        if filters.get('end_date'):
            builder.where("p.EndDate <= ?", filters['end_date'])

        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            builder.where("(p.PromotionID LIKE ? OR p.PromotionName LIKE ?)", search_term, search_term)

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """Promotion 전용 QueryBuilder 생성 (Brand 조인 포함)"""
        builder = QueryBuilder("[dbo].[Promotion] p")

        # 조인 추가
        builder.join("[dbo].[Brand] b", "p.BrandID = b.BrandID", "LEFT JOIN")

        # SELECT 컬럼 설정
        builder.select(
            "p.PromotionID", "p.PromotionName", "p.PromotionType",
            "p.StartDate", "p.EndDate", "p.Status",
            "p.BrandID", "b.Name as BrandName",
            "p.ChannelID", "p.ChannelName", "p.CommissionRate",
            "p.DiscountOwner", "p.CompanyShare", "p.ChannelShare",
            "p.TargetSalesAmount", "p.TargetQuantity",
            "p.Notes", "p.CreatedDate", "p.UpdatedDate"
        )

        # 필터 적용
        if filters:
            self._apply_filters(builder, filters)

        return builder

    def bulk_insert(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        대량 INSERT/UPDATE 처리 (MERGE)
        """
        inserted = 0
        updated = 0

        sql = """
            MERGE INTO [dbo].[Promotion] AS target
            USING (SELECT ? AS PromotionID) AS source
            ON target.PromotionID = source.PromotionID
            WHEN MATCHED THEN
                UPDATE SET
                    PromotionName = ?,
                    PromotionType = ?,
                    StartDate = ?,
                    EndDate = ?,
                    Status = ?,
                    BrandID = ?,
                    ChannelID = ?,
                    ChannelName = ?,
                    CommissionRate = ?,
                    DiscountOwner = ?,
                    CompanyShare = ?,
                    ChannelShare = ?,
                    TargetSalesAmount = ?,
                    TargetQuantity = ?,
                    Notes = ?,
                    UpdatedDate = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (PromotionID, PromotionName, PromotionType, StartDate, EndDate, Status,
                        BrandID, ChannelID, ChannelName, CommissionRate,
                        DiscountOwner, CompanyShare, ChannelShare,
                        TargetSalesAmount, TargetQuantity, Notes, CreatedDate, UpdatedDate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            OUTPUT $action;
        """

        with get_db_cursor(commit=True) as cursor:
            for record in records:
                params = (
                    # USING
                    record['PromotionID'],
                    # UPDATE SET
                    record['PromotionName'], record.get('PromotionType'),
                    record['StartDate'], record['EndDate'], record.get('Status', 'SCHEDULED'),
                    record['BrandID'], record.get('ChannelID'), record.get('ChannelName'),
                    record.get('CommissionRate'), record.get('DiscountOwner'),
                    record.get('CompanyShare'), record.get('ChannelShare'),
                    record.get('TargetSalesAmount'), record.get('TargetQuantity'),
                    record.get('Notes'),
                    # INSERT VALUES
                    record['PromotionID'], record['PromotionName'], record.get('PromotionType'),
                    record['StartDate'], record['EndDate'], record.get('Status', 'SCHEDULED'),
                    record['BrandID'], record.get('ChannelID'), record.get('ChannelName'),
                    record.get('CommissionRate'), record.get('DiscountOwner'),
                    record.get('CompanyShare'), record.get('ChannelShare'),
                    record.get('TargetSalesAmount'), record.get('TargetQuantity'),
                    record.get('Notes')
                )
                cursor.execute(sql, params)
                result = cursor.fetchone()
                if result:
                    if result[0] == 'INSERT':
                        inserted += 1
                    else:
                        updated += 1

        return {'inserted': inserted, 'updated': updated}

    def get_distinct_channel_names(self) -> List[str]:
        """ChannelName 고유값 목록 조회"""
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT DISTINCT ChannelName
                FROM [dbo].[Promotion]
                WHERE ChannelName IS NOT NULL AND ChannelName != ''
                ORDER BY ChannelName
            """)
            return [row[0] for row in cursor.fetchall()]

    def find_by_unique_key(
        self,
        brand_id: int,
        channel_name: str,
        promotion_name: str,
        start_date: str
    ) -> Optional[Dict[str, Any]]:
        """
        유니크 키로 행사 조회 (브랜드 + 채널명 + 행사명 + 시작일)

        Args:
            brand_id: 브랜드 ID
            channel_name: 채널명
            promotion_name: 행사명
            start_date: 시작일 (YYYY-MM-DD 형식)

        Returns:
            행사 정보 또는 None
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT
                    p.PromotionID, p.PromotionName, p.PromotionType,
                    p.StartDate, p.EndDate, p.Status,
                    p.BrandID, b.Name as BrandName,
                    p.ChannelID, p.ChannelName, p.CommissionRate,
                    p.DiscountOwner, p.CompanyShare, p.ChannelShare,
                    p.TargetSalesAmount, p.TargetQuantity,
                    p.Notes, p.CreatedDate, p.UpdatedDate
                FROM [dbo].[Promotion] p
                LEFT JOIN [dbo].[Brand] b ON p.BrandID = b.BrandID
                WHERE p.BrandID = ?
                  AND p.ChannelName = ?
                  AND p.PromotionName = ?
                  AND CONVERT(DATE, p.StartDate) = CONVERT(DATE, ?)
            """, (brand_id, channel_name, promotion_name, start_date))

            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None


class PromotionProductRepository(BaseRepository):
    """PromotionProduct(행사 상품) 테이블 Repository"""

    def __init__(self):
        super().__init__(table_name="[dbo].[PromotionProduct]", id_column="PromotionProductID")

    def get_select_query(self) -> str:
        """PromotionProduct 조회 쿼리 (Product 조인 포함)"""
        return """
            SELECT
                pp.PromotionProductID, pp.PromotionID, pp.ProductID, pp.Uniquecode,
                pr.Name as ProductName,
                pp.SellingPrice, pp.PromotionPrice, pp.SupplyPrice, pp.CouponDiscountRate,
                pp.UnitCost, pp.LogisticsCost, pp.ManagementCost, pp.WarehouseCost, pp.EDICost, pp.MisCost,
                pp.TargetSalesAmount, pp.TargetQuantity,
                pp.Notes, pp.CreatedDate, pp.UpdatedDate
            FROM [dbo].[PromotionProduct] pp
            LEFT JOIN [dbo].[Product] pr ON pp.ProductID = pr.ProductID
        """

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Row를 Dictionary로 변환"""
        return {
            "PromotionProductID": row[0],
            "PromotionID": row[1],
            "ProductID": row[2],
            "Uniquecode": row[3],
            "ProductName": row[4],
            "SellingPrice": float(row[5]) if row[5] else None,
            "PromotionPrice": float(row[6]) if row[6] else None,
            "SupplyPrice": float(row[7]) if row[7] else None,
            "CouponDiscountRate": float(row[8]) if row[8] else None,
            "UnitCost": float(row[9]) if row[9] else None,
            "LogisticsCost": float(row[10]) if row[10] else None,
            "ManagementCost": float(row[11]) if row[11] else None,
            "WarehouseCost": float(row[12]) if row[12] else None,
            "EDICost": float(row[13]) if row[13] else None,
            "MisCost": float(row[14]) if row[14] else None,
            "TargetSalesAmount": float(row[15]) if row[15] else 0,
            "TargetQuantity": row[16],
            "Notes": row[17],
            "CreatedDate": row[18].strftime('%Y-%m-%d %H:%M:%S') if row[18] else None,
            "UpdatedDate": row[19].strftime('%Y-%m-%d %H:%M:%S') if row[19] else None
        }

    def _apply_filters(self, builder: QueryBuilder, filters: Dict[str, Any]) -> None:
        """PromotionProduct 전용 필터 로직"""
        if filters.get('promotion_id'):
            builder.where_equals("pp.PromotionID", filters['promotion_id'])

        if filters.get('product_id'):
            builder.where_equals("pp.ProductID", filters['product_id'])

        if filters.get('uniquecode'):
            builder.where_equals("pp.Uniquecode", filters['uniquecode'])

    def _build_query_with_filters(self, filters: Optional[Dict[str, Any]] = None) -> QueryBuilder:
        """PromotionProduct 전용 QueryBuilder 생성"""
        builder = QueryBuilder("[dbo].[PromotionProduct] pp")

        # 조인 추가
        builder.join("[dbo].[Product] pr", "pp.ProductID = pr.ProductID", "LEFT JOIN")

        # SELECT 컬럼 설정
        builder.select(
            "pp.PromotionProductID", "pp.PromotionID", "pp.ProductID", "pp.Uniquecode",
            "pr.Name as ProductName",
            "pp.SellingPrice", "pp.PromotionPrice", "pp.SupplyPrice", "pp.CouponDiscountRate",
            "pp.UnitCost", "pp.LogisticsCost", "pp.ManagementCost", "pp.WarehouseCost", "pp.EDICost", "pp.MisCost",
            "pp.TargetSalesAmount", "pp.TargetQuantity",
            "pp.Notes", "pp.CreatedDate", "pp.UpdatedDate"
        )

        # 필터 적용
        if filters:
            self._apply_filters(builder, filters)

        return builder

    def get_by_promotion_id(self, promotion_id: str) -> List[Dict[str, Any]]:
        """특정 행사의 모든 상품 조회"""
        return self.get_list(filters={'promotion_id': promotion_id}, limit=1000)['data']

    def bulk_insert(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        대량 INSERT/UPDATE 처리 (MERGE)
        """
        inserted = 0
        updated = 0

        sql = """
            MERGE INTO [dbo].[PromotionProduct] AS target
            USING (SELECT ? AS PromotionID, ? AS ProductID) AS source
            ON target.PromotionID = source.PromotionID AND target.ProductID = source.ProductID
            WHEN MATCHED THEN
                UPDATE SET
                    Uniquecode = ?,
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
                    TargetSalesAmount = ?,
                    TargetQuantity = ?,
                    Notes = ?,
                    UpdatedDate = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (PromotionID, ProductID, Uniquecode,
                        SellingPrice, PromotionPrice, SupplyPrice, CouponDiscountRate,
                        UnitCost, LogisticsCost, ManagementCost, WarehouseCost, EDICost, MisCost,
                        TargetSalesAmount, TargetQuantity, Notes, CreatedDate, UpdatedDate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            OUTPUT $action;
        """

        with get_db_cursor(commit=True) as cursor:
            for record in records:
                params = (
                    # USING
                    record['PromotionID'], record['ProductID'],
                    # UPDATE SET
                    record['Uniquecode'],
                    record.get('SellingPrice'), record.get('PromotionPrice'),
                    record.get('SupplyPrice'), record.get('CouponDiscountRate'),
                    record.get('UnitCost'), record.get('LogisticsCost'),
                    record.get('ManagementCost'), record.get('WarehouseCost'),
                    record.get('EDICost'), record.get('MisCost'),
                    record.get('TargetSalesAmount'), record.get('TargetQuantity'),
                    record.get('Notes'),
                    # INSERT VALUES
                    record['PromotionID'], record['ProductID'], record['Uniquecode'],
                    record.get('SellingPrice'), record.get('PromotionPrice'),
                    record.get('SupplyPrice'), record.get('CouponDiscountRate'),
                    record.get('UnitCost'), record.get('LogisticsCost'),
                    record.get('ManagementCost'), record.get('WarehouseCost'),
                    record.get('EDICost'), record.get('MisCost'),
                    record.get('TargetSalesAmount'), record.get('TargetQuantity'),
                    record.get('Notes')
                )
                cursor.execute(sql, params)
                result = cursor.fetchone()
                if result:
                    if result[0] == 'INSERT':
                        inserted += 1
                    else:
                        updated += 1

        return {'inserted': inserted, 'updated': updated}

    def delete_by_promotion_id(self, promotion_id: str) -> int:
        """특정 행사의 모든 상품 삭제"""
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(
                "DELETE FROM [dbo].[PromotionProduct] WHERE PromotionID = ?",
                (promotion_id,)
            )
            return cursor.rowcount
