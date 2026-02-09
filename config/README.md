# config/ — QTS 설정

환경별 YAML 설정 및 환경 변수 파일을 관리합니다.

## 파일 구조

| 파일 | 용도 |
|------|------|
| **default.yaml** | 기본 설정 파일. 로컬 개발 및 기본값 정의. |
| **production.yaml** | 프로덕션 환경 설정 파일. |
| **.env.example** | 환경 변수 예시 파일. |
| **.env** | (생성 필요) 실제 환경 변수 및 시크릿 키 저장. Git에 포함되지 않음. |

## 주요 설정 항목

*   **observer**: 데이터 수신 방식 (stub, uds, ipc 등)
*   **broker**: 브로커 설정 (kis, kiwoom) 및 모드 (paper, live)
*   **strategy**: 전략 파라미터 및 실행 주기

## 사용법

1. `.env.example`을 복사하여 `.env` 생성: `cp config/.env.example config/.env`
2. `.env` 파일에 필요한 API 키 및 경로 설정.
3. 애플리케이션 실행 시 `QTS_ENV` 환경 변수에 따라 `default.yaml` 또는 `production.yaml`이 로드됨.
