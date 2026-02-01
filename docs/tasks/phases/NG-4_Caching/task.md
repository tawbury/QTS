# NG-4: Caching Layer

## 목표

Redis 캐싱 레이어 구현으로 Scalp 레이턴시 < 100ms 달성

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — NG-4 Section
- [docs/arch/sub/19_Caching_Architecture.md](../../../arch/sub/19_Caching_Architecture.md)
- 코드: `src/runtime/cache/` (신규 생성)

---

## 아키텍처 요약

```python
# 캐시 모델
price:{symbol}        # Hash, 100ms TTL
pos:{symbol}          # Hash, 1s TTL
book:{symbol}:{side}  # Sorted Set, 50ms TTL
risk:account          # Hash, 5s TTL
ord:{order_id}        # Hash, 60s TTL
strat:{strategy_id}   # Hash, 60s TTL
```

---

## 핵심 작업

| 작업 | 설명 | 상태 |
|------|------|------|
| CacheManager | Redis 연결 풀 및 관리 | 🟡 |
| Cache-Aside 패턴 | 읽기 캐시 패턴 구현 | 🟡 |
| Write-Through 패턴 | 쓰기 캐시 패턴 구현 | 🟡 |
| FallbackHandler | DB Fallback 처리 | 🟡 |
| Circuit Breaker | 캐시 장애 대응 | 🟡 |

---

## 체크리스트

### 1. CacheManager 구현

- [ ] `src/runtime/cache/manager.py` 생성
- [ ] Redis 연결 풀 관리
  ```python
  class CacheManager:
      def __init__(self, redis_url: str, pool_size: int = 10): ...
      def get_connection(self) -> Redis: ...
      def health_check(self) -> bool: ...
  ```
- [ ] 연결 재시도 로직
- [ ] 연결 상태 모니터링

### 2. TTL 기반 캐시 모델

- [ ] `src/runtime/cache/models.py` 생성
- [ ] 캐시 키 스키마 정의
  ```python
  class CacheKeys:
      PRICE = "price:{symbol}"           # 100ms TTL
      POSITION = "pos:{symbol}"          # 1s TTL
      ORDERBOOK = "book:{symbol}:{side}" # 50ms TTL
      RISK = "risk:account"              # 5s TTL
      ORDER = "ord:{order_id}"           # 60s TTL
      STRATEGY = "strat:{strategy_id}"   # 60s TTL
  ```
- [ ] TTL 자동 관리

### 3. Cache-Aside 패턴

- [ ] `src/runtime/cache/patterns/aside.py` 생성
  ```python
  class CacheAside:
      async def get(self, key: str, loader: Callable) -> Any:
          # 1. 캐시 확인
          # 2. 캐시 미스 시 loader 호출
          # 3. 결과 캐시 저장
          # 4. 반환
  ```
- [ ] 캐시 미스 시 DB 로딩
- [ ] 비동기 캐시 갱신 옵션

### 4. Write-Through 패턴

- [ ] `src/runtime/cache/patterns/write.py` 생성
  ```python
  class WriteThrough:
      async def write(self, key: str, value: Any, writer: Callable) -> bool:
          # 1. 캐시에 쓰기
          # 2. DB에 쓰기
          # 3. 실패 시 캐시 무효화
  ```
- [ ] 트랜잭션 일관성 보장
- [ ] 쓰기 실패 시 캐시 무효화

### 5. FallbackHandler

- [ ] `src/runtime/cache/fallback.py` 생성
- [ ] 캐시 장애 시 DB 직접 조회
- [ ] Fallback 메트릭 수집
- [ ] 자동 복구 감지

### 6. Circuit Breaker

- [ ] `src/runtime/cache/circuit_breaker.py` 생성
- [ ] 상태: CLOSED → OPEN → HALF_OPEN
- [ ] 실패 임계값 설정 (연속 5회)
- [ ] 복구 대기 시간 (30초)
- [ ] Half-Open 시 테스트 요청

### 7. 테스트

- [ ] 단위 테스트: CacheManager, Patterns
- [ ] 통합 테스트: Cache + DB 연동
- [ ] 성능 테스트: Cache Hit Rate > 90%
- [ ] 장애 테스트: Circuit Breaker 동작

---

## 구현 범위

| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| CacheManager | `src/runtime/cache/manager.py` | Redis 연결 풀 |
| CacheModels | `src/runtime/cache/models.py` | 캐시 키/TTL 정의 |
| CacheAside | `src/runtime/cache/patterns/aside.py` | Cache-Aside 패턴 |
| WriteThrough | `src/runtime/cache/patterns/write.py` | Write-Through |
| FallbackHandler | `src/runtime/cache/fallback.py` | DB Fallback |
| CircuitBreaker | `src/runtime/cache/circuit_breaker.py` | 장애 대응 |

---

## 완료 조건 (Exit Criteria)

- [ ] Redis 연결 및 TTL 관리 구현
- [ ] Cache Hit Rate > 90% (벤치마크)
- [ ] Graceful Degradation (캐시 장애 시 DB 폴백)
- [ ] Circuit Breaker 구현 및 테스트
- [ ] Scalp 조회 레이턴시 < 100ms

---

## 의존성

- **선행 Phase**: NG-3 (Data Layer Migration)
- **후행 Phase**: NG-6 (Scalp Execution)
- **Critical Decision**: CD-002 (Redis Infrastructure)

---

## 예상 기간

2주

---

## 관련 문서

- [19_Caching_Architecture.md](../../../arch/sub/19_Caching_Architecture.md)
- [18_Data_Layer_Architecture.md](../../../arch/sub/18_Data_Layer_Architecture.md)
