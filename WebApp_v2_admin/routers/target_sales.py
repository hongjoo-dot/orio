"""
TargetSalesProduct Router
- 목표매출(상품별) 관리 API 엔드포인트
- Promotion과 독립적으로 채널/브랜드별 월 목표 매출 관리
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import io
from datetime import datetime
from repositories import (
    TargetSalesProductRepository,
    BrandRepository,
    ChannelRepository,
    ProductRepository
)
from repositories import ActivityLogRepository
from core.dependencies import get_current_user, get_client_ip, CurrentUser
from utils.excel import TargetSalesExcelHandler

router = APIRouter(prefix="/api/target-sales", tags=["TargetSales"])

# Repository 인스턴스
target_sales_repo = TargetSalesProductRepository()
brand_repo = BrandRepository()
channel_repo = ChannelRepository()
product_repo = ProductRepository()
activity_log_repo = ActivityLogRepository()


# Pydantic Models
class BulkDeleteRequest(BaseModel):
    ids: List[int]


# ========== 조회 엔드포인트 ==========

@router.get("")
async def get_target_sales(
    page: int = 1,
    limit: int = 20,
    brand_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    product_id: Optional[int] = None,
    sales_type: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None
):
    """
    목표매출 목록 조회 (페이지네이션 및 필터링)

    필터 옵션:
    - brand_id: 브랜드 ID
    - channel_id: 채널 ID
    - product_id: 상품 ID
    - sales_type: 매출유형 (BASE / PROMOTION)
    - year: 연도
    - month: 월
    """
    try:
        filters = {}
        if brand_id is not None:
            filters['brand_id'] = brand_id
        if channel_id:
            filters['channel_id'] = channel_id
        if product_id:
            filters['product_id'] = product_id
        if sales_type:
            filters['sales_type'] = sales_type
        if year:
            filters['year'] = year
        if month:
            filters['month'] = month

        result = target_sales_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by="t.[Year] DESC, t.[Month] DESC, t.BrandID, t.ChannelID"
        )

        return result
    except Exception as e:
        raise HTTPException(500, f"목표매출 목록 조회 실패: {str(e)}")


@router.get("/filter-options")
async def get_filter_options():
    """필터 옵션 목록 조회 (브랜드, 채널, 연도, 월)"""
    try:
        # 브랜드 목록
        brands = brand_repo.get_list(page=1, limit=100)

        # 채널 목록
        channels = channel_repo.get_list(page=1, limit=100)

        return {
            "brands": [
                {"value": b["BrandID"], "label": b["Name"]}
                for b in brands.get("data", [])
            ],
            "channels": [
                {"value": c["ChannelID"], "label": c["Name"]}
                for c in channels.get("data", [])
            ],
            "sales_types": [
                {"value": "BASE", "label": "비행사"},
                {"value": "PROMOTION", "label": "행사"}
            ],
            "years": list(range(datetime.now().year - 2, datetime.now().year + 3)),
            "months": list(range(1, 13))
        }
    except Exception as e:
        raise HTTPException(500, f"필터 옵션 조회 실패: {str(e)}")


@router.get("/{target_id}")
async def get_target_sale(target_id: int):
    """목표매출 단일 조회"""
    try:
        item = target_sales_repo.get_by_id(target_id)
        if not item:
            raise HTTPException(404, "목표매출을 찾을 수 없습니다")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"목표매출 조회 실패: {str(e)}")


# ========== 삭제 엔드포인트 ==========

@router.delete("/{target_id}")
async def delete_target_sale(
    target_id: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """목표매출 단일 삭제"""
    try:
        if not target_sales_repo.exists(target_id):
            raise HTTPException(404, "목표매출을 찾을 수 없습니다")

        success = target_sales_repo.delete(target_id)
        if not success:
            raise HTTPException(500, "목표매출 삭제 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="DELETE",
                target_table="TargetSalesProduct",
                target_id=str(target_id),
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"목표매출 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
async def bulk_delete_target_sales(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """목표매출 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = 0
        for target_id in request_body.ids:
            if target_sales_repo.delete(target_id):
                deleted_count += 1

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="BULK_DELETE",
                target_table="TargetSalesProduct",
                details={
                    "deleted_ids": request_body.ids,
                    "deleted_count": deleted_count
                },
                ip_address=get_client_ip(request)
            )

        return {
            "message": "삭제되었습니다",
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ========== 엑셀 다운로드 ==========

@router.get("/download/template")
async def download_template():
    """
    목표매출 등록용 빈 템플릿 다운로드

    컬럼: 연도 | 월 | 브랜드 | 채널명 | 상품코드 | 매출유형 | 목표매출액 | 목표수량 | 비고
    (목표ID 없음 - 신규 등록용)
    """
    columns = ['연도', '월', '브랜드', '채널명', '상품코드', '매출유형', '목표매출액', '목표수량', '비고']

    # 샘플 데이터
    sample_data = [
        {
            '연도': 2026,
            '월': 1,
            '브랜드': '스크럽대디',
            '채널명': '쿠팡',
            '상품코드': 1001,
            '매출유형': '비행사',
            '목표매출액': 50000000,
            '목표수량': 2500,
            '비고': ''
        },
        {
            '연도': 2026,
            '월': 1,
            '브랜드': '스크럽대디',
            '채널명': '쿠팡',
            '상품코드': 1002,
            '매출유형': '행사',
            '목표매출액': 30000000,
            '목표수량': 1500,
            '비고': '1월 프로모션'
        }
    ]

    df = pd.DataFrame(sample_data, columns=columns)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book

        # 헤더 스타일
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#4472C4',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        # 데이터 시트
        df.to_excel(writer, index=False, sheet_name='목표매출', startrow=1, header=False)
        ws = writer.sheets['목표매출']

        # 헤더 직접 작성
        for col_idx, col_name in enumerate(columns):
            ws.write(0, col_idx, col_name, header_format)

        # 칼럼 너비 설정
        ws.set_column(0, 0, 8)   # 연도
        ws.set_column(1, 1, 6)   # 월
        ws.set_column(2, 2, 12)  # 브랜드
        ws.set_column(3, 3, 15)  # 채널명
        ws.set_column(4, 4, 10)  # 상품코드
        ws.set_column(5, 5, 10)  # 매출유형
        ws.set_column(6, 6, 15)  # 목표매출액
        ws.set_column(7, 7, 10)  # 목표수량
        ws.set_column(8, 8, 20)  # 비고

        # 안내 시트
        info_data = [
            ['칼럼 설명', ''],
            ['연도', '목표 연도 (예: 2026)'],
            ['월', '목표 월 (1~12)'],
            ['브랜드', '브랜드명 (DB에 등록된 이름)'],
            ['채널명', '채널명 (DB에 등록된 이름)'],
            ['상품코드', '상품 Uniquecode'],
            ['매출유형', '비행사 / 행사'],
            ['목표매출액', '목표 매출액 (숫자)'],
            ['목표수량', '목표 수량 (숫자)'],
            ['비고', '참고사항'],
            ['', ''],
            ['유니크 키', '연도 + 월 + 브랜드 + 채널 + 상품코드 + 매출유형'],
            ['', '이 조합이 같으면 업데이트, 다르면 신규 등록'],
        ]
        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, index=False, header=False, sheet_name='안내')
        ws_info = writer.sheets['안내']
        ws_info.set_column(0, 0, 15)
        ws_info.set_column(1, 1, 50)

    output.seek(0)

    headers = {
        'Content-Disposition': 'attachment; filename="target_sales_template.xlsx"'
    }

    return StreamingResponse(
        output,
        headers=headers,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


class DownloadDataRequest(BaseModel):
    ids: List[int]


@router.post("/download/data")
async def download_data(request_body: DownloadDataRequest):
    """
    선택한 목표매출 데이터 다운로드 (수정용)

    컬럼: 목표ID | 연도 | 월 | 브랜드 | 채널명 | 상품코드 | 매출유형 | 목표매출액 | 목표수량 | 비고
    (목표ID 포함 - 수정용)
    """
    try:
        if not request_body.ids:
            raise HTTPException(400, "다운로드할 데이터를 선택해주세요")

        # 선택된 ID로 데이터 조회
        data = []
        for target_id in request_body.ids:
            item = target_sales_repo.get_by_id(target_id)
            if item:
                data.append(item)

        if not data:
            raise HTTPException(404, "다운로드할 데이터가 없습니다")

        # DataFrame 변환
        columns = ['목표ID', '연도', '월', '브랜드', '채널명', '상품코드', '매출유형', '목표매출액', '목표수량', '비고']

        # SalesType 영문 -> 한글 매핑
        sales_type_map = {'BASE': '비행사', 'PROMOTION': '행사'}

        rows = []
        for item in data:
            rows.append({
                '목표ID': item['TargetID'],
                '연도': item['Year'],
                '월': item['Month'],
                '브랜드': item['BrandName'],
                '채널명': item['ChannelName'],
                '상품코드': item.get('ProductID'),  # TODO: Uniquecode 조회 필요시 수정
                '매출유형': sales_type_map.get(item['SalesType'], item['SalesType']),
                '목표매출액': item['TargetAmount'],
                '목표수량': item['TargetQuantity'],
                '비고': item.get('Notes', '')
            })

        df = pd.DataFrame(rows, columns=columns)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book

            # 헤더 스타일
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#4472C4',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })

            id_header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#C00000',  # 빨강색 - ID 컬럼 강조
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })

            # 데이터 시트
            df.to_excel(writer, index=False, sheet_name='목표매출', startrow=1, header=False)
            ws = writer.sheets['목표매출']

            # 헤더 직접 작성 (목표ID는 주황색)
            for col_idx, col_name in enumerate(columns):
                if col_name == '목표ID':
                    ws.write(0, col_idx, col_name, id_header_format)
                else:
                    ws.write(0, col_idx, col_name, header_format)

            # 칼럼 너비 설정
            ws.set_column(0, 0, 10)  # 목표ID
            ws.set_column(1, 1, 8)   # 연도
            ws.set_column(2, 2, 6)   # 월
            ws.set_column(3, 3, 12)  # 브랜드
            ws.set_column(4, 4, 15)  # 채널명
            ws.set_column(5, 5, 10)  # 상품코드
            ws.set_column(6, 6, 10)  # 매출유형
            ws.set_column(7, 7, 15)  # 목표매출액
            ws.set_column(8, 8, 10)  # 목표수량
            ws.set_column(9, 9, 20)  # 비고

        output.seek(0)

        # 파일명 생성 (선택된 데이터 기반)
        filename = f'target_sales_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }

        return StreamingResponse(
            output,
            headers=headers,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"데이터 다운로드 실패: {str(e)}")


# ========== 엑셀 업로드 ==========

@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    request: Request = None,
    user: CurrentUser = Depends(get_current_user)
):
    """
    엑셀 파일 업로드 및 TargetSalesProduct에 UPSERT

    처리 로직:
    - TargetID가 있으면: 해당 ID로 UPDATE
    - TargetID가 없으면: 유니크키(Year+Month+Brand+Channel+Product+SalesType)로 MERGE
    """
    try:
        start_time = datetime.now()

        # 핸들러 초기화
        handler = TargetSalesExcelHandler()
        handler.validate_file(file)

        print(f"\n[목표매출 업로드 시작] {file.filename}")

        # 파일 읽기
        excel_file = await handler.read_file(file)

        # 시트 읽기
        df = handler.read_sheet(excel_file, '목표매출', required=True)
        print(f"   목표매출: {len(df):,}행")

        # 매핑 테이블 로드
        handler.load_mappings(load_brand=True, load_channel=True, load_product=True)
        print(f"   매핑 테이블 로드 완료")

        # 레코드 파싱
        records = handler.process_sheet(df)
        print(f"   유효 레코드: {len(records):,}건")

        if not records:
            raise HTTPException(400, "업로드할 유효한 데이터가 없습니다")

        # TargetID 유무로 분리
        records_with_id = [r for r in records if r.get('TargetID')]
        records_without_id = [r for r in records if not r.get('TargetID')]

        print(f"   - ID 있음 (UPDATE): {len(records_with_id):,}건")
        print(f"   - ID 없음 (MERGE): {len(records_without_id):,}건")

        updated_by_id = 0
        result = {'inserted': 0, 'updated': 0}

        # ID가 있는 레코드는 직접 UPDATE
        if records_with_id:
            for record in records_with_id:
                target_id = record.pop('TargetID')
                success = target_sales_repo.update(target_id, record)
                if success:
                    updated_by_id += 1

        # ID가 없는 레코드는 bulk_insert (MERGE)
        if records_without_id:
            # TargetID 필드 제거 (None 값)
            for record in records_without_id:
                record.pop('TargetID', None)
            result = target_sales_repo.bulk_insert(records_without_id)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 매핑 실패 정보
        warnings = handler.get_unmapped_summary()

        # 활동 로그
        if user and request:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="TargetSalesProduct",
                details={
                    "action": "EXCEL_UPLOAD",
                    "filename": file.filename,
                    "total_records": len(records),
                    "updated_by_id": updated_by_id,
                    "inserted": result['inserted'],
                    "updated": result['updated'],
                    "unmapped_brands": warnings['unmapped_brands']['count'],
                    "unmapped_channels": warnings['unmapped_channels']['count'],
                    "unmapped_products": warnings['unmapped_products']['count'],
                    "duration_seconds": duration
                },
                ip_address=get_client_ip(request)
            )

        print(f"\n{'='*60}")
        print(f"업로드 완료:")
        print(f"   ID로 UPDATE: {updated_by_id:,}건")
        print(f"   MERGE INSERT: {result['inserted']:,}건")
        print(f"   MERGE UPDATE: {result['updated']:,}건")
        if warnings['unmapped_brands']['items']:
            print(f"   [경고] 매핑 안 된 브랜드: {warnings['unmapped_brands']['items']}")
        if warnings['unmapped_channels']['items']:
            print(f"   [경고] 매핑 안 된 채널: {warnings['unmapped_channels']['items']}")
        if warnings['unmapped_products']['items']:
            print(f"   [경고] 매핑 안 된 상품코드: {warnings['unmapped_products']['items']}")
        print(f"{'='*60}")

        return {
            "message": "업로드 완료",
            "success": True,
            "total_records": len(records),
            "updated_by_id": updated_by_id,
            "inserted": result['inserted'],
            "updated": result['updated'],
            "warnings": warnings,
            "duration_seconds": duration
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"업로드 실패: {str(e)}")
