"""
src/shared/utils.py 단위 테스트.

테스트 대상:
- require_env: 필수 환경 변수 로드
- get_env: 환경 변수 로드 (기본값)
- safe_get: 딕셔너리 안전 추출
- coalesce: 첫 번째 non-None 값
- is_truthy: 문자열 truthy 판별
"""
import os
import pytest
from src.shared.utils import (
    EnvironmentError,
    require_env,
    get_env,
    safe_get,
    coalesce,
    is_truthy,
)


class TestRequireEnv:
    """require_env 함수 테스트."""

    def test_returns_value_when_set(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY_ABC", "hello")
        assert require_env("TEST_KEY_ABC") == "hello"

    def test_raises_when_missing(self):
        # 존재하지 않는 키
        with pytest.raises(EnvironmentError, match="Required environment variable"):
            require_env("__SURELY_MISSING_KEY__")

    def test_error_includes_description(self):
        with pytest.raises(EnvironmentError, match="API 키"):
            require_env("__MISSING__", description="API 키")

    def test_returns_empty_string_if_set_empty(self, monkeypatch):
        monkeypatch.setenv("TEST_EMPTY", "")
        assert require_env("TEST_EMPTY") == ""


class TestGetEnv:
    """get_env 함수 테스트."""

    def test_returns_value_when_set(self, monkeypatch):
        monkeypatch.setenv("GE_KEY", "value")
        assert get_env("GE_KEY") == "value"

    def test_returns_default_when_missing(self):
        assert get_env("__MISSING__", "fallback") == "fallback"

    def test_returns_none_when_missing_no_default(self):
        assert get_env("__MISSING__") is None


class TestSafeGet:
    """safe_get 함수 테스트."""

    def test_returns_value(self):
        assert safe_get({"a": 1}, "a") == 1

    def test_returns_default_for_missing_key(self):
        assert safe_get({"a": 1}, "b", 99) == 99

    def test_returns_default_for_none_data(self):
        assert safe_get(None, "key", "default") == "default"

    def test_returns_none_for_missing_key_no_default(self):
        assert safe_get({"a": 1}, "b") is None

    def test_returns_falsy_value(self):
        assert safe_get({"a": 0}, "a", 99) == 0
        assert safe_get({"a": ""}, "a", "default") == ""


class TestCoalesce:
    """coalesce 함수 테스트."""

    def test_returns_first_non_none(self):
        assert coalesce(None, None, "x") == "x"

    def test_returns_first_value(self):
        assert coalesce("a", "b") == "a"

    def test_all_none(self):
        assert coalesce(None, None) is None

    def test_no_args(self):
        assert coalesce() is None

    def test_zero_is_not_none(self):
        assert coalesce(None, 0, 1) == 0

    def test_empty_string_is_not_none(self):
        assert coalesce(None, "", "x") == ""


class TestIsTruthy:
    """is_truthy 함수 테스트."""

    @pytest.mark.parametrize("value", ["1", "true", "True", "TRUE", "yes", "Yes", "on", "ON", "y", "Y"])
    def test_truthy_values(self, value):
        assert is_truthy(value) is True

    @pytest.mark.parametrize("value", ["0", "false", "no", "off", "n", "", "random", "2"])
    def test_falsy_values(self, value):
        assert is_truthy(value) is False

    def test_none(self):
        assert is_truthy(None) is False

    def test_whitespace_trimmed(self):
        assert is_truthy("  true  ") is True
