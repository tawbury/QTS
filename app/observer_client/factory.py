"""
Observer Client Factory

설정에 따라 적절한 Observer Client 인스턴스를 생성합니다.
"""

import logging
from typing import Union

from .stub import StubObserverClient
from .uds_client import UDSObserverClient


logger = logging.getLogger("app.observer_client.factory")


ObserverClientType = Union[StubObserverClient, UDSObserverClient]


def create_observer_client(
    client_type: str = "stub", endpoint: str = None
) -> ObserverClientType:
    """
    Observer Client 인스턴스 생성

    Args:
        client_type: 클라이언트 타입 ("stub", "uds", "ipc")
        endpoint: 연결 엔드포인트 (UDS 소켓 경로 등)

    Returns:
        ObserverClientType: Observer Client 인스턴스

    Raises:
        ValueError: 지원하지 않는 client_type
    """
    logger.info(f"Creating Observer client: type={client_type}, endpoint={endpoint}")

    if client_type == "stub":
        return StubObserverClient()

    elif client_type == "uds":
        if not endpoint:
            raise ValueError("UDS client requires endpoint (socket path)")
        return UDSObserverClient(socket_path=endpoint)

    elif client_type == "ipc":
        raise NotImplementedError("IPC client not implemented yet")

    else:
        raise ValueError(
            f"Unsupported observer client type: {client_type}. "
            f"Supported types: stub, uds, ipc"
        )
