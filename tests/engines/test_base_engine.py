#!/usr/bin/env python3
"""
Base Engine 테스트
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.strategy.engines.base_engine import BaseEngine, EngineState, EngineMetrics
from src.qts.core.config.config_models import UnifiedConfig, ConfigScope


class MockEngine(BaseEngine):
    """테스트용 Mock 엔진"""
    
    async def initialize(self) -> bool:
        return True
    
    async def start(self) -> bool:
        self._update_state(is_running=True)  # 명시적으로 상태 업데이트
        return True
    
    async def stop(self) -> bool:
        return True
    
    async def execute(self, data):
        return {'result': 'mock_result'}  # BaseEngine의 execute 로직을 따르지 않음


class TestBaseEngine:
    """BaseEngine 테스트 클래스"""
    
    def setup_method(self):
        """테스트 설정"""
        self.config = UnifiedConfig(
            config_map={},
            metadata={}
        )
        self.engine = MockEngine(self.config)
    
    def test_initialization(self):
        """초기화 테스트"""
        assert self.engine.config == self.config
        assert isinstance(self.engine.state, EngineState)
        assert isinstance(self.engine.metrics, EngineMetrics)
        assert self.engine._event_callbacks == {}
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """초기화 테스트"""
        result = await self.engine.initialize()
        assert result is True
        assert self.engine.state.is_running is False
    
    @pytest.mark.asyncio
    async def test_start(self):
        """시작 테스트"""
        result = await self.engine.start()
        assert result is True
        assert self.engine.state.is_running is True
    
    @pytest.mark.asyncio
    async def test_stop(self):
        """중지 테스트"""
        result = await self.engine.stop()
        assert result is True
        assert self.engine.state.is_running is False
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """실행 테스트"""
        data = {'operation': 'test'}
        result = await self.engine.execute(data)
        
        # MockEngine은 BaseEngine의 execute 로직을 따르지 않음
        assert result['result'] == 'mock_result'
    
    def test_register_event_callback(self):
        """이벤트 콜백 등록 테스트"""
        callback = Mock()
        self.engine.register_event_callback('test_event', callback)
        
        assert 'test_event' in self.engine._event_callbacks
        assert callback in self.engine._event_callbacks['test_event']
    
    def test_unregister_event_callback(self):
        """이벤트 콜백 등록 해제 테스트"""
        callback = Mock()
        self.engine.register_event_callback('test_event', callback)
        self.engine.unregister_event_callback('test_event', callback)
        
        assert callback not in self.engine._event_callbacks.get('test_event', [])
    
    @pytest.mark.asyncio
    async def test_emit_event(self):
        """이벤트 발생 테스트"""
        callback = AsyncMock()
        self.engine.register_event_callback('test_event', callback)
        
        data = {'test': 'data'}
        await self.engine._emit_event('test_event', data)
        
        callback.assert_called_once_with(data)
    
    @pytest.mark.asyncio
    async def test_get_status(self):
        """상태 조회 테스트"""
        status = await self.engine.get_status()
        
        assert 'engine_type' in status
        assert 'state' in status
        assert 'metrics' in status
        assert 'config' in status
        assert status['engine_type'] == 'MockEngine'
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """헬스체크 테스트"""
        health = await self.engine.health_check()
        
        assert 'status' in health
        assert 'engine' in health
        assert 'timestamp' in health
        assert health['engine'] == 'MockEngine'
    
    def test_update_metrics(self):
        """성과 지표 업데이트 테스트"""
        self.engine._update_metrics(0.5, True)
        
        assert self.engine.metrics.total_operations == 1
        assert self.engine.metrics.success_operations == 1
        assert self.engine.metrics.error_operations == 0
        assert self.engine.metrics.last_execution_time == 0.5
    
    def test_update_state(self):
        """상태 업데이트 테스트"""
        self.engine._update_state(True, "test error")
        
        assert self.engine.state.is_running is True
        assert self.engine.state.last_updated is not None
        assert self.engine.state.last_error == "test error"


if __name__ == "__main__":
    pytest.main([__file__])
