# Decision Pipeline

## 개요
QTS 시스템의 의사결정 로직을 독립적으로 수행하기 위한 파이프라인입니다.
라이브 매매(ETEDA)와 달리, 데이터 분석, 시뮬레이션, 또는 배치(Batch) 작업에서의 의사결정에 주로 사용됩니다.

## 주요 기능
- **No-Act Execution**: 주문 실행(Act) 단계 없이 Evaluate 및 Decide 단계까지만 수행 가능.
- **Simulation**: 과거 데이터를 기반으로 한 전략 시뮬레이션 지원.
- **Ops Automation**: 운영 자동화 스크립트에서 전략적 판단이 필요할 때 사용.

## 구조
- **pipeline/**: 파이프라인 실행 로직
- **contracts/**: 데이터 계약 및 모델 정의
- **execution_stub/**: 실행 단계의 모의 객체 (Stub)
