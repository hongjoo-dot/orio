"""
Promotion 전용 엑셀 처리 핸들러
- PromotionID 자동 생성
- Promotion/PromotionProduct 데이터 파싱
"""

from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from repositories.promotion_expected_repository import PromotionRepository
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

    # Promotion 시트 칼럼 매핑 (한글 -> 영문) - 기존 2시트 방식 호환
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
        '예상매출액': 'EXPECTED_SALES_AMOUNT',
        '예상수량': 'EXPECTED_QUANTITY',
        '비고': 'NOTES',
    }

    # PromotionProduct 시트 칼럼 매핑 (한글 -> 영문) - 기존 2시트 방식 호환
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
        '예상매출액': 'EXPECTED_SALES_AMOUNT',
        '예상수량': 'EXPECTED_QUANTITY',
        '비고': 'NOTES',
    }

    # 통합 시트 칼럼 매핑 (한글 -> 영문)
    UNIFIED_COL_MAP = {
        # Promotion 칼럼 (파란색)
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
        '행사비고': 'PROMOTION_NOTES',
        # PromotionProduct 칼럼 (초록색)
        '상품코드': 'UNIQUECODE',
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
        '예상매출액': 'EXPECTED_SALES_AMOUNT',
        '예상수량': 'EXPECTED_QUANTITY',
        '상품비고': 'PRODUCT_NOTES',
    }

    PROMOTION_REQUIRED_COLS = ['PROMOTION_NAME', 'START_DATE', 'END_DATE', 'BRAND']
    PRODUCT_REQUIRED_COLS = ['PROMOTION_ID', 'UNIQUECODE']
    UNIFIED_REQUIRED_COLS = ['PROMOTION_NAME', 'START_DATE', 'BRAND', 'CHANNEL_NAME', 'UNIQUECODE']

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
            'ExpectedSalesAmount': self.safe_float(row.get('EXPECTED_SALES_AMOUNT')),
            'ExpectedQuantity': self.safe_int(row.get('EXPECTED_QUANTITY')),
            'Notes': self.safe_str(row.get('NOTES')),
        }

    def parse_product_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """PromotionProduct 시트 1행 파싱"""
        promotion_id = self.safe_str(row.get('PROMOTION_ID'))
        if not promotion_id:
            return None

        uniquecode = row.get('UNIQUECODE')
        product_id = self.get_product_id(uniquecode)

        if product_id is None:
            return None  # 상품 매핑 실패 시 스킵

        # ProductID 타입 검증 (디버깅용)
        if not isinstance(product_id, int):
            print(f"   [경고] PromotionProduct 시트 ProductID 타입 오류: Uniquecode={uniquecode}, ProductID={product_id} ({type(product_id).__name__})")
            return None

        return {
            'PromotionID': promotion_id,
            'ProductID': int(product_id),  # 명시적 int 변환
            'Uniquecode': self.safe_str(uniquecode),
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
            'ExpectedSalesAmount': self.safe_float(row.get('EXPECTED_SALES_AMOUNT')),
            'ExpectedQuantity': self.safe_int(row.get('EXPECTED_QUANTITY')),
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

    def _generate_unique_key(self, brand_id: int, channel_name: str, promotion_name: str, start_date: str) -> str:
        """
        행사 유니크 키 생성
        형식: {BrandID}_{ChannelName}_{PromotionName}_{StartDate}
        """
        return f"{brand_id}_{channel_name}_{promotion_name}_{start_date}"

    def process_unified_sheet(
        self,
        df: pd.DataFrame,
        promotion_repo=None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        통합 시트 처리 (Promotion + PromotionProduct가 한 시트에 있는 경우)

        유니크 키: 브랜드 + 채널명 + 행사명 + 시작일
        - 같은 유니크 키를 가진 행들은 같은 Promotion에 속하는 Product로 처리
        - 기존 DB에 있으면 기존 PromotionID 사용, 없으면 새로 생성

        Args:
            df: 통합 시트 DataFrame
            promotion_repo: PromotionRepository 인스턴스 (기존 행사 조회용)

        Returns:
            Tuple[promotion_records, product_records]
        """
        df = self.map_columns(df, self.UNIFIED_COL_MAP)
        self.check_required_columns(df, self.UNIFIED_REQUIRED_COLS, "행사등록")

        # 유니크 키별로 그룹핑
        promotion_map = {}  # unique_key -> promotion_record
        promotion_id_map = {}  # unique_key -> PromotionID
        product_records = []

        for _, row in df.iterrows():
            # 브랜드 매핑
            brand_name = self.safe_str(row.get('BRAND'))
            brand_id = self.get_brand_id(brand_name)

            if brand_id is None:
                continue  # 브랜드 매핑 실패 시 스킵

            # 채널명
            channel_name = self.safe_str(row.get('CHANNEL_NAME'))
            if not channel_name:
                continue  # 채널명 필수

            channel_id = self.get_channel_id(channel_name)
            if channel_id is None:
                print(f"   [경고] 채널 매핑 실패: '{channel_name}' - 해당 행 스킵")
                continue  # ChannelID 필수 (NOT NULL)

            # 행사명, 시작일
            promotion_name = self.safe_str(row.get('PROMOTION_NAME'))
            start_date = self.safe_date(row.get('START_DATE'))

            if not promotion_name or not start_date:
                continue

            # 유니크 키 생성
            unique_key = self._generate_unique_key(brand_id, channel_name, promotion_name, start_date)

            # 이미 처리한 행사가 아니면 Promotion 정보 추출
            if unique_key not in promotion_map:
                # PromotionType 변환 (한글 -> 영문)
                promotion_type = self.safe_str(row.get('PROMOTION_TYPE'))
                if promotion_type and promotion_type in PROMOTION_TYPE_KR_MAP:
                    promotion_type = PROMOTION_TYPE_KR_MAP[promotion_type]

                # Status 변환 (한글 -> 영문)
                status = self.safe_str(row.get('STATUS'), 'SCHEDULED')
                if status in STATUS_KR_MAP:
                    status = STATUS_KR_MAP[status]

                # 기존 DB에서 PromotionID 조회
                promotion_id = None
                if promotion_repo:
                    existing = promotion_repo.find_by_unique_key(
                        brand_id=brand_id,
                        channel_name=channel_name,
                        promotion_name=promotion_name,
                        start_date=start_date
                    )
                    if existing:
                        promotion_id = existing['PromotionID']

                # 없으면 새로 생성
                if not promotion_id:
                    brand_code = self.get_brand_code(brand_id)
                    if brand_code and promotion_type and start_date:
                        start_date_obj = pd.to_datetime(row.get('START_DATE')).date()
                        promotion_id = generate_promotion_id(brand_code, promotion_type, start_date_obj)
                    else:
                        continue  # 자동 생성 실패 시 스킵

                promotion_id_map[unique_key] = promotion_id

                promotion_map[unique_key] = {
                    'PromotionID': promotion_id,
                    'PromotionName': promotion_name,
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
                    'ExpectedSalesAmount': None,  # 통합 시트에서는 상품별 목표로 관리
                    'ExpectedQuantity': None,
                    'Notes': self.safe_str(row.get('PROMOTION_NOTES')),
                }

            # PromotionProduct 정보 추출
            promotion_id = promotion_id_map.get(unique_key)
            if not promotion_id:
                continue

            uniquecode = row.get('UNIQUECODE')
            product_id = self.get_product_id(uniquecode)

            if product_id is None:
                continue  # 상품 매핑 실패 시 스킵

            # ProductID 타입 검증 (디버깅용)
            if not isinstance(product_id, int):
                print(f"   [경고] 통합시트 ProductID 타입 오류: Uniquecode={uniquecode}, ProductID={product_id} ({type(product_id).__name__})")
                continue

            # 최종 검증: ProductID가 확실히 int인지 확인
            if not isinstance(product_id, int):
                print(f"   [오류] 최종 검증 실패: Uniquecode={uniquecode}, ProductID={product_id} (타입: {type(product_id).__name__})")
                continue

            product_record = {
                'PromotionID': promotion_id,
                'ProductID': int(product_id),  # 명시적 int 변환
                'Uniquecode': self.safe_str(uniquecode),
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
                'ExpectedSalesAmount': self.safe_float(row.get('EXPECTED_SALES_AMOUNT')),
                'ExpectedQuantity': self.safe_int(row.get('EXPECTED_QUANTITY')),
                'Notes': self.safe_str(row.get('PRODUCT_NOTES')),
            }

            product_records.append(product_record)

        promotion_records = list(promotion_map.values())

        return promotion_records, product_records
