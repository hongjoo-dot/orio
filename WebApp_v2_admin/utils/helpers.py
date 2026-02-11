"""
공통 헬퍼 함수
- 여러 모듈에서 사용되는 유틸리티 함수
"""

import pandas as pd


def format_time_value(value, default: str = '00:00:00') -> str:
    """시간 값을 HH:MM:SS 형식으로 변환"""
    if pd.isna(value):
        return default
    if hasattr(value, 'strftime'):
        return value.strftime('%H:%M:%S')
    time_str = str(value).strip()
    if len(time_str) == 5:  # HH:MM
        return time_str + ':00'
    elif len(time_str) >= 8:  # HH:MM:SS
        return time_str[:8]
    return default


def calculate_amount_ex_vat(amount, vat_rate: float = 1.1) -> float:
    """VAT 포함 금액에서 VAT 제외 금액 계산"""
    if not amount:
        return 0
    return round(float(amount) / vat_rate, 2)
