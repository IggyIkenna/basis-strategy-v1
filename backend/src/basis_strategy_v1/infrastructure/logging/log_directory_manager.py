"""
Log Directory Manager

Manages the log directory structure: logs/{correlation_id}/{pid}/

This creates isolated log directories for each run with proper metadata
tracking for debugging and analysis.

Reference: docs/LOGGING_GUIDE.md - Log Directory Structure
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


class LogDirectoryManager:
    """
    Manages log directory structure and metadata.

    Directory structure:
        logs/{correlation_id}/{pid}/
        ├── run_metadata.json
        ├── api.log
        ├── component_name.log
        ├── ...
        └── events/
            ├── positions.jsonl
            ├── exposures.jsonl
            ├── operation_executions.jsonl
            └── ...
    """

    @staticmethod
    def create_run_logs(
        correlation_id: str,
        pid: int,
        mode: str,
        strategy: str,
        capital: float,
        base_dir: str = "logs",
    ) -> Path:
        """
        Create log directory structure for a run.

        Args:
            correlation_id: Unique correlation ID for this run
            pid: Process ID
            mode: Execution mode ('backtest' or 'live')
            strategy: Strategy name
            capital: Initial capital
            base_dir: Base directory for logs (default: "logs")

        Returns:
            Path to the log directory for this run
        """
        # Create base directory structure
        log_dir = Path(base_dir) / correlation_id / str(pid)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create events subdirectory
        events_dir = log_dir / "events"
        events_dir.mkdir(exist_ok=True)

        # Create run metadata file
        metadata = {
            "correlation_id": correlation_id,
            "pid": pid,
            "mode": mode,
            "strategy": strategy,
            "initial_capital": capital,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "start_time_local": datetime.now().isoformat(),
            "real_date": datetime.now().strftime("%Y-%m-%d"),
            "real_time": datetime.now().strftime("%H:%M:%S"),
            "timezone": "UTC",
            "log_directory": str(log_dir.absolute()),
            "events_directory": str(events_dir.absolute()),
        }

        # Write metadata to log directory (pid level) for easier access
        metadata_file = log_dir / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Also write to parent directory (correlation_id level) for correlation tracking
        parent_metadata_file = log_dir.parent / "run_metadata.json"
        with open(parent_metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        return log_dir

    @staticmethod
    def get_log_directory(correlation_id: str, pid: int, base_dir: str = "logs") -> Path:
        """
        Get path to log directory for a specific run.

        Args:
            correlation_id: Correlation ID
            pid: Process ID
            base_dir: Base directory for logs

        Returns:
            Path to log directory
        """
        return Path(base_dir) / correlation_id / str(pid)

    @staticmethod
    def get_events_directory(correlation_id: str, pid: int, base_dir: str = "logs") -> Path:
        """
        Get path to events directory for a specific run.

        Args:
            correlation_id: Correlation ID
            pid: Process ID
            base_dir: Base directory for logs

        Returns:
            Path to events directory
        """
        return Path(base_dir) / correlation_id / str(pid) / "events"

    @staticmethod
    def read_run_metadata(correlation_id: str, base_dir: str = "logs") -> Optional[dict]:
        """
        Read run metadata for a specific correlation ID.

        Args:
            correlation_id: Correlation ID
            base_dir: Base directory for logs

        Returns:
            Run metadata dictionary or None if not found
        """
        metadata_file = Path(base_dir) / correlation_id / "run_metadata.json"

        if not metadata_file.exists():
            return None

        with open(metadata_file, "r") as f:
            return json.load(f)

    @staticmethod
    def list_runs(base_dir: str = "logs") -> list:
        """
        List all runs (correlation IDs) in the log directory.

        Args:
            base_dir: Base directory for logs

        Returns:
            List of correlation IDs
        """
        base_path = Path(base_dir)

        if not base_path.exists():
            return []

        # Return directories that have run_metadata.json
        return [
            d.name for d in base_path.iterdir() if d.is_dir() and (d / "run_metadata.json").exists()
        ]

    @staticmethod
    def cleanup_old_logs(base_dir: str = "logs", days: int = 30) -> int:
        """
        Clean up log directories older than specified days.

        Args:
            base_dir: Base directory for logs
            days: Number of days to keep logs

        Returns:
            Number of directories cleaned up
        """
        import time

        base_path = Path(base_dir)

        if not base_path.exists():
            return 0

        cutoff_time = time.time() - (days * 24 * 60 * 60)
        cleaned = 0

        for correlation_dir in base_path.iterdir():
            if not correlation_dir.is_dir():
                continue

            # Check if directory is old enough
            if correlation_dir.stat().st_mtime < cutoff_time:
                # Clean up directory
                import shutil

                shutil.rmtree(correlation_dir)
                cleaned += 1

        return cleaned

    @staticmethod
    def get_component_log_path(
        correlation_id: str, pid: int, component_name: str, base_dir: str = "logs"
    ) -> Path:
        """
        Get path to component log file.

        Args:
            correlation_id: Correlation ID
            pid: Process ID
            component_name: Component name
            base_dir: Base directory for logs

        Returns:
            Path to component log file
        """
        log_dir = LogDirectoryManager.get_log_directory(correlation_id, pid, base_dir)
        return log_dir / f"{component_name}.log"

    @staticmethod
    def get_event_log_path(
        correlation_id: str, pid: int, event_type: str, base_dir: str = "logs"
    ) -> Path:
        """
        Get path to event JSONL file.

        Args:
            correlation_id: Correlation ID
            pid: Process ID
            event_type: Event type (e.g., 'positions', 'operations', etc.)
            base_dir: Base directory for logs

        Returns:
            Path to event JSONL file
        """
        events_dir = LogDirectoryManager.get_events_directory(correlation_id, pid, base_dir)
        return events_dir / f"{event_type}.jsonl"

    @staticmethod
    def ensure_log_directory_exists(log_dir: Path) -> None:
        """
        Ensure log directory and events subdirectory exist.

        Args:
            log_dir: Path to log directory
        """
        log_dir.mkdir(parents=True, exist_ok=True)
        events_dir = log_dir / "events"
        events_dir.mkdir(exist_ok=True)
