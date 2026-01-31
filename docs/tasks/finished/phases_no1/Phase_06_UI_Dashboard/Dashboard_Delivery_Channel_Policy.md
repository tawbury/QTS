# 대시보드 제공 채널 및 보안 정책

**관련:** task_03_dashboard_delivery_channel.md, docs/arch/06_UI_Architecture.md §9

---

## 1. UI 제공 방식 (최소 구현 경로)

### 1.1 확정: Sheets-only

- **최소 구현 경로:** **Google Sheets(R_Dash)만** 사용한다.
- 운영자 대시보드 최소 기능은 다음으로 충족한다:
  - UI Contract 생성 (UIContractBuilder)
  - R_Dash 시트 갱신 (R_DashWriter + Renderers)
  - 운영자는 해당 스프레드시트에 접근해 계좌/리스크/파이프라인 상태를 확인한다.
- **Web(Streamlit/FastAPI/React 등)** 은 **향후 확장**으로 둔다 (06_UI_Architecture §9.1 웹 UI 확장 참조).

### 1.2 향후 Web 추가 시

- Web 채널을 추가할 때는 별도 태스크로 다음을 결정한다:
  - 프레임워크 선택 (Streamlit vs FastAPI+React vs Dash)
  - WebSocket/폴링 등 데이터 전달 방식
  - 기본 인증 방식(아래 §2.2)

---

## 2. 보안/접근 제어 — 최소 인증 정책

### 2.1 현재(Sheets-only)

- **시트 접근:** Google 계정/서비스 계정으로만 제어한다.
  - 스프레드시트 ID(`SPREADSHEET_ID`/`GOOGLE_SHEET_KEY`)와 인증 파일(`CREDENTIALS_PATH`/`GOOGLE_CREDENTIALS_FILE`)은 설정/환경변수로만 전달한다.
  - 시트 공유/권한은 Google Drive/Sheets 설정에서 관리한다.
- **대시보드 조회:** 시트에 접근 권한이 있는 운영자만 R_Dash를 볼 수 있다. 별도 애플리케이션 레벨 로그인은 두지 않는다.

### 2.2 향후 Web 채널 추가 시

- **기본 인증(Basic Auth 또는 API 키)** 을 적용한다.
- 운영자만 접근 가능하도록 최소 수준의 인증 정책을 수립한 뒤 구현한다 (예: 환경변수 기반 API 키, 또는 Basic Auth).

---

## 3. 운영 환경 — 디버그/민감정보 노출 점검

### 3.1 금지 사항

- **로그/표준 출력에 다음을 출력하지 않는다:**
  - 비밀번호, API 시크릿, 토큰(access/refresh), 인증 파일 내용
  - 서비스 계정 JSON 전체
- **운영 환경에서** 임시 디버그용 `print()` 또는 상세 config 덤프를 남기지 않는다.

### 3.2 허용

- **spreadsheet_id** 는 URL에 포함되는 식별자이므로 로그에 기록해도 된다 (민감정보로 간주하지 않음).
- **credentials_path** (파일 경로)는 로그에 남기지 않는 것을 권장한다. 필요 시 “credentials loaded” 수준만 기록한다.

### 3.3 점검 체크리스트

- [ ] UI/대시보드·파이프라인·config 로드 코드에 `print(..., credential|token|password|secret)` 없음
- [ ] `logger.info/debug` 에 토큰·비밀번호·인증 파일 내용 미포함
- [ ] 운영 빌드/실행 시 디버그 전용 출력 비활성화 또는 제거

---

## 4. 완료 조건 정리

- UI 제공 방식: **Sheets-only** 로 확정됨.
- 보안/접근: **Sheets = Google 접근 제어**, **Web = 향후 기본 인증 정책** 수립됨.
- 코드 품질: **민감정보 노출 금지·점검 체크리스트** 문서화됨.
