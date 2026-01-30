"""
Base Engine

모든 엔진의 기본 인터페이스와 공통 기능을 정의합니다.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from ..config.config_models import UnifiedConfig


@dataclass
class EngineState:
    """엔진 상태 정보"""
    is_running: bool = False
    last_updated: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class EngineMetrics:
    """엔진 성과 지표"""
    total_operations: int = 0
    success_operations: int = 0
    error_operations: int = 0
    average_execution_time: float = 0.0
    last_execution_time: Optional[float] = None


class BaseEngine(ABC):
    """
    모든 엔진의 기본 클래스
    
    공통 인터페이스와 유틸리티 기능을 제공합니다.
    """
    
    def __init__(self, config: UnifiedConfig):
        """
        BaseEngine 초기화
        
        Args:
            config: 통합 설정 객체
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 상태 관리
        self.state = EngineState()
        self.metrics = EngineMetrics()
        
        # 이벤트 콜백
        self._event_callbacks: Dict[str, List[callable]] = {}
        
        self.logger.info(f"{self.__class__.__name__} initialized")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        엔진 초기화
        
        Returns:
            bool: 초기화 성공 여부
        """
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """
        엔진 시작
        
        Returns:
            bool: 시작 성공 여부
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        엔진 중지
        
        Returns:
            bool: 중지 성공 여부
        """
        pass
    
    @abstractmethod
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        엔진 실행 (Engine I/O Contract — ETEDA Evaluate/Decide/Act와 정합)

        Input Contract:
            data: Dict with required key "operation" (str); operation별 추가 키는 각 엔진 명세.

        Output Contract:
            성공: {"success": True, "data": <result>, "execution_time": float}
            실패: {"success": False, "error": str, "execution_time": float}
        """
        pass
    
    def register_event_callback(self, event_type: str, callback: callable) -> None:
        """
        이벤트 콜백 등록
        
        Args:
            event_type: 이벤트 타입
            callback: 콜백 함수
        """
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        
        self._event_callbacks[event_type].append(callback)
        self.logger.debug(f"Registered callback for event: {event_type}")
    
    def unregister_event_callback(self, event_type: str, callback: callable) -> None:
        """
        이벤트 콜백 등록 해제
        
        Args:
            event_type: 이벤트 타입
            callback: 콜백 함수
        """
        if event_type in self._event_callbacks:
            try:
                self._event_callbacks[event_type].remove(callback)
                self.logger.debug(f"Unregistered callback for event: {event_type}")
            except ValueError:
                pass
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        이벤트 발생
        
        Args:
            event_type: 이벤트 타입
            data: 이벤트 데이터
        """
        if event_type in self._event_callbacks:
            for callback in self._event_callbacks[event_type]:
                try:
                    await callback(data)
                except Exception as e:
                    self.logger.error(f"Error in event callback for {event_type}: {str(e)}")
    
    def _update_metrics(self, execution_time: float, success: bool) -> None:
        """
        성과 지표 업데이트
        
        Args:
            execution_time: 실행 시간
            success: 성공 여부
        """
        self.metrics.total_operations += 1
        self.metrics.last_execution_time = execution_time
        
        if success:
            self.metrics.success_operations += 1
        else:
            self.metrics.error_operations += 1
            self.state.error_count += 1
        
        # 평균 실행 시간 계산
        if self.metrics.total_operations > 0:
            total_time = sum([
                self.metrics.last_execution_time or 0.0
                for _ in range(self.metrics.total_operations)
            ])
            self.metrics.average_execution_time = total_time / self.metrics.total_operations
    
    def _update_state(self, is_running: bool, error: Optional[str] = None) -> None:
        """
        상태 업데이트
        
        Args:
            is_running: 실행 상태
            error: 에러 메시지
        """
        self.state.is_running = is_running
        self.state.last_updated = datetime.now()
        
        if error:
            self.state.last_error = error
    
    def _state_kind(self) -> str:
        """
        엔진 상태 종류 (Engine State Model — docs/arch/02_Engine_Core_Architecture.md §9).
        FAULT: Safety 연동·매매 중단 고려. WARNING: 경고 표시. OK: 정상.
        """
        if self.state.error_count >= 10:
            return "FAULT"
        if self.state.error_count >= 1:
            return "WARNING"
        return "OK"

    async def get_status(self) -> Dict[str, Any]:
        """
        엔진 상태 조회
        
        Returns:
            Dict[str, Any]: 상태 정보 (state_kind: OK | WARNING | FAULT)
        """
        return {
            'engine_type': self.__class__.__name__,
            'state_kind': self._state_kind(),
            'state': {
                'is_running': self.state.is_running,
                'last_updated': self.state.last_updated.isoformat() if self.state.last_updated else None,
                'error_count': self.state.error_count,
                'last_error': self.state.last_error
            },
            'metrics': {
                'total_operations': self.metrics.total_operations,
                'success_operations': self.metrics.success_operations,
                'error_operations': self.metrics.error_operations,
                'success_rate': (
                    self.metrics.success_operations / self.metrics.total_operations 
                    if self.metrics.total_operations > 0 else 0.0
                ),
                'average_execution_time': self.metrics.average_execution_time,
                'last_execution_time': self.metrics.last_execution_time
            },
            'config': {
                'config_map_size': len(self.config.config_map),
                'metadata_size': len(self.config.metadata)
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        헬스체크
        
        Returns:
            Dict[str, Any]: 헬스체크 결과
        """
        try:
            status = await self.get_status()
            
            # 기본 헬스체크 로직
            is_healthy = (
                self.state.error_count < 10 and  # 에러 횟수 기준
                self.metrics.average_execution_time < 5.0  # 응답 시간 기준
            )
            
            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'engine': self.__class__.__name__,
                'state_kind': self._state_kind(),
                'timestamp': datetime.now().isoformat(),
                'details': status
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'engine': self.__class__.__name__,
                'state_kind': 'FAULT',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
