# Google Sheets 9-Sheet 연동 테스트 계획

**생성일:** 2026-01-24  
**예상 기간:** 1주  
**담당자:** 지정 예정  

---

## 1. 테스트 개요

Google Sheets 9-Sheet 연동 기능의 품질 보증을 위한 종합적인 테스트 계획입니다. 단위 테스트, 통합 테스트, 성능 테스트, 보안 테스트를 포함하여 시스템의 안정성과 신뢰성을 검증합니다.

## 2. 테스트 목표

### 2.1 주요 목표
- [ ] 9개 시트 모든 CRUD 오퍼레이션 정상 동작 검증
- [ ] 스키마 기반 필드 매핑 정확성 검증
- [ ] 에러 처리 및 복구 메커니즘 검증
- [ ] 성능 기준 충족 여부 검증
- [ ] 보안 요구사항 준수 여부 검증

### 2.2 성공 기준
- **기능적**: 모든 기능 요구사항 100% 충족
- **성능**: 응답 시간 2초 이내 (일반 조회)
- **안정성**: 99.9% 가용성
- **테스트 커버리지**: 단위 테스트 90% 이상

## 3. 테스트 범위

### 3.1 포함 범위
- GoogleSheetsClient 모듈
- 9개 시트 리포지토리
- 필드 매핑 기능
- 에러 처리 로직
- 캐싱 메커니즘
- 동시성 제어
- 인증 및 권한 관리

### 3.2 제외 범위
- Google Sheets API 자체 기능
- 외부 네트워크 인프라
- QTS 시스템의 다른 모듈과의 연동

## 4. 테스트 전략

### 4.1 테스트 레벨

```
┌─────────────────────────────────────────────────────────┐
│                    E2E Test                             │
│              (실제 Google Sheets 연동)                   │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                Integration Test                         │
│          (모듈 간 연동 및 Mock Google Sheets)           │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                  Unit Test                              │
│              (개별 모듈 단위 테스트)                    │
└─────────────────────────────────────────────────────────┘
```

### 4.2 테스트 환경

#### 4.2.1 개발 환경
- **목적**: 단위 테스트 및 기본 기능 검증
- **데이터**: Mock 데이터 사용
- **Google Sheets**: Mock 서버 사용

#### 4.2.2 통합 환경
- **목적**: 모듈 간 연동 테스트
- **데이터**: 테스트용 Google Sheets 사용
- **Google Sheets**: 실제 API 연동 (테스트 계정)

#### 4.2.3 스테이징 환경
- **목적**: E2E 테스트 및 성능 테스트
- **데이터**: 프로덕션과 유사한 데이터
- **Google Sheets**: 실제 API 연동 (스테이징 계정)

## 5. 단위 테스트 계획

### 5.1 GoogleSheetsClient 테스트

#### 5.1.1 인증 테스트
```python
class TestGoogleSheetsClientAuthentication:
    """GoogleSheetsClient 인증 테스트"""
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """인증 성공 시나리오"""
        # Given: 유효한 인증 정보
        client = GoogleSheetsClient("valid_credentials.json")
        
        # When: 인증 시도
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_build.return_value = AsyncMock()
            result = await client.authenticate()
        
        # Then: 인증 성공
        assert result is True
        mock_build.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_invalid_credentials(self):
        """유효하지 않은 인증 정보 테스트"""
        # Given: 유효하지 않은 인증 정보
        client = GoogleSheetsClient("invalid_credentials.json")
        
        # When & Then: 인증 실패
        with pytest.raises(AuthenticationError):
            await client.authenticate()
    
    @pytest.mark.asyncio
    async def test_token_refresh(self):
        """토큰 갱신 테스트"""
        # Given: 만료된 토큰
        client = GoogleSheetsClient("credentials.json")
        client._token_expiry = datetime.now() - timedelta(hours=1)
        
        # When: API 호출
        with patch.object(client, '_refresh_token') as mock_refresh:
            mock_refresh.return_value = "new_token"
            await client.get_sheet_data("test_id", "Sheet1!A:Z")
        
        # Then: 토큰 갱신 호출
        mock_refresh.assert_called_once()
```

#### 5.1.2 API 호출 테스트
```python
class TestGoogleSheetsClientAPI:
    """GoogleSheetsClient API 호출 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_sheet_data_success(self):
        """데이터 조회 성공 테스트"""
        client = GoogleSheetsClient("credentials.json")
        client.service = AsyncMock()
        
        # Mock API 응답
        mock_response = {
            "values": [
                ["id", "symbol", "action", "quantity"],
                ["1", "AAPL", "BUY", "100"],
                ["2", "GOOGL", "SELL", "50"]
            ]
        }
        client.service.spreadsheets().values().get().execute.return_value = mock_response
        
        result = await client.get_sheet_data("test_id", "Sheet1!A:Z")
        
        assert len(result) == 3
        assert result[0] == ["id", "symbol", "action", "quantity"]
        assert result[1] == ["1", "AAPL", "BUY", "100"]
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """API 제한 처리 테스트"""
        client = GoogleSheetsClient("credentials.json")
        client.service = AsyncMock()
        
        # Mock Rate Limit Error
        from googleapiclient.errors import HttpError
        error = HttpError(resp=Mock(status=429), content=b'Rate limit exceeded')
        client.service.spreadsheets().values().get().execute.side_effect = error
        
        with pytest.raises(RateLimitError):
            await client.get_sheet_data("test_id", "Sheet1!A:Z")
```

### 5.2 Repository 테스트

#### 5.2.1 T_LedgerRepository 테스트
```python
class TestT_LedgerRepository:
    """T_LedgerRepository 테스트"""
    
    @pytest.fixture
    async def repository(self):
        """테스트용 리포지토리 설정"""
        mock_client = AsyncMock(spec=GoogleSheetsClient)
        return T_LedgerRepository(mock_client, "test_spreadsheet", "T_Ledger_Test")
    
    @pytest.mark.asyncio
    async def test_create_trade(self, repository):
        """거래 생성 테스트"""
        # Given
        trade_data = {
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
        
        # Mock client response
        repository.client.append_sheet_data.return_value = {"updatedRows": 1}
        
        # When
        result = await repository.create(trade_data)
        
        # Then
        assert result["id"] == "test_001"
        assert result["symbol"] == "AAPL"
        repository.client.append_sheet_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_date_range(self, repository):
        """기간별 거래 조회 테스트"""
        # Given
        start_date = "2026-01-01"
        end_date = "2026-01-31"
        
        mock_data = [
            {"id": "1", "timestamp": "2026-01-15", "symbol": "AAPL"},
            {"id": "2", "timestamp": "2026-01-20", "symbol": "GOOGL"}
        ]
        repository.client.get_sheet_data.return_value = mock_data
        
        # When
        result = await repository.get_by_date_range(start_date, end_date)
        
        # Then
        assert len(result) == 2
        assert all(start_date <= item["timestamp"] <= end_date for item in result)
```

### 5.3 Field Mapper 테스트

```python
class TestFieldMapper:
    """필드 매핑 테스트"""
    
    @pytest.fixture
    def mapper(self):
        """테스트용 필드 매퍼 설정"""
        mock_schema_registry = AsyncMock()
        mock_schema_registry.get_schema.return_value = T_LEDGER_SCHEMA
        return FieldMapper(mock_schema_registry)
    
    def test_map_to_sheet_success(self, mapper):
        """시트 형식으로 매핑 성공 테스트"""
        # Given
        data = {
            "id": "test_001",
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 150.0
        }
        
        # When
        result = mapper.map_to_sheet(data, "T_Ledger")
        
        # Then
        assert isinstance(result, list)
        assert len(result) == len(T_LEDGER_SCHEMA["fields"])
        assert "test_001" in result
        assert "AAPL" in result
    
    def test_map_from_sheet_success(self, mapper):
        """객체 형식으로 매핑 성공 테스트"""
        # Given
        row = ["test_001", "2026-01-24 10:00:00", "AAPL", "BUY", "100", "150.0"]
        
        # When
        result = mapper.map_from_sheet(row, "T_Ledger")
        
        # Then
        assert isinstance(result, dict)
        assert result["id"] == "test_001"
        assert result["symbol"] == "AAPL"
        assert result["action"] == "BUY"
        assert result["quantity"] == 100
        assert result["price"] == 150.0
    
    def test_validate_data_success(self, mapper):
        """데이터 유효성 검사 성공 테스트"""
        # Given
        valid_data = {
            "id": "test_001",
            "symbol": "AAPL",
            "action": "BUY",
            "quantity": 100,
            "price": 150.0
        }
        
        # When & Then
        assert mapper.validate_data(valid_data, "T_Ledger") is True
    
    def test_validate_data_failure(self, mapper):
        """데이터 유효성 검사 실패 테스트"""
        # Given
        invalid_data = {
            "id": "test_001",
            "symbol": "AAPL",
            "action": "INVALID_ACTION",  # 유효하지 않은 값
            "quantity": 100,
            "price": 150.0
        }
        
        # When & Then
        assert mapper.validate_data(invalid_data, "T_Ledger") is False
```

## 6. 통합 테스트 계획

### 6.1 Repository 통합 테스트

```python
class TestRepositoryIntegration:
    """리포지토리 통합 테스트"""
    
    @pytest.fixture(scope="class")
    async def integration_setup(self):
        """통합 테스트 환경 설정"""
        # 테스트용 Google Sheets 설정
        spreadsheet_id = os.getenv("TEST_SPREADSHEET_ID")
        client = GoogleSheetsClient("test_credentials.json")
        await client.authenticate()
        
        # 테스트 데이터 초기화
        await self._setup_test_data(client, spreadsheet_id)
        
        yield {
            "client": client,
            "spreadsheet_id": spreadsheet_id
        }
        
        # 테스트 데이터 정리
        await self._cleanup_test_data(client, spreadsheet_id)
    
    @pytest.mark.asyncio
    async def test_t_ledger_full_crud_cycle(self, integration_setup):
        """T_Ledger 전체 CRUD 사이클 테스트"""
        client = integration_setup["client"]
        spreadsheet_id = integration_setup["spreadsheet_id"]
        
        repository = T_LedgerRepository(client, spreadsheet_id, "T_Ledger_Test")
        
        # Create
        trade_data = {
            "id": "integration_test_001",
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
        
        created = await repository.create(trade_data)
        assert created["id"] == "integration_test_001"
        
        # Read
        retrieved = await repository.get_by_id("integration_test_001")
        assert retrieved is not None
        assert retrieved["symbol"] == "AAPL"
        
        # Update
        updated_data = {"status": "COMPLETED"}
        updated = await repository.update("integration_test_001", updated_data)
        assert updated["status"] == "COMPLETED"
        
        # Delete
        deleted = await repository.delete("integration_test_001")
        assert deleted is True
        
        # Verify deletion
        deleted_record = await repository.get_by_id("integration_test_001")
        assert deleted_record is None
```

### 6.2 다중 리포지토리 통합 테스트

```python
class TestMultiRepositoryIntegration:
    """다중 리포지토리 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_trade_to_position_flow(self, integration_setup):
        """거래에서 포지션으로의 데이터 흐름 테스트"""
        client = integration_setup["client"]
        spreadsheet_id = integration_setup["spreadsheet_id"]
        
        t_ledger_repo = T_LedgerRepository(client, spreadsheet_id, "T_Ledger_Test")
        position_repo = PositionRepository(client, spreadsheet_id, "Position_Test")
        
        # Given: 초기 포지션 없음
        initial_positions = await position_repo.get_current_positions()
        assert len(initial_positions) == 0
        
        # When: 거래 실행
        trade_data = {
            "id": "flow_test_001",
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
        
        await t_ledger_repo.create(trade_data)
        
        # Then: 포지션 생성 확인
        updated_positions = await position_repo.get_current_positions()
        aapl_position = next((p for p in updated_positions if p["symbol"] == "AAPL"), None)
        
        assert aapl_position is not None
        assert aapl_position["quantity"] == 100
        assert aapl_position["avg_price"] == 150.0
```

## 7. 성능 테스트 계획

### 7.1 부하 테스트

#### 7.1.1 동시 요청 테스트
```python
class TestPerformance:
    """성능 테스트"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, integration_setup):
        """동시 요청 성능 테스트"""
        client = integration_setup["client"]
        spreadsheet_id = integration_setup["spreadsheet_id"]
        
        repository = T_LedgerRepository(client, spreadsheet_id, "T_Ledger_Test")
        
        # Given: 100개의 동시 요청
        num_requests = 100
        requests = []
        
        for i in range(num_requests):
            request = repository.get_by_id(f"perf_test_{i}")
            requests.append(request)
        
        # When: 동시 실행
        start_time = time.time()
        results = await asyncio.gather(*requests, return_exceptions=True)
        end_time = time.time()
        
        # Then: 성능 기준 충족
        duration = end_time - start_time
        assert duration < 10.0  # 10초 이내 완료
        assert len([r for r in results if not isinstance(r, Exception)]) > 95  # 95% 이상 성공
    
    @pytest.mark.asyncio
    async def test_batch_update_performance(self, integration_setup):
        """배치 업데이트 성능 테스트"""
        client = integration_setup["client"]
        spreadsheet_id = integration_setup["spreadsheet_id"]
        
        # Given: 1000개의 데이터 업데이트
        batch_size = 100
        num_batches = 10
        
        updates = []
        for batch in range(num_batches):
            batch_updates = []
            for i in range(batch_size):
                row_data = [f"batch_{batch}_item_{i}", "AAPL", "BUY", 100, 150.0]
                batch_updates.append((f"Batch_{batch}!A{batch*i+2}:E{batch*i+2}", [row_data]))
            updates.extend(batch_updates)
        
        # When: 배치 업데이트 실행
        start_time = time.time()
        batch_processor = BatchProcessor(client)
        results = await batch_processor.batch_update(spreadsheet_id, updates)
        end_time = time.time()
        
        # Then: 성능 기준 충족
        duration = end_time - start_time
        assert duration < 30.0  # 30초 이내 완료
        assert len(results) == len(updates)  # 모든 업데이트 성공
```

### 7.2 메모리 사용량 테스트

```python
class TestMemoryUsage:
    """메모리 사용량 테스트"""
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, integration_setup):
        """메모리 누수 감지 테스트"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Given: 대량의 데이터 처리
        client = integration_setup["client"]
        repository = T_LedgerRepository(client, integration_setup["spreadsheet_id"], "T_Ledger_Test")
        
        # When: 반복적인 데이터 처리
        for iteration in range(100):
            # 대량 데이터 조회
            await repository.get_all()
            
            # 메모리 정리
            gc.collect()
            
            if iteration % 10 == 0:
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # Then: 메모리 증가량 제한 (50MB 이하)
                assert memory_increase < 50 * 1024 * 1024
```

## 8. 보안 테스트 계획

### 8.1 인증 보안 테스트

```python
class TestSecurity:
    """보안 테스트"""
    
    @pytest.mark.asyncio
    async def test_invalid_credentials_rejection(self):
        """유효하지 않은 인증 정보 거부 테스트"""
        # Given: 유효하지 않은 인증 정보
        client = GoogleSheetsClient("invalid_credentials.json")
        
        # When & Then: 인증 실패
        with pytest.raises(AuthenticationError):
            await client.authenticate()
    
    @pytest.mark.asyncio
    async def test_token_expiration_handling(self, integration_setup):
        """토큰 만료 처리 테스트"""
        client = integration_setup["client"]
        
        # Given: 만료된 토큰으로 설정
        original_expiry = client._token_expiry
        client._token_expiry = datetime.now() - timedelta(hours=1)
        
        try:
            # When: API 호출
            await client.get_sheet_data(
                integration_setup["spreadsheet_id"],
                "T_Ledger!A:Z"
            )
            
            # Then: 토큰이 자동 갱신되어야 함
            assert client._token_expiry > datetime.now()
        finally:
            # Cleanup
            client._token_expiry = original_expiry
    
    @pytest.mark.asyncio
    async def test_access_control_enforcement(self, integration_setup):
        """접근 제어 강제 테스트"""
        access_controller = AccessController()
        
        # Given: 읽기 전용 권한 사용자
        user_role = "read"
        
        # When & Then: 쓰기 권한이 없는 시트에 접근 시도
        assert not access_controller.can_access("Config_Operations", "write", user_role)
        assert access_controller.can_access("T_Ledger", "read", user_role)
```

## 9. 에러 시나리오 테스트

### 9.1 네트워크 장애 테스트

```python
class TestErrorScenarios:
    """에러 시나리오 테스트"""
    
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, integration_setup):
        """네트워크 타임아웃 처리 테스트"""
        client = integration_setup["client"]
        
        # Given: 네트워크 타임아웃 시뮬레이션
        with patch.object(client, '_make_api_request') as mock_request:
            mock_request.side_effect = asyncio.TimeoutError("Network timeout")
            
            # When & Then: 타임아웃 에러 처리
            with pytest.raises(APIError) as exc_info:
                await client.get_sheet_data("test_id", "Sheet1!A:Z")
            
            assert "Network timeout" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_api_quota_exceeded_handling(self, integration_setup):
        """API 할당량 초과 처리 테스트"""
        client = integration_setup["client"]
        
        # Given: API 할당량 초과 시뮬레이션
        from googleapiclient.errors import HttpError
        error = HttpError(resp=Mock(status=429), content=b'Quota exceeded')
        
        with patch.object(client.service.spreadsheets().values().get(), 'execute', side_effect=error):
            # When & Then: RateLimitError 발생
            with pytest.raises(RateLimitError):
                await client.get_sheet_data("test_id", "Sheet1!A:Z")
    
    @pytest.mark.asyncio
    async def test_data_corruption_recovery(self, integration_setup):
        """데이터 손상 복구 테스트"""
        client = integration_setup["client"]
        repository = T_LedgerRepository(client, integration_setup["spreadsheet_id"], "T_Ledger_Test")
        
        # Given: 손상된 데이터
        corrupted_data = ["invalid_id", "", "INVALID_ACTION", "not_a_number", "not_a_price"]
        
        # When: 데이터 매핑 시도
        mapper = FieldMapper(AsyncMock())
        
        # Then: 유효성 검사 실패
        assert not mapper.validate_data_from_sheet(corrupted_data, "T_Ledger")
```

## 10. 테스트 실행 계획

### 10.1 테스트 일정

| 주차 | 테스트 유형 | 목표 | 담당자 |
|------|------------|------|--------|
| 1주차 | 단위 테스트 | 모든 모듈 단위 테스트 완료 | 개발자 |
| 2주차 | 통합 테스트 | 모듈 간 연동 테스트 완료 | 개발자 |
| 3주차 | 성능 테스트 | 성능 기준 충족 검증 | 성능 엔지니어 |
| 4주차 | 보안 테스트 | 보안 요구사항 검증 | 보안 전문가 |
| 5주차 | E2E 테스트 | 전체 시스템 테스트 | QA팀 |

### 10.2 테스트 환경 구성

#### 10.2.1 테스트 데이터
- **테스트용 Google Sheets**: 별도의 테스트 스프레드시트 사용
- **데이터 크기**: 소규모(100행), 중규모(1,000행), 대규모(10,000행)
- **데이터 종류**: 정상 데이터, 경계값 데이터, 오류 데이터

#### 10.2.2 테스트 도구
- **테스트 프레임워크**: pytest, pytest-asyncio
- **Mock 도구**: unittest.mock, pytest-mock
- **성능 측정**: pytest-benchmark
- **커버리지**: pytest-cov
- **CI/CD**: GitHub Actions

### 10.3 테스트 보고

#### 10.3.1 보고서 내용
- 테스트 실행 결과 요약
- 성능 테스트 결과
- 에러 발생 현황
- 커버리지 리포트
- 개선 사항 및 권고사항

#### 10.3.2 성공 기준
- **기능 테스트**: 100% 통과
- **성능 테스트**: 모든 기준 충족
- **보안 테스트**: 모든 취약점 해결
- **커버리지**: 단위 테스트 90% 이상

---

**문서 버전:** 1.0  
**최종 업데이트:** 2026-01-24  
**테스트 시작 예정:** 2026-02-03  
**테스트 완료 목표:** 2026-03-03
