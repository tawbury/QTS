
---

# QTS Phase 2 Guide

**Broker Adapter & Runtime Integration 기준 문서 (초석 문서)**

- **File:** `QTS/docs/architecture/QTS_Phase2_Guide.md`
    
- **Version:** v1.0.0
    
- **Status:** **Enforcing (Phase 2 기준 문서)**
    
- **Scope:** QTS Phase 2 (Broker Adapter & Runtime Integration)
    
- **Input Asset:** `QTS_Phase1_5_Assetization.md`
    
- **Last Updated:** 2025-12-28
    

---

## 1. 문서의 목적

본 문서는 Phase 2에서 수행될 **Broker Adapter 구현 및 Runtime 연동**의  
범위, 책임 경계, 안전 제약을 사전에 고정하기 위해 작성되었다.

Phase 2의 목적은 다음 한 문장으로 요약된다.

> **“Phase 1.5에서 자산화된 관측 결과를 입력으로 삼아,  
> Broker Adapter와 Runtime을 연결하되,  
> Execution 및 ops의 책임을 침범하지 않는다.”**

본 문서는 Phase 2 전 기간 동안  
**Single Source of Truth**로 사용된다.

---

## 2. Phase 2의 위치 정의

- Phase 1: 설계 및 스켈레톤 고정
    
- Phase 1.5: 실 API 관측 및 자산화
    
- **Phase 2: Adapter 및 Runtime 연결 구현**
    

Phase 2는 최초의 **연결 구현 단계**이나,  
아직 자동화·전략·실행 최적화 단계는 아니다.

---

## 3. Phase 2의 핵심 산출물

Phase 2에서 확보해야 할 산출물은 다음과 같다.

1. KIS Broker Adapter
    
    - 인증 요청
        
    - access_token 수신
        
    - MODE 기반 환경 분기
        
2. Runtime Token Cache
    
    - 토큰 저장
        
    - 만료 관리
        
    - 재발급 트리거
        
3. Adapter ↔ Runtime 연동 테스트
    

---

## 4. Phase 2 범위 정의

### 4.1 포함 범위

- Broker Adapter 구현 (KIS 기준)
    
- OAuth2 인증 로직 구현
    
- Runtime 토큰 캐시 모듈 구현
    
- MODE(VTS / REAL) 기반 분기 로직 고정
    
- Adapter ↔ Runtime 연동 테스트
    

---

### 4.2 제외 범위 (강제)

아래 항목은 Phase 2에서 수행하지 않는다.

- 전략 로직 구현
    
- 자동 매매 루프
    
- 주문 최적화 및 분할 체결
    
- 리스크 엔진 연동
    
- ops 자동화 확장
    
- 멀티 브로커 확장
    

해당 항목은 Phase 3 이후의 책임이다.

---

## 5. 책임 분리 (고정 규칙)

### 5.1 Broker Adapter 책임

- `.env` 기반 MODE 분기
    
- 인증 요청 수행 (`/oauth2/tokenP`)
    
- access_token 수신
    
- Runtime으로 토큰 전달
    

Adapter는 **무상태(stateless)** 로 유지된다.

---

### 5.2 Runtime 책임

- access_token 저장
    
- 만료 시간 추적
    
- 재발급 조건 판단
    
- API 호출 시 토큰 주입
    

Runtime은 **상태 관리자(stateful)** 이다.

---

### 5.3 금지 사항

- Adapter에서 토큰 캐시 보유
    
- Runtime에서 인증 파라미터 관리
    

---

## 6. Phase 1.5 자산 사용 규칙

Phase 2는 다음 자산을 참조 입력으로 사용한다.

- `QTS_Phase1_5_Assetization.md`
    
- `.env` 환경 분기 구조
    
- Phase 1 Runtime 자산
    

해당 자산은 **수정 대상이 아니다.**

---

## 7. Phase 2 폴더 구조 기준

Phase 2에서는 아래 폴더 구조를 최초로 생성하고 고정한다.

본 구조는 이후 Phase에서 확장될 수 있으나,  
책임 경계는 유지되어야 한다.

```
QTS/
├─ src/
│  └─ runtime/
│     ├─ broker/
│     │  ├─ __init__.py
│     │  ├─ base.py              # BrokerAdapter 인터페이스
│     │  └─ kis/
│     │     ├─ __init__.py
│     │     ├─ adapter.py        # KIS BrokerAdapter 구현
│     │     └─ auth.py           # OAuth2 인증 로직
│     │
│     └─ auth/
│        ├─ __init__.py
│        └─ token_cache.py       # Runtime Token Cache
│
├─ tests/
│  └─ runtime/
│     └─ broker/
│        ├─ test_kis_auth.py
│        ├─ test_token_cache.py
│        └─ test_kis_adapter_integration.py
```

---

## 7.1 구조 설계 원칙

- `broker/`
    
    - 외부 시스템(KIS 등)과의 접점
        
    - 인증 요청 및 API 호출 책임
        
- `auth/`
    
    - Runtime 내부 상태 관리 전용
        
    - 토큰 저장, 만료, 재발급 판단
        

Adapter는 무상태,  
Runtime은 상태 관리자로 유지된다.

---

## 7.2 Phase 2에서 생성하지 않는 구조

다음 구조는 Phase 2에서 생성하지 않는다.

- `strategy/`
    
- `execution/`
    
- `risk/`
    
- `ops/automation/`
    

---

## 8. 테스트 전략

### 8.1 테스트 위치

```
QTS/tests/runtime/broker/
```

- Adapter 단위 테스트
    
- Runtime 연동 테스트
    
- Phase 1.5 테스트 자산 참조 가능
    

---

### 8.2 테스트 원칙

- 인증 성공 및 실패 모두 테스트 케이스로 인정
    
- 실주문은 기본적으로 제외
    
- 토큰 만료 및 재발급 시나리오 포함
    

---

## 9. Phase 2 종료 기준 (Gate C)

Phase 2는 다음 조건을 모두 만족할 경우 종료한다.

1. Broker Adapter가 MODE 분기를 정확히 처리함
    
2. 인증 토큰이 Runtime에 저장됨
    
3. 토큰 만료 시 재발급 흐름이 검증됨
    
4. Adapter ↔ Runtime 인터페이스가 고정됨
    
5. Phase 1 자산이 변경되지 않았음이 보장됨
    

---

## 10. Phase 3 이관 규칙

Phase 2 종료 후:

- Phase 3에서 주문 API 확장 및 전략 연동 진행
    
- Phase 2 코드는 확장 대상이지만 수정 대상은 아니다
    

---

## 11. 최종 선언

> **Phase 2는 연결의 단계다.  
> Phase 2는 자동화의 단계가 아니다.  
> Phase 2는 Phase 3 실패를 예방하기 위해 존재한다.**

---
