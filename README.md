# QTS (Qualitative Trading System)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

**QTS**는 저지연 스켈핑에 최적화된 **프로덕션급 자동매매 시스템**입니다. ETEDA 파이프라인 아키텍처를 기반으로 설계되었으며, 독립적인 4대 엔진(Strategy, Risk, Portfolio, Performance)이 유기적으로 작동하여 안정적인 매매를 수행합니다.

## 핵심 특징

- **ETEDA 파이프라인**: Extract → Transform → Evaluate → Decide → Act의 5단계 실행 흐름.
- **Multi-Engine 구조**: Strategy, Risk, Portfolio, Performance 4대 독립 엔진 탑재.
- **Observer 통합**: Stub/UDS/IPC 기반 실시간 시장 데이터 수신.
- **Multi-Broker 지원**: 한국투자증권(KIS), 키움증권(KIWOOM) 지원.
- **Safety Layer**: Fail-Safe, Kill Switch, Guardrail 등 다층 안전 시스템 (`src/safety/`).
- **Data Repository**: Google Sheets 연동 및 데이터 영속성 관리 (`src/db/`).

## 폴더 구조

```text
qts/
├── config/                     # 환경별 설정 파일 (YAML/JSON)
├── docker/                     # Docker 배포 설정
├── docs/                       # 기술 문서 및 아키텍처 정의서
├── scripts/                    # 유틸리티 스크립트
├── src/                        # 소스 코드
│   ├── automation/             # 자동화 워크플로우
│   ├── backup/                 # 데이터 백업 및 복구
│   ├── db/                     # 데이터베이스 및 저장소
│   ├── decision_pipeline/      # 의사결정 파이프라인
│   ├── maintenance/            # 시스템 유지보수 태스크
│   ├── monitoring/             # 로깅 및 메트릭
│   ├── observer_client/        # Observer 데이터 수신 인터페이스
│   ├── pipeline/               # ETEDA 파이프라인 런너
│   ├── provider/               # 외부 서비스 프로바이더 (KIS, Kiwoom 등)
│   ├── qts/                    # 핵심 비즈니스 로직
│   ├── retention/              # 데이터 보존 정책
│   ├── risk/                   # 리스크 관리 엔진
│   ├── runtime/                # 런타임 실행 환경
│   ├── safety/                 # 킬스위치 및 가드레일 (Safety Layer)
│   ├── shared/                 # 공통 유틸리티
│   └── strategy/               # 매매 전략 엔진
└── tests/                      # 단위/통합 테스트 스위트
```

## 빠른 시작

### 1. 로컬 개발

```bash
# 의존성 설치
pip install -r requirements.txt

# 설정 파일 생성
cp config/.env.example config/.env

# 로컬 실행
python -m src.runtime.main
```

### 2. Docker 실행

```bash
# Docker Compose 기반 실행
docker-compose -f docker/docker-compose.test.yml up -d --build
```

## 설정 관리

- **설정 파일**: `config/default.yaml` (기본), `config/production.yaml` (운영)
- **환경 변수**: `config/.env` 파일을 통해 `QTS_ENV`, `BROKER_TYPE` 등 주요 설정 주입.

## 개발 가이드 & 문서

- **[설정 가이드](config/README.md)**
- **[테스트 가이드](tests/README.md)**
- **[Docker 가이드](docker/README.md)**
