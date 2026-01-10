# TASK_432_EngineToEngine_Communication_Interface_Design

**Status**: ⚪ To-Do

**Related Architecture**: Engine Layer, ETEDA Pipeline (Section 6)

**Description**: 
Engine 간 통신 인터페이스 설계는 ScalpEngine/SwingEngine, Risk Engine, Trading Engine, Portfolio Engine, Performance Engine 간의 데이터 흐름과 통신 규약을 정의한다. Strategy → Risk 신호 전달, Risk → Trading 승인/거부 체계, Portfolio → Trading 수량 조정 등 엔진 간 상호작용을 표준화한다.

**Constraints**:
- ETEDA 파이프라인의 단계별 실행 순서를 준수해야 함
- Data Contract 기반 표준화된 인터페이스 사용해야 함
- 엔진 간 직접 호출 대신 Pipeline을 통한 간접 통신 선호
- 실시간 통신 성능 보장 필요
- 통신 실패 시 롤백/재시도 메커니즘 필요
- 비동기 통신 지원 필요

**Checklist**:
- [ ] Strategy → Risk 신호 전달 인터페이스 설계
- [ ] Risk → Trading 승인/거부 체계 설계
- [ ] Portfolio → Trading 수량 조정 인터페이스 설계
- [ ] Performance → Dashboard 성과 데이터 전송 설계
- [ ] Engine 간 통신 프로토콜 표준화 설계
- [ ] 비동기 메시지 큐 시스템 설계
- [ ] 통신 데이터 포맷 정의 (JSON/Protocol Buffers 등)
- [ ] 통신 실패 처리 및 재시도 로직 설계
- [ ] 엔진 상태 동기화 메커니즘 설계
- [ ] Engine 간 통신 테스트 프레임워크 설계
