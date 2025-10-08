# Test Infrastructure Documentation

## Overview

This document describes the comprehensive test infrastructure that has been created to support reliable and centralized testing across the Basis Strategy project. The infrastructure addresses the need for consistent test environments, mock data, and configuration management.

## Components

### 1. Test Environment Variables (`backend/env.test`)

A comprehensive test environment file that provides all necessary environment variables for testing:

- **Core Configuration**: API, cache, database, and monitoring settings
- **Environment-Specific Settings**: Production, development, and staging configurations with test values
- **CEX Integration**: Test API keys and secrets for all supported exchanges (Binance, Bybit, OKX)
- **Blockchain Integration**: Test RPC URLs, private keys, and wallet addresses
- **Risk Management**: Test risk parameters and limits
- **Data Providers**: Test API keys for external data sources

**Key Features:**
- All values are clearly marked as test values (prefixed with `test_`)
- No real API keys or sensitive data
- Comprehensive coverage of all environment variables needed by the application

### 2. Test Configuration Files

#### Main Test Config (`configs/test.json`)
- Complete test configuration with all necessary settings
- Optimized for testing (debug enabled, test database, etc.)
- Includes all major configuration sections

#### Test Mode Configurations (`configs/modes/test_*.yaml`)
- `test_pure_lending.yaml`: Simplified pure lending strategy
- `test_btc_basis.yaml`: Simplified BTC basis trading strategy
- Additional test modes can be easily added

### 3. Centralized Mock Infrastructure

#### Mock Config Loader (`tests/tools/mocks/test_config_loader.py`)

**Features:**
- Predefined test configurations for all strategy modes
- Support for custom configuration overrides
- Easy addition of new test modes
- Centralized configuration management

**Usage:**
```python
from tests.tools.mocks.test_config_loader import get_mock_config_loader

mock_loader = get_mock_config_loader()
config = mock_loader.get_complete_config('test_pure_lending')
```

#### Mock Data Provider (`tests/tools/mocks/test_data_provider.py`)

**Features:**
- Realistic test data for all market conditions
- Configurable prices, APYs, and market data
- Support for historical data simulation
- Easy customization of test scenarios

**Usage:**
```python
from tests.tools.mocks.test_data_provider import get_mock_data_provider

mock_provider = get_mock_data_provider()
eth_price = await mock_provider.get_spot_price('ETH')
```

### 4. Enhanced conftest.py

**New Fixtures:**
- `mock_config_loader`: Access to centralized mock config loader
- `mock_data_provider`: Access to centralized mock data provider
- `config_loader_patch`: Patch for config loader in tests
- `data_provider_patch`: Patch for data provider in tests
- `test_config`: Complete test configuration object

**Environment Setup:**
- Automatic loading of test environment variables from `env.test`
- Fallback to hardcoded values if file not found
- Proper cleanup after tests

## Usage Examples

### Basic Test with Centralized Infrastructure

```python
import pytest
from unittest.mock import patch

class TestMyService:
    @pytest.mark.asyncio
    async def test_my_service(self, service, mock_config_loader):
        # Mock the config loader
        with patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader', 
                   return_value=mock_config_loader):
            # Your test logic here
            result = await service.run_operation()
            assert result is not None
```

### Testing Multiple Modes

```python
@pytest.mark.asyncio
async def test_all_modes(self, service, mock_config_loader):
    test_modes = mock_config_loader.get_available_modes()
    
    for mode in test_modes:
        with patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader', 
                   return_value=mock_config_loader):
            result = await service.run_with_mode(mode)
            assert result is not None
```

### Custom Configuration Testing

```python
@pytest.mark.asyncio
async def test_custom_config(self, service, mock_config_loader):
    # Add custom test configuration
    custom_config = {
        'mode': 'custom_test',
        'target_apy': 0.10,
        'max_drawdown': 0.05
    }
    mock_config_loader.add_custom_config('custom_test', custom_config)
    
    try:
        # Test with custom config
        with patch('backend.src.basis_strategy_v1.infrastructure.config.config_loader.get_config_loader', 
                   return_value=mock_config_loader):
            result = await service.run_with_mode('custom_test')
            assert result is not None
    finally:
        # Clean up
        mock_config_loader.clear_custom_configs()
```

## Benefits

### 1. **Reliability**
- No dependency on external APIs or real data
- Consistent test environment across all tests
- Predictable test outcomes

### 2. **Maintainability**
- Centralized configuration management
- Easy to add new test modes or scenarios
- Single source of truth for test data

### 3. **Performance**
- Fast test execution (no network calls)
- Parallel test execution support
- Minimal setup overhead

### 4. **Coverage**
- Comprehensive test coverage for all strategy modes
- Easy testing of edge cases and error conditions
- Support for complex integration scenarios

### 5. **Developer Experience**
- Simple, intuitive API
- Clear documentation and examples
- Easy debugging and troubleshooting

## Best Practices

### 1. **Use Centralized Mocks**
Always use the centralized mock infrastructure instead of creating ad-hoc mocks:

```python
# Good
@pytest.mark.asyncio
async def test_with_centralized_mocks(self, mock_config_loader):
    with patch('path.to.config_loader', return_value=mock_config_loader):
        # Test logic

# Avoid
@pytest.mark.asyncio
async def test_with_ad_hoc_mocks(self):
    mock_loader = Mock()
    mock_loader.get_config.return_value = {...}
    # Test logic
```

### 2. **Clean Up Custom Configurations**
Always clean up custom configurations after tests:

```python
@pytest.mark.asyncio
async def test_with_custom_config(self, mock_config_loader):
    mock_config_loader.add_custom_config('test_mode', {...})
    try:
        # Test logic
        pass
    finally:
        mock_config_loader.clear_custom_configs()
```

### 3. **Use Appropriate Wait Times**
For async operations, use appropriate wait times:

```python
# Wait for async operations to complete
import asyncio
await asyncio.sleep(0.1)
```

### 4. **Test Environment Variables**
Verify that test environment variables are properly loaded:

```python
def test_environment_setup(self):
    import os
    assert os.getenv('BASIS_ENVIRONMENT') == 'test'
    assert os.getenv('BASIS_PRODUCTION__ALCHEMY__PRIVATE_KEY').startswith('test_')
```

## File Structure

```
tests/
├── conftest.py                          # Enhanced with new fixtures
├── tools/
│   └── mocks/
│       ├── test_config_loader.py        # Centralized mock config loader
│       └── test_data_provider.py        # Centralized mock data provider
├── unit/
│   └── services/
│       └── test_backtest_service_new.py # Example usage
└── README_TEST_INFRASTRUCTURE.md        # This documentation

backend/
└── env.test                             # Test environment variables

configs/
├── test.json                            # Main test configuration
└── modes/
    ├── test_pure_lending.yaml           # Test mode configurations
    └── test_btc_basis.yaml
```

## Migration Guide

### From Old Test Infrastructure

1. **Replace Environment Variable Setup:**
   ```python
   # Old
   os.environ['BASIS_PRODUCTION__ALCHEMY__PRIVATE_KEY'] = 'test_key'
   
   # New - Automatic via conftest.py
   # No manual setup needed
   ```

2. **Replace Ad-hoc Mocks:**
   ```python
   # Old
   mock_loader = Mock()
   mock_loader.get_config.return_value = {...}
   
   # New
   from tests.tools.mocks.test_config_loader import get_mock_config_loader
   mock_loader = get_mock_config_loader()
   ```

3. **Use New Fixtures:**
   ```python
   # Old
   def test_my_service(self):
       # Manual setup
   
   # New
   def test_my_service(self, mock_config_loader, mock_data_provider):
       # Automatic setup via fixtures
   ```

## Future Enhancements

1. **Additional Test Modes**: Add more test mode configurations as needed
2. **Performance Testing**: Add performance benchmarks and thresholds
3. **Integration Testing**: Extend infrastructure for end-to-end testing
4. **Data Validation**: Add comprehensive data validation testing
5. **Error Simulation**: Add more sophisticated error condition testing

## Conclusion

The new test infrastructure provides a robust, maintainable, and efficient foundation for testing the Basis Strategy project. It eliminates common testing pain points while providing comprehensive coverage and excellent developer experience.

For questions or issues with the test infrastructure, please refer to the test files in `tests/unit/services/test_backtest_service_new.py` for examples of proper usage.
