"""
ETH Leveraged Data Provider

Provides data for ETH leveraged staking strategy with LST rewards and seasonal bonuses.

Data Requirements:
- eth_prices: ETH/USDT spot prices (Binance)
- weeth_prices: weETH/ETH oracle prices (AAVE)
- aave_lending_rates: AAVE rates (weETH, WETH)
- staking_rewards: Base staking yields
- eigen_rewards: EIGEN distributions
- gas_costs: Ethereum gas prices
- execution_costs: Execution cost models
- aave_risk_params: AAVE v3 risk parameters

Reference: configs/modes/eth_leveraged.yaml
Reference: docs/specs/09_DATA_PROVIDER.md
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List
import json

from .base_data_provider import BaseDataProvider
from ..infrastructure.data.historical_data_provider import _validate_data_file, DataProviderError

logger = logging.getLogger(__name__)


class ETHLeveragedDataProvider(BaseDataProvider):
    """Data provider for ETH leveraged staking strategy"""
    
    def __init__(self, execution_mode: str, config: Dict[str, Any]):
        super().__init__(execution_mode, config)
        self.available_data_types = [
            'eth_prices',
            'weeth_prices',
            'aave_lending_rates',
            'staking_rewards',
            'eigen_rewards',
            'gas_costs',
            'execution_costs',
            'aave_risk_params'
        ]
        self.lst_type = config.get('lst_type', 'weeth')
        self.rewards_mode = config.get('rewards_mode', 'base_only')
        self.data = {}
    
    def validate_data_requirements(self, data_requirements: List[str]) -> None:
        """
        Validate that this provider can satisfy data requirements.
        
        Args:
            data_requirements: List of required data types
            
        Raises:
            ValueError: If provider cannot satisfy requirements
        """
        unsupported = set(data_requirements) - set(self.available_data_types)
        if unsupported:
            raise ValueError(
                f"ETHLeveragedDataProvider cannot satisfy requirements: {unsupported}. "
                f"Available: {self.available_data_types}"
            )
        
        logger.info(f"✅ ETHLeveragedDataProvider can satisfy all requirements: {data_requirements}")
    
    def load_data(self) -> None:
        """Load all required data for ETH leveraged staking strategy."""
        logger.info(f"🔄 Loading data for ETH leveraged staking strategy...")
        
        try:
            # Load ETH spot prices
            self._load_eth_spot_prices()
            
            # Load LST oracle prices
            self._load_lst_oracle_prices()
            
            # Load AAVE lending rates
            self._load_aave_rates()
            
            # Load staking rewards
            self._load_staking_rewards()
            
            # Load seasonal rewards (EIGEN/ETHFI) if needed
            if self.rewards_mode != 'base_only':
                self._load_seasonal_rewards()
            
            # Load protocol token prices for KING unwrapping
            self._load_protocol_token_prices()
            
            # Load gas costs
            self._load_gas_costs()
            
            # Load execution costs
            self._load_execution_costs()
            
            # Load AAVE risk parameters
            self._load_aave_risk_parameters()
            
            # Validate all data requirements are satisfied
            self._validate_loaded_data()
            
            self._data_loaded = True
            logger.info(f"✅ ETH leveraged data loaded successfully: {len(self.data)} datasets")
            
        except Exception as e:
            logger.error(f"❌ Failed to load ETH leveraged data: {e}")
            raise DataProviderError('DATA-004', message=f"ETH leveraged data loading failed: {e}")
    
    def get_data(self, timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Return standardized data structure for ETH leveraged staking strategy.
        
        Args:
            timestamp: Timestamp for data query
            
        Returns:
            Standardized data structure with market_data and protocol_data
        """
        if not self._data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        data = self._get_standardized_structure(timestamp)
        
        # Market data - ETH spot prices
        if 'eth_spot_binance' in self.data:
            eth_data = self.data['eth_spot_binance']
            ts = eth_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['market_data']['prices']['ETH'] = eth_data.loc[ts, 'open']
        
        # Protocol data - LST oracle prices
        if f'{self.lst_type.lower()}_oracle' in self.data:
            oracle_data = self.data[f'{self.lst_type.lower()}_oracle']
            ts = oracle_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['protocol_data']['oracle_prices'][self.lst_type.lower()] = oracle_data.loc[ts, 'oracle_price_eth']
        
        # Protocol data - AAVE rates and indexes
        for asset in ['weeth', 'weth']:
            rates_key = f'{asset}_rates'
            if rates_key in self.data:
                rates_data = self.data[rates_key]
                ts = rates_data.index.asof(timestamp)
                if not pd.isna(ts):
                    row = rates_data.loc[ts]
                    data['protocol_data']['aave_indexes'][f'a{asset.upper()}'] = row.get('liquidityIndex', 1.0)
                    data['protocol_data']['protocol_rates'][f'aave_{asset}_supply'] = row.get('liquidity_apy', 0.0)
                    data['protocol_data']['protocol_rates'][f'aave_{asset}_borrow'] = row.get('borrow_apy', 0.0)
        
        # Protocol data - staking rewards
        if 'staking_yields' in self.data:
            staking_data = self.data['staking_yields']
            ts = staking_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['protocol_data']['staking_rewards']['base_staking'] = staking_data.loc[ts, 'yield']
        
        # Protocol data - seasonal rewards
        if 'seasonal_rewards' in self.data and self.rewards_mode != 'base_only':
            rewards_data = self.data['seasonal_rewards']
            ts = rewards_data.index.asof(timestamp)
            if not pd.isna(ts):
                row = rewards_data.loc[ts]
                data['protocol_data']['staking_rewards']['eigen_rewards'] = row.get('eigen_rewards', 0.0)
                data['protocol_data']['staking_rewards']['ethfi_rewards'] = row.get('ethfi_rewards', 0.0)
        
        # Protocol data - protocol token prices
        for token in ['eigen', 'ethfi']:
            for price_type in ['eth', 'usdt']:
                price_key = f'{token}_{price_type}_price'
                if price_key in self.data:
                    price_data = self.data[price_key]
                    ts = price_data.index.asof(timestamp)
                    if not pd.isna(ts):
                        data['protocol_data']['protocol_rates'][f'{token}_{price_type}'] = price_data.loc[ts, 'price']
        
        # Execution data - gas costs
        if 'gas_costs' in self.data:
            gas_data = self.data['gas_costs']
            ts = gas_data.index.asof(timestamp)
            if not pd.isna(ts):
                data['execution_data']['gas_costs']['stake'] = gas_data.loc[ts, 'CREATE_LST_eth']
                data['execution_data']['gas_costs']['supply'] = gas_data.loc[ts, 'COLLATERAL_SUPPLIED_eth']
                data['execution_data']['gas_costs']['borrow'] = gas_data.loc[ts, 'BORROW_eth']
                data['execution_data']['gas_costs']['repay'] = gas_data.loc[ts, 'REPAY_eth']
                data['execution_data']['gas_costs']['withdraw'] = gas_data.loc[ts, 'WITHDRAW_eth']
        
        return data
    
    def _load_eth_spot_prices(self) -> None:
        """Load ETH spot prices from Binance."""
        file_path = Path(self.data_dir) / 'market_data/spot_prices/eth_usd/binance_ETHUSDT_1h_2020-01-01_2025-09-26.csv'
        
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, 'ETH spot prices')
        
        self.data['eth_spot_binance'] = df
        logger.info(f"Loaded ETH spot prices: {len(df)} records")
    
    def _load_lst_oracle_prices(self) -> None:
        """Load LST oracle prices."""
        if self.lst_type.lower() == 'weeth':
            file_path = Path(self.data_dir) / 'protocol_data/aave/oracle/weETH_ETH_oracle_2024-01-01_2025-09-18.csv'
        elif self.lst_type.lower() == 'wsteth':
            file_path = Path(self.data_dir) / 'protocol_data/aave/oracle/wstETH_ETH_oracle_2024-01-01_2025-09-18.csv'
        else:
            raise ValueError(f"Unknown LST type: {self.lst_type}")
        
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, f'{self.lst_type} oracle prices')
        
        self.data[f'{self.lst_type.lower()}_oracle'] = df
        logger.info(f"Loaded {self.lst_type} oracle prices: {len(df)} records")
    
    def _load_aave_rates(self) -> None:
        """Load AAVE rates for weETH and WETH."""
        # Load weETH rates
        weeth_file = Path(self.data_dir) / 'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_weETH_rates_2024-05-12_2025-09-18_hourly.csv'
        df_weeth = _validate_data_file(weeth_file)
        self._validate_timestamp_alignment(df_weeth, 'weETH rates')
        self.data['weeth_rates'] = df_weeth
        logger.info(f"Loaded weETH rates: {len(df_weeth)} records")
        
        # Load WETH rates
        weth_file = Path(self.data_dir) / 'protocol_data/aave/rates/aave_v3_aave-v3-ethereum_WETH_rates_2024-01-01_2025-09-18_hourly.csv'
        df_weth = _validate_data_file(weth_file)
        self._validate_timestamp_alignment(df_weth, 'WETH rates')
        self.data['weth_rates'] = df_weth
        logger.info(f"Loaded WETH rates: {len(df_weth)} records")
    
    def _load_staking_rewards(self) -> None:
        """Load staking rewards data."""
        # Try multiple possible filenames for staking yields
        possible_paths = [
            Path(self.data_dir) / 'protocol_data/staking/base_staking_yields_2024-01-01_2025-09-18_hourly.csv',
            Path(self.data_dir) / 'protocol_data/staking/base_yields/weeth_oracle_yields_2024-01-01_2025-09-18.csv',
            Path(self.data_dir) / 'protocol_data/staking/base_staking_yields_2024-01-01_2025-09-18.csv'
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            raise DataProviderError('DATA-001', file_path=str(possible_paths[0]))
        
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, 'staking yields')
        
        self.data['staking_yields'] = df
        logger.info(f"Loaded staking yields: {len(df)} records")
    
    def _load_seasonal_rewards(self) -> None:
        """Load seasonal rewards data (EIGEN/ETHFI)."""
        file_path = Path(self.data_dir) / 'protocol_data/staking/restaking_final/etherfi_seasonal_rewards_2024-01-01_2025-09-18.csv'
        
        df = _validate_data_file(file_path, timestamp_column="period_start")
        self._validate_timestamp_alignment(df, 'seasonal rewards')
        
        self.data['seasonal_rewards'] = df
        logger.info(f"Loaded seasonal rewards: {len(df)} records")
    
    def _load_protocol_token_prices(self) -> None:
        """Load protocol token prices (EIGEN/ETHFI) for KING unwrapping."""
        # Load EIGEN prices
        eigen_eth_file = Path(self.data_dir) / 'market_data/spot_prices/protocol_tokens/uniswapv3_EIGENWETH_1h_2024-10-05_2025-09-27.csv'
        eigen_usdt_file = Path(self.data_dir) / 'market_data/spot_prices/protocol_tokens/binance_EIGENUSDT_1h_2024-10-05_2025-09-30.csv'
        
        if eigen_eth_file.exists():
            df_eigen_eth = _validate_data_file(eigen_eth_file, strict_date_range=False)
            df_eigen_eth['price'] = df_eigen_eth['close']
            self.data['eigen_eth_price'] = df_eigen_eth
            logger.info(f"Loaded EIGEN/ETH prices: {len(df_eigen_eth)} records")
        
        if eigen_usdt_file.exists():
            df_eigen_usdt = _validate_data_file(eigen_usdt_file, strict_date_range=False)
            self.data['eigen_usdt_price'] = df_eigen_usdt
            logger.info(f"Loaded EIGEN/USDT prices: {len(df_eigen_usdt)} records")
        
        # Load ETHFI prices
        ethfi_eth_file = Path(self.data_dir) / 'market_data/spot_prices/protocol_tokens/uniswapv3_ETHFIWETH_1h_2024-04-01_2025-09-27.csv'
        ethfi_usdt_file = Path(self.data_dir) / 'market_data/spot_prices/protocol_tokens/binance_ETHFIUSDT_1h_2024-06-01_2025-09-30.csv'
        
        if ethfi_eth_file.exists():
            df_ethfi_eth = _validate_data_file(ethfi_eth_file, strict_date_range=False)
            df_ethfi_eth['price'] = df_ethfi_eth['close']
            self.data['ethfi_eth_price'] = df_ethfi_eth
            logger.info(f"Loaded ETHFI/ETH prices: {len(df_ethfi_eth)} records")
        
        if ethfi_usdt_file.exists():
            df_ethfi_usdt = _validate_data_file(ethfi_usdt_file, strict_date_range=False)
            self.data['ethfi_usdt_price'] = df_ethfi_usdt
            logger.info(f"Loaded ETHFI/USDT prices: {len(df_ethfi_usdt)} records")
    
    def _load_gas_costs(self) -> None:
        """Load gas costs data."""
        # Try enhanced version first, fall back to regular version
        enhanced_path = Path(self.data_dir) / 'blockchain_data/gas_prices/ethereum_gas_prices_enhanced_2024-01-01_2025-09-26.csv'
        regular_path = Path(self.data_dir) / 'blockchain_data/gas_prices/ethereum_gas_prices_2024-01-01_2025-09-26.csv'
        
        if enhanced_path.exists():
            file_path = enhanced_path
        else:
            file_path = regular_path
        
        df = _validate_data_file(file_path)
        self._validate_timestamp_alignment(df, 'gas costs')
        
        self.data['gas_costs'] = df
        logger.info(f"Loaded gas costs: {len(df)} records")
    
    def _load_execution_costs(self) -> None:
        """Load execution costs data."""
        file_path = Path(self.data_dir) / 'execution_costs/execution_cost_simulation_results.csv'
        
        if not file_path.exists():
            raise DataProviderError('DATA-001', file_path=str(file_path))
        
        df = pd.read_csv(file_path)
        if df.empty:
            raise DataProviderError('DATA-003', message="Execution costs file is empty", file_path=str(file_path))
        
        # Execution costs are lookup tables, not time series
        df._is_time_series = False
        self.data['execution_costs'] = df
        logger.info(f"Loaded execution costs: {len(df)} records")
    
    def _load_aave_risk_parameters(self) -> None:
        """Load AAVE v3 risk parameters."""
        file_path = Path(self.data_dir) / 'protocol_data/aave/risk_params/aave_v3_risk_parameters.json'
        
        if not file_path.exists():
            raise DataProviderError('DATA-001', file_path=str(file_path))
        
        with open(file_path, 'r') as f:
            raw_data = json.load(f)
        
        # Process and structure the risk parameters
        aave_risk_params = {
            'emode': {
                'liquidation_thresholds': raw_data['emode']['liquidation_thresholds'],
                'max_ltv_limits': raw_data['emode']['ltv_limits'],
                'liquidation_bonus': raw_data['emode']['liquidation_bonus'],
                'eligible_pairs': list(raw_data['emode']['ltv_limits'].keys())
            },
            'normal_mode': {
                'liquidation_thresholds': raw_data['standard']['liquidation_thresholds'],
                'max_ltv_limits': raw_data['standard']['ltv_limits'],
                'liquidation_bonus': raw_data['standard']['liquidation_bonus'],
                'eligible_pairs': list(raw_data['standard']['ltv_limits'].keys())
            },
            'reserve_factors': raw_data['reserve_factors'],
            'metadata': {
                'source': 'aave_v3_risk_parameters.json',
                'created': pd.Timestamp.now().isoformat(),
                'description': 'AAVE v3 risk parameters for liquidation simulation',
                'version': 'v3'
            }
        }
        
        self.data['aave_risk_params'] = aave_risk_params
        logger.info("Loaded AAVE risk parameters")
    
    def _validate_loaded_data(self) -> None:
        """Validate all required data is loaded."""
        required_data = [
            'eth_spot_binance',
            f'{self.lst_type.lower()}_oracle',
            'weeth_rates',
            'weth_rates',
            'staking_yields',
            'gas_costs',
            'execution_costs',
            'aave_risk_params'
        ]
        
        # Add seasonal rewards if needed
        if self.rewards_mode != 'base_only':
            required_data.append('seasonal_rewards')
        
        missing_data = [key for key in required_data if key not in self.data]
        
        if missing_data:
            raise DataProviderError(
                'DATA-004',
                message=f"Missing required data for ETH leveraged: {missing_data}",
                missing_data=missing_data,
                mode=self.mode
            )
        
        logger.info("✅ All ETH leveraged data requirements satisfied")
