# Phase 0 — Observer Infrastructure (Separated)

## 목표

- Observer가 본 QTS 프로젝트 범위에서 분리(↗️)되었음을 기준으로
  - 본 저장소에서 유지해야 하는 경계/연동 지점을 명확히 한다.

## 근거

- `docs/Roadmap.md`
- `docs/arch/09_Ops_Automation_Architecture.md`

## 작업

- [ ] Observer 분리 이후 경계 정의
  - [ ] QTS에서 Observer 산출물을 소비하는 지점이 있는지 확인(있다면 계약 문서화)
  - [ ] 본 저장소에서 Observer 관련 의존성이 남아있다면 제거/정리
- [ ] 코드 품질 개선(필수)
  - [ ] Observer 관련 dead code/import/unused configuration 정리

## 완료 조건

- [ ] QTS 저장소에서 Observer 경계가 문서로 명확히 정의되어 있다.
