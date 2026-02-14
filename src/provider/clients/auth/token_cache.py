"""
runtime.auth.token_cache

Phase 2 Runtime Token Cache (state manager)

Responsibilities:
- Store access token state
- Track expiry
- Decide refresh necessity (but DO NOT perform refresh)
- Provide token injection utility for API calls (Phase 2: token retrieval only)

Hard constraints (Phase 2):
- Must NOT import broker adapters (no runtime.broker.*)
- Must NOT manage auth request parameters
- Must NOT perform HTTP requests
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional

from src.shared.timezone_utils import now_kst


@dataclass(frozen=True, slots=True)
class TokenState:
    access_token: str
    token_type: str
    expires_at: datetime
    scope: Optional[str] = None
    updated_at: datetime = field(default_factory=now_kst)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        now = now or now_kst()
        return now >= self.expires_at

    def will_expire_within(self, seconds: int, now: Optional[datetime] = None) -> bool:
        if seconds < 0:
            raise ValueError("seconds must be >= 0")
        now = now or now_kst()
        return now + timedelta(seconds=seconds) >= self.expires_at


class TokenCache:
    """
    In-memory token cache.

    Notes:
- Phase 2 scope: in-memory only
- If persistence is required later, it must be introduced as a separate module
  without changing this contract (Phase 3+).
    """

    def __init__(self, refresh_skew_seconds: int = 30) -> None:
        if refresh_skew_seconds < 0:
            raise ValueError("refresh_skew_seconds must be >= 0")
        self._refresh_skew_seconds = refresh_skew_seconds
        self._lock = Lock()
        self._state: Optional[TokenState] = None

    @property
    def refresh_skew_seconds(self) -> int:
        return self._refresh_skew_seconds

    def get_state(self) -> Optional[TokenState]:
        with self._lock:
            return self._state

    def clear(self) -> None:
        with self._lock:
            self._state = None

    def update(
        self,
        *,
        access_token: str,
        token_type: str,
        expires_at: datetime,
        scope: Optional[str] = None,
        updated_at: Optional[datetime] = None,
    ) -> TokenState:
        if not access_token:
            raise ValueError("access_token is required")
        if not token_type:
            raise ValueError("token_type is required")
        if expires_at.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware (KST recommended)")

        updated_at = updated_at or now_kst()
        if updated_at.tzinfo is None:
            raise ValueError("updated_at must be timezone-aware")

        state = TokenState(
            access_token=access_token,
            token_type=token_type,
            expires_at=expires_at,
            scope=scope,
            updated_at=updated_at,
        )
        with self._lock:
            self._state = state
        return state

    def update_from_payload(
        self,
        *,
        access_token: str,
        token_type: str,
        expires_in: int,
        issued_at: datetime,
        scope: Optional[str] = None,
    ) -> TokenState:
        if expires_in <= 0:
            raise ValueError("expires_in must be > 0")
        if issued_at.tzinfo is None:
            raise ValueError("issued_at must be timezone-aware (KST recommended)")

        expires_at = issued_at + timedelta(seconds=expires_in)
        return self.update(
            access_token=access_token,
            token_type=token_type,
            expires_at=expires_at,
            scope=scope,
            updated_at=now_kst(),
        )

    def needs_refresh(self, now: Optional[datetime] = None) -> bool:
        """
        Returns True if:
- no token exists OR
- token expired OR
- token will expire within refresh_skew_seconds
        """
        now = now or now_kst()
        with self._lock:
            state = self._state

        if state is None:
            return True
        if state.is_expired(now):
            return True
        return state.will_expire_within(self._refresh_skew_seconds, now)

    def get_valid_token(self, now: Optional[datetime] = None) -> str:
        """
        Return a token string that is safe to use.
        Raises RuntimeError if refresh is needed.
        """
        now = now or now_kst()
        with self._lock:
            state = self._state

        if state is None:
            raise RuntimeError("No token in cache (refresh required)")
        if state.is_expired(now):
            raise RuntimeError("Token expired (refresh required)")
        if state.will_expire_within(self._refresh_skew_seconds, now):
            raise RuntimeError("Token near expiry (refresh required)")
        return state.access_token

    def get_authorization_header(self, now: Optional[datetime] = None) -> str:
        """
        Convenience: returns 'Bearer <token>' style header value.
        """
        now = now or now_kst()
        with self._lock:
            state = self._state

        if state is None:
            raise RuntimeError("No token in cache (refresh required)")
        token = self.get_valid_token(now=now)
        return f"{state.token_type} {token}"
