# TASK_424_PerformanceEngine_Design

**Status**: ⚪ To-Do

**Related Architecture**: Engine Layer (Section 5.6)

**Description**: 
Performance Engine은 QTS의 성과 분석을 담당하는 엔진으로, 전략별 성과 분석 체계와 실시간 손익 계산 로직을 설계한다. 거래 성과 추적, 수익률 계산, 리스크 조정 성과 분석, 실시간 손익 모니터링을 구현한다.

**Constraints**:
- T_Ledger 및 History Sheet 데이터를 활용해야 함
- Config_Local 성과 파라미터를 우선 적용해야 함
- Data Contract 기반 I/O를 준수해야 함
- 실시간 성과 계산 능력 필수
- Dashboard/Visualization Layer에 데이터 제공 필요
- 다양한 성과 지표 표준화 필요

**Checklist**:
- [ ] 전략별 성과 분석 체계 설계 (Scalp/Swing 구분)
- [ ] 실시간 손익 계산 로직 설계
- [ ] 수익률 계산 알고리즘 설계 (단기/장기/누적)
- [ ] 리스크 조정 성과 분석 (Sharpe Ratio, Sortino Ratio 등) 설계
- [ ] 거래 성과 추적 메커니즘 설계
- [ ] 최대 손실(Max Drawdown) 계산 설계
- [ ] 변동성 지표 계산 설계
- [ ] 성과 보고서 생성 로직 설계
- [ ] Dashboard 데이터 전송 포맷 설계
- [ ] 성과 데이터 검증 및 정확성 테스트 설계
