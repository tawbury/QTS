# Observer Client

## 개요
Observer 시스템으로부터 실시간 시장 데이터를 수신하는 클라이언트 모듈입니다.

## 통신 방식
- **Stub**: 개발 및 테스트용 모의 데이터 생성기
- **UDS (Unix Domain Socket)**: 로컬 고속 통신 (Linux/Docker 환경)
- **IPC (Inter-Process Communication)**: 프로세스 간 직접 통신

## 주요 기능
- **Data Ingestion**: 호가, 체결가 등 실시간 데이터 수신
- **Heartbeat**: Observer 상태 모니터링 및 연결 유지
- **Deserialization**: 수신된 바이너리/JSON 데이터를 내부 객체로 변환
