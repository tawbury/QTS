"""
File Observer Client

Observer가 생성한 JSONL 파일을 읽어 스트리밍하는 클라이언트입니다.
로컬 테스트 및 백테스팅 용도로 사용됩니다.
"""

import asyncio
import glob
import json
import logging
import os
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from shared.timezone_utils import get_kst_now

logger = logging.getLogger("app.observer_client.file")


class FileObserverClient:
    """
    JSONL 파일 기반 Observer Client
    
    지정된 디렉토리의 JSONL 파일을 모니터링하고 읽어서 
    ETEDA 파이프라인에 공급할 스냅샷 형태로 변환합니다.
    """

    def __init__(self, assets_dir: str, scope: str = "scalp"):
        """
        Args:
            assets_dir: Observer 데이터 디렉토리 경로
            scope: 모니터링할 전략 범위 (scalp, swing)
        """
        self.assets_dir = Path(assets_dir)
        self.scope = scope
        self._connected = False
        self._generator: Optional[AsyncIterator[Dict[str, Any]]] = None
        
        logger.info(f"FileObserverClient initialized: {assets_dir} (scope={scope})")

    async def connect(self) -> bool:
        """연결 (파일 확인)"""
        if not self.assets_dir.exists():
            logger.error(f"Assets directory not found: {self.assets_dir}")
            return False
            
        self._connected = True
        # 제너레이터 초기화
        self._generator = self._create_snapshot_generator()
        logger.info("FileObserverClient connected (ready to read files)")
        return True

    async def disconnect(self) -> None:
        self._connected = False
        self._generator = None
        logger.info("FileObserverClient disconnected")

    async def get_next_snapshot(self) -> Dict[str, Any]:
        """
        다음 스냅샷 반환 (ETEDA Loop용)
        데이터가 없으면 대기하거나 종료 신호를 보낼 수 있음
        """
        if not self._connected or not self._generator:
            raise ConnectionError("FileObserverClient not connected")

        try:
            return await self._generator.__anext__()
        except StopAsyncIteration:
            # 루프 종료를 위해 특별한 시그널을 보내거나, 잠시 대기 후 재시도 등 정책 결정
            # 여기서는 빈 딕셔너리나 None을 반환하지 않고, 
            # 계속 기다리거나 종료를 유도해야 함.
            # 테스트 목적이므로 잠시 대기 후 다시 시도하지 않고 종료 에러 발생
            logger.info("No more data in files.")
            await asyncio.sleep(1) # 과도한 루프 방지
            raise StopAsyncIteration

    async def _create_snapshot_generator(self) -> AsyncIterator[Dict[str, Any]]:
        """JSONL 파일을 읽어 스냅샷을 생성하는 제너레이터"""
        target_dir = self.assets_dir / self.scope
        pattern = str(target_dir / "*.jsonl")
        
        # 파일 목록 대기 (테스트 환경에서 파일 생성 시간 고려)
        retries = 30
        files = []
        while retries > 0:
            files = glob.glob(pattern)
            if files:
                break
            logger.info(f"Waiting for .jsonl files in {target_dir}...")
            await asyncio.sleep(1)
            retries -= 1
            
        if not files:
            logger.warning(f"No jsonl files found in {target_dir} after waiting")
            return

        logger.info(f"Found {len(files)} files. Starting processing.")
        
        # 간단하게 첫 번째 파일부터 순차 처리 (혹은 최신 파일)
        # 테스트 데이터는 보통 하나 또는 소수
        for file_path in sorted(files):
            logger.info(f"Processing file: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            snapshot = self._map_to_snapshot(data)
                            if snapshot:
                                yield snapshot
                            # 너무 빠른 처리를 방지하기 위해 약간의 딜레이 (선택사항)
                            # await asyncio.sleep(0.01) 
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in {file_path}: {line[:50]}...")
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")

    def _map_to_snapshot(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Observer 데이터를 ETEDA Snapshot 구조로 변환
        
        Observer Data (Example):
        {
            "symbol": "005930",
            "price": 70000,
            "volume": 100,
            "timestamp": "2024-01-01T09:00:00"
        }
        
        Target Snapshot:
        {
            "trigger": "observer_file",
            "observation": {
                 "inputs": { "price": ..., "volume": ... }
            },
            "context": { "symbol": ... },
            "meta": { "timestamp_ms": ... }
        }
        """
        try:
            symbol = data.get("symbol") or data.get("code")
            # Support various price field names from different sources (observer, kiwoom, etc)
            price = data.get("price") or data.get("trade_price") or data.get("current_price") or data.get("close")
            
            if not symbol:
                # logger.debug(f"Skipping line without symbol: {data.keys()}")
                return None
                
            if price is None:
                # logger.debug(f"Skipping line without price: {symbol} {data.keys()}")
                return None
                
            return {
                "trigger": "observer_file",
                "observation": {
                    "inputs": {
                        "price": float(price),
                        "volume": float(data.get("volume", 0) or data.get("trade_volume", 0))
                    }
                },
                "context": {
                    "symbol": symbol
                },
                "meta": {
                    "timestamp": data.get("timestamp"), # ISO String expected
                    "timestamp_ms": 0 # TODO: Parse timestamp if needed
                }
            }
        except Exception as e:
            logger.warning(f"Mapping error: {e}")
            return None
