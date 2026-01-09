# 복합키워드 수집 구현 가이드

## 개요

네이버 자동완성 API를 활용하여 복합키워드(예: "스크럽대디 스티커", "스크럽대디 수세미")를 수집하고, 각 복합키워드의 검색량을 수집하는 시스템입니다.

## 주요 변경사항

### 1. 데이터베이스 스키마 변경

**기존:**
- `HintKeyword`: 입력한 힌트 키워드
- `Keyword`: API가 반환한 연관 키워드

**변경 후:**
- `Keyword`: Keyword 테이블의 기본 키워드 (예: "스크럽대디")
- `CompoundKeyword`: 자동완성/검색된 복합키워드 (예: "스크럽대디 스티커")

**실행 방법:**
```sql
-- c:\Python\KeywordTrend\ALTER_RENAME_COLUMNS.sql 실행
```

### 2. 새로운 컴포넌트

#### `autocomplete_client.py`
- 네이버 자동완성 API 클라이언트
- 기본 키워드로 복합키워드 리스트 수집
- 상위 10개 결과 반환

**API 엔드포인트:**
```
https://ac.search.naver.com/nx/ac?q={키워드}&con=1&frm=nx&ans=2&r_format=json
```

### 3. 수집 로직 변경

#### 기존 로직:
```
Keyword 테이블 → KeywordTool API → 단일어 + 연관키워드 → DB
```

#### 새 로직:
```
Keyword 테이블 → [Priority 1만] 자동완성 API → 복합키워드 리스트
                                                    ↓
                                        각 복합키워드 → KeywordTool API → 검색량 → DB
```

### 4. Priority 별 수집 전략

**Priority 1:**
- 기본 키워드 검색량 수집 (예: "스크럽대디")
- 자동완성 API로 복합키워드 최대 10개 수집
- 각 복합키워드의 검색량 수집
- 연관키워드는 제외

**Priority 2+:**
- 기본 키워드 검색량만 수집
- 복합키워드 수집 안 함

## 실행 순서

### 1단계: 데이터베이스 스키마 업데이트

```sql
-- c:\Python\KeywordTrend\ALTER_RENAME_COLUMNS.sql 실행
-- HintKeyword → Keyword
-- Keyword → CompoundKeyword
```

### 2단계: 로컬 테스트

```bash
cd c:\Python\Azure\Functions\KeywordCollector
python -c "from shared.naver_keyword.autocomplete_client import NaverAutocompleteClient; client = NaverAutocompleteClient(); print(client.get_autocomplete_keywords('스크럽대디', 10))"
```

### 3단계: 전체 파이프라인 실행

```bash
cd c:\Python\Azure\Functions\KeywordCollector
python -c "from shared.naver_keyword.naver_pipeline import run_naver_ads_pipeline; run_naver_ads_pipeline()"
```

### 4단계: Azure Functions 배포

```bash
cd c:\Python\Azure\Functions\KeywordCollector
func azure functionapp publish <function-app-name>
```

## 수집 예시

**입력 키워드:** "스크럽대디" (Priority 1)

**자동완성 API 결과:**
```json
[
  "스크럽대디",
  "스크럽대디 스티커",
  "스크럽대디 수세미",
  "스크럽대디 종류",
  "스크럽대디 가격",
  ...
]
```

**최종 DB 저장 (NaverAdsSearchVolume):**

| KeywordID | Keyword | CompoundKeyword | MonthlyTotalSearchCount | IsHintKeyword |
|-----------|---------|-----------------|-------------------------|---------------|
| 9 | 스크럽대디 | 스크럽대디 | 12,300 | 1 |
| 9 | 스크럽대디 | 스크럽대디 스티커 | 2,400 | 0 |
| 9 | 스크럽대디 | 스크럽대디 수세미 | 1,800 | 0 |
| 9 | 스크럽대디 | 스크럽대디 종류 | 950 | 0 |

## 주요 특징

1. **연관키워드 제외**: 기존의 "생분해수세미", "친환경기업" 같은 단일어 연관키워드는 수집하지 않음
2. **복합키워드만 수집**: 자동완성으로 얻은 실제 검색어만 수집
3. **검색량 100 이상**: 월간 총 검색량 100 미만 키워드는 자동 필터링
4. **Priority 기반**: Priority 1 키워드만 복합키워드 확장 수집

## 파일 구조

```
KeywordCollector/
├── shared/
│   └── naver_keyword/
│       ├── autocomplete_client.py  (NEW)
│       ├── naver_pipeline.py       (MODIFIED)
│       ├── naver_uploader.py       (MODIFIED)
│       ├── api_client.py
│       ├── keyword_manager.py
│       └── config.py
└── function_app.py
```

## 주의사항

1. **자동완성 API는 비공식 API**입니다. 대량 크롤링은 금지되어 있으므로 적절한 Rate Limiting이 적용되어 있습니다.
2. **API 호출 간격**: 각 복합키워드 조회 간 0.5초, 기본 키워드 간 1초 대기
3. **Priority 1 키워드가 많으면** 실행 시간이 크게 증가할 수 있습니다. (복합키워드 각각 API 호출 필요)

## 문제 해결

### 자동완성 API 응답 없음
- 네트워크 문제 또는 일시적 차단 가능
- 로그에서 에러 확인 후 재시도

### 복합키워드 검색량이 0
- 월간 총 검색량 100 미만은 자동 필터링됨
- 실제 검색량이 매우 적은 키워드일 수 있음

### DB 업로드 실패
- 스키마 변경이 제대로 적용되었는지 확인
- `ALTER_RENAME_COLUMNS.sql` 실행 후 테이블 구조 확인

## 다음 단계

1. 수집된 복합키워드 데이터 분석
2. 검색량 트렌드 모니터링
3. 필요시 Priority 설정 조정
4. 자동완성 개수 제한 조정 (현재 10개)
