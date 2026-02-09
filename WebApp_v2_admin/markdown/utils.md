# Utils (`utils/`)

공통 유틸리티 모듈. Excel 파일 처리 시스템과 Slack 알림.

---

## 1. Excel Handler System (`utils/excel/`)

Template Method 패턴으로 엑셀 처리 로직을 상속 구조로 관리.

### 클래스 계층

```
ExcelBaseHandler (부모 - 공통 기능)
├── ProductExcelHandler      # 제품 엑셀 import
├── SalesExcelHandler        # 매출 엑셀 import
├── PromotionExcelHandler    # 프로모션 엑셀
└── TargetExcelHandler       # 목표 엑셀
```

### ExcelBaseHandler (`base_handler.py`)

공통 엑셀 처리 기능 제공:

```python
class ExcelBaseHandler:
    # 파일 처리
    validate_file(file)           # 확장자 검증 (.xlsx, .xls)
    read_file(file) -> BytesIO    # 파일 읽기
    read_sheet(file, sheet_name)  # 특정 시트 읽기 (Pandas DataFrame)

    # 컬럼 매핑
    COLUMN_MAP = {
        "제품명": "Name",         # 한글 → 영문 매핑
        "브랜드": "BrandName",
    }
    map_columns(df)               # DataFrame 컬럼명 변환

    # DB 매핑 (Brand/Channel/Product 이름 → ID 변환)
    load_db_mappings()            # DB에서 lookup 데이터 로드
    resolve_brand(name) -> int    # 브랜드명 → BrandID
    resolve_product(name) -> int  # 제품명 → ProductID

    # 결과 추적
    add_success(row)              # 성공 행 기록
    add_failure(row, reason)      # 실패 행 기록 (사유 포함)
    get_result() -> Dict          # {success_count, failed_count, failed_rows, unmapped}
```

### ProductExcelHandler (`product_handler.py`)

```python
class ProductExcelHandler(ExcelBaseHandler):
    COLUMN_MAP = {
        "제품명": "Name",
        "브랜드": "BrandName",
        "규격": "Specification",
        ...
    }

    async def process_upload(self, file_content: bytes) -> Dict:
        """
        1. 파일 검증
        2. 시트 읽기
        3. 컬럼 매핑 (한글 → 영문)
        4. DB 매핑 로드 (Brand 이름 → ID)
        5. 행별 검증 + INSERT/UPDATE
        6. 결과 반환
        """
```

### SalesExcelHandler (`sales_handler.py`)

```python
class SalesExcelHandler(ExcelBaseHandler):
    COLUMN_MAP = {
        "제품명": "ProductName",
        "채널": "ChannelName",
        "매출액": "Revenue",
        "수량": "Quantity",
        ...
    }
    # Product + Channel + Brand 3중 매핑 필요
```

### Router에서 사용

```python
@router.post("/upload/excel")
async def upload_excel(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_permission("Product", "IMPORT"))
):
    handler = ProductExcelHandler()
    content = await file.read()
    result = await handler.process_upload(content)
    return result
    # → {success_count: 50, failed_count: 3, failed_rows: [...], unmapped_brands: [...]}
```

### 새 핸들러 작성 시

1. `ExcelBaseHandler` 상속
2. `COLUMN_MAP` 정의 (한글 → 영문)
3. `process_upload()` 구현
4. 필요 시 `load_db_mappings()` 오버라이드

---

## 2. Slack Notifier (`slack_notifier.py`)

Slack 웹훅을 통한 알림 발송.

```python
from utils.slack_notifier import SlackNotifier

notifier = SlackNotifier(webhook_url="https://hooks.slack.com/...")
notifier.send_message("배포 완료", channel="#deploy")
```

현재 선택적 사용 (메인 로직에 필수는 아님).
