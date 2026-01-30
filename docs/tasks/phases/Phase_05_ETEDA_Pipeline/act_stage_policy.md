# Act Stage Policy (Phase 5)

근거: `docs/arch/03_Pipeline_ETEDA_Architecture.md`, `docs/arch/07_FailSafe_Architecture.md`

## 1. 실행 모드 정의 및 전환

| 모드 | 설명 | 부작용 | 런타임 대응 |
|------|------|--------|-------------|
| **VIRTUAL** | 검증만 수행, 실행 없음 | 없음 | NoopExecutor / VirtualExecutor |
| **SIM** | 시뮬레이션/페이퍼 실행 | 로그/검증만 | SimExecutor (PAPER) |
| **REAL** | 실거래 실행 | 브로커 전송 | Live broker (LIVE) |

- **전환 조건**: Config `RUN_MODE`(또는 ops `context.mode`) + Guard 통과 시에만 해당 모드로 Act 수행.
- **Fail-Safe 연계**: `trading_enabled=False`, `kill_switch=True`, `pipeline_paused=True`, `anomaly_flags` 존재 시 Act 비활성(REJECTED/SKIPPED). Act 실패 시 즉시 Fail-Safe(FS040 등).

## 2. Guard / Fail-Safe 연계

Act 단계 진입 전 공통 Guard(코드: `apply_execution_guards`):

- `symbol` empty → REJECTED (`G_EXE_SYMBOL_EMPTY`)
- `qty` ≤ 0 → REJECTED (`G_EXE_QTY_NONPOSITIVE`)
- `trading_enabled` False → REJECTED (`G_EXE_TRADING_DISABLED`)
- `kill_switch` True → REJECTED (`G_EXE_KILLSWITCH_ON`)
- `anomaly_flags` 존재 → REJECTED (`G_EXE_ANOMALY`)

이 조건과 Fail-Safe 조건을 코드 레벨에서 일관 적용: VirtualExecutor, SimExecutor 모두 동일 Guard 사용 권장. 런타임 ETEDA Act는 Config `trading_enabled`/`KILLSWITCH_STATUS`/`PIPELINE_PAUSED` 등으로 동일 정책 적용.

## 3. ExecutionResult 계약

**Act 단계 정책 결과**(ops `ExecutionResult`):

- `mode`: VIRTUAL | SIM | REAL
- `status`: ACCEPTED | REJECTED | SKIPPED
- `executed`: bool (실제/시뮬 체결 여부)
- `decision_id`, `order_fingerprint`: 추적용
- `blocked_by`, `reason`, `audit`: 차단 시 원인 및 감사

**Ledger 결과**(실제 체결 시): `docs/arch/04_Data_Contract_Spec.md` §6 — `success`, `order_id`, `symbol`, `filled_qty`, `avg_fill_price`, `amount`, `fee`, `timestamp` 등. `status=ACCEPTED`且`executed=True`일 때 하류에서 이 계약으로 기록.

## 4. stub/executor 정합

- **NoopExecutor**: 항상 VIRTUAL, status=SKIPPED, blocked_by=G_EXE_NOOP_POLICY.
- **VirtualExecutor**: Guard 적용 → SKIPPED/REJECTED/ACCEPTED(executed=False).
- **SimExecutor**: Guard 적용 후 시뮬레이션 → ACCEPTED(executed=True) 또는 REJECTED/SKIPPED. Guard 코드는 `execution_guards`와 동일(G_EXE_*) 사용.
