# Phase 9 — Ops/Automation: Backup/Retention Verification

## 목표

- 이미 존재하는 백업/보관 정책 코드가 운영 관점에서 유효한지 검증하고 부족한 부분을 채운다.

## 근거

- `docs/arch/09_Ops_Automation_Architecture.md`
- 코드:
  - `src/ops/backup/`
  - `src/ops/retention/`

## 작업

- [x] 백업 산출물 검증
  - [x] manifest/checksum/restore 절차 점검: `src/ops/backup/README.md` (Manifest 필드, Checksum, Restore 절차)
- [x] 보관 정책(retention) 적용 범위 점검
  - [x] `src/ops/retention/README.md`: raw/pattern/decision 적용 범위 및 정책 필드 명시
- [x] 코드 품질 개선(필수)
  - [x] 실패/예외 처리 시 로깅/리턴 규칙 통일: retention cleaner unlink 실패 시 `logging.warning`; maintenance_runner backup 예외 시 `_log.warning` + 구조화 반환

## 완료 조건

- [x] 운영자가 복구 절차를 수행할 수 있을 정도로 문서/코드가 준비되어 있다. (`ops/backup/README.md` Restore 절차, manifest/checksum 검증)
