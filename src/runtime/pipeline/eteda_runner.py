from __future__ import annotations

import logging
from typing import Any, Dict


class ETEDARunner:
    """
    ETEDA Pipeline Runner
    - Act 단계는 절대 실행되지 않는다
    """

    def __init__(self, observer: Any) -> None:
        self._log = logging.getLogger("ETEDARunner")
        self._observer = observer

    def run_once(self, context: Any) -> Dict[str, Any]:
        if context.runtime_flags.get("execution_enabled", False):
            raise RuntimeError("Execution (Act) is forbidden")

        raw = self._extract()
        transformed = self._transform(raw)
        evaluated = self._evaluate(transformed)
        decision = self._decide(evaluated)

        self._observer.emit("pipeline.decision", decision)

        snapshot = self._observer.snapshot(
            "pipeline.snapshot",
            {
                "raw": raw,
                "transformed": transformed,
                "evaluated": evaluated,
                "decision": decision,
            },
        )

        return snapshot

    def _extract(self) -> Dict[str, Any]:
        self._log.info("ETEDA.Extract")
        return {"symbol": "DUMMY", "price": 100.0}

    def _transform(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        self._log.info("ETEDA.Transform")
        return {
            "symbol": raw["symbol"],
            "price": raw["price"],
            "bucket": "HIGH" if raw["price"] >= 100 else "LOW",
        }

    def _evaluate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._log.info("ETEDA.Evaluate")
        return {
            "symbol": data["symbol"],
            "signal": "BUY" if data["bucket"] == "HIGH" else "HOLD",
        }

    def _decide(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        self._log.info("ETEDA.Decide")
        return {
            "symbol": evaluation["symbol"],
            "decision": evaluation["signal"],
            "act": "FORBIDDEN",
        }
