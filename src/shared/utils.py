"""
공통 유틸리티 함수 모듈.

이 모듈은 ops와 runtime 양쪽에서 사용되는 공통 유틸리티를 제공합니다.

Functions:
    require_env: 필수 환경 변수 로드 (없으면 예외)
    get_env: 환경 변수 로드 (기본값 지원)
    safe_get: 딕셔너리에서 안전하게 값 추출
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional, TypeVar

T = TypeVar("T")


class EnvironmentError(Exception):
    """환경 변수 관련 예외."""
    pass


def require_env(key: str, description: Optional[str] = None) -> str:
    """
    필수 환경 변수를 로드합니다.

    Args:
        key: 환경 변수 키
        description: 변수 설명 (에러 메시지용)

    Returns:
        환경 변수 값

    Raises:
        EnvironmentError: 환경 변수가 설정되지 않은 경우

    Example:
        api_key = require_env("API_KEY", "API 인증 키")
    """
    value = os.getenv(key)
    if value is None:
        desc = f" ({description})" if description else ""
        raise EnvironmentError(f"Required environment variable '{key}'{desc} is not set")
    return value


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    환경 변수를 로드합니다.

    Args:
        key: 환경 변수 키
        default: 기본값 (환경 변수가 없을 경우)

    Returns:
        환경 변수 값 또는 기본값
    """
    return os.getenv(key, default)


def safe_get(
    data: Dict[str, Any],
    key: str,
    default: T = None,
) -> Any:
    """
    딕셔너리에서 안전하게 값을 추출합니다.

    Args:
        data: 딕셔너리
        key: 키
        default: 기본값

    Returns:
        값 또는 기본값

    Example:
        value = safe_get(config, "timeout", 30)
    """
    if data is None:
        return default
    return data.get(key, default)


def coalesce(*values: Optional[T]) -> Optional[T]:
    """
    첫 번째 None이 아닌 값을 반환합니다.

    Args:
        *values: 검사할 값들

    Returns:
        첫 번째 None이 아닌 값 또는 None

    Example:
        result = coalesce(None, None, "default")  # "default"
    """
    for v in values:
        if v is not None:
            return v
    return None


def is_truthy(value: Optional[str]) -> bool:
    """
    문자열 값이 truthy인지 확인합니다.

    Truthy values: "1", "true", "yes", "on", "y" (대소문자 무관)

    Args:
        value: 검사할 문자열

    Returns:
        truthy 여부

    Example:
        if is_truthy(os.getenv("FEATURE_ENABLED")):
            enable_feature()
    """
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}
