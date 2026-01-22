"""
TargetSalesProduct 전용 엑셀 처리 핸들러
- 목표매출 데이터 파싱
- ID 매핑 (Brand, Channel, Product)
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from .base_handler import ExcelBaseHandler


class TargetSalesExcelHandler(ExcelBaseHandler):
    """TargetSalesProduct 전용 엑셀 처리 핸들러"""

    # 칼럼 매핑 (한글 -> 영문)
    COLUMN_MAP = {
        '목표ID': 'TARGET_ID',
        '연도': 'YEAR',
        '월': 'MONTH',
        '브랜드': 'BRAND',
        '채널명': 'CHANNEL_NAME',
        '상품코드': 'UNIQUECODE',
        '매출유형': 'SALES_TYPE',
        '목표매출액': 'TARGET_AMOUNT',
        '목표수량': 'TARGET_QUANTITY',
        '비고': 'NOTES',
    }

    # 필수 칼럼 (신규 등록용)
    REQUIRED_COLS = ['YEAR', 'MONTH', 'BRAND', 'CHANNEL_NAME', 'UNIQUECODE', 'SALES_TYPE']

    # SalesType 한글 -> 영문 매핑
    SALES_TYPE_KR_MAP = {
        '비행사': 'BASE',
        '행사': 'PROMOTION',
        'BASE': 'BASE',
        'PROMOTION': 'PROMOTION',
    }

    def __init__(self):
        super().__init__()

    def parse_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        TargetSalesProduct 1행 파싱

        Returns:
            파싱된 레코드 딕셔너리 또는 None (매핑 실패 시)
        """
        # 브랜드 매핑
        brand_name = self.safe_str(row.get('BRAND'))
        brand_id = self.get_brand_id(brand_name)

        if brand_id is None:
            return None  # 브랜드 매핑 실패 시 스킵

        # 채널 매핑
        channel_name = self.safe_str(row.get('CHANNEL_NAME'))
        channel_id = self.get_channel_id(channel_name)

        if channel_id is None:
            return None  # 채널 매핑 실패 시 스킵

        # 상품 매핑 (문자열 Uniquecode 지원)
        uniquecode = row.get('UNIQUECODE')
        product_id = self.get_product_id(uniquecode)

        if product_id is None:
            return None  # 상품 매핑 실패 시 스킵

        # SalesType 변환 (한글 -> 영문)
        sales_type = self.safe_str(row.get('SALES_TYPE'), 'BASE')
        if sales_type in self.SALES_TYPE_KR_MAP:
            sales_type = self.SALES_TYPE_KR_MAP[sales_type]

        # 연도, 월
        year = self.safe_int(row.get('YEAR'))
        month = self.safe_int(row.get('MONTH'))

        if not year or not month:
            return None  # 연도/월 필수

        return {
            'TargetID': self.safe_int(row.get('TARGET_ID')),  # 수정 시 사용
            'Year': year,
            'Month': month,
            'BrandID': brand_id,
            'ChannelID': channel_id,
            'ProductID': product_id,
            'SalesType': sales_type,
            'TargetAmount': self.safe_float(row.get('TARGET_AMOUNT')),
            'TargetQuantity': self.safe_int(row.get('TARGET_QUANTITY')),
            'Notes': self.safe_str(row.get('NOTES')),
        }

    def process_sheet(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        시트 전체 처리

        Args:
            df: DataFrame

        Returns:
            파싱된 레코드 리스트
        """
        df = self.map_columns(df, self.COLUMN_MAP)
        self.check_required_columns(df, self.REQUIRED_COLS, "목표매출")

        records = []
        for _, row in df.iterrows():
            record = self.parse_row(row)
            if record:
                records.append(record)

        return records
