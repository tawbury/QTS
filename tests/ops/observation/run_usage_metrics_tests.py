# tests/ops/observation/run_usage_metrics_tests.py

"""
Simple test runner for usage metrics without pytest dependency.
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from test_usage_metrics import (
    TestUsageMetricsConfig,
    TestWindowMetrics,
    TestUsageMetricsCollector,
    TestUsageMetricsIntegration,
)


def run_test_class(test_class):
    """Run all test methods in a test class."""
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    passed = 0
    failed = 0
    
    print(f"\n=== Running {test_class.__name__} ===")
    
    for method_name in test_methods:
        try:
            test_instance = test_class()
            method = getattr(test_instance, method_name)
            method()
            print(f"✓ {method_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {method_name}: {e}")
            traceback.print_exc()
            failed += 1
    
    return passed, failed


def main():
    """Run all usage metrics tests."""
    print("Usage Metrics Test Runner")
    print("=" * 50)
    
    test_classes = [
        TestUsageMetricsConfig,
        TestWindowMetrics,
        TestUsageMetricsCollector,
        TestUsageMetricsIntegration,
    ]
    
    total_passed = 0
    total_failed = 0
    
    for test_class in test_classes:
        passed, failed = run_test_class(test_class)
        total_passed += passed
        total_failed += failed
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {total_passed/(total_passed+total_failed)*100:.1f}%")
    
    if total_failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"❌ {total_failed} test(s) failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
