# TASK_411_ScalpEngine_Design

**Status**: ⚪ To-Do

**Related Architecture**: Engine Layer (Section 5.1)

**Description**: 
ScalpEngine은 QTS의 "단기 판단자(Short-term Decision Maker)"로서, 단기·고회전 매매를 전제로 기술적 지표와 신호 기반의 빠른 진입/청산 판단을 수행하는 엔진을 설계한다. RSI, MACD, 볼린저 등 기술적 지표 기반 신호 계산, 단기 변동성 기반 진입/청산 시그널 생성, 시간 기반 청산 로직, 단건 손실 제어 메커니즘을 구현한다.

**Constraints**:
- Config_Scalp 파라미터를 기반으로 동작해야 함
- Config_Local 보호 규칙을 우선 적용해야 함
- ETEDA 파이프라인의 Evaluate 단계에서 실행됨
- Data Contract 기반 I/O를 준수해야 함
- 단기·고회전 특성을 고려한 성능 최적화 필요

**Checklist**:
- [ ] 기술적 지표 계산 모듈 설계 (RSI, MACD, 볼린저 등)
- [ ] 단기 변동성 기반 신호 생성 로직 설계
- [ ] 시간 기반 청산 (타임아웃) 메커니즘 설계
- [ ] 단건 손실 제어 및 변동성 제한 로직 설계
- [ ] 최대 포지션 수 및 단건 비중 제한 설계
- [ ] Config_Scalp 파라미터 반영 체계 설계
- [ ] 실시간 데이터 수신 및 처리 파이프라인 설계
- [ ] 신호 출력 포맷 (scalp_signal, recommended_qty, confidence, reason) 설계
- [ ] 단위 테스트 케이스 설계
- [ ] 성능 벤치마크 기준 마련
