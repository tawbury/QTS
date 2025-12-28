from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Union
from uuid import uuid4

from runtime.execution.models.intent import ExecutionIntent


JsonLike = Union[str, Mapping[str, Any], Dict[str, Any]]


@dataclass(frozen=True)
class OpsDecisionParseResult:
    """
    Parse result for ops decision payload.

    - intent: QTS ExecutionIntent
    - raw: original payload as dict (after normalization)
    """
    intent: ExecutionIntent
    raw: Dict[str, Any]


class OpsDecisionToIntentAdapter:
    """
    Adapter: ops decision output (black-box) -> QTS ExecutionIntent

    Constraints (Phase 1):
    - Must not import ops modules
    - Must accept dict or json string input
    - Must never assume brokerage/API fields
    """

    def from_payload(self, payload: JsonLike) -> OpsDecisionParseResult:
        raw = self._coerce_to_dict(payload)
        normalized = self._normalize_keys(raw)

        symbol = self._require_one(normalized, ["symbol", "ticker"])
        side = self._require_one(normalized, ["side"])
        quantity = self._require_one(normalized, ["quantity", "qty"])

        intent_type = self._optional_one(normalized, ["intent_type", "order_type"]) or "NOOP"

        # NOTE: Phase 1 safety: only allow BUY/SELL; anything else becomes NOOP
        side_norm = str(side).upper().strip()
        if side_norm not in ("BUY", "SELL"):
            side_norm = "BUY"  # default normalization target
            intent_type = "NOOP"

        qty = self._coerce_quantity(quantity)
        if qty <= 0:
            intent_type = "NOOP"

        intent = ExecutionIntent(
            intent_id=str(uuid4()),
            symbol=str(symbol).strip(),
            side=side_norm,
            quantity=float(qty),
            intent_type=str(intent_type).upper().strip(),
            metadata={
                "source": "ops",
                "ops_payload": normalized,
            },
        )
        return OpsDecisionParseResult(intent=intent, raw=normalized)

    # -------------------------
    # Internals
    # -------------------------

    def _coerce_to_dict(self, payload: JsonLike) -> Dict[str, Any]:
        if isinstance(payload, str):
            payload_str = payload.strip()
            if not payload_str:
                raise ValueError("ops payload is empty string")
            try:
                obj = json.loads(payload_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"ops payload is not valid JSON: {e}") from e
            if not isinstance(obj, dict):
                raise ValueError("ops payload JSON must be an object/dict")
            return obj

        if isinstance(payload, Mapping):
            return dict(payload)

        raise TypeError(f"unsupported payload type: {type(payload)!r}")

    def _normalize_keys(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize keys to snake_case-ish (very light) and lower.
        We do NOT attempt deep transformation; we only make keys comparable.
        """
        normalized: Dict[str, Any] = {}
        for k, v in raw.items():
            key = str(k).strip().lower()
            normalized[key] = v
        return normalized

    def _require_one(self, d: Dict[str, Any], keys: list[str]) -> Any:
        for k in keys:
            if k in d and d[k] is not None and str(d[k]).strip() != "":
                return d[k]
        raise KeyError(f"missing required key: one of {keys}")

    def _optional_one(self, d: Dict[str, Any], keys: list[str]) -> Any | None:
        for k in keys:
            if k in d and d[k] is not None and str(d[k]).strip() != "":
                return d[k]
        return None

    def _coerce_quantity(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"quantity must be numeric; got: {value!r}") from e
