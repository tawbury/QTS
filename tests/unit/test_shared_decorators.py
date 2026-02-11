"""
src/shared/decorators.py 단위 테스트.

테스트 대상:
- retry: 재시도 데코레이터
- log_execution: 실행 로깅 데코레이터
- deprecated: 사용 중단 경고 데코레이터
"""
import warnings
import pytest
from unittest.mock import patch
from src.shared.decorators import retry, log_execution, deprecated


class TestRetry:
    """retry 데코레이터 테스트."""

    def test_success_no_retry(self):
        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert succeed() == "ok"
        assert call_count == 1

    def test_retries_on_failure_then_succeeds(self):
        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        assert fail_twice() == "ok"
        assert call_count == 3

    def test_raises_after_max_attempts(self):
        @retry(max_attempts=2, delay=0.01)
        def always_fail():
            raise RuntimeError("always")

        with pytest.raises(RuntimeError, match="always"):
            always_fail()

    def test_only_catches_specified_exceptions(self):
        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def raise_type_error():
            raise TypeError("wrong type")

        with pytest.raises(TypeError):
            raise_type_error()

    def test_preserves_function_name(self):
        @retry()
        def my_func():
            pass

        assert my_func.__name__ == "my_func"


class TestLogExecution:
    """log_execution 데코레이터 테스트."""

    def test_returns_result(self):
        @log_execution()
        def add(a, b):
            return a + b

        assert add(1, 2) == 3

    def test_propagates_exception(self):
        @log_execution()
        def fail():
            raise ValueError("bad")

        with pytest.raises(ValueError, match="bad"):
            fail()

    def test_preserves_function_name(self):
        @log_execution()
        def my_func():
            pass

        assert my_func.__name__ == "my_func"


class TestDeprecated:
    """deprecated 데코레이터 테스트."""

    def test_warns_on_call(self):
        @deprecated(reason="outdated")
        def old_func():
            return "result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_func()
            assert result == "result"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "outdated" in str(w[0].message)

    def test_includes_replacement(self):
        @deprecated(replacement="new_func")
        def old_func():
            pass

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            old_func()
            assert "new_func" in str(w[0].message)

    def test_includes_version(self):
        @deprecated(version="2.0")
        def old_func():
            pass

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            old_func()
            assert "2.0" in str(w[0].message)

    def test_preserves_function_name(self):
        @deprecated()
        def my_func():
            pass

        assert my_func.__name__ == "my_func"
