
---

# QTS Project Tree Definition

**(Maintenance Reference Document)**

## 1. Project Root

```
QTS/
```

### 목적

- QTS 내부 자동매매 시스템의 단일 프로젝트 루트
    
- 실행 진입점, 소스 코드, 테스트, 개발 도구를 명확히 분리 관리
    

---

## 2. Entry Point

```
main.py
```

### 목적

- 프로그램 단일 실행 진입점
    
- Runtime 초기화 및 Observer 기동 담당
    
- 비즈니스 로직 미포함 (Orchestration 전용)
    

---

## 3. Source Code (`src/`)

```
src/
```

### 목적

- 실제 시스템 동작 코드 영역
    
- 실행(Runtime), 외부 연동(Integration), 운영/관찰(Ops), 공용 코드(Shared)로 분리
    

---

### 3.1 Runtime Layer

```
src/runtime/
```

### 목적

- 판단·흐름·파이프라인 등 **시스템 핵심 실행 영역**
    
- 매매 판단 로직의 “실제 동작 경로”
    

#### 3.1.1 Core

```
src/runtime/core/
└─ app_context.py
```

- **AppContext**
    
    - 런타임 전역 상태 컨테이너
        
    - Config, Schema, Observer, Pipeline 간 공유 컨텍스트
        

---

#### 3.1.2 Config

```
src/runtime/config/
└─ config_loader.py
```

- 설정 로딩 및 검증 책임
    
- 실행 환경별 설정 분리의 기준점
    

---

#### 3.1.3 Schema

```
src/runtime/schema/
└─ schema_registry.py
```

- 스키마 로딩 및 등록 책임
    
- 데이터 구조의 단일 진실 소스 진입점
    

---

#### 3.1.4 Data

```
src/runtime/data/
└─ repository_base.py
```

- Repository 공통 베이스 정의
    
- 데이터 접근 추상화 계층의 기준 파일
    

---

#### 3.1.5 Engines

```
src/runtime/engines/
```

- Strategy / Risk / Portfolio / Trading 엔진 위치
    
- 현재 단계에서는 비워둠 (확장 시 생성)
    

---

#### 3.1.6 Pipeline

```
src/runtime/pipeline/
└─ eteda_runner.py
```

- ETEDA 파이프라인 실행 주체
    
- 판단 흐름의 중심 컨트롤러
    
- Observer에 관측 이벤트를 전달하는 역할
    

---

### 3.2 Integration Layer

```
src/integration/
└─ broker/
```

### 목적

- 외부 시스템 연동 영역
    
- 브로커, API, 외부 서비스 어댑터 위치
    
- Runtime과 물리적 분리 유지
    

---

### 3.3 Operations Layer

```
src/ops/
```

### 목적

- **관찰·안전·자동화 중심 운영 계층**
    
- 실행 로직과 분리된 시스템 보호 및 관측 책임
    

#### 3.3.1 Observer

```
src/ops/observer/
├─ observer.py
├─ event_bus.py
└─ snapshot.py
```

- **Observer Core**
    
    - 시스템 상태, 판단 결과, 이벤트 관측
        
- Event Bus
    
    - 이벤트 수집·전파
        
- Snapshot
    
    - 시점별 상태 스냅샷 기록
        

---

#### 3.3.2 Safety

```
src/ops/safety/
└─ guard.py
```

- Fail-safe 및 Guardrail 정의
    
- 비정상 상태 차단 기준점
    

---

#### 3.3.3 Automation

```
src/ops/automation/
```

- 스케줄링, 자동 점검, 동기화 영역
    
- 현재 단계에서는 비워둠
    

---

### 3.4 Shared

```
src/shared/
├─ utils.py
└─ decorators.py
```

### 목적

- Runtime에서 공통으로 사용하는 헬퍼 코드
    
- 실행 중 import 가능한 유틸만 위치
    

---

## 4. Tests

```
tests/
├─ conftest.py
└─ e2e/
```

### 목적

- 테스트 전용 영역 (src 외부)
    
- 실행·옵저버 기동 흐름 검증
    

---

## 5. Development Tools

```
tools/
├─ audit/
├─ maintenance/
└─ refactor/
```

### 목적

- **개발 생산성 전용 도구 영역**
    
- 코드 자체를 분석·수정·점검하는 스크립트 위치
    
- Runtime 코드와 완전 분리
    
- 필요 시에만 파일 생성
    

---

## 6. Project Configuration

```
.gitignore
pyproject.toml
.env   (git 제외)
```

### 목적

- Git 관리 기준 정의
    
- Python 프로젝트 기준 선언
    
- 실행 환경 변수는 로컬 전용으로 관리
    

---

## 7. 폴더 구조

```
QTS/
├─ main.py
│
├─ src/
│  ├─ runtime/
│  │  ├─ core/
│  │  │  └─ app_context.py
│  │  │
│  │  ├─ config/
│  │  │  └─ config_loader.py
│  │  │
│  │  ├─ schema/
│  │  │  └─ schema_registry.py
│  │  │
│  │  ├─ data/
│  │  │  └─ repository_base.py
│  │  │
│  │  ├─ engines/
│  │  │
│  │  └─ pipeline/
│  │     └─ eteda_runner.py
│  │
│  ├─ integration/
│  │  └─ broker/
│  │
│  ├─ ops/
│  │  ├─ observer/
│  │  │  ├─ observer.py
│  │  │  ├─ event_bus.py
│  │  │  └─ snapshot.py
│  │  │
│  │  ├─ safety/
│  │  │  └─ guard.py
│  │  │
│  │  └─ automation/
│  │
│  └─ shared/
│     ├─ utils.py
│     └─ decorators.py
│
├─ tests/
│  ├─ conftest.py
│  └─ e2e/
│
├─ tools/
│  ├─ audit/
│  ├─ maintenance/
│  └─ refactor/
│
├─ .env
├─ .gitignore
└─ pyproject.toml

```

---

## 8. 구조 운영 원칙 (요약)

- Runtime ↔ Ops ↔ Tools **물리적 분리 유지**
    
- Observer는 항상 실행 로직보다 상위 개념
    
- 구조 변경 없이 확장 가능하도록 설계
    
- 불필요한 파일 선생성 금지
    

---
