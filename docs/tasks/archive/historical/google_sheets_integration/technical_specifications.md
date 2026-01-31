# Google Sheets 11-Sheet 연동 기술 명세서

**생성일:** 2026-01-24  
**버전:** 1.0  
**작성자:** QTS 개발팀  

---

## 1. 개요

본 문서는 Google Sheets 11-Sheet 연동 기능의 기술적 명세를 정의합니다. QTS 시스템의 데이터 영속성 계층을 구현하는 핵심 컴포넌트로서, 스키마 기반의 자동화된 데이터 연동을 목표로 합니다.

## 2. 시스템 아키텍처

### 2.1 전체 구조

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   QTS Runtime   │    │ Google Sheets   │    │   Schema        │
│                 │    │     API         │    │   Registry      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────────────────────────────────────────────────────┐
│                    Data Access Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ GoogleSheets    │  │   Repository    │  │   Field         │ │
│  │ Client          │  │   Manager       │  │   Mapper        │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────────────────────────────────────────────────────┐
│                   Repository Layer                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ T_Ledger    │ │ Position    │ │ History     │ │ Strategy   │ │
│  │ Repository  │ │ Repository  │ │ Repository  │ │ Performance│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ │ Repository│ │
│                                                   └───────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ R_Dash      │ │ Config_Ops  │ │ Risk_Monitor │ │ System_    │ │
│  │ Repository  │ │ Repository  │ │ Repository  │ │ Health     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ │ Repository│ │
│                                                   └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 컴포넌트 상세

#### 2.2.1 GoogleSheetsClient
- **책임**: Google Sheets API와의 직접 통신
- **기능**: 인증, API 호출, 에러 처리, 재시도 로직
- **위치**: `src/runtime/data/google_sheets_client.py`

#### 2.2.2 Repository Manager
- **책임**: 리포지토리 생명주기 관리
- **기능**: 리포지토리 생성, 연결 풀 관리, 트랜잭션 관리
- **위치**: `src/runtime/data/repository_manager.py`

#### 2.2.3 Field Mapper
- **책임**: 스키마와 시트 필드 간 매핑
- **기능**: 데이터 타입 변환, 필드 유효성 검사, 자동 매핑
- **위치**: `src/runtime/data/mappers/field_mapper.py`

## 3. 데이터 모델

### 3.1 스키마 정의

#### 3.1.1 T_Ledger 스키마
```python
T_LEDGER_SCHEMA = {
    "sheet_name": "T_Ledger",
    "fields": {
        "id": {"type": "string", "required": True, "primary_key": True},
        "timestamp": {"type": "datetime", "required": True},
        "symbol": {"type": "string", "required": True},
        "action": {"type": "enum", "values": ["BUY", "SELL"], "required": True},
        "quantity": {"type": "integer", "required": True},
        "price": {"type": "decimal", "required": True},
        "total_amount": {"type": "decimal", "required": True},
        "strategy": {"type": "string", "required": True},
        "broker": {"type": "string", "required": True},
        "status": {"type": "enum", "values": ["PENDING", "EXECUTED", "FAILED"], "required": True}
    }
}
```

#### 3.1.2 Position 스키마
```python
POSITION_SCHEMA = {
    "sheet_name": "Position",
    "fields": {
        "symbol": {"type": "string", "required": True, "primary_key": True},
        "quantity": {"type": "integer", "required": True},
        "avg_price": {"type": "decimal", "required": True},
        "current_price": {"type": "decimal", "required": True},
        "unrealized_pnl": {"type": "decimal", "required": True},
        "realized_pnl": {"type": "decimal", "required": True},
        "total_value": {"type": "decimal", "required": True},
        "last_updated": {"type": "datetime", "required": True},
        "strategy": {"type": "string", "required": True}
    }
}
```

### 3.2 데이터 흐름

```
Application Layer
       ↓
Repository Layer (CRUD Operations)
       ↓
Field Mapper (Schema ↔ Sheet Mapping)
       ↓
GoogleSheetsClient (API Communication)
       ↓
Google Sheets API
```

## 4. API 명세

### 4.1 GoogleSheetsClient API

#### 4.1.1 인증
```python
async def authenticate() -> bool:
    """
    Google API 인증 수행
    
    Returns:
        bool: 인증 성공 여부
        
    Raises:
        AuthenticationError: 인증 실패 시
    """
```

#### 4.1.2 데이터 조회
```python
async def get_sheet_data(
    spreadsheet_id: str, 
    range_name: str,
    max_retries: int = 3
) -> List[List[Any]]:
    """
    시트 데이터 조회
    
    Args:
        spreadsheet_id: 스프레드시트 ID
        range_name: 조회 범위 (예: "Sheet1!A:Z")
        max_retries: 최대 재시도 횟수
        
    Returns:
        List[List[Any]]: 시트 데이터
        
    Raises:
        APIError: API 호출 실패 시
        RateLimitError: API 제한 초과 시
    """
```

#### 4.1.3 데이터 업데이트
```python
async def update_sheet_data(
    spreadsheet_id: str,
    range_name: str,
    values: List[List[Any]],
    value_input_option: str = "USER_ENTERED"
) -> Dict[str, Any]:
    """
    시트 데이터 업데이트
    
    Args:
        spreadsheet_id: 스프레드시트 ID
        range_name: 업데이트 범위
        values: 업데이트할 데이터
        value_input_option: 값 입력 옵션
        
    Returns:
        Dict[str, Any]: 업데이트 결과
        
    Raises:
        APIError: API 호출 실패 시
        ValidationError: 데이터 유효성 검사 실패 시
    """
```

### 4.2 Repository API

#### 4.2.1 BaseRepository
```python
class BaseSheetRepository(ABC):
    """시트 리포지토리 베이스 클래스"""
    
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
        
    @abstractmethod
    async def exists(self, record_id: str) -> bool:
        """데이터 존재 여부 확인"""
```

## 5. 에러 처리

### 5.1 에러 타입 정의

```python
class GoogleSheetsError(Exception):
    """Google Sheets 관련 기본 에러"""
    pass

class AuthenticationError(GoogleSheetsError):
    """인증 에러"""
    pass

class APIError(GoogleSheetsError):
    """API 호출 에러"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code

class RateLimitError(APIError):
    """API 제한 초과 에러"""
    def __init__(self, retry_after: int = None):
        super().__init__("API rate limit exceeded")
        self.retry_after = retry_after

class ValidationError(GoogleSheetsError):
    """데이터 유효성 검사 에러"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field
```

### 5.2 에러 처리 전략

#### 5.2.1 재시도 로직
```python
async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """
    지수 백오프 재시도 로직
    
    Args:
        func: 재시도할 함수
        max_retries: 최대 재시도 횟수
        base_delay: 기본 지연 시간
        max_delay: 최대 지연 시간
    """
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except RateLimitError as e:
            if attempt == max_retries:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            await asyncio.sleep(delay)
        except APIError as e:
            if e.status_code and e.status_code < 500:
                raise  # 클라이언트 에러는 재시도 안 함
            if attempt == max_retries:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            await asyncio.sleep(delay)
```

## 6. 성능 최적화

### 6.1 캐싱 전략

#### 6.1.1 메모리 캐시
```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedRepository:
    """캐싱 기능이 있는 리포지토리"""
    
    def __init__(self, repository: BaseSheetRepository, cache_ttl: int = 300):
        self.repository = repository
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_timestamps = {}
    
    async def get_all(self) -> List[Dict[str, Any]]:
        cache_key = "all"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        data = await self.repository.get_all()
        self._update_cache(cache_key, data)
        return data
    
    def _is_cache_valid(self, key: str) -> bool:
        """캐시 유효성 검사"""
        if key not in self._cache:
            return False
        
        timestamp = self._cache_timestamps.get(key, datetime.min)
        return datetime.now() - timestamp < timedelta(seconds=self.cache_ttl)
```

#### 6.1.2 배치 처리
```python
class BatchProcessor:
    """배치 데이터 처리"""
    
    def __init__(self, client: GoogleSheetsClient, batch_size: int = 100):
        self.client = client
        self.batch_size = batch_size
    
    async def batch_update(
        self, 
        spreadsheet_id: str, 
        updates: List[Tuple[str, List[List[Any]]]]
    ) -> List[Dict[str, Any]]:
        """
        배치 업데이트 수행
        
        Args:
            spreadsheet_id: 스프레드시트 ID
            updates: (range_name, values) 튜플 리스트
            
        Returns:
            List[Dict[str, Any]]: 업데이트 결과 리스트
        """
        results = []
        for i in range(0, len(updates), self.batch_size):
            batch = updates[i:i + self.batch_size]
            batch_results = await self._process_batch(spreadsheet_id, batch)
            results.extend(batch_results)
        return results
```

### 6.2 동시성 제어

#### 6.2.1 세마포어 기반 제어
```python
import asyncio

class ConcurrencyController:
    """동시성 제어"""
    
    def __init__(self, max_concurrent_requests: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
    
    async def execute(self, func: Callable, *args, **kwargs):
        """동시성 제어하며 함수 실행"""
        async with self.semaphore:
            return await func(*args, **kwargs)
```

## 7. 보안

### 7.1 인증 관리

#### 7.1.1 OAuth 2.0 토큰 관리
```python
class TokenManager:
    """OAuth 2.0 토큰 관리"""
    
    def __init__(self, credentials_path: str):
        self.credentials_path = credentials_path
        self._token_cache = None
        self._token_expiry = None
    
    async def get_valid_token(self) -> str:
        """유효한 토큰获取"""
        if self._is_token_valid():
            return self._token_cache
        
        await self._refresh_token()
        return self._token_cache
    
    def _is_token_valid(self) -> bool:
        """토큰 유효성 검사"""
        if not self._token_cache or not self._token_expiry:
            return False
        
        return datetime.now() < self._token_expiry - timedelta(minutes=5)
```

### 7.2 접근 제어

#### 7.2.1 권한 관리
```python
class AccessController:
    """접근 제어"""
    
    def __init__(self):
        self.permissions = {
            "read": ["T_Ledger", "Position", "History", "Strategy_Performance", "R_Dash"],
            "write": ["T_Ledger", "Position", "History", "Strategy_Performance"],
            "admin": ["Config_Operations", "Risk_Monitoring", "System_Health", "Audit_Log"]
        }
    
    def can_access(self, sheet_name: str, operation: str, user_role: str) -> bool:
        """접근 권한 확인"""
        if user_role not in self.permissions:
            return False
        
        allowed_sheets = self.permissions.get(user_role, [])
        return sheet_name in allowed_sheets
```

## 8. 모니터링 및 로깅

### 8.1 메트릭 수집

```python
class MetricsCollector:
    """메트릭 수집기"""
    
    def __init__(self):
        self.api_calls = Counter("google_sheets_api_calls_total")
        self.api_errors = Counter("google_sheets_api_errors_total")
        self.response_time = Histogram("google_sheets_response_time_seconds")
        self.cache_hits = Counter("google_sheets_cache_hits_total")
        self.cache_misses = Counter("google_sheets_cache_misses_total")
    
    def record_api_call(self, operation: str, success: bool, duration: float):
        """API 호출 기록"""
        self.api_calls.labels(operation=operation).inc()
        if not success:
            self.api_errors.labels(operation=operation).inc()
        self.response_time.observe(duration)
```

### 8.2 로깅

```python
import logging

class GoogleSheetsLogger:
    """Google Sheets 전용 로거"""
    
    def __init__(self):
        self.logger = logging.getLogger("google_sheets")
        
    def log_api_call(self, operation: str, spreadsheet_id: str, range_name: str):
        """API 호출 로그"""
        self.logger.info(
            f"API Call: {operation}",
            extra={
                "operation": operation,
                "spreadsheet_id": spreadsheet_id,
                "range_name": range_name
            }
        )
    
    def log_error(self, operation: str, error: Exception):
        """에러 로그"""
        self.logger.error(
            f"Error in {operation}: {str(error)}",
            extra={
                "operation": operation,
                "error_type": type(error).__name__,
                "error_message": str(error)
            },
            exc_info=True
        )
```

## 9. 테스트 전략

### 9.1 단위 테스트

#### 9.1.1 GoogleSheetsClient 테스트
```python
import pytest
from unittest.mock import AsyncMock, patch

class TestGoogleSheetsClient:
    """GoogleSheetsClient 단위 테스트"""
    
    @pytest.fixture
    def client(self):
        return GoogleSheetsClient("test_credentials.json")
    
    @patch('googleapiclient.discovery.build')
    async def test_authenticate_success(self, mock_build, client):
        """인증 성공 테스트"""
        mock_build.return_value = AsyncMock()
        result = await client.authenticate()
        assert result is True
    
    @patch('googleapiclient.discovery.build')
    async def test_authenticate_failure(self, mock_build, client):
        """인증 실패 테스트"""
        mock_build.side_effect = Exception("Auth failed")
        with pytest.raises(AuthenticationError):
            await client.authenticate()
```

### 9.2 통합 테스트

#### 9.2.1 Repository 통합 테스트
```python
class TestRepositoryIntegration:
    """리포지토리 통합 테스트"""
    
    @pytest.fixture
    async def setup(self):
        """테스트 환경 설정"""
        # 테스트용 Google Sheets 설정
        # 테스트 데이터 초기화
        pass
    
    async def test_t_ledger_crud_operations(self, setup):
        """T_Ledger CRUD 오퍼레이션 테스트"""
        repository = T_LedgerRepository(client, test_spreadsheet_id, "T_Ledger_Test")
        
        # Create
        test_data = {
            "id": "test_001",
            "timestamp": datetime.now(),
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 150.0,
            "total_amount": 15000.0,
            "strategy": "scalp",
            "broker": "kis",
            "status": "EXECUTED"
        }
        
        created = await repository.create(test_data)
        assert created["id"] == "test_001"
        
        # Read
        retrieved = await repository.get_by_id("test_001")
        assert retrieved is not None
        assert retrieved["symbol"] == "AAPL"
        
        # Update
        updated_data = {"status": "COMPLETED"}
        updated = await repository.update("test_001", updated_data)
        assert updated["status"] == "COMPLETED"
        
        # Delete
        deleted = await repository.delete("test_001")
        assert deleted is True
```

## 10. 배포 및 운영

### 10.1 환경 설정

#### 10.1.1 환경 변수
```bash
# Google Sheets API 설정
GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_SHEETS_API_QUOTA=100

# 캐싱 설정
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# 동시성 설정
MAX_CONCURRENT_REQUESTS=10
BATCH_SIZE=100
```

#### 10.1.2 설정 파일
```python
# config/google_sheets_config.py
GOOGLE_SHEETS_CONFIG = {
    "credentials_path": os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH"),
    "spreadsheet_id": os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID"),
    "api_quota": int(os.getenv("GOOGLE_SHEETS_API_QUOTA", "100")),
    "cache_ttl": int(os.getenv("CACHE_TTL", "300")),
    "max_concurrent_requests": int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
    "batch_size": int(os.getenv("BATCH_SIZE", "100"))
}
```

### 10.2 모니터링

#### 10.2.1 헬스체크
```python
async def health_check() -> Dict[str, Any]:
    """시스템 헬스체크"""
    try:
        client = GoogleSheetsClient(GOOGLE_SHEETS_CONFIG["credentials_path"])
        await client.authenticate()
        
        # 샘플 데이터 조회 테스트
        await client.get_sheet_data(
            GOOGLE_SHEETS_CONFIG["spreadsheet_id"],
            "T_Ledger!A1:Z1"
        )
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "google_sheets": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
```

---

**문서 버전:** 1.0  
**최종 업데이트:** 2026-01-24  
**다음 검토일:** 2026-01-31
