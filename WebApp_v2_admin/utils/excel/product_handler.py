from .base_handler import ExcelBaseHandler
import pandas as pd
import io
from typing import List, Dict, Any, Optional
from repositories import ProductRepository, ProductBoxRepository, BrandRepository

class ProductExcelHandler(ExcelBaseHandler):
    def __init__(self):
        super().__init__()
        self.product_repo = ProductRepository()
        self.box_repo = ProductBoxRepository()
        self.brand_repo = BrandRepository()

    def process_upload(self, file_content: bytes) -> Dict[str, Any]:
        """
        제품 엑셀 업로드 처리
        """
        # BytesIO로 변환
        excel_file = io.BytesIO(file_content)
        
        # 첫 번째 시트 읽기
        df = self.read_sheet(excel_file, sheet_name=0, required=True)
        
        # 필수 컬럼 검증
        required_columns = ['UniqueCode', 'Name', 'TypeERP', 'TypeDB', 'ERPCode', 'QuantityInBox']
        self.check_required_columns(df, required_columns)

        # 브랜드 매핑 로드
        self.load_mappings(load_brand=True, load_channel=False, load_product=False)
        
        results = {
            "total_rows": len(df),
            "inserted": 0,
            "updated": 0,
            "errors": 0,
            "warnings": self.get_unmapped_summary()
        }

        for index, row in df.iterrows():
            try:
                # 1. 브랜드 매핑
                brand_name = self.safe_str(row.get('BrandName'))
                brand_id = self.get_brand_id(brand_name)
                
                # 2. Product 데이터 준비
                product_data = {
                    "BrandID": brand_id,
                    "UniqueCode": self.safe_str(row['UniqueCode']),
                    "Name": self.safe_str(row['Name']),
                    "TypeERP": self.safe_str(row['TypeERP']),
                    "TypeDB": self.safe_str(row['TypeDB']),
                    "BaseBarcode": self.safe_str(row.get('BaseBarcode')),
                    "Barcode2": self.safe_str(row.get('Barcode2')),
                    "SabangnetCode": self.safe_str(row.get('SabangnetCode')),
                    "SabangnetUniqueCode": self.safe_str(row.get('SabangnetUniqueCode')),
                    "BundleType": self.safe_str(row.get('BundleType')),
                    "CategoryMid": self.safe_str(row.get('CategoryMid')),
                    "CategorySub": self.safe_str(row.get('CategorySub')),
                    "Status": self.safe_str(row.get('Status')),
                    "ReleaseDate": self.safe_date(row.get('ReleaseDate'))
                }

                # 3. ProductBox 데이터 준비
                box_data = {
                    "ERPCode": self.safe_str(row['ERPCode']),
                    "QuantityInBox": self.safe_int(row['QuantityInBox'], 1)
                }

                # 4. 통합 생성/수정
                existing_product = self.product_repo.get_by_unique_code(product_data['UniqueCode'])
                
                if existing_product:
                    # Update
                    self.product_repo.update(existing_product['ProductID'], product_data)
                    # Box 업데이트 로직은 복잡하므로 여기서는 생략하거나 별도 처리 필요
                    # 일단 Product 업데이트만 카운트
                    results['updated'] += 1
                else:
                    # Create
                    self.box_repo.create_with_product(product_data, box_data)
                    results['inserted'] += 1

            except Exception as e:
                print(f"Row {index} Error: {str(e)}")
                results['errors'] += 1

        # 경고 업데이트
        results['warnings'] = self.get_unmapped_summary()
        return results

    def create_template(self) -> bytes:
        """업로드용 템플릿 생성"""
        columns = [
            'BrandName', 'UniqueCode', 'Name', 'TypeERP', 'TypeDB', 
            'BaseBarcode', 'Barcode2', 'SabangnetCode', 'SabangnetUniqueCode',
            'BundleType', 'CategoryMid', 'CategorySub', 'Status', 'ReleaseDate',
            'ERPCode', 'QuantityInBox'
        ]
        df = pd.DataFrame(columns=columns)
        return self._to_excel_bytes(df)

    def export_products(self, filters: Dict[str, Any]) -> bytes:
        """제품 목록 엑셀 다운로드"""
        # Repository에서 데이터 조회 (필터 적용)
        products = self.product_repo.get_list(filters=filters, limit=100000)
        
        # DataFrame 변환
        df = pd.DataFrame(products)
        
        # 컬럼명 한글화
        rename_map = {
            'ProductID': 'ID',
            'BrandName': '브랜드',
            'Name': '제품명',
            'UniqueCode': '고유코드',
            'TypeERP': 'TypeERP',
            'TypeDB': 'TypeDB',
            'BaseBarcode': '기본바코드',
            'Barcode2': '바코드2',
            'SabangnetCode': '사방넷코드',
            'SabangnetUniqueCode': '사방넷고유코드',
            'BundleType': '번들타입',
            'CategoryMid': '중분류',
            'CategorySub': '소분류',
            'Status': '상태',
            'ReleaseDate': '출시일'
        }
        df.rename(columns=rename_map, inplace=True)
        
        return self._to_excel_bytes(df)

    def _to_excel_bytes(self, df: pd.DataFrame) -> bytes:
        """DataFrame을 엑셀 bytes로 변환"""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()
