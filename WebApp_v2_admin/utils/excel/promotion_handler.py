"""
Promotion 전용 엑셀 처리 핸들러
- PromotionID 자동 생성
- Promotion/PromotionProduct 데이터 파싱
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import date
import pandas as pd
from core import get_db_cursor
from .base_handler import ExcelBaseHandler


# PromotionType 코드 매핑 (영문 -> 2자리 코드)
PROMOTION_TYPE_CODE_MAP = {
    'ONLINE_PRICE_DISCOUNT': 'PD',      # 판매가할인
    'ONLINE_COUPON': 'CP',              # 쿠폰
    'ONLINE_PRICE_COUPON': 'PC',        # 판매가+쿠폰
    'ONLINE_POST_SETTLEMENT': 'PS',     # 정산후보정
    'OFFLINE_WHOLESALE_DISCOUNT': 'WD', # 원매가할인
    'OFFLINE_SPECIAL_PRODUCT': 'SP',    # 기획상품
    'OFFLINE_BUNDLE_DISCOUNT': 'BD',    # 에누리(묶음할인)
}

# 한글 -> 영문 매핑
PROMOTION_TYPE_KR_MAP = {
    '판매가할인': 'ONLINE_PRICE_DISCOUNT',
    '쿠폰': 'ONLINE_COUPON',
    '판매가+쿠폰': 'ONLINE_PRICE_COUPON',
    '정산후보정': 'ONLINE_POST_SETTLEMENT',
    '원매가할인': 'OFFLINE_WHOLESALE_DISCOUNT',
    '기획상품': 'OFFLINE_SPECIAL_PRODUCT',
    '에누리': 'OFFLINE_BUNDLE_DISCOUNT',
}

# Status 한글 -> 영문 매핑
STATUS_KR_MAP = {
    '예정': 'SCHEDULED',
    '진행중': 'ACTIVE',
    '완료': 'COMPLETED',
    '취소': 'CANCELLED',
}


def generate_promotion_id(
    brand_code: str,
    promotion_type: str,
    start_date: date
) -> str:
    """
    PromotionID 자동 생성

    형식: [브랜드 2자리][유형 2자리][년월 4자리][순번 2자리]
    예시: SDPD260201 = Scrub Daddy + 판매가할인 + 2026년02월 + 01번

    Args:
        brand_code: 브랜드 코드 (SD, FR, OR 등)
        promotion_type: 행사유형 (ONLINE_PRICE_DISCOUNT 등 영문 또는 한글)
        start_date: 행사 시작일

    Returns:
        생성된 PromotionID
    """
    # 한글 유형이면 영문으로 변환
    if promotion_type in PROMOTION_TYPE_KR_MAP:
        promotion_type = PROMOTION_TYPE_KR_MAP[promotion_type]

    # 유형 코드 가져오기
    type_code = PROMOTION_TYPE_CODE_MAP.get(promotion_type)
    if not type_code:
        raise ValueError(f"알 수 없는 행사유형: {promotion_type}")

    # 년월 추출 (YYMM)
    year_month = start_date.strftime("%y%m")

    # prefix 생성
    prefix = f"{brand_code}{type_code}{year_month}"

    # 기존 순번 조회
    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM [dbo].[Promotion] WHERE PromotionID LIKE ?",
            f"{prefix}%"
        )
        count = cursor.fetchone()[0]

    next_seq = count + 1

    # 순번 포맷 (01~99, 100~)
    if next_seq <= 99:
        seq_str = f"{next_seq:02d}"
    else:
        seq_str = str(next_seq)

    return f"{prefix}{seq_str}"


def get_next_promotion_id(
    brand_code: str,
    type_code: str,
    year_month: str
) -> str:
    """
    다음 PromotionID 조회 (직접 코드 지정)

    Args:
        brand_code: 브랜드 코드 (SD, FR, OR)
        type_code: 유형 코드 (PD, CP, PC, PS, WD, SP, BD)
        year_month: 년월 (YYMM 형식, 예: 2602)

    Returns:
        다음 PromotionID
    """
    prefix = f"{brand_code}{type_code}{year_month}"

    with get_db_cursor(commit=False) as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM [dbo].[Promotion] WHERE PromotionID LIKE ?",
            f"{prefix}%"
        )
        count = cursor.fetchone()[0]

    next_seq = count + 1

    if next_seq <= 99:
        seq_str = f"{next_seq:02d}"
    else:
        seq_str = str(next_seq)

    return f"{prefix}{seq_str}"


class PromotionExcelHandler(ExcelBaseHandler):
    """Promotion 전용 엑셀 처리 핸들러"""

    # Promotion 시트 칼럼 매핑 (한글 -> 영문)
    PROMOTION_COL_MAP = {
        '행사ID': 'PROMOTION_ID',
        '행사명': 'PROMOTION_NAME',
        '행사유형': 'PROMOTION_TYPE',
        '시작일': 'START_DATE',
        '종료일': 'END_DATE',
        '상태': 'STATUS',
        '브랜드': 'BRAND',
        '채널명': 'CHANNEL_NAME',
        '수수료율(%)': 'COMMISSION_RATE',
        '할인분담주체': 'DISCOUNT_OWNER',
        '회사분담율(%)': 'COMPANY_SHARE',
        '채널분담율(%)': 'CHANNEL_SHARE',
        '목표매출액': 'TARGET_SALES_AMOUNT',
        '목표수량': 'TARGET_QUANTITY',
        '비고': 'NOTES',
    }

    # PromotionProduct 시트 칼럼 매핑 (한글 -> 영문)
    PRODUCT_COL_MAP = {
        '행사ID': 'PROMOTION_ID',
        '상품코드': 'UNIQUECODE',
        '상품명': 'PRODUCT_NAME',
        '판매가': 'SELLING_PRICE',
        '행사가': 'PROMOTION_PRICE',
        '공급가': 'SUPPLY_PRICE',
        '쿠폰할인율(%)': 'COUPON_DISCOUNT_RATE',
        '원가': 'UNIT_COST',
        '물류비': 'LOGISTICS_COST',
        '관리비': 'MANAGEMENT_COST',
        '창고비': 'WAREHOUSE_COST',
        'EDI비용': 'EDI_COST',
        '잡손실': 'MIS_COST',
        '목표매출액': 'TARGET_SALES_AMOUNT',
        '목표수량': 'TARGET_QUANTITY',
        '비고': 'NOTES',
    }

    PROMOTION_REQUIRED_COLS = ['PROMOTION_NAME', 'START_DATE', 'END_DATE', 'BRAND']
    PRODUCT_REQUIRED_COLS = ['PROMOTION_ID', 'UNIQUECODE']

    def __init__(self):
        super().__init__()

    def parse_promotion_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Promotion 시트 1행 파싱

        행사ID가 없거나 비어있으면 자동 생성
        """
        # 브랜드 매핑
        brand_name = self.safe_str(row.get('BRAND'))
        brand_id = self.get_brand_id(brand_name)

        if brand_id is None:
            return None  # 브랜드 매핑 실패 시 스킵

        # 채널 매핑 (선택)
        channel_name = self.safe_str(row.get('CHANNEL_NAME'))
        channel_id = self.get_channel_id(channel_name) if channel_name else None

        # PromotionType 변환 (한글 -> 영문)
        promotion_type = self.safe_str(row.get('PROMOTION_TYPE'))
        if promotion_type and promotion_type in PROMOTION_TYPE_KR_MAP:
            promotion_type = PROMOTION_TYPE_KR_MAP[promotion_type]

        # Status 변환 (한글 -> 영문)
        status = self.safe_str(row.get('STATUS'), 'SCHEDULED')
        if status in STATUS_KR_MAP:
            status = STATUS_KR_MAP[status]

        # 시작일
        start_date = self.safe_date(row.get('START_DATE'))

        # PromotionID 처리
        promotion_id = self.safe_str(row.get('PROMOTION_ID'))

        # ID가 없거나 비어있으면 자동 생성
        if not promotion_id:
            brand_code = self.get_brand_code(brand_id)
            if brand_code and promotion_type and start_date:
                start_date_obj = pd.to_datetime(row.get('START_DATE')).date()
                promotion_id = generate_promotion_id(brand_code, promotion_type, start_date_obj)
            else:
                # 자동 생성 실패 시 스킵
                return None

        return {
            'PromotionID': promotion_id,
            'PromotionName': self.safe_str(row.get('PROMOTION_NAME')),
            'PromotionType': promotion_type,
            'StartDate': start_date,
            'EndDate': self.safe_date(row.get('END_DATE')),
            'Status': status,
            'BrandID': brand_id,
            'ChannelID': channel_id,
            'ChannelName': channel_name,
            'CommissionRate': self.safe_float(row.get('COMMISSION_RATE')),
            'DiscountOwner': self.safe_str(row.get('DISCOUNT_OWNER')),
            'CompanyShare': self.safe_float(row.get('COMPANY_SHARE')),
            'ChannelShare': self.safe_float(row.get('CHANNEL_SHARE')),
            'TargetSalesAmount': self.safe_float(row.get('TARGET_SALES_AMOUNT')),
            'TargetQuantity': self.safe_int(row.get('TARGET_QUANTITY')),
            'Notes': self.safe_str(row.get('NOTES')),
        }

    def parse_product_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """PromotionProduct 시트 1행 파싱"""
        promotion_id = self.safe_str(row.get('PROMOTION_ID'))
        if not promotion_id:
            return None

        uniquecode = self.safe_int(row.get('UNIQUECODE'))
        product_id = self.get_product_id(uniquecode)

        if product_id is None:
            return None  # 상품 매핑 실패 시 스킵

        return {
            'PromotionID': promotion_id,
            'ProductID': product_id,
            'Uniquecode': uniquecode,
            'SellingPrice': self.safe_float(row.get('SELLING_PRICE')),
            'PromotionPrice': self.safe_float(row.get('PROMOTION_PRICE')),
            'SupplyPrice': self.safe_float(row.get('SUPPLY_PRICE')),
            'CouponDiscountRate': self.safe_float(row.get('COUPON_DISCOUNT_RATE')),
            'UnitCost': self.safe_float(row.get('UNIT_COST')),
            'LogisticsCost': self.safe_float(row.get('LOGISTICS_COST')),
            'ManagementCost': self.safe_float(row.get('MANAGEMENT_COST')),
            'WarehouseCost': self.safe_float(row.get('WAREHOUSE_COST')),
            'EDICost': self.safe_float(row.get('EDI_COST')),
            'MisCost': self.safe_float(row.get('MIS_COST')),
            'TargetSalesAmount': self.safe_float(row.get('TARGET_SALES_AMOUNT')),
            'TargetQuantity': self.safe_int(row.get('TARGET_QUANTITY')),
            'Notes': self.safe_str(row.get('NOTES')),
        }

    def process_promotion_sheet(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Promotion 시트 전체 처리"""
        df = self.map_columns(df, self.PROMOTION_COL_MAP)
        self.check_required_columns(df, self.PROMOTION_REQUIRED_COLS, "Promotion")

        records = []
        for _, row in df.iterrows():
            record = self.parse_promotion_row(row)
            if record:
                records.append(record)

        return records

    def process_product_sheet(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """PromotionProduct 시트 전체 처리"""
        df = self.map_columns(df, self.PRODUCT_COL_MAP)
        self.check_required_columns(df, self.PRODUCT_REQUIRED_COLS, "PromotionProduct")

        records = []
        for _, row in df.iterrows():
            record = self.parse_product_row(row)
            if record:
                records.append(record)

        return records
