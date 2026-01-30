# Repository 통합 테스트 범위 및 환경

11-Sheet(또는 운영 대상 Sheet) 리포지토리의 기능 커버리지·안정성을 테스트로 고정하기 위한 범위·시나리오·환경 규칙.

**근거:** `docs/arch/10_Testability_Architecture.md`, `docs/tasks/backups/google_sheets_integration/*`

---

## 1. 통합 테스트 범위

### 1.1 필수 시트별 최소 시나리오

| 시트 | 리포지토리 클래스 | 최소 시나리오 |
|------|-------------------|----------------|
| T_Ledger | T_LedgerRepository | get_all, get_by_id, create(append), 헤더/행 매핑 |
| Position | PositionRepository | get_all, get_by_id(심볼), get_current_positions |
| History | HistoryRepository | get_all, get_by_id(date), create, 헤더 매핑 |
| Strategy_Performance | StrategyPerformanceRepository | get_all, create, 헤더 매핑 |
| R_Dash | R_DashRepository | get_all, 헤더 매핑 |
| Config_Scalp | ConfigScalpRepository | get_all, create/update(키 기준) |
| Config_Swing | ConfigSwingRepository | get_all, create/update(키 기준) |
| Portfolio | EnhancedPortfolioRepository | get_kpi_overview, update_kpi_overview (스키마 기반) |
| Performance | EnhancedPerformanceRepository | get_kpi_summary, update_kpi_summary (스키마 기반) |

- **CRUD + 핵심 쿼리:** 위 표의 get_all / get_by_id / create(·update) 및 시트별 특화 쿼리를 최소 1회씩 시나리오에 포함.
- **통과 기준:** 해당 시나리오가 Mock 기반으로 통과; 실 스프레드시트 연동은 선택(환경 변수 있을 때만).

---

## 2. 테스트 데이터·환경 분리

### 2.1 실 스프레드시트 vs Mock 경계

| 구분 | 용도 | 조건 |
|------|------|------|
| **Mock 기반** | 단위·통합 테스트, CI 기본 실행 | GoogleSheetsClient/Repository를 Mock 또는 Fake로 주입. 실제 API 호출 없음. |
| **실 스프레드시트** | E2E·수동 검증, 선택 통합 테스트 | `GOOGLE_CREDENTIALS_FILE`, `GOOGLE_SHEET_KEY` 등이 설정된 환경에서만 실행. |

- **CI 기본:** Mock만 사용. 실 API 호출 테스트는 스킵(마커 또는 env 검사).
- **실 스프레드시트 테스트:** `pytest -m "not live_sheets"` 또는 `SKIP_LIVE_SHEETS=1` 등으로 비활성화 가능해야 함.

### 2.2 CI 환경에서 민감정보(서비스 계정 키) 취급

- **원칙:** CI에서는 서비스 계정 키 파일/JSON을 저장소에 넣지 않는다.
- **실행 규칙:**
  - CI에 `GOOGLE_CREDENTIALS_FILE`, `GOOGLE_SHEET_KEY`가 **설정되지 않음** → 실 스프레드시트 테스트는 스킵.
  - 설정된 경우(예: 자체 runner·로컬)에만 실 연동 테스트 실행 가능.
- **문서화:** `tests/google_sheets_integration/README.md`에 “실 연동 테스트는 env 설정 시에만 실행” 명시.

---

## 3. 실패 시 원인 분리(로그/리포트)

테스트 실패 시 원인을 다음 세 가지로 구분할 수 있도록 한다.

| 원인 | 예시 | 식별 방법 |
|------|------|-----------|
| **인증** | credentials 누락/만료, 401 | `AuthenticationError`, "Authentication failed" 등 |
| **네트워크** | 타임아웃, 5xx, 429 | `APIError`, `RateLimitError`, status_code/메시지 |
| **스키마 불일치** | 헤더/컬럼 불일치, 필수 필드 누락 | `ValidationError`, `ValueError`(필수 필드), 빈 헤더/매핑 실패 |

- **구현:** 테스트/헬퍼에서 위 예외를 catch한 뒤, 실패 원인을 로그 또는 pytest 리포트(예: `pytest -v`, custom hook)에 분류해 남긴다.
- **Mock 테스트:** Mock 사용 시 인증/네트워크 실패는 발생하지 않으므로, 스키마/인터페이스 불일치 위주로 검증.

---

## 4. 코드 품질(테스트–코드 정합)

- 테스트는 **실제 인터페이스**(시그니처/경로/클래스명)와 일치해야 한다.
- **정리한 항목:**
  - `test_repositories.py`: PortfolioRepository/PerformanceRepository → EnhancedPortfolioRepository/EnhancedPerformanceRepository, 생성자에 `project_root` 포함.
  - `tests/runtime/data/test_google_sheets_client.py`: Mock 기반 + 실 API 테스트는 `live_sheets` 마커 또는 env로 스킵.

---

## 5. 완료 조건 충족

- [x] 리포지토리별 최소 CRUD + 핵심 쿼리 시나리오가 정의되어 있으며, Mock 기반으로 통과 가능.
- [x] 실패 시 원인(인증/네트워크/스키마 불일치)이 로그/리포트로 분리되도록 규칙이 문서화됨.
