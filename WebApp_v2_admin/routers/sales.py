"""
Sales (ERPSales) Router
- ERPSales CRUD API 엔드포인트
- Repository 패턴 활용
- 활동 로그 기록
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import io
from datetime import datetime
from repositories import SalesRepository, ActivityLogRepository
from core import get_db_cursor
from core.dependencies import get_current_user, get_client_ip, CurrentUser
from utils import send_sync_notification, send_erpsales_upload_notification

router = APIRouter(prefix="/api/erpsales", tags=["Sales"])

# Repository 인스턴스
sales_repo = SalesRepository()
activity_log_repo = ActivityLogRepository()


# Pydantic Models
class SalesCreate(BaseModel):
    DATE: Optional[str] = None
    BRAND: Optional[str] = None
    BrandID: Optional[int] = None
    ProductID: Optional[int] = None
    PRODUCT_NAME: Optional[str] = None
    ERPCode: Optional[str] = None
    Quantity: Optional[float] = None
    UnitPrice: Optional[float] = None
    TaxableAmount: Optional[float] = None
    ChannelID: Optional[int] = None
    ChannelName: Optional[str] = None
    ChannelDetailID: Optional[int] = None
    ChannelDetailName: Optional[str] = None
    Owner: Optional[str] = None
    ERPIDX: Optional[str] = None
    DateNo: Optional[str] = None
    WarehouseID: Optional[int] = None
    WarehouseName: Optional[str] = None
    TransactionType: Optional[str] = None


class SalesUpdate(BaseModel):
    DATE: Optional[str] = None
    BRAND: Optional[str] = None
    BrandID: Optional[int] = None
    ProductID: Optional[int] = None
    PRODUCT_NAME: Optional[str] = None
    ERPCode: Optional[str] = None
    Quantity: Optional[float] = None
    UnitPrice: Optional[float] = None
    TaxableAmount: Optional[float] = None
    ChannelID: Optional[int] = None
    ChannelName: Optional[str] = None
    ChannelDetailID: Optional[int] = None
    ChannelDetailName: Optional[str] = None
    Owner: Optional[str] = None
    ERPIDX: Optional[str] = None
    DateNo: Optional[str] = None
    WarehouseID: Optional[int] = None
    WarehouseName: Optional[str] = None
    TransactionType: Optional[str] = None


class BulkDeleteRequest(BaseModel):
    ids: List[int]


class BulkUpdateRequest(BaseModel):
    ids: List[int]
    updates: dict


# ========== CRUD 엔드포인트 ==========

@router.get("")
async def get_sales(
    page: int = 1,
    limit: int = 20,
    brand: Optional[str] = None,
    product_name: Optional[str] = None,
    erp_code: Optional[str] = None,
    channel_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """ERPSales 목록 조회 (페이지네이션 및 필터링)"""
    try:
        filters = {}
        if brand:
            filters['brand'] = brand
        if product_name:
            filters['product_name'] = product_name
        if erp_code:
            filters['erp_code'] = erp_code
        if channel_name:
            filters['channel_name'] = channel_name
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date

        result = sales_repo.get_list(
            page=page,
            limit=limit,
            filters=filters,
            order_by="e.IDX",
            order_dir="DESC"
        )

        return result
    except Exception as e:
        raise HTTPException(500, f"판매 데이터 조회 실패: {str(e)}")


@router.get("/{idx}")
async def get_sales_item(idx: int):
    """ERPSales 단일 조회"""
    try:
        sales_item = sales_repo.get_by_id(idx)
        if not sales_item:
            raise HTTPException(404, "판매 데이터를 찾을 수 없습니다")
        return sales_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"판매 데이터 조회 실패: {str(e)}")


@router.post("")
async def create_sales(
    data: SalesCreate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ERPSales 생성"""
    try:
        idx = sales_repo.create(data.dict(exclude_none=True))

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="ERPSales",
                target_id=str(idx),
                details={"PRODUCT_NAME": data.PRODUCT_NAME, "ERPCode": data.ERPCode},
                ip_address=get_client_ip(request)
            )

        return {"IDX": idx, **data.dict()}
    except Exception as e:
        raise HTTPException(500, f"판매 데이터 생성 실패: {str(e)}")


@router.put("/{idx}")
async def update_sales(
    idx: int,
    data: SalesUpdate,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ERPSales 수정"""
    try:
        if not sales_repo.exists(idx):
            raise HTTPException(404, "판매 데이터를 찾을 수 없습니다")

        update_data = data.dict(exclude_none=True)
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        success = sales_repo.update(idx, update_data)
        if not success:
            raise HTTPException(500, "판매 데이터 수정 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="UPDATE",
                target_table="ERPSales",
                target_id=str(idx),
                details=update_data,
                ip_address=get_client_ip(request)
            )

        return {"message": "수정되었습니다", "IDX": idx}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"판매 데이터 수정 실패: {str(e)}")


@router.delete("/{idx}")
async def delete_sales(
    idx: int,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ERPSales 삭제"""
    try:
        if not sales_repo.exists(idx):
            raise HTTPException(404, "판매 데이터를 찾을 수 없습니다")

        success = sales_repo.delete(idx)
        if not success:
            raise HTTPException(500, "판매 데이터 삭제 실패")

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="DELETE",
                target_table="ERPSales",
                target_id=str(idx),
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"판매 데이터 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
async def bulk_delete_sales(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ERPSales 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = sales_repo.bulk_delete(request_body.ids)

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="BULK_DELETE",
                target_table="ERPSales",
                details={"deleted_ids": request_body.ids, "count": deleted_count},
                ip_address=get_client_ip(request)
            )

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


@router.post("/bulk-update")
async def bulk_update_sales(
    request_body: BulkUpdateRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user)
):
    """ERPSales 일괄 수정"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "수정할 ID가 없습니다")

        if not request_body.updates:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        updated_count = sales_repo.bulk_update(request_body.ids, request_body.updates)

        if user:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="UPDATE",
                target_table="ERPSales",
                details={"updated_ids": request_body.ids, "count": updated_count, "updates": request_body.updates},
                ip_address=get_client_ip(request)
            )

        return {"message": "수정되었습니다", "updated_count": updated_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 수정 실패: {str(e)}")


# ========== 엑셀 업로드/다운로드 ==========

@router.get("/download/template")
async def download_template():
    """엑셀 업로드용 양식 다운로드"""
    columns = [
        '일자', '브랜드명', '품목명', '품목코드',
        'Ea', '단가', '공급가액',
        '거래처그룹1명', '거래처명', '담당자',
        '라인별', '일자-No.', '출하창고명', '거래유형명'
    ]

    df = pd.DataFrame(columns=columns)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sales_Template')

        worksheet = writer.sheets['Sales_Template']
        for i, col in enumerate(columns):
            worksheet.set_column(i, i, 15)

    output.seek(0)

    headers = {
        'Content-Disposition': 'attachment; filename="sales_upload_template.xlsx"'
    }

    return StreamingResponse(
        output,
        headers=headers,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    request: Request = None,
    user: CurrentUser = Depends(get_current_user)
):
    """
    엑셀 파일 업로드 및 ERPSales에 삽입 (대용량 지원 - 배치 처리)
    """
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, "엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.")

        start_time = datetime.now()
        print(f"\n[엑셀 업로드 시작] {file.filename}")

        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        print(f"   총 {len(df):,}행 로드됨")

        # 컬럼명 매핑
        column_mapping = {
            '일자': 'DATE',
            '브랜드명': 'BRAND',
            '품목명': 'PRODUCT_NAME',
            '품목코드': 'ERPCode',
            'Ea': 'Quantity',
            '단가': 'UnitPrice',
            '공급가액': 'TaxableAmount',
            '거래처그룹1명': 'ChannelName',
            '거래처명': 'ChannelDetailName',
            '담당자': 'Owner',
            '라인별': 'ERPIDX',
            '일자-No.': 'DateNo',
            '출하창고명': 'WarehouseName',
            '거래유형명': 'TransactionType'
        }

        df.rename(columns=column_mapping, inplace=True)

        # 필수 컬럼 확인
        required_columns = ['DATE', 'Quantity', 'UnitPrice', 'TaxableAmount']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(400, f"필수 컬럼 누락: {', '.join(missing_columns)}")

        # 날짜 변환
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')

        invalid_dates = df['DATE'].isna().sum()
        if invalid_dates > 0:
            print(f"   [경고] 날짜 파싱 실패: {invalid_dates:,}행 제거")
            df = df[df['DATE'].notna()]

        date_range = None
        if len(df) > 0:
            date_min = df['DATE'].min()
            date_max = df['DATE'].max()
            date_range = f"{date_min.strftime('%Y-%m-%d')} ~ {date_max.strftime('%Y-%m-%d')}"
            print(f"   날짜 범위: {date_range}")

        # NULL 처리
        numeric_columns = ['Quantity', 'UnitPrice', 'TaxableAmount']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        string_columns = ['BRAND', 'PRODUCT_NAME', 'ERPCode', 'ChannelName', 'ChannelDetailName', 'Owner', 'ERPIDX', 'DateNo', 'WarehouseName', 'TransactionType']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')

        print(f"   데이터 전처리 완료: {len(df):,}행")

        # 매핑 테이블 로드
        with get_db_cursor(commit=False) as cursor:
            print(f"   매핑 테이블 로드 중...")

            cursor.execute("SELECT Name, BrandID FROM [dbo].[Brand]")
            brand_map = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT ERPCode, ProductID FROM [dbo].[ProductBox] WHERE ERPCode IS NOT NULL")
            product_map = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT Name, ChannelID FROM [dbo].[Channel]")
            channel_map = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT DetailName, ChannelDetailID FROM [dbo].[ChannelDetail]")
            channel_detail_map = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT WarehouseName, WarehouseID FROM [dbo].[Warehouse]")
            warehouse_map = {row[0]: row[1] for row in cursor.fetchall()}

            print(f"   매핑 테이블 로드 완료 (Brand:{len(brand_map)}, Product:{len(product_map)}, Channel:{len(channel_map)}, Detail:{len(channel_detail_map)}, Warehouse:{len(warehouse_map)})")

        # 매핑 실패 추적
        unmapped_brands = set()
        unmapped_products = set()
        unmapped_channels = set()
        unmapped_channel_details = set()
        unmapped_warehouses = set()

        # 배치 처리
        BATCH_SIZE = 5000
        inserted_count = 0
        updated_count = 0
        failed_rows = []
        total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"   배치 처리 시작 (배치 크기: {BATCH_SIZE}, 총 배치: {total_batches})")

        merge_sql = """
            MERGE INTO [dbo].[ERPSales] AS target
            USING (SELECT ? AS ERPIDX) AS source
            ON target.ERPIDX = source.ERPIDX
            WHEN MATCHED THEN
                UPDATE SET
                    [DATE] = ?,
                    BRAND = ?,
                    BrandID = ?,
                    ProductID = ?,
                    PRODUCT_NAME = ?,
                    ERPCode = ?,
                    Quantity = ?,
                    UnitPrice = ?,
                    TaxableAmount = ?,
                    ChannelID = ?,
                    ChannelName = ?,
                    ChannelDetailID = ?,
                    ChannelDetailName = ?,
                    Owner = ?,
                    DateNo = ?,
                    WarehouseID = ?,
                    WarehouseName = ?,
                    TransactionType = ?
            WHEN NOT MATCHED THEN
                INSERT ([DATE], BRAND, BrandID, ProductID, PRODUCT_NAME, ERPCode,
                        Quantity, UnitPrice, TaxableAmount,
                        ChannelID, ChannelName, ChannelDetailID, ChannelDetailName, Owner,
                        ERPIDX, DateNo, WarehouseID, WarehouseName, TransactionType)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            OUTPUT $action;
        """

        with get_db_cursor(commit=True) as cursor:
            for batch_num in range(total_batches):
                start_idx = batch_num * BATCH_SIZE
                end_idx = min((batch_num + 1) * BATCH_SIZE, len(df))
                batch_df = df.iloc[start_idx:end_idx]

                for idx, row in batch_df.iterrows():
                    try:
                        brand_name = row.get('BRAND') or None
                        erp_code = row.get('ERPCode') or None
                        channel_name = row.get('ChannelName') or None
                        channel_detail_name = row.get('ChannelDetailName') or None
                        warehouse_name = row.get('WarehouseName') or None

                        brand_id = brand_map.get(brand_name) if brand_name else None
                        product_id = product_map.get(erp_code) if erp_code else None
                        channel_id = channel_map.get(channel_name) if channel_name else None
                        channel_detail_id = channel_detail_map.get(channel_detail_name) if channel_detail_name else None
                        warehouse_id = warehouse_map.get(warehouse_name) if warehouse_name else None

                        # 매핑 실패 추적
                        if brand_name and brand_id is None:
                            unmapped_brands.add(brand_name)
                        if erp_code and product_id is None:
                            unmapped_products.add(erp_code)
                        if channel_name and channel_id is None:
                            unmapped_channels.add(channel_name)
                        if channel_detail_name and channel_detail_id is None:
                            unmapped_channel_details.add(channel_detail_name)
                        if warehouse_name and warehouse_id is None:
                            unmapped_warehouses.add(warehouse_name)

                        # 필수 데이터 유효성 검사
                        if warehouse_id is None:
                            raise ValueError(f"창고명 매핑 실패 (입력값: '{warehouse_name or '없음'}') - 필수 항목입니다.")

                        erpidx = row.get('ERPIDX') or None
                        date_val = row['DATE']
                        product_name = row.get('PRODUCT_NAME') or None
                        quantity = float(row['Quantity']) if row.get('Quantity') else 0
                        unit_price = float(row['UnitPrice']) if row.get('UnitPrice') else 0
                        taxable = float(row['TaxableAmount']) if row.get('TaxableAmount') else 0
                        owner = row.get('Owner') or None
                        date_no = row.get('DateNo') or None
                        trans_type = row.get('TransactionType') or None

                        # MERGE 실행
                        cursor.execute(merge_sql, (
                            erpidx,  # source ERPIDX
                            # UPDATE SET values
                            date_val, brand_name, brand_id, product_id, product_name, erp_code,
                            quantity, unit_price, taxable,
                            channel_id, channel_name, channel_detail_id, channel_detail_name, owner,
                            date_no, warehouse_id, warehouse_name, trans_type,
                            # INSERT VALUES
                            date_val, brand_name, brand_id, product_id, product_name, erp_code,
                            quantity, unit_price, taxable,
                            channel_id, channel_name, channel_detail_id, channel_detail_name, owner,
                            erpidx, date_no, warehouse_id, warehouse_name, trans_type
                        ))

                        # OUTPUT $action 결과 확인
                        result = cursor.fetchone()
                        if result and result[0] == 'INSERT':
                            inserted_count += 1
                        elif result and result[0] == 'UPDATE':
                            updated_count += 1

                    except Exception as e:
                        failed_rows.append({
                            "row": idx + 2,
                            "error": str(e),
                            "data": {
                                "ERPIDX": row.get('ERPIDX'),
                                "BRAND": row.get('BRAND'),
                                "PRODUCT_NAME": row.get('PRODUCT_NAME'),
                                "ERPCode": row.get('ERPCode'),
                                "DATE": str(row.get('DATE'))
                            }
                        })

                if (batch_num + 1) % 5 == 0 or (batch_num + 1) == total_batches:
                    progress_pct = (batch_num + 1) / total_batches * 100
                    print(f"   진행: {batch_num + 1}/{total_batches} 배치 (삽입:{inserted_count:,}, 수정:{updated_count:,}, 실패:{len(failed_rows)}, {progress_pct:.1f}%)")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 활동 로그 기록 (엑셀 업로드)
        if user and request:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="ERPSales",
                details={
                    "action": "EXCEL_UPLOAD",
                    "filename": file.filename,
                    "total_rows": len(df),
                    "inserted": inserted_count,
                    "updated": updated_count,
                    "failed": len(failed_rows),
                    "date_range": date_range,
                    "duration_seconds": duration
                },
                ip_address=get_client_ip(request)
            )

        # 리포트
        print(f"\n{'='*70}")
        print(f"업로드 리포트")
        print(f"{'='*70}")
        print(f"   업로드 완료: {inserted_count:,}건 삽입, {updated_count:,}건 수정, {len(failed_rows)}건 실패")

        if unmapped_brands:
            print(f"\n[경고] 매핑 안 된 브랜드 {len(unmapped_brands)}개")
            for b in sorted(list(unmapped_brands)[:20]):
                print(f"   → {b}")

        if unmapped_products:
            print(f"\n[경고] 매핑 안 된 상품코드 {len(unmapped_products)}개")
            for p in sorted(list(unmapped_products)[:20]):
                print(f"   → {p}")

        if unmapped_channels:
            print(f"\n[경고] 매핑 안 된 채널 {len(unmapped_channels)}개")
            for c in sorted(list(unmapped_channels)[:20]):
                print(f"   → {c}")

        if unmapped_channel_details:
            print(f"\n[경고] 매핑 안 된 거래처 {len(unmapped_channel_details)}개")
            for cd in sorted(list(unmapped_channel_details)[:20]):
                print(f"   → {cd}")

        if unmapped_warehouses:
            print(f"\n[경고] 매핑 안 된 창고 {len(unmapped_warehouses)}개")
            for w in sorted(list(unmapped_warehouses)[:20]):
                print(f"   → {w}")
        print(f"{'='*70}")

        return {
            "message": "Upload completed",
            "total_rows": len(df),
            "inserted": inserted_count,
            "updated": updated_count,
            "failed": len(failed_rows),
            "failed_rows": failed_rows[:100],
            "unmapped_brands": len(unmapped_brands),
            "unmapped_products": len(unmapped_products),
            "unmapped_channels": len(unmapped_channels),
            "unmapped_channel_details": len(unmapped_channel_details),
            "unmapped_warehouses": len(unmapped_warehouses),
            "unmapped_brands_list": sorted(list(unmapped_brands)),
            "unmapped_products_list": sorted(list(unmapped_products)),
            "unmapped_channels_list": sorted(list(unmapped_channels)),
            "unmapped_channel_details_list": sorted(list(unmapped_channel_details)),
            "unmapped_warehouses_list": sorted(list(unmapped_warehouses))
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"업로드 실패: {str(e)}")


@router.post("/sync-to-orders")
async def sync_erpsales_to_orders(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    request: Request = None,
    user: CurrentUser = Depends(get_current_user)
):
    """
    ERPSales 데이터를 OrdersRealtime으로 동기화 (MERGE 방식)

    - Channel.LiveSource = 'ERP'인 모든 채널 동기화
    - SourceOrderID (ERPIDX) 기준으로 중복 체크
    - 존재하면 UPDATE, 없으면 INSERT
    """
    try:
        print(f"\n[ERPSales → OrdersRealtime 동기화 시작]")
        if start_date:
            print(f"   시작 날짜: {start_date}")
        if end_date:
            print(f"   종료 날짜: {end_date}")

        start_time = datetime.now()

        with get_db_cursor(commit=True) as cursor:
            sql = """
                EXEC [dbo].[sp_MergeERPSalesToOrders]
                    @StartDate = ?,
                    @EndDate = ?
            """

            cursor.execute(sql, (start_date, end_date))
            result = cursor.fetchone()

            insert_count = result[0]
            update_count = result[1]
            error_count = result[2]
            status = result[3]

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 활동 로그 기록 (동기화)
        if user and request:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="UPDATE",
                target_table="OrdersRealtime",
                details={
                    "action": "SYNC_FROM_ERPSALES",
                    "start_date": start_date,
                    "end_date": end_date,
                    "insert_count": insert_count,
                    "update_count": update_count,
                    "error_count": error_count,
                    "duration_seconds": duration,
                    "status": status
                },
                ip_address=get_client_ip(request)
            )

        print(f"\n{'='*70}")
        print(f"동기화 완료")
        print(f"{'='*70}")
        print(f"   INSERT: {insert_count:,}건")
        print(f"   UPDATE: {update_count:,}건")
        print(f"   ERROR: {error_count}건")
        print(f"   소요 시간: {duration:.1f}초")
        print(f"   상태: {status}")
        print(f"{'='*70}")

        # Slack 알림 전송
        try:
            send_sync_notification(
                insert_count=insert_count,
                update_count=update_count,
                error_count=error_count,
                status=status,
                duration=duration,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as slack_error:
            print(f"[경고] Slack 알림 전송 실패: {str(slack_error)}")

        return {
            "message": "Sync completed",
            "status": status,
            "insert_count": insert_count,
            "update_count": update_count,
            "error_count": error_count,
            "duration_seconds": duration,
            "start_date": start_date,
            "end_date": end_date
        }

    except Exception as e:
        print(f"\n[ERROR] 동기화 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"동기화 실패: {str(e)}")
