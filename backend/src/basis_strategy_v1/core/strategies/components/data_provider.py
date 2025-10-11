"""
Data Provider Component

Provides data access for all strategy components with caching, validation,
and on-demand loading capabilities.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 8 (Data Provider Architecture)
Reference: docs/specs/06_DATA_PROVIDER.md - Data provider specification
"""

import os
import pandas as pd
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path

from ...infrastructure.data.data_loader import DataLoader
from ...infrastructure.data.data_validator import DataValidator
from ...infrastructure.logging.structured_logger import get_data_provider_logger


class DataProvider:
    """Provides data access for strategy components."""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_data_provider_logger()
        
        # Data configuration
        self.data_dir = config.get('data_dir', 'data')
        self.data_mode = config.get('data_mode', 'csv')
        self.cache_ttl = config.get('cache_ttl', 300)  # 5 minutes
        
        # Data components
        self.data_loader = DataLoader(config)
        self.data_validator = DataValidator(config)
        
        # Data cache
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, float] = {}
        
        self.logger.info("Data Provider initialized", event_type='initialization')
    
    def get_market_data(
        self,
        asset: str,
        start_date: str,
        end_date: str,
        data_type: str = 'price'
    ) -> pd.DataFrame:
        """
        Get market data for an asset.
        
        Args:
            asset: Asset symbol (e.g., 'BTC', 'ETH', 'USDT')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            data_type: Type of data ('price', 'volume', 'funding_rate')
            
        Returns:
            DataFrame with market data
        """
        cache_key = f"market_{asset}_{data_type}_{start_date}_{end_date}"
        
        # Check cache first
        if self._is_cached(cache_key):
            self.logger.debug(f"Returning cached market data: {cache_key}")
            return self.cache[cache_key]['data']
        
        try:
            # Load data
            data = self.data_loader.load_market_data(asset, start_date, end_date, data_type)
            
            # Validate data
            if not self.data_validator.validate_market_data(data, asset, data_type):
                raise ValueError(f"Invalid market data for {asset}")
            
            # Cache data
            self._cache_data(cache_key, data)
            
            self.logger.info(
                f"Market data loaded: {asset} {data_type}",
                event_type='data_loaded',
                asset=asset,
                data_type=data_type,
                rows=len(data),
                start_date=start_date,
                end_date=end_date
            )
            
            return data
            
        except Exception as e:
            self.logger.error(
                f"Failed to load market data: {asset} {data_type}",
                event_type='data_load_error',
                asset=asset,
                data_type=data_type,
                error=str(e)
            )
            raise
    
    def get_protocol_data(
        self,
        protocol: str,
        data_type: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Get protocol data (e.g., AAVE rates, LST data).
        
        Args:
            protocol: Protocol name (e.g., 'aave', 'lido', 'etherfi')
            data_type: Type of data (e.g., 'rates', 'apy', 'stake')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DataFrame with protocol data
        """
        cache_key = f"protocol_{protocol}_{data_type}_{start_date}_{end_date}"
        
        # Check cache first
        if self._is_cached(cache_key):
            self.logger.debug(f"Returning cached protocol data: {cache_key}")
            return self.cache[cache_key]['data']
        
        try:
            # Load data
            data = self.data_loader.load_protocol_data(protocol, data_type, start_date, end_date)
            
            # Validate data
            if not self.data_validator.validate_protocol_data(data, protocol, data_type):
                raise ValueError(f"Invalid protocol data for {protocol}")
            
            # Cache data
            self._cache_data(cache_key, data)
            
            self.logger.info(
                f"Protocol data loaded: {protocol} {data_type}",
                event_type='data_loaded',
                protocol=protocol,
                data_type=data_type,
                rows=len(data),
                start_date=start_date,
                end_date=end_date
            )
            
            return data
            
        except Exception as e:
            self.logger.error(
                f"Failed to load protocol data: {protocol} {data_type}",
                event_type='data_load_error',
                protocol=protocol,
                data_type=data_type,
                error=str(e)
            )
            raise
    
    def get_execution_costs(self, venue: str, asset: str) -> Dict[str, float]:
        """
        Get execution costs for a venue and asset.
        
        Args:
            venue: Venue name (e.g., 'binance', 'bybit', 'okx')
            asset: Asset symbol
            
        Returns:
            Dictionary with cost information
        """
        cache_key = f"costs_{venue}_{asset}"
        
        # Check cache first
        if self._is_cached(cache_key):
            self.logger.debug(f"Returning cached execution costs: {cache_key}")
            return self.cache[cache_key]['data']
        
        try:
            # Load costs
            costs = self.data_loader.load_execution_costs(venue, asset)
            
            # Cache data
            self._cache_data(cache_key, costs)
            
            self.logger.info(
                f"Execution costs loaded: {venue} {asset}",
                event_type='data_loaded',
                venue=venue,
                asset=asset
            )
            
            return costs
            
        except Exception as e:
            self.logger.error(
                f"Failed to load execution costs: {venue} {asset}",
                event_type='data_load_error',
                venue=venue,
                asset=asset,
                error=str(e)
            )
            raise
    
    def get_gas_costs(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get gas costs data.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DataFrame with gas costs data
        """
        cache_key = f"gas_{start_date}_{end_date}"
        
        # Check cache first
        if self._is_cached(cache_key):
            self.logger.debug(f"Returning cached gas costs: {cache_key}")
            return self.cache[cache_key]['data']
        
        try:
            # Load data
            data = self.data_loader.load_gas_costs(start_date, end_date)
            
            # Cache data
            self._cache_data(cache_key, data)
            
            self.logger.info(
                f"Gas costs loaded",
                event_type='data_loaded',
                rows=len(data),
                start_date=start_date,
                end_date=end_date
            )
            
            return data
            
        except Exception as e:
            self.logger.error(
                f"Failed to load gas costs",
                event_type='data_load_error',
                error=str(e)
            )
            raise
    
    def get_data_availability(
        self,
        data_type: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get data availability information.
        
        Args:
            data_type: Type of data to check
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with availability information
        """
        try:
            availability = self.data_loader.check_data_availability(data_type, start_date, end_date)
            
            self.logger.info(
                f"Data availability checked: {data_type}",
                event_type='data_availability_checked',
                data_type=data_type,
                start_date=start_date,
                end_date=end_date,
                available=availability.get('available', False)
            )
            
            return availability
            
        except Exception as e:
            self.logger.error(
                f"Failed to check data availability: {data_type}",
                event_type='data_availability_error',
                data_type=data_type,
                error=str(e)
            )
            raise
    
    def clear_cache(self, pattern: Optional[str] = None):
        """Clear data cache."""
        if pattern:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
                del self.cache_timestamps[key]
            self.logger.info(f"Cache cleared for pattern: {pattern}")
        else:
            self.cache.clear()
            self.cache_timestamps.clear()
            self.logger.info("All cache cleared")
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if data is cached and not expired."""
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache_timestamps.get(cache_key, 0)
        if time.time() - cache_time > self.cache_ttl:
            # Cache expired
            del self.cache[cache_key]
            del self.cache_timestamps[cache_key]
            return False
        
        return True
    
    def _cache_data(self, cache_key: str, data: Any):
        """Cache data with timestamp."""
        self.cache[cache_key] = data
        self.cache_timestamps[cache_key] = time.time()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get data provider health status."""
        return {
            'status': 'healthy',
            'data_mode': self.data_mode,
            'data_directory': self.data_dir,
            'cache_size': len(self.cache),
            'cache_ttl': self.cache_ttl,
            'data_loader_healthy': self.data_loader is not None,
            'data_validator_healthy': self.data_validator is not None
        }