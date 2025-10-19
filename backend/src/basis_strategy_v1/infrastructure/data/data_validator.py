"""
Data Validator

Comprehensive data validation with error codes for data provider operations.
Implements all error codes from DATA-001 through DATA-013 as specified in
docs/specs/09_DATA_PROVIDER.md.

Reference: docs/specs/09_DATA_PROVIDER.md - Data Provider Specification
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataProviderError(Exception):
    """Custom exception for data provider errors with error codes"""

    def __init__(self, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{error_code}] {message}")


class DataValidator:
    """Comprehensive data validation with error codes"""

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.logger = logging.getLogger(__name__)

        # Environment variables for date range validation
        self.start_date = os.getenv("BASIS_DATA_START_DATE")
        self.end_date = os.getenv("BASIS_DATA_END_DATE")

        # Error code mappings
        self.error_codes = {
            "DATA-001": "Required data file not found",
            "DATA-002": "CSV parsing failed",
            "DATA-003": "Data file is empty",
            "DATA-004": "Data date range mismatch",
            "DATA-005": "Required column missing",
            "DATA-006": "Invalid data type in column",
            "DATA-007": "Data contains null values",
            "DATA-008": "Data contains duplicate timestamps",
            "DATA-009": "Data timestamp format invalid",
            "DATA-010": "Data timestamp not hourly aligned",
            "DATA-011": "Data contains gaps (missing hours)",
            "DATA-012": "Data validation failed",
            "DATA-013": "Data provider initialization failed",
            "DATA-014": "Data outside backtest date range",
        }

    def validate_file_existence(self, file_path: Path) -> None:
        """Validate that required data file exists (DATA-001)"""
        if not file_path.exists():
            raise DataProviderError(
                "DATA-001",
                f"Required data file not found: {file_path}",
                {"file_path": str(file_path)},
            )
        self.logger.debug(f"✅ File exists: {file_path}")

    def validate_csv_parsing(self, file_path: Path) -> pd.DataFrame:
        """Validate CSV parsing (DATA-002)"""
        try:
            df = pd.read_csv(file_path)
            self.logger.debug(f"✅ CSV parsed successfully: {file_path}")
            return df
        except Exception as e:
            raise DataProviderError(
                "DATA-002",
                f"CSV parsing failed for {file_path}: {e}",
                {"file_path": str(file_path), "error": str(e)},
            )

    def validate_empty_file(self, df: pd.DataFrame, file_path: Path) -> None:
        """Validate file is not empty (DATA-003)"""
        if len(df) == 0:
            raise DataProviderError(
                "DATA-003",
                f"Data file is empty: {file_path}",
                {"file_path": str(file_path), "rows": 0},
            )
        self.logger.debug(f"✅ File not empty: {file_path} ({len(df)} rows)")

    def validate_date_range(self, df: pd.DataFrame, file_path: Path) -> None:
        """Validate data date range against environment variables (DATA-004)"""
        if not self.start_date or not self.end_date:
            self.logger.warning(
                "BASIS_DATA_START_DATE or BASIS_DATA_END_DATE not set, skipping date range validation"
            )
            return

        try:
            # Check if timestamp column exists
            timestamp_col = None
            for col in df.columns:
                if "timestamp" in col.lower() or "date" in col.lower() or "time" in col.lower():
                    timestamp_col = col
                    break

            if not timestamp_col:
                self.logger.warning(
                    f"No timestamp column found in {file_path}, skipping date range validation"
                )
                return

            # Convert timestamps to datetime
            df_timestamps = pd.to_datetime(df[timestamp_col])
            min_date = df_timestamps.min()
            max_date = df_timestamps.max()

            expected_start = pd.to_datetime(self.start_date)
            expected_end = pd.to_datetime(self.end_date)

            # Handle timezone comparison - make both timezone-aware or both timezone-naive
            if min_date.tz is not None and expected_start.tz is None:
                expected_start = expected_start.tz_localize("UTC")
                expected_end = expected_end.tz_localize("UTC")
            elif min_date.tz is None and expected_start.tz is not None:
                min_date = min_date.tz_localize("UTC")
                max_date = max_date.tz_localize("UTC")

            # STRICT VALIDATION: ALL data must be within the backtest date range
            # Check if any data is outside the allowed range
            data_before_start = df_timestamps < expected_start
            data_after_end = df_timestamps > expected_end

            if data_before_start.any():
                out_of_range_before = df_timestamps[data_before_start]
                raise DataProviderError(
                    "DATA-014",
                    f"Data contains timestamps before backtest start date in {file_path}. Start date: {expected_start}, Found: {out_of_range_before.min()} to {out_of_range_before.max()}",
                    {
                        "file_path": str(file_path),
                        "expected_start": str(expected_start),
                        "out_of_range_count": data_before_start.sum(),
                        "out_of_range_min": str(out_of_range_before.min()),
                        "out_of_range_max": str(out_of_range_before.max()),
                    },
                )

            if data_after_end.any():
                out_of_range_after = df_timestamps[data_after_end]
                raise DataProviderError(
                    "DATA-014",
                    f"Data contains timestamps after backtest end date in {file_path}. End date: {expected_end}, Found: {out_of_range_after.min()} to {out_of_range_after.max()}",
                    {
                        "file_path": str(file_path),
                        "expected_end": str(expected_end),
                        "out_of_range_count": data_after_end.sum(),
                        "out_of_range_min": str(out_of_range_after.min()),
                        "out_of_range_max": str(out_of_range_after.max()),
                    },
                )

            # Also check if data covers the requested range (original DATA-004 logic)
            if max_date < expected_start or min_date > expected_end:
                raise DataProviderError(
                    "DATA-004",
                    f"Data does not cover requested date range in {file_path}. Requested: {expected_start} to {expected_end}, Data available: {min_date} to {max_date}",
                    {
                        "file_path": str(file_path),
                        "expected_start": str(expected_start),
                        "expected_end": str(expected_end),
                        "actual_start": str(min_date),
                        "actual_end": str(max_date),
                    },
                )

            self.logger.debug(f"✅ Date range valid: {file_path} ({min_date} to {max_date})")

        except Exception as e:
            if isinstance(e, DataProviderError):
                raise
            raise DataProviderError(
                "DATA-004",
                f"Date range validation failed for {file_path}: {e}",
                {"file_path": str(file_path), "error": str(e)},
            )

    def validate_backtest_date_range(
        self, df: pd.DataFrame, file_path: Path, start_date: str, end_date: str
    ) -> None:
        """Validate data is within backtest date range (DATA-014)"""
        try:
            # Check if timestamp column exists
            timestamp_col = None
            for col in df.columns:
                if "timestamp" in col.lower() or "date" in col.lower() or "time" in col.lower():
                    timestamp_col = col
                    break

            if not timestamp_col:
                self.logger.warning(
                    f"No timestamp column found in {file_path}, skipping backtest date range validation"
                )
                return

            # Convert timestamps to datetime
            df_timestamps = pd.to_datetime(df[timestamp_col])
            min_date = df_timestamps.min()
            max_date = df_timestamps.max()

            expected_start = pd.to_datetime(start_date)
            expected_end = pd.to_datetime(end_date)

            # Handle timezone comparison - make both timezone-aware or both timezone-naive
            if min_date.tz is not None and expected_start.tz is None:
                expected_start = expected_start.tz_localize("UTC")
                expected_end = expected_end.tz_localize("UTC")
            elif min_date.tz is None and expected_start.tz is not None:
                min_date = min_date.tz_localize("UTC")
                max_date = max_date.tz_localize("UTC")

            # STRICT VALIDATION: ALL data must be within the backtest date range
            # Check if any data is outside the allowed range
            data_before_start = df_timestamps < expected_start
            data_after_end = df_timestamps > expected_end

            if data_before_start.any():
                out_of_range_before = df_timestamps[data_before_start]
                raise DataProviderError(
                    "DATA-014",
                    f"Data contains timestamps before backtest start date in {file_path}. Start date: {expected_start}, Found: {out_of_range_before.min()} to {out_of_range_before.max()}",
                    {
                        "file_path": str(file_path),
                        "expected_start": str(expected_start),
                        "out_of_range_count": data_before_start.sum(),
                        "out_of_range_min": str(out_of_range_before.min()),
                        "out_of_range_max": str(out_of_range_before.max()),
                    },
                )

            if data_after_end.any():
                out_of_range_after = df_timestamps[data_after_end]
                raise DataProviderError(
                    "DATA-014",
                    f"Data contains timestamps after backtest end date in {file_path}. End date: {expected_end}, Found: {out_of_range_after.min()} to {out_of_range_after.max()}",
                    {
                        "file_path": str(file_path),
                        "expected_end": str(expected_end),
                        "out_of_range_count": data_after_end.sum(),
                        "out_of_range_min": str(out_of_range_after.min()),
                        "out_of_range_max": str(out_of_range_after.max()),
                    },
                )

            self.logger.debug(
                f"✅ Backtest date range valid: {file_path} (all data within {expected_start} to {expected_end})"
            )

        except Exception as e:
            if isinstance(e, DataProviderError):
                raise
            raise DataProviderError(
                "DATA-014",
                f"Backtest date range validation failed for {file_path}: {e}",
                {"file_path": str(file_path), "error": str(e)},
            )

    def validate_required_columns(
        self, df: pd.DataFrame, required_columns: List[str], file_path: Path
    ) -> None:
        """Validate required columns exist (DATA-005)"""
        # Create column mapping for camelCase to snake_case conversion
        column_mapping = {
            "liquidityIndex": "liquidity_index",
            "variableBorrowIndex": "variable_borrow_index",
            "currentLiquidityRate": "supply_rate",
            "currentVariableBorrowRate": "borrow_rate",
        }

        # Apply column mapping
        df_mapped = df.rename(columns=column_mapping)

        missing_columns = set(required_columns) - set(df_mapped.columns)
        if missing_columns:
            raise DataProviderError(
                "DATA-005",
                f"Required columns missing in {file_path}: {missing_columns}",
                {
                    "file_path": str(file_path),
                    "missing_columns": list(missing_columns),
                    "available_columns": list(df.columns),
                    "mapped_columns": list(df_mapped.columns),
                },
            )
        self.logger.debug(f"✅ Required columns present: {file_path} ({required_columns})")

    def validate_data_types(
        self, df: pd.DataFrame, expected_types: Dict[str, str], file_path: Path
    ) -> None:
        """Validate data types in columns (DATA-006)"""
        for column, expected_type in expected_types.items():
            if column not in df.columns:
                continue

            actual_type = str(df[column].dtype)
            if expected_type not in actual_type:
                raise DataProviderError(
                    "DATA-006",
                    f"Invalid data type in column '{column}' of {file_path}. Expected: {expected_type}, Got: {actual_type}",
                    {
                        "file_path": str(file_path),
                        "column": column,
                        "expected_type": expected_type,
                        "actual_type": actual_type,
                    },
                )
        self.logger.debug(f"✅ Data types valid: {file_path}")

    def validate_null_values(
        self, df: pd.DataFrame, file_path: Path, allow_nulls: bool = False
    ) -> None:
        """Validate no null values (DATA-007)"""
        if allow_nulls:
            self.logger.debug(f"✅ Null values allowed: {file_path}")
            return

        null_columns = df.columns[df.isnull().any()].tolist()
        if null_columns:
            null_counts = df[null_columns].isnull().sum().to_dict()
            raise DataProviderError(
                "DATA-007",
                f"Data contains null values in {file_path}: {null_columns}",
                {
                    "file_path": str(file_path),
                    "null_columns": null_columns,
                    "null_counts": null_counts,
                },
            )
        self.logger.debug(f"✅ No null values: {file_path}")

    def validate_duplicate_timestamps(self, df: pd.DataFrame, file_path: Path) -> None:
        """Validate no duplicate timestamps (DATA-008)"""
        # Find timestamp column
        timestamp_col = None
        for col in df.columns:
            if "timestamp" in col.lower() or "date" in col.lower() or "time" in col.lower():
                timestamp_col = col
                break

        if not timestamp_col:
            self.logger.debug(
                f"No timestamp column found in {file_path}, skipping duplicate validation"
            )
            return

        # Allow duplicates for execution costs (daily lookup tables resampled to hourly)
        file_path_str = str(file_path).lower()
        if "execution_costs" in file_path_str:
            self.logger.debug(
                f"✅ Allowing duplicate timestamps for execution costs lookup table: {file_path}"
            )
            return

        duplicates = df[df.duplicated(subset=[timestamp_col], keep=False)]
        if len(duplicates) > 0:
            duplicate_timestamps = duplicates[timestamp_col].unique()
            raise DataProviderError(
                "DATA-008",
                f"Data contains duplicate timestamps in {file_path}: {len(duplicate_timestamps)} duplicates",
                {
                    "file_path": str(file_path),
                    "duplicate_count": len(duplicates),
                    "duplicate_timestamps": duplicate_timestamps.tolist(),
                },
            )
        self.logger.debug(f"✅ No duplicate timestamps: {file_path}")

    def validate_timestamp_format(self, df: pd.DataFrame, file_path: Path) -> None:
        """Validate timestamp format (DATA-009)"""
        # Find timestamp column
        timestamp_col = None
        for col in df.columns:
            if "timestamp" in col.lower() or "date" in col.lower() or "time" in col.lower():
                timestamp_col = col
                break

        if not timestamp_col:
            self.logger.debug(
                f"No timestamp column found in {file_path}, skipping timestamp format validation"
            )
            return

        try:
            # Try to convert to datetime
            pd.to_datetime(df[timestamp_col])
            self.logger.debug(f"✅ Timestamp format valid: {file_path}")
        except Exception as e:
            raise DataProviderError(
                "DATA-009",
                f"Invalid timestamp format in {file_path}: {e}",
                {"file_path": str(file_path), "error": str(e)},
            )

    def validate_hourly_alignment(self, df: pd.DataFrame, file_path: Path) -> None:
        """Validate timestamps are properly aligned based on data type (DATA-010)"""
        # Find timestamp column
        timestamp_col = None
        for col in df.columns:
            if "timestamp" in col.lower() or "date" in col.lower() or "time" in col.lower():
                timestamp_col = col
                break

        if not timestamp_col:
            self.logger.debug(
                f"No timestamp column found in {file_path}, skipping alignment validation"
            )
            return

        try:
            timestamps = pd.to_datetime(df[timestamp_col])
            file_path_str = str(file_path).lower()

            # Determine expected alignment based on data type
            if "ml_data" in file_path_str or "predictions" in file_path_str:
                # ML prediction data uses 5-minute intervals
                # Check if timestamps are aligned to 5-minute intervals
                non_aligned = timestamps[
                    (timestamps.dt.minute % 5 != 0) | (timestamps.dt.second != 0)
                ]
                if len(non_aligned) > 0:
                    raise DataProviderError(
                        "DATA-010",
                        f"Data timestamps not 5-minute aligned in {file_path}: {len(non_aligned)} non-aligned timestamps",
                        {
                            "file_path": str(file_path),
                            "non_aligned_count": len(non_aligned),
                            "non_aligned_timestamps": non_aligned.tolist(),
                        },
                    )
                self.logger.debug(f"✅ Timestamps 5-minute aligned: {file_path}")
            elif "funding_rates" in file_path_str:
                # Funding rates should be aligned to 8-hour intervals (00:00, 08:00, 16:00)
                # Check if timestamps are aligned to 8-hour intervals
                non_aligned = timestamps[
                    (timestamps.dt.hour % 8 != 0)
                    | (timestamps.dt.minute != 0)
                    | (timestamps.dt.second != 0)
                ]
                if len(non_aligned) > 0:
                    raise DataProviderError(
                        "DATA-010",
                        f"Data timestamps not 8-hour aligned in {file_path}: {len(non_aligned)} non-aligned timestamps",
                        {
                            "file_path": str(file_path),
                            "non_aligned_count": len(non_aligned),
                            "non_aligned_timestamps": non_aligned.tolist(),
                        },
                    )
                self.logger.debug(f"✅ Timestamps 8-hour aligned: {file_path}")

            elif "staking" in file_path_str or "rewards" in file_path_str:
                # Staking rewards are typically daily, so just check for proper date alignment
                non_daily = timestamps[
                    (timestamps.dt.hour != 0)
                    | (timestamps.dt.minute != 0)
                    | (timestamps.dt.second != 0)
                ]
                if len(non_daily) > 0:
                    raise DataProviderError(
                        "DATA-010",
                        f"Data timestamps not daily aligned in {file_path}: {len(non_daily)} non-daily timestamps",
                        {
                            "file_path": str(file_path),
                            "non_daily_count": len(non_daily),
                            "non_daily_timestamps": non_daily.tolist(),
                        },
                    )
                self.logger.debug(f"✅ Timestamps daily aligned: {file_path}")

            else:
                # Default: Check if timestamps are hourly aligned (minutes and seconds should be 0)
                non_hourly = timestamps[(timestamps.dt.minute != 0) | (timestamps.dt.second != 0)]
                if len(non_hourly) > 0:
                    raise DataProviderError(
                        "DATA-010",
                        f"Data timestamps not hourly aligned in {file_path}: {len(non_hourly)} non-hourly timestamps",
                        {
                            "file_path": str(file_path),
                            "non_hourly_count": len(non_hourly),
                            "non_hourly_timestamps": non_hourly.tolist(),
                        },
                    )
                self.logger.debug(f"✅ Timestamps hourly aligned: {file_path}")

        except Exception as e:
            if isinstance(e, DataProviderError):
                raise
            raise DataProviderError(
                "DATA-010",
                f"Alignment validation failed for {file_path}: {e}",
                {"file_path": str(file_path), "error": str(e)},
            )

    def validate_data_gaps(self, df: pd.DataFrame, file_path: Path) -> None:
        """Validate no gaps in data with appropriate frequency based on data type (DATA-011)"""
        # Find timestamp column
        timestamp_col = None
        for col in df.columns:
            if "timestamp" in col.lower() or "date" in col.lower() or "time" in col.lower():
                timestamp_col = col
                break

        if not timestamp_col:
            self.logger.debug(f"No timestamp column found in {file_path}, skipping gap validation")
            return

        try:
            timestamps = pd.to_datetime(df[timestamp_col])
            timestamps = timestamps.sort_values()

            # Determine expected frequency based on file path and data type
            expected_freq = self._get_expected_frequency(file_path, df)

            # Create expected range with appropriate frequency
            start_time = timestamps.min()
            end_time = timestamps.max()
            expected_range = pd.date_range(start=start_time, end=end_time, freq=expected_freq)

            # Find missing timestamps
            missing_timestamps = set(expected_range) - set(timestamps)
            if missing_timestamps:
                missing_list = sorted(list(missing_timestamps))
                missing_percentage = len(missing_timestamps) / len(expected_range) * 100

                # Special handling for execution costs (daily lookup tables resampled to hourly)
                file_path_str = str(file_path).lower()
                if "execution_costs" in file_path_str:
                    # Execution costs are daily lookup tables, so gaps are expected
                    self.logger.debug(
                        f"✅ Allowing gaps for execution costs lookup table: {file_path} ({missing_percentage:.1f}% gaps)"
                    )
                    return

                # Special handling for known sparse data types
                if "seasonal_rewards" in file_path_str or "staking" in file_path_str:
                    # Seasonal rewards and staking data are sparse by nature
                    self.logger.debug(
                        f"✅ Allowing gaps for sparse data: {file_path} ({missing_percentage:.1f}% gaps)"
                    )
                    return

                # STRICT VALIDATION: 100% data quality required for all other data
                # Only allow gaps for known sparse data types
                if missing_percentage > 0.0:
                    raise DataProviderError(
                        "DATA-011",
                        f"Data contains significant gaps in {file_path}: {len(missing_timestamps)} missing {expected_freq} periods ({missing_percentage:.1f}%)",
                        {
                            "file_path": str(file_path),
                            "missing_count": len(missing_timestamps),
                            "missing_percentage": missing_percentage,
                            "expected_frequency": expected_freq,
                            "missing_timestamps": [
                                str(ts) for ts in missing_list[:10]
                            ],  # Show first 10
                        },
                    )
                else:
                    self.logger.warning(
                        f"Data has minor gaps in {file_path}: {len(missing_timestamps)} missing {expected_freq} periods ({missing_percentage:.1f}%) - proceeding"
                    )

            self.logger.debug(f"✅ No data gaps: {file_path}")

        except Exception as e:
            if isinstance(e, DataProviderError):
                raise
            raise DataProviderError(
                "DATA-011",
                f"Gap validation failed for {file_path}: {e}",
                {"file_path": str(file_path), "error": str(e)},
            )

    def _get_expected_frequency(self, file_path: Path, df: pd.DataFrame) -> str:
        """Determine expected data frequency based on file path and content."""
        file_path_str = str(file_path).lower()

        # ML prediction data uses 5-minute intervals
        if "ml_data" in file_path_str or "predictions" in file_path_str:
            return "5T"

        # Execution costs are daily lookup tables resampled to hourly (allow duplicates)
        if "execution_costs" in file_path_str:
            return "H"

        # Funding rates are updated every 8 hours
        if "funding_rates" in file_path_str:
            return "8H"

        # Staking rewards are typically daily
        if "staking" in file_path_str or "rewards" in file_path_str:
            return "D"

        # Protocol data (like AAVE rates) are typically hourly
        if "protocol_data" in file_path_str:
            return "H"

        # Market data (prices, OHLCV) are typically hourly
        if any(x in file_path_str for x in ["market_data", "prices", "ohlcv", "futures"]):
            return "H"

        # Default to hourly for unknown data types
        return "H"

    def validate_data_requirements(
        self, data_requirements: List[str], available_data: List[str]
    ) -> None:
        """Validate data requirements can be satisfied (DATA-012)"""
        missing_data = set(data_requirements) - set(available_data)
        if missing_data:
            raise DataProviderError(
                "DATA-012",
                f"Data validation failed: missing required data types: {missing_data}",
                {
                    "missing_data": list(missing_data),
                    "available_data": available_data,
                    "REQUIRED_DATA": data_requirements,
                },
            )
        self.logger.debug(f"✅ Data requirements satisfied: {data_requirements}")

    def validate_data_provider_initialization(
        self, provider_name: str, config: Dict[str, Any]
    ) -> None:
        """Validate data provider initialization (DATA-013)"""
        required_fields = ["mode", "data_requirements"]

        # Handle both Pydantic models and dictionaries
        if hasattr(config, "model_dump"):
            # Pydantic model
            config_dict = config.model_dump()
            missing_fields = [field for field in required_fields if field not in config_dict]
        else:
            # Dictionary
            missing_fields = [field for field in required_fields if field not in config]

        if missing_fields:
            raise DataProviderError(
                "DATA-013",
                f"Data provider initialization failed for {provider_name}: missing required fields: {missing_fields}",
                {
                    "provider_name": provider_name,
                    "missing_fields": missing_fields,
                    "config": config,
                },
            )

        self.logger.debug(f"✅ Data provider initialization valid: {provider_name}")

    def validate_complete_file(
        self,
        file_path: Path,
        required_columns: List[str] = None,
        expected_types: Dict[str, str] = None,
        allow_nulls: bool = False,
    ) -> pd.DataFrame:
        """Run complete validation suite on a file"""
        self.logger.info(f"🔍 Validating file: {file_path}")

        # Basic file validation
        self.validate_file_existence(file_path)
        df = self.validate_csv_parsing(file_path)
        self.validate_empty_file(df, file_path)

        # Date and timestamp validation
        self.validate_date_range(df, file_path)
        self.validate_timestamp_format(df, file_path)
        self.validate_hourly_alignment(df, file_path)
        self.validate_duplicate_timestamps(df, file_path)
        self.validate_data_gaps(df, file_path)

        # Data content validation
        if required_columns:
            self.validate_required_columns(df, required_columns, file_path)

        if expected_types:
            self.validate_data_types(df, expected_types, file_path)

        self.validate_null_values(df, file_path, allow_nulls)

        # Apply column mapping for camelCase to snake_case conversion
        column_mapping = {
            "liquidityIndex": "liquidity_index",
            "variableBorrowIndex": "variable_borrow_index",
            "currentLiquidityRate": "supply_rate",
            "currentVariableBorrowRate": "borrow_rate",
        }
        df_mapped = df.rename(columns=column_mapping)

        self.logger.info(f"✅ File validation complete: {file_path}")
        return df_mapped

    def get_error_summary(self) -> Dict[str, str]:
        """Get summary of all error codes"""
        return self.error_codes.copy()
