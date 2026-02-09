# QTS Test Suite

QTS 프로젝트의 테스트 스위트입니다. `pytest` 기반으로 구성되어 있으며, 단위 테스트부터 E2E 통합 테스트까지 포함합니다.

## 테스트 구조

```
tests/
├── api/                           # KIS API 등 외부 API 테스트
├── config/                        # 설정 로딩 및 검증 테스트
├── contracts/                     # 데이터 계약 및 스키마 검증
├── engines/                       # 4대 엔진 (Strategy, Risk, Portfolio, Performance) 단위 테스트
├── fixtures/                      # Pytest 픽스처 및 테스트 데이터
├── google_sheets_integration/     # Google Sheets 연동 통합 테스트
├── integration/                   # 시스템 통합 테스트
├── ops/                           # 운영 및 안전 레이어 테스트
├── runtime/                       # 런타임 실행 및 브로커 테스트
└── unit/                          # 기타 단위 테스트
```

## 테스트 마커

QTS는 다음 pytest 마커를 사용합니다:

| 마커 | 설명 | 기본 실행 |
|------|------|----------|
| `live_sheets` | Google Sheets 실 API 연동 | ❌ (opt-in) |
| `real_broker` | 실 브로커 API 연동 | ❌ (opt-in) |
| (없음) | Mock 기반 단위/통합 테스트 | ✅ |

## 테스트 실행

### 기본 테스트 (Mock 기반, CI 기본)

```bash
# 전체 테스트 (live_sheets, real_broker 제외)
pytest tests/ -v -m "not live_sheets and not real_broker"

# 특정 폴더만 실행
pytest tests/engines/ -v
pytest tests/runtime/broker/ -v
```

### Google Sheets 연동 테스트

실 Google Sheets API를 사용하는 테스트입니다. `.env` 설정 필요.

```bash
# live_sheets 마커 테스트
pytest tests/ -v -m "live_sheets"

# 또는 직접 실행
python tests/google_sheets_integration/test_repositories.py
```

**환경 요구사항**:
- `config/.env`에 `GOOGLE_CREDENTIALS_FILE`, `GOOGLE_SHEET_KEY` 설정
- Google Cloud 서비스 계정 JSON 키 파일

### 실 브로커 테스트

한국투자증권(KIS) API를 사용하는 스모크 테스트입니다.

```bash
# real_broker 마커 테스트
pytest tests/ -v -m "real_broker"

# 또는 환경 변수로 활성화
QTS_RUN_REAL_BROKER=1 pytest tests/runtime/broker/test_kis_real_broker_smoke.py -v
```

**환경 요구사항**:
- KIS API 인증 정보 (APP_KEY, APP_SECRET, ACCOUNT_NO)
- 모의 계좌 또는 dry_run 모드 권장

## 테스트 범주별 설명

### 1. 엔진 테스트 (`tests/engines/`)

Strategy, Risk, Portfolio, Performance 엔진의 핵심 로직 단위 테스트.

```bash
pytest tests/engines/ -v
```

### 2. 브로커 테스트 (`tests/runtime/broker/`)

Mock 기반 회귀 테스트와 실 브로커 스모크 테스트가 분리되어 있습니다.

| 파일 | 유형 | 설명 |
|------|------|------|
| `test_broker_factory.py` | Mock | Broker Factory 로직 |
| `test_kis_adapter_integration.py` | Mock | KIS 어댑터 통합 |
| `test_kis_payload_mapping.py` | Mock | 요청/응답 매핑 |
| `test_kis_real_broker_smoke.py` | Real | 실 브로커 스모크 (opt-in) |

자세한 내용: [`tests/runtime/broker/README.md`](runtime/broker/README.md)

### 3. ETEDA 파이프라인 테스트 (`tests/runtime/integration/`)

E2E 시나리오 및 ETEDA 전체 흐름 검증.

```bash
# E2E 테스트 (Mock 기반)
pytest tests/runtime/integration/test_eteda_e2e.py -v
```

**테스트 시나리오**:
- ETEDA 전체 흐름 (Extract → Act)
- 10회 연속 성공 시나리오
- 에러 복구 시나리오
- 성능 벤치마크 (사이클 < 3초)

### 4. Safety Layer 테스트 (`tests/ops/safety/`)

Fail-Safe, Guard, Notifier, State 컴포넌트 검증.

```bash
pytest tests/ops/safety/ -v
```

### 5. Google Sheets 통합 테스트 (`tests/google_sheets_integration/`)

Repository 패턴 및 Google Sheets API 연동 테스트.

자세한 내용: [`tests/google_sheets_integration/README.md`](google_sheets_integration/README.md)

## 픽스처 및 설정

### 전역 픽스처 (`conftest.py`)

```python
# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))  # app, ops, shared import

# .env 로딩
dotenv.load_dotenv(PROJECT_ROOT / ".env")

# live_sheets 테스트 간 API 쿼터 보호
@pytest.fixture(autouse=True)
def live_sheets_rate_limit(request):
    if "live_sheets" in request.node.keywords:
        time.sleep(LIVE_SHEETS_DELAY_SEC)
    yield
    if "live_sheets" in request.node.keywords:
        time.sleep(LIVE_SHEETS_DELAY_SEC)
```

### 마커 등록

```python
def pytest_configure(config):
    config.addinivalue_line("markers", "live_sheets: Google Sheets 실 API 연동 테스트")
    config.addinivalue_line("markers", "real_broker: 실 브로커 API 연동 테스트")
```

## 테스트 작성 가이드

### 1. Mock 기반 테스트 (기본)

```python
from unittest.mock import MagicMock, AsyncMock

def test_engine_logic():
    mock_client = MagicMock()
    mock_client.get_data = AsyncMock(return_value=[...])
    
    engine = SomeEngine(client=mock_client)
    result = engine.evaluate(...)
    
    assert result.signal == "BUY"
```

### 2. Live 테스트 (opt-in)

```python
import pytest

@pytest.mark.live_sheets
async def test_live_repository():
    """실 Google Sheets 연동 테스트"""
    # .env에서 credentials 로딩
    repo = PortfolioRepository(client=real_client)
    data = await repo.get_portfolio()
    assert len(data) > 0
```

### 3. 성능 테스트

```python
import time

@pytest.mark.asyncio
async def test_eteda_cycle_latency():
    """ETEDA 사이클 < 3초 검증"""
    runner = ETEDARunner(...)
    
    start = time.perf_counter()
    await runner.run_once(snapshot)
    elapsed = time.perf_counter() - start
    
    assert elapsed < 3.0, f"Cycle {elapsed:.3f}s exceeds 3s target"
```

## 실패 진단

### Google Sheets 테스트 실패

| 에러 | 원인 | 해결 |
|------|------|------|
| `AuthenticationError` | credentials 누락/만료 | `config/.env` 및 JSON 키 확인 |
| `APIError 429` | Rate Limit 초과 | 테스트 간 대기 시간 증가 |
| `ValidationError` | 스키마 불일치 | 시트 헤더 확인 |

### 브로커 테스트 실패

| 에러 | 원인 | 해결 |
|------|------|------|
| `TokenExpired` | OAuth 토큰 만료 | 토큰 재발급 |
| `OrderRejected` | 주문 조건 미충족 | 주문 파라미터 확인 |
| `ConnectionTimeout` | 네트워크 이슈 | 재시도 또는 VPN 확인 |

## CI/CD 통합

```yaml
# GitHub Actions 예시
- name: Run Tests
  run: |
    pytest tests/ -v -m "not live_sheets and not real_broker" \
      --cov=app --cov-report=xml
```

## 참고 문서

- **테스트 가이드**: `docs/tasks/finished/phases_no1/Phase_10_Test_Governance/`
- **Phase Exit Criteria**: `docs/tasks/finished/phases_no1/Phase_10_Test_Governance/Phase_Exit_Criteria.md`
- **E2E 시나리오**: `tests/runtime/integration/test_eteda_e2e.py`

---

**최종 갱신**: 2026-02-01
