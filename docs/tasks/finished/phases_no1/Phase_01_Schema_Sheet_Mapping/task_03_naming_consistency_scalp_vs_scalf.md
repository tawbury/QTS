# Phase 1 — Naming Consistency: Scalp vs Scalf

## 목표

- Config/Repository/문서에서 혼재된 용어(`Scalp` vs `Scalf`)를 정리하여 유지보수 리스크를 줄인다.

## 근거

- 문서: `docs/arch/13_Config_3분할_Architecture.md`
- 코드:
  - `src/runtime/data/repositories/config_scalp_repository.py`
  - `src/runtime/config/sheet_config.py`
- 명칭·이행 상세: [Naming_Scalp_vs_Scalf.md](./Naming_Scalp_vs_Scalf.md)

## 작업

- [x] 표준 용어 확정
  - [x] 문서/코드/시트명에서 표준 **Scalp** (Config_Scalp) 사용 → [Naming_Scalp_vs_Scalf.md](./Naming_Scalp_vs_Scalf.md) §1
- [x] 코드 품질 개선(필수)
  - [x] 표준 용어에 맞추어 클래스/파일/심볼 정리 → config_scalf 제거, config_scalp_repository·ConfigScalpRepository·Config_Scalp 적용
  - [x] 변경 영향 범위(Imports/테스트/문서/시트명) 목록화 → §2, §3

## 완료 조건

- [x] 문서와 코드의 전략 스코프 명칭이 일치한다. → Scalp / Config_Scalp 통일
- [x] 기존 명칭이 남아있다면 “호환 레이어” 또는 “이행 계획”이 문서화되어 있다. → §3 (시트 탭 이름 변경 안내)
