"""feedback/kpi.py 단위 테스트."""
from src.feedback.contracts import FeedbackSummary, KPIThresholds
from src.feedback.kpi import KPIResult, evaluate_kpis


class TestEvaluateKPIs:
    def test_all_pass(self):
        """모든 KPI 통과."""
        summary = FeedbackSummary(
            avg_slippage_bps=5.0,
            avg_market_impact_bps=10.0,
            avg_quality_score=0.90,
            avg_fill_latency_ms=50.0,
            avg_fill_ratio=0.98,
        )
        results = evaluate_kpis(summary)
        assert len(results) == 5
        assert all(r.passed for r in results)

    def test_all_fail(self):
        """모든 KPI 실패."""
        summary = FeedbackSummary(
            avg_slippage_bps=20.0,
            avg_market_impact_bps=30.0,
            avg_quality_score=0.50,
            avg_fill_latency_ms=200.0,
            avg_fill_ratio=0.80,
        )
        results = evaluate_kpis(summary)
        assert all(not r.passed for r in results)

    def test_slippage_boundary(self):
        """슬리피지 경계값: 10bps = pass."""
        summary = FeedbackSummary(avg_slippage_bps=10.0)
        results = evaluate_kpis(summary)
        slippage_result = next(r for r in results if r.metric == "avg_slippage_bps")
        assert slippage_result.passed is True

    def test_slippage_fail(self):
        """슬리피지 초과: 10.1bps = fail."""
        summary = FeedbackSummary(avg_slippage_bps=10.1)
        results = evaluate_kpis(summary)
        slippage_result = next(r for r in results if r.metric == "avg_slippage_bps")
        assert slippage_result.passed is False

    def test_quality_boundary(self):
        """품질 경계값: 0.85 = pass."""
        summary = FeedbackSummary(avg_quality_score=0.85)
        results = evaluate_kpis(summary)
        quality_result = next(r for r in results if r.metric == "quality_score")
        assert quality_result.passed is True

    def test_custom_thresholds(self):
        """커스텀 기준."""
        summary = FeedbackSummary(avg_slippage_bps=8.0)
        strict = KPIThresholds(max_avg_slippage_bps=5.0)
        results = evaluate_kpis(summary, strict)
        slippage_result = next(r for r in results if r.metric == "avg_slippage_bps")
        assert slippage_result.passed is False

    def test_result_structure(self):
        """KPIResult 구조 확인."""
        summary = FeedbackSummary()
        results = evaluate_kpis(summary)
        for r in results:
            assert isinstance(r, KPIResult)
            assert r.metric != ""
            assert isinstance(r.passed, bool)

    def test_metric_names(self):
        """5개 메트릭 이름."""
        results = evaluate_kpis(FeedbackSummary())
        names = {r.metric for r in results}
        assert names == {
            "avg_slippage_bps",
            "quality_score",
            "fill_ratio",
            "avg_latency_ms",
            "market_impact_bps",
        }

    def test_default_summary_kpis(self):
        """기본값(conservative) KPI 결과."""
        results = evaluate_kpis(FeedbackSummary())
        # default: slippage=10 (pass), quality=0.75 (fail), fill=0.95 (pass),
        # latency=50 (pass), impact=15 (pass)
        passed = {r.metric: r.passed for r in results}
        assert passed["avg_slippage_bps"] is True
        assert passed["quality_score"] is False  # 0.75 < 0.85
        assert passed["fill_ratio"] is True
        assert passed["avg_latency_ms"] is True
        assert passed["market_impact_bps"] is True

    def test_fill_ratio_boundary(self):
        """체결률 경계값: 0.95 = pass."""
        summary = FeedbackSummary(avg_fill_ratio=0.95)
        results = evaluate_kpis(summary)
        fill_result = next(r for r in results if r.metric == "fill_ratio")
        assert fill_result.passed is True

    def test_latency_boundary(self):
        """지연 경계값: 100ms = pass."""
        summary = FeedbackSummary(avg_fill_latency_ms=100.0)
        results = evaluate_kpis(summary)
        latency_result = next(r for r in results if r.metric == "avg_latency_ms")
        assert latency_result.passed is True
