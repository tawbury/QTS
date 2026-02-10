import asyncio
import json
import logging
import os
import tempfile
import pytest
from src.observer_client.uds_client import UDSObserverClient

# Logging setup for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MockUDSServer:
    def __init__(self, socket_path):
        self.socket_path = socket_path
        self.server = None
        self.clients = []
        self.received_messages = []

    async def start(self):
        self.server = await asyncio.start_unix_server(
            self.handle_client, self.socket_path
        )
        logger.info(f"Mock Server started on {self.socket_path}")

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        # Close client connections
        for writer in self.clients:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

    async def handle_client(self, reader, writer):
        self.clients.append(writer)
        try:
            while not reader.at_eof():
                data = await reader.readline()
                if not data:
                    break
                message = data.decode().strip()
                if message:
                    self.received_messages.append(json.loads(message))
        except Exception as e:
            logger.error(f"Server handle error: {e}")

    async def broadcast(self, message: dict):
        data = json.dumps(message).encode() + b"\n"
        for writer in self.clients:
            try:
                writer.write(data)
                await writer.drain()
            except Exception:
                pass

@pytest.fixture
async def mock_server():
    # Create a temp socket path
    with tempfile.TemporaryDirectory() as tmpdir:
        socket_path = os.path.join(tmpdir, "test_observer.sock")
        server = MockUDSServer(socket_path)
        await server.start()
        yield server
        await server.stop()

@pytest.mark.asyncio
async def test_uds_client_full_flow(mock_server):
    """Test connection, subscription and snapshot in one flow to avoid fixture overhead"""
    client = UDSObserverClient(socket_path=mock_server.socket_path)
    
    # 1. Connect
    connected = await asyncio.wait_for(client.connect(), timeout=1.0)
    assert connected is True
    assert await client.is_connected() is True
    
    # 2. Subscribe
    symbols = ["005930"]
    await client.subscribe(symbols)
    
    # Wait for server to process
    await asyncio.sleep(0.5)
    assert len(mock_server.received_messages) > 0
    assert mock_server.received_messages[0]["type"] == "SUBSCRIBE"
    
    # 3. Snapshot
    snapshot_payload = {
        "type": "SNAPSHOT",
        "payload": {
            "symbol": "005930",
            "price": 70000
        }
    }
    await mock_server.broadcast(snapshot_payload)
    
    # 4. Receive
    received = await asyncio.wait_for(client.get_next_snapshot(), timeout=1.0)
    assert received["symbol"] == "005930"
    assert received["price"] == 70000
    
    # 5. Disconnect
    await client.disconnect()
    assert await client.is_connected() is False
