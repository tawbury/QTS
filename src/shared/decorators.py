"""
공통 데코레이터 모듈.

이 모듈은 ops와 runtime 양쪽에서 사용되는 공통 데코레이터를 제공합니다.

Decorators:
    retry: 재시도 데코레이터
    log_execution: 실행 로깅 데코레이터
    deprecated: 사용 중단 경고 데코레이터
"""
from __future__ import annotations

import functools
import logging
import time
import warnings
from typing import Any, Callable, Optional, Type, TypeVar, Union

F = TypeVar("F", bound=Callable[..., Any])

_log = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """
    재시도 데코레이터.

    지정된 예외 발생 시 함수를 재시도합니다.

    Args:
        max_attempts: 최대 시도 횟수 (기본 3)
        delay: 초기 대기 시간 (초, 기본 1.0)
        backoff: 대기 시간 배수 (기본 2.0)
        exceptions: 재시도할 예외 타입들

    Example:
        @retry(max_attempts=5, delay=0.5)
        def fetch_data():
            return api_call()
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        _log.warning(
                            "Attempt %d/%d failed for %s: %s. Retrying in %.1fs...",
                            attempt, max_attempts, func.__name__, e, current_delay
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        _log.error(
                            "All %d attempts failed for %s",
                            max_attempts, func.__name__
                        )

            if last_exception is not None:
                raise last_exception

        return wrapper  # type: ignore
    return decorator


def log_execution(
    level: int = logging.DEBUG,
    include_args: bool = False,
    include_result: bool = False,
) -> Callable[[F], F]:
    """
    실행 로깅 데코레이터.

    함수 실행 시작/종료를 로깅합니다.

    Args:
        level: 로그 레벨 (기본 DEBUG)
        include_args: 인자 포함 여부
        include_result: 결과 포함 여부

    Example:
        @log_execution(level=logging.INFO, include_args=True)
        def process_data(data):
            return transform(data)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = func.__qualname__

            if include_args:
                _log.log(level, "Executing %s with args=%s kwargs=%s", func_name, args, kwargs)
            else:
                _log.log(level, "Executing %s", func_name)

            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time

                if include_result:
                    _log.log(level, "Completed %s in %.3fs with result=%s", func_name, elapsed, result)
                else:
                    _log.log(level, "Completed %s in %.3fs", func_name, elapsed)

                return result
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                _log.log(level, "Failed %s in %.3fs with error: %s", func_name, elapsed, e)
                raise

        return wrapper  # type: ignore
    return decorator


def deprecated(
    reason: str = "",
    replacement: Optional[str] = None,
    version: Optional[str] = None,
) -> Callable[[F], F]:
    """
    사용 중단 경고 데코레이터.

    함수 호출 시 DeprecationWarning을 발생시킵니다.

    Args:
        reason: 사용 중단 이유
        replacement: 대체 함수/모듈
        version: 제거 예정 버전

    Example:
        @deprecated(reason="성능 이슈", replacement="new_function", version="2.0")
        def old_function():
            pass
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            message_parts = [f"{func.__qualname__} is deprecated"]

            if reason:
                message_parts.append(f": {reason}")
            if replacement:
                message_parts.append(f". Use {replacement} instead")
            if version:
                message_parts.append(f". Will be removed in version {version}")

            message = "".join(message_parts)
            warnings.warn(message, DeprecationWarning, stacklevel=2)

            return func(*args, **kwargs)

        return wrapper  # type: ignore
    return decorator
