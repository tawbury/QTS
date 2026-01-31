# Phase 6 — UI Dashboard: Zero-Formula UI Foundation

## 목표

- Zero-Formula UI 기반 구조 구축
- R_Dash 시각화 컴포넌트 기반 마련

## 근거

- 현재 UI Layer가 완전히 누락되어 있음
- 아키텍처 문서의 Zero-Formula UI 원칙 구현 필요
- Dashboard 및 모니터링 인터페이스 부재

## 작업

- [x] UI Layer 기본 구조 구축
  - [x] `src/runtime/ui/` 폴더 구조 설계 (UI Layer 단일 진입점)
  - [x] Zero-Formula UI 기본 클래스 설계 (`BlockRenderer` Protocol)
- [x] R_Dash 컴포넌트 기반 마련
  - [x] `src/runtime/ui/r_dash/` 모듈 구조 설계 (Writer + Renderers re-export)
  - [x] Data Contract 기반 시각화 인터페이스 정의 (Contract → 행 데이터, 값만)
- [x] Dashboard Block Architecture 설계
  - [x] 포트폴리오·성과·리스크·파이프라인·메타 블록 → 렌더러·R_Dash 영역 매핑
  - [x] 실시간 데이터 업데이트 채널 설계 (R_Dash_Update_Policy)
- [x] UI Contract 정의
  - [x] Engine → UI 데이터 전송 Contract 명세 (UI_Contract_Schema.md)
  - [x] Zero-Formula 원칙 준수 확인 (Zero_Formula_UI_Foundation.md §5)

## 완료 조건

- [x] UI Layer 기본 구조가 구축됨
- [x] Zero-Formula UI 원칙이 적용됨
- [x] R_Dash 시각화 기반이 마련됨

## 산출물

- **코드:** `zero_formula_base.py` (BlockRenderer Protocol), `r_dash/__init__.py` (R_Dash 컴포넌트 네임스페이스)
- **문서:** `Zero_Formula_UI_Foundation.md` — UI Layer 구조, R_Dash 컴포넌트, Dashboard Block 매핑, 업데이트 채널, Zero-Formula 준수 체크리스트
