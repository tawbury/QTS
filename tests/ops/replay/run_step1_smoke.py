import sys
from pathlib import Path

# 프로젝트 루트(QTS)를 sys.path에 등록
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.ops.observer.inputs import MockMarketDataProvider
from src.ops.runtime.observer_runner import ObserverRunner


def main():
    provider = MockMarketDataProvider()

    runner = ObserverRunner(
        provider,
        interval_sec=0.5,   # 천천히
        max_iterations=5,  # 5회만
    )

    runner.run()


if __name__ == "__main__":
    main()
