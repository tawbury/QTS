# Strategy Layer

## 개요
QTS의 전략 레이어는 다양한 기술적 지표와 시장 데이터를 분석하여 매매 시그널을 생성하는 역할을 합니다.

## 구조
- **engines/**: 실제 매매 로직을 수행하는 엔진 (Strategy, Risk, Portfolio, Performance)
- **arbitration/**: 다중 전략 간의 충돌 해결 및 우선순위 조정
- **registry/**: 전략 등록 및 설정 관리
- **multiplexer/**: 다중 전략 실행 결과 통합

## 주요 컴포넌트
- **Strategy Engine**: 시장 데이터를 입력받아 Buy/Sell/Hold 시그널 생성
- **Strategy Registry**: 실행 가능한 전략들의 메타데이터 및 인스턴스 관리
