# Google Sheets 9-Sheet 연동 구현 계획

**생성일:** 2026-01-24  
**예상 기간:** 3-4주  
**담당자:** 지정 예정  

---

## 1. 구현 개요

Google Sheets 9-Sheet 연동 기능을 단계적으로 구현하는 상세 계획입니다. 스키마 관리 기반을 활용하여 데이터 영속성 계층을 완성합니다.

## 2. 구현 단계

### 단계 1: Google Sheets 클라이언트 구현 (1주차)

#### 1.1 기본 클라이언트 설계
```python
# src/runtime/data/google_sheets_client.py
class GoogleSheetsClient:
    """Google Sheets API v4 클라이언트"""
    
    def __init__(self, credentials_path: str):
        self.service = None
        self.credentials_path = credentials_path
        
    async def authenticate(self) -> bool:
        """Google API 인증"""
        
    async def get_spreadsheet(self, spreadsheet_id: str) -> dict:
        """스프레드시트 정보 조회"""
        
    async def get_sheet_data(self, spreadsheet_id: str, range_name: str) -> List[List]:
        """시트 데이터 조회"""
        
    async def update_sheet_data(self, spreadsheet_id: str, range_name: str, values: List[List]) -> dict:
        """시트 데이터 업데이트"""
        
    async def append_sheet_data(self, spreadsheet_id: str, range_name: str, values: List[List]) -> dict:
        """시트 데이터 추가"""
```

#### 1.2 인증 관리
- [ ] Google OAuth 2.0 인증 구현
- [ ] 토큰 자동 갱신 로직
- [ ] 인증 실패 처리 및 재시도
- [ ] 인증 정보 안전한 저장

#### 1.3 API 제한 관리
- [ ] 요청 레이트 리밋 구현 (100초당 100요청)
- [ ] 배치 작업 최적화
- [ ] 캐싱 전략 구현
- [ ] 지수 백오프 재시도 로직

### 단계 2: 리포지토리 베이스 설계 (1주차)

#### 2.1 공통 베이스 클래스
```python
# src/runtime/data/repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseSheetRepository(ABC):
    """시트 리포지토리 베이스 클래스"""
    
    def __init__(self, client: GoogleSheetsClient, spreadsheet_id: str, sheet_name: str):
        self.client = client
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.range_name = f"{sheet_name}!A:Z"
        
    @abstractmethod
    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 데이터 조회"""
        
    @abstractmethod
    async def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """ID로 데이터 조회"""
        
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 생성"""
        
    @abstractmethod
    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 업데이트"""
        
    @abstractmethod
    async def delete(self, record_id: str) -> bool:
        """데이터 삭제"""
```

#### 2.2 데이터 매핑 유틸리티
```python
# src/runtime/data/mappers/field_mapper.py
class FieldMapper:
    """스키마 기반 필드 매핑"""
    
    def __init__(self, schema_registry: SchemaRegistry):
        self.schema_registry = schema_registry
        
    def map_to_sheet(self, data: Dict[str, Any], sheet_name: str) -> List[Any]:
        """데이터를 시트 형식으로 매핑"""
        
    def map_from_sheet(self, row: List[Any], sheet_name: str) -> Dict[str, Any]:
        """시트 데이터를 객체 형식으로 매핑"""
        
    def validate_data(self, data: Dict[str, Any], sheet_name: str) -> bool:
        """데이터 유효성 검사"""
```

### 단계 3: 9개 시트 리포지토리 구현 (2주차)

#### 3.1 T_Ledger 리포지토리
```python
# src/runtime/data/repositories/t_ledger_repository.py
class T_LedgerRepository(BaseSheetRepository):
    """거래 장부 리포지토리"""
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 거래 기록 조회"""
        
    async def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """기간별 거래 기록 조회"""
        
    async def get_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """종목별 거래 기록 조회"""
        
    async def create_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """거래 기록 생성"""
```

#### 3.2 Position 리포지토리
```python
# src/runtime/data/repositories/position_repository.py
class PositionRepository(BaseSheetRepository):
    """포지션 리포지토리"""
    
    async def get_current_positions(self) -> List[Dict[str, Any]]:
        """현재 포지션 조회"""
        
    async def get_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """종목별 포지션 조회"""
        
    async def update_position(self, symbol: str, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """포지션 업데이트"""
```

#### 3.3 History 리포지토리
```python
# src/runtime/data/repositories/history_repository.py
class HistoryRepository(BaseSheetRepository):
    """히스토리 리포지토리"""
    
    async def get_execution_history(self) -> List[Dict[str, Any]]:
        """실행 히스토리 조회"""
        
    async def get_error_history(self) -> List[Dict[str, Any]]:
        """에러 히스토리 조회"""
```

#### 3.4 Strategy_Performance 리포지토리
```python
# src/runtime/data/repositories/strategy_performance_repository.py
class StrategyPerformanceRepository(BaseSheetRepository):
    """전략 성과 리포지토리"""
    
    async def get_performance_by_strategy(self, strategy_name: str) -> Dict[str, Any]:
        """전략별 성과 조회"""
        
    async def update_performance_metrics(self, strategy_name: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """성과 지표 업데이트"""
```

#### 3.5 R_Dash 리포지토리
```python
# src/runtime/data/repositories/r_dash_repository.py
class R_DashRepository(BaseSheetRepository):
    """대시보드 리포지토리"""
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """대시보드 데이터 조회"""
        
    async def update_dashboard_widget(self, widget_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """대시보드 위젯 업데이트"""
```

#### 3.6 기타 운영 시트 리포지토리 (4개)
- Config_Operations
- Risk_Monitoring  
- System_Health
- Audit_Log

### 단계 4: 통합 및 테스트 (0.5주차)

#### 4.1 통합 테스트
```python
# tests/runtime/data/integration/test_google_sheets_integration.py
class TestGoogleSheetsIntegration:
    """Google Sheets 연동 통합 테스트"""
    
    async def test_t_ledger_crud_operations(self):
        """T_Ledger CRUD 오퍼레이션 테스트"""
        
    async def test_position_repository_operations(self):
        """Position 리포지토리 오퍼레이션 테스트"""
        
    async def test_schema_field_mapping(self):
        """스키마 필드 매핑 테스트"""
        
    async def test_error_handling(self):
        """에러 핸들링 테스트"""
```

#### 4.2 성능 테스트
- [ ] 대용량 데이터 조회 성능 테스트
- [ ] 동시 요청 처리 성능 테스트
- [ ] API 제한 준수 확인
- [ ] 캐싱 효율성 테스트

## 3. 구현 우선순위

### 최우선 (1주차)
1. Google Sheets 클라이언트 기본 기능
2. T_Ledger 리포지토리 (가장 중요한 거래 데이터)
3. Position 리포지토리 (포지션 관리)

### 중요 (2주차)
4. History 리포지토리 (실행 기록)
5. Strategy_Performance 리포지토리 (성과 추적)
6. R_Dash 리포지토리 (대시보드)

### 후순위 (3주차)
7. 기타 운영 시트 리포지토리 4개
8. 고급 기능 (배치 처리, 캐싱 최적화)
9. 모니터링 및 로깅 강화

## 4. 기술적 고려사항

### 4.1 성능 최적화
- **배치 처리**: 여러 행을 한 번에 처리
- **캐싱**: 자주 조회하는 데이터 메모리 캐싱
- **비동기 처리**: asyncio를 통한 동시 요청 처리
- **API 제한**: Google Sheets API 제한 준수

### 4.2 에러 처리
- **네트워크 장애**: 재시도 로직 및 오프라인 모드
- **API 오류**: 상세한 에러 로깅 및 복구 전략
- **데이터 불일치**: 검증 레이어 및 롤백 메커니즘

### 4.3 보안
- **인증**: OAuth 2.0 토큰 안전한 관리
- **권한**: 최소 권한 원칙 적용
- **감사**: 모든 데이터 접근 로깅

## 5. 검증 기준

### 5.1 기능적 요구사항
- [ ] 9개 시트 모두 CRUD 오퍼레이션 가능
- [ ] 스키마 기반 필드 매핑 정확성
- [ ] 데이터 타입 변환 정확성
- [ ] 에러 상황에서의 안정적인 동작

### 5.2 비기능적 요구사항
- [ ] API 제한 준수 (100초당 100요청)
- [ ] 응답 시간 2초 이내 (일반 조회)
- [ ] 동시 요청 10개 처리 가능
- [ ] 99.9% 가용성

### 5.3 테스트 커버리지
- [ ] 단위 테스트 커버리지 90% 이상
- [ ] 통합 테스트 모든 시트 커버
- [ ] 에러 시나리오 테스트 완료

---

**구현 시작 예정:** 2026-01-27  
**완료 목표:** 2026-02-21
