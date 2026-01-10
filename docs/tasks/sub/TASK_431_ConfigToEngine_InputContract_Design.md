# TASK_431_ConfigToEngine_InputContract_Design

**Status**: ⚪ To-Do

**Related Architecture**: Engine Layer, Config Architecture (Section 3.1.3)

**Description**: 
Config → Engine 입력 계약 설계는 Unified Config가 각 엔진에 전달되는 방식과 규칙을 정의한다. Unified Config 전달 체계, Config_Local 보호 규칙 적용, 전략별 Config 분리 처리를 구현하여 모든 엔진이 일관된 설정 기반으로 동작하도록 보장한다.

**Constraints**:
- Unified Config Resolution Flow를 준수해야 함 (Local + Strategy + Secrets)
- Config_Local은 보호 영역으로 전략 시트가 override 할 수 없음
- ScalpEngine은 Config_Local + Config_Scalp + Secrets를 입력으로 받음
- SwingEngine은 Config_Local + Config_Swing + Secrets를 입력으로 받음
- Secrets가 최우선 적용되어야 함
- Data Contract 표준을 준수해야 함

**Checklist**:
- [ ] Unified Config 전달 체계 설계 (엔진별 설정 주입)
- [ ] Config_Local 보호 규칙 적용 메커니즘 설계
- [ ] 전략별 Config 분리 처리 로직 설계 (Scalp/Swing)
- [ ] Config Parser와 Engine 연동 인터페이스 설계
- [ ] 설정 충돌 감지 및 해결 로직 설계
- [ ] 동적 Config 변경 반영 메커니즘 설계
- [ ] Config 유효성 검증 체계 설계
- [ ] Engine별 Config 요구사항 명세 설계
- [ ] Config 전달 성능 최적화 설계
- [ ] Config 테스트 데이터 및 검증 케이스 설계
