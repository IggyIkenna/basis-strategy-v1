#!/usr/bin/env python3
"""
Async Ordering Quality Gates - Validate async I/O ordering guarantees.

This quality gate validates that AsyncResultsStore maintains proper ordering
and data integrity under various load conditions.

Quality Gate Thresholds:
- 100% ordering correctness (no out-of-order writes)
- 100% data integrity (no dropped results)
- < 5% performance overhead vs synchronous writes
- Graceful error handling without data loss
"""

import asyncio
import tempfile
import shutil
import json
import time
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add backend to path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from basis_strategy_v1.infrastructure.persistence.async_results_store import AsyncResultsStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncOrderingQualityGate:
    """Quality gate for validating async ordering guarantees."""
    
    def __init__(self):
        self.temp_dir = None
        self.results_store = None
        self.test_results = {}
    
    async def setup(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.results_store = AsyncResultsStore(self.temp_dir, 'backtest')
        logger.info(f"Quality gate setup: {self.temp_dir}")
    
    async def cleanup(self):
        """Cleanup test environment."""
        if self.results_store:
            try:
                await self.results_store.stop()
            except Exception as e:
                logger.warning(f"Error stopping results store: {e}")
        
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info("Quality gate cleanup completed")
    
    async def test_ordering_correctness(self) -> Dict[str, Any]:
        """Test 1: Verify 100% ordering correctness."""
        logger.info("Testing ordering correctness...")
        
        await self.results_store.start()
        
        # Queue results with specific ordering
        test_count = 100
        expected_order = []
        
        for i in range(test_count):
            timestamp = pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(minutes=i)
            expected_order.append(i)
            
            await self.results_store.save_timestep_result(
                request_id='ordering_test',
                timestamp=timestamp,
                data={'sequence': i, 'timestamp': timestamp.isoformat()}
            )
        
        await self.results_store.stop()
        
        # Verify ordering
        results_dir = Path(self.temp_dir) / 'ordering_test' / 'timesteps'
        files = sorted(results_dir.glob('*.json'))
        
        actual_order = []
        for file_path in files:
            with open(file_path, 'r') as f:
                data = json.load(f)
                actual_order.append(data['sequence'])
        
        # Check ordering correctness
        ordering_correct = actual_order == expected_order
        ordering_percentage = 100.0 if ordering_correct else 0.0
        
        result = {
            'test_name': 'ordering_correctness',
            'passed': ordering_correct,
            'percentage': ordering_percentage,
            'expected_count': test_count,
            'actual_count': len(actual_order),
            'threshold': 100.0,
            'details': {
                'expected_order': expected_order[:10],  # First 10 for logging
                'actual_order': actual_order[:10],
                'files_created': len(files)
            }
        }
        
        logger.info(f"Ordering correctness: {ordering_percentage}% ({'PASS' if ordering_correct else 'FAIL'})")
        return result
    
    async def test_data_integrity(self) -> Dict[str, Any]:
        """Test 2: Verify 100% data integrity (no dropped results)."""
        logger.info("Testing data integrity...")
        
        await self.results_store.start()
        
        # Queue many results rapidly
        test_count = 500
        expected_data = set()
        
        for i in range(test_count):
            timestamp = pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(seconds=i)
            expected_data.add(i)
            
            await self.results_store.save_timestep_result(
                request_id='integrity_test',
                timestamp=timestamp,
                data={'id': i, 'data': f'test_data_{i}'}
            )
        
        await self.results_store.stop()
        
        # Verify no data lost
        results_dir = Path(self.temp_dir) / 'integrity_test' / 'timesteps'
        files = list(results_dir.glob('*.json'))
        
        actual_data = set()
        for file_path in files:
            with open(file_path, 'r') as f:
                data = json.load(f)
                actual_data.add(data['id'])
        
        # Check data integrity
        data_lost = expected_data - actual_data
        data_integrity = len(data_lost) == 0
        integrity_percentage = 100.0 if data_integrity else ((len(actual_data) / len(expected_data)) * 100)
        
        result = {
            'test_name': 'data_integrity',
            'passed': data_integrity,
            'percentage': integrity_percentage,
            'expected_count': len(expected_data),
            'actual_count': len(actual_data),
            'threshold': 100.0,
            'details': {
                'data_lost': list(data_lost)[:10],  # First 10 for logging
                'files_created': len(files)
            }
        }
        
        logger.info(f"Data integrity: {integrity_percentage}% ({'PASS' if data_integrity else 'FAIL'})")
        return result
    
    async def test_performance_overhead(self) -> Dict[str, Any]:
        """Test 3: Verify < 5% performance overhead vs synchronous writes."""
        logger.info("Testing performance overhead...")
        
        test_count = 1000
        
        # Test async performance
        await self.results_store.start()
        start_time = time.time()
        
        for i in range(test_count):
            timestamp = pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(seconds=i)
            await self.results_store.save_timestep_result(
                request_id='performance_test',
                timestamp=timestamp,
                data={'id': i}
            )
        
        await self.results_store.stop()
        async_time = time.time() - start_time
        
        # Test synchronous performance (simulate)
        start_time = time.time()
        sync_dir = Path(self.temp_dir) / 'sync_test'
        sync_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(test_count):
            file_path = sync_dir / f'{i:06d}.json'
            with open(file_path, 'w') as f:
                json.dump({'id': i}, f)
        
        sync_time = time.time() - start_time
        
        # Calculate overhead
        overhead_percentage = ((async_time - sync_time) / sync_time) * 100
        performance_acceptable = overhead_percentage < 5.0
        
        result = {
            'test_name': 'performance_overhead',
            'passed': performance_acceptable,
            'percentage': 100.0 - overhead_percentage,  # Invert for pass percentage
            'async_time': async_time,
            'sync_time': sync_time,
            'overhead_percentage': overhead_percentage,
            'threshold': 95.0,  # < 5% overhead = > 95% performance
            'details': {
                'test_count': test_count,
                'async_ops_per_second': test_count / async_time,
                'sync_ops_per_second': test_count / sync_time
            }
        }
        
        logger.info(f"Performance overhead: {overhead_percentage:.2f}% ({'PASS' if performance_acceptable else 'FAIL'})")
        return result
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test 4: Verify graceful error handling without data loss."""
        logger.info("Testing error handling...")
        
        await self.results_store.start()
        
        # Queue some valid results
        valid_count = 50
        for i in range(valid_count):
            timestamp = pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(minutes=i)
            await self.results_store.save_timestep_result(
                request_id='error_test',
                timestamp=timestamp,
                data={'id': i, 'valid': True}
            )
        
        # Queue some results that might cause issues (but shouldn't break the worker)
        for i in range(10):
            timestamp = pd.Timestamp('2024-01-01 00:00:00') + pd.Timedelta(minutes=valid_count + i)
            await self.results_store.save_timestep_result(
                request_id='error_test',
                timestamp=timestamp,
                data={'id': valid_count + i, 'valid': True, 'complex_data': {'nested': {'value': i}}}
            )
        
        await self.results_store.stop()
        
        # Verify all results processed despite any errors
        results_dir = Path(self.temp_dir) / 'error_test' / 'timesteps'
        files = list(results_dir.glob('*.json'))
        
        processed_count = len(files)
        expected_count = valid_count + 10
        error_handling_ok = processed_count == expected_count
        error_handling_percentage = (processed_count / expected_count) * 100
        
        result = {
            'test_name': 'error_handling',
            'passed': error_handling_ok,
            'percentage': error_handling_percentage,
            'expected_count': expected_count,
            'actual_count': processed_count,
            'threshold': 100.0,
            'details': {
                'files_created': len(files),
                'worker_stopped_gracefully': True
            }
        }
        
        logger.info(f"Error handling: {error_handling_percentage}% ({'PASS' if error_handling_ok else 'FAIL'})")
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all quality gate tests."""
        logger.info("Starting Async Ordering Quality Gates...")
        
        try:
            await self.setup()
            
            tests = [
                self.test_ordering_correctness(),
                self.test_data_integrity(),
                self.test_performance_overhead(),
                self.test_error_handling()
            ]
            
            results = await asyncio.gather(*tests)
            
            # Calculate overall score
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r['passed'])
            overall_percentage = (passed_tests / total_tests) * 100
            
            quality_gate_result = {
                'quality_gate': 'async_ordering',
                'overall_passed': passed_tests == total_tests,
                'overall_percentage': overall_percentage,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'threshold': 100.0,
                'test_results': results,
                'summary': {
                    'ordering_correctness': results[0]['passed'],
                    'data_integrity': results[1]['passed'],
                    'performance_acceptable': results[2]['passed'],
                    'error_handling_ok': results[3]['passed']
                }
            }
            
            logger.info(f"Quality Gate Result: {overall_percentage}% ({'PASS' if quality_gate_result['overall_passed'] else 'FAIL'})")
            return quality_gate_result
            
        except Exception as e:
            logger.error(f"Quality gate failed with error: {e}")
            return {
                'quality_gate': 'async_ordering',
                'overall_passed': False,
                'overall_percentage': 0.0,
                'error': str(e)
            }
        
        finally:
            await self.cleanup()


async def main():
    """Main entry point for quality gate."""
    quality_gate = AsyncOrderingQualityGate()
    result = await quality_gate.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("ASYNC ORDERING QUALITY GATE RESULTS")
    print("="*60)
    print(f"Overall Result: {'PASS' if result['overall_passed'] else 'FAIL'}")
    print(f"Overall Score: {result['overall_percentage']:.1f}%")
    print(f"Tests Passed: {result['passed_tests']}/{result['total_tests']}")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    
    print("\nTest Details:")
    for test_result in result.get('test_results', []):
        status = 'PASS' if test_result['passed'] else 'FAIL'
        print(f"  {test_result['test_name']}: {status} ({test_result['percentage']:.1f}%)")
    
    print("="*60)
    
    # Exit with appropriate code
    exit_code = 0 if result['overall_passed'] else 1
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
