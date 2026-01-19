"""
Revenue Plan 전용 엑셀 처리 핸들러
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from .base_handler import ExcelBaseHandler


class RevenuePlanExcelHandler(ExcelBaseHandler):
    """RevenuePlan 전용 엑셀 처리 핸들러"""

    # 칼럼 매핑 (한글 -> 영문) - 대소문자 무관
    COLUMN_MAP = {
        'DATE': 'DATE',
        'BRAND': 'BRAND',
        'CHANNEL': 'CHANNEL',
        'CHANNEL_DETAIL': 'CHANNEL_DETAIL',
        'PLAN_TYPE': 'PLAN_TYPE',
        'AMOUNT': 'AMOUNT',
        # 한글 대응
        '날짜': 'DATE',
        '브랜드': 'BRAND',
        '채널': 'CHANNEL',
        '채널상세': 'CHANNEL_DETAIL',
        '계획유형': 'PLAN_TYPE',
        '금액': 'AMOUNT',
    }

    REQUIRED_COLS = ['DATE', 'BRAND', 'CHANNEL', 'PLAN_TYPE', 'AMOUNT']
    VALID_PLAN_TYPES = ['TARGET', 'EXPECTED']

    def __init__(self):
        super().__init__()

    def preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터프레임 전처리"""
        # 칼럼명 대문자 정규화 후 매핑
        df.columns = [col.upper().strip() for col in df.columns]
        df = df.rename(columns=self.COLUMN_MAP)

        # 날짜 변환
        if 'DATE' in df.columns:
            df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
            # 유효하지 않은 날짜 제거
            df = df[df['DATE'].notna()]

        # PLAN_TYPE 정규화
        if 'PLAN_TYPE' in df.columns:
            df['PLAN_TYPE'] = df['PLAN_TYPE'].str.upper().str.strip()
            # 유효하지 않은 타입 제거
            df = df[df['PLAN_TYPE'].isin(self.VALID_PLAN_TYPES)]

        return df

    def parse_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """단일 행 파싱"""
        brand_name = self.safe_str(row.get('BRAND'))
        channel_name = self.safe_str(row.get('CHANNEL'))
        channel_detail = self.safe_str(row.get('CHANNEL_DETAIL'))

        brand_id = self.get_brand_id(brand_name)
        channel_id = self.get_channel_id(channel_name)

        # 필수 매핑 실패 시 스킵
        if brand_id is None or channel_id is None:
            return None

        return {
            'Date': row['DATE'],
            'BrandID': brand_id,
            'ChannelID': channel_id,
            'ChannelDetail': channel_detail,
            'PlanType': row['PLAN_TYPE'],
            'Amount': self.safe_float(row.get('AMOUNT'), 0),
        }

    def process_sheet(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """시트 전체 처리"""
        # 전처리
        df = self.preprocess_dataframe(df)

        # 필수 칼럼 확인
        self.check_required_columns(df, self.REQUIRED_COLS, "RevenuePlan")

        # 행별 파싱
        records = []
        for _, row in df.iterrows():
            record = self.parse_row(row)
            if record:
                records.append(record)

        return records
