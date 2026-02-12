"""
WithdrawalPlan (불출 계획) Router
- 캠페인 그룹 목록 + 상품 상세 조회
- 엑셀 업로드/다운로드
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import io
from datetime import datetime
from repositories.withdrawal_plan_repository import WithdrawalPlanRepository
from repositories import ProductRepository, ActivityLogRepository
from core import get_db_cursor
from core.dependencies import get_client_ip, CurrentUser
from core import log_activity, log_delete, log_bulk_delete, require_permission
from core.models import BulkDeleteAnyRequest as BulkDeleteRequest


# ========== Repository 인스턴스 ==========
plan_repo = WithdrawalPlanRepository()
product_repo = ProductRepository()
activity_log_repo = ActivityLogRepository()


# ========== Pydantic Models ==========

class WithdrawalPlanCreate(BaseModel):
    Title: str
    Date: str
    Type: str
    ERPCode: str
    PlannedQty: int = 1
    Notes: Optional[str] = None


class WithdrawalPlanUpdate(BaseModel):
    Title: Optional[str] = None
    Date: Optional[str] = None
    Type: Optional[str] = None
    ERPCode: Optional[str] = None
    PlannedQty: Optional[int] = None
    Notes: Optional[str] = None


class GroupDeleteRequest(BaseModel):
    group_id: int


class WithdrawalPlanBulkUpdateItem(BaseModel):
    PlanID: int
    PlannedQty: Optional[int] = None
    Notes: Optional[str] = None


class WithdrawalPlanBulkUpdateRequest(BaseModel):
    items: List[WithdrawalPlanBulkUpdateItem]


# ==========================================================
#  WithdrawalPlan Router
# ==========================================================
router = APIRouter(prefix="/api/withdrawal-plans", tags=["WithdrawalPlan"])


# ========== 캠페인 그룹 목록 (마스터) ==========

@router.get("/groups")
async def get_withdrawal_groups(
    year_month: Optional[str] = None,
    type: Optional[str] = None,
    title: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("WithdrawalPlan", "READ"))
):
    """캠페인 그룹 목록 조회 (마스터용)"""
    try:
        filters = {}
        if year_month:
            filters['year_month'] = year_month
        if type:
            filters['type'] = type
        if title:
            filters['title'] = title

        groups = plan_repo.get_groups(filters=filters)
        return {"data": groups, "total": len(groups)}
    except Exception as e:
        raise HTTPException(500, f"그룹 목록 조회 실패: {str(e)}")


# ========== 그룹 상세 (디테일) ==========

@router.get("/groups/{group_id}/items")
async def get_group_items(
    group_id: int,
    user: CurrentUser = Depends(require_permission("WithdrawalPlan", "READ"))
):
    """특정 그룹의 상품 목록 조회 (디테일용)"""
    try:
        items = plan_repo.get_by_group_id(group_id)
        return {"data": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(500, f"상품 목록 조회 실패: {str(e)}")


# ========== 전체 목록 조회 ==========

@router.get("")
async def get_withdrawal_plans(
    page: int = 1,
    limit: int = 20,
    year_month: Optional[str] = None,
    type: Optional[str] = None,
    title: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "DESC",
    user: CurrentUser = Depends(require_permission("WithdrawalPlan", "READ"))
):
    """불출 계획 전체 목록 조회"""
    try:
        ALLOWED_SORT = {
            "PlanID": "p.PlanID",
            "GroupID": "p.GroupID",
            "Title": "p.Title",
            "Date": "p.[Date]",
            "Type": "p.Type",
            "ProductName": "p.ProductName",
            "PlannedQty": "p.PlannedQty",
            "CreatedDate": "p.CreatedDate",
        }
        order_by = ALLOWED_SORT.get(sort_by, "p.[Date]")
        order_dir_safe = sort_dir if sort_dir in ("ASC", "DESC") else "DESC"

        filters = {}
        if year_month:
            filters['year_month'] = year_month
        if type:
            filters['type'] = type
        if title:
            filters['title'] = title

        result = plan_repo.get_list(
            page=page, limit=limit,
            filters=filters,
            order_by=order_by, order_dir=order_dir_safe
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"목록 조회 실패: {str(e)}")


# ========== 메타데이터 ==========

@router.get("/types")
async def get_withdrawal_types(user: CurrentUser = Depends(require_permission("WithdrawalPlan", "READ"))):
    """사용유형 목록"""
    try:
        return {"types": plan_repo.get_types()}
    except Exception as e:
        raise HTTPException(500, f"사용유형 목록 조회 실패: {str(e)}")


@router.get("/year-months")
async def get_year_months(user: CurrentUser = Depends(require_permission("WithdrawalPlan", "READ"))):
    """년월 목록"""
    try:
        return {"year_months": plan_repo.get_year_months()}
    except Exception as e:
        raise HTTPException(500, f"년월 목록 조회 실패: {str(e)}")


# ========== 엑셀 다운로드 ==========

@router.get("/download")
async def download_withdrawal_plans(
    year_month: Optional[str] = None,
    type: Optional[str] = None,
    group_id: Optional[int] = None,
    group_ids: Optional[str] = None,  # 복수 그룹 ID (콤마 구분)
    ids: Optional[str] = None,
    user: CurrentUser = Depends(require_permission("WithdrawalPlan", "EXPORT"))
):
    """불출 계획 엑셀 다운로드"""
    try:
        data = []

        if ids:
            # 특정 ID들
            id_list = [int(id.strip()) for id in ids.split(',') if id.strip()]
            data = plan_repo.get_by_ids(id_list)
        elif group_ids:
            # 복수 그룹 (체크박스 선택)
            group_id_list = [int(gid.strip()) for gid in group_ids.split(',') if gid.strip()]
            for gid in group_id_list:
                data.extend(plan_repo.get_by_group_id(gid))
        elif group_id:
            # 특정 그룹
            data = plan_repo.get_by_group_id(group_id)
        else:
            # 선택 없음 → 빈 양식
            data = []

        # 엑셀 컬럼 정의
        export_columns = ['계획ID(수정X)', '캠페인ID(수정X)', '캠페인명', '일자(YYYY-MM-DD)', '사용유형', '품목코드', '예정수량', '메모']
        id_column_indices = [0, 1]  # 계획ID, 캠페인ID (빨간색)

        rows = []
        for item in data:
            rows.append({
                '계획ID(수정X)': item.get('PlanID'),
                '캠페인ID(수정X)': item.get('GroupID'),
                '캠페인명': item.get('Title'),
                '일자(YYYY-MM-DD)': item.get('Date'),
                '사용유형': item.get('Type'),
                '품목코드': item.get('ERPCode'),
                '예정수량': item.get('PlannedQty'),
                '메모': item.get('Notes'),
            })

        if not rows:
            df = pd.DataFrame(columns=export_columns)
        else:
            df = pd.DataFrame(rows, columns=export_columns)

        # 안내 시트
        guide_data = [
            ['[불출 계획 업로드 안내]', ''],
            ['', ''],
            ['■ 업로드 방식', ''],
            ['계획ID가 있는 행', '해당 행을 수정합니다.'],
            ['계획ID가 없는 행', '신규 등록합니다. 같은 캠페인명은 동일 그룹으로 묶입니다.'],
            ['', ''],
            ['■ 컬럼 설명', ''],
            ['계획ID(수정X) (빨간색)', '수정할 행 식별용 (비워두면 신규 등록, 값 수정 금지)'],
            ['캠페인ID(수정X) (빨간색)', '캠페인 그룹 식별용 (자동 설정, 값 수정 금지)'],
            ['캠페인명', '캠페인/건명 (같은 이름은 동일 그룹)'],
            ['일자(YYYY-MM-DD)', 'YYYY-MM-DD 형식'],
            ['사용유형', '인플루언서, 증정, 업체샘플, 직원복지, 기타'],
            ['품목코드', '품목코드 (필수, ProductBox 테이블의 ERPCode, 상품명 자동 매핑)'],
            ['예정수량', '숫자'],
            ['메모', '메모'],
        ]
        guide_df = pd.DataFrame(guide_data, columns=['항목', '설명'])

        # 드롭다운용 데이터 (ProductBox ERPCode)
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT DISTINCT pb.ERPCode
                FROM ProductBox pb
                INNER JOIN Product p ON pb.ProductID = p.ProductID
                WHERE p.Status = 'YES'
                ORDER BY pb.ERPCode
            """)
            erp_codes = [row[0] for row in cursor.fetchall()]

        withdrawal_types = plan_repo.get_types()

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='불출계획')
            guide_df.to_excel(writer, index=False, sheet_name='안내')

            workbook = writer.book
            worksheet = writer.sheets['불출계획']

            # 목록 시트 (드롭다운 소스)
            list_sheet = workbook.add_worksheet('목록')
            list_sheet.hide()

            # A열: 품목코드 목록
            for i, code in enumerate(erp_codes):
                list_sheet.write(i, 0, code)
            # B열: 사용유형 목록
            for i, t in enumerate(withdrawal_types):
                list_sheet.write(i, 1, t)

            max_row = max(len(df) + 100, 1000)

            # 품목코드 드롭다운 (인덱스 5)
            if erp_codes:
                worksheet.data_validation(1, 5, max_row, 5, {
                    'validate': 'list',
                    'source': f'=목록!$A$1:$A${len(erp_codes)}',
                    'input_message': '품목코드를 선택하세요',
                    'error_message': '목록에서 선택해주세요'
                })

            # 사용유형 드롭다운 (인덱스 4)
            if withdrawal_types:
                worksheet.data_validation(1, 4, max_row, 4, {
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
            col_widths = [14, 14, 25, 18, 12, 15, 10, 30]
            for i, width in enumerate(col_widths):
                worksheet.set_column(i, i, width)

            guide_sheet = writer.sheets['안내']
            guide_sheet.set_column(0, 0, 30)
            guide_sheet.set_column(1, 1, 50)

        output.seek(0)
        filename = f"withdrawal_plan_{year_month or 'all'}.xlsx"
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
async def upload_withdrawal_plans(
    file: UploadFile = File(...),
    request: Request = None,
    user: CurrentUser = Depends(require_permission("WithdrawalPlan", "UPLOAD"))
):
    """불출 계획 엑셀 업로드"""
    try:
        upload_start_time = datetime.now()

        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(400, "엑셀 파일(.xlsx, .xls)만 업로드 가능합니다")

        content = await file.read()
        excel_file = io.BytesIO(content)
        df = pd.read_excel(excel_file)

        # 컬럼 매핑 (수정X 붙은 컬럼명도 지원)
        column_map = {
            '계획ID(수정X)': 'PlanID',
            '캠페인ID(수정X)': 'GroupID',
            '계획ID': 'PlanID',  # 기존 양식 호환
            '캠페인ID': 'GroupID',  # 기존 양식 호환
            '캠페인명': 'Title',
            '일자(YYYY-MM-DD)': 'Date',
            '사용유형': 'Type',
            '품목코드': 'ERPCode',
            '고유코드': 'ERPCode',  # 기존 양식 호환
            '예정수량': 'PlannedQty',
            '메모': 'Notes',
        }
        df = df.rename(columns=column_map)

        # 필수 컬럼 확인
        required_cols = ['Title', 'Date', 'Type', 'ERPCode']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(400, f"필수 컬럼이 없습니다: {missing_cols}")

        # 날짜 변환
        if 'Date' in df.columns:
            df['Date'] = df['Date'].apply(_parse_date)

        # 수량 변환
        if 'PlannedQty' in df.columns:
            df['PlannedQty'] = pd.to_numeric(df['PlannedQty'], errors='coerce').fillna(1).astype(int)

        # ERPCode → UniqueCode, ProductName 매핑
        erp_codes_unique = df['ERPCode'].dropna().unique().tolist()
        erp_codes_unique = [str(c).strip() for c in erp_codes_unique if c and str(c).strip()]

        product_map = {}
        errors = []

        for code in erp_codes_unique:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT pb.ERPCode, p.UniqueCode, p.Name
                    FROM ProductBox pb
                    INNER JOIN Product p ON pb.ProductID = p.ProductID
                    WHERE pb.ERPCode = ?
                """, (code,))
                row = cursor.fetchone()
                if row:
                    product_map[code] = {'ERPCode': row[0], 'UniqueCode': row[1], 'ProductName': row[2]}
                else:
                    row_nums = df[df['ERPCode'].astype(str).str.strip() == code].index.tolist()
                    errors.append(f"존재하지 않는 품목코드: {code} (행 {', '.join(map(str, [r + 2 for r in row_nums[:5]]))})")

        if errors:
            raise HTTPException(400, "\n".join(errors))

        # 사용유형 검증
        valid_types = plan_repo.get_types()
        for idx, row in df.iterrows():
            type_val = str(row.get('Type', '')).strip()
            if type_val and type_val not in valid_types:
                raise HTTPException(400, f"유효하지 않은 사용유형: '{type_val}' (행 {idx + 2})")

        # 레코드 준비
        records = []
        for idx, row in df.iterrows():
            erp_code = str(row.get('ERPCode', '')).strip()
            product_info = product_map.get(erp_code, {})

            record = {
                'Title': str(row.get('Title', '')).strip(),
                'Date': row.get('Date'),
                'Type': str(row.get('Type', '')).strip(),
                'ERPCode': erp_code,
                'UniqueCode': product_info.get('UniqueCode', ''),
                'ProductName': product_info.get('ProductName', ''),
                'PlannedQty': int(row.get('PlannedQty', 1)) if pd.notna(row.get('PlannedQty')) else 1,
                'Notes': str(row.get('Notes', '')).strip() if pd.notna(row.get('Notes')) and str(row.get('Notes')).strip() != 'nan' else None,
                'CreatedBy': user.user_id if user else None,
            }

            # PlanID가 있으면 UPDATE
            if 'PlanID' in row and pd.notna(row.get('PlanID')):
                try:
                    record['PlanID'] = int(row['PlanID'])
                except (ValueError, TypeError):
                    pass

            # GroupID가 있으면 사용 (없으면 Title 기준 자동 설정)
            if 'GroupID' in row and pd.notna(row.get('GroupID')):
                try:
                    record['GroupID'] = int(row['GroupID'])
                except (ValueError, TypeError):
                    pass

            records.append(record)

        # UPSERT 실행
        result = plan_repo.bulk_upsert(records)

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
                    "inserted": result['inserted'],
                    "updated": result['updated'],
                    "duration_seconds": duration
                },
                ip_address=get_client_ip(request)
            )

        return {
            "message": "업로드 완료",
            "total_rows": len(df),
            "inserted": result['inserted'],
            "updated": result['updated'],
            "duration_seconds": duration
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"업로드 실패: {str(e)}")


def _parse_date(value):
    """날짜 파싱"""
    if pd.isna(value):
        return None
    val_str = str(value).strip()
    if not val_str or val_str == 'nan':
        return None
    # YYYYMMDD
    if len(val_str) == 8 and val_str.isdigit():
        try:
            return datetime.strptime(val_str, '%Y%m%d').strftime('%Y-%m-%d')
        except ValueError:
            pass
    # pandas datetime
    try:
        dt = pd.to_datetime(value, errors='coerce')
        if pd.notna(dt):
            return dt.strftime('%Y-%m-%d')
    except Exception:
        pass
    return None


# ========== 인라인 편집 일괄 저장 ==========

@router.put("/bulk-update")
@log_activity("UPDATE", "WithdrawalPlan")
async def bulk_update_withdrawal_plans_inline(
    data: WithdrawalPlanBulkUpdateRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("WithdrawalPlan", "UPDATE"))
):
    """불출 계획 인라인 편집 일괄 저장"""
    try:
        items = [item.dict() for item in data.items]
        result = plan_repo.bulk_update_items(items)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 수정 실패: {str(e)}")


# ========== 단건 CRUD ==========

@router.get("/{plan_id}")
async def get_withdrawal_plan(plan_id: int, user: CurrentUser = Depends(require_permission("WithdrawalPlan", "READ"))):
    """단건 조회"""
    try:
        item = plan_repo.get_by_id(plan_id)
        if not item:
            raise HTTPException(404, "데이터를 찾을 수 없습니다")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"조회 실패: {str(e)}")


@router.post("")
@log_activity("CREATE", "WithdrawalPlan", id_key="PlanID")
async def create_withdrawal_plan(
    data: WithdrawalPlanCreate,
    request: Request,
    user: CurrentUser = Depends(require_permission("WithdrawalPlan", "CREATE"))
):
    """단건 생성"""
    try:
        # ERPCode → UniqueCode, ProductName 매핑
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT pb.ERPCode, p.UniqueCode, p.Name
                FROM ProductBox pb
                INNER JOIN Product p ON pb.ProductID = p.ProductID
                WHERE pb.ERPCode = ?
            """, (data.ERPCode,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(400, f"존재하지 않는 품목코드: {data.ERPCode}")

        # GroupID 결정
        group_id = plan_repo.get_group_id_by_title(data.Title)
        if not group_id:
            group_id = plan_repo.get_next_group_id()

        create_data = {
            'GroupID': group_id,
            'Title': data.Title,
            'Date': data.Date,
            'Type': data.Type,
            'ERPCode': data.ERPCode,
            'ProductName': row[2],
            'UniqueCode': row[1],
            'PlannedQty': data.PlannedQty,
            'Notes': data.Notes,
            'CreatedBy': user.user_id if user else None,
        }

        plan_id = plan_repo.create(create_data)
        return {"PlanID": plan_id, "message": "생성 완료"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"생성 실패: {str(e)}")


@router.put("/{plan_id}")
@log_activity("UPDATE", "WithdrawalPlan", id_key="PlanID")
async def update_withdrawal_plan(
    plan_id: int,
    data: WithdrawalPlanUpdate,
    request: Request,
    user: CurrentUser = Depends(require_permission("WithdrawalPlan", "UPDATE"))
):
    """단건 수정"""
    try:
        existing = plan_repo.get_by_id(plan_id)
        if not existing:
            raise HTTPException(404, "데이터를 찾을 수 없습니다")

        update_data = {k: v for k, v in data.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(400, "수정할 데이터가 없습니다")

        # ERPCode가 변경되면 UniqueCode, ProductName도 업데이트
        if 'ERPCode' in update_data:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT pb.ERPCode, p.UniqueCode, p.Name
                    FROM ProductBox pb
                    INNER JOIN Product p ON pb.ProductID = p.ProductID
                    WHERE pb.ERPCode = ?
                """, (update_data['ERPCode'],))
                row = cursor.fetchone()
                if not row:
                    raise HTTPException(400, f"존재하지 않는 품목코드: {update_data['ERPCode']}")
                update_data['UniqueCode'] = row[1]
                update_data['ProductName'] = row[2]

        plan_repo.update(plan_id, update_data)
        return {"PlanID": plan_id, "message": "수정 완료"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"수정 실패: {str(e)}")


@router.delete("/{plan_id}")
@log_delete("WithdrawalPlan", id_param="plan_id")
async def delete_withdrawal_plan(
    plan_id: int,
    request: Request,
    user: CurrentUser = Depends(require_permission("WithdrawalPlan", "DELETE"))
):
    """단건 삭제"""
    try:
        existing = plan_repo.get_by_id(plan_id)
        if not existing:
            raise HTTPException(404, "데이터를 찾을 수 없습니다")
        plan_repo.delete(plan_id)
        return {"message": "삭제 완료"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"삭제 실패: {str(e)}")


@router.post("/bulk-delete")
@log_bulk_delete("WithdrawalPlan")
async def bulk_delete_withdrawal_plans(
    data: BulkDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("WithdrawalPlan", "DELETE"))
):
    """일괄 삭제"""
    try:
        if not data.ids:
            raise HTTPException(400, "삭제할 항목이 없습니다")
        deleted = plan_repo.bulk_delete(data.ids)
        return {"message": f"{deleted}건 삭제 완료", "deleted_count": deleted, "deleted_ids": data.ids}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"일괄 삭제 실패: {str(e)}")


@router.post("/groups/delete")
@log_activity("DELETE", "WithdrawalPlan", id_key="group_id")
async def delete_withdrawal_group(
    data: GroupDeleteRequest,
    request: Request,
    user: CurrentUser = Depends(require_permission("WithdrawalPlan", "DELETE"))
):
    """그룹 전체 삭제"""
    try:
        deleted = plan_repo.delete_by_group_id(data.group_id)
        if deleted == 0:
            raise HTTPException(404, "그룹을 찾을 수 없습니다")
        return {"message": f"{deleted}건 삭제 완료", "group_id": data.group_id, "deleted_count": deleted}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"그룹 삭제 실패: {str(e)}")
