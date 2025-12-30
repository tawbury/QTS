from runtime.config.execution_mode import decide_execution_mode, ExecutionMode


def test_default_is_paper_when_mode_not_live():
    d = decide_execution_mode(sheet_execution_mode="PAPER", sheet_live_enabled="1", env_live_ack="I_UNDERSTAND_LIVE_TRADING")
    assert d.mode == ExecutionMode.PAPER
    assert d.live_allowed is False
    assert d.reason == "mode_not_live"


def test_live_mode_requires_live_enabled_truthy():
    d = decide_execution_mode(sheet_execution_mode="LIVE", sheet_live_enabled="0", env_live_ack="I_UNDERSTAND_LIVE_TRADING")
    assert d.mode == ExecutionMode.LIVE
    assert d.live_allowed is False
    assert d.reason == "live_enabled_false"


def test_live_mode_requires_ack():
    d = decide_execution_mode(sheet_execution_mode="LIVE", sheet_live_enabled="1", env_live_ack=None)
    assert d.mode == ExecutionMode.LIVE
    assert d.live_allowed is False
    assert d.reason == "ack_missing_or_invalid"


def test_live_mode_allows_only_when_all_conditions_met():
    d = decide_execution_mode(sheet_execution_mode="LIVE", sheet_live_enabled="true", env_live_ack="I_UNDERSTAND_LIVE_TRADING")
    assert d.mode == ExecutionMode.LIVE
    assert d.live_allowed is True
    assert d.reason == "live_allowed"
