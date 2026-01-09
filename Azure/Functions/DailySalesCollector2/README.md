# DailySalesCollector2

## 개요
**Azure Functions 기반 자동화된 판매 데이터 수집 파이프라인**입니다. 두 개의 이커머스 플랫폼(Cafe24, 사방넷)에서 일일 주문 데이터를 수집하여 통합 SQL 데이터베이스로 병합합니다.

---

## 프로젝트 구조
```
DailySalesCollector2/
├── function_app.py              # Azure Functions 진입점 (2개 타이머 트리거)
├── requirements.txt             # Python 의존성
├── host.json                    # Azure Functions 설정
├── local.settings.json          # 로컬 환경 설정
└── shared/
    ├── system_config.py         # DB 기반 설정 관리 (SystemConfig 테이블)
    ├── common/database.py       # Azure SQL 연결 유틸리티
    ├── cafe24/                  # Cafe24 파이프라인 모듈
    │   ├── collector.py         # OAuth 2.0 기반 주문 수집
    │   ├── main.py              # 파이프라인 오케스트레이터
    │   ├── upload_to_blob.py    # Blob 저장소 업로드
    │   ├── upload_to_db.py      # DB MERGE 작업
    │   └── upload_to_realtime.py # OrdersRealtime 통합
    └── sabangnet/               # 사방넷 파이프라인 모듈
        ├── sabangnet_api.py     # XML 기반 API 클라이언트
        ├── main.py              # 데이터 수집 오케스트레이터
        ├── upload_to_db.py      # DB MERGE 작업
        └── upload_to_realtime.py # OrdersRealtime 통합
```

---

## 핵심 기능

| 기능 | 설명 |
|------|------|
| **Cafe24 주문 수집** | REST API (OAuth 2.0), 롤링 10일 데이터 |
| **사방넷 주문 수집** | XML-RPC API, 롤링 7일 데이터 |
| **고객 데이터 수집** | Cafe24 고객 정보 동기화 |
| **Blob Storage 저장** | 원본 데이터 감사 추적용 저장 |
| **DB 통합** | MERGE 문으로 중복 방지 INSERT/UPDATE |
| **Slack 알림** | 수집 결과 및 오류 알림 |

---

## 실행 스케줄

| 함수 | UTC 시간 | KST 시간 | 주기 |
|------|----------|----------|------|
| `daily_sales_collector` | 09:00 | 18:00 | 매일 |
| `daily_customer_collector` | 09:10 | 18:10 | 매일 |

---

## 데이터 흐름

```
┌─────────────┐
│ Cafe24 API  │──┐
└─────────────┘  │     ┌──────────────┐     ┌─────────────┐     ┌─────────────────┐
                 ├────→│ Blob Storage │────→│  DB 테이블   │────→│ OrdersRealtime  │
┌─────────────┐  │     └──────────────┘     └─────────────┘     └────────┬────────┘
│ 사방넷 API  │──┘                                                       │
└─────────────┘                                                          ▼
                                                                 ┌──────────────┐
                                                                 │  Slack 알림  │
                                                                 └──────────────┘
```

### Cafe24 파이프라인
1. OAuth 2.0 토큰으로 Cafe24 API 호출
2. 롤링 10일간 주문 데이터 수집
3. Blob Storage에 JSON 파일 저장 (`cafe24-orders/YYYY-MM-DD.json`)
4. `Cafe24Orders`, `Cafe24OrdersDetail` 테이블에 MERGE
5. ProductID 매핑 후 `OrdersRealtime` 테이블에 통합
6. Slack으로 결과 알림

### 사방넷 파이프라인
1. Request XML 생성 및 Blob Storage 업로드
2. 사방넷 API 호출 (XML-RPC)
3. Response XML 파싱 후 JSON 저장
4. `SabangnetOrders`, `SabangnetOrdersDetail` 테이블에 MERGE
5. BOM 매핑 후 `OrdersRealtime` 테이블에 통합
6. Slack으로 결과 알림

---

## 외부 연동

| 서비스 | 용도 | 인증 방식 |
|--------|------|-----------|
| **Cafe24 API** | 자사몰 주문/고객 수집 | OAuth 2.0 Bearer Token |
| **사방넷 API** | 멀티채널 주문 수집 | Company ID + Auth Key (XML) |
| **Azure Blob Storage** | 원본 JSON/XML 저장 | Connection String |
| **Azure SQL Database** | 통합 데이터 웨어하우스 | ODBC Driver 18 |
| **Slack Webhook** | 운영 모니터링 | Webhook URL |

---

## 주요 DB 테이블

| 테이블 | 용도 | Merge Key |
|--------|------|-----------|
| `Cafe24Orders` | Cafe24 주문 헤더 | order_id |
| `Cafe24OrdersDetail` | Cafe24 주문 상세 | order_item_code |
| `SabangnetOrders` | 사방넷 주문 헤더 | IDX |
| `SabangnetOrdersDetail` | 사방넷 주문 상세 | IDX |
| `Cafe24Customers` | 고객 마스터 | member_id |
| `OrdersRealtime` | 통합 주문 테이블 | SourceChannel + SourceOrderID |
| `SystemConfig` | 런타임 설정 관리 | Category + ConfigKey |

---

## 설정 관리

### 우선순위
1. **SystemConfig 테이블** (DB 기반) - 최우선
2. **환경 변수** - 폴백
3. **하드코딩 기본값** - 최하위

### 주요 환경 변수

```bash
# Database
DB_SERVER=oriodatabase.database.windows.net
DB_DATABASE=oriodatabase
DB_USERNAME=oriodatabase
DB_PASSWORD=orio2025!@
DB_DRIVER={ODBC Driver 18 for SQL Server}

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...

# Cafe24 API (SystemConfig 테이블에서 관리)
CAFE24_MALL_ID=vorio01
CAFE24_CLIENT_ID=DF3fUZHlPqyYfnK7o8VViI
CAFE24_CLIENT_SECRET=dIOYk6ZHL1sogRqndsfmnG

# Sabangnet API (SystemConfig 테이블에서 관리)
SABANGNET_COMPANY_ID=vorio01
SABANGNET_AUTH_KEY=3S200SM93ASbFJ3RR3u0Z1S1E9CSrHX0GCN

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### SystemConfig 테이블 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| ConfigID | int | Primary Key |
| Category | nvarchar | 설정 카테고리 (Cafe24, Sabangnet, Common) |
| ConfigKey | nvarchar | 설정 키 |
| ConfigValue | nvarchar | 설정 값 |
| DataType | nvarchar | 데이터 타입 (int, bool, json, string) |
| IsActive | bit | 활성화 여부 |

---

## 의존성

```txt
azure-functions>=1.18.0          # Azure Functions 런타임
azure-storage-blob>=12.19.0      # Blob Storage SDK
pyodbc>=5.0.0                    # SQL Server 연결
requests>=2.31.0                 # HTTP API 호출
python-dotenv>=1.0.0             # .env 파일 로딩
python-dateutil>=2.8.0           # 날짜 처리
lxml>=5.0.0                      # XML 파싱 (사방넷)
```

---

## 배포

### Azure Functions 배포
```bash
func azure functionapp publish func-orio-daily-sales --python
```

### 로컬 실행
```bash
func start
```

---

## 에러 처리 및 모니터링

- **Try-Catch 블록**: 각 파이프라인 단계별 예외 처리
- **Slack 알림**: 실패 시 상세 오류 정보 전송
- **Application Insights**: Azure Functions 텔레메트리
- **Function Timeout**: 10분 (host.json)

---

## 설계 패턴

| 패턴 | 적용 위치 |
|------|-----------|
| Singleton | SystemConfig 인메모리 캐싱 |
| Context Manager | 데이터베이스 연결 (`with` 문) |
| Factory | 플랫폼별 Collector 클래스 |
| Template Method | 파이프라인 오케스트레이션 |
