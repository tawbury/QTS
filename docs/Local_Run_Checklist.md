# QTS 로컬 구동 점검 체크리스트

**검수 일자**: 2026-02-01  
**목적**: 실제 로컬에서 프로그램 구동 전 전체 점검

---

## 1. 점검 결과 요약

| 구분 | 상태 | 비고 |
|------|------|------|
| **--local-only 모드** | ✅ 통과 | Mock 클라이언트로 API 없이 실행 |
| **프로덕션 모드** | ⚠️ 설정 필요 | .env + Google Sheets + Broker 설정 |
| **핵심 테스트** | ✅ 348 passed | live_sheets, real_broker 제외 |
| **Import 오류** | ✅ 수정 완료 | `Protocol` import 경로 수정 |

---

## 2. 실행 모드별 요구사항

### 2.1 로컬 전용 모드 (권장: 첫 실행 시)

```bash
python main.py --local-only --max-iterations 5 -v
```

| 항목 | 필수 | 경로/설명 |
|------|------|-----------|
| **config/local/config_local.json** | ✅ | 필수. `config` 디렉터리 생성 후 `local/config_local.json` 배치 |
| **config/schema/credentials.json** | ✅ | 스키마 정의 JSON (시트 구조). Mock 모드에서도 Repository 초기화 시 로드 |
| **Python 3.11+** | ✅ | `runtime_checks`에서 검증 |
| **.env** | ❌ | local-only에서는 불필요 |
| **Google Sheets** | ❌ | 불필요 (MockSheetsClient 사용) |
| **Broker API** | ❌ | 불필요 (NoopBroker 사용) |

**config_local.json 필수 키** (ConfigValidator 검증):

```
INTERVAL_MS, ERROR_BACKOFF_MS, ERROR_BACKOFF_MAX_RETRIES,
RUN_MODE, LIVE_ENABLED, trading_enabled,
PIPELINE_PAUSED, KS_ENABLED, BASE_EQUITY
```

**config_local.json 예시** (category.subcategory.key 형식으로 get_flat 자동 매칭):

```json
[
  {"category": "SYSTEM", "subcategory": "LOOP", "key": "INTERVAL_MS", "value": "1000"},
  {"category": "SYSTEM", "subcategory": "LOOP", "key": "ERROR_BACKOFF_MS", "value": "5000"},
  {"category": "SYSTEM", "subcategory": "LOOP", "key": "ERROR_BACKOFF_MAX_RETRIES", "value": "3"},
  {"category": "SYSTEM", "subcategory": "EXECUTION", "key": "RUN_MODE", "value": "PAPER"},
  {"category": "SYSTEM", "subcategory": "EXECUTION", "key": "LIVE_ENABLED", "value": "N"},
  {"category": "SYSTEM", "subcategory": "EXECUTION", "key": "trading_enabled", "value": "Y"},
  {"category": "SYSTEM", "subcategory": "PIPELINE", "key": "PIPELINE_PAUSED", "value": "N"},
  {"category": "SYSTEM", "subcategory": "SAFETY", "key": "KS_ENABLED", "value": "Y"},
  {"category": "SYSTEM", "subcategory": "BROKER", "key": "BASE_EQUITY", "value": "10000000"}
]
```

---

### 2.2 프로덕션 모드 (Broker + Google Sheets)

```bash
python main.py --broker kis --scope scalp
# 또는
python main.py --broker kiwoom --scope scalp
```

| 항목 | 필수 | 설명 |
|------|------|------|
| **.env** | ✅ | `load_dotenv_if_available()`로 로드 |
| **KIS 모드** | ✅ | `KIS_MODE=KIS_VTS`, `KIS_VTS_APP_KEY`, `KIS_VTS_APP_SECRET`, `KIS_VTS_ACCOUNT_NO`, `KIS_VTS_BASE_URL` |
| **Kiwoom 모드** | ✅ | `KIWOOM_MODE=KIWOOM_VTS`, `KIWOOM_VTS_APP_KEY`, `KIWOOM_VTS_APP_SECRET`, `KIWOOM_VTS_ACCOUNT_NO`, `KIWOOM_VTS_BASE_URL` |
| **Google Sheets** | ✅ | `GOOGLE_SHEET_KEY`, `GOOGLE_CREDENTIALS_FILE` |
| **Config_Scalp/Config_Swing 시트** | ✅ | Google Sheet에 Config_Scalp 또는 Config_Swing 시트 존재 |

#### .env 스키마 (env_loader 기준)

`.env`는 프로젝트 루트에 두고 아래 키를 참고한다. (`env_loader.py`가 읽는 키만 정리)

**Broker – KIS (모의투자)**

```
KIS_MODE=KIS_VTS
KIS_VTS_APP_KEY=<앱키>
KIS_VTS_APP_SECRET=<앱시크릿>
KIS_VTS_ACCOUNT_NO=<계좌번호>
KIS_VTS_ACNT_PRDT_CD=01
KIS_VTS_BASE_URL=https://openapivts.koreainvestment.com:29443
KIS_VTS_WEBSOCKET_URL=   # 선택
```

**Broker – KIS (실전투자)**

```
KIS_MODE=KIS_REAL
KIS_REAL_APP_KEY=...
KIS_REAL_APP_SECRET=...
KIS_REAL_ACCOUNT_NO=...
KIS_REAL_ACNT_PRDT_CD=01
KIS_REAL_BASE_URL=https://openapi.koreainvestment.com:9443
KIS_REAL_WEBSOCKET_URL=   # 선택
```

**Broker – Kiwoom (모의투자)**

```
KIWOOM_MODE=KIWOOM_VTS
KIWOOM_VTS_APP_KEY=...
KIWOOM_VTS_APP_SECRET=...
KIWOOM_VTS_ACCOUNT_NO=...
KIWOOM_VTS_ACNT_PRDT_CD=01
KIWOOM_VTS_BASE_URL=https://mockapi.kiwoom.com
KIWOOM_VTS_WEBSOCKET_URL=   # 선택
```

**Broker – Kiwoom (실전투자)**

```
KIWOOM_MODE=KIWOOM_REAL
KIWOOM_REAL_APP_KEY=...
KIWOOM_REAL_APP_SECRET=...
KIWOOM_REAL_ACCOUNT_NO=...
KIWOOM_REAL_ACNT_PRDT_CD=01
KIWOOM_REAL_BASE_URL=https://api.kiwoom.com
KIWOOM_REAL_WEBSOCKET_URL=   # 선택
```

**실전 주문 스위치**

```
ENABLE_REAL_ORDER=N   # Y=실전 주문 허용, N=거부
```

**Google Sheets**

```
GOOGLE_SHEET_KEY=<스프레드시트 ID>
GOOGLE_CREDENTIALS_FILE=<서비스 계정 JSON 경로>
GOOGLE_SHEETS_API_QUOTA=100   # 선택, 기본 100
```

#### Google Sheets 연동 체크

- `ETEDARunner`: `sheets_client=None`이면 `config.get_flat("SPREADSHEET_ID")` 또는 `GOOGLE_SHEET_KEY`, `config.get_flat("CREDENTIALS_PATH")` 또는 `GOOGLE_CREDENTIALS_FILE` 사용.
- `load_unified_config(scope=SCALP/SWING)`는 **Config_Scalp** 또는 **Config_Swing** 시트를 Google Sheets에서 읽어야 함.
- `GoogleSheetsClient.authenticate()`: `credentials_path`, `spreadsheet_id` 필수.
- 스프레드시트에 **Config_Scalp** 또는 **Config_Swing** 시트와 필요한 컬럼이 있어야 로드 성공.

#### Broker 설정 체크

- `main.py`는 `--broker kis` 또는 `--broker kiwoom`에 따라 `get_broker_config("KIS")` 또는 `get_broker_config("KIWOOM")` 호출.
- 필수 키 누락 시 `ValueError: Missing required environment variables for ...` 발생.
- 인증 검증: `python test_broker_auth.py` (KIS·Kiwoom 둘 다 테스트).
- 주문 검증: `python test_kis_order.py` (KIS VTS 모드 전제).

---

## 3. 사전 검증 명령어

### 3.1 로컬 전용 실행 테스트

```bash
python main.py --local-only --max-iterations 2 -v
```

**예상 출력**:
- `Preflight check: PASSED`
- `Config validation passed`
- `Creating mock runner (local-only mode)...`
- `ETEDA loop stopped (should_stop=True)`
- `ETEDA loop finished.`

### 3.2 KIS 인증 테스트 (.env 필요)

```bash
python test_broker_auth.py
```

### 3.3 KIS 주문 테스트 (.env + VTS 모드 필요)

```bash
python test_kis_order.py
```

### 3.4 핵심 테스트 실행

```bash
pytest tests/integration/test_main_mock_run.py tests/config/ tests/runtime/broker/ -v
```

---

## 4. 디렉터리 구조 확인

```
prj_qts/
├── main.py                 # 진입점
├── config/
│   ├── local/
│   │   └── config_local.json   # 필수 (gitignore 대상)
│   └── schema/
│       └── credentials.json    # 필수 (스키마 정의)
├── .env                     # 프로덕션 시 필수 (gitignore)
└── src/
```

- `config/local/`는 `.gitignore`에 포함되어 있어 새 환경에서는 직접 생성 필요

---

## 5. 접속·주문 성공/실패 DATA·LOG 기록 현황

접속, 주문 등 주요 이벤트에 대한 **영구 저장(DATA)** 및 **로그(LOG)** 기록 여부를 정리했다.

### 5.1 현재 구현된 기록

| 대상 | 로그 (LOG) | 데이터 저장 (DATA) |
|------|------------|---------------------|
| **Broker API 접속(토큰)** | ✅ `KISClient`/`KiwoomClient`: `_log.info("access token acquired")`, `_log.error("Token acquisition failed")` | ✅ 토큰 파일 캐시 (`~/.qts_kis_token_*.json`) |
| **Broker API 요청(주문/조회)** | ✅ `_log.info("Placing KIS order...")`, `_log.error("KIS API error...")`, `_log.warning("rt_cd != 0")` | ❌ 미구현 |
| **주문 결과 (성공/실패)** | ✅ ETEDARunner `_log.info("[PAPER] Act result: ...")`, OrderAdapter `_log.error("Failed to submit intent")` | ❌ **T_Ledger 미연동** |
| **Google Sheets 접속** | ✅ `GoogleSheetsClient`: `_log.info("authentication successful")`, `_log.error("Authentication failed")` | ❌ 미구현 |
| **Google Sheets API 호출** | ✅ `get_sheet_data`, `update_sheet_data` 등: `_log.info("Retrieved N rows")`, `_log.warning("Rate limit hit")` | ❌ 미구현 |
| **Fail-Safe (FS040 등)** | ✅ `MockSafetyHook.record_fail_safe` → `_log.warning`, `SafetyLayer` → `record_fail_safe` | ⚠️ `safety_hook` 주입 시에만 메모리/상태 기록, 영구 저장 없음 |

### 5.2 미구현·부족 사항

1. **주문 결과 → T_Ledger 미연동**
   - `T_LedgerRepository.create_trade()`는 존재하지만, **ETEDARunner._act()에서 호출하지 않음**.
   - 주문 성공/실패가 T_Ledger 시트에 기록되지 않음.

2. **History 시트**
   - `HistoryRepository.log_execution()`, `log_error()`는 **일일 성과·에러용**.
   - 개별 주문 이벤트 기록용이 아님.

3. **접속/주문 감사 로그**
   - 접속 성공/실패, 주문 성공/실패를 **별도 시트나 파일로 영구 저장**하는 로직 없음.
   - Python `logging`만 사용 → 콘솔/파일 로그는 로그 설정에 의존.

4. **프로덕션 Safety Hook**
   - `safety_hook=None`이면 `record_fail_safe` 호출 대상이 없음.
   - Fail-Safe 이벤트도 로그 외 영구 저장 없음.

### 5.3 로그 확인 방법

- 실행 시 `-v` 사용: `python main.py --broker kis --scope scalp -v`
- 로그 포맷: `%(asctime)s [%(name)s] %(levelname)s %(message)s`
- **파일 로그**: `{project_root}/logs/qts.log`에 자동 기록됨 (자정 기준 일별 로테이션, 7일 보관). `QTS_LOG_RETENTION_DAYS` 환경 변수로 보관 일수 조정 가능.

### 5.4 권장 개선 (향후)

- [ ] Act 단계 후 `ExecutionResponse` 기준으로 `T_LedgerRepository.create_trade()` 호출 (성공/실패 모두).
- [ ] Broker API 접속·주문 실패를 별도 감사 시트(예: `Audit_Log`) 또는 파일에 기록.
- [x] **파일 로그**: `configure_central_logging(log_file=...)`로 `logs/qts.log`에 기록 (2026-02-01 구현).
- [ ] 프로덕션에서 `SafetyLayer` 주입 후 `record_fail_safe` → Notifier → Slack/Email 등 알림.

---

## 6. 알려진 주의사항

| 항목 | 내용 |
|------|------|
| **StrategyEngine** | 현재 기본 HOLD 시그널만 반환. BUY/SELL 로직은 전략 등록 필요 |
| **Safety Hook** | 프로덕션 모드에서 `safety_hook=None` (ops.safety 연결 예정) |
| **Snapshot Source** | 프로덕션 모드에서 `snapshot_source=None` → interval 트리거 사용. 실시간 시세는 WebSocket 미연동 |
| **실전 주문** | `ENABLE_REAL_ORDER=Y` 없으면 REAL 모드에서도 주문 거부 |
| **Preflight credentials.json** | `runtime_checks`가 credentials.json을 확인하지만, 없으면 경고만 출력 후 진행 |

---

## 7. 내일 실행 전 최종 체크

- [ ] `config/local/config_local.json` 존재 및 필수 키 9개 포함
- [ ] `config/schema/credentials.json` 존재 (스키마 정의)
- [ ] `python main.py --local-only --max-iterations 2` 성공
- [ ] (선택) KIS/Kiwoom 사용 시 `.env` 설정 및 `test_broker_auth.py` 통과
- [ ] (선택) 프로덕션 모드 시 Google Sheets 연동 설정 완료

---

## 8. 수정 사항 (2026-02-01)

- **ops/safety/notifier.py**: `Protocol`을 `shared.timezone_utils`가 아닌 `typing`에서 import하도록 수정 (ImportError 해결)
- 전체 테스트 348 passed 확인
