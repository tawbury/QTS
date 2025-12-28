from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4

from paths import observer_data_dir

from src.ops.observer.inputs import (
    IMarketDataProvider,
    MarketDataContract,
)

from src.ops.observer.event_bus import EventBus
from src.ops.observer.observer import Observer
from src.ops.observer.snapshot import (
    ObservationSnapshot,
    build_snapshot,
)


class ObserverRunner:
    """
    ObserverRunner (Phase 10)

    - MarketDataProvider(Mock / Replay)를 받아 Observer를 실행한다.
    - Execution / Broker / Account와 완전 분리된 실행 루프.
    """

    def __init__(
        self,
        provider: IMarketDataProvider,
        *,
        interval_sec: float = 1.0,
        out_file: Optional[Path] = None,
        max_iterations: Optional[int] = None,
        mode: str = "observation",
        session_id: Optional[str] = None,
    ) -> None:
        self._provider = provider
        self._interval = interval_sec
        self._max_iterations = max_iterations

        self._session_id = session_id or str(uuid4())
        self._mode = mode

        self._out_file = out_file or (observer_data_dir() / "market_observation.jsonl")
        self._out_file.parent.mkdir(parents=True, exist_ok=True)

        # Observer는 구조 완성 및 계약 검증용으로만 존재
        self._observer = Observer(
            session_id=self._session_id,
            mode=self._mode,
            event_bus=EventBus(sinks=[]),
        )

    def run(self) -> None:
        iteration = 0

        with self._out_file.open("a", encoding="utf-8") as fp:
            while True:
                if self._max_iterations is not None and iteration >= self._max_iterations:
                    print("STOP: max_iterations reached")
                    break

                contract: Optional[MarketDataContract] = self._provider.fetch()
                print("FETCH RESULT:", contract)

                if contract is None:
                    print("STOP: provider returned None")
                    break

                snapshot = self._build_snapshot(contract)
                print("SNAPSHOT RESULT:", snapshot)

                if snapshot is None:
                    print("SKIP: snapshot is None")
                    time.sleep(self._interval)
                    continue

                # Phase 10: Snapshot 자체를 기록 단위로 사용
                record = snapshot.to_dict()
                print("RECORD RESULT:", record)

                fp.write(json.dumps(record, ensure_ascii=False) + "\n")
                fp.flush()

                iteration += 1
                time.sleep(self._interval)

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
                print("SNAPSHOT FAIL: instruments empty")
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

        except Exception as e:
            print("SNAPSHOT EXCEPTION:", e)
            return None
