# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

이 프로젝트는 전자상거래 운영을 위한 통합 데이터 파이프라인 및 ERP 관리 시스템입니다.

### 주요 구성 요소

- **Functions/**: Azure Functions 기반 자동 데이터 수집 (Timer Trigger)
- **WebApp_v2_admin/**: FastAPI 기반 관리자 웹 애플리케이션
- **DATA_PIPELINE_ARCHITECTURE.md**: 데이터 파이프라인 아키텍처 상세 문서

### 주요 기술 스택
- Python 3.10-3.11
- Azure Functions v4
- FastAPI
- SQL Server (Azure)
- Azure Blob Storage

## 프로젝트 구조

```
Azure/
├── Functions/                          # Azure Functions (자동화 파이프라인)
│   ├── DailySalesCollector/           # Cafe24 + Sabangnet 매출 데이터
│   ├── AdDataCollector/               # Meta + Naver 광고 데이터
│   ├── KeywordCollector/              # 키워드 트렌드 데이터
│   └── ViralMonitor/                  # 브랜드 바이럴 모니터링
│
├── WebApp_v2_admin/                   # FastAPI 관리 애플리케이션
│   ├── app.py                         # 메인 애플리케이션
│   ├── core/                          # 핵심 유틸리티 (Repository, QueryBuilder, DB)
│   ├── repositories/                  # 데이터 접근 계층
│   ├── routers/                       # API 엔드포인트
│   ├── templates/                     # Jinja2 HTML 템플릿
│   └── static/                        # CSS/JS 정적 파일
│
└── DATA_PIPELINE_ARCHITECTURE.md      # 파이프라인 아키텍처 문서
```

## 데이터 파이프라인 아키텍처

### 3개의 메인 파이프라인

본 시스템은 3개의 독립적인 데이터 파이프라인을 통해 주문 데이터를 수집하고 `OrdersRealtime` 테이블로 통합합니다.

#### 1. Sabangnet 파이프라인 (3P 멀티채널)
- **트리거**: 매일 18:00 (한국시간) = 09:00 (UTC)
- **롤링 기간**: 최근 7일
- **데이터 흐름**: API → Blob → SabangnetOrders/Detail → OrdersRealtime
- **필터 조건**: `DELIVERY_CONFIRM_DATE IS NOT NULL` (출고 완료된 주문만)
- **Merge 키**: `SabangnetIDX`

#### 2. Cafe24 파이프라인 (3P 자사몰)
- **트리거**: 매일 18:00 (한국시간) = 09:00 (UTC)
- **롤링 기간**: 최근 10일
- **데이터 흐름**: API → Blob → Cafe24Orders/Detail → OrdersRealtime
- **필터 조건**: `shipped_date IS NOT NULL` (출고된 주문만)
- **Merge 키**: `order_item_code`

#### 3. ERP 파이프라인 (1P 직접 주문)
- **트리거**: WebApp UI에서 수동 실행
- **데이터 흐름**: Excel 업로드 → ERPSales → 수동 검토 → OrdersRealtime
- **필터 조건**: `Channel.LiveSource = 'ERP'` + 사용자 선택 날짜 범위
- **Merge 키**: `ERPIDX`

### 파이프라인 실행 스케줄

| Function | 스케줄 (UTC) | 한국시간 | 설명 |
|----------|-------------|---------|------|
| `daily_sales_collector` | `0 0 9 * * *` | 18:00 | Cafe24 + Sabangnet 매출 수집 |
| `daily_customer_collector` | `0 0 9 * * *` | 18:00 | Cafe24 고객 데이터 수집 |
| `daily_ad_data_collector` | `0 0 0 * * *` | 09:00 | Meta + Naver 광고 데이터 수집 |

## 하위 문서

각 구성 요소에 대한 상세한 개발 가이드는 다음 문서를 참조하세요:

- **Functions/CLAUDE.md**: Azure Functions 개발 가이드
  - 로컬 개발 환경 설정
  - Timer Trigger 추가 방법
  - 배포 및 모니터링
  - 공통 모듈 사용법

- **WebApp_v2_admin/CLAUDE.md**: FastAPI 웹앱 개발 가이드
  - Repository 패턴 사용법
  - Query Builder 사용법
  - API 엔드포인트 추가 방법
  - 인증 및 권한 관리

- **DATA_PIPELINE_ARCHITECTURE.md**: 데이터 파이프라인 상세 아키텍처
  - 파이프라인별 필터 조건
  - 매핑 로직
  - Merge 조건
  - 데이터 흐름도

## 환경 설정

### 공통 환경 변수

모든 구성 요소에서 필요한 데이터베이스 연결 정보:

```ini
DB_SERVER=your-server.database.windows.net
DB_DATABASE=your-database
DB_USERNAME=your-username
DB_PASSWORD=your-password
DB_DRIVER={ODBC Driver 17 for SQL Server}
```

### 설정 위치

- **Functions**: `local.settings.json` (로컬) / Azure Portal Application Settings (프로덕션)
- **WebApp**: `.env` 파일

## SystemConfig 기반 설정 관리

Functions와 WebApp은 데이터베이스의 `SystemConfig` 테이블에서 설정을 읽어옵니다.

```python
from shared.system_config import get_config

config = get_config()
rolling_days = config.get('CAFE24_ROLLING_DAYS', 10)
slack_webhook = config.get('SLACK_WEBHOOK_URL')
```

설정은 WebApp의 `/system-config` 페이지에서 관리할 수 있습니다.

## 빠른 시작

### Functions 로컬 실행

```bash
cd Azure/Functions/DailySalesCollector
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
func start
```

### WebApp 로컬 실행

```bash
cd Azure/WebApp_v2_admin
pip install -r requirements.txt
python app.py
# 접속: http://localhost:8002
```

## 주요 참고 문서

1. **Azure Functions 개발**: `Functions/CLAUDE.md`
2. **WebApp 개발**: `WebApp_v2_admin/CLAUDE.md`
3. **파이프라인 아키텍처**: `DATA_PIPELINE_ARCHITECTURE.md`
4. **DailySalesCollector 가이드**: `Functions/DailySalesCollector/README.md`
5. **WebApp 아키텍처**: `WebApp_v2_admin/ARCHITECTURE.md`
