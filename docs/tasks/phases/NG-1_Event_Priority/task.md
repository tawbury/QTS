# NG-1: Event Priority System

## 목표

P0 이벤트의 절대적 레이턴시 보장 (< 10ms)

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — NG-1 Section
- [docs/arch/sub/17_Event_Priority_Architecture.md](../../../arch/sub/17_Event_Priority_Architecture.md)
- 코드: `src/runtime/events/` (신규 생성)

---

## 아키텍처 요약

```python
# 우선순위 계층
P0 (Execution/Fill)   → < 10ms, 전용 스레드, BLOCK 정책
P1 (Market Data)      → < 50ms, 스레드 풀 2개, DROP_OLDEST
P2 (Strategy)         → < 500ms, 워커 풀 4개, COLLAPSE
P3 (UI/Logging)       → Best Effort, 샘플링 허용
```

---

## 핵심 작업

| 작업 | 설명 | 상태 |
|------|------|------|
| EventPriority Enum | P0/P1/P2/P3 우선순위 정의 | 🟡 |
| QTSEvent 데이터 클래스 | 이벤트 데이터 구조 | 🟡 |
| EventQueue | 우선순위별 큐 관리 | 🟡 |
| EventDispatcher | 이벤트 라우팅 및 핸들러 관리 | 🟡 |
| P0 전용 핸들러 스레드 | 레이턴시 격리 보장 | 🟡 |

---

## 체크리스트

### 1. 기본 구조 구현

- [ ] `src/runtime/events/` 폴더 생성
- [ ] `priority.py` — EventPriority Enum
  ```python
  class EventPriority(Enum):
      P0 = 0  # Execution/Fill (< 10ms)
      P1 = 1  # Market Data (< 50ms)
      P2 = 2  # Strategy (< 500ms)
      P3 = 3  # UI/Logging (Best Effort)
  ```
- [ ] `event.py` — QTSEvent 데이터 클래스
  ```python
  @dataclass
  class QTSEvent:
      priority: EventPriority
      event_type: str
      payload: Any
      timestamp: datetime
      source: str
  ```

### 2. 큐 관리 구현

- [ ] `queue.py` — EventQueue
  - [ ] 우선순위별 분리된 큐 (P0~P3)
  - [ ] 큐 오버플로우 정책 (BLOCK, DROP_OLDEST, COLLAPSE)
  - [ ] 큐 크기 제한 설정
- [ ] 큐 메트릭 수집 (크기, 대기 시간)

### 3. 디스패처 구현

- [ ] `dispatcher.py` — EventDispatcher
  - [ ] 핸들러 등록/해제
  - [ ] 우선순위 기반 라우팅
  - [ ] P0 전용 스레드 관리
- [ ] 핸들러 타임아웃 처리

### 4. P0 레이턴시 보장

- [ ] P0 전용 핸들러 스레드 구현
- [ ] OS 스레드 우선순위 조정 (Critical Decision CD-003 반영)
- [ ] P1~P3가 P0를 블로킹하지 않음 검증

### 5. 테스트

- [ ] 단위 테스트: EventPriority, QTSEvent, EventQueue
- [ ] 통합 테스트: EventDispatcher 라우팅
- [ ] 성능 테스트: P0 레이턴시 < 10ms (p99)
- [ ] 스트레스 테스트: 고부하 상황에서 P0 격리 검증

---

## 구현 범위

| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| EventPriority | `src/runtime/events/priority.py` | 우선순위 Enum |
| QTSEvent | `src/runtime/events/event.py` | 이벤트 데이터 클래스 |
| EventQueue | `src/runtime/events/queue.py` | 우선순위별 큐 관리 |
| EventDispatcher | `src/runtime/events/dispatcher.py` | 이벤트 라우팅 |
| `__init__.py` | `src/runtime/events/__init__.py` | 모듈 익스포트 |

---

## 완료 조건 (Exit Criteria)

- [ ] P0 이벤트 처리 레이턴시 < 10ms (p99)
- [ ] P1 이벤트가 P0를 절대 블로킹하지 않음 (테스트 검증)
- [ ] 단위 테스트 100% 커버리지
- [ ] 통합 테스트 통과

---

## 의존성

- **선행 Phase**: NG-0 (E2E Stabilization)
- **후행 Phase**: NG-2 (Micro Risk Loop)
- **Critical Decision**: CD-003 (Event Priority Thread Model)

---

## 예상 기간

2주

---

## 관련 문서

- [17_Event_Priority_Architecture.md](../../../arch/sub/17_Event_Priority_Architecture.md)
