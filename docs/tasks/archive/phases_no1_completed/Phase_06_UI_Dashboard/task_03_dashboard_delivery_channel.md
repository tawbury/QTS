# Phase 6 — UI/Dashboard: Delivery Channel (Web/Sheets)

## 목표

- 운영자가 접근할 수 있는 대시보드 제공 채널을 확정하고 최소 제공 경로를 만든다.

## 근거

- `docs/tasks/backups/Phase_06_Dashboard/task.md`

## 작업

- [x] UI 제공 방식 확정
  - [x] Sheets-only vs Web(예: Streamlit/FastAPI) 중 최소 구현 경로 확정 → **Sheets-only**
- [x] 보안/접근 제어
  - [x] 최소 인증(기본 auth) 정책 수립
- [x] 코드 품질 개선(필수)
  - [x] 운영 환경에서 임시 디버그 출력/민감정보 노출 경로 점검

## 완료 조건

- [x] 운영자 대시보드 최소 기능이 제공된다.

## 산출물

- **정책 문서:** `Dashboard_Delivery_Channel_Policy.md`
  - §1 UI 제공 방식: Sheets-only 최소 경로 확정, Web은 향후 확장
  - §2 보안/접근: Sheets = Google 접근 제어, Web 추가 시 기본 인증 정책
  - §3 운영 환경: 민감정보(토큰·비밀번호·인증 내용) 로그/출력 금지, 점검 체크리스트
- **점검 결과:** `src/runtime` 내 `print()` 없음; UI/대시보드 코드에 credential/token 로그 없음
