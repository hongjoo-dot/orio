"""
Product Router
- Product CRUD API 엔드포인트
- Repository 패턴 활용
- 활동 로그 기록
"""

from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import io
from datetime import datetime
from urllib.parse import quote
from repositories import ProductRepository, ProductBoxRepository
from core.dependencies import get_current_user, get_client_ip, CurrentUser
from core import log_activity, log_delete, log_bulk_delete
from utils.excel import ProductExcelHandler

router = APIRouter(prefix="/api/products", tags=["Product"])

# Repository 인스턴스
product_repo = ProductRepository()
box_repo = ProductBoxRepository()


# Pydantic Models
class ProductCreate(BaseModel):
    BrandID: Optional[int] = None
    UniqueCode: Optional[str] = None
    Name: str
    TypeERP: str
    TypeDB: str
    BaseBarcode: Optional[str] = None
    Barcode2: Optional[str] = None
    SabangnetCode: Optional[str] = None
    SabangnetUniqueCode: Optional[str] = None
    BundleType: Optional[str] = None
    CategoryMid: Optional[str] = None
    CategorySub: Optional[str] = None
    Status: Optional[str] = None
    ReleaseDate: Optional[str] = None


class ProductUpdate(BaseModel):
    BrandID: Optional[int] = None
    UniqueCode: Optional[str] = None
    Name: Optional[str] = None
    TypeERP: Optional[str] = None
    TypeDB: Optional[str] = None
    BaseBarcode: Optional[str] = None
    Barcode2: Optional[str] = None
    SabangnetCode: Optional[str] = None
    SabangnetUniqueCode: Optional[str] = None
    BundleType: Optional[str] = None
    CategoryMid: Optional[str] = None
    CategorySub: Optional[str] = None
    Status: Optional[str] = None
    ReleaseDate: Optional[str] = None


class ProductBoxCreate(BaseModel):
    ERPCode: str
    QuantityInBox: Optional[int] = None


class ProductBoxFull(BaseModel):
    """ProductBox 전체 생성 (ProductID 포함)"""
    ProductID: int
    ERPCode: str
    QuantityInBox: Optional[int] = None


class ProductIntegratedCreate(BaseModel):
    """Product와 ProductBox 통합 생성"""
    product: ProductCreate
    box: ProductBoxCreate


class BulkDeleteRequest(BaseModel):
    ids: List[int]


# ========== CRUD 엔드포인트 ==========

@router.get("")
async def get_products(
    page: int = 1,
    limit: int = 20,
    brand: Optional[str] = None,
    unique_code: Optional[str] = None,
    name: Optional[str] = None,
    bundle_type: Optional[str] = None
):
    """
    Product 목록 조회 (페이지네이션 및 필터링)

    Query Parameters:
    - page: 페이지 번호 (기본: 1)
    - limit: 페이지당 항목 수 (기본: 20)
    - brand: 브랜드 Title 필터
    - unique_code: 고유코드 필터 (LIKE)
    - name: 상품명 필터 (LIKE)
    - bundle_type: 유형 필터
    """
    try:
        # 필터 딕셔너리 구성
        filters = {}
        if brand:
            filters['brand'] = brand
        if unique_code:
            filters['unique_code'] = unique_code
        if name:
            filters['name'] = name
        if bundle_type:
            filters['bundle_type'] = bundle_type

        # Repository를 통한 조회
        result = product_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by="p.ProductID",
            order_dir="DESC"
        )

        return result
    except Exception as e:
        raise HTTPException(500, f"제품 목록 조회 실패: {str(e)}")


@router.get("/metadata")
async def get_product_metadata():
    """
    Product 메타데이터 조회 (필터용)

    Returns:
    - bundle_types: BundleType 목록
    - unique_codes: UniqueCode 목록
    - names: 제품명 목록
    """
    try:
        return {
            "bundle_types": product_repo.get_bundle_types(),
            "unique_codes": product_repo.get_unique_codes(),
            "names": product_repo.get_product_names()
        }
    except Exception as e:
        raise HTTPException(500, f"메타데이터 조회 실패: {str(e)}")


@router.get("/download/excel")
async def download_products_excel(
    brand: Optional[str] = None,
    unique_code: Optional[str] = None,
    name: Optional[str] = None,
    bundle_type: Optional[str] = None
):
    """
    필터 조건에 맞는 Product 데이터를 엑셀로 다운로드
    
    Query Parameters:
    - brand: 브랜드 Title 필터
    - unique_code: 고유코드 필터 (LIKE)
    - name: 상품명 필터 (LIKE)
    - bundle_type: 유형 필터
    """
    try:
        # 필터 딕셔너리 구성
        filters = {}
        if brand:
            filters['brand'] = brand
        if unique_code:
            filters['unique_code'] = unique_code
        if name:
            filters['name'] = name
        if bundle_type:
            filters['bundle_type'] = bundle_type

        # 페이지네이션 없이 전체 데이터 조회 (limit을 매우 크게 설정)
        result = product_repo.get_list(
            page=1,
            limit=100000,  # 전체 조회
            filters=filters,
            order_by="p.ProductID",
            order_dir="DESC"
        )

        products = result.get('data', [])

        # 한글 칼럼명 매핑
        column_mapping = {
            'ProductID': '제품ID',
            'BrandID': '브랜드ID',
            'BrandName': '브랜드명',
            'BrandTitle': '브랜드타이틀',
            'UniqueCode': '고유코드',
            'Name': '상품명',
            'TypeERP': 'ERP유형',
            'TypeDB': 'DB유형',
            'BaseBarcode': '바코드1',
            'Barcode2': '바코드2',
            'SabangnetCode': '사방넷코드',
            'SabangnetUniqueCode': '사방넷고유코드',
            'BundleType': '단품세트구분',
            'CategoryMid': '중분류',
            'CategorySub': '소분류',
            'Status': '상태',
            'ReleaseDate': '출시일'
        }

        # DataFrame 생성
        if products:
            df = pd.DataFrame(products)
            # 칼럼 순서 정렬 및 한글명으로 변경
            ordered_columns = [
                'ProductID', 'BrandName', 'BrandTitle', 'UniqueCode', 'Name',
                'TypeERP', 'TypeDB', 'BaseBarcode', 'Barcode2',
                'SabangnetCode', 'SabangnetUniqueCode', 'BundleType',
                'CategoryMid', 'CategorySub', 'Status', 'ReleaseDate'
            ]
            # 존재하는 칼럼만 선택
            available_columns = [col for col in ordered_columns if col in df.columns]
            df = df[available_columns]
            # 한글 칼럼명으로 변경
            df.rename(columns=column_mapping, inplace=True)
        else:
            # 데이터가 없을 경우 빈 DataFrame 생성 (칼럼명만 포함)
            df = pd.DataFrame(columns=[column_mapping[col] for col in [
                'ProductID', 'BrandName', 'BrandTitle', 'UniqueCode', 'Name',
                'TypeERP', 'TypeDB', 'BaseBarcode', 'Barcode2',
                'SabangnetCode', 'SabangnetUniqueCode', 'BundleType',
                'CategoryMid', 'CategorySub', 'Status', 'ReleaseDate'
            ]])

        # 엑셀 파일 생성
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='상품목록')
            
            # 칼럼 너비 자동 조정
            worksheet = writer.sheets['상품목록']
            for i, col in enumerate(df.columns):
                max_len = max(
                    df[col].astype(str).apply(len).max() if len(df) > 0 else 0,
                    len(str(col))
                ) + 2
                worksheet.set_column(i, i, min(max_len, 50))

        output.seek(0)

        # 파일명: 상품목록_YYYYMMDD.xlsx
        today = datetime.now().strftime('%Y%m%d')
        filename = f"상품목록_{today}.xlsx"
        encoded_filename = quote(filename)

        headers = {
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"
        }

        return StreamingResponse(
            output,
            headers=headers,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        raise HTTPException(500, f"엑셀 다운로드 실패: {str(e)}")


@router.get("/{product_id}")
async def get_product(product_id: int):
    """Product 단일 조회"""
    try:
        product = product_repo.get_by_id(product_id)

        if not product:
            raise HTTPException(404, "제품을 찾을 수 없습니다")

        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"제품 조회 실패: {str(e)}")


@router.post("")
@log_activity("CREATE", "Product", id_key="ProductID")
async def create_product(
    data: ProductCreate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """Product 생성"""
    try:
        # 중복 체크 (UniqueCode)
        if data.UniqueCode and product_repo.check_duplicate("UniqueCode", data.UniqueCode):
            raise HTTPException(400, f"중복된 고유코드입니다: {data.UniqueCode}")

        # 생성
        product_id = product_repo.create(data.dict(exclude_none=True))

        return {"ProductID": product_id, "Name": data.Name, "UniqueCode": data.UniqueCode}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"제품 생성 실패: {str(e)}")


@router.post("/integrated")
@log_activity("CREATE", "Product+ProductBox", id_key="ProductID")
async def create_product_integrated(
    data: ProductIntegratedCreate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Product와 ProductBox를 한 번에 생성 (트랜잭션)

    Request Body:
    {
        "product": { ProductCreate 데이터 },
        "box": { ProductBoxCreate 데이터 }
    }
    """
    try:
        # 중복 체크
        if data.product.UniqueCode and product_repo.check_duplicate("UniqueCode", data.product.UniqueCode):
            raise HTTPException(400, f"중복된 고유코드입니다: {data.product.UniqueCode}")

        if data.box.ERPCode and box_repo.check_duplicate("ERPCode", data.box.ERPCode):
            raise HTTPException(400, f"중복된 ERP 코드입니다: {data.box.ERPCode}")

        # 통합 생성
        result = box_repo.create_with_product(
            product_data=data.product.dict(exclude_none=True),
            box_data=data.box.dict(exclude_none=True)
        )

        # 로깅용 정보 추가
        result["Name"] = data.product.Name
        result["ERPCode"] = data.box.ERPCode

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"통합 생성 실패: {str(e)}")


@router.put("/{product_id}")
@log_activity("UPDATE", "Product", id_key="ProductID")
async def update_product(
    product_id: int,
    data: ProductUpdate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """Product 수정"""
    try:
        # 존재 여부 확인
        if not product_repo.exists(product_id):
            raise HTTPException(404, "제품을 찾을 수 없습니다")

        # 중복 체크 (UniqueCode, 자기 자신 제외)
        if data.UniqueCode and product_repo.check_duplicate("UniqueCode", data.UniqueCode, exclude_id=product_id):
            raise HTTPException(400, f"중복된 고유코드입니다: {data.UniqueCode}")

        # 수정
        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = product_repo.update(product_id, update_data)

        if not success:
            raise HTTPException(500, "제품 수정 실패")

        return {"ProductID": product_id, **update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"제품 수정 실패: {str(e)}")


@router.delete("/{product_id}")
@log_delete("Product", id_param="product_id")
async def delete_product(
    product_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """Product 삭제 (연관된 ProductBox도 함께 삭제)"""
    try:
        # 존재 여부 확인
        if not product_repo.exists(product_id):
            raise HTTPException(404, "제품을 찾을 수 없습니다")

        # ProductBox 먼저 삭제 (FK 제약)
        box_repo.delete_by_product_id(product_id)

        # Product 삭제
        success = product_repo.delete(product_id)

        if not success:
            raise HTTPException(500, "제품 삭제 실패")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"제품 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
@log_bulk_delete("Product")
async def bulk_delete_products(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """Product 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        # ProductBox 먼저 일괄 삭제
        for product_id in request_body.ids:
            box_repo.delete_by_product_id(product_id)

        # Product 일괄 삭제
        deleted_count = product_repo.bulk_delete(request_body.ids)

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ========== 엑셀 다운로드/업로드 ==========

@router.get("/download/template")
async def download_template():
    """업로드용 엑셀 템플릿 다운로드"""
    try:
        handler = ProductExcelHandler()
        excel_bytes = handler.create_template()
        
        filename = f"product_upload_template.xlsx"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        
        return StreamingResponse(io.BytesIO(excel_bytes), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers=headers)
    except Exception as e:
        raise HTTPException(500, f"템플릿 생성 실패: {str(e)}")


@router.get("/download/excel")
async def download_excel(
    brand: Optional[str] = None,
    unique_code: Optional[str] = None,
    name: Optional[str] = None,
    bundle_type: Optional[str] = None
):
    """제품 목록 엑셀 다운로드"""
    try:
        filters = {}
        if brand: filters['brand'] = brand
        if unique_code: filters['unique_code'] = unique_code
        if name: filters['name'] = name
        if bundle_type: filters['bundle_type'] = bundle_type

        handler = ProductExcelHandler()
        excel_bytes = handler.export_products(filters)
        
        filename = f"products_{datetime.now().strftime('%Y%m%d')}.xlsx"
        headers = {
            'Content-Disposition': f'attachment; filename="{quote(filename)}"'
        }
        
        return StreamingResponse(io.BytesIO(excel_bytes), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers=headers)
    except Exception as e:
        raise HTTPException(500, f"엑셀 다운로드 실패: {str(e)}")


@router.post("/upload")
@log_activity("EXCEL_UPLOAD", "Product")
async def upload_excel(
    file: UploadFile = File(...),
    request: Request = None,
    user: CurrentUser = Depends(get_current_user)
):
    """엑셀 업로드 (제품 및 박스 일괄 등록/수정)"""
    try:
        content = await file.read()
        handler = ProductExcelHandler()
        result = handler.process_upload(content)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"업로드 처리 실패: {str(e)}")


# ========== ProductBox 관련 엔드포인트 ==========

@router.get("/{product_id}/boxes")
async def get_product_boxes(product_id: int):
    """특정 Product의 모든 Box 조회"""
    try:
        boxes = box_repo.get_by_product_id(product_id)
        return {"data": boxes, "total": len(boxes)}
    except Exception as e:
        raise HTTPException(500, f"Box 조회 실패: {str(e)}")


@router.post("/{product_id}/boxes")
@log_activity("CREATE", "ProductBox", id_key="BoxID")
async def create_product_box(
    product_id: int,
    data: ProductBoxCreate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ProductBox 생성"""
    try:
        # Product 존재 여부 확인
        if not product_repo.exists(product_id):
            raise HTTPException(404, "제품을 찾을 수 없습니다")

        # ERPCode 중복 체크
        if data.ERPCode and box_repo.check_duplicate("ERPCode", data.ERPCode):
            raise HTTPException(400, f"중복된 ERP 코드입니다: {data.ERPCode}")

        # 생성
        box_data = data.dict()
        box_data['ProductID'] = product_id

        box_id = box_repo.create(box_data)

        return {"BoxID": box_id, "ERPCode": data.ERPCode, "ProductID": product_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Box 생성 실패: {str(e)}")


@router.delete("/boxes/{box_id}")
@log_delete("ProductBox", id_param="box_id")
async def delete_product_box(
    box_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ProductBox 삭제"""
    try:
        success = box_repo.delete(box_id)

        if not success:
            raise HTTPException(404, "Box를 찾을 수 없습니다")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Box 삭제 실패: {str(e)}")


# ========== ProductBox 독립 라우터 (원본 WebApp 호환) ==========

productbox_router = APIRouter(prefix="/api/productboxes", tags=["ProductBox"])


@productbox_router.get("")
async def get_productboxes(
    page: int = 1,
    limit: int = 50,
    product_id: Optional[int] = None
):
    """ProductBox 목록 조회 (product_id 필터 지원)"""
    try:
        filters = {}
        if product_id:
            filters['product_id'] = product_id

        result = box_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by="BoxID",
            order_dir="DESC"
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"Box 목록 조회 실패: {str(e)}")


@productbox_router.get("/{box_id}")
async def get_productbox_by_id(box_id: int):
    """ProductBox 단일 조회"""
    try:
        box = box_repo.get_by_id(box_id)
        if not box:
            raise HTTPException(404, "Box를 찾을 수 없습니다")
        return box
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Box 조회 실패: {str(e)}")


@productbox_router.post("")
@log_activity("CREATE", "ProductBox", id_key="BoxID")
async def create_productbox_direct(
    data: ProductBoxFull,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ProductBox 직접 생성 (ProductID 포함)"""
    try:
        # Product 존재 여부 확인
        if not product_repo.exists(data.ProductID):
            raise HTTPException(404, "제품을 찾을 수 없습니다")

        # ERPCode 중복 체크
        if data.ERPCode and box_repo.check_duplicate("ERPCode", data.ERPCode):
            raise HTTPException(400, f"중복된 ERP 코드입니다: {data.ERPCode}")

        box_id = box_repo.create(data.dict(exclude_none=True))

        return {"BoxID": box_id, "ERPCode": data.ERPCode, "ProductID": data.ProductID}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Box 생성 실패: {str(e)}")


@productbox_router.put("/{box_id}")
@log_activity("UPDATE", "ProductBox", id_key="BoxID")
async def update_productbox_direct(
    box_id: int,
    data: ProductBoxFull,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ProductBox 수정"""
    try:
        if not box_repo.exists(box_id):
            raise HTTPException(404, "Box를 찾을 수 없습니다")

        # Product 존재 여부 확인
        if not product_repo.exists(data.ProductID):
            raise HTTPException(404, "제품을 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = box_repo.update(box_id, update_data)
        if not success:
            raise HTTPException(500, "Box 수정 실패")

        return {"BoxID": box_id, **update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Box 수정 실패: {str(e)}")


@productbox_router.delete("/{box_id}")
@log_delete("ProductBox", id_param="box_id")
async def delete_productbox_direct(
    box_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ProductBox 삭제"""
    try:
        success = box_repo.delete(box_id)
        if not success:
            raise HTTPException(404, "Box를 찾을 수 없습니다")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Box 삭제 실패: {str(e)}")
