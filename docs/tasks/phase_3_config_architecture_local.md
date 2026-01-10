# Phase 3 Tasks - Config Architecture (Local)

**상태: 🟡 부분 정리 / 설계 완료**

## 개요
Local Bootstrap Config의 설계 범위가 종료(Frozen)되었습니다. 역할·책임·경계 정의와 모든 KEY의 기본값 확정까지 완료되었습니다. 구현만 대기 중인 상태입니다.

## 완료된 태스크 목록

### 3.1 Design & Architecture (완료)
- [x] Local Bootstrap Config 역할·책임·경계 정의
- [x] 전략(SCALP/SWING/FUTURE PORTFOLIO)과의 분리 원칙 확정
- [x] System/Broker/Fail-safe/Strategy Guard 구분 체계 확정
- [x] 모든 Local KEY 의미 정의
- [x] 전략 개입 가능/불가 판정 기준 확정
- [x] 권장 기본값(Recommended Default) 확정
- [x] Kill Switch/Fail-safe/Exposure/Market Guard 구조 고정
- [x] Portfolio 확장 대응 네이밍 규칙(`*_PORTFOLIO`) 사전 정의

## 미구현 태스크 목록 (Implementation Scope)

### 3.2 File Format & Loading (대기)
- [ ] Local Bootstrap Config 파일 포맷 선택
  - [ ] YAML/JSON/Excel 포맷 결정
  - [ ] Runtime 변환 로직 설계
- [ ] Runtime 로딩 시점 확정
- [ ] Loader 결합 위치 설계
- [ ] Google Sheet Config와의 병합/우선순위 처리 로직 구현

### 3.3 Secrets & Environment Integration (대기)
- [ ] Secrets/Env/Override의 코드 레벨 처리 방식 구현
- [ ] 환경변수 우선순위 처리 로직
- [ ] 보안 정보 분리 저장 방식

### 3.4 Validation & Fail-safe Integration (대기)
- [ ] Validation 로직 구현
- [ ] Fail-safe 연동 로직 구현
- [ ] Config 충돌 감지 및 처리 메커니즘

## 다음 Phase 연결 포인트
- **Phase 4. Runtime Integration & Validation**으로 이관 필요
- Engine Layer와의 Config 전달 체계 확정 후 구현 시작 가능
- 실제 구현은 Phase 4에서 진행

## 비고
- **설계는 종료되었으며, 구현만 대기 중**
- 파일 포맷과 로딩 방식 결정 필요
- 다른 Phase 구현 진행에 따라 우선순위 조정 가능
