"""
Mode-Agnostic Results Store

Provides mode-agnostic results storage that works for both backtest and live modes.
Manages results storage across all venues and provides generic storage logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/11_RESULTS_STORE.md - Mode-agnostic results storage
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

class ResultsStore:
    """Mode-agnostic results store that works for both backtest and live modes"""
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize results store.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        
        # Results tracking
        self.results_history = []
        self.stored_results = {}
        
        # Storage configuration
        self.storage_path = config.get('storage_path', './results')
        self.storage_format = config.get('storage_format', 'json')
        
        logger.info("ResultsStore initialized (mode-agnostic)")
    
    def store_results(self, results: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Store results regardless of mode (backtest or live).
        
        Args:
            results: Results dictionary to store
            timestamp: Current timestamp
            
        Returns:
            Dictionary with storage result
        """
        try:
            # Validate results
            validation_result = self._validate_results(results)
            if not validation_result['valid']:
                return {
                    'status': 'failed',
                    'error': validation_result['error'],
                    'timestamp': timestamp
                }
            
            # Store results based on format
            if self.storage_format == 'json':
                storage_result = self._store_results_json(results, timestamp)
            elif self.storage_format == 'csv':
                storage_result = self._store_results_csv(results, timestamp)
            elif self.storage_format == 'parquet':
                storage_result = self._store_results_parquet(results, timestamp)
            else:
                return {
                    'status': 'failed',
                    'error': f"Unsupported storage format: {self.storage_format}",
                    'timestamp': timestamp
                }
            
            if storage_result['success']:
                # Add to results history
                self.results_history.append({
                    'results': results,
                    'timestamp': timestamp,
                    'storage_result': storage_result
                })
                
                # Add to stored results
                self.stored_results[timestamp.isoformat()] = results
                
                logger.info(f"Successfully stored results for {timestamp}")
            else:
                logger.error(f"Failed to store results for {timestamp}: {storage_result.get('error', 'Unknown error')}")
            
            return {
                'status': 'success' if storage_result['success'] else 'failed',
                'timestamp': timestamp,
                'storage_result': storage_result
            }
            
        except Exception as e:
            logger.error(f"Error storing results: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def load_results(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Load results regardless of mode (backtest or live).
        
        Args:
            timestamp: Timestamp to load results for
            
        Returns:
            Dictionary with loaded results
        """
        try:
            # Check if results are in memory
            timestamp_str = timestamp.isoformat()
            if timestamp_str in self.stored_results:
                return {
                    'status': 'success',
                    'results': self.stored_results[timestamp_str],
                    'timestamp': timestamp,
                    'source': 'memory'
                }
            
            # Load from storage
            if self.storage_format == 'json':
                load_result = self._load_results_json(timestamp)
            elif self.storage_format == 'csv':
                load_result = self._load_results_csv(timestamp)
            elif self.storage_format == 'parquet':
                load_result = self._load_results_parquet(timestamp)
            else:
                return {
                    'status': 'failed',
                    'error': f"Unsupported storage format: {self.storage_format}",
                    'timestamp': timestamp
                }
            
            if load_result['success']:
                # Add to stored results
                self.stored_results[timestamp_str] = load_result['results']
                
                logger.info(f"Successfully loaded results for {timestamp}")
            else:
                logger.error(f"Failed to load results for {timestamp}: {load_result.get('error', 'Unknown error')}")
            
            return {
                'status': 'success' if load_result['success'] else 'failed',
                'results': load_result.get('results', {}),
                'timestamp': timestamp,
                'source': 'storage'
            }
            
        except Exception as e:
            logger.error(f"Error loading results: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': timestamp
            }
    
    def get_results_summary(self) -> Dict[str, Any]:
        """Get results summary."""
        try:
            return {
                'results_history': self.results_history,
                'stored_results_count': len(self.stored_results),
                'storage_path': self.storage_path,
                'storage_format': self.storage_format,
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting results summary: {e}")
            return {
                'results_history': [],
                'stored_results_count': 0,
                'storage_path': self.storage_path,
                'storage_format': self.storage_format,
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def _validate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate results before storage."""
        try:
            # Check if results is a dictionary
            if not isinstance(results, dict):
                return {
                    'valid': False,
                    'error': "Results must be a dictionary"
                }
            
            # Check for required fields
            required_fields = ['timestamp', 'total_usdt_balance', 'total_share_class_balance']
            for field in required_fields:
                if field not in results:
                    return {
                        'valid': False,
                        'error': f"Missing required field: {field}"
                    }
            
            return {'valid': True}
        except Exception as e:
            logger.error(f"Error validating results: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _store_results_json(self, results: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Store results in JSON format."""
        try:
            # Create storage directory if it doesn't exist
            os.makedirs(self.storage_path, exist_ok=True)
            
            # Create filename
            filename = f"results_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.storage_path, filename)
            
            # Store results
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            return {
                'success': True,
                'filepath': filepath,
                'format': 'json'
            }
        except Exception as e:
            logger.error(f"Error storing results as JSON: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _store_results_csv(self, results: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Store results in CSV format."""
        try:
            # Create storage directory if it doesn't exist
            os.makedirs(self.storage_path, exist_ok=True)
            
            # Create filename
            filename = f"results_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.storage_path, filename)
            
            # Convert results to DataFrame
            df = pd.DataFrame([results])
            
            # Store results
            df.to_csv(filepath, index=False)
            
            return {
                'success': True,
                'filepath': filepath,
                'format': 'csv'
            }
        except Exception as e:
            logger.error(f"Error storing results as CSV: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _store_results_parquet(self, results: Dict[str, Any], timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Store results in Parquet format."""
        try:
            # Create storage directory if it doesn't exist
            os.makedirs(self.storage_path, exist_ok=True)
            
            # Create filename
            filename = f"results_{timestamp.strftime('%Y%m%d_%H%M%S')}.parquet"
            filepath = os.path.join(self.storage_path, filename)
            
            # Convert results to DataFrame
            df = pd.DataFrame([results])
            
            # Store results
            df.to_parquet(filepath, index=False)
            
            return {
                'success': True,
                'filepath': filepath,
                'format': 'parquet'
            }
        except Exception as e:
            logger.error(f"Error storing results as Parquet: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _load_results_json(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Load results from JSON format."""
        try:
            # Create filename
            filename = f"results_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.storage_path, filename)
            
            # Check if file exists
            if not os.path.exists(filepath):
                return {
                    'success': False,
                    'error': f"Results file not found: {filepath}"
                }
            
            # Load results
            with open(filepath, 'r') as f:
                results = json.load(f)
            
            return {
                'success': True,
                'results': results,
                'filepath': filepath
            }
        except Exception as e:
            logger.error(f"Error loading results from JSON: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _load_results_csv(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Load results from CSV format."""
        try:
            # Create filename
            filename = f"results_{timestamp.strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.storage_path, filename)
            
            # Check if file exists
            if not os.path.exists(filepath):
                return {
                    'success': False,
                    'error': f"Results file not found: {filepath}"
                }
            
            # Load results
            df = pd.read_csv(filepath)
            results = df.iloc[0].to_dict()
            
            return {
                'success': True,
                'results': results,
                'filepath': filepath
            }
        except Exception as e:
            logger.error(f"Error loading results from CSV: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _load_results_parquet(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Load results from Parquet format."""
        try:
            # Create filename
            filename = f"results_{timestamp.strftime('%Y%m%d_%H%M%S')}.parquet"
            filepath = os.path.join(self.storage_path, filename)
            
            # Check if file exists
            if not os.path.exists(filepath):
                return {
                    'success': False,
                    'error': f"Results file not found: {filepath}"
                }
            
            # Load results
            df = pd.read_parquet(filepath)
            results = df.iloc[0].to_dict()
            
            return {
                'success': True,
                'results': results,
                'filepath': filepath
            }
        except Exception as e:
            logger.error(f"Error loading results from Parquet: {e}")
            return {
                'success': False,
                'error': str(e)
            }
