from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.shared.paths import data_dir
from src.shared.timezone_utils import get_kst_now


_LOG = logging.getLogger(__name__)


class TradeRecorder:
    """
    Records trade execution data to daily JSONL files.
    """

    def __init__(self, base_path: Path | None = None) -> None:
        """
        Initializes the TradeRecorder.

        Args:
            base_path: The base directory for trade data. Defaults to data_dir() / "trades".
        """
        self._base_path = base_path or data_dir() / "trades"
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Ensures the base directory for trade data exists."""
        try:
            self._base_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            _LOG.error(f"Failed to create trade data directory: {self._base_path}", exc_info=True)
            raise

    def _get_file_path(self, timestamp: datetime) -> Path:
        """
        Gets the file path for the given timestamp.

        Args:
            timestamp: The timestamp of the trade.

        Returns:
            The path to the JSONL file for the given day.
        """
        return self._base_path / f"{timestamp.strftime('%Y-%m-%d')}.jsonl"

    def record_trade(self, trade_data: Dict[str, Any]) -> None:
        """
        Records a single trade to a JSONL file.

        The trade data is appended to a file named after the trade's date (YYYY-MM-DD.jsonl).

        Args:
            trade_data: The trade data to record.
        """
        try:
            now = get_kst_now()
            file_path = self._get_file_path(now)
            
            # Add a timestamp to the trade data
            record = {"timestamp": now.isoformat(), **trade_data}
            
            with open(file_path, "a") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        except Exception:
            _LOG.error(f"Failed to record trade data to {file_path}", exc_info=True)

