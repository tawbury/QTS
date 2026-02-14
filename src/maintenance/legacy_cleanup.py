"""
This script cleans up old log and trade data files.
"""
import glob
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Use the canonical path resolver
from src.shared.paths import log_dir, data_dir

_LOG = logging.getLogger(__name__)

def cleanup_logs(retention_days: int = 7) -> None:
    """
    Deletes log files older than the specified retention period.
    Log files are expected to follow the format 'qts_YYYYMMDD.log'.
    """
    target_dir = log_dir()
    if not target_dir.exists():
        _LOG.warning(f"Log directory not found, skipping cleanup: {target_dir}")
        return

    _LOG.info(f"Scanning log directory for files older than {retention_days} days: {target_dir}")
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    for log_file_path in glob.glob(str(target_dir / "qts_*.log")):
        try:
            log_file = Path(log_file_path)
            file_name = log_file.name
            
            # Extract date from 'qts_YYYYMMDD.log'
            date_str = file_name.split("_")[1].split(".")[0]
            file_date = datetime.strptime(date_str, "%Y%m%d")

            if file_date < cutoff_date:
                log_file.unlink()
                _LOG.info(f"Deleted old log file: {log_file}")
        except (IndexError, ValueError) as e:
            _LOG.warning(f"Could not parse date from log file, skipping: {log_file_path} ({e})")
        except Exception as e:
            _LOG.error(f"Error deleting log file {log_file_path}: {e}", exc_info=True)


def cleanup_trade_data(retention_days: int = 30) -> None:
    """
    Deletes trade data files older than the specified retention period.
    Trade data files are expected to be in JSONL format with names like 'YYYY-MM-DD.jsonl'.
    """
    # The path to trade data is typically data_dir() / "trades"
    target_dir = data_dir() / "trades"
    if not target_dir.exists():
        _LOG.warning(f"Trade data directory not found, skipping cleanup: {target_dir}")
        return

    _LOG.info(f"Scanning trade data directory for files older than {retention_days} days: {target_dir}")
    cutoff_date = datetime.now() - timedelta(days=retention_days)

    for data_file_path in glob.glob(str(target_dir / "*.jsonl")):
        try:
            data_file = Path(data_file_path)
            file_name = data_file.stem  # Gets filename without extension
            
            # Assuming format 'YYYY-MM-DD'
            file_date = datetime.strptime(file_name, "%Y-%m-%d")

            if file_date < cutoff_date:
                data_file.unlink()
                _LOG.info(f"Deleted old trade data file: {data_file}")
        except ValueError as e:
            _LOG.warning(f"Could not parse date from data file, skipping: {data_file_path} ({e})")
        except Exception as e:
            _LOG.error(f"Error deleting trade data file {data_file_path}: {e}", exc_info=True)


if __name__ == "__main__":
    # Basic logging setup for standalone execution
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    _LOG.info("Running standalone cleanup...")
    cleanup_logs()
    cleanup_trade_data()
    _LOG.info("Cleanup complete.")
