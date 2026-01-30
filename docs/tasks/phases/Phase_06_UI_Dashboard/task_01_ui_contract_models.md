# Phase 6 — UI/Dashboard: UI Contract Models

## 목표

- UI는 Raw/Calc 데이터를 직접 읽지 않고 UI Contract만으로 렌더링한다(Zero-Formula 원칙)

## 근거

- `docs/arch/06_UI_Architecture.md`

## 작업

- [ ] UI Contract 스키마 정의/고정
  - [ ] Pipeline 종료 시 생성되는 UI Contract의 필드/버전 정책 정의
- [ ] 코드 품질 개선(필수)
  - [ ] Contract가 산발적으로 생성/변경되는 구조를 방지(단일 빌더/팩토리)

## 완료 조건

- [ ] UI Contract 구조가 문서로 고정되어 있고, 변경 시 버전 정책이 있다.
