# Risk Management Layer

## 개요
주문 실행 전 리스크를 분석하고 시스템 안정성을 보장하기 위한 레이어입니다.

## 주요 기능
- **Pre-Trade Risk Check**: 주문 전 한도 초과, 금지 종목 여부 확인
- **Dynamic Limit**: 시장 변동성에 따른 동적 한도 조정
- **Exposure Management**: 총 노출 금액 및 레버리지 관리

## 구조
- **calculators/**: 리스크 지표 계산 로직
- **gates/**: 주문 통과 여부를 결정하는 게이트키퍼
- **policies/**: 리스크 관리 정책 정의
