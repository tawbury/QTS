# docker/ — Docker 배포 설정

QTS 애플리케이션의 Docker 빌드 및 실행을 위한 설정 파일입니다.

## 파일 목록

*   **Dockerfile**: QTS 애플리케이션 이미지를 빌드하기 위한 명세. Python 3.11 Slim 기반.
*   **docker-compose.test.yml**: 로컬 테스트 및 개발 환경을 위한 Docker Compose 설정. Google Sheets Mocking 등을 포함할 수 있음.
*   **.dockerignore**: Docker 빌드 컨텍스트에서 제외할 파일 목록.

## 실행 방법

Dockerfile을 사용하여 이미지를 빌드하고 실행하거나, Compose를 통해 서비스를 실행할 수 있습니다.

```bash
# 이미지 빌드
docker build -t qts-app -f docker/Dockerfile .

# Compose 실행
docker-compose -f docker/docker-compose.test.yml up -d
```
