# QTS 앱형 리팩토링 분석 문서

> 작성일: 2026-02-01
> 버전: 1.0
> 목적: 현재 레포 구조 분석 및 앱형 리팩토링 설계

---

## 1. 현재 레포 구조 분석

### 1.1 전체 폴더 구조 (현재 상태)

```
qts/
├── main.py                      # 메인 엔트리포인트
├── test_broker_auth.py          # 테스트 스크립트 (루트에 방치)
├── test_kis_order.py            # 테스트 스크립트 (루트에 방치)
│
├── src/
│   ├── runtime/                 # 핵심 런타임 코드
│   │   ├── auth/                # 토큰 캐싱
│   │   ├── broker/              # 브로커 클라이언트 (KIS, KIWOOM)
│   │   │   ├── adapters/        # 브로커 어댑터 패턴
│   │   │   ├── kis/             # KIS API 클라이언트
│   │   │   └── kiwoom/          # KIWOOM API 클라이언트
│   │   ├── config/              # 설정 관리 (3분할)
│   │   ├── core/                # 앱 컨텍스트
│   │   ├── data/                # 데이터 레이어 (Repository)
│   │   ├── engines/             # 엔진 (Strategy, Portfolio, Performance)
│   │   ├── execution/           # 주문 실행 레이어
│   │   ├── execution_loop/      # ETEDA 루프
│   │   ├── execution_state/     # 주문 상태 관리
│   │   ├── monitoring/          # 로깅/메트릭
│   │   ├── pipeline/            # ETEDA 파이프라인
│   │   ├── risk/                # 리스크 관리
│   │   ├── schema/              # 스키마 버전 관리
│   │   ├── strategy/            # 전략 모듈
│   │   ├── ui/                  # Zero-Formula UI (R_Dash)
│   │   └── utils/               # 유틸리티
│   │
│   ├── ops/                     # 운영 자동화
│   │   ├── automation/          # 스케줄러, 알림
│   │   ├── backup/              # 백업 관리
│   │   ├── decision_pipeline/   # Ops 레벨 의사결정
│   │   ├── maintenance/         # 유지보수
│   │   ├── retention/           # 보존 정책
│   │   ├── runtime/             # Ops 런타임 브릿지
│   │   └── safety/              # Safety Layer (Kill Switch)
│   │
│   └── shared/                  # 공용 유틸리티
│       ├── paths.py
│       ├── timezone_utils.py
│       └── utils.py
│
├── config/
│   ├── local/
│   │   └── config_local.json    # 불변 시스템 설정
│   └── schema/
│       └── credentials.json     # Google API 인증
│
├── logs/
│   └── qts.log                  # 중앙 집중 로그
│
├── docs/                        # 문서
├── tests/                       # 테스트 스위트
├── scripts/                     # 유틸리티 스크립트
├── notebook/                    # 프롬프트/실험 노트북
├── backup/                      # 백업 디렉토리
└── .venv/                       # Python 가상환경
```

### 1.2 실제 실행 엔트리포인트

| 파일 | 역할 | 상태 |
|------|------|------|
| `main.py` | 메인 진입점 (ETEDA 루프) | ✅ 정상 |
| `test_broker_auth.py` | 브로커 인증 테스트 | ⚠️ 루트에 방치 |
| `test_kis_order.py` | KIS 주문 테스트 | ⚠️ 루트에 방치 |

**main.py 실행 흐름:**
```
CLI 파싱 → 로깅 설정 → 시그널 핸들러 → .env 로드
→ Preflight Check → Config 로드 → Config 검증
→ Runner 생성 → ETEDA Loop 실행 → Graceful Shutdown
```

### 1.3 전략 판단 로직 위치

| 컴포넌트 | 위치 | 역할 |
|----------|------|------|
| ETEDARunner | `src/runtime/pipeline/eteda_runner.py` | ETEDA 5단계 실행 |
| StrategyEngine | `src/runtime/engines/strategy_engine.py` | 신호 생성 |
| SimpleStrategy | `src/runtime/strategy/simple_strategy.py` | 기본 전략 구현 |
| StrategyMultiplexer | `src/runtime/strategy/multiplexer/` | 다중 전략 결합 |
| IntentArbitrator | `src/runtime/strategy/arbitration/` | Intent 중재 |

**ETEDA 파이프라인:**
```
Extract → Transform → Evaluate → Decide → Act
  │          │           │          │       │
  │          │           │          │       └─ BrokerEngine.submit_intent()
  │          │           │          └─ 리스크 검증 + 실행 모드 결정
  │          │           └─ StrategyEngine.calculate_signal()
  │          └─ market_data + position_data 정규화
  └─ snapshot에서 데이터 추출
```

### 1.4 주문/브로커 연동 코드 위치

**실행 계층 구조:**
```
src/runtime/execution/
├── interfaces/
│   └── broker.py           # BrokerEngine 추상 인터페이스
├── brokers/
│   ├── live_broker.py      # 실 브로커 (ConsecutiveFailureGuard)
│   ├── mock_broker.py      # Mock 브로커
│   └── noop_broker.py      # No-op 브로커
├── models/
│   ├── intent.py           # ExecutionIntent 계약
│   └── response.py         # ExecutionResponse 계약
├── adapters/
│   └── order_adapter_to_broker_engine_adapter.py
└── failsafe/
    └── consecutive_failure_guard.py
```

**브로커 클라이언트:**
```
src/runtime/broker/
├── base.py                 # BrokerAdapter 인터페이스
├── config.py               # 브로커 설정 모델
├── kis/
│   ├── kis_client.py       # KIS API 클라이언트
│   ├── adapter.py          # KIS 주문 어댑터
│   └── auth.py             # OAuth2 인증
└── kiwoom/
    ├── kiwoom_client.py    # KIWOOM 클라이언트
    └── adapter.py          # KIWOOM 주문 어댑터
```

### 1.5 설정(Config) 로딩 방식

**3분할 아키텍처:**
```
┌─────────────────────────────────────────────────────────┐
│  Config_Local (파일 기반, 불변)                          │
│  위치: config/local/config_local.json                    │
│  범위: SYSTEM, BROKER, SAFETY, RISK, FILTER, ORDER, LOOP│
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Config_Strategy (Google Sheet 기반)                     │
│  - Config_Scalp (Scalp 전략 설정)                        │
│  - Config_Swing (Swing 전략 설정)                        │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  UnifiedConfig (병합 결과)                               │
│  - precedence: Local > Strategy                          │
│  - conflicts 기록                                        │
└─────────────────────────────────────────────────────────┘
```

**주요 로드 함수:**
- `load_local_only_config()` - Local-Only 모드 (테스트용)
- `load_unified_config()` - Production 모드 (Local + Strategy 병합)

### 1.6 로그/데이터 파일 생성 위치

| 유형 | 위치 | 설명 |
|------|------|------|
| 로그 파일 | `logs/qts.log` | 중앙 집중 로깅 |
| Local Config | `config/local/config_local.json` | 시스템 설정 |
| Dividend DB | `config/local/dividend_db.json` | 배당 데이터 |
| Credentials | `config/schema/credentials.json` | Google API 인증 |
| 백업 | `backup/` | Config/데이터 스냅샷 |

---

## 2. 현재 구조의 문제점

### 2.1 구조적 문제

| 문제 | 현황 | 영향 |
|------|------|------|
| 테스트 코드 방치 | `test_*.py`가 루트에 존재 | 운영/실험 코드 혼재 |
| Dockerfile 부재 | 없음 | Docker 배포 불가 |
| YAML 설정 부재 | JSON만 사용 | 환경별 설정 관리 어려움 |
| Observer 연동 없음 | 직접 연동 구조 없음 | IPC/UDS 확장 어려움 |

### 2.2 의존성 문제

```
현재 의존성 흐름:
main.py → runtime.* (직접 import)
        → ops.safety.* (직접 import)

문제점:
- Observer 연동 시 결합도 증가 위험
- 전략 로직이 broker 레이어에 직접 접근 가능
- Risk Gate가 Strategy와 동일 레벨에 혼재
```

### 2.3 경계 불명확

| 영역 | 문제 |
|------|------|
| strategy/ | 신호 생성 + 일부 실행 로직 혼재 |
| execution/ | 브로커 어댑터 + 실행 로직 혼재 |
| ops/ | 운영 자동화 + Safety Layer 혼재 |

---

## 3. 목표 앱 구조 설계

### 3.1 새로운 폴더 구조 (목표)

```
qts/
├── app/
│   ├── core/                    # 앱 생명주기, bootstrap
│   │   ├── __init__.py
│   │   ├── bootstrap.py         # 앱 초기화 로직
│   │   ├── lifecycle.py         # 생명주기 관리
│   │   └── context.py           # 런타임 컨텍스트
│   │
│   ├── strategy/                # 매매 전략 로직
│   │   ├── __init__.py
│   │   ├── interfaces/          # 전략 인터페이스
│   │   ├── engines/             # 전략 엔진
│   │   ├── multiplexer/         # 다중 전략 결합
│   │   ├── arbitration/         # Intent 중재
│   │   └── registry/            # 전략 레지스트리
│   │
│   ├── risk/                    # 리스크 관리
│   │   ├── __init__.py
│   │   ├── interfaces/          # 리스크 게이트 인터페이스
│   │   ├── calculators/         # 리스크 계산기
│   │   ├── gates/               # 리스크 게이트 구현
│   │   └── policies/            # 리스크 정책
│   │
│   ├── execution/               # 주문 실행 / 브로커 인터페이스
│   │   ├── __init__.py
│   │   ├── interfaces/          # BrokerEngine 인터페이스
│   │   ├── brokers/             # Broker 구현체 (live, mock, noop)
│   │   ├── adapters/            # 브로커 어댑터
│   │   ├── models/              # Intent, Response 모델
│   │   ├── clients/             # 브로커 API 클라이언트
│   │   │   ├── kis/             # KIS 클라이언트
│   │   │   └── kiwoom/          # KIWOOM 클라이언트
│   │   └── failsafe/            # 연속 실패 가드
│   │
│   ├── observer_client/         # Observer 연동 어댑터 (stub 포함)
│   │   ├── __init__.py
│   │   ├── interfaces.py        # Observer 인터페이스 정의
│   │   ├── stub.py              # Stub 구현 (개발/테스트용)
│   │   ├── uds_client.py        # UDS 클라이언트 (향후)
│   │   └── ipc_client.py        # IPC 클라이언트 (향후)
│   │
│   ├── pipeline/                # ETEDA 파이프라인
│   │   ├── __init__.py
│   │   ├── eteda_runner.py      # ETEDA 실행기
│   │   ├── eteda_loop.py        # 루프 관리
│   │   └── safety_hook.py       # Safety 연계
│   │
│   ├── data/                    # 데이터 레이어
│   │   ├── __init__.py
│   │   ├── repositories/        # Repository 패턴
│   │   ├── clients/             # 데이터 클라이언트 (Sheets, Mock)
│   │   └── mappers/             # 필드 매퍼
│   │
│   ├── monitoring/              # 로깅/메트릭
│   │   ├── __init__.py
│   │   ├── central_logger.py
│   │   └── metrics_collector.py
│   │
│   └── main.py                  # 단일 엔트리포인트
│
├── config/
│   ├── default.yaml             # 기본 설정
│   ├── production.yaml          # 프로덕션 설정
│   ├── local/
│   │   └── config_local.json    # 불변 시스템 설정 (유지)
│   └── schema/
│       └── credentials.json     # Google API 인증
│
├── ops/                         # 운영 자동화 (분리)
│   ├── automation/
│   ├── backup/
│   ├── maintenance/
│   ├── retention/
│   └── safety/                  # Safety Layer
│
├── shared/                      # 공용 유틸리티
│   ├── paths.py
│   ├── timezone_utils.py
│   └── utils.py
│
├── logs/
│   └── .gitkeep
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/                     # 유틸리티 스크립트
│
├── Dockerfile                   # Docker 배포
├── docker-compose.yaml          # Docker Compose (옵션)
├── requirements.txt             # Python 의존성
├── pyproject.toml              # 프로젝트 메타데이터
└── README.md
```

### 3.2 핵심 설계 원칙

| 원칙 | 설명 |
|------|------|
| 전략 격리 | `app/strategy/` 밖으로 전략 로직 이동 금지 |
| Observer 추상화 | `app/observer_client/` 통해서만 Observer 접근 |
| 주문 분리 | 전략 코드 내 직접 주문 코드 금지 |
| 단일 진입점 | `app/main.py`만 실행 진입점 |
| 환경 분리 | YAML 기반 환경별 설정 |

### 3.3 의존성 방향

```
┌─────────────────────────────────────────────────────────┐
│                      app/main.py                        │
│                    (엔트리포인트)                         │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐  ┌────────────┐  ┌──────────────┐
    │ core/    │  │ pipeline/  │  │ monitoring/  │
    │ bootstrap│  │ eteda      │  │ logger       │
    └────┬─────┘  └─────┬──────┘  └──────────────┘
         │              │
         │    ┌─────────┼─────────┐
         │    ▼         ▼         ▼
         │ ┌────────┐ ┌──────┐ ┌───────────┐
         │ │strategy│ │ risk │ │ execution │
         │ └────┬───┘ └──┬───┘ └─────┬─────┘
         │      │        │           │
         │      └────────┼───────────┘
         │               │
         │               ▼
         │      ┌────────────────┐
         │      │ observer_client│ ◀── Observer (외부)
         │      │ (stub/uds/ipc) │
         │      └────────────────┘
         │
         ▼
    ┌──────────┐
    │  data/   │
    │ repos    │
    └──────────┘
```

---

## 4. 파일 이동 계획

### 4.1 이동 대상 (현재 → 목표)

| 현재 위치 | 목표 위치 | 변경 유형 |
|-----------|-----------|-----------|
| `main.py` | `app/main.py` | 이동 + 수정 |
| `src/runtime/core/` | `app/core/` | 이동 |
| `src/runtime/strategy/` | `app/strategy/` | 이동 |
| `src/runtime/risk/` | `app/risk/` | 이동 |
| `src/runtime/execution/` | `app/execution/` | 이동 |
| `src/runtime/broker/` | `app/execution/clients/` | 이동 + 통합 |
| `src/runtime/pipeline/` | `app/pipeline/` | 이동 |
| `src/runtime/data/` | `app/data/` | 이동 |
| `src/runtime/monitoring/` | `app/monitoring/` | 이동 |
| `src/runtime/engines/` | `app/strategy/engines/` | 이동 + 통합 |
| `src/ops/` | `ops/` | 이동 (app 외부로) |
| `src/shared/` | `shared/` | 이동 |

### 4.2 삭제 대상

| 파일 | 사유 |
|------|------|
| `test_broker_auth.py` | tests/로 이동 |
| `test_kis_order.py` | tests/로 이동 |
| `src/runtime/config/` | `app/core/config/`로 통합 |
| `src/runtime/auth/` | `app/execution/clients/`로 통합 |
| `src/runtime/schema/` | `app/data/schema/`로 통합 |
| `src/runtime/ui/` | 별도 패키지로 분리 또는 삭제 검토 |
| `src/runtime/execution_loop/` | `app/pipeline/`로 통합 |
| `src/runtime/execution_state/` | `app/execution/`로 통합 |
| `src/runtime/utils/` | `shared/`로 통합 |

### 4.3 신규 생성 대상

| 파일 | 목적 |
|------|------|
| `app/observer_client/interfaces.py` | Observer 인터페이스 정의 |
| `app/observer_client/stub.py` | Stub 구현 |
| `config/default.yaml` | 기본 설정 |
| `config/production.yaml` | 프로덕션 설정 |
| `Dockerfile` | Docker 배포 |
| `docker-compose.yaml` | Docker Compose |

---

## 5. Import 경로 변경 계획

### 5.1 주요 변경

| 현재 | 변경 후 |
|------|---------|
| `from runtime.config.*` | `from app.core.config import *` |
| `from runtime.strategy.*` | `from app.strategy import *` |
| `from runtime.risk.*` | `from app.risk import *` |
| `from runtime.execution.*` | `from app.execution import *` |
| `from runtime.broker.*` | `from app.execution.clients import *` |
| `from runtime.pipeline.*` | `from app.pipeline import *` |
| `from runtime.data.*` | `from app.data import *` |
| `from ops.safety.*` | `from ops.safety import *` |
| `from shared.*` | `from shared import *` |

### 5.2 sys.path 설정 (app/main.py)

```python
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parent.parent  # qts/
sys.path.insert(0, str(_ROOT))

# 이제 모든 import는 qts/ 기준
from app.core.bootstrap import bootstrap_app
from app.pipeline.eteda_runner import ETEDARunner
from shared.timezone_utils import get_kst_now
```

---

## 6. 엔트리포인트 재정의

### 6.1 app/main.py 책임

```python
"""
QTS 앱 단일 엔트리포인트

책임:
1. Config 로드 (YAML + JSON)
2. Observer client 초기화 (stub 허용)
3. 전략 엔진 시작
4. Graceful shutdown 처리
"""

def main():
    # 1. Config 로드
    config = load_config(environment=os.getenv("QTS_ENV", "development"))

    # 2. Observer client 초기화
    observer = create_observer_client(config.observer)  # stub or real

    # 3. 앱 Bootstrap
    app = bootstrap_app(config, observer)

    # 4. ETEDA 루프 실행
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        app.shutdown()
```

### 6.2 실행 명령어

```bash
# 개발 모드 (stub observer)
python -m app.main --env development

# 프로덕션 모드
python -m app.main --env production

# Docker
docker run -e QTS_ENV=production qts-app
```

---

## 7. Docker 배포 설계

### 7.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY app/ ./app/
COPY ops/ ./ops/
COPY shared/ ./shared/
COPY config/ ./config/

# 환경변수
ENV QTS_ENV=production
ENV OBSERVER_ENDPOINT=unix:///var/run/observer.sock
ENV PYTHONPATH=/app

# 로그 디렉토리
RUN mkdir -p /app/logs

# 실행
CMD ["python", "-m", "app.main"]
```

### 7.2 환경변수 설계

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `QTS_ENV` | 실행 환경 | `development` |
| `OBSERVER_ENDPOINT` | Observer 연결 경로 | `stub` |
| `BROKER_TYPE` | 브로커 선택 | `kiwoom` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |

---

## 8. Observer IPC 연동 지점

### 8.1 연동 인터페이스

```python
# app/observer_client/interfaces.py
from typing import Protocol, Optional
from dataclasses import dataclass

@dataclass
class MarketSnapshot:
    symbol: str
    price: float
    volume: int
    timestamp: datetime

class ObserverClient(Protocol):
    """Observer 연동 인터페이스"""

    async def connect(self) -> bool:
        """Observer 연결"""
        ...

    async def subscribe(self, symbols: list[str]) -> bool:
        """종목 구독"""
        ...

    async def get_snapshot(self, symbol: str) -> Optional[MarketSnapshot]:
        """스냅샷 조회"""
        ...

    async def disconnect(self) -> None:
        """연결 해제"""
        ...
```

### 8.2 Stub 구현

```python
# app/observer_client/stub.py
class StubObserverClient:
    """개발/테스트용 Stub Observer"""

    async def connect(self) -> bool:
        return True

    async def subscribe(self, symbols: list[str]) -> bool:
        self._symbols = symbols
        return True

    async def get_snapshot(self, symbol: str) -> Optional[MarketSnapshot]:
        # Mock 데이터 반환
        return MarketSnapshot(
            symbol=symbol,
            price=random.uniform(50000, 100000),
            volume=random.randint(1000, 10000),
            timestamp=datetime.now(KST),
        )

    async def disconnect(self) -> None:
        pass
```

### 8.3 향후 UDS 연동

```python
# app/observer_client/uds_client.py
class UDSObserverClient:
    """Unix Domain Socket 기반 Observer 클라이언트"""

    def __init__(self, socket_path: str = "/var/run/observer.sock"):
        self._socket_path = socket_path
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    async def connect(self) -> bool:
        self._reader, self._writer = await asyncio.open_unix_connection(
            self._socket_path
        )
        return True
```

---

## 9. 리팩토링 실행 순서

### Phase 1: 구조 준비
1. `app/` 디렉토리 생성
2. 기본 `__init__.py` 파일 생성
3. `config/default.yaml`, `config/production.yaml` 생성

### Phase 2: 핵심 모듈 이동
1. `app/core/` 이동 (config, bootstrap, context)
2. `app/strategy/` 이동 (engines 통합)
3. `app/risk/` 이동
4. `app/execution/` 이동 (broker clients 통합)

### Phase 3: 파이프라인 이동
1. `app/pipeline/` 이동 (eteda_runner, eteda_loop)
2. `app/data/` 이동 (repositories, clients)
3. `app/monitoring/` 이동

### Phase 4: Observer Client 생성
1. `app/observer_client/interfaces.py` 생성
2. `app/observer_client/stub.py` 생성

### Phase 5: 엔트리포인트 재정의
1. `app/main.py` 작성
2. 기존 `main.py` → `app/main.py` 로직 이전
3. 기존 `main.py` 삭제 또는 래퍼로 변환

### Phase 6: Import 경로 정리
1. 모든 파일의 import 경로 업데이트
2. 순환 참조 검증

### Phase 7: Docker 배포
1. `Dockerfile` 작성
2. `docker-compose.yaml` 작성 (옵션)
3. Docker 빌드 및 테스트

### Phase 8: 정리
1. 루트의 테스트 파일 → `tests/`로 이동
2. 불필요한 파일/디렉토리 삭제
3. README 업데이트

---

## 10. 검증 체크리스트

- [ ] `python -m app.main --local-only` 정상 실행
- [ ] ETEDA 파이프라인 5단계 정상 동작
- [ ] Mock Broker 주문 테스트 통과
- [ ] Config 로드 (Local + Strategy) 정상
- [ ] Graceful shutdown (Ctrl+C) 정상
- [ ] Docker 빌드 성공
- [ ] Docker 컨테이너 실행 성공
- [ ] 로그 파일 생성 확인
- [ ] Observer stub 연동 테스트

---

## 11. 위험 요소 및 대응

| 위험 | 영향 | 대응 |
|------|------|------|
| 순환 참조 발생 | Import 실패 | 의존성 그래프 검증 |
| Import 경로 누락 | 런타임 에러 | 전체 grep 검색 |
| Config 로드 실패 | 앱 시작 불가 | Preflight check 강화 |
| Docker 빌드 실패 | 배포 불가 | 단계별 빌드 테스트 |

---

**문서 끝**
