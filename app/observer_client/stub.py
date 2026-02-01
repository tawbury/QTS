"""
Stub Observer Client

개발 및 테스트용 Observer Client 구현입니다.
실제 Observer 연동 없이 Mock 데이터를 반환합니다.
"""

import random
import logging
from typing import Optional, List
from datetime import datetime

from .interfaces import ObserverClient, MarketSnapshot
from shared.timezone_utils import get_kst_now


logger = logging.getLogger("app.observer_client.stub")


class StubObserverClient:
    """개발/테스트용 Stub Observer Client"""

    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: 랜덤 시드 (테스트 재현성 위해)
        """
        self._connected = False
        self._subscribed_symbols: List[str] = []
        if seed is not None:
            random.seed(seed)

        logger.info("StubObserverClient initialized")

    async def connect(self) -> bool:
        """Stub 연결 (항상 성공)"""
        logger.info("StubObserverClient.connect() called")
        self._connected = True
        return True

    async def disconnect(self) -> None:
        """Stub 연결 해제"""
        logger.info("StubObserverClient.disconnect() called")
        self._connected = False
        self._subscribed_symbols.clear()

    async def subscribe(self, symbols: List[str]) -> bool:
        """
        종목 구독 (Mock)

        Args:
            symbols: 구독할 종목 코드 리스트

        Returns:
            bool: 항상 True
        """
        logger.info(f"StubObserverClient.subscribe({symbols}) called")
        self._subscribed_symbols.extend(symbols)
        return True

    async def unsubscribe(self, symbols: List[str]) -> bool:
        """
        종목 구독 해제 (Mock)

        Args:
            symbols: 구독 해제할 종목 코드 리스트

        Returns:
            bool: 항상 True
        """
        logger.info(f"StubObserverClient.unsubscribe({symbols}) called")
        for symbol in symbols:
            if symbol in self._subscribed_symbols:
                self._subscribed_symbols.remove(symbol)
        return True

    async def get_snapshot(self, symbol: str) -> Optional[MarketSnapshot]:
        """
        Mock 스냅샷 반환

        Args:
            symbol: 종목 코드

        Returns:
            MarketSnapshot: Mock 데이터
        """
        if not self._connected:
            logger.warning(f"Not connected. Cannot get snapshot for {symbol}")
            return None

        # Mock 데이터 생성
        base_price = random.uniform(50000, 100000)
        spread = base_price * 0.001  # 0.1% spread

        snapshot = MarketSnapshot(
            symbol=symbol,
            price=base_price,
            volume=random.randint(1000, 10000),
            timestamp=get_kst_now(),
            bid_price=base_price - spread / 2,
            ask_price=base_price + spread / 2,
            bid_volume=random.randint(100, 1000),
            ask_volume=random.randint(100, 1000),
        )

        logger.debug(f"Generated mock snapshot for {symbol}: {snapshot.price}")
        return snapshot

    async def is_connected(self) -> bool:
        """
        연결 상태 반환

        Returns:
            bool: 연결 여부
        """
        return self._connected
