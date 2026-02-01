# QTS (Qualitative Trading System)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**QTS**는 데이터 중심(Data-Driven), 파이프라인 기반(Pipeline-Oriented), 스키마 자동화(Schema Automation) 아키텍처를 갖춘 **엔터프라이즈급 자동매매 시스템**입니다.

## 핵심 특징

- **ETEDA 파이프라인**: Extract → Transform → Evaluate → Decide → Act의 5단계 실행 흐름
- **Multi-Engine 구조**: Strategy, Risk, Portfolio, Performance 4대 독립 엔진
- **Schema Automation**: Google Sheets 구조 변경 시 자동 매핑 및 복구
- **Zero-Formula UI**: 모든 계산은 Python에서 수행, Sheets는 시각화 전용
- **Multi-Broker 지원**: 한국투자증권(KIS) 기본 지원, 확장 가능한 Broker Adapter 패턴
- **Safety Layer**: Fail-Safe, Guardrail, Lockdown 등 다층 안전 시스템

## 프로젝트 구조

```
prj_qts/
├── src/
│   ├── runtime/               # 핵심 런타임 시스템
│   │   ├── auth/              # 인증 (KIS OAuth2)
│   │   ├── broker/            # 브로커 어댑터 (KIS API)
│   │   ├── config/            # 설정 관리 (3분할: Local/Scalp/Swing)
│   │   ├── data/              # 데이터 레이어 (Repository 패턴)
│   │   ├── engines/           # 엔진 레이어 (Strategy/Risk/Portfolio/Performance)
│   │   ├── execution/         # 실행 레이어 (Broker Factory, Intent/Response)
│   │   ├── pipeline/          # ETEDA 파이프라인
│   │   ├── risk/              # 리스크 계산기 및 게이트
│   │   ├── schema/            # 스키마 자동화 엔진
│   │   ├── strategy/          # 전략 모듈
│   │   └── ui/                # Zero-Formula UI 렌더러
│   ├── ops/                   # 운영 자동화
│   │   ├── automation/        # 스케줄러, 알림
│   │   ├── decision_pipeline/ # ops 레벨 의사결정 파이프라인
│   │   ├── maintenance/       # 백업, 정리, 리텐션
│   │   └── safety/            # Safety Layer (Guard, Notifier, State)
│   └── shared/                # 공용 유틸리티
├── tests/                     # 테스트 스위트 (pytest)
├── docs/
│   ├── arch/                  # 아키텍처 문서
│   └── tasks/                 # Task 관리 문서
└── scripts/                   # 유틸리티 스크립트
```

## 아키텍처 개요

### 7 Layer Model

| Layer | 설명 |
|-------|------|
| L1. UI Layer | Zero-Formula Dashboard (R_Dash) |
| L2. Data Layer | 11개 시트 기반 데이터 (Google Sheets 10 + Config_Local) |
| L3. Schema Layer | 스키마 자동화 엔진, 데이터 계약 |
| L4. Engine Layer | Strategy/Risk/Portfolio/Performance 엔진 |
| L5. Pipeline Layer | ETEDA 실행 파이프라인 |
| L6. Broker Layer | Multi-Broker 추상화 (KIS → 확장) |
| L7. Ops & Safety Layer | 운영 자동화, Fail-Safe, Guardrail |

### ETEDA 파이프라인

```
┌─────────┐     ┌───────────┐     ┌──────────┐     ┌────────┐     ┌─────┐
│ Extract │ ──▶ │ Transform │ ──▶ │ Evaluate │ ──▶ │ Decide │ ──▶ │ Act │
└─────────┘     └───────────┘     └──────────┘     └────────┘     └─────┘
   데이터         정규화/계산      엔진 평가        최종 결정      주문 실행
```

## 시작하기

### 요구사항

- Python 3.10+
- Google Cloud 서비스 계정 (Google Sheets API)
- 한국투자증권 API 계정 (실거래 시)

### 설치

```bash
# 저장소 클론
git clone https://github.com/your-username/prj_qts.git
cd prj_qts

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 환경 설정

`.env` 파일을 프로젝트 루트에 생성:

```env
# Google Sheets
GOOGLE_CREDENTIALS_FILE=path/to/service-account.json
GOOGLE_SHEET_KEY=your-spreadsheet-id

# KIS API (선택)
KIS_APP_KEY=your-app-key
KIS_APP_SECRET=your-app-secret
KIS_ACCOUNT_NO=your-account-number
```

### 테스트 실행

```bash
# 전체 테스트 (live_sheets, real_broker 제외)
pytest tests/ -v -m "not live_sheets and not real_broker"

# Google Sheets 연동 테스트 (env 설정 필요)
pytest tests/ -v -m "live_sheets"

# 실 브로커 스모크 테스트 (opt-in)
pytest tests/ -v -m "real_broker"
```

## 문서

- **아키텍처**: [`docs/arch/`](docs/arch/) - 시스템 설계 문서
- **로드맵**: [`docs/Roadmap.md`](docs/Roadmap.md) - Next-Gen 구현 계획
- **Task 관리**: [`docs/tasks/`](docs/tasks/) - Phase별 작업 현황

### 주요 아키텍처 문서

| 문서 | 설명 |
|------|------|
| [00_Architecture.md](docs/arch/00_Architecture.md) | QTS 전체 아키텍처 (Main) |
| [03_Pipeline_ETEDA_Architecture.md](docs/arch/03_Pipeline_ETEDA_Architecture.md) | ETEDA 파이프라인 상세 |
| [07_FailSafe_Architecture.md](docs/arch/07_FailSafe_Architecture.md) | Safety Layer 설계 |
| [08_Broker_Integration_Architecture.md](docs/arch/08_Broker_Integration_Architecture.md) | Multi-Broker 아키텍처 |

## 현재 상태 (Next-Gen Roadmap v2.0.0)

| Phase | 이름 | 상태 |
|-------|------|------|
| NG-0 | E2E Testing & Stabilization | 🟡 진행 중 |
| NG-1 | Event Priority System | ⏳ 대기 |
| NG-2 | Micro Risk Loop | ⏳ 대기 |
| NG-3 | Data Layer Migration | ⏳ 대기 |
| NG-4 | Caching Layer | ⏳ 대기 |
| NG-5 | Capital Flow Engine | ⏳ 대기 |
| NG-6 | Scalp Execution Micro-Pipeline | ⏳ 대기 |
| NG-7 | System State Promotion | ⏳ 대기 |
| NG-8 | Feedback Loop | ⏳ 대기 |

**Legacy Phase 1-10**: ✅ 완료 (`docs/tasks/finished/phases_no1/`)

## 설계 원칙

1. **Data-Driven**: 모든 판단은 데이터 계약(Data Contract)에 종속
2. **Pipeline-Oriented**: 매매는 이벤트가 아닌 파이프라인 흐름
3. **Engine-Modular**: 엔진은 독립적이지만 데이터로 연결
4. **Schema-Automation**: 시트 변경에도 시스템은 멈추지 않음
5. **Zero-Formula UI**: Sheets는 계산도구가 아닌 인터페이스
6. **Safety-First**: 잘못된 매매보다 중단이 낫다

## 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

## 기여

이슈 및 풀 리퀘스트 환영합니다. 기여 전 아키텍처 문서를 먼저 검토해 주세요.

---

**최종 갱신**: 2026-01-31
