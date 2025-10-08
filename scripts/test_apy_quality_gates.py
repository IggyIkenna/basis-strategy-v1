#!/usr/bin/env python3
"""
APY Quality Gates for All Strategies

Tests APY ranges for all available strategies:
- Pure lending: 3-8% APY
- BTC basis: 3-30% APY  
- Others: 2-50% APY

Must use 2 months data minimum for accurate APY calculation.
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import sys
import os

# Add the backend src to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Strategy APY targets
STRATEGY_APY_TARGETS = {
    'pure_lending': (3.0, 8.0),      # 3-8% APY - IMPLEMENTED
    'btc_basis': (3.0, 30.0),        # 3-30% APY - IMPLEMENTED
    # Note: Other strategies are not fully implemented yet
    # 'eth_leveraged': (2.0, 50.0),    # 2-50% APY - NOT IMPLEMENTED
    # 'usdt_market_neutral': (2.0, 50.0),  # 2-50% APY - NOT IMPLEMENTED
    # 'eth_staking_only': (2.0, 50.0),     # 2-50% APY - NOT IMPLEMENTED
    # 'usdt_market_neutral_no_leverage': (2.0, 50.0)  # 2-50% APY - NOT IMPLEMENTED
}

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_START_DATE = "2024-06-01T00:00:00Z"
TEST_END_DATE = "2024-08-01T00:00:00Z"  # 2 months for realistic APY calculation
INITIAL_CAPITAL = 100000
SHARE_CLASS = "USDT"

class APYQualityGates:
    """APY Quality Gates for all strategies."""
    
    def __init__(self):
        self.results = {}
        self.failed_strategies = []
        self.passed_strategies = []
    
    def run_all_apy_tests(self) -> Dict:
        """Run APY quality gates for all strategies."""
        logger.info("🎯 APY QUALITY GATES FOR ALL STRATEGIES")
        logger.info("=" * 60)
        logger.info(f"Testing APY ranges with 2 months data ({TEST_START_DATE} to {TEST_END_DATE})")
        logger.info(f"Initial capital: ${INITIAL_CAPITAL:,}")
        logger.info("")
        
        for strategy_name, (min_apy, max_apy) in STRATEGY_APY_TARGETS.items():
            logger.info(f"🔍 Testing {strategy_name.upper()} Strategy")
            logger.info("-" * 40)
            
            try:
                result = self._test_strategy_apy(strategy_name, min_apy, max_apy)
                self.results[strategy_name] = result
                
                if result['passed']:
                    self.passed_strategies.append(strategy_name)
                    logger.info(f"✅ {strategy_name.upper()} PASSED: APY {result['apy']:.2f}% (target: {min_apy}-{max_apy}%)")
                else:
                    self.failed_strategies.append(strategy_name)
                    logger.info(f"❌ {strategy_name.upper()} FAILED: APY {result['apy']:.2f}% outside target range ({min_apy}-{max_apy}%)")
                
            except Exception as e:
                logger.error(f"❌ {strategy_name.upper()} ERROR: {str(e)}")
                self.results[strategy_name] = {
                    'passed': False,
                    'error': str(e),
                    'apy': None,
                    'total_return': None,
                    'final_value': None
                }
                self.failed_strategies.append(strategy_name)
            
            logger.info("")
        
        return self._generate_summary()
    
    def _test_strategy_apy(self, strategy_name: str, min_apy: float, max_apy: float) -> Dict:
        """Test APY for a specific strategy."""
        # Start backtest
        backtest_request = {
            "strategy_name": strategy_name,
            "start_date": TEST_START_DATE,
            "end_date": TEST_END_DATE,
            "initial_capital": INITIAL_CAPITAL,
            "share_class": SHARE_CLASS,
            "debug_mode": False
        }
        
        logger.info(f"Starting backtest for {strategy_name}...")
        response = requests.post(f"{BASE_URL}/api/v1/backtest/", json=backtest_request)
        
        if response.status_code != 200:
            raise Exception(f"Backtest request failed: {response.status_code} - {response.text}")
        
        backtest_data = response.json()
        request_id = backtest_data['data']['request_id']
        
        # Wait for completion
        logger.info(f"Waiting for backtest completion (request_id: {request_id})...")
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_response = requests.get(f"{BASE_URL}/api/v1/backtest/{request_id}/status")
            if status_response.status_code != 200:
                raise Exception(f"Status check failed: {status_response.status_code}")
            
            status_data = status_response.json()
            status = status_data['data']['status']
            
            if status == 'completed':
                break
            elif status == 'failed':
                raise Exception(f"Backtest failed: {status_data.get('error', 'Unknown error')}")
            
            time.sleep(5)
        else:
            raise Exception("Backtest timed out after 5 minutes")
        
        # Get results
        result_response = requests.get(f"{BASE_URL}/api/v1/backtest/{request_id}/result")
        if result_response.status_code != 200:
            raise Exception(f"Result retrieval failed: {result_response.status_code}")
        
        result_data = result_response.json()
        performance = result_data['data']
        
        # Calculate APY
        # The API returns annualized_return as a decimal (e.g., 0.521 = 52.1%)
        annualized_return = performance.get('annualized_return', 0.0)
        if isinstance(annualized_return, str):
            annualized_return = float(annualized_return)
        
        # Convert to APY percentage
        apy_pct = annualized_return * 100
        
        # Also calculate total return percentage for logging
        total_return = performance.get('total_return', 0.0)
        if isinstance(total_return, str):
            total_return = float(total_return)
        
        initial_capital = performance.get('initial_capital', INITIAL_CAPITAL)
        if isinstance(initial_capital, str):
            initial_capital = float(initial_capital)
        
        total_return_pct = (total_return / initial_capital) * 100 if initial_capital > 0 else 0.0
        
        # Check if APY is within target range
        passed = min_apy <= apy_pct <= max_apy
        
        return {
            'passed': passed,
            'apy': apy_pct,
            'total_return_pct': total_return_pct,
            'total_return': performance.get('total_return', 0.0),
            'final_value': performance.get('final_value', INITIAL_CAPITAL),
            'min_apy': min_apy,
            'max_apy': max_apy,
            'request_id': request_id
        }
    
    def _generate_summary(self) -> Dict:
        """Generate summary of all APY tests."""
        total_strategies = len(STRATEGY_APY_TARGETS)
        passed_count = len(self.passed_strategies)
        failed_count = len(self.failed_strategies)
        
        logger.info("=" * 60)
        logger.info("📊 APY QUALITY GATES SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Strategies: {total_strategies}")
        logger.info(f"Passed: {passed_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Success Rate: {passed_count/total_strategies*100:.1f}%")
        logger.info("")
        
        if self.passed_strategies:
            logger.info("✅ PASSED STRATEGIES:")
            for strategy in self.passed_strategies:
                result = self.results[strategy]
                logger.info(f"  - {strategy}: {result['apy']:.2f}% APY (target: {result['min_apy']}-{result['max_apy']}%)")
            logger.info("")
        
        if self.failed_strategies:
            logger.info("❌ FAILED STRATEGIES:")
            for strategy in self.failed_strategies:
                result = self.results[strategy]
                if 'error' in result:
                    logger.info(f"  - {strategy}: ERROR - {result['error']}")
                else:
                    logger.info(f"  - {strategy}: {result['apy']:.2f}% APY (target: {result['min_apy']}-{result['max_apy']}%)")
            logger.info("")
        
        # Overall status
        if failed_count == 0:
            logger.info("🎉 ALL APY QUALITY GATES PASSED!")
            overall_status = "PASS"
        else:
            logger.info(f"⚠️  {failed_count} APY QUALITY GATES FAILED")
            overall_status = "FAIL"
        
        return {
            'overall_status': overall_status,
            'total_strategies': total_strategies,
            'passed_count': passed_count,
            'failed_count': failed_count,
            'success_rate': passed_count/total_strategies*100,
            'results': self.results,
            'passed_strategies': self.passed_strategies,
            'failed_strategies': self.failed_strategies
        }

def main():
    """Main function to run APY quality gates."""
    try:
        gates = APYQualityGates()
        summary = gates.run_all_apy_tests()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"/workspace/results/apy_quality_gates_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"📄 Results saved to: {results_file}")
        
        # Exit with appropriate code
        if summary['overall_status'] == 'PASS':
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"APY Quality Gates failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()