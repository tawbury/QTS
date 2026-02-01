# Meta: QTS 키움 REST API 구현 및 아키텍처 보완 지침

| Field | Value |
|-------|-------|
| **Project Name** | QTS (Quantitative Trading System) |
| **Document ID** | META-240523-03 |
| **Author** | Code Bridge Expert |
| **Reviewer** | [TBD] |
| **Status** | Approved & Active |
| **Created** | 2024-05-23 15:00 KST |
| **Last Updated** | 2025-02-01 |
| **Related** | base.md, KIS-Architecture-Analysis, Kiwoom-REST-API-Spec |

---

## 1. 페르소나 및 미션 (Persona & Mission)

**QTS 핵심 프레임워크 설계자**로서:

- 기존 KIS 구현 패턴과 **100% 일관성** 유지
- 분석에서 지적된 **미구현 브릿지(Bridge)** 해결
- 완전한 **멀티 브로커 엔진** 완성

---

## 2. 핵심 분석 기반 보완 가이드라인

### A. 브릿지(Bridge) 모듈 최우선 구현

- **문제**: OrderAdapter와 BrokerEngine 사이의 ExecutionIntent ↔ OrderRequest 변환 브릿지가 모호함.
- **해결**: `runtime/execution/intent_to_order_bridge.py`  
  - `intent_to_order_request()`, `order_response_to_execution_response()`  
  - `OrderAdapterToBrokerEngineAdapter`: OrderAdapter를 BrokerEngine.submit_intent 계약으로 감싸는 공통 변환기.

### B. KIS 패턴의 엄격한 준수 (Protocol-Driven)

- **KiwoomOrderClientProtocol** 정의 → 실제 API 호출부와 어댑터 로직 분리
- **kiwoom/payload_mapping.py** → Error→Safety 매핑(FS040~FS042) 정교화

### C. 인증 및 상태 관리 (Stateless Adapter)

- 어댑터는 **Stateless**
- 인증 토큰은 **Runtime 소유 TokenCache**로 관리

---

## 3. 비개발자용 설명 (Bridge Strategy)

| 개념 | 비유 |
|------|------|
| **표준화** | 어떤 증권사 차가 와도 달릴 수 있는 '표준 고속도로'. KIS에서 검증된 Fail-Safe를 키움에도 이식. |
| **브릿지** | 주문 명령(Intent)이 실제 증권사 언어(Request)로 번역되는 통역소. |

---

## 4. 실행 단계별 체크리스트

- [x] BaseBrokerAdapter 하위 KiwoomOrderAdapter 구체화
- [x] kiwoom_payload_mapping.py 생성, KIS 대비 에러 코드 일대일 대응
- [ ] runtime.broker.kiwoom.auth 모듈 구성 및 OAuth 2.0 흐름 설계
- [x] KiwoomOrderClientProtocol 및 MockKiwoomOrderClient 테스트 환경

---

## 5. 핸드오프

**다음 단계**: kiwoom.auth OAuth 2.0 구현 또는 App Key/Secret 보안 정책 확정.
