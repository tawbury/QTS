# TASK_423_PortfolioEngine_Design

**Status**: ⚪ To-Do

**Related Architecture**: Engine Layer (Section 5.5)

**Description**: 
Portfolio Engine은 QTS의 포트폴리오 관리를 담당하는 엔진으로, 전략별 포트폴리오 관리 로직과 수량/비중 조정 알고리즘을 설계한다. 포지션 및 수량 계산, 자산 배분 비중 관리, 포트폴리오 레벨 최적화를 구현한다.

**Constraints**:
- Risk Engine 승인 후 수량 조정 수행
- Config_Local 포트폴리오 파라미터를 우선 적용해야 함
- ETEDA 파이프라인의 Evaluate 단계에서 실행됨
- Data Contract 기반 I/O를 준수해야 함
- 실시간 포지션 상태 반영 필요
- 다중 전략 포트폴리오 통합 관리 능력 필수

**Checklist**:
- [ ] 전략별 포트폴리오 관리 로직 설계 (Scalp/Swing 구분)
- [ ] 수량/비중 조정 알고리즘 설계
- [ ] 포지션 및 수량 계산 로직 설계
- [ ] 자산 배분 비중 관리 메커니즘 설계
- [ ] 포트폴리오 레벨 최적화 알고리즘 설계
- [ ] 실시간 포지션 상태 반영 체계 설계
- [ ] 다중 전략 포트폴리오 통합 관리 설계
- [ ] 리밸런싱 로직 설계
- [ ] 포트폴리오 제약 조건 검증 설계
- [ ] 포트폴리오 상태 보고 포맷 설계
