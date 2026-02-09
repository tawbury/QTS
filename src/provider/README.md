# Provider Layer

## 개요
외부 시스템(증권사 API 등)과의 연동을 담당하는 레이어입니다.

## 지원 브로커
- **KIS (한국투자증권)**: REST API 및 WebSocket 실시간 데이터
- **Kiwoom (키움증권)**: Open API (Windows 전용)

## 주요 기능
- **Authentication**: 오토 토큰 갱신 및 세션 관리
- **Order Management**: 주문 전송, 정정, 취소
- **Market Data**: 실시간 시세 수신 및 과거 데이터 조회
- **Account**: 계좌 잔고 및 보유 종목 조회

## 구조
- **clients/**: 각 증권사별 API 클라이언트 구현체
- **failsafe/**: API 호출 실패 시 재시도 및 폴백 메커니즘
