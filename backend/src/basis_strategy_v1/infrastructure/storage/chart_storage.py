"""Simple chart storage management for backtesting results."""

import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ChartStorageManager:
    """Simple chart storage management with cleanup and archival."""

    def __init__(
            self,
            base_dir: str = "results",
            max_results: int = 50,
            max_age_days: int = 30):
        """
        Initialize chart storage manager.

        Args:
            base_dir: Base directory for storing charts
            max_results: Maximum number of result sets to keep
            max_age_days: Maximum age in days before cleanup
        """
        self.base_dir = Path(base_dir)
        self.max_results = max_results
        self.max_age_days = max_age_days

        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"ChartStorageManager initialized: {base_dir}, max_results={max_results}, max_age_days={max_age_days}")

    def get_chart_directory(self, request_id: str, strategy_name: str) -> Path:
        """Get the chart directory for a specific request."""
        return self.base_dir / f"{request_id}_{strategy_name}"

    def get_chart_path(
            self,
            request_id: str,
            strategy_name: str,
            chart_name: str) -> Path:
        """Get the full path for a specific chart file."""
        chart_dir = self.get_chart_directory(request_id, strategy_name)
        return chart_dir / f"{request_id}_{strategy_name}_{chart_name}.html"

    def list_result_sets(self) -> List[Dict[str, any]]:
        """List all stored result sets with metadata."""
        result_sets = []

        for item in self.base_dir.iterdir():
            if item.is_dir() and "_" in item.name:
                try:
                    # Parse request_id_strategy_name format
                    parts = item.name.split("_", 1)
                    if len(parts) == 2:
                        request_id, strategy_name = parts

                        # Get creation time and file count
                        created_at = datetime.fromtimestamp(
                            item.stat().st_mtime)
                        chart_files = list(item.glob("*.html"))

                        result_sets.append({
                            "request_id": request_id,
                            "strategy_name": strategy_name,
                            "directory": str(item),
                            "created_at": created_at,
                            "chart_count": len(chart_files),
                            "total_size_mb": sum(f.stat().st_size for f in item.iterdir()) / (1024 * 1024)
                        })
                except Exception as e:
                    logger.warning(
                        f"Could not parse result set {item.name}: {e}")

        # Sort by creation time (newest first)
        result_sets.sort(key=lambda x: x["created_at"], reverse=True)
        return result_sets

    def cleanup_old_results(self) -> Dict[str, int]:
        """
        Clean up old results based on age and count limits.

        Returns:
            Statistics about cleanup operation
        """
        logger.info("Starting chart storage cleanup")

        result_sets = self.list_result_sets()
        removed_count = 0
        removed_size_mb = 0

        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)

        # Remove results that are too old
        for result_set in result_sets:
            if result_set["created_at"] < cutoff_date:
                try:
                    shutil.rmtree(result_set["directory"])
                    removed_count += 1
                    removed_size_mb += result_set["total_size_mb"]
                    logger.info(
                        f"Removed old result set: {result_set['request_id']} (age: {(datetime.now() - result_set['created_at']).days} days)")
                except Exception as e:
                    logger.error(
                        f"Failed to remove {result_set['directory']}: {e}")

        # Remove excess results (keep only max_results newest)
        remaining_sets = [rs for rs in result_sets if datetime.fromtimestamp(
            Path(rs["directory"]).stat().st_mtime) >= cutoff_date]

        if len(remaining_sets) > self.max_results:
            excess_sets = remaining_sets[self.max_results:]
            for result_set in excess_sets:
                try:
                    shutil.rmtree(result_set["directory"])
                    removed_count += 1
                    removed_size_mb += result_set["total_size_mb"]
                    logger.info(
                        f"Removed excess result set: {result_set['request_id']} (count limit exceeded)")
                except Exception as e:
                    logger.error(
                        f"Failed to remove {result_set['directory']}: {e}")

        stats = {
            "removed_count": removed_count,
            "removed_size_mb": round(removed_size_mb, 2),
            "remaining_count": len(result_sets) - removed_count,
            "total_size_mb": round(sum(rs["total_size_mb"] for rs in result_sets[:self.max_results]), 2)
        }

        logger.info(f"Cleanup completed: {stats}")
        return stats

    def get_storage_stats(self) -> Dict[str, any]:
        """Get current storage statistics."""
        result_sets = self.list_result_sets()

        return {
            "total_result_sets": len(result_sets),
            "total_size_mb": round(sum(rs["total_size_mb"] for rs in result_sets), 2),
            "oldest_result": result_sets[-1]["created_at"] if result_sets else None,
            "newest_result": result_sets[0]["created_at"] if result_sets else None,
            "average_size_mb": round(sum(rs["total_size_mb"] for rs in result_sets) / len(result_sets), 2) if result_sets else 0,
            "max_results_limit": self.max_results,
            "max_age_days": self.max_age_days
        }

    def archive_result_set(
            self,
            request_id: str,
            strategy_name: str,
            archive_dir: Optional[str] = None) -> bool:
        """
        Archive a specific result set to long-term storage.

        Args:
            request_id: Request ID to archive
            strategy_name: Strategy name
            archive_dir: Optional archive directory (defaults to {base_dir}/archive)

        Returns:
            True if archived successfully
        """
        try:
            source_dir = self.get_chart_directory(request_id, strategy_name)
            if not source_dir.exists():
                logger.warning(f"Source directory not found: {source_dir}")
                return False

            # Create archive directory
            archive_path = Path(
                archive_dir) if archive_dir else self.base_dir / "archive"
            archive_path.mkdir(parents=True, exist_ok=True)

            # Move to archive with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archived_name = f"{request_id}_{strategy_name}_{timestamp}"
            destination = archive_path / archived_name

            shutil.move(str(source_dir), str(destination))
            logger.info(f"Archived result set: {source_dir} -> {destination}")
            return True

        except Exception as e:
            logger.error(f"Failed to archive {request_id}: {e}")
            return False

    def cleanup_on_startup(self):
        """Run cleanup on service startup (called once)."""
        try:
            stats = self.cleanup_old_results()
            logger.info(f"Startup cleanup completed", extra=stats)
        except Exception as e:
            logger.error(f"Startup cleanup failed: {e}")
