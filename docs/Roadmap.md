# QTS Next-Generation Roadmap

_(Strategic Implementation Plan — Post Phase 1-10 Completion)_

**최종 갱신:** 2026-01-31
**버전:** v2.0.0 (Next-Gen Roadmap)

---

## 0. Executive Summary

QTS(Qualitative Trading System)는 Phase 1~10의 기초 구현을 완료했습니다. 본 로드맵은 **E2E 테스팅 및 안정화** 이후 **차세대 아키텍처(docs/arch/sub/ 14~20번)** 구현을 목표로 합니다.

### 핵심 전략적 방향

```
[E2E Testing & Stabilization]
           ↓
[Advanced Architecture Implementation]
           ↓
[Operational Automation & Production Readiness]
```

---

## 1. Phase 상태 요약 (Legacy Phases)

| Phase | 이름 | 상태 | 비고 |
|-------|------|------|------|
| 0 | Observer Infrastructure | ↗️ | 독립 프로젝트 분리 |
| 1 | Schema & Sheet Mapping | ✅ | 완료 |
| 2 | Config Architecture (Sheet) | ✅ | 완료 |
| 3 | Config Architecture (Local) | ✅ | 완료 |
| 4 | Engine Layer | ✅ | 완료 |
| 5 | Execution Pipeline (ETEDA) | ✅ | 완료 |
| 6 | Dashboard / Visualization | ✅ | 완료 |
| 7 | Safety & Risk Core | ✅ | 완료 |
| 8 | Multi-Broker Integration | ✅ | 완료 |
| 9 | Ops & Automation | ✅ | 완료 |
| 10 | Test & Governance | ✅ | 완료 |

**Legacy Phase 문서:** `docs/tasks/phases/`, `docs/tasks/finished/phases_no1/`

---

## 2. Next-Gen Roadmap Overview

### 2.1 우선순위 및 진행 순서

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NEXT-GEN IMPLEMENTATION PHASES                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  NG-0. E2E Testing & Stabilization (Foundation)                    │
│        ├─ E2E 통합 테스트 시나리오 실행                              │
│        ├─ 성능 벤치마크 및 병목 식별                                 │
│        └─ 버그 수정 및 안정화                                        │
│                           ↓                                         │
│  NG-1. Event Priority System (17번)                                 │
│        ├─ P0/P1/P2/P3 우선순위 큐 구현                              │
│        ├─ P0 전용 핸들러 스레드                                      │
│        └─ 레이턴시 격리 보장                                         │
│                           ↓                                         │
│  NG-2. Micro Risk Loop (16번)                                       │
│        ├─ 독립 스레드 기반 100ms 주기 루프                           │
│        ├─ Position Shadow 동기화                                    │
│        └─ 4가지 리스크 규칙 (Trailing Stop, MAE, Time, Volatility)  │
│                           ↓                                         │
│  NG-3. Data Layer Migration (18-2번)                               │
│        ├─ PostgreSQL + TimescaleDB 스키마                           │
│        ├─ DataSourceAdapter 인터페이스                              │
│        └─ HybridAdapter (Dual-Write) 마이그레이션                   │
│                           ↓                                         │
│  NG-4. Caching Layer (19번)                                        │
│        ├─ Redis 캐싱 레이어 구현                                     │
│        ├─ Cache-Aside / Write-Through 패턴                          │
│        └─ Scalp 레이턴시 < 100ms 목표 달성                          │
│                           ↓                                         │
│  NG-5. Capital Flow Engine (14번)                                  │
│        ├─ 3-Track 자본 전략 (Scalp/Swing/Portfolio)                 │
│        ├─ Capital Engine (6번째 엔진)                               │
│        └─ Promotion/Demotion 규칙 구현                              │
│                           ↓                                         │
│  NG-6. Scalp Execution Micro-Pipeline (15번)                       │
│        ├─ 6단계 실행 파이프라인                                      │
│        │   (PreCheck→OrderSplit→AsyncSend→                         │
│        │    PartialFillMonitor→AdaptiveAdjust→EmergencyEscape)     │
│        └─ 전체 실행 < 100ms (체결 대기 제외)                        │
│                           ↓                                         │
│  NG-7. System State Promotion (18-1번)                             │
│        ├─ Operating State (AGGRESSIVE/BALANCED/DEFENSIVE)           │
│        ├─ 상태 전이 조건 및 리밸런싱                                 │
│        └─ Safety State와 연계                                       │
│                           ↓                                         │
│  NG-8. Feedback Loop (20번)                                        │
│        ├─ 실행 품질 메트릭 수집                                      │
│        ├─ Slippage/Market Impact 분석                               │
│        └─ Strategy Engine 피드백 연동                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Phase Specifications

### NG-0: E2E Testing & Stabilization

**목표:** 현재 구현된 Phase 1~10의 통합 테스트 및 프로덕션 준비

**핵심 작업:**
| 작업 | 설명 | 상태 |
|------|------|------|
| E2E 시나리오 테스트 | ETEDA 전체 흐름 (Extract→Act) 통합 검증 | 🟡 |
| 성능 벤치마크 | 각 단계별 레이턴시 측정 및 병목 식별 | 🟡 |
| 실 환경 스모크 테스트 | Google Sheets + KIS Mock API 연동 | 🟡 |
| 버그 수정 | 발견된 이슈 해결 및 안정화 | 🟡 |

**Exit Criteria:**
- [ ] `pytest tests/ -v` 전체 통과 (live_sheets, real_broker 제외)
- [ ] E2E 시나리오 10회 연속 성공
- [ ] 평균 ETEDA 사이클 < 3초 (Google Sheets 기준)

---

### NG-1: Event Priority System (17번)

**목표:** P0 이벤트의 절대적 레이턴시 보장 (< 10ms)

**아키텍처 참조:** `docs/arch/sub/17_Event_Priority_Architecture.md`

**핵심 컴포넌트:**
```python
# 우선순위 계층
P0 (Execution/Fill)   → < 10ms, 전용 스레드, BLOCK 정책
P1 (Market Data)      → < 50ms, 스레드 풀 2개, DROP_OLDEST
P2 (Strategy)         → < 500ms, 워커 풀 4개, COLLAPSE
P3 (UI/Logging)       → Best Effort, 샘플링 허용
```

**구현 범위:**
| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| EventPriority | `src/runtime/events/priority.py` | 우선순위 Enum |
| QTSEvent | `src/runtime/events/event.py` | 이벤트 데이터 클래스 |
| EventQueue | `src/runtime/events/queue.py` | 우선순위별 큐 관리 |
| EventDispatcher | `src/runtime/events/dispatcher.py` | 이벤트 라우팅 |

**Exit Criteria:**
- [ ] P0 이벤트 처리 레이턴시 < 10ms (p99)
- [ ] P1 이벤트가 P0를 절대 블로킹하지 않음 (테스트 검증)
- [ ] 단위 테스트 100% 커버리지

---

### NG-2: Micro Risk Loop (16번)

**목표:** ETEDA와 독립적인 100ms 주기 리스크 제어

**아키텍처 참조:** `docs/arch/sub/16_Micro_Risk_Loop_Architecture.md`

**핵심 컴포넌트:**
```python
# Position Shadow
- 메인 포지션의 읽기 전용 복사본
- 100ms 주기 동기화
- 논블로킹 아키텍처

# 4가지 리스크 규칙
1. Trailing Stop Control (수익 1% 이상 시 활성화)
2. MAE Threshold (포지션당 2% 임계값)
3. Time-in-Trade (Scalp 1시간, Swing 7일)
4. Volatility Kill-Switch (VIX > 40)
```

**구현 범위:**
| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| PositionShadow | `src/runtime/risk/shadow.py` | 포지션 섀도우 |
| MicroRiskLoop | `src/runtime/risk/micro_loop.py` | 메인 루프 |
| RiskRuleEvaluator | `src/runtime/risk/rules.py` | 규칙 평가 |
| ActionDispatcher | `src/runtime/risk/actions.py` | P0 이벤트 전송 |

**Exit Criteria:**
- [ ] 100ms 주기 달성 (p99 < 150ms)
- [ ] 모든 리스크 규칙 동작 검증 (테스트)
- [ ] ETEDA 영향 없음 (분리 검증)

**의존성:** NG-1 (Event Priority System)

---

### NG-3: Data Layer Migration (18-2번)

**목표:** PostgreSQL + TimescaleDB로 확장 가능한 데이터 레이어

**아키텍처 참조:** `docs/arch/sub/18_Data_Layer_Architecture.md`

**스키마 설계:**
```sql
-- Hypertables (시계열)
tick_data          -- 7일 보존, 자동 압축
ohlcv_1d          -- 영구 보존
execution_logs    -- 90일 보존
feedback_data     -- 180일 보존

-- Regular Tables (트랜잭션)
positions, t_ledger, strategies, risk_configs

-- Continuous Aggregates
ohlcv_1m, daily_pnl, hourly_execution_metrics
```

**구현 범위:**
| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| DataSourceAdapter | `src/runtime/data/adapters/base.py` | 추상 인터페이스 |
| GoogleSheetsAdapter | `src/runtime/data/adapters/sheets.py` | 기존 구현 래핑 |
| TimescaleDBAdapter | `src/runtime/data/adapters/timescale.py` | 신규 구현 |
| HybridAdapter | `src/runtime/data/adapters/hybrid.py` | Dual-Write |

**Exit Criteria:**
- [ ] DDL 스크립트 완성 및 검증
- [ ] Adapter 패턴 구현 완료
- [ ] Dual-Write 마이그레이션 테스트 통과
- [ ] 롤백 절차 문서화

---

### NG-4: Caching Layer (19번)

**목표:** Scalp 레이턴시 < 100ms 달성

**아키텍처 참조:** `docs/arch/sub/19_Caching_Architecture.md`

**캐시 모델:**
```python
price:{symbol}        # Hash, 100ms TTL
pos:{symbol}          # Hash, 1s TTL
book:{symbol}:{side}  # Sorted Set, 50ms TTL
risk:account          # Hash, 5s TTL
ord:{order_id}        # Hash, 60s TTL
strat:{strategy_id}   # Hash, 60s TTL
```

**구현 범위:**
| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| CacheManager | `src/runtime/cache/manager.py` | Redis 연결 풀 |
| CacheAside | `src/runtime/cache/patterns/aside.py` | Cache-Aside 패턴 |
| WriteThrough | `src/runtime/cache/patterns/write.py` | Write-Through |
| FallbackHandler | `src/runtime/cache/fallback.py` | DB Fallback |

**Exit Criteria:**
- [ ] Redis 연결 및 TTL 관리 구현
- [ ] Cache Hit Rate > 90% (벤치마크)
- [ ] Graceful Degradation (캐시 장애 시 DB 폴백)
- [ ] Circuit Breaker 구현

**의존성:** NG-3 (Data Layer)

---

### NG-5: Capital Flow Engine (14번)

**목표:** 3-Track 자본 전략 및 풀 기반 자본 관리

**아키텍처 참조:** `docs/arch/sub/14_Capital_Flow_Architecture.md`

**자본 풀 구조:**
```python
# 3-Track Strategy
SCALP     → 현금흐름 창출, 고빈도
SWING     → 복리 성장, 중빈도
PORTFOLIO → 자산 보존, 저빈도

# Promotion 조건
Scalp → Swing: 누적 수익 > 100만원, Sharpe > 1.5, 승률 > 55%
Swing → Portfolio: 누적 수익 > 500만원, Sharpe > 1.2
```

**구현 범위:**
| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| CapitalPool | `src/runtime/capital/pool.py` | 풀 상태 관리 |
| CapitalEngine | `src/runtime/engines/capital_engine.py` | 배분 엔진 |
| PromotionRule | `src/runtime/capital/promotion.py` | 프로모션 규칙 |
| RebalancePolicy | `src/runtime/capital/rebalance.py` | 리밸런싱 |

**Exit Criteria:**
- [ ] Capital Engine ETEDA 통합
- [ ] Promotion/Demotion 규칙 동작 검증
- [ ] FS080-FS089 Fail-Safe 연동
- [ ] GR050-GR059 Guardrail 연동

**의존성:** NG-3 (Data Layer), NG-7 (System State)

---

### NG-6: Scalp Execution Micro-Pipeline (15번)

**목표:** 6단계 마이크로 실행 파이프라인

**아키텍처 참조:** `docs/arch/sub/15_Scalp_Execution_Micro_Architecture.md`

**파이프라인 단계:**
```
PreCheck (< 5ms)
    ↓
OrderSplit (VWAP/TWAP/Iceberg)
    ↓
AsyncSend (< 10ms)
    ↓
PartialFillMonitor (< 60s)
    ↓
AdaptiveAdjust (< 5ms, 최대 3회)
    ↓
EmergencyEscape (< 5ms)
```

**구현 범위:**
| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| PreCheckStage | `src/runtime/execution/stages/precheck.py` | 사전 검증 |
| OrderSplitStage | `src/runtime/execution/stages/split.py` | 주문 분할 |
| AsyncSendStage | `src/runtime/execution/stages/send.py` | 비동기 전송 |
| FillMonitor | `src/runtime/execution/stages/monitor.py` | 체결 모니터 |
| AdaptiveAdjust | `src/runtime/execution/stages/adjust.py` | 적응형 조정 |
| EmergencyEscape | `src/runtime/execution/stages/escape.py` | 긴급 탈출 |

**Exit Criteria:**
- [ ] 전체 실행 < 100ms (체결 대기 제외)
- [ ] 각 단계 레이턴시 목표 달성
- [ ] Slippage < 0.5% (시뮬레이션)

**의존성:** NG-1, NG-4

---

### NG-7: System State Promotion (18-1번)

**목표:** 운영 상태 기반 동적 자본 배분

**아키텍처 참조:** `docs/arch/sub/18_System_State_Promotion_Architecture.md`

**운영 상태:**
```python
AGGRESSIVE  → Scalp 60-80%, Swing 15-30%, Portfolio 5-10%
BALANCED    → Scalp 30-50%, Swing 30-40%, Portfolio 20-30%
DEFENSIVE   → Scalp 5-15%, Swing 15-25%, Portfolio 60-80%
```

**상태 전이 조건:**
```
AGGRESSIVE → BALANCED: DD > 5%, VIX > 25, 연속 손실 > 5회
BALANCED → DEFENSIVE: DD > 10%, VIX > 30, Safety WARNING/FAIL
DEFENSIVE → BALANCED: DD < 5%, VIX < 20, 연속 수익 >= 3일 (최소 5일 유지)
```

**구현 범위:**
| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| OperatingState | `src/runtime/state/operating.py` | 상태 정의 |
| StateTransition | `src/runtime/state/transition.py` | 전이 로직 |
| AllocationPolicy | `src/runtime/state/allocation.py` | 배분 정책 |

**Exit Criteria:**
- [ ] 3가지 운영 상태 구현
- [ ] 상태 전이 조건 자동 평가
- [ ] Safety State 연계 동작
- [ ] 일일 최대 5% 조정 제한

**의존성:** NG-5 (Capital Flow)

---

### NG-8: Feedback Loop (20번)

**목표:** 실행 품질 기반 전략 개선

**아키텍처 참조:** `docs/arch/sub/20_Feedback_Loop_Architecture.md`

**피드백 데이터:**
```python
FeedbackData:
  - total_slippage_bps: float
  - avg_fill_latency_ms: float
  - partial_fill_ratio: float
  - execution_quality_score: float (0.0-1.0)
  - market_impact_bps: float
```

**구현 범위:**
| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| FeedbackAggregator | `src/runtime/feedback/aggregator.py` | 데이터 수집 |
| SlippageCalculator | `src/runtime/feedback/slippage.py` | 슬리피지 계산 |
| QualityScorer | `src/runtime/feedback/quality.py` | 품질 점수 |
| StrategyFeedback | `src/runtime/feedback/strategy.py` | 전략 연동 |

**Exit Criteria:**
- [ ] 실행 품질 메트릭 수집 구현
- [ ] TimescaleDB 저장 (180일 보존)
- [ ] Strategy Engine 피드백 연동 (보정 입력)

**의존성:** NG-3, NG-6

---

## 4. Critical Decisions Pending

### [CD-001] Database Migration Strategy

**이슈:** PostgreSQL + TimescaleDB 마이그레이션 시 Google Sheets 병행 운영 기간

**권장 방안:**
1. **Dual-Write 기간**: 2주 (데이터 정합성 검증)
2. **Read 전환**: Dual-Write 성공 후 TimescaleDB 우선 읽기
3. **Cutover**: 정합성 100% 확인 후 Google Sheets 읽기 중단

**결정 필요:** 마이그레이션 시작 시점 및 롤백 기준

---

### [CD-002] Redis Infrastructure

**이슈:** Redis 인프라 구성 (Single vs Sentinel vs Cluster)

**권장 방안:**
- **초기**: Single Instance (개발/테스트)
- **프로덕션**: Redis Sentinel (고가용성)
- **확장 시**: Redis Cluster (수평 확장)

**결정 필요:** 프로덕션 Redis 인프라 사양 및 호스팅

---

### [CD-003] Event Priority Thread Model

**이슈:** P0 전용 핸들러 스레드의 OS 우선순위 설정

**권장 방안:**
- Python threading + `nice` 값 조정 (Linux)
- Windows: `SetThreadPriority` API 래퍼

**결정 필요:** 스레드 모델 및 OS별 구현 방식

---

### [CD-004] Micro Risk Loop Isolation

**이슈:** MicroRiskLoop의 GIL 영향 및 멀티프로세싱 고려

**권장 방안:**
1. **초기**: Threading 기반 (GIL 영향 최소화 - I/O 바운드)
2. **성능 이슈 시**: `multiprocessing` 또는 별도 프로세스

**결정 필요:** 초기 구현 방식 및 성능 벤치마크 기준

---

## 5. Legacy Phase Maintenance

### 5.1 유지보수 범위

Phase 1~10은 **핵심 기능 유지**만 수행:

| Phase | 유지보수 범위 |
|-------|---------------|
| 1-3 | Config/Schema 버그 수정 |
| 4 | Engine I/O 계약 유지 |
| 5 | ETEDA 파이프라인 안정성 |
| 6 | UI Contract 호환성 |
| 7 | Safety State 일관성 |
| 8 | Broker Adapter 호환성 |
| 9-10 | 테스트 유지 |

### 5.2 변경 금지 영역

- **인터페이스 변경**: 기존 시그니처 유지 (어댑터 패턴으로 확장)
- **데이터 계약**: RawDataContract, CalcDataContract 구조 유지
- **Safety 코드**: 기존 FS/GR 코드 변경 금지 (신규 추가만 허용)

---

## 6. Implementation Timeline

| Phase | 예상 기간 | 의존성 |
|-------|----------|--------|
| NG-0 | 1주 | - |
| NG-1 | 2주 | NG-0 |
| NG-2 | 2주 | NG-1 |
| NG-3 | 3주 | NG-0 |
| NG-4 | 2주 | NG-3 |
| NG-5 | 2주 | NG-3, NG-7 |
| NG-6 | 3주 | NG-1, NG-4 |
| NG-7 | 2주 | NG-5 |
| NG-8 | 2주 | NG-3, NG-6 |

**병렬 가능 경로:**
- NG-0 → NG-1 → NG-2 (Event/Risk 경로)
- NG-0 → NG-3 → NG-4 (Data/Cache 경로)
- NG-5 → NG-7 (Capital/State 경로, NG-3 이후)
- NG-6 (NG-1, NG-4 완료 후)
- NG-8 (마지막)

---

## 7. 문서 참조

### 아키텍처 문서
- `docs/arch/sub/14_Capital_Flow_Architecture.md`
- `docs/arch/sub/15_Scalp_Execution_Micro_Architecture.md`
- `docs/arch/sub/16_Micro_Risk_Loop_Architecture.md`
- `docs/arch/sub/17_Event_Priority_Architecture.md`
- `docs/arch/sub/18_System_State_Promotion_Architecture.md`
- `docs/arch/sub/18_Data_Layer_Architecture.md`
- `docs/arch/sub/19_Caching_Architecture.md`
- `docs/arch/sub/20_Feedback_Loop_Architecture.md`

### 운영 문서
- `docs/tasks/phases/` — Phase별 Task 현황
- `docs/tasks/finished/phases_no1/` — 완료된 Task 기록
- `docs/tasks/archive/` — 히스토리컬 아카이브

---

**End of Roadmap v2.0.0**
