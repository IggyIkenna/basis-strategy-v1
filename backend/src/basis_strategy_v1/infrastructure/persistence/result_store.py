"""Filesystem-based result storage implementation."""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import glob
import structlog

logger = structlog.get_logger()


class ResultStore:
    """
    Filesystem-based result storage.

    Results are stored in the results/ directory with the pattern:
    results/{request_id}_{strategy_name}/

    This aligns with the current architecture where results are exported
    as directories containing CSV files and charts.
    """

    def __init__(self, base_path: str = "results"):
        """Initialize with base results directory."""
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_result(self, request_id: str, result: Dict[str, Any]) -> None:
        """
        Save result summary to filesystem using existing format.

        Note: The actual CSV and chart generation is handled by ChartGenerator.
        This method saves the summary.json file to match existing format.
        """
        try:
            strategy_name = result.get('strategy_name', 'unknown')
            share_class = result.get('share_class', 'usdt').lower()  # Default to usdt, lowercase
            result_dir = self.base_path / f"{request_id}_{share_class}_{strategy_name}"
            result_dir.mkdir(parents=True, exist_ok=True)

            # Save summary using existing format (summary.json, not
            # metadata.json)
            summary_file = result_dir / "summary.json"
            summary = {
                'request_id': request_id,
                'strategy_name': strategy_name,
                'start_date': result.get('start_date'),
                'end_date': result.get('end_date'),
                'initial_capital': result.get('initial_capital'),
                'final_value': result.get('final_value'),
                'total_return': result.get('total_return'),
                'annualized_return': result.get('annualized_return', 0),
                'sharpe_ratio': result.get('sharpe_ratio', 0),
                'max_drawdown': result.get('max_drawdown', 0),
                'total_trades': result.get('total_trades', 0),
                'chart_paths': result.get('chart_paths', [])
            }

            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)

            logger.info(
                "Result summary saved",
                request_id=request_id,
                result_dir=str(result_dir))
            
            # Generate CSV files and charts using ChartGenerator
            try:
                from ..visualization.chart_generator import ChartGenerator
                chart_generator = ChartGenerator()
                
                # Generate charts and CSV files
                chart_generator.generate_all_charts(
                    results=result,
                    request_id=request_id,
                    strategy_name=strategy_name,
                    output_dir=result_dir
                )
                
                logger.info(f"Charts and CSV files generated for {request_id}")
                
            except Exception as e:
                logger.warning(f"Failed to generate charts and CSV files: {e}")
                # Continue without failing the result save

        except Exception as e:
            logger.error(
                "Failed to save result summary",
                request_id=request_id,
                error=str(e))
            raise

    async def get_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get result by request_id from filesystem.

        Returns summary.json if available, otherwise None.
        The results.py route handles CSV parsing as fallback.
        """
        try:
            # Find result directory
            candidates = sorted(
                glob.glob(str(self.base_path / f"{request_id}_*")))
            if not candidates:
                return None

            result_dir = Path(candidates[0])
            summary_file = result_dir / "summary.json"

            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    return json.load(f)

            # Fallback: basic info from directory name
            strategy_name = result_dir.name.split(
                '_', 1)[1] if '_' in result_dir.name else 'unknown'
            return {
                'request_id': request_id,
                'strategy_name': strategy_name,
                'status': 'completed'
            }

        except Exception as e:
            logger.error(
                "Failed to get result",
                request_id=request_id,
                error=str(e))
            return None

    async def list_results(self,
                           strategy_filter: Optional[str] = None,
                           limit: int = 1000,
                           offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all results from filesystem.

        Note: The results.py route has more sophisticated scanning logic.
        This method is mainly for compatibility.
        """
        try:
            results = []

            for entry in self.base_path.iterdir():
                if not entry.is_dir():
                    continue

                # Parse directory name: {request_id}_{strategy_name}
                parts = entry.name.split('_', 1)
                if len(parts) != 2:
                    continue

                request_id, strategy_name = parts

                if strategy_filter and strategy_filter != strategy_name:
                    continue

                # Try to load summary
                summary_file = entry / "summary.json"
                if summary_file.exists():
                    try:
                        with open(summary_file, 'r') as f:
                            result = json.load(f)
                            results.append(result)
                            continue
                    except Exception:
                        pass

                # Fallback: basic info
                results.append({
                    'request_id': request_id,
                    'strategy_name': strategy_name,
                    'status': 'completed',
                    'export_dir': str(entry)
                })

            # Sort by request_id (most recent first, assuming UUID timestamp
            # ordering)
            results.sort(key=lambda x: x.get('request_id', ''), reverse=True)

            # Apply pagination
            return results[offset:offset + limit]

        except Exception as e:
            logger.error("Failed to list results", error=str(e))
            return []

    async def delete_result(self, request_id: str) -> bool:
        """
        Delete result directory from filesystem.
        """
        try:
            candidates = sorted(
                glob.glob(str(self.base_path / f"{request_id}_*")))
            if not candidates:
                return False

            result_dir = Path(candidates[0])

            # Remove entire directory
            import shutil
            shutil.rmtree(result_dir)

            logger.info(
                "Result deleted",
                request_id=request_id,
                result_dir=str(result_dir))
            return True

        except Exception as e:
            logger.error(
                "Failed to delete result",
                request_id=request_id,
                error=str(e))
            return False
