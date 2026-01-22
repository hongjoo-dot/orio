"""
엑셀 처리 공통 베이스 클래스
- 파일 검증
- 시트 읽기
- 칼럼 매핑 (한글 ↔ 영문)
- DB 매핑 로드 (Brand, Channel, Product 등)
- 매핑 실패 추적
"""

import pandas as pd
import io
from typing import Dict, List, Optional, Set, Any, Tuple
from fastapi import UploadFile, HTTPException
from core import get_db_cursor


class ExcelBaseHandler:
    """엑셀 업로드 공통 기능"""

    ALLOWED_EXTENSIONS = ('.xlsx', '.xls')

    def __init__(self):
        self._brand_map: Dict[str, int] = {}
        self._channel_map: Dict[str, int] = {}
        self._product_map: Dict[str, int] = {}  # Uniquecode(str) -> ProductID
        self._brand_code_map: Dict[int, str] = {}  # BrandID -> BrandCode

        # 매핑 실패 추적
        self.unmapped_brands: Set[str] = set()
        self.unmapped_channels: Set[str] = set()
        self.unmapped_products: Set[str] = set()

    def reset_unmapped(self):
        """매핑 실패 추적 초기화"""
        self.unmapped_brands = set()
        self.unmapped_channels = set()
        self.unmapped_products = set()

    def validate_file(self, file: UploadFile) -> bool:
        """파일 확장자 검증"""
        if not file.filename:
            raise HTTPException(400, "파일명이 없습니다.")

        if not file.filename.endswith(self.ALLOWED_EXTENSIONS):
            raise HTTPException(400, f"엑셀 파일({', '.join(self.ALLOWED_EXTENSIONS)})만 업로드 가능합니다.")

        return True

    async def read_file(self, file: UploadFile) -> io.BytesIO:
        """파일 읽어서 BytesIO로 반환"""
        contents = await file.read()
        return io.BytesIO(contents)

    def read_sheet(
        self,
        excel_file: io.BytesIO,
        sheet_name: str,
        required: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        특정 시트 읽기

        Args:
            excel_file: 엑셀 파일 BytesIO
            sheet_name: 시트명
            required: 필수 여부 (True면 없을 때 에러)

        Returns:
            DataFrame 또는 None (required=False이고 시트 없을 때)
        """
        try:
            excel_file.seek(0)
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            return df
        except Exception as e:
            if required:
                raise HTTPException(400, f"'{sheet_name}' 시트를 찾을 수 없습니다.")
            return None

    def map_columns(
        self,
        df: pd.DataFrame,
        column_map: Dict[str, str]
    ) -> pd.DataFrame:
        """
        칼럼명 변환 (한글 -> 영문)
        매핑에 없는 칼럼은 대문자+언더스코어로 변환
        """
        new_columns = []
        for col in df.columns:
            col_stripped = str(col).strip()
            if col_stripped in column_map:
                new_columns.append(column_map[col_stripped])
            else:
                new_columns.append(col_stripped.upper().replace(' ', '_'))

        df.columns = new_columns
        return df

    def check_required_columns(
        self,
        df: pd.DataFrame,
        required_cols: List[str],
        sheet_name: str = "시트"
    ) -> None:
        """필수 칼럼 확인"""
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise HTTPException(400, f"{sheet_name} 필수 컬럼 누락: {', '.join(missing)}")

    def load_mappings(self, load_brand: bool = True, load_channel: bool = True, load_product: bool = True):
        """
        DB 매핑 테이블 로드

        Args:
            load_brand: Brand 매핑 로드 여부
            load_channel: Channel 매핑 로드 여부
            load_product: Product 매핑 로드 여부
        """
        with get_db_cursor(commit=False) as cursor:
            if load_brand:
                cursor.execute("SELECT Name, BrandID, BrandCode FROM [dbo].[Brand]")
                for row in cursor.fetchall():
                    self._brand_map[row[0]] = row[1]  # Name -> BrandID
                    if row[2]:  # BrandCode가 있으면
                        self._brand_code_map[row[1]] = row[2]  # BrandID -> BrandCode

            if load_channel:
                cursor.execute("SELECT Name, ChannelID FROM [dbo].[Channel]")
                self._channel_map = {row[0]: row[1] for row in cursor.fetchall()}

            if load_product:
                cursor.execute("SELECT Uniquecode, ProductID FROM [dbo].[Product]")
                self._product_map = {
                    str(row[0]): row[1] for row in cursor.fetchall() if row[0] is not None
                }

    def get_brand_id(self, brand_name: Optional[str]) -> Optional[int]:
        """브랜드명 -> BrandID 매핑"""
        if not brand_name:
            return None

        brand_name = str(brand_name).strip()
        brand_id = self._brand_map.get(brand_name)

        if brand_id is None:
            self.unmapped_brands.add(brand_name)

        return brand_id

    def get_brand_code(self, brand_id: int) -> Optional[str]:
        """BrandID -> BrandCode 매핑"""
        return self._brand_code_map.get(brand_id)

    def get_channel_id(self, channel_name: Optional[str]) -> Optional[int]:
        """채널명 -> ChannelID 매핑"""
        if not channel_name:
            return None

        channel_name = str(channel_name).strip()
        channel_id = self._channel_map.get(channel_name)

        if channel_id is None:
            self.unmapped_channels.add(channel_name)

        return channel_id

    def get_product_id(self, uniquecode) -> Optional[int]:
        """상품코드(Uniquecode) -> ProductID 매핑"""
        if uniquecode is None or pd.isna(uniquecode):
            return None

        uniquecode_str = str(uniquecode).strip()
        if uniquecode_str.endswith('.0'):
            uniquecode_str = uniquecode_str[:-2]

        product_id = self._product_map.get(uniquecode_str)
        if product_id is None:
            self.unmapped_products.add(uniquecode_str)

        return product_id

    def get_unmapped_summary(self) -> Dict[str, Any]:
        """매핑 실패 요약"""
        return {
            "unmapped_brands": {
                "count": len(self.unmapped_brands),
                "items": sorted(list(self.unmapped_brands))
            },
            "unmapped_channels": {
                "count": len(self.unmapped_channels),
                "items": sorted(list(self.unmapped_channels))
            },
            "unmapped_products": {
                "count": len(self.unmapped_products),
                "items": sorted(list(self.unmapped_products))
            }
        }

    @staticmethod
    def safe_str(value, default: str = None) -> Optional[str]:
        """안전한 문자열 변환"""
        if pd.isna(value):
            return default
        return str(value).strip()

    @staticmethod
    def safe_float(value, default: float = None) -> Optional[float]:
        """안전한 float 변환"""
        if pd.isna(value):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_int(value, default: int = None) -> Optional[int]:
        """안전한 int 변환"""
        if pd.isna(value):
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_date(value, format: str = '%Y-%m-%d') -> Optional[str]:
        """안전한 날짜 변환 (문자열로)"""
        if pd.isna(value):
            return None
        try:
            return pd.to_datetime(value).strftime(format)
        except Exception:
            return None
