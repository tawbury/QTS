# TASK_421_TradingEngine_Redesign

**Status**: ⚪ To-Do

**Related Architecture**: Engine Layer (Section 5.3)

**Description**: 
Trading Engine은 QTS의 "실행자(Executor)"로서, ScalpEngine/SwingEngine에서 전달된 의사결정을 받아 실제 주문으로 변환하여 브로커에 전달하는 엔진을 재설계한다. 전략별 주문 실행 로직, 브로커 API 연동 인터페이스, Fail-Safe 조건 충족 시 주문 중단(Lockdown) 기능을 구현한다.

**Constraints**:
- ScalpEngine/SwingEngine 신호를 수신해야 함
- Risk Engine 승인 후에만 주문 실행 가능
- Portfolio Engine 수량 조정을 반영해야 함
- ETEDA 파이프라인의 Act 단계에서 실행됨
- "생각"하지 않고 오직 "실행"만 수행해야 함
- 브로커별 API 차이를 추상화해야 함

**Checklist**:
- [ ] ScalpEngine/SwingEngine 신호 수신 체계 설계
- [ ] 전략별 주문 실행 로직 설계 (Scalp/Swing 구분)
- [ ] 브로커 API 연동 인터페이스 설계 (추상화 계층)
- [ ] 주문량 계산 알고리즘 설계
- [ ] 주문 유형(지정가/시장가 등) 적용 로직 설계
- [ ] 브로커 API 호출 및 응답 처리 설계
- [ ] T_Ledger 기록 자동화 설계
- [ ] 실패 시 재시도 로직 설계
- [ ] Fail-Safe 조건 충족 시 주문 중단(Lockdown) 설계
- [ ] 주문 요청/체결 결과 출력 포맷 설계
