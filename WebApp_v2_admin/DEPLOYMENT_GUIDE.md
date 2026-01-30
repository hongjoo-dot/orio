# 배포 및 운영 가이드 - WebApp_v2_admin

이 문서는 AI에게 개발을 지시할 때 반드시 참조해야 하는 배포/운영 프로세스 가이드입니다.

---

## 1. 환경 구분

| 환경 | 목적 | 브랜치 | URL (예시) |
|---|---|---|---|
| **Local** | 개발 및 디버깅 | `feature/*`, `develop` | `localhost:8002` |
| **Staging** | 배포 전 최종 테스트 | `develop` | `staging.example.com` |
| **Production** | 실제 사용자 운영 | `main` | `app.example.com` |

> **핵심 원칙**: Production에는 Staging에서 검증된 코드만 올라간다.

---

## 2. 브랜치 전략

```
main (운영) ← develop (개발 통합) ← feature/* (기능 개발)
  ↑
  └── hotfix/* (긴급 수정)
```

### 브랜치 규칙

| 브랜치 | 생성 기준 | 병합 대상 | 설명 |
|---|---|---|---|
| `main` | - | - | 운영 코드. 직접 커밋 금지 |
| `develop` | `main`에서 최초 1회 | `main` | 다음 배포 준비 코드 |
| `feature/기능명` | `develop`에서 분기 | `develop` | 새 기능 개발 |
| `hotfix/설명` | `main`에서 분기 | `main` + `develop` | 운영 긴급 버그 수정 |

### AI에게 개발 지시 시 규칙

```
1. 새 기능 개발 시: "develop 브랜치에서 feature/기능명 브랜치를 만들어서 작업해"
2. 작업 완료 시: "develop에 병합해" (main에 직접 병합하지 않는다)
3. 긴급 수정 시: "main에서 hotfix/설명 브랜치를 만들어서 수정해"
```

---

## 3. 개발 프로세스 (기능 추가 시)

### Phase 1: 작업 시작

- [ ] develop 브랜치가 최신 상태인지 확인 (`git pull origin develop`)
- [ ] feature 브랜치 생성 (`git checkout -b feature/기능명 develop`)

### Phase 2: 개발

- [ ] 기존 아키텍처 패턴을 따르는지 확인 (CLAUDE.md 참조)
  - Backend: Repository 패턴 사용
  - Frontend: 공통 모듈(TableManager, ApiClient 등) 활용
  - Excel: ExcelBaseHandler 상속
- [ ] .env에 새 환경변수가 필요한 경우 `.env.example`에도 추가
- [ ] SQL 스키마 변경이 있으면 `sql/` 폴더에 마이그레이션 스크립트 작성
- [ ] 하드코딩된 값 없이 환경변수 또는 system_config 사용

### Phase 3: 자체 검증

- [ ] 로컬에서 `python app.py`로 실행 확인
- [ ] `/api/health` 헬스체크 정상 응답 확인
- [ ] 새로 만든 API 엔드포인트 `/docs`(Swagger)에서 테스트
- [ ] 브라우저 콘솔에 JavaScript 에러 없는지 확인
- [ ] 기존 기능이 깨지지 않았는지 주요 페이지 확인 (회귀 테스트)

### Phase 4: 코드 병합

- [ ] feature 브랜치를 develop에 병합
- [ ] 병합 후 develop에서 다시 한 번 실행 테스트

---

## 4. 배포 전 체크리스트 (Staging → Production)

### 4-1. 코드 품질

- [ ] 모든 기능이 develop 브랜치에 병합되어 있는가
- [ ] `print()` 디버그 문이 남아있지 않은가
- [ ] 불필요한 `console.log()`가 제거되었는가
- [ ] 주석 처리된 코드(dead code)가 정리되었는가
- [ ] 하드코딩된 localhost URL이나 테스트 데이터가 없는가

### 4-2. 보안

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는가
- [ ] JWT_SECRET_KEY가 운영용으로 설정되어 있는가 (개발용과 다르게)
- [ ] CORS 설정이 `allow_origins=["*"]`가 아닌 특정 도메인으로 제한되어 있는가
- [ ] SQL Injection 방지: QueryBuilder를 통한 파라미터 바인딩 사용 확인
- [ ] 민감 정보(비밀번호, API 키)가 로그에 출력되지 않는가
- [ ] 관리자 계정의 기본 비밀번호가 변경되었는가

### 4-3. 데이터베이스

- [ ] 스키마 변경 사항이 있는가? → 마이그레이션 스크립트 준비
- [ ] 마이그레이션 스크립트가 멱등성(idempotent)을 보장하는가 (중복 실행해도 안전)
- [ ] 운영 DB 백업을 수행했는가
- [ ] 새 테이블/컬럼에 적절한 인덱스가 있는가

### 4-4. 환경 설정

- [ ] 운영 환경의 `.env` 파일이 올바르게 설정되어 있는가
- [ ] 새로 추가된 환경변수가 운영 서버에도 설정되어 있는가
- [ ] `requirements.txt`가 최신 상태인가 (`pip freeze > requirements.txt`)
- [ ] Python 패키지 버전이 운영 환경과 호환되는가

### 4-5. 기능 테스트 (Staging에서)

- [ ] 로그인/로그아웃 정상 동작
- [ ] 권한별 접근 제어 확인 (Admin, Manager, Viewer)
- [ ] 주요 CRUD 동작 확인 (제품, BOM, 채널, 매출, 행사)
- [ ] 엑셀 업로드/다운로드 정상 동작
- [ ] 활동 로그가 정상 기록되는지 확인
- [ ] 에러 상황 시 적절한 메시지가 표시되는지 확인

---

## 5. 배포 절차

### 5-1. 배포 실행

```bash
# 1. develop → main 병합
git checkout main
git pull origin main
git merge develop
git push origin main

# 2. 운영 서버에서
git pull origin main
pip install -r requirements.txt    # 새 패키지가 있는 경우
# DB 마이그레이션 스크립트 실행 (있는 경우)

# 3. 서비스 재시작
# (배포 방식에 따라 다름 - 아래 "향후 개선" 참조)
```

### 5-2. 배포 직후 확인

- [ ] `/api/health` 헬스체크 응답 확인
- [ ] 로그인 정상 동작 확인
- [ ] 주요 페이지 접근 확인 (대시보드, 제품, 매출)
- [ ] 에러 로그 모니터링 (최소 30분)
- [ ] 사용자에게 배포 완료 공지

### 5-3. 롤백 절차 (문제 발생 시)

```bash
# 1. 이전 버전으로 복원
git checkout main
git revert HEAD    # 마지막 병합 취소
git push origin main

# 2. 운영 서버에서
git pull origin main
# 서비스 재시작

# 3. DB 변경이 있었다면 롤백 스크립트 실행
```

---

## 6. 운영 모니터링

### 일상 점검 항목

| 항목 | 주기 | 확인 방법 |
|---|---|---|
| 헬스체크 | 상시 | `/api/health` 응답 확인 |
| 에러 로그 | 매일 | 서버 로그 파일 확인 |
| 활동 로그 | 주 1회 | 활동 로그 페이지에서 이상 패턴 확인 |
| DB 용량 | 월 1회 | Azure Portal에서 DB 사용량 확인 |
| 보안 | 월 1회 | 비정상 로그인 시도, 권한 설정 점검 |

---

## 7. 버전 관리

### 버전 번호 규칙 (Semantic Versioning)

```
v주버전.부버전.패치  (예: v2.1.0)

주버전(Major): 큰 변경, 기존 기능 호환 안 될 수 있음
부버전(Minor): 새 기능 추가, 기존 기능 호환
패치(Patch):   버그 수정
```

### 릴리스 노트 작성

배포 시 아래 형식으로 변경 사항을 기록합니다:

```markdown
## v2.x.x (YYYY-MM-DD)

### 새 기능
- 행사 관리 기능 추가

### 개선
- UI 성능 개선

### 버그 수정
- 엑셀 업로드 시 날짜 형식 오류 수정

### 데이터베이스 변경
- Promotion 테이블 추가 (마이그레이션 필요)
```

---

## 8. AI에게 개발 지시 시 반드시 포함할 내용

AI(Claude 등)에게 코드 작성을 요청할 때 아래 사항을 함께 전달하세요:

### 필수 전달 사항

```
1. "CLAUDE.md와 DEPLOYMENT_GUIDE.md를 먼저 읽어"
2. "develop 브랜치에서 feature/기능명으로 브랜치를 만들어서 작업해"
3. "main 브랜치에 직접 커밋하지 마"
4. "작업 후 배포 전 체크리스트(섹션 4)를 확인해"
5. "DB 스키마 변경이 있으면 sql/ 폴더에 마이그레이션 스크립트를 만들어"
```

### 금지 사항

```
- main 브랜치에 직접 커밋/푸시
- .env 파일에 실제 비밀번호 커밋
- CORS를 allow_origins=["*"]로 설정한 채 배포
- requirements.txt 업데이트 없이 새 패키지 사용
- 마이그레이션 스크립트 없이 DB 스키마 변경
```

---

## 9. 향후 개선 권장 사항

현재 프로젝트에 아직 없지만 도입을 권장하는 항목입니다:

### 우선순위 높음

- [ ] **requirements.txt 갱신**: 현재 패키지 목록을 정확히 기록
- [ ] **CORS 설정 변경**: `allow_origins=["*"]` → 운영 도메인만 허용
- [ ] **.env 보안**: `.gitignore`에 `.env` 추가, 기존 커밋에서 제거
- [ ] **테스트 코드 작성**: 최소한 API 엔드포인트 동작 테스트 (`pytest`)

### 우선순위 중간

- [ ] **Docker 컨테이너화**: 환경 차이로 인한 문제 방지
- [ ] **CI/CD 파이프라인**: GitHub Actions로 자동 테스트/배포
- [ ] **로그 시스템 개선**: 파일/클라우드 로깅 (현재 콘솔만)
- [ ] **에러 알림**: Slack 연동 에러 알림 (slack_notifier.py 활용)

### 우선순위 낮음

- [ ] **모니터링 대시보드**: 서버 상태, 응답 시간 모니터링
- [ ] **자동 백업**: DB 자동 백업 스케줄 설정
- [ ] **부하 테스트**: 동시 접속자 수 대응 확인