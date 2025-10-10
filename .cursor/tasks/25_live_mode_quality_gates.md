# LIVE TRADING QUALITY GATES

## OVERVIEW
Live trading quality gates ensure all required clients and external APIs are properly configured and available for the selected strategy mode.

## CLIENT REQUIREMENT VALIDATION

### 1. Mode-Based Client Requirements
- **Strategy mode determines required clients**: Each strategy mode requires specific clients
- **Configuration-driven**: Client requirements determined by config YAML files
- **Environment-specific**: Testnet vs production client configurations
- **Venue-specific**: Different venues require different clients

### 2. Client Availability Validation
- **API connectivity**: All required APIs must be accessible
- **Authentication**: All required authentication must be valid
- **Rate limits**: Rate limits must be within acceptable ranges
- **Client initialization**: All clients must initialize successfully

## CONFIGURATION-BASED CLIENT REQUIREMENTS

### YAML Configuration Structure
```yaml
# configs/modes/pure_lending.yaml
name: "pure_lending"
required_clients:
  onchain:
    - name: "ethereum"
      type: "web3"
      required: true
    - name: "aave_v3"
      type: "contract"
      required: true
  cex:
    - name: "binance"
      type: "spot"
      required: false
    - name: "bybit"
      type: "spot"
      required: false

# configs/modes/btc_basis.yaml
name: "btc_basis"
required_clients:
  cex:
    - name: "binance"
      type: "spot"
      required: true
    - name: "binance"
      type: "futures"
      required: true
    - name: "bybit"
      type: "spot"
      required: true
    - name: "bybit"
      type: "futures"
      required: true
    - name: "okx"
      type: "spot"
      required: true
    - name: "okx"
      type: "futures"
      required: true
```

### Environment-Specific Configuration
```yaml
# configs/environments/testnet.yaml
name: "testnet"
clients:
  binance:
    base_url: "https://testnet.binance.vision"
    api_key: "${BINANCE_TESTNET_API_KEY}"
    secret_key: "${BINANCE_TESTNET_SECRET_KEY}"
  bybit:
    base_url: "https://api-testnet.bybit.com"
    api_key: "${BYBIT_TESTNET_API_KEY}"
    secret_key: "${BYBIT_TESTNET_SECRET_KEY}"

# configs/environments/production.yaml
name: "production"
clients:
  binance:
    base_url: "https://api.binance.com"
    api_key: "${BINANCE_API_KEY}"
    secret_key: "${BINANCE_SECRET_KEY}"
  bybit:
    base_url: "https://api.bybit.com"
    api_key: "${BYBIT_API_KEY}"
    secret_key: "${BYBIT_SECRET_KEY}"
```

## CLIENT VALIDATION REQUIREMENTS

### 1. API Connectivity
- **Endpoint accessibility**: All required API endpoints must be accessible
- **Response time**: API response times must be within acceptable limits
- **Error rates**: API error rates must be within acceptable limits
- **Network connectivity**: Network connectivity to all required services

### 2. Authentication Validation
- **API keys**: All required API keys must be valid and active
- **Secret keys**: All required secret keys must be valid
- **Permissions**: API keys must have required permissions
- **Rate limits**: API keys must have sufficient rate limits

### 3. Client Initialization
- **Client creation**: All required clients must initialize successfully
- **Configuration loading**: Client configurations must load properly
- **Connection establishment**: Connections to external services must establish
- **Error handling**: Client initialization errors must be handled properly

## QUALITY GATE IMPLEMENTATION

### Validation Script
```python
def validate_live_trading_clients(strategy_mode: str, environment: str):
    """Validate all required clients for live trading mode."""
    
    # 1. Load client requirements from config
    client_requirements = load_client_requirements(strategy_mode)
    
    # 2. Load environment configuration
    env_config = load_environment_config(environment)
    
    # 3. Validate each required client
    for client_req in client_requirements:
        client_name = client_req['name']
        client_type = client_req['type']
        required = client_req['required']
        
        if required:
            # Validate client availability
            assert validate_client_availability(client_name, client_type), \
                f"Required client {client_name} ({client_type}) not available"
            
            # Validate client configuration
            assert validate_client_config(client_name, env_config), \
                f"Client {client_name} configuration invalid"
            
            # Validate client connectivity
            assert validate_client_connectivity(client_name, client_type), \
                f"Client {client_name} connectivity failed"
    
    return True

def validate_client_availability(client_name: str, client_type: str) -> bool:
    """Validate that a client is available and can be initialized."""
    try:
        client = create_client(client_name, client_type)
        return client is not None
    except Exception as e:
        logger.error(f"Client {client_name} ({client_type}) not available: {e}")
        return False

def validate_client_config(client_name: str, env_config: dict) -> bool:
    """Validate client configuration."""
    client_config = env_config.get('clients', {}).get(client_name)
    if not client_config:
        logger.error(f"Client {client_name} configuration not found")
        return False
    
    # Check required configuration fields
    required_fields = ['api_key', 'secret_key']
    for field in required_fields:
        if field not in client_config:
            logger.error(f"Client {client_name} missing required field: {field}")
            return False
    
    return True

def validate_client_connectivity(client_name: str, client_type: str) -> bool:
    """Validate client connectivity to external services."""
    try:
        client = create_client(client_name, client_type)
        # Test connectivity with a simple API call
        response = client.test_connectivity()
        return response.get('status') == 'success'
    except Exception as e:
        logger.error(f"Client {client_name} connectivity test failed: {e}")
        return False
```

## CLIENT TYPES AND VALIDATION

### CEX Clients
- **Binance**: Spot and futures trading
- **Bybit**: Spot and futures trading
- **OKX**: Spot and futures trading
- **Validation**: API connectivity, authentication, rate limits

### On-Chain Clients
- **Ethereum**: Web3 client for Ethereum mainnet
- **Aave V3**: Smart contract client for Aave protocol
- **Lido**: Smart contract client for Lido protocol
- **EtherFi**: Smart contract client for EtherFi protocol
- **Validation**: RPC connectivity, contract availability, gas estimation

### Data Clients
- **Market data**: Real-time market data feeds
- **Protocol data**: Real-time protocol data feeds
- **Validation**: Data feed connectivity, data quality, latency

## ENVIRONMENT-SPECIFIC VALIDATION

### Testnet Environment
- **Testnet APIs**: All clients must connect to testnet endpoints
- **Testnet contracts**: All smart contracts must be testnet versions
- **Testnet data**: All data feeds must be testnet data
- **Validation**: Testnet-specific configuration and connectivity

### Production Environment
- **Production APIs**: All clients must connect to production endpoints
- **Production contracts**: All smart contracts must be production versions
- **Production data**: All data feeds must be production data
- **Validation**: Production-specific configuration and connectivity

## ERROR HANDLING AND RECOVERY

### Client Initialization Errors
- **Missing configuration**: Handle missing client configuration
- **Invalid credentials**: Handle invalid API keys or secrets
- **Network errors**: Handle network connectivity issues
- **Rate limit errors**: Handle rate limit exceeded errors

### Client Runtime Errors
- **API errors**: Handle API-specific errors
- **Network timeouts**: Handle network timeout errors
- **Authentication errors**: Handle authentication failures
- **Rate limit errors**: Handle rate limit exceeded errors

## QUALITY GATE INTEGRATION

### Scripts to Update
- **test_pure_lending_quality_gates.py**: Add live trading client validation
- **test_btc_basis_quality_gates.py**: Add live trading client validation
- **test_eth_leveraged_quality_gates.py**: Add live trading client validation
- **run_quality_gates.py**: Add live trading client validation

### Validation Points
- **Before strategy execution**: Validate all required clients
- **Environment setup**: Validate environment-specific configuration
- **Client initialization**: Validate client initialization
- **Connectivity testing**: Test connectivity to all required services

## VALIDATION CHECKLIST

### Configuration Validation
- [ ] Client requirements loaded from config YAML files
- [ ] Environment configuration loaded properly
- [ ] All required clients identified for strategy mode
- [ ] Client configurations valid and complete

### Client Availability
- [ ] All required clients can be initialized
- [ ] Client configurations are valid
- [ ] API keys and secrets are valid
- [ ] Client permissions are sufficient

### Connectivity Validation
- [ ] All required APIs are accessible
- [ ] Network connectivity is stable
- [ ] Response times are acceptable
- [ ] Error rates are within limits

### Environment-Specific
- [ ] Testnet clients connect to testnet endpoints
- [ ] Production clients connect to production endpoints
- [ ] Environment-specific configuration is correct
- [ ] Data feeds match environment requirements

## SUCCESS CRITERIA
- [ ] All required clients for strategy mode are available
- [ ] All clients initialize successfully
- [ ] All clients can connect to external services
- [ ] Client configurations are valid and complete
- [ ] Environment-specific requirements are met
- [ ] Quality gate scripts updated with live trading validation

## IMPLEMENTATION REQUIREMENTS

### Configuration Files
- **Mode configs**: Add client requirements to mode YAML files
- **Environment configs**: Add client configurations to environment YAML files
- **Validation configs**: Add validation rules to configuration files

### Quality Gate Scripts
- **Client validation**: Add client validation to quality gate scripts
- **Environment validation**: Add environment-specific validation
- **Connectivity testing**: Add connectivity testing to quality gates

### Error Handling
- **Client errors**: Handle client initialization and runtime errors
- **Configuration errors**: Handle configuration validation errors
- **Connectivity errors**: Handle connectivity testing errors

