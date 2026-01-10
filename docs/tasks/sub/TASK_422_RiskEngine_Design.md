# TASK_422_RiskEngine_Design

**Status**: ⚪ To-Do

**Related Architecture**: Engine Layer (Section 5.4)

**Description**: 
Risk Engine은 QTS의 "안전 승인(Safety Approver)" 역할을 수행하는 엔진으로, 전략 신호가 있어도 리스크에서 허용하지 않으면 주문이 실행되지 않도록 하는 안전장치를 설계한다. 전략별 리스크 평가 체계, 포지션 노출도 계산 로직, Kill Switch 연동 방식을 구현한다.

**Constraints**:
- 전략 신호에 대한 사전 승인/거부 권한 보유
- Config_Local 리스크 파라미터를 우선 적용해야 함
- ETEDA 파이프라인의 Evaluate 단계에서 Risk Engine → Trading Engine 순서로 실행
- Data Contract 기반 I/O를 준수해야 함
- 실시간 리스크 평가 능력 필수
- Safety & Risk Core와 연동 필요

**Checklist**:
- [ ] 전략별 리스크 평가 체계 설계 (Scalp/Swing 구분)
- [ ] 포지션 노출도 실시간 계산 로직 설계
- [ ] 현재 계좌 위험도 계산 알고리즘 설계
- [ ] 공매도 가능 여부 판단 로직 (브로커 옵션 기반)
- [ ] 최대 주문량 제한 메커니즘 설계
- [ ] 일손실/일익절 조건 감시 로직 설계
- [ ] 전략별 MaxDrawdown 제한 감지 설계
- [ ] Kill Switch 연동 방식 설계
- [ ] 리스크 승인/거부 출력 포맷 설계 (risk_approval, allowed_qty, risk_reason)
- [ ] 스트레스 시나리오 테스트 케이스 설계
