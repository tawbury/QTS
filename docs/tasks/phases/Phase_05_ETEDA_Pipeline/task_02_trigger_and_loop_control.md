# Phase 5 — ETEDA Pipeline: Trigger & Loop Control

## 목표

- 파이프라인을 실행 루프/스케줄러와 안전하게 연결(ETEDA 원칙을 위반하지 않도록)

## 근거

- `docs/arch/03_Pipeline_ETEDA_Architecture.md`

## 작업

- [ ] 실행 루프 정책 확정
  - [ ] interval 기반 vs event 기반 트리거의 우선순위/병행 규칙
  - [ ] 루프 중단/재시작/에러 백오프 규칙
- [ ] 코드 품질 개선(필수)
  - [ ] 루프/트리거 코드가 ETEDA 단계 책임을 침범하지 않도록 정리

## 완료 조건

- [ ] 반복 실행 중 장애가 발생해도 안전하게 중단/복구할 수 있다.
