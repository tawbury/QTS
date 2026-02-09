from __future__ import annotations

"""
runtime.broker.base

Phase 2 Contract (Enforcing via Phase 2 Guide)

Purpose:
- Define the BrokerAdapter interface as the single contract between:
  - Broker Adapter (stateless)
  - Runtime (state manager)

Hard constraints (Phase 2):
- Adapter MUST be stateless: no token cache, no persistence.
- Runtime MUST be stateful: stores tokens, tracks expiry, triggers re-auth.
- This module must NOT import runtime.auth.token_cache or any state manager.

Notes:
- Phase 2 focuses on authentication only (KIS OAuth2 token).
- Execution / strategy / ops responsibilities are explicitly excluded.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional

from src.shared.timezone_utils import now_kst


# =========================
# Exceptions (Contract-level)
# =========================

class BrokerAuthError(RuntimeError):
    """Raised when broker authentication fails (network/response/validation)."""


class BrokerConfigError(ValueError):
    """Raised when required configuration (.env / settings) is missing or invalid."""


# =========================
# Token Payload (Adapter -> Runtime)
# =========================

@dataclass(frozen=True, slots=True)
class AccessTokenPayload:
    """
    Adapter output payload. Runtime owns caching and expiry management.

    Minimal fields:
    - access_token: the bearer token string
    - token_type: typically "Bearer"
    - expires_in: seconds until expiry (as reported by broker)
    - issued_at: timestamp created at adapter side (KST)

    Optional:
    - scope: broker-provided scope string
    - raw: raw response for diagnostics (must NOT include sensitive secrets beyond token)
    """
    access_token: str
    token_type: str
    expires_in: int
    issued_at: datetime

    scope: Optional[str] = None
    raw: Optional[Mapping[str, Any]] = None

    def expires_at(self) -> datetime:
        """Compute expiry timestamp from issued_at + expires_in."""
        return self.issued_at + timedelta_seconds(self.expires_in)

    @staticmethod
    def now_kst() -> datetime:
        return now_kst()


def timedelta_seconds(seconds: int):
    # Local helper to avoid importing timedelta at module top if you prefer.
    # Kept explicit for clarity.
    from datetime import timedelta
    return timedelta(seconds=seconds)


# =========================
# Broker Adapter Interface (Stateless)
# =========================

class BrokerAdapter(ABC):
    """
    Stateless broker adapter contract.

    Responsibilities (Phase 2):
    - Read MODE and auth settings (typically from env/config passed in)
    - Perform authentication request
    - Return AccessTokenPayload
    """

    @property
    @abstractmethod
    def broker_name(self) -> str:
        """Human-readable broker identifier (e.g., 'KIS')."""

    @abstractmethod
    def authenticate(self) -> AccessTokenPayload:
        """
        Perform broker authentication and return an access token payload.

        MUST:
        - be stateless (no caching)
        - raise BrokerAuthError / BrokerConfigError on failure
        - return AccessTokenPayload with issued_at in KST
        """
        raise NotImplementedError
