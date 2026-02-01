# NG-3: Data Layer Migration

## 목표

PostgreSQL + TimescaleDB로 확장 가능한 데이터 레이어 구축

## 근거

- [docs/Roadmap.md](../../../Roadmap.md) — NG-3 Section
- [docs/arch/sub/18_Data_Layer_Architecture.md](../../../arch/sub/18_Data_Layer_Architecture.md)
- 코드: `src/runtime/data/adapters/` (신규 생성)

---

## 아키텍처 요약

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

---

## 핵심 작업

| 작업 | 설명 | 상태 |
|------|------|------|
| DataSourceAdapter 인터페이스 | 추상 어댑터 정의 | 🟡 |
| GoogleSheetsAdapter | 기존 구현 래핑 | 🟡 |
| TimescaleDBAdapter | PostgreSQL/TimescaleDB 구현 | 🟡 |
| HybridAdapter | Dual-Write 마이그레이션 | 🟡 |
| DDL 스크립트 | 스키마 정의 | 🟡 |

---

## 체크리스트

### 1. 스키마 설계

- [ ] `scripts/sql/` 폴더 생성
- [ ] `001_init_schema.sql` — 기본 테이블
  ```sql
  CREATE TABLE positions (
      id SERIAL PRIMARY KEY,
      symbol VARCHAR(20) NOT NULL,
      strategy_type VARCHAR(20) NOT NULL,
      qty DECIMAL(18,8) NOT NULL,
      avg_price DECIMAL(18,8) NOT NULL,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );
  ```
- [ ] `002_timescale_hypertables.sql` — 시계열 테이블
- [ ] `003_continuous_aggregates.sql` — 집계 뷰
- [ ] `004_retention_policies.sql` — 보존 정책

### 2. DataSourceAdapter 인터페이스

- [ ] `src/runtime/data/adapters/base.py` 생성
  ```python
  class DataSourceAdapter(Protocol):
      def read(self, query: str, params: Dict) -> List[Dict]: ...
      def write(self, table: str, data: Dict) -> bool: ...
      def batch_write(self, table: str, data: List[Dict]) -> int: ...
      def health_check(self) -> bool: ...
  ```
- [ ] 공통 에러 타입 정의
- [ ] 연결 풀 인터페이스

### 3. GoogleSheetsAdapter 래핑

- [ ] `src/runtime/data/adapters/sheets.py` 생성
- [ ] 기존 `GoogleSheetsClient` 래핑
- [ ] `DataSourceAdapter` 프로토콜 구현
- [ ] 기존 리포지토리와 호환성 유지

### 4. TimescaleDBAdapter 구현

- [ ] `src/runtime/data/adapters/timescale.py` 생성
- [ ] asyncpg 또는 psycopg3 기반 구현
- [ ] 연결 풀 관리 (최소 5, 최대 20)
- [ ] Prepared Statement 캐싱
- [ ] 트랜잭션 지원

### 5. HybridAdapter (Dual-Write)

- [ ] `src/runtime/data/adapters/hybrid.py` 생성
- [ ] Dual-Write 로직
  ```python
  class HybridAdapter:
      def write(self, table, data):
          # 1. Primary (TimescaleDB)에 쓰기
          # 2. Secondary (Sheets)에 쓰기
          # 3. 불일치 감지 및 로깅
  ```
- [ ] 읽기 전환 플래그 (Sheets → TimescaleDB)
- [ ] 불일치 감지 및 알림

### 6. 마이그레이션 도구

- [ ] `scripts/migration/` 폴더 생성
- [ ] 초기 데이터 마이그레이션 스크립트
- [ ] 롤백 스크립트
- [ ] 정합성 검증 스크립트

### 7. 테스트

- [ ] 단위 테스트: 각 Adapter
- [ ] 통합 테스트: Hybrid Dual-Write
- [ ] 마이그레이션 테스트: Sheets → TimescaleDB
- [ ] 롤백 테스트: 마이그레이션 실패 시 복구

---

## 구현 범위

| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| DataSourceAdapter | `src/runtime/data/adapters/base.py` | 추상 인터페이스 |
| GoogleSheetsAdapter | `src/runtime/data/adapters/sheets.py` | 기존 구현 래핑 |
| TimescaleDBAdapter | `src/runtime/data/adapters/timescale.py` | 신규 구현 |
| HybridAdapter | `src/runtime/data/adapters/hybrid.py` | Dual-Write |
| DDL Scripts | `scripts/sql/*.sql` | 스키마 정의 |

---

## 완료 조건 (Exit Criteria)

- [ ] DDL 스크립트 완성 및 검증
- [ ] Adapter 패턴 구현 완료
- [ ] Dual-Write 마이그레이션 테스트 통과
- [ ] 롤백 절차 문서화
- [ ] 기존 리포지토리 호환성 유지

---

## 의존성

- **선행 Phase**: NG-0 (E2E Stabilization)
- **후행 Phase**: NG-4 (Caching Layer), NG-5 (Capital Flow)
- **Critical Decision**: CD-001 (Database Migration Strategy)

---

## 예상 기간

3주

---

## 관련 문서

- [18_Data_Layer_Architecture.md](../../../arch/sub/18_Data_Layer_Architecture.md)
