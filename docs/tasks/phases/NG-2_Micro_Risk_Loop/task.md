# NG-2: Micro Risk Loop

## 목표

ETEDA와 독립적인 100ms 주기 리스크 제어 루프 구현

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — NG-2 Section
- [docs/arch/sub/16_Micro_Risk_Loop_Architecture.md](../../../arch/sub/16_Micro_Risk_Loop_Architecture.md)
- 코드: `src/runtime/risk/` (확장)

---

## 아키텍처 요약

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

---

## 핵심 작업

| 작업 | 설명 | 상태 |
|------|------|------|
| PositionShadow | 메인 포지션 읽기 전용 복사본 | 🟡 |
| MicroRiskLoop | 100ms 주기 독립 스레드 루프 | 🟡 |
| RiskRuleEvaluator | 4가지 리스크 규칙 평가 | 🟡 |
| ActionDispatcher | P0 이벤트 전송 (긴급 청산 등) | 🟡 |

---

## 체크리스트

### 1. Position Shadow 구현

- [ ] `src/runtime/risk/shadow.py` 생성
- [ ] PositionShadow 클래스
  ```python
  class PositionShadow:
      positions: Dict[str, ShadowPosition]  # symbol → position
      last_sync: datetime
      sync_interval_ms: int = 100
  ```
- [ ] 논블로킹 동기화 메커니즘
- [ ] 읽기 전용 보장 (immutable 또는 복사본)

### 2. Micro Risk Loop 구현

- [ ] `src/runtime/risk/micro_loop.py` 생성
- [ ] MicroRiskLoop 클래스
  ```python
  class MicroRiskLoop:
      def start(self) -> None: ...
      def stop(self) -> None: ...
      def is_running(self) -> bool: ...
  ```
- [ ] 100ms 주기 달성 (p99 < 150ms)
- [ ] ETEDA와 완전 독립 (분리된 스레드)
- [ ] Graceful shutdown 지원

### 3. 리스크 규칙 구현

- [ ] `src/runtime/risk/rules.py` 생성
- [ ] 4가지 규칙 구현:
  - [ ] **Trailing Stop Control**
    - 수익 1% 이상 시 활성화
    - 최고점 대비 0.5% 하락 시 청산 신호
  - [ ] **MAE Threshold**
    - 포지션당 최대 허용 손실 2%
    - 임계값 도달 시 즉시 청산 신호
  - [ ] **Time-in-Trade**
    - Scalp: 1시간 초과 시 경고/청산
    - Swing: 7일 초과 시 경고/청산
  - [ ] **Volatility Kill-Switch**
    - VIX > 40 시 모든 Scalp 포지션 청산
    - VIX > 50 시 Swing도 50% 감축

### 4. Action Dispatcher 연동

- [ ] `src/runtime/risk/actions.py` 생성
- [ ] P0 이벤트 생성 및 전송
  - [ ] EMERGENCY_LIQUIDATE (긴급 청산)
  - [ ] REDUCE_POSITION (포지션 감축)
  - [ ] RISK_WARNING (경고)
- [ ] Event Priority System (NG-1) 연동

### 5. 테스트

- [ ] 단위 테스트: PositionShadow, RiskRules
- [ ] 통합 테스트: MicroRiskLoop 전체 흐름
- [ ] 성능 테스트: 100ms 주기 달성 (p99 < 150ms)
- [ ] 격리 테스트: ETEDA 영향 없음 검증

---

## 구현 범위

| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| PositionShadow | `src/runtime/risk/shadow.py` | 포지션 섀도우 |
| MicroRiskLoop | `src/runtime/risk/micro_loop.py` | 메인 루프 |
| RiskRuleEvaluator | `src/runtime/risk/rules.py` | 규칙 평가 |
| ActionDispatcher | `src/runtime/risk/actions.py` | P0 이벤트 전송 |

---

## 완료 조건 (Exit Criteria)

- [ ] 100ms 주기 달성 (p99 < 150ms)
- [ ] 모든 리스크 규칙 동작 검증 (테스트)
- [ ] ETEDA 영향 없음 (분리 검증)
- [ ] P0 이벤트 전송 < 10ms

---

## 의존성

- **선행 Phase**: NG-1 (Event Priority System)
- **후행 Phase**: 없음 (독립 모듈)
- **Critical Decision**: CD-004 (Micro Risk Loop Isolation)

---

## 예상 기간

2주

---

## 관련 문서

- [16_Micro_Risk_Loop_Architecture.md](../../../arch/sub/16_Micro_Risk_Loop_Architecture.md)
- [17_Event_Priority_Architecture.md](../../../arch/sub/17_Event_Priority_Architecture.md) (P0 이벤트 연동)
