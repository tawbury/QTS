# app/ — QTS 애플리케이션 코어

QTS 트레이딩 시스템의 단일 애플리케이션 레이어입니다. 앱형 리팩토링(2026-02-01)으로 `src/runtime` 구조에서 전환되었습니다.

## 디렉터리 구조

| 디렉터리 | 역할 |
|----------|------|
| **main.py** | 단일 엔트리포인트. `python -m app.main` |
| **core/** | 앱 생명주기, 설정(Config_Local, env_loader, schema) |
| **strategy/** | 매매 전략 로직. StrategyEngine, PortfolioEngine, PerformanceEngine, TradingEngine |
| **risk/** | 리스크 계산기, 게이트, 정책 |
| **execution/** | 주문 실행, BrokerEngine, KIS/Kiwoom 클라이언트, Fail-Safe |
| **observer_client/** | Observer 연동 추상화 (stub/uds/ipc) |
| **pipeline/** | ETEDA 파이프라인, run_eteda_loop, MockSnapshotSource |
| **monitoring/** | Central Logger, MetricsCollector, 파일 로그 |

## 실행

```bash
# Local-Only (Mock)
python -m app.main --local-only --verbose

# 프로덕션 (Scalp + KIS)
python -m app.main --scope scalp --broker kis --env production
```

## 의존성

- `ops/` — Safety Layer, Automation (스케줄러, 알림)
- `shared/` — paths, timezone_utils, decorators
- `config/` — default.yaml, production.yaml

## 참고

- [QTS_App_Refactoring_Completion_Report.md](../docs/arch/QTS_App_Refactoring_Completion_Report.md)
- [00_Architecture.md](../docs/arch/00_Architecture.md)
