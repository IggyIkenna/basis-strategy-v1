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
        self.data_dir = Path(data_dir) if data_dir else Path('data')
        self.logger = logging.getLogger(__name__)
        
        # Environment variables for date range validation
        self.start_date = os.getenv('BASIS_DATA_START_DATE')
        self.end_date = os.getenv('BASIS_DATA_END_DATE')
        
        # Error code mappings
        self.error_codes = {
            'DATA-001': 'Required data file not found',
            'DATA-002': 'CSV parsing failed',
            'DATA-003': 'Data file is empty',
            'DATA-004': 'Data date range mismatch',
            'DATA-005': 'Required column missing',
            'DATA-006': 'Invalid data type in column',
            'DATA-007': 'Data contains null values',
            'DATA-008': 'Data contains duplicate timestamps',
            'DATA-009': 'Data timestamp format invalid',
            'DATA-010': 'Data timestamp not hourly aligned',
            'DATA-011': 'Data contains gaps (missing hours)',
            'DATA-012': 'Data validation failed',
            'DATA-013': 'Data provider initialization failed'
        }
    
    def validate_file_existence(self, file_path: Path) -> None:
        """Validate that required data file exists (DATA-001)"""
        if not file_path.exists():
            raise DataProviderError(
                'DATA-001',
                f"Required data file not found: {file_path}",
                {'file_path': str(file_path)}
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
                'DATA-002',
                f"CSV parsing failed for {file_path}: {e}",
                {'file_path': str(file_path), 'error': str(e)}
            )
    
    def validate_empty_file(self, df: pd.DataFrame, file_path: Path) -> None:
        """Validate file is not empty (DATA-003)"""
        if len(df) == 0:
            raise DataProviderError(
                'DATA-003',
                f"Data file is empty: {file_path}",
                {'file_path': str(file_path), 'rows': 0}
            )
        self.logger.debug(f"✅ File not empty: {file_path} ({len(df)} rows)")
    
    def validate_date_range(self, df: pd.DataFrame, file_path: Path) -> None:
        """Validate data date range against environment variables (DATA-004)"""
        if not self.start_date or not self.end_date:
            self.logger.warning("BASIS_DATA_START_DATE or BASIS_DATA_END_DATE not set, skipping date range validation")
            return
        
        try:
            # Check if timestamp column exists
            timestamp_col = None
            for col in df.columns:
                if 'timestamp' in col.lower() or 'date' in col.lower() or 'time' in col.lower():
                    timestamp_col = col
                    break
            
            if not timestamp_col:
                self.logger.warning(f"No timestamp column found in {file_path}, skipping date range validation")
                return
            
            # Convert timestamps to datetime
            df_timestamps = pd.to_datetime(df[timestamp_col])
            min_date = df_timestamps.min()
            max_date = df_timestamps.max()
            
            expected_start = pd.to_datetime(self.start_date)
            expected_end = pd.to_datetime(self.end_date)
            
            # Handle timezone comparison - make both timezone-aware or both timezone-naive
            if min_date.tz is not None and expected_start.tz is None:
                expected_start = expected_start.tz_localize('UTC')
                expected_end = expected_end.tz_localize('UTC')
            elif min_date.tz is None and expected_start.tz is not None:
                min_date = min_date.tz_localize('UTC')
                max_date = max_date.tz_localize('UTC')
            
            if min_date < expected_start or max_date > expected_end:
                raise DataProviderError(
                    'DATA-004',
                    f"Data date range mismatch in {file_path}. Expected: {expected_start} to {expected_end}, Got: {min_date} to {max_date}",
                    {
                        'file_path': str(file_path),
                        'expected_start': str(expected_start),
                        'expected_end': str(expected_end),
                        'actual_start': str(min_date),
                        'actual_end': str(max_date)
                    }
                )
            
            self.logger.debug(f"✅ Date range valid: {file_path} ({min_date} to {max_date})")
            
        except Exception as e:
            if isinstance(e, DataProviderError):
                raise
            raise DataProviderError(
                'DATA-004',
                f"Date range validation failed for {file_path}: {e}",
                {'file_path': str(file_path), 'error': str(e)}
            )
    
    def validate_required_columns(self, df: pd.DataFrame, required_columns: List[str], file_path: Path) -> None:
        """Validate required columns exist (DATA-005)"""
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise DataProviderError(
                'DATA-005',
                f"Required columns missing in {file_path}: {missing_columns}",
                {
                    'file_path': str(file_path),
                    'missing_columns': list(missing_columns),
                    'available_columns': list(df.columns)
                }
            )
        self.logger.debug(f"✅ Required columns present: {file_path} ({required_columns})")
    
    def validate_data_types(self, df: pd.DataFrame, expected_types: Dict[str, str], file_path: Path) -> None:
        """Validate data types in columns (DATA-006)"""
        for column, expected_type in expected_types.items():
            if column not in df.columns:
                continue
            
            actual_type = str(df[column].dtype)
            if expected_type not in actual_type:
                raise DataProviderError(
                    'DATA-006',
                    f"Invalid data type in column '{column}' of {file_path}. Expected: {expected_type}, Got: {actual_type}",
                    {
                        'file_path': str(file_path),
                        'column': column,
                        'expected_type': expected_type,
                        'actual_type': actual_type
                    }
                )
        self.logger.debug(f"✅ Data types valid: {file_path}")
    
    def validate_null_values(self, df: pd.DataFrame, file_path: Path, allow_nulls: bool = False) -> None:
        """Validate no null values (DATA-007)"""
        if allow_nulls:
            self.logger.debug(f"✅ Null values allowed: {file_path}")
            return
        
        null_columns = df.columns[df.isnull().any()].tolist()
        if null_columns:
            null_counts = df[null_columns].isnull().sum().to_dict()
            raise DataProviderError(
                'DATA-007',
                f"Data contains null values in {file_path}: {null_columns}",
                {
                    'file_path': str(file_path),
                    'null_columns': null_columns,
                    'null_counts': null_counts
                }
            )
        self.logger.debug(f"✅ No null values: {file_path}")
    
    def validate_duplicate_timestamps(self, df: pd.DataFrame, file_path: Path) -> None:
        """Validate no duplicate timestamps (DATA-008)"""
        # Find timestamp column
        timestamp_col = None
        for col in df.columns:
            if 'timestamp' in col.lower() or 'date' in col.lower() or 'time' in col.lower():
                timestamp_col = col
                break
        
        if not timestamp_col:
            self.logger.debug(f"No timestamp column found in {file_path}, skipping duplicate validation")
            return
        
        duplicates = df[df.duplicated(subset=[timestamp_col], keep=False)]
        if len(duplicates) > 0:
            duplicate_timestamps = duplicates[timestamp_col].unique()
            raise DataProviderError(
                'DATA-008',
                f"Data contains duplicate timestamps in {file_path}: {len(duplicate_timestamps)} duplicates",
                {
                    'file_path': str(file_path),
                    'duplicate_count': len(duplicates),
                    'duplicate_timestamps': duplicate_timestamps.tolist()
                }
            )
        self.logger.debug(f"✅ No duplicate timestamps: {file_path}")
    
    def validate_timestamp_format(self, df: pd.DataFrame, file_path: Path) -> None:
        """Validate timestamp format (DATA-009)"""
        # Find timestamp column
        timestamp_col = None
        for col in df.columns:
            if 'timestamp' in col.lower() or 'date' in col.lower() or 'time' in col.lower():
                timestamp_col = col
                break
        
        if not timestamp_col:
            self.logger.debug(f"No timestamp column found in {file_path}, skipping timestamp format validation")
            return
        
        try:
            # Try to convert to datetime
            pd.to_datetime(df[timestamp_col])
            self.logger.debug(f"✅ Timestamp format valid: {file_path}")
        except Exception as e:
            raise DataProviderError(
                'DATA-009',
                f"Invalid timestamp format in {file_path}: {e}",
                {'file_path': str(file_path), 'error': str(e)}
            )
    
    def validate_hourly_alignment(self, df: pd.DataFrame, file_path: Path) -> None:
        """Validate timestamps are hourly aligned (DATA-010)"""
        # Find timestamp column
        timestamp_col = None
        for col in df.columns:
            if 'timestamp' in col.lower() or 'date' in col.lower() or 'time' in col.lower():
                timestamp_col = col
                break
        
        if not timestamp_col:
            self.logger.debug(f"No timestamp column found in {file_path}, skipping hourly alignment validation")
            return
        
        try:
            timestamps = pd.to_datetime(df[timestamp_col])
            
            # Check if timestamps are hourly aligned (minutes and seconds should be 0)
            non_hourly = timestamps[(timestamps.dt.minute != 0) | (timestamps.dt.second != 0)]
            if len(non_hourly) > 0:
                raise DataProviderError(
                    'DATA-010',
                    f"Data timestamps not hourly aligned in {file_path}: {len(non_hourly)} non-hourly timestamps",
                    {
                        'file_path': str(file_path),
                        'non_hourly_count': len(non_hourly),
                        'non_hourly_timestamps': non_hourly.tolist()
                    }
                )
            
            self.logger.debug(f"✅ Timestamps hourly aligned: {file_path}")
            
        except Exception as e:
            if isinstance(e, DataProviderError):
                raise
            raise DataProviderError(
                'DATA-010',
                f"Hourly alignment validation failed for {file_path}: {e}",
                {'file_path': str(file_path), 'error': str(e)}
            )
    
    def validate_data_gaps(self, df: pd.DataFrame, file_path: Path) -> None:
        """Validate no gaps in hourly data (DATA-011)"""
        # Find timestamp column
        timestamp_col = None
        for col in df.columns:
            if 'timestamp' in col.lower() or 'date' in col.lower() or 'time' in col.lower():
                timestamp_col = col
                break
        
        if not timestamp_col:
            self.logger.debug(f"No timestamp column found in {file_path}, skipping gap validation")
            return
        
        try:
            timestamps = pd.to_datetime(df[timestamp_col])
            timestamps = timestamps.sort_values()
            
            # Create expected hourly range
            start_time = timestamps.min()
            end_time = timestamps.max()
            expected_range = pd.date_range(start=start_time, end=end_time, freq='H')
            
            # Find missing timestamps
            missing_timestamps = set(expected_range) - set(timestamps)
            if missing_timestamps:
                missing_list = sorted(list(missing_timestamps))
                raise DataProviderError(
                    'DATA-011',
                    f"Data contains gaps in {file_path}: {len(missing_timestamps)} missing hours",
                    {
                        'file_path': str(file_path),
                        'missing_count': len(missing_timestamps),
                        'missing_timestamps': [str(ts) for ts in missing_list[:10]]  # Show first 10
                    }
                )
            
            self.logger.debug(f"✅ No data gaps: {file_path}")
            
        except Exception as e:
            if isinstance(e, DataProviderError):
                raise
            raise DataProviderError(
                'DATA-011',
                f"Gap validation failed for {file_path}: {e}",
                {'file_path': str(file_path), 'error': str(e)}
            )
    
    def validate_data_requirements(self, data_requirements: List[str], available_data: List[str]) -> None:
        """Validate data requirements can be satisfied (DATA-012)"""
        missing_data = set(data_requirements) - set(available_data)
        if missing_data:
            raise DataProviderError(
                'DATA-012',
                f"Data validation failed: missing required data types: {missing_data}",
                {
                    'missing_data': list(missing_data),
                    'available_data': available_data,
                    'required_data': data_requirements
                }
            )
        self.logger.debug(f"✅ Data requirements satisfied: {data_requirements}")
    
    def validate_data_provider_initialization(self, provider_name: str, config: Dict[str, Any]) -> None:
        """Validate data provider initialization (DATA-013)"""
        required_fields = ['mode', 'data_requirements']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            raise DataProviderError(
                'DATA-013',
                f"Data provider initialization failed for {provider_name}: missing required fields: {missing_fields}",
                {
                    'provider_name': provider_name,
                    'missing_fields': missing_fields,
                    'config': config
                }
            )
        
        self.logger.debug(f"✅ Data provider initialization valid: {provider_name}")
    
    def validate_complete_file(self, file_path: Path, required_columns: List[str] = None, 
                             expected_types: Dict[str, str] = None, allow_nulls: bool = False) -> pd.DataFrame:
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
        
        self.logger.info(f"✅ File validation complete: {file_path}")
        return df
    
    def get_error_summary(self) -> Dict[str, str]:
        """Get summary of all error codes"""
        return self.error_codes.copy()