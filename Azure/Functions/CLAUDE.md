# CLAUDE.md - Azure Functions

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 개요

Azure Functions 기반 자동화된 데이터 수집 파이프라인입니다. Timer Trigger를 사용하여 정해진 시간에 외부 API로부터 데이터를 수집하고 Azure SQL Database에 저장합니다.

## Functions 목록 및 배포 정보

```
Functions/
├── DailySalesCollector/        # 일일 매출 데이터 수집 (Cafe24 + Sabangnet)
│   └── Azure: func-orio-daily-sales
├── AdDataCollector/            # 광고 데이터 수집 (Meta + Naver)
│   └── Azure: func-addata-collector
├── KeywordCollector/           # 키워드 트렌드 데이터 수집 (Naver + Google)
│   └── Azure: func-keyword-collector
└── ViralMonitor/               # 브랜드 바이럴 모니터링
    ├── brands/frog/            # Azure: func-frog-monitor
    └── brands/scrubdaddy/      # Azure: func-scrubdaddy-monitor
```

## 실행 스케줄 요약

| Function App | Trigger | 스케줄 (UTC) | 한국시간 | 설명 |
|--------------|---------|-------------|---------|------|
| func-orio-daily-sales | `daily_sales_collector` | `0 0 9 * * *` | 18:00 | Cafe24 + Sabangnet 매출 수집 |
| func-orio-daily-sales | `daily_customer_collector` | `0 0 9 * * *` | 18:00 | Cafe24 고객 데이터 수집 |
| func-addata-collector | `daily_ad_data_collector` | `0 0 0 * * *` | 09:00 | Meta + Naver 광고 데이터 수집 |
| func-keyword-collector | `daily_keyword_collector` | `0 0 5 * * *` | 14:00 | 키워드 검색량 수집 |
| func-frog-monitor | `frog_monitor` | `0 0 */3 * * *` | 매 3시간 | 프로그 바이럴 모니터링 |
| func-scrubdaddy-monitor | `scrubdaddy_monitor` | `0 0 */3 * * *` | 매 3시간 | 스크럽대디 바이럴 모니터링 |

---

## 1. DailySalesCollector

### 개요
Cafe24 자사몰과 Sabangnet 멀티채널의 주문/고객 데이터를 수집합니다.

### Timer Triggers

| Trigger | 스케줄 | 설명 |
|---------|--------|------|
| `daily_sales_collector` | 18:00 KST | Cafe24 + Sabangnet 주문 수집 |
| `daily_customer_collector` | 18:00 KST | Cafe24 고객 정보 수집 |

### 데이터 파이프라인

```
[Cafe24 API] → Blob Storage → Cafe24Orders/Detail → OrdersRealtime
[Sabangnet API] → Blob Storage → SabangnetOrders/Detail → OrdersRealtime
[Cafe24 Customer API] → Cafe24Customers
```

### 대상 테이블

| 테이블 | 설명 | Merge 키 |
|--------|------|----------|
| `Cafe24Orders` | Cafe24 주문 헤더 | order_id |
| `Cafe24OrdersDetail` | Cafe24 주문 상세 | order_item_code |
| `SabangnetOrders` | Sabangnet 주문 헤더 | IDX |
| `SabangnetOrdersDetail` | Sabangnet 주문 상세 | IDX |
| `OrdersRealtime` | 통합 주문 테이블 | SourceChannel + SourceOrderID |
| `Cafe24Customers` | 고객 정보 | member_id |

### 디렉토리 구조

```
DailySalesCollector/
├── function_app.py              # Timer Trigger 정의
├── requirements.txt
├── host.json
├── local.settings.json
└── shared/
    ├── system_config.py         # DB 기반 설정 로더
    ├── common/
    │   └── database.py          # DB 연결 유틸리티
    ├── cafe24/
    │   ├── pipeline.py          # 전체 파이프라인 오케스트레이션
    │   ├── collector.py         # API 데이터 수집
    │   ├── customer_collector.py # 고객 데이터 수집
    │   ├── upload_to_blob.py    # Blob Storage 업로드
    │   ├── upload_to_db.py      # DB 업로드 (MERGE)
    │   ├── upload_to_realtime.py # OrdersRealtime MERGE
    │   ├── upload_customers_to_db.py # 고객 DB 업로드
    │   └── slack_notifier.py    # Slack 알림
    └── sabangnet/
        ├── pipeline.py          # Sabangnet 파이프라인
        ├── sabangnet_api.py     # API 클라이언트
        ├── azure_blob.py        # Blob 업로드
        ├── upload_to_db.py      # DB 업로드
        ├── upload_to_realtime.py # OrdersRealtime MERGE
        └── slack_notifier.py    # Slack 알림
```

### 배포

```bash
cd C:/Python/Azure/Functions/DailySalesCollector
func azure functionapp publish func-orio-daily-sales --python
```

---

## 2. AdDataCollector

### 개요
Meta Ads API와 Naver Ads API에서 광고 성과 데이터를 수집합니다.

### Timer Triggers

| Trigger | 스케줄 | 설명 |
|---------|--------|------|
| `daily_ad_data_collector` | 09:00 KST | Meta + Naver 광고 데이터 수집 |

### 데이터 파이프라인

```
[Meta Insights API] → AdDataMeta (일별 성과)
                    → AdDataMetaBreakdown (연령/성별/플랫폼 분석)

[Naver Ads API] → AdDataNaver (일별 성과)
```

### 대상 테이블

| 테이블 | 설명 | Merge 키 |
|--------|------|----------|
| `AdDataMeta` | Meta 일별 광고 성과 (63개 컬럼) | Date + AdID |
| `AdDataMetaBreakdown` | Meta Breakdown 데이터 | Date + AdID + BreakdownType + Age + Gender + ... |
| `AdDataNaver` | Naver 일별 광고 성과 | Date + AdID |

### 주요 기능 (최근 업데이트)

1. **Creative URL 추출 개선**
   - `ImageURL`: object_story_spec, asset_feed_spec에서 추출, 해시→URL 변환
   - `LinkURL`: link_data, video_data, template_data(Catalog Ads), link_urls(Dynamic Creative)
   - `PreviewURL`: 광고 미리보기 링크 (preview_shareable_link)

2. **Breakdown 데이터**
   - `age_gender`: 연령/성별별 성과
   - `publisher_platform`: 플랫폼별 성과 (Facebook, Instagram 등)

3. **Backfill 스크립트**
   - `backfill_creative_urls.py`: ImageURL, LinkURL, PreviewURL 백필
   - `backfill_breakdown_outbound.py`: OutboundClicks 백필
   - `backfill_historical.py`: 과거 데이터 백필

### 디렉토리 구조

```
AdDataCollector/
├── function_app.py              # Timer Trigger 정의
├── requirements.txt
├── host.json
├── local.settings.json
├── backfill_creative_urls.py    # Creative URL 백필 스크립트
├── backfill_breakdown_outbound.py
├── backfill_historical.py
└── shared/
    ├── database.py              # DB 연결
    ├── system_config.py         # SystemConfig 로더
    ├── slack_notifier.py        # Slack 알림
    ├── meta/
    │   ├── auth.py              # Meta API 인증 (Long-lived Token)
    │   ├── data_fetcher.py      # Insights/Creatives 수집
    │   ├── db_uploader.py       # AdDataMeta/Breakdown 업로드
    │   └── pipeline.py          # 전체 파이프라인
    └── naver/
        ├── auth.py              # Naver API 인증
        ├── data_fetcher.py      # 성과 데이터 수집
        ├── db_uploader.py       # AdDataNaver 업로드
        ├── name_mapper.py       # ID→이름 매핑
        └── pipeline.py          # 전체 파이프라인
```

### 배포

```bash
cd C:/Python/Azure/Functions/AdDataCollector
func azure functionapp publish func-addata-collector --python
```

---

## 3. KeywordCollector

### 개요
네이버/구글 키워드 검색량 데이터를 수집합니다.

### Timer Triggers

| Trigger | 스케줄 | 설명 |
|---------|--------|------|
| `daily_keyword_collector` | 14:00 KST | 네이버 + 구글 키워드 검색량 수집 |

### 데이터 파이프라인

```
[Naver Keyword API] → NaverKeywordStats
[Google Keyword API] → GoogleKeywordStats
```

### 대상 테이블

| 테이블 | 설명 |
|--------|------|
| `NaverKeywordStats` | 네이버 키워드 검색량/경쟁도 |
| `GoogleKeywordStats` | 구글 키워드 검색량/트렌드 |

### 디렉토리 구조

```
KeywordCollector/
├── function_app.py
├── requirements.txt
├── host.json
├── local.settings.json
└── shared/
    ├── common/
    │   ├── database.py
    │   ├── system_config.py
    │   └── slack_notifier.py
    ├── naver_keyword/
    │   ├── api_client.py        # 네이버 검색광고 API
    │   ├── autocomplete_client.py # 자동완성 API
    │   ├── keyword_manager.py   # 키워드 관리
    │   ├── naver_pipeline.py    # 네이버 파이프라인
    │   └── naver_uploader.py    # DB 업로더
    └── google_keyword/
        ├── api_client.py        # 구글 Ads API
        ├── google_pipeline.py   # 구글 파이프라인
        └── google_uploader.py   # DB 업로더
```

### 배포

```bash
cd C:/Python/Azure/Functions/KeywordCollector
func azure functionapp publish func-keyword-collector --python
```

---

## 4. ViralMonitor

### 개요
네이버 블로그/카페에서 브랜드 관련 바이럴 포스트를 모니터링하고 Slack으로 알림합니다.

### 브랜드별 Function Apps

| 브랜드 | Function App | 키워드 |
|--------|--------------|--------|
| 프로그 | `func-frog-monitor` | 개구리, 프로그, frog 등 |
| 스크럽대디 | `func-scrubdaddy-monitor` | 스크럽대디, scrubdaddy 등 |

### Timer Triggers

| Trigger | 스케줄 | 설명 |
|---------|--------|------|
| `frog_monitor` | 매 3시간 | 프로그 바이럴 모니터링 |
| `scrubdaddy_monitor` | 매 3시간 | 스크럽대디 바이럴 모니터링 |

### 데이터 흐름

```
[Naver Blog/Cafe 검색] → 중복 체크 (Azure Blob) → 새 포스트 감지 → Slack 알림
```

### 저장소

- **Azure Blob Storage**: `seen_posts.json` (중복 체크용)
- Container: `viral-scrubdaddy`, `viral-frog`

### 디렉토리 구조

```
ViralMonitor/
└── brands/
    ├── frog/
    │   ├── function_app.py
    │   ├── scheduler.py         # 모니터링 스케줄러
    │   ├── frog_collector.py    # 포스트 수집기
    │   ├── config.py            # 키워드/설정
    │   ├── requirements.txt
    │   └── common/
    │       ├── collectors/
    │       │   ├── base_collector.py
    │       │   └── naver_collector.py
    │       ├── notifiers/
    │       │   └── slack_notifier.py
    │       └── storage/
    │           └── duplicate_checker_azure.py
    └── scrubdaddy/
        └── (동일 구조)
```

### 배포

```bash
# 프로그 모니터
cd C:/Python/Azure/Functions/ViralMonitor/brands/frog
func azure functionapp publish func-frog-monitor --python

# 스크럽대디 모니터
cd C:/Python/Azure/Functions/ViralMonitor/brands/scrubdaddy
func azure functionapp publish func-scrubdaddy-monitor --python
```

---

## 개발 환경 설정

### 사전 요구사항

- **Python 3.10 또는 3.11** (Azure Functions v4 지원)
- **Azure Functions Core Tools v4**
  ```bash
  npm install -g azure-functions-core-tools@4 --unsafe-perm true
  ```
- **ODBC Driver 17 for SQL Server**

### 로컬 개발 환경 구축

```bash
# 1. Function 디렉토리로 이동
cd Azure/Functions/DailySalesCollector

# 2. 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. 패키지 설치
pip install -r requirements.txt

# 4. local.settings.json 설정 (아래 참조)

# 5. Functions 실행
func start
```

### local.settings.json 예시

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",

    "DB_SERVER": "your-server.database.windows.net",
    "DB_DATABASE": "your-database",
    "DB_USERNAME": "your-username",
    "DB_PASSWORD": "your-password",
    "DB_DRIVER": "{ODBC Driver 17 for SQL Server}",

    "AZURE_STORAGE_CONNECTION_STRING": "your-blob-connection-string",

    "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/..."
  }
}
```

---

## Cron 표현식 (Timer Trigger)

Azure Functions는 UTC 기준으로 실행됩니다. 한국시간(KST) = UTC + 9시간

```python
# 매일 오후 6시 (한국시간) = 오전 9시 (UTC)
"0 0 9 * * *"

# 매일 오전 9시 (한국시간) = 자정 (UTC)
"0 0 0 * * *"

# 매일 오후 2시 (한국시간) = 오전 5시 (UTC)
"0 0 5 * * *"

# 3시간마다
"0 0 */3 * * *"

# 5분마다
"0 */5 * * * *"
```

---

## SystemConfig 설정 로드

Functions는 데이터베이스의 `SystemConfig` 테이블에서 설정을 읽습니다:

```python
from shared.system_config import get_config

config = get_config()

# Section.Key 형식으로 조회 (기본값 지정 가능)
rolling_days = int(config.get('Cafe24', 'ROLLING_DAYS', 10))
ad_accounts = config.get('MetaAdAPI', 'AD_ACCOUNTS')  # JSON 문자열
usd_rate = int(config.get('Common', 'USD_TO_KRW_RATE', 1400))
```

---

## 공통 개발 명령어

### 로컬 테스트

```bash
# Functions 실행
func start

# 특정 함수만 실행
func start --functions daily_sales_collector
```

### Azure 배포

```bash
# Azure 로그인
az login

# Function App에 배포
func azure functionapp publish <function-app-name> --python
```

### 로그 확인

```bash
# 실시간 로그 스트리밍
az functionapp log tail --name <function-app-name> --resource-group <rg-name>
```

---

## 트러블슈팅

### 문제: Function이 실행되지 않음
- Application Insights에서 로그 확인
- Timer Trigger 스케줄 확인 (UTC 기준)
- `use_monitor=True` 설정 확인

### 문제: 패키지 Import 오류
- `requirements.txt`에 패키지 추가 후 재배포
- `sys.path.insert(0, ...)` 확인
- Python 버전 확인 (3.10 or 3.11)

### 문제: DB 연결 실패
- Application Settings에 DB 환경 변수 확인
- Azure SQL Firewall에 "Allow Azure services" 활성화
- ODBC Driver 설치 확인

### 문제: Meta API 토큰 만료
- `MetaAPIAuth.refresh_long_lived_token()` 호출 확인
- SystemConfig에서 토큰 갱신 날짜 확인
