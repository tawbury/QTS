"""Micro Risk Loop 비동기 러너.

근거: docs/arch/sub/16_Micro_Risk_Loop_Architecture.md §4.2
- ETEDA와 독립적으로 asyncio Task에서 실행
- 100ms~1s 주기로 run_cycle() 호출
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from src.micro_risk.contracts import MicroRiskConfig
from src.micro_risk.loop import MicroRiskLoop

_LOG = logging.getLogger("micro_risk.runner")


class MicroRiskLoopRunner:
    """asyncio Task로 MicroRiskLoop를 주기적으로 실행하는 러너."""

    def __init__(
        self,
        loop: MicroRiskLoop,
        interval_ms: Optional[int] = None,
    ) -> None:
        self._loop = loop
        self._interval = (interval_ms or loop.config.loop_interval_ms) / 1000.0
        self._running = False
        self._task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def micro_risk_loop(self) -> MicroRiskLoop:
        return self._loop

    async def run(self) -> None:
        """Micro Risk Loop 비동기 실행 (§4.2).

        ETEDA Loop와 독립적으로 asyncio.gather()에서 실행된다.
        """
        self._loop.start()
        self._running = True
        _LOG.info(
            f"Micro Risk Loop started (interval={self._interval * 1000:.0f}ms)"
        )

        try:
            while self._running and self._loop.is_running:
                alerts = self._loop.run_cycle()

                for alert in alerts:
                    if alert.severity == "CRITICAL":
                        _LOG.error(f"[MicroRisk] {alert.code}: {alert.message}")
                    else:
                        _LOG.warning(f"[MicroRisk] {alert.code}: {alert.message}")

                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            _LOG.info("Micro Risk Loop cancelled")
        except Exception as e:
            _LOG.error(f"Micro Risk Loop runner error: {e}")
        finally:
            self._running = False
            self._loop.stop()
            _LOG.info(
                f"Micro Risk Loop stopped (cycles={self._loop.cycle_count})"
            )

    def stop(self) -> None:
        """러너 정지."""
        self._running = False
        self._loop.stop()
        if self._task is not None and not self._task.done():
            self._task.cancel()

    def start_background(self) -> asyncio.Task:
        """백그라운드 Task로 시작."""
        self._task = asyncio.create_task(self.run())
        return self._task
