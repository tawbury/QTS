# config/ — QTS 설정

환경별 YAML 설정 및 로컬 설정 파일을 관리합니다.

## 파일 구조

| 파일 | 용도 |
|------|------|
| **default.yaml** | 개발/기본 설정. observer type=stub, broker mode=paper |
| **production.yaml** | 프로덕션 설정. observer type=uds, broker mode=live |
| **local/** | (선택) config_local.json 등 로컬 전용 설정 |

## YAML 구조

```yaml
observer:
  type: "stub" | "uds" | "ipc"
  endpoint: null | "unix:///var/run/observer.sock"

broker:
  type: "kiwoom" | "kis"
  mode: "paper" | "live"
```

## 환경 변수 오버라이드

- `QTS_ENV`: `development` | `production` (config 파일 선택)
- `OBSERVER_ENDPOINT`: Observer 연결 경로
- `BROKER_TYPE`, `LOG_LEVEL`, `STRATEGY_SCOPE` 등

## 참고

- Config 로딩: `app/core/config/config_loader.py`
- .env: Broker API 키, Google Sheets 등 (config/ 밖 프로젝트 루트)
