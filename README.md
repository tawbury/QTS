# QTS (Qualitative Trading System)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**QTS**는 저지연 스켈핑 최적화된 **프로덕션급 자동매매 시스템**입니다.

## 핵심 특징

- **ETEDA 파이프라인**: Extract → Transform → Evaluate → Decide → Act의 5단계 실행 흐름
- **Multi-Engine 구조**: Strategy, Risk, Portfolio, Performance 4대 독립 엔진
- **Observer 통합**: Stub/UDS/IPC 기반 실시간 시장 데이터 수신
- **Multi-Broker 지원**: 한국투자증권(KIS), 키움증권(KIWOOM) 지원
- **Safety Layer**: Fail-Safe, Kill Switch, Guardrail 등 다층 안전 시스템
- **Docker 배포**: 단일 컨테이너 배포, 프로덕션 레디

## 프로젝트 구조 (앱형 리팩토링 완료)

```
qts/
├── app/                        # 애플리케이션 코어
│   ├── core/                   # 앱 생명주기, 설정
│   ├── strategy/               # 매매 전략 로직
│   ├── risk/                   # 리스크 관리
│   ├── execution/              # 주문 실행 & 브로커 클라이언트
│   ├── observer_client/        # Observer 연동 (stub/uds/ipc)
│   ├── pipeline/               # ETEDA 파이프라인
│   ├── data/                   # 데이터 레이어 (Repository)
│   ├── monitoring/             # 로깅, 메트릭
│   └── main.py                 # 단일 엔트리포인트
│
├── ops/                        # 운영 자동화 (Safety Layer, Backup 등)
├── shared/                     # 공용 유틸리티
├── config/                     # 설정 파일 (YAML + JSON)
│   ├── default.yaml
│   ├── production.yaml
│   └── local/
│       └── config_local.json
│
├── tests/                      # 테스트 스위트
├── docs/                       # 문서
│   └── arch/
│       └── QTS_App_Refactoring_Analysis.md
│
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
└── README.md
```

## 아키텍처 개요

### 핵심 설계 원칙

| 원칙 | 설명 |
|------|------|
| **전략 격리** | `app/strategy/` 밖으로 전략 로직 이동 금지 |
| **Observer 추상화** | `app/observer_client/` 통해서만 Observer 접근 |
| **주문 분리** | 전략 코드 내 직접 주문 코드 금지 |
| **단일 진입점** | `app/main.py`만 실행 진입점 |

### 의존성 흐름

```
app/main.py (엔트리포인트)
    ↓
┌────────────────┬──────────────┬───────────────┐
│   core/        │  pipeline/   │  monitoring/  │
│   bootstrap    │  eteda       │  logger       │
└────────┬───────┴──────┬───────┴───────────────┘
         │              │
    ┌────┼──────────────┼────┐
    ▼    ▼              ▼    ▼
┌────────┐ ┌──────┐ ┌───────────┐
│strategy│ │ risk │ │ execution │
└────┬───┘ └──┬───┘ └─────┬─────┘
     │        │           │
     └────────┼───────────┘
              │
              ▼
     ┌────────────────┐
     │ observer_client│ ◀── Observer (외부)
     │ (stub/uds/ipc) │
     └────────────────┘
```

## 빠른 시작

### 1. 로컬 개발 (Stub Observer)

```bash
# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성
cp .env.example .env

# Local-Only 모드 실행 (Mock 클라이언트)
python -m app.main --local-only --verbose

# 최대 5번 반복 후 종료
python -m app.main --local-only --max-iterations 5
```

### 2. 프로덕션 실행

```bash
# Scalp 전략, KIWOOM 브로커
python -m app.main --scope scalp --broker kiwoom --env production

# Swing 전략, KIS 브로커
python -m app.main --scope swing --broker kis --env production
```

### 3. Docker 배포

```bash
# 이미지 빌드
docker build -t qts-trading-system:latest .

# 컨테이너 실행
docker run -d \
  --name qts-app \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config:/app/config:ro \
  --env-file .env \
  qts-trading-system:latest

# Docker Compose 사용
docker-compose up -d
```

## 설정 관리

### YAML 기반 환경별 설정

```yaml
# config/default.yaml (개발)
observer:
  type: "stub"  # stub/uds/ipc
  endpoint: null

broker:
  type: "kiwoom"
  mode: "paper"

# config/production.yaml (프로덕션)
observer:
  type: "uds"
  endpoint: "unix:///var/run/observer.sock"

broker:
  type: "kiwoom"
  mode: "live"
```

### 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `QTS_ENV` | 실행 환경 | `development` |
| `OBSERVER_ENDPOINT` | Observer 연결 경로 | `stub` |
| `BROKER_TYPE` | 브로커 선택 | `kiwoom` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |
| `STRATEGY_SCOPE` | 전략 범위 | `scalp` |

## Observer 연동

### Stub (개발/테스트)

```python
# app/observer_client/stub.py 사용
observer = StubObserverClient()
await observer.connect()
snapshot = await observer.get_snapshot("005930")
```

### UDS (프로덕션)

```python
# app/observer_client/uds_client.py 사용 (향후 구현)
observer = UDSObserverClient(socket_path="/var/run/observer.sock")
await observer.connect()
```

## 테스트

```bash
# 유닛 테스트
pytest tests/unit/ -v

# 통합 테스트
pytest tests/integration/ -v

# 커버리지
pytest --cov=app --cov-report=html
```

## 개발 가이드

### 코드 품질

```bash
# Black 포맷팅
black app/ ops/ shared/

# isort import 정리
isort app/ ops/ shared/

# flake8 린팅
flake8 app/ ops/ shared/

# mypy 타입 체크
mypy app/
```

### 새로운 전략 추가

1. `app/strategy/` 내에 새 전략 클래스 생성
2. `StrategyEngine`에 등록
3. Config Sheet에 전략 파라미터 추가
4. 테스트 작성

### 새로운 브로커 추가

1. `app/execution/clients/` 내에 브로커 클라이언트 구현
2. `BrokerAdapter` 인터페이스 구현
3. Registry에 등록
4. 환경변수/Config에 브로커 추가

## 문서

- [아키텍처 분석](docs/arch/QTS_App_Refactoring_Analysis.md)
- [Observer 연동 가이드](docs/observer_integration.md) (작성 예정)
- [배포 가이드](docs/deployment.md) (작성 예정)

## 라이센스

MIT License

## 기여

이슈 및 풀 리퀘스트는 환영합니다.

## 연락처

QTS Team
