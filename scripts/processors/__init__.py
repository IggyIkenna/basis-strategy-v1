"""
Data processing scripts for manually-sourced and downloaded data.

This module contains processors for:
- EtherFi restaking rewards (manual CSV processing + real distributions)
- Lido stETH staking yields (manual CSV processing)
- Ethena benchmark data (manual CSV processing)
- LST peg discount/premium analysis
- AAVE oracle price extraction
- Data validation and cleaning
- Format standardization
"""

from .process_ethena_benchmark import EthenaBenchmarkProcessor
from .process_peg_discount_data import PegDiscountProcessor
from .process_aave_oracle_prices import AAVEOraclePriceProcessor
from .process_etherfi_seasonal_rewards import EtherFiSeasonalRewardsProcessor
from .process_oracle_base_yields import OracleBaseYieldsProcessor
from .process_simulation_results import SimulationResultProcessor

__all__ = [
    "EthenaBenchmarkProcessor",
    "PegDiscountProcessor",
    "AAVEOraclePriceProcessor",
    "EtherFiSeasonalRewardsProcessor",
    "OracleBaseYieldsProcessor",
    "SimulationResultProcessor"
]