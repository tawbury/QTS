from __future__ import annotations

import time
from typing import Optional
from uuid import uuid4

from ops.observer.inputs import (
    IMarketDataProvider,
    MarketDataContract,
)
from ops.observer.event_bus import EventBus, JsonlFileSink
from ops.observer.observer import Observer
from ops.observer.snapshot import (
    ObservationSnapshot,
    build_snapshot,
)


class ObserverRunner:
    """
    ObserverRunner (Phase F)

    - MarketDataProvider(Mock / Replay)를 받아 Observer를 실행한다.
    - Observer 출력은 EventBus + Sink를 통해서만 이루어진다.
    - Runner는 파일 경로를 알지 못한다.
    """

    def __init__(
        self,
        provider: IMarketDataProvider,
        *,
        interval_sec: float = 1.0,
        max_iterations: Optional[int] = None,
        mode: str = "observation",
        session_id: Optional[str] = None,
        sink_filename: str = "market_observation.jsonl",
    ) -> None:
        self._provider = provider
        self._interval = interval_sec
        self._max_iterations = max_iterations

        self._session_id = session_id or str(uuid4())
        self._mode = mode

        sink = JsonlFileSink(sink_filename)
        bus = EventBus(sinks=[sink])

        self._observer = Observer(
            session_id=self._session_id,
            mode=self._mode,
            event_bus=bus,
        )

    def run(self) -> None:
        iteration = 0

        self._observer.start()

        try:
            while True:
                if self._max_iterations is not None and iteration >= self._max_iterations:
                    break

                contract: Optional[MarketDataContract] = self._provider.fetch()

                if contract is None:
                    break

                snapshot = self._build_snapshot(contract)
                if snapshot is None:
                    time.sleep(self._interval)
                    continue

                self._observer.on_snapshot(snapshot)

                iteration += 1
                time.sleep(self._interval)

        finally:
            self._observer.stop()
            try:
                self._provider.close()
            except Exception:
                pass

    def _build_snapshot(
        self, contract: MarketDataContract
    ) -> Optional[ObservationSnapshot]:
        try:
            meta = contract.get("meta", {})
            instruments = contract.get("instruments", [])

            if not instruments:
                return None

            inst = instruments[0]

            inputs = {
                "price": {
                    "open": inst["price"]["open"],
                    "high": inst["price"]["high"],
                    "low": inst["price"]["low"],
                    "close": inst["price"]["close"],
                },
                "volume": inst["volume"],
                "timestamp": inst["timestamp"],
            }

            return build_snapshot(
                session_id=self._session_id,
                mode=self._mode,
                source=meta.get("source", "market"),
                stage="raw",
                inputs=inputs,
                computed={},
                state={},
                symbol=inst.get("symbol"),
                market=meta.get("market"),
            )

        except Exception:
            return None
