# shared/ — 공용 유틸리티

QTS 전역에서 사용하는 공용 모듈입니다. `app/`, `ops/` 등에서 import합니다.

## 모듈

| 모듈 | 용도 |
|------|------|
| **paths** | `project_root()`, 경로 해석 |
| **timezone_utils** | `now_kst()`, `to_kst()`, `KST` |
| **decorators** | 공통 데코레이터 |
| **utils** | 기타 유틸 함수 |

## 사용 예

```python
from shared.paths import project_root
from shared.timezone_utils import now_kst, KST
```

## 의존성

- 표준 라이브러리만 사용 (외부 패키지 최소화)
- `app/`, `ops/`에 의존하지 않음
