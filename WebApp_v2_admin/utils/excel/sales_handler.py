"""
Sales (ERPSales) 전용 엑셀 처리 핸들러
- 대용량 배치 처리
- 다중 매핑 테이블 (Brand, Product, Channel, ChannelDetail, Warehouse)
"""

from typing import Dict, List, Optional, Any, Set
import pandas as pd
from core import get_db_cursor
from .base_handler import ExcelBaseHandler


class SalesExcelHandler(ExcelBaseHandler):
    """Sales 전용 엑셀 처리 핸들러"""

    # 칼럼 매핑 (한글 -> 영문)
    COLUMN_MAP = {
        '라인별': 'ERPIDX',
        '일자-No.': 'DateNo',
        '일자': 'DATE',
        '품목그룹1명': 'BRAND',
        '품목명': 'PRODUCT_NAME',
        '품목코드': 'ERPCode',
        'Ea': 'Quantity',
        '단가': 'UnitPrice',
        '공급가액': 'TaxableAmount',
        '거래처그룹1명': 'ChannelName',
        '거래처명': 'ChannelDetailName',
        '출하창고명': 'WarehouseName',
        '담당자명': 'Owner',
        '거래유형명': 'TransactionType',
    }

    REQUIRED_COLS = ['DATE', 'Quantity', 'UnitPrice', 'TaxableAmount']

    def __init__(self):
        super().__init__()
        self._product_erp_map: Dict[str, int] = {}  # ERPCode -> ProductID
        self._channel_detail_map: Dict[str, int] = {}  # DetailName -> ChannelDetailID
        self._warehouse_map: Dict[str, int] = {}  # WarehouseName -> WarehouseID

        # 추가 매핑 실패 추적
        self.unmapped_channel_details: Set[str] = set()
        self.unmapped_warehouses: Set[str] = set()

    def reset_unmapped(self):
        """매핑 실패 추적 초기화"""
        super().reset_unmapped()
        self.unmapped_channel_details = set()
        self.unmapped_warehouses = set()

    def load_sales_mappings(self):
        """Sales 전용 매핑 테이블 로드 (Brand, Product, Channel, ChannelDetail, Warehouse)"""
        with get_db_cursor(commit=False) as cursor:
            # Brand
            cursor.execute("SELECT Name, BrandID FROM [dbo].[Brand]")
            self._brand_map = {row[0]: row[1] for row in cursor.fetchall()}

            # Product (ERPCode 기준)
            cursor.execute("SELECT ERPCode, ProductID FROM [dbo].[ProductBox] WHERE ERPCode IS NOT NULL")
            self._product_erp_map = {row[0]: row[1] for row in cursor.fetchall()}

            # Channel
            cursor.execute("SELECT Name, ChannelID FROM [dbo].[Channel]")
            self._channel_map = {row[0]: row[1] for row in cursor.fetchall()}

            # ChannelDetail
            cursor.execute("SELECT DetailName, ChannelDetailID FROM [dbo].[ChannelDetail]")
            self._channel_detail_map = {row[0]: row[1] for row in cursor.fetchall()}

            # Warehouse
            cursor.execute("SELECT WarehouseName, WarehouseID FROM [dbo].[Warehouse]")
            self._warehouse_map = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            'brand': len(self._brand_map),
            'product': len(self._product_erp_map),
            'channel': len(self._channel_map),
            'channel_detail': len(self._channel_detail_map),
            'warehouse': len(self._warehouse_map),
        }

    def get_product_id_by_erp(self, erp_code: Optional[str]) -> Optional[int]:
        """ERPCode -> ProductID 매핑"""
        if not erp_code:
            return None

        product_id = self._product_erp_map.get(erp_code)
        if product_id is None:
            self.unmapped_products.add(erp_code)

        return product_id

    def get_channel_detail_id(self, detail_name: Optional[str]) -> Optional[int]:
        """거래처명 -> ChannelDetailID 매핑"""
        if not detail_name:
            return None

        detail_name = str(detail_name).strip()
        detail_id = self._channel_detail_map.get(detail_name)

        if detail_id is None:
            self.unmapped_channel_details.add(detail_name)

        return detail_id

    def get_warehouse_id(self, warehouse_name: Optional[str]) -> Optional[int]:
        """창고명 -> WarehouseID 매핑"""
        if not warehouse_name:
            return None

        warehouse_name = str(warehouse_name).strip()
        warehouse_id = self._warehouse_map.get(warehouse_name)

        if warehouse_id is None:
            self.unmapped_warehouses.add(warehouse_name)

        return warehouse_id

    def preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터프레임 전처리"""
        # 칼럼명 매핑
        df = df.rename(columns=self.COLUMN_MAP)

        # 날짜 변환
        if 'DATE' in df.columns:
            df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')

        # 숫자 컬럼 NULL 처리
        numeric_columns = ['Quantity', 'UnitPrice', 'TaxableAmount']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        # 문자열 컬럼 NULL 처리
        string_columns = ['BRAND', 'PRODUCT_NAME', 'ERPCode', 'ChannelName',
                          'ChannelDetailName', 'Owner', 'ERPIDX', 'DateNo',
                          'WarehouseName', 'TransactionType']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')

        return df

    def parse_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """단일 행 파싱 (매핑 포함)"""
        brand_name = row.get('BRAND') or None
        erp_code = row.get('ERPCode') or None
        channel_name = row.get('ChannelName') or None
        channel_detail_name = row.get('ChannelDetailName') or None
        warehouse_name = row.get('WarehouseName') or None

        brand_id = self.get_brand_id(brand_name) if brand_name else None
        product_id = self.get_product_id_by_erp(erp_code) if erp_code else None
        channel_id = self.get_channel_id(channel_name) if channel_name else None
        channel_detail_id = self.get_channel_detail_id(channel_detail_name) if channel_detail_name else None
        warehouse_id = self.get_warehouse_id(warehouse_name) if warehouse_name else None

        # 창고는 필수
        if warehouse_id is None and warehouse_name:
            return None  # 창고 매핑 실패 시 스킵

        return {
            'ERPIDX': row.get('ERPIDX') or None,
            'DateNo': row.get('DateNo') or None,
            'DATE': row['DATE'] if pd.notna(row.get('DATE')) else None,
            'BRAND': brand_name,
            'BrandID': brand_id,
            'ProductID': product_id,
            'PRODUCT_NAME': row.get('PRODUCT_NAME') or None,
            'ERPCode': erp_code,
            'Quantity': self.safe_float(row.get('Quantity'), 0),
            'UnitPrice': self.safe_float(row.get('UnitPrice'), 0),
            'TaxableAmount': self.safe_float(row.get('TaxableAmount'), 0),
            'ChannelID': channel_id,
            'ChannelName': channel_name,
            'ChannelDetailID': channel_detail_id,
            'ChannelDetailName': channel_detail_name,
            'Owner': row.get('Owner') or None,
            'WarehouseID': warehouse_id,
            'WarehouseName': warehouse_name,
            'TransactionType': row.get('TransactionType') or None,
        }

    def get_unmapped_summary(self) -> Dict[str, Any]:
        """매핑 실패 요약 (Sales 전용 필드 포함)"""
        summary = super().get_unmapped_summary()
        summary['unmapped_channel_details'] = {
            "count": len(self.unmapped_channel_details),
            "items": sorted(list(self.unmapped_channel_details))
        }
        summary['unmapped_warehouses'] = {
            "count": len(self.unmapped_warehouses),
            "items": sorted(list(self.unmapped_warehouses))
        }
        return summary
