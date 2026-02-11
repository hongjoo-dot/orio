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
from core.dependencies import get_client_ip, CurrentUser
from core import log_activity, log_delete, log_bulk_delete, require_permission
from core.models import BulkDeleteRequest
from utils import send_sync_notification, send_erpsales_upload_notification
from utils.excel import SalesExcelHandler

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
    end_date: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "DESC",
    user: CurrentUser = Depends(require_permission("Sales", "READ"))
):
    """ERPSales 목록 조회 (페이지네이션 및 필터링)"""
    try:
        ALLOWED_SORT = {
            "DATE": "e.DATE",
            "BRAND": "e.BRAND",
            "PRODUCT": "e.PRODUCT",
            "ChannelName": "e.ChannelName",
            "Quantity": "e.Quantity",
            "Amount": "e.Amount",
        }
        order_by = ALLOWED_SORT.get(sort_by, "e.IDX")
        order_dir = sort_dir if sort_dir in ("ASC", "DESC") else "DESC"

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
            order_by=order_by,
            order_dir=order_dir
        )

        return result
    except Exception as e:
        raise HTTPException(500, f"판매 데이터 조회 실패: {str(e)}")


@router.get("/{idx}")
async def get_sales_item(idx: int, user: CurrentUser = Depends(require_permission("Sales", "READ"))):
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
@log_activity("CREATE", "ERPSales", id_key="IDX")
async def create_sales(
    data: SalesCreate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Sales", "CREATE"))
):
    """ERPSales 생성"""
    try:
        idx = sales_repo.create(data.dict(exclude_none=True))

        return {"IDX": idx, "PRODUCT_NAME": data.PRODUCT_NAME, "ERPCode": data.ERPCode}
    except Exception as e:
        raise HTTPException(500, f"판매 데이터 생성 실패: {str(e)}")


@router.put("/{idx}")
@log_activity("UPDATE", "ERPSales", id_key="IDX")
async def update_sales(
    idx: int,
    data: SalesUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Sales", "UPDATE"))
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

        return {"IDX": idx, **update_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"판매 데이터 수정 실패: {str(e)}")


@router.delete("/{idx}")
@log_delete("ERPSales", id_param="idx")
async def delete_sales(
    idx: int,
    request: Request,
    user: CurrentUser = Depends(require_permission("Sales", "DELETE"))
):
    """ERPSales 삭제"""
    try:
        if not sales_repo.exists(idx):
            raise HTTPException(404, "판매 데이터를 찾을 수 없습니다")

        success = sales_repo.delete(idx)
        if not success:
            raise HTTPException(500, "판매 데이터 삭제 실패")

        return {"message": "삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"판매 데이터 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
@log_bulk_delete("ERPSales")
async def bulk_delete_sales(
    request_body: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Sales", "DELETE"))
):
    """ERPSales 일괄 삭제"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "삭제할 ID가 없습니다")

        deleted_count = sales_repo.bulk_delete(request_body.ids)

        return {"message": "삭제되었습니다", "deleted_count": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


@router.post("/bulk-update")
@log_activity("BULK_UPDATE", "ERPSales")
async def bulk_update_sales(
    request_body: BulkUpdateRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Sales", "UPDATE"))
):
    """ERPSales 일괄 수정"""
    try:
        if not request_body.ids:
            raise HTTPException(400, "수정할 ID가 없습니다")

        if not request_body.updates:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        updated_count = sales_repo.bulk_update(request_body.ids, request_body.updates)

        return {
            "updated_count": updated_count,
            "updated_ids": request_body.ids,
            "updates": request_body.updates
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 수정 실패: {str(e)}")


# ========== 엑셀 업로드/다운로드 ==========

@router.get("/download/template")
async def download_template(user: CurrentUser = Depends(require_permission("Sales", "EXPORT"))):
    """엑셀 업로드용 양식 다운로드"""
    columns = [
        '라인별', '일자-No.', '일자', 
        '품목그룹1명', '품목명', '품목코드',
        'Ea', '단가', '공급가액',
        '거래처그룹1명', '거래처명', '출하창고명', 
        '담당자명', '거래유형명'
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
    user: CurrentUser = Depends(require_permission("Sales", "UPLOAD"))
):
    """
    엑셀 파일 업로드 및 ERPSales에 삽입 (대용량 지원 - 배치 처리)
    """
    try:
        start_time = datetime.now()

        # 핸들러 초기화
        handler = SalesExcelHandler()
        handler.validate_file(file)

        print(f"\n[엑셀 업로드 시작] {file.filename}")

        # 파일 읽기
        excel_file = await handler.read_file(file)
        df = pd.read_excel(excel_file)
        print(f"   총 {len(df):,}행 로드됨")

        # 전처리 (칼럼 매핑, 날짜 변환, NULL 처리)
        df = handler.preprocess_dataframe(df)

        # 필수 컬럼 확인
        handler.check_required_columns(df, handler.REQUIRED_COLS, "Sales")

        # 날짜 유효성 검사
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

        print(f"   데이터 전처리 완료: {len(df):,}행")

        # 매핑 테이블 로드
        mapping_counts = handler.load_sales_mappings()
        print(f"   매핑 테이블 로드 완료 (Brand:{mapping_counts['brand']}, Product:{mapping_counts['product']}, Channel:{mapping_counts['channel']}, Detail:{mapping_counts['channel_detail']}, Warehouse:{mapping_counts['warehouse']})")

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
                        # 핸들러로 행 파싱 (매핑 포함)
                        parsed = handler.parse_row(row)

                        if parsed is None:
                            # 창고 매핑 실패 등
                            warehouse_name = row.get('WarehouseName') or '없음'
                            raise ValueError(f"창고명 매핑 실패 (입력값: '{warehouse_name}') - 필수 항목입니다.")

                        # MERGE 실행
                        cursor.execute(merge_sql, (
                            parsed['ERPIDX'],  # source ERPIDX
                            # UPDATE SET values
                            parsed['DATE'], parsed['BRAND'], parsed['BrandID'], parsed['ProductID'],
                            parsed['PRODUCT_NAME'], parsed['ERPCode'],
                            parsed['Quantity'], parsed['UnitPrice'], parsed['TaxableAmount'],
                            parsed['ChannelID'], parsed['ChannelName'],
                            parsed['ChannelDetailID'], parsed['ChannelDetailName'],
                            parsed['Owner'], parsed['DateNo'],
                            parsed['WarehouseID'], parsed['WarehouseName'], parsed['TransactionType'],
                            # INSERT VALUES
                            parsed['DATE'], parsed['BRAND'], parsed['BrandID'], parsed['ProductID'],
                            parsed['PRODUCT_NAME'], parsed['ERPCode'],
                            parsed['Quantity'], parsed['UnitPrice'], parsed['TaxableAmount'],
                            parsed['ChannelID'], parsed['ChannelName'],
                            parsed['ChannelDetailID'], parsed['ChannelDetailName'],
                            parsed['Owner'], parsed['ERPIDX'], parsed['DateNo'],
                            parsed['WarehouseID'], parsed['WarehouseName'], parsed['TransactionType']
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

        # 매핑 실패 요약
        warnings = handler.get_unmapped_summary()

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

        if warnings['unmapped_brands']['items']:
            print(f"\n[경고] 매핑 안 된 브랜드 {warnings['unmapped_brands']['count']}개")
            for b in warnings['unmapped_brands']['items'][:20]:
                print(f"   → {b}")

        if warnings['unmapped_products']['items']:
            print(f"\n[경고] 매핑 안 된 상품코드 {warnings['unmapped_products']['count']}개")
            for p in warnings['unmapped_products']['items'][:20]:
                print(f"   → {p}")

        if warnings['unmapped_channels']['items']:
            print(f"\n[경고] 매핑 안 된 채널 {warnings['unmapped_channels']['count']}개")
            for c in warnings['unmapped_channels']['items'][:20]:
                print(f"   → {c}")

        if warnings['unmapped_channel_details']['items']:
            print(f"\n[경고] 매핑 안 된 거래처 {warnings['unmapped_channel_details']['count']}개")
            for cd in warnings['unmapped_channel_details']['items'][:20]:
                print(f"   → {cd}")

        if warnings['unmapped_warehouses']['items']:
            print(f"\n[경고] 매핑 안 된 창고 {warnings['unmapped_warehouses']['count']}개")
            for w in warnings['unmapped_warehouses']['items'][:20]:
                print(f"   → {w}")
        print(f"{'='*70}")

        return {
            "message": "Upload completed",
            "total_rows": len(df),
            "inserted": inserted_count,
            "updated": updated_count,
            "failed": len(failed_rows),
            "failed_rows": failed_rows[:100],
            "warnings": warnings
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"업로드 실패: {str(e)}")


@router.post("/sync-to-orders")
@log_activity("SYNC", "OrdersRealtime")
async def sync_erpsales_to_orders(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    request: Request = None,
    user: CurrentUser = Depends(require_permission("Sales", "UPDATE"))
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
            "action": "SYNC_FROM_ERPSALES",
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
