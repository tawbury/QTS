
---

# Phase 1.5 종료 선언문

**Phase:** QTS Phase 1.5 – API Exploration  
**Status:** **CLOSED (Gate B Passed)**  
**Closure Date:** 2025-12-28

Phase 1.5는 다음 기준을 모두 충족함에 따라 공식적으로 종료한다.

- 실계좌 기준 KIS OAuth2 인증 API의 **실행 성공** 확인
    
- `.env` 기반 **MODE 분기(VTS / REAL)** 구조가 실 API와 정합함을 실증
    
- QTS BrokerEngine 인터페이스 변경 없이 **포섭 가능성 검증 완료**
    
- Runtime / ops / Execution 영역 **무변경 상태 유지**
    
- 실주문 구조적 미발생 보장
    

Phase 1.5는 구현 단계가 아니라 **관측·검증 단계**이며,  
본 Phase에서 확보된 결과물은 **Phase 2의 입력 자산**으로만 사용된다.

본 선언과 함께 Phase 1.5는 더 이상 확장하지 않는다.

---

# QTS Phase 1.5 자산화 문서

**File:** `QTS/docs/architecture/QTS_Phase1_5_Assetization.md`  
**Version:** v1.0.0  
**Status:** Archived Asset (Input for Phase 2)  
**Scope:** Phase 1.5 Result Canonicalization

---

## 1. 문서 목적

본 문서는 Phase 1.5에서 **실 API 관측을 통해 확정된 사실**을  
Phase 2 설계·구현에서 재사용 가능한 **자산(Asset)** 형태로 고정하기 위해 작성되었다.

본 문서는:

- 규칙을 집행하지 않는다
    
- 구현을 지시하지 않는다
    
- 해석의 여지를 최소화하기 위해 **관측 사실만 기록**한다
    

---

## 2. 관측 환경 요약

- Broker: KIS (Korea Investment & Securities)
    
- 인증 방식: OAuth2 Client Credentials
    
- 테스트 방식: pytest 기반 실 API 호출
    
- 실행 위치: `QTS/tests/api/`
    
- Runtime / ops 코드 수정: 없음
    

---

## 3. 환경 변수 설계 자산 (.env)

### 3.1 MODE 분기 원칙

```env
KIS_MODE=REAL  # or VTS
```

MODE 값에 따라 **URL + 인증 키가 동시에 분기**된다.

---

### 3.2 Base URL 분기

```env
VTS_BASE_URL=...
REAL_BASE_URL=...
```

- 단일 `KIS_BASE_URL`은 사용하지 않음
    
- MODE 기반 분기가 QTS의 표준 설계임이 실증됨
    

---

### 3.3 인증 키 분기 구조

```env
VTS_APP_KEY=...
VTS_APP_SECRET=...

REAL_APP_KEY=...
REAL_APP_SECRET=...
```

- 인증 정보 역시 MODE 기반으로 분리 관리
    
- 단일 키 재사용 구조 ❌
    
- 보안·운영 측면에서 합리적 구조로 판단됨
    

---

## 4. 인증 API 관측 결과

### 4.1 Endpoint

```
POST {BASE_URL}/oauth2/tokenP
```

### 4.2 Request Payload

```json
{
  "grant_type": "client_credentials",
  "appkey": "<APP_KEY>",
  "appsecret": "<APP_SECRET>"
}
```

### 4.3 Response (요약)

- 성공 시:
    
    - `access_token`
        
    - 토큰 타입
        
    - 만료 정보
        
- 실패 시:
    
    - HTTP 400 / 401
        
    - 에러 코드 및 메시지 JSON 반환
        

※ 성공/실패 모두 **정상 관측 결과**로 인정됨

---

## 5. 책임 분리 자산 (Phase 2 입력)

Phase 1.5 관측을 통해 다음 책임 분리가 **구조적으로 타당함**이 확정되었다.

### 5.1 Broker Adapter 책임

- 인증 요청 수행
    
- access_token 수신
    
- MODE 기반 환경 분기 처리
    

### 5.2 Runtime 책임

- access_token 저장 및 만료 관리
    
- 재발급 트리거
    
- 주문/조회 API 호출 시 토큰 주입
    

### 5.3 제외 사항

- access_token을 `.env`에 저장 ❌
    
- Phase 1.5에서 주문 API 실행 ❌
    

---

## 6. Phase 2로의 이관 규칙

본 문서에 기록된 자산은 다음 방식으로만 사용된다.

- Phase 2 기준 문서의 **입력 자료**
    
- BrokerAdapter 설계 시 **사실 기준 레퍼런스**
    
- 테스트 코드 재사용 시 **구조 참고용**
    

본 문서 자체는 **집행 대상이 아니다.**

---

## 7. Phase 1.5 최종 결론

Phase 1.5는 다음 사실을 실증했다.

> **QTS의 기존 환경 분기 및 BrokerEngine 추상 구조는  
> KIS 실 API와 충돌하지 않으며,  
> Phase 2에서 Adapter 구현만으로 연결 가능하다.**

---
