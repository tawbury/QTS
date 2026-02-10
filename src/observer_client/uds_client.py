"""
UDS Observer Client

Unix Domain Socket 기반 Observer Client 구현입니다.
Observer Server(외부 프로세스)와 UDS로 통신하여 실시간 시장 데이터를 수신합니다.
"""

import asyncio
import json
import logging
from typing import Optional, List, Dict, Any, AsyncIterator

from .interfaces import ObserverClient, MarketSnapshot


logger = logging.getLogger("src.observer_client.uds")


class UDSObserverClient:
    """Unix Domain Socket 기반 Observer 클라이언트"""

    def __init__(self, socket_path: str = "/var/run/observer.sock"):
        """
        Args:
            socket_path: UDS 소켓 경로
        """
        self._socket_path = socket_path
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        
        # 데이터 수신용 큐 (get_next_snapshot에서 소모)
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        
        # 백그라운드 리스너 태스크
        self._listener_task: Optional[asyncio.Task] = None

        logger.info(f"UDSObserverClient initialized with socket={socket_path}")

    async def connect(self) -> bool:
        """
        Observer에 UDS 연결 및 리스너 시작

        Returns:
            bool: 연결 성공 여부
        """
        try:
            logger.info(f"Connecting to Observer via UDS: {self._socket_path}")
            self._reader, self._writer = await asyncio.open_unix_connection(
                self._socket_path
            )
            self._connected = True
            
            # 리스너 시작
            self._listener_task = asyncio.create_task(self._listen())
            
            logger.info("Connected to Observer via UDS")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Observer via UDS: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Observer 연결 해제 및 리소스 정리"""
        self._connected = False
        
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None
            
        if self._writer:
            logger.info("Disconnecting from Observer via UDS")
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self._writer = None
                self._reader = None
                
        logger.info("Disconnected from Observer via UDS")

    async def _listen(self) -> None:
        """UDS 데이터 수신 루프 (Background)"""
        if not self._reader:
            return
            
        logger.info("UDS Listener started")
        try:
            while self._connected and not self._reader.at_eof():
                # Line-based JSON protocol assumption
                line = await self._reader.readline()
                if not line:
                    break
                    
                line_str = line.decode().strip()
                if not line_str:
                    continue
                    
                try:
                    data = json.loads(line_str)
                    # 스냅샷 데이터인 경우 큐에 추가
                    # Protocol: {"type": "SNAPSHOT", "payload": {...}} or just {...}
                    # 여기서는 간단히 전체 데이터를 큐에 넣고 get_next_snapshot에서 처리
                    await self._queue.put(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON/Message received: {line_str[:100]}")
                    
        except asyncio.CancelledError:
            logger.debug("UDS Listener cancelled")
            raise
        except Exception as e:
            logger.error(f"UDS Listener error: {e}")
            self._connected = False
        finally:
            logger.info("UDS Listener stopped")

    async def subscribe(self, symbols: List[str]) -> bool:
        """
        종목 구독 요청 전달

        Args:
            symbols: 구독할 종목 코드 리스트

        Returns:
            bool: 구독 요청 전송 성공 여부
        """
        if not self._connected or not self._writer:
            logger.error("Not connected to Observer")
            return False

        try:
            msg = {
                "type": "SUBSCRIBE",
                "symbols": symbols
            }
            data = json.dumps(msg).encode() + b"\n"
            self._writer.write(data)
            await self._writer.drain()
            logger.info(f"Sent SUBSCRIBE request for {len(symbols)} symbols")
            return True
        except Exception as e:
            logger.error(f"Failed to send SUBSCRIBE request: {e}")
            return False

    async def unsubscribe(self, symbols: List[str]) -> bool:
        """
        종목 구독 해제 요청 전달

        Args:
            symbols: 구독 해제할 종목 코드 리스트

        Returns:
            bool: 요청 전송 성공 여부
        """
        if not self._connected or not self._writer:
            logger.error("Not connected to Observer")
            return False

        try:
            msg = {
                "type": "UNSUBSCRIBE",
                "symbols": symbols
            }
            data = json.dumps(msg).encode() + b"\n"
            self._writer.write(data)
            await self._writer.drain()
            logger.info(f"Sent UNSUBSCRIBE request for {len(symbols)} symbols")
            return True
        except Exception as e:
            logger.error(f"Failed to send UNSUBSCRIBE request: {e}")
            return False

    async def get_next_snapshot(self) -> Dict[str, Any]:
        """
        ETEDA Loop용 스냅샷 Provider.
        수신 큐에서 다음 메시지를 꺼내 반환합니다.

        Returns:
            Dict[str, Any]: 스냅샷 데이터
        """
        if not self._connected:
            raise ConnectionError("UDSObserverClient not connected")
            
        # 큐에서 대기 (Loop는 여기서 블로킹됨)
        data = await self._queue.get()
        
        # 데이터 포맷 정규화 (필요 시)
        # Observer가 보내는 데이터가 ETEDA Snapshot 포맷이 아니면 매핑 필요.
        # 일단은 그대로 반환하거나 간단한 매핑 적용.
        # 만약 type="SNAPSHOT" 래퍼가 있다면 payload만 추출.
        if data.get("type") == "SNAPSHOT" and "payload" in data:
            return data["payload"]
            
        return data

    async def get_snapshot(self, symbol: str) -> Optional[MarketSnapshot]:
        """
        특정 종목의 스냅샷 조회 (Interface 구현)
        
        Note: 현재 구현은 스트리밍 방식(get_next_snapshot)에 최적화되어 있습니다.
        이 메서드는 UDS에 명시적 요청을 보내거나 캐시를 조회해야 하지만,
        ETEDA Loop에서는 사용되지 않으므로 현재는 미구현 상태로 둡니다.
        """
        # TODO: Implement synchronous request via UDS or lookup local cache
        logger.warning("UDS get_snapshot(symbol) is not fully implemented yet.")
        return None

    async def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._connected
