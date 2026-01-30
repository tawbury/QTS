# Phase 1 — Naming Consistency: Scalp vs Scalf

## 목표

- Config/Repository/문서에서 혼재된 용어(`Scalp` vs `Scalf`)를 정리하여 유지보수 리스크를 줄인다.

## 근거

- 문서: `docs/arch/13_Config_3분할_Architecture.md`
- 코드:
  - `src/runtime/data/repositories/config_scalf_repository.py`
  - `src/runtime/config/sheet_config.py`

## 작업

- [ ] 표준 용어 확정
  - [ ] 문서/코드/시트명에서 어떤 표기를 표준으로 사용할지 결정
- [ ] 코드 품질 개선(필수)
  - [ ] 표준 용어에 맞추어 클래스/파일/심볼 정리(필요 시 점진적 마이그레이션)
  - [ ] 변경 영향 범위(Imports/테스트/문서/시트명)를 목록화

## 완료 조건

- [ ] 문서와 코드의 전략 스코프 명칭이 일치한다.
- [ ] 기존 명칭이 남아있다면 “호환 레이어” 또는 “이행 계획”이 문서화되어 있다.
