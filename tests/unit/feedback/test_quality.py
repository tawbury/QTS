"""feedback/quality.py 단위 테스트."""
import pytest

from src.feedback.quality import calculate_execution_quality_score


class TestExecutionQualityScore:
    def test_perfect_execution(self):
        """완벽한 실행: 0 slippage, 0 partial fill, 0 latency."""
        score = calculate_execution_quality_score(0.0, 0.0, 0.0)
        assert score == 1.0

    def test_worst_execution(self):
        """최악의 실행."""
        score = calculate_execution_quality_score(100.0, 1.0, 2000.0)
        assert score == 0.0

    def test_moderate_slippage(self):
        """중간 슬리피지 (25bps → 0.5 score)."""
        score = calculate_execution_quality_score(25.0, 0.0, 0.0)
        assert pytest.approx(score, abs=0.01) == 0.75  # 0.5*0.5 + 1.0*0.3 + 1.0*0.2

    def test_slippage_weight(self):
        """슬리피지 가중치 50%."""
        # 50bps → slippage_score=0
        score = calculate_execution_quality_score(50.0, 0.0, 0.0)
        assert pytest.approx(score, abs=0.01) == 0.50  # 0*0.5 + 1*0.3 + 1*0.2

    def test_fill_weight(self):
        """Fill 가중치 30%."""
        # 100% partial fill → fill_score=0
        score = calculate_execution_quality_score(0.0, 1.0, 0.0)
        assert pytest.approx(score, abs=0.01) == 0.70  # 1*0.5 + 0*0.3 + 1*0.2

    def test_latency_weight(self):
        """Latency 가중치 20%."""
        # 1000ms → latency_score=0
        score = calculate_execution_quality_score(0.0, 0.0, 1000.0)
        assert pytest.approx(score, abs=0.01) == 0.80  # 1*0.5 + 1*0.3 + 0*0.2

    def test_negative_slippage(self):
        """유리한 슬리피지도 절대값으로 계산."""
        score = calculate_execution_quality_score(-10.0, 0.0, 0.0)
        expected_slip = 1.0 - (10.0 / 50.0)  # 0.8
        expected = expected_slip * 0.5 + 1.0 * 0.3 + 1.0 * 0.2
        assert pytest.approx(score, abs=0.01) == expected

    def test_clamped_to_0_1(self):
        """결과는 0.0~1.0 범위."""
        score = calculate_execution_quality_score(0.0, 0.0, 0.0)
        assert 0.0 <= score <= 1.0

        score = calculate_execution_quality_score(200.0, 2.0, 5000.0)
        assert 0.0 <= score <= 1.0

    def test_typical_execution(self):
        """일반적인 실행: 8bps, 5% partial, 45ms."""
        score = calculate_execution_quality_score(8.0, 0.05, 45.0)
        assert score > 0.85  # KPI 기준 충족

    def test_partial_fill_half(self):
        """50% 부분 체결."""
        score = calculate_execution_quality_score(0.0, 0.5, 0.0)
        expected = 1.0 * 0.5 + 0.5 * 0.3 + 1.0 * 0.2  # 0.85
        assert pytest.approx(score, abs=0.01) == expected
