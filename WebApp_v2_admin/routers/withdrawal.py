"""
Withdrawal (불출 관리) Router
- 불출 계획 (WithdrawalPlan) CRUD + 엑셀 업로드/다운로드
- 불출 상품 (WithdrawalPlanItem) 조회
- 승인/반려 워크플로우
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Any
import pandas as pd
import io
from datetime import datetime
from repositories.withdrawal_repository import WithdrawalPlanRepository, WithdrawalPlanItemRepository
from repositories import ProductRepository, ActivityLogRepository
from core import get_db_cursor
from core.dependencies import get_client_ip, CurrentUser
from core import log_activity, log_delete, log_bulk_delete, require_permission


# ========== Repository 인스턴스 ==========
plan_repo = WithdrawalPlanRepository()
item_repo = WithdrawalPlanItemRepository()
product_repo = ProductRepository()
activity_log_repo = ActivityLogRepository()


# ========== Pydantic Models ==========

class WithdrawalPlanUpdate(BaseModel):
    Title: Optional[str] = None
    Type: Optional[str] = None
    OrdererName: Optional[str] = None
    RecipientName: Optional[str] = None
    Phone1: Optional[str] = None
    Phone2: Optional[str] = None
    Address1: Optional[str] = None
    Address2: Optional[str] = None
    DeliveryMethod: Optional[str] = None
    DeliveryMessage: Optional[str] = None
    DesiredDate: Optional[str] = None
    TrackingNo: Optional[str] = None
    Notes: Optional[str] = None


class StatusChangeRequest(BaseModel):
    status: str
    rejection_reason: Optional[str] = None


class BulkDeleteRequest(BaseModel):
    ids: List[Any]


# ==========================================================
#  WithdrawalPlan Router (불출 계획 CRUD + 엑셀)
# ==========================================================
router = APIRouter(prefix="/api/withdrawals", tags=["Withdrawal"])


# ========== 불출 계획 목록 조회 ==========

@router.get("")
async def get_withdrawal_list(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    type: Optional[str] = None,
    year_month: Optional[str] = None,
    order_no: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "DESC",
    user: CurrentUser = Depends(require_permission("Withdrawal", "READ"))
):
    """불출 계획 목록 조회"""
    try:
        ALLOWED_SORT = {
            "PlanID": "w.PlanID",
            "OrderNo": "w.OrderNo",
            "Title": "w.Title",
            "Type": "w.Type",
            "Status": "w.Status",
            "OrdererName": "w.OrdererName",
            "RecipientName": "w.RecipientName",
            "DesiredDate": "w.DesiredDate",
            "CreatedDate": "w.CreatedDate",
        }
        order_by = ALLOWED_SORT.get(sort_by, "w.CreatedDate")
        order_dir = sort_dir if sort_dir in ("ASC", "DESC") else "DESC"

        filters = {}
        if status:
            filters['status'] = status
        if type:
            filters['type'] = type
        if year_month:
            filters['year_month'] = year_month
        if order_no:
            filters['order_no'] = order_no

        result = plan_repo.get_list(
            page=page, limit=limit,
            filters=filters,
            order_by=order_by, order_dir=order_dir
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"불출 계획 목록 조회 실패: {str(e)}")


@router.get("/year-months")
async def get_year_months(user: CurrentUser = Depends(require_permission("Withdrawal", "READ"))):
    """년월 목록 조회"""
    try:
        return {"year_months": plan_repo.get_year_months()}
    except Exception as e:
        raise HTTPException(500, f"년월 목록 조회 실패: {str(e)}")


@router.get("/types")
async def get_withdrawal_types(user: CurrentUser = Depends(require_permission("Withdrawal", "READ"))):
    """사용유형 목록 조회"""
    try:
        return {"types": plan_repo.get_types()}
    except Exception as e:
        raise HTTPException(500, f"사용유형 목록 조회 실패: {str(e)}")


@router.get("/statuses")
async def get_withdrawal_statuses(user: CurrentUser = Depends(require_permission("Withdrawal", "READ"))):
    """상태 목록 조회"""
    try:
        return {"statuses": plan_repo.get_statuses()}
    except Exception as e:
        raise HTTPException(500, f"상태 목록 조회 실패: {str(e)}")


# ========== 엑셀 다운로드 (양식 + 데이터) ==========

@router.get("/download")
async def download_withdrawals(
    status: Optional[str] = None,
    type: Optional[str] = None,
    year_month: Optional[str] = None,
    ids: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("Withdrawal", "EXPORT"))
):
    """불출 계획 엑셀 다운로드"""
    try:
        plans = []
        items = []

        if ids:
            id_list = [int(id.strip()) for id in ids.split(',') if id.strip()]
            plans = plan_repo.get_by_ids(id_list)
            items = item_repo.get_by_plan_ids(id_list)
        elif status or type or year_month:
            filters = {}
            if status:
                filters['status'] = status
            if type:
                filters['type'] = type
            if year_month:
                filters['year_month'] = year_month
            result = plan_repo.get_list(page=1, limit=100000, filters=filters)
            plans = result['data']
            if plans:
                plan_ids = [p['PlanID'] for p in plans]
                items = item_repo.get_by_plan_ids(plan_ids)

        # 계획별 상품 매핑
        items_by_plan = {}
        for item in items:
            pid = item['PlanID']
            if pid not in items_by_plan:
                items_by_plan[pid] = []
            items_by_plan[pid].append(item)

        # 통합 행 생성
        rows = []
        for plan in plans:
            plan_items = items_by_plan.get(plan['PlanID'], [])
            if plan_items:
                for item in plan_items:
                    rows.append({
                        '계획ID': plan['PlanID'],
                        '상품명': item['ProductName'],
                        '수량': item['Quantity'],
                        '배송방식': plan['DeliveryMethod'],
                        '주문자이름': plan['OrdererName'],
                        '받는분이름': plan['RecipientName'],
                        '전화번호1': plan['Phone1'],
                        '전화번호2': plan['Phone2'],
                        '주소1': plan['Address1'],
                        '주소2': plan['Address2'],
                        '배송메세지': plan['DeliveryMessage'],
                        '주문번호': plan['OrderNo'],
                        '사용유형': plan['Type'],
                        '출고희망일': plan['DesiredDate'],
                        '관리메모': plan['Notes'],
                        '송장번호': plan['TrackingNo'],
                    })
            else:
                rows.append({
                    '계획ID': plan['PlanID'],
                    '상품명': None,
                    '수량': None,
                    '배송방식': plan['DeliveryMethod'],
                    '주문자이름': plan['OrdererName'],
                    '받는분이름': plan['RecipientName'],
                    '전화번호1': plan['Phone1'],
                    '전화번호2': plan['Phone2'],
                    '주소1': plan['Address1'],
                    '주소2': plan['Address2'],
                    '배송메세지': plan['DeliveryMessage'],
                    '주문번호': plan['OrderNo'],
                    '사용유형': plan['Type'],
                    '출고희망일': plan['DesiredDate'],
                    '관리메모': plan['Notes'],
                    '송장번호': plan['TrackingNo'],
                })

        export_columns = [
            '계획ID', '상품명', '수량', '배송방식',
            '주문자이름', '받는분이름', '전화번호1', '전화번호2',
            '주소1', '주소2', '배송메세지',
            '주문번호', '사용유형', '출고희망일', '관리메모', '송장번호'
        ]

        id_column_indices = [0]      # 계획ID (빨간색)
        readonly_columns = []        # 없음

        if not rows:
            df = pd.DataFrame(columns=export_columns)
        else:
            df = pd.DataFrame(rows, columns=export_columns)

        # 안내 시트
        guide_data = [
            ['[불출 관리 업로드 안내]', ''],
            ['', ''],
            ['■ 업로드 방식', ''],
            ['계획ID가 있는 행', '계획ID 기준으로 해당 계획을 수정합니다.'],
            ['계획ID가 없는 행', '주문번호 기준으로 그룹핑하여 신규 등록합니다.'],
            ['', ''],
            ['■ 컬럼 설명', ''],
            ['계획ID (빨간색)', '수정할 계획 식별용 (비워두면 신규 등록)'],
            ['상품명', '상품명 선택 (드롭다운, Status=YES이고 바코드가 있는 상품만)'],
            ['수량', '숫자'],
            ['배송방식', '택배 등'],
            ['주문자이름', '주문자 이름'],
            ['받는분이름', '수령인 이름'],
            ['전화번호1/2', '연락처'],
            ['주소1/2', '배송지 주소'],
            ['배송메세지', '배송시 메세지'],
            ['주문번호', '동일 주문번호의 행은 하나의 불출 계획으로 묶입니다.'],
            ['사용유형', '업체샘플, 증정, 인플루언서, 직원복지, 기타'],
            ['출고희망일', 'YYYY-MM-DD 또는 YYYYMMDD 형식'],
            ['관리메모', '메모'],
            ['송장번호', '택배 송장번호'],
            ['', ''],
            ['■ 주의사항', ''],
            ['1. 같은 주문번호의 여러 상품은 하나의 불출 계획으로 묶입니다.', ''],
            ['2. 상품명은 반드시 DB에 등록된 상품이어야 합니다 (BaseBarcode가 있는 상품).', ''],
            ['3. 계획ID(빨간색 배경) 컬럼은 수정해도 반영되지 않습니다.', ''],
        ]
        guide_df = pd.DataFrame(guide_data, columns=['항목', '설명'])

        # 드롭다운용 상품명 목록 (Status=YES, BaseBarcode 존재)
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT Name FROM [dbo].[Product]
                WHERE Status = 'YES'
                  AND BaseBarcode IS NOT NULL AND BaseBarcode != ''
                ORDER BY Name
            """)
            product_names = [row[0] for row in cursor.fetchall()]

        # 사용유형 목록
        withdrawal_types = plan_repo.get_types()

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='불출관리')
            guide_df.to_excel(writer, index=False, sheet_name='안내')

            workbook = writer.book
            worksheet = writer.sheets['불출관리']

            # 목록 시트 (드롭다운 소스)
            list_sheet = workbook.add_worksheet('목록')
            list_sheet.hide()

            # A열: 상품명 목록
            for i, name in enumerate(product_names):
                list_sheet.write(i, 0, name)
            # B열: 사용유형 목록
            for i, name in enumerate(withdrawal_types):
                list_sheet.write(i, 1, name)

            max_row = max(len(df) + 100, 1000)

            # 상품명 드롭다운 (인덱스 1)
            if product_names:
                worksheet.data_validation(1, 1, max_row, 1, {
                    'validate': 'list',
                    'source': f'=목록!$A$1:$A${len(product_names)}',
                    'input_message': '상품명을 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 사용유형 드롭다운 (인덱스 12)
            if withdrawal_types:
                worksheet.data_validation(1, 12, max_row, 12, {
                    'validate': 'list',
                    'source': f'=목록!$B$1:$B${len(withdrawal_types)}',
                    'input_message': '사용유형을 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 서식 정의
            id_header_format = workbook.add_format({
                'bold': True, 'font_color': 'white',
                'bg_color': '#dc2626', 'border': 1
            })
            editable_header_format = workbook.add_format({
                'bold': True, 'border': 1
            })
            id_data_format = workbook.add_format({
                'font_color': 'white', 'bg_color': '#ef4444', 'border': 1
            })

            # 헤더 서식
            for col_idx, col_name in enumerate(export_columns):
                if col_idx in id_column_indices:
                    worksheet.write(0, col_idx, col_name, id_header_format)
                else:
                    worksheet.write(0, col_idx, col_name, editable_header_format)

            # 데이터 행 서식 (ID 컬럼 빨간색)
            if len(df) > 0:
                for row_idx in range(len(df)):
                    for id_col in id_column_indices:
                        col_name = export_columns[id_col]
                        if col_name in df.columns:
                            value = df.iloc[row_idx][col_name]
                            if pd.notna(value):
                                worksheet.write(row_idx + 1, id_col, value, id_data_format)
                            else:
                                worksheet.write_blank(row_idx + 1, id_col, None, id_data_format)

            # 컬럼 너비
            for i in range(len(export_columns)):
                worksheet.set_column(i, i, 15)

            guide_sheet = writer.sheets['안내']
            guide_sheet.set_column(0, 0, 65)
            guide_sheet.set_column(1, 1, 40)

        output.seek(0)
        filename = f"withdrawals_{year_month or 'template'}.xlsx"
        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}

        return StreamingResponse(
            output, headers=headers,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"다운로드 실패: {str(e)}")


# ========== 엑셀 업로드 ==========

@router.post("/upload")
async def upload_withdrawals(
    file: UploadFile = File(...),
    request: Request = None,
    user: CurrentUser = Depends(require_permission("Withdrawal", "UPLOAD"))
):
    """불출 계획 엑셀 업로드"""
    try:
        upload_start_time = datetime.now()

        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, "엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        print(f"\n[불출 관리 업로드 시작] {file.filename}")

        content = await file.read()
        excel_file = io.BytesIO(content)
        df = pd.read_excel(excel_file)
        print(f"   총 {len(df):,}행 로드됨")

        # 컬럼 매핑 (한글 → 영문)
        column_map = {
            '계획ID': 'PlanID',
            '상품명': 'ProductName',
            '수량': 'Quantity',
            '배송방식': 'DeliveryMethod',
            '주문자이름': 'OrdererName',
            '받는분이름': 'RecipientName',
            '전화번호1': 'Phone1',
            '전화번호2': 'Phone2',
            '주소1': 'Address1',
            '주소2': 'Address2',
            '배송메세지': 'DeliveryMessage',
            '주문번호': 'OrderNo',
            '사용유형': 'Type',
            '출고희망일': 'DesiredDate',
            '관리메모': 'Notes',
            '송장번호': 'TrackingNo',
        }
        df = df.rename(columns=column_map)

        # 필수 컬럼 확인
        required_cols = ['ProductName', 'OrderNo', 'Type']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(400, f"필수 컬럼이 없습니다: {missing_cols}")

        # 날짜 변환
        if 'DesiredDate' in df.columns:
            df['DesiredDate'] = df['DesiredDate'].apply(_parse_date)

        # 수량 변환
        if 'Quantity' in df.columns:
            df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(1).astype(int)

        # 문자열 공백 제거
        for col in ['ProductName', 'OrderNo', 'Type', 'OrdererName', 'RecipientName']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', '')

        # 상품명 → Product 매핑 (Status=YES, BaseBarcode 존재)
        product_names_unique = df['ProductName'].dropna().unique().tolist()
        product_names_unique = [n for n in product_names_unique if n and n != 'nan' and n != '']
        product_map = {}
        errors = {'product': {}}

        for name in product_names_unique:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT Name, BaseBarcode, UniqueCode
                    FROM [dbo].[Product]
                    WHERE Name = ? AND Status = 'YES'
                      AND BaseBarcode IS NOT NULL AND BaseBarcode != ''
                """, (name,))
                row = cursor.fetchone()
                if row:
                    product_map[name] = {
                        'ProductName': row[0],
                        'BaseBarcode': row[1],
                        'UniqueCode': row[2]
                    }
                else:
                    row_nums = df[df['ProductName'] == name].index.tolist()
                    errors['product'][name] = [r + 2 for r in row_nums]

        if errors['product']:
            error_messages = []
            for name, rows in errors['product'].items():
                error_messages.append(
                    f"존재하지 않거나 바코드가 없는 상품: {name} (행 {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})"
                )
            raise HTTPException(400, "\n".join(error_messages))

        # 사용유형 검증
        valid_types = plan_repo.get_types()
        if 'Type' in df.columns:
            invalid_types = []
            for idx, row in df.iterrows():
                type_val = str(row.get('Type', '')).strip()
                if type_val and type_val != 'nan' and type_val not in valid_types:
                    invalid_types.append(f"행 {idx + 2}: '{type_val}'")
            if invalid_types:
                raise HTTPException(400, f"유효하지 않은 사용유형이 있습니다: {', '.join(invalid_types[:10])}\n유효한 유형: {', '.join(valid_types)}")

        # 주문번호 기준 그룹핑
        groups = {}
        for idx, row in df.iterrows():
            has_plan_id = (
                'PlanID' in row
                and pd.notna(row.get('PlanID'))
                and str(row.get('PlanID')).strip() not in ['', 'nan']
            )

            if has_plan_id:
                key = f"ID_{row['PlanID']}"
            else:
                order_no = str(row.get('OrderNo', '')).strip()
                if not order_no or order_no == 'nan':
                    raise HTTPException(400, f"주문번호가 비어있습니다 (행 {idx + 2})")
                key = f"NEW_{order_no}"

            if key not in groups:
                groups[key] = []
            groups[key].append(idx)

        # WithdrawalPlan 레코드 준비
        plan_records = []
        for key, indices in groups.items():
            first_row = df.iloc[indices[0]]
            has_plan_id = key.startswith("ID_")

            plan_record = {
                'OrderNo': str(first_row.get('OrderNo', '')).strip() if pd.notna(first_row.get('OrderNo')) else '',
                'Title': None,  # 자동 생성
                'Type': str(first_row.get('Type', '')).strip() if pd.notna(first_row.get('Type')) and str(first_row.get('Type')).strip() != 'nan' else '기타',
                'OrdererName': str(first_row.get('OrdererName', '')).strip() if pd.notna(first_row.get('OrdererName')) and str(first_row.get('OrdererName')).strip() != 'nan' else None,
                'RecipientName': str(first_row.get('RecipientName', '')).strip() if pd.notna(first_row.get('RecipientName')) and str(first_row.get('RecipientName')).strip() != 'nan' else None,
                'Phone1': str(first_row.get('Phone1', '')).strip() if pd.notna(first_row.get('Phone1')) and str(first_row.get('Phone1')).strip() != 'nan' else None,
                'Phone2': str(first_row.get('Phone2', '')).strip() if pd.notna(first_row.get('Phone2')) and str(first_row.get('Phone2')).strip() != 'nan' else None,
                'Address1': str(first_row.get('Address1', '')).strip() if pd.notna(first_row.get('Address1')) and str(first_row.get('Address1')).strip() != 'nan' else None,
                'Address2': str(first_row.get('Address2', '')).strip() if pd.notna(first_row.get('Address2')) and str(first_row.get('Address2')).strip() != 'nan' else None,
                'DeliveryMethod': str(first_row.get('DeliveryMethod', '택배')).strip() if pd.notna(first_row.get('DeliveryMethod')) and str(first_row.get('DeliveryMethod')).strip() != 'nan' else '택배',
                'DeliveryMessage': str(first_row.get('DeliveryMessage', '')).strip() if pd.notna(first_row.get('DeliveryMessage')) and str(first_row.get('DeliveryMessage')).strip() != 'nan' else None,
                'DesiredDate': first_row.get('DesiredDate') if pd.notna(first_row.get('DesiredDate')) else None,
                'TrackingNo': str(first_row.get('TrackingNo', '')).strip() if pd.notna(first_row.get('TrackingNo')) and str(first_row.get('TrackingNo')).strip() != 'nan' else None,
                'Notes': str(first_row.get('Notes', '')).strip() if pd.notna(first_row.get('Notes')) and str(first_row.get('Notes')).strip() != 'nan' else None,
                'RequestedBy': user.user_id if user else None,
            }

            if has_plan_id:
                try:
                    plan_record['PlanID'] = int(first_row['PlanID'])
                except (ValueError, TypeError):
                    plan_record['PlanID'] = None

            plan_records.append(plan_record)

        plan_result = plan_repo.bulk_upsert(plan_records)

        plan_duplicates = plan_result.get('duplicates', [])
        if plan_duplicates:
            error_messages = []
            for dup in plan_duplicates[:10]:
                error_messages.append(f"중복 주문번호: {dup.get('order_no', '')}")
            raise HTTPException(400, "중복된 불출 계획이 있습니다.\n" + "\n".join(error_messages))

        plan_ids = plan_result.get('plan_ids', {})

        # WithdrawalPlanItem 레코드 준비
        item_records = []
        for key, indices in groups.items():
            first_row = df.iloc[indices[0]]
            order_no = str(first_row.get('OrderNo', '')).strip()
            plan_id = plan_ids.get(order_no)

            if not plan_id:
                continue

            # 기존 계획이 UPDATE된 경우 기존 Item 삭제 후 재등록
            has_plan_id = key.startswith("ID_")
            if has_plan_id:
                item_repo.delete_by_plan_id(plan_id)

            for idx in indices:
                row = df.iloc[idx]
                product_name = str(row.get('ProductName', '')).strip()
                if not product_name or product_name == 'nan':
                    continue

                prod_info = product_map.get(product_name, {})

                item_records.append({
                    'PlanID': plan_id,
                    'ProductName': prod_info.get('ProductName', product_name),
                    'BaseBarcode': prod_info.get('BaseBarcode'),
                    'UniqueCode': prod_info.get('UniqueCode'),
                    'Quantity': int(row.get('Quantity', 1)) if pd.notna(row.get('Quantity')) else 1,
                    'Notes': None,
                })

        items_inserted = 0
        if item_records:
            items_inserted = item_repo.bulk_insert(item_records)

        upload_end_time = datetime.now()
        duration = (upload_end_time - upload_start_time).total_seconds()

        # 활동 로그
        if user and request:
            activity_log_repo.log_action(
                user_id=user.user_id,
                action_type="CREATE",
                target_table="WithdrawalPlan",
                details={
                    "action": "EXCEL_UPLOAD",
                    "filename": file.filename,
                    "total_rows": len(df),
                    "plan_inserted": plan_result['inserted'],
                    "plan_updated": plan_result['updated'],
                    "items_inserted": items_inserted,
                    "duration_seconds": duration
                },
                ip_address=get_client_ip(request)
            )

        print(f"   업로드 완료: 계획 {plan_result['inserted']}건 삽입/{plan_result['updated']}건 수정, 상품 {items_inserted}건 삽입")

        return {
            "message": "업로드 완료",
            "total_rows": len(df),
            "plan_inserted": plan_result['inserted'],
            "plan_updated": plan_result['updated'],
            "items_inserted": items_inserted,
            "duration_seconds": duration
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"업로드 실패: {str(e)}")


def _parse_date(value):
    """날짜 값을 파싱 (YYYYMMDD, YYYY-MM-DD 등)"""
    if pd.isna(value):
        return None
    val_str = str(value).strip()
    if not val_str or val_str == 'nan':
        return None
    # YYYYMMDD 형식
    if len(val_str) == 8 and val_str.isdigit():
        try:
            return datetime.strptime(val_str, '%Y%m%d').strftime('%Y-%m-%d')
        except ValueError:
            pass
    # pandas datetime 변환
    try:
        dt = pd.to_datetime(value, errors='coerce')
        if pd.notna(dt):
            return dt.strftime('%Y-%m-%d')
    except Exception:
        pass
    return None


# ========== 단일 CRUD ==========

@router.get("/{plan_id}")
async def get_withdrawal_plan(plan_id: int, user: CurrentUser = Depends(require_permission("Withdrawal", "READ"))):
    """불출 계획 단일 조회"""
    try:
        item = plan_repo.get_by_id(plan_id)
        if not item:
            raise HTTPException(404, "불출 계획을 찾을 수 없습니다")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"불출 계획 조회 실패: {str(e)}")


@router.put("/{plan_id}")
@log_activity("UPDATE", "WithdrawalPlan", id_key="plan_id")
async def update_withdrawal_plan(
    plan_id: int,
    data: WithdrawalPlanUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("Withdrawal", "UPDATE"))
):
    """불출 계획 수정"""
    try:
        existing = plan_repo.get_by_id(plan_id)
        if not existing:
            raise HTTPException(404, "불출 계획을 찾을 수 없습니다")

        update_data = {k: v for k, v in data.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        plan_repo.update(plan_id, update_data)
        return {"message": "수정 완료", "plan_id": plan_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"불출 계획 수정 실패: {str(e)}")


@router.put("/{plan_id}/status")
@log_activity("UPDATE", "WithdrawalPlan", id_key="plan_id")
async def change_withdrawal_status(
    plan_id: int,
    data: StatusChangeRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Withdrawal", "UPDATE"))
):
    """불출 계획 상태 변경 (신청/승인/반려)"""
    try:
        existing = plan_repo.get_by_id(plan_id)
        if not existing:
            raise HTTPException(404, "불출 계획을 찾을 수 없습니다")

        current_status = existing['Status']
        new_status = data.status

        # 상태 전환 규칙 검증
        valid_transitions = {
            'DRAFT': ['PENDING'],
            'PENDING': ['APPROVED', 'REJECTED'],
            'REJECTED': ['PENDING'],
            'APPROVED': [],
        }
        if new_status not in valid_transitions.get(current_status, []):
            raise HTTPException(400, f"'{current_status}' → '{new_status}' 전환이 불가능합니다")

        plan_repo.update_status(
            plan_id, new_status,
            user_id=user.user_id,
            rejection_reason=data.rejection_reason
        )

        return {"message": f"상태 변경 완료: {new_status}", "plan_id": plan_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"상태 변경 실패: {str(e)}")


@router.delete("/{plan_id}")
@log_delete("WithdrawalPlan", id_param="plan_id")
async def delete_withdrawal_plan(
    plan_id: int,
    request: Request,
    user: CurrentUser = Depends(require_permission("Withdrawal", "DELETE"))
):
    """불출 계획 삭제"""
    try:
        existing = plan_repo.get_by_id(plan_id)
        if not existing:
            raise HTTPException(404, "불출 계획을 찾을 수 없습니다")
        plan_repo.delete(plan_id)
        return {"message": "삭제 완료", "plan_id": plan_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"불출 계획 삭제 실패: {str(e)}")


@router.post("/bulk-delete")
@log_bulk_delete("WithdrawalPlan")
async def bulk_delete_withdrawal_plans(
    data: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("Withdrawal", "DELETE"))
):
    """불출 계획 일괄 삭제"""
    try:
        if not data.ids:
            raise HTTPException(400, "삭제할 항목이 없습니다")
        deleted = plan_repo.bulk_delete(data.ids)
        return {"message": f"{deleted}건 삭제 완료", "deleted": deleted}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


# ========== 불출 상품 조회 ==========

@router.get("/{plan_id}/items")
async def get_withdrawal_items(plan_id: int, user: CurrentUser = Depends(require_permission("Withdrawal", "READ"))):
    """특정 불출 계획의 상품 목록"""
    try:
        items = item_repo.get_by_plan_id(plan_id)
        return {"data": items}
    except Exception as e:
        raise HTTPException(500, f"불출 상품 조회 실패: {str(e)}")