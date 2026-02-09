# QTS (Qualitative Trading System)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**QTS**는 저지연 스켈핑에 최적화된 **프로덕션급 자동매매 시스템**입니다. ETEDA 파이프라인 아키텍처를 기반으로 설계되었으며, 독립적인 4대 엔진(Strategy, Risk, Portfolio, Performance)이 유기적으로 작동하여 안정적인 매매를 수행합니다.

## 핵심 특징

- **ETEDA 파이프라인**: Extract → Transform → Evaluate → Decide → Act의 5단계 실행 흐름.
- **Multi-Engine 구조**: Strategy, Risk, Portfolio, Performance 4대 독립 엔진 탑재.
- **Observer 통합**: Stub/UDS/IPC 기반 실시간 시장 데이터 수신.
- **Multi-Broker 지원**: 한국투자증권(KIS), 키움증권(KIWOOM) 지원.
- **Safety Layer**: Fail-Safe, Kill Switch, Guardrail 등 다층 안전 시스템 (`ops/`).
- **Data Repository**: Google Sheets 연동 및 데이터 영속성 관리 (`app/data/`).

## 폴더 구조

```text
qts/
├── app/                        # 애플리케이션 코어 비즈니스 로직
│   ├── core/                   # 앱 생명주기 및 설정 (Bootstrap, Config)
│   ├── data/                   # 데이터 리포지토리 및 어댑터 (Google Sheets 등)
│   ├── strategy/               # 매매 전략 엔진 및 로직 (Arbitration, Registry)
│   ├── risk/                   # 리스크 관리 엔진 (Calculators, Gates)
│   ├── execution/              # 주문 실행 및 브로커 클라이언트 (KIS, Kiwoom)
│   ├── observer_client/        # Observer 데이터 수신 인터페이스 (Stub/UDS)
│   ├── pipeline/               # ETEDA 파이프라인 런너
│   ├── monitoring/             # 로깅 및 메트릭
│   └── main.py                 # 단일 엔트리포인트
│
├── ops/                        # 운영 및 안정성 레이어
│   ├── safety/                 # 킬스위치 및 가드레일 (Safety Layer)
│   ├── maintenance/            # 시스템 유지보수 태스크
│   ├── automation/             # 자동화 워크플로우
│   └── backup/                 # 데이터 백업 및 복구
│
├── shared/                     # 공통 유틸리티 (Time, Validation 등)
├── config/                     # 환경별 설정 파일 (YAML/JSON)
├── data/                       # 런타임 데이터 및 로컬 스토리지
├── docs/                       # 기술 문서 및 아키텍처 정의서
├── tests/                      # 단위/통합 테스트 스위트
└── docker/                     # Docker 배포 설정
```

## 아키텍처 개요

### 의존성 흐름
`Main` → `Pipeline` → `Engines` (Strategy, Risk) → `Repository` / `Broker` / `Observer`

### 주요 엔진 역할
1.  **Strategy Engine**: 시장 데이터를 분석하여 매매 신호 생성.
2.  **Risk Engine**: 주문 전 리스크 한도 및 규정 준수 여부 검증.
3.  **Portfolio Engine**: 현재 포지션 및 자산 배분 상태 관리.
4.  **Performance Engine**: 수익률 계산 및 성과 분석 리포트 생성.

## 빠른 시작

### 1. 로컬 개발 (Stub Mode)

```bash
# 의존성 설치
pip install -r requirements.txt

# 설정 파일 생성
cp .env.example .env

# 로컬 모드 실행 (Stub Observer 사용)
python -m app.main --local-only --verbose
```

### 2. 프로덕션 실행

```bash
# Docker Compose 기반 실행
docker-compose -f docker/docker-compose.test.yml up -d
```

## 설정 관리

- **설정 파일**: `config/default.yaml` (기본), `config/production.yaml` (운영)
- **환경 변수**: `.env` 파일을 통해 `QTS_ENV`, `BROKER_TYPE` 등 주요 설정 주입.

## 개발 가이드 & 문서

- **[아키텍처 분석](docs/arch/QTS_App_Refactoring_Analysis.md)**
- **[Observer 연동](docs/observer_integration.md)** (작성 예정)
- **Legacy 실행**: 루트의 `main.py`는 하위 호환성을 위한 래퍼입니다. 새로운 엔트리포인트 `python -m app.main`을 사용하세요.
