"""
Observer Client Interfaces

이 모듈은 Observer 시스템과의 연동을 위한 추상 인터페이스를 정의합니다.
실제 구현체는 stub.py (개발/테스트), uds_client.py (UDS), ipc_client.py (IPC)입니다.
"""

from typing import Protocol, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketSnapshot:
    """시장 스냅샷 데이터"""

    symbol: str
    price: float
    volume: int
    timestamp: datetime
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    bid_volume: Optional[int] = None
    ask_volume: Optional[int] = None


class ObserverClient(Protocol):
    """Observer 연동 인터페이스"""

    async def connect(self) -> bool:
        """
        Observer에 연결

        Returns:
            bool: 연결 성공 여부
        """
        ...

    async def disconnect(self) -> None:
        """Observer 연결 해제"""
        ...

    async def subscribe(self, symbols: List[str]) -> bool:
        """
        종목 구독

        Args:
            symbols: 구독할 종목 코드 리스트

        Returns:
            bool: 구독 성공 여부
        """
        ...

    async def unsubscribe(self, symbols: List[str]) -> bool:
        """
        종목 구독 해제

        Args:
            symbols: 구독 해제할 종목 코드 리스트

        Returns:
            bool: 구독 해제 성공 여부
        """
        ...

    async def get_snapshot(self, symbol: str) -> Optional[MarketSnapshot]:
        """
        특정 종목의 현재 스냅샷 조회

        Args:
            symbol: 종목 코드

        Returns:
            Optional[MarketSnapshot]: 스냅샷 데이터 (실패 시 None)
        """
        ...

    async def is_connected(self) -> bool:
        """
        연결 상태 확인

        Returns:
            bool: 연결 여부
        """
        ...
