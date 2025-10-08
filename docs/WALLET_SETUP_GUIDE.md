# Wallet Setup Guide 🏦

**Purpose**: Complete guide for setting up testnet and mainnet wallets for all environments  
**Updated**: October 3, 2025

---

## 📚 **Related Documentation**

- **OnChain Execution** → [specs/07_ONCHAIN_EXECUTION_MANAGER.md](specs/07_ONCHAIN_EXECUTION_MANAGER.md) (wallet integration)
- **Configuration** → [CONFIG_WORKFLOW.md](CONFIG_WORKFLOW.md) (environment setup)
- **Data Requirements** → [DATA_VALIDATION_GUIDE.md](DATA_VALIDATION_GUIDE.md) (network requirements)

---

## 🎯 **Environment Overview**

| Environment | Network | CEX APIs | ERC-20 Wallet | Purpose |
|-------------|---------|----------|---------------|---------|
| **dev** | Sepolia Testnet | Testnet APIs | Testnet Wallet | Free testing, full E2E |
| **Staging** | Mainnet | Mainnet APIs | Mainnet Wallet (Small) | Real money testing, small amounts |
| **Production** | Mainnet | Mainnet APIs | Mainnet Wallet (Full) | Live trading, full amounts |

---

## 🔧 **ERC-20 Wallet Setup**

### **What is an ERC-20 Wallet?**
- **Blockchain wallet** (NOT a CEX wallet)
- Holds ETH and ERC-20 tokens (USDT, weETH, etc.)
- Used for on-chain operations: AAVE, staking, flash loans, gas payments
- **Private key** = access to the wallet (keep secure!)

### **How to Create Wallets**

#### **Option 1: MetaMask (Recommended)**
1. **Install MetaMask** browser extension
2. **Create new wallet** (don't use existing one!)
3. **Export private key**:
   - Click account icon → Account details → Export private key
   - **Remove 0x prefix** when copying to env file
4. **Copy wallet address** (with 0x prefix)

#### **Option 2: Programmatic (Advanced)**
```python
from eth_account import Account
import secrets

# Generate new wallet
private_key = "0x" + secrets.token_hex(32)
account = Account.from_key(private_key)

print(f"Private Key: {private_key[2:]}")  # Remove 0x
print(f"Address: {account.address}")
```

### **Wallet Requirements by Environment**

#### **dev (Testnet)**
- **Network**: Sepolia Testnet
- **Funding**: Get testnet ETH from https://sepoliafaucet.com/
- **Amount**: 1-2 ETH (testnet is free)
- **Purpose**: Full E2E testing without real money

#### **Staging (Mainnet - Small)**
- **Network**: Ethereum Mainnet
- **Funding**: Real ETH (small amount: 0.1-0.5 ETH)
- **Purpose**: Real money testing with small amounts
- **Safety**: Use separate wallet from production

#### **Production (Mainnet - Full)**
- **Network**: Ethereum Mainnet
- **Funding**: Real ETH (full amount for trading)
- **Purpose**: Live trading with full amounts
- **Safety**: Use separate wallet from staging

---

## 🏦 **CEX API Setup**

### **dev Environment (Testnet APIs)**

#### **Binance Testnet**
1. **Go to**: https://testnet.binance.vision/
2. **Create account** (separate from main account)
3. **Get API keys**:
   - API Key
   - Secret Key
4. **Enable permissions**: Spot trading, Futures trading
5. **Add to env**: `BASIS_DEV__CEX__BINANCE_SPOT_API_KEY=...`

#### **Bybit Testnet**
1. **Go to**: https://testnet.bybit.com/
2. **Create account** (separate from main account)
3. **Get API keys**:
   - API Key
   - Secret Key
4. **Enable permissions**: Trading
5. **Add to env**: `BASIS_DEV__CEX__BYBIT_API_KEY=...`

#### **OKX Testnet**
1. **Go to**: https://www.okx.com/developers/testnet
2. **Create account** (separate from main account)
3. **Get API keys**:
   - API Key
   - Secret Key
   - Passphrase
4. **Enable permissions**: Trading
5. **Add to env**: `BASIS_DEV__CEX__OKX_API_KEY=...`

### **Staging/Production Environment (Mainnet APIs)**

#### **Binance Mainnet**
1. **Go to**: https://www.binance.com/en/my/settings/api-management
2. **Create API key** (separate from testnet)
3. **Set restrictions**:
   - **Staging**: IP restrictions, small amounts
   - **Production**: Full permissions
4. **Enable permissions**: Spot trading, Futures trading
5. **Add to env**: `BASIS_STAGING__CEX__BINANCE_SPOT_API_KEY=...`

#### **Bybit Mainnet**
1. **Go to**: https://www.bybit.com/app/user/api-management
2. **Create API key** (separate from testnet)
3. **Set restrictions**:
   - **Staging**: IP restrictions, small amounts
   - **Production**: Full permissions
4. **Enable permissions**: Trading
5. **Add to env**: `BASIS_STAGING__CEX__BYBIT_API_KEY=...`

#### **OKX Mainnet**
1. **Go to**: https://www.okx.com/account/my-api
2. **Create API key** (separate from testnet)
3. **Set restrictions**:
   - **Staging**: IP restrictions, small amounts
   - **Production**: Full permissions
4. **Enable permissions**: Trading
5. **Add to env**: `BASIS_STAGING__CEX__OKX_API_KEY=...`

---

## 🔄 **Hybrid Testnet Testing Reality**

### **Network Separation Reality**
❌ **You CANNOT directly send Sepolia tokens to CEX testnets** - they're different networks
✅ **You CAN test the complete flow** using the hybrid approach:

1. **System simulates** cross-network transfers
2. **Real CEX trading** on CEX testnets
3. **Real DeFi operations** on Sepolia testnet
4. **Complete strategy logic** with simulated transfers
5. **Full E2E testing** without real money

### **How Hybrid Testing Works**
- **Sepolia Wallet**: Real blockchain operations (AAVE, staking, flash loans)
- **CEX Testnets**: Real trading operations (spot, perps, hedging)
- **Cross-Network**: System simulates transfers between networks
- **Balance Tracking**: System maintains separate balance tracking

### **What You CAN Test**
- ✅ **Real CEX trading** (spot, perps) on CEX testnets
- ✅ **Real DeFi operations** (staking, lending, flash loans) on Sepolia
- ✅ **Complete strategy logic** with simulated cross-network transfers
- ✅ **All rebalancing logic** and risk management
- ✅ **Full E2E workflow** testing
- ✅ **Error handling** and API integrations

### **What You CANNOT Test**
- ❌ **Real cross-network transfers** (system simulates these)
- ❌ **Real gas costs** (testnet gas is free)
- ❌ **Real slippage** (testnet has perfect liquidity)
- ❌ **Real network congestion** effects
- ❌ **Real market volatility**

---

## 📝 **Environment File Setup**

### **Complete Environment Configuration**

```bash
# Environment Control
BASIS_ENVIRONMENT=dev  # dev | staging | production

# =============================================================================
# dev ENVIRONMENT (Testnet Everything)
# =============================================================================
# CEX APIs - Testnet
BASIS_DEV__CEX__BINANCE_SPOT_API_KEY=your_testnet_binance_spot_key
BASIS_DEV__CEX__BINANCE_SPOT_SECRET=your_testnet_binance_spot_secret
BASIS_DEV__CEX__BINANCE_FUTURES_API_KEY=your_testnet_binance_futures_key
BASIS_DEV__CEX__BINANCE_FUTURES_SECRET=your_testnet_binance_futures_secret
BASIS_DEV__CEX__BYBIT_API_KEY=your_testnet_bybit_key
BASIS_DEV__CEX__BYBIT_SECRET=your_testnet_bybit_secret
BASIS_DEV__CEX__OKX_API_KEY=your_testnet_okx_key
BASIS_DEV__CEX__OKX_SECRET=your_testnet_okx_secret
BASIS_DEV__CEX__OKX_PASSPHRASE=your_testnet_okx_passphrase

# ERC-20 Wallet - Testnet
BASIS_DEV__ALCHEMY__PRIVATE_KEY=your_testnet_wallet_private_key_no_0x_prefix
BASIS_DEV__ALCHEMY__WALLET_ADDRESS=0x...
BASIS_DEV__ALCHEMY__RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your_sepolia_key
BASIS_DEV__ALCHEMY__NETWORK=sepolia
BASIS_DEV__ALCHEMY__CHAIN_ID=11155111

# =============================================================================
# STAGING ENVIRONMENT (Real Everything - Small Amounts)
# =============================================================================
# CEX APIs - Mainnet (Small amounts)
BASIS_STAGING__CEX__BINANCE_SPOT_API_KEY=your_staging_binance_spot_key
BASIS_STAGING__CEX__BINANCE_SPOT_SECRET=your_staging_binance_spot_secret
# ... (same pattern for all CEX APIs)

# ERC-20 Wallet - Mainnet (Small amounts)
BASIS_STAGING__ALCHEMY__PRIVATE_KEY=your_staging_wallet_private_key_no_0x_prefix
BASIS_STAGING__ALCHEMY__WALLET_ADDRESS=0x...
BASIS_STAGING__ALCHEMY__RPC_URL=https://eth-mainnet.g.alchemy.com/v2/your_mainnet_key
BASIS_STAGING__ALCHEMY__NETWORK=mainnet
BASIS_STAGING__ALCHEMY__CHAIN_ID=1

# =============================================================================
# PRODUCTION ENVIRONMENT (Real Everything - Full Amounts)
# =============================================================================
# CEX APIs - Mainnet (Full amounts)
BASIS_PROD__CEX__BINANCE_SPOT_API_KEY=your_prod_binance_spot_key
BASIS_PROD__CEX__BINANCE_SPOT_SECRET=your_prod_binance_spot_secret
# ... (same pattern for all CEX APIs)

# ERC-20 Wallet - Mainnet (Full amounts)
BASIS_PROD__ALCHEMY__PRIVATE_KEY=your_prod_wallet_private_key_no_0x_prefix
BASIS_PROD__ALCHEMY__WALLET_ADDRESS=0x...
BASIS_PROD__ALCHEMY__RPC_URL=https://eth-mainnet.g.alchemy.com/v2/your_prod_mainnet_key
BASIS_PROD__ALCHEMY__NETWORK=mainnet
BASIS_PROD__ALCHEMY__CHAIN_ID=1
```

---

## 🚀 **Quick Start**

### **Step 1: dev Setup**
1. **Create testnet wallets** (MetaMask + CEX testnet accounts)
2. **Get testnet ETH** from Sepolia faucet
3. **Set**: `BASIS_ENVIRONMENT=dev`
4. **Fill in**: All `BASIS_DEV__*` variables
5. **Test**: Full E2E flow with fake money

### **Step 2: Staging Setup**
1. **Create mainnet wallets** (separate from dev)
2. **Fund with small amounts** (0.1-0.5 ETH)
3. **Set**: `BASIS_ENVIRONMENT=staging`
4. **Fill in**: All `BASIS_STAGING__*` variables
5. **Test**: Real money with small amounts

### **Step 3: Production Setup**
1. **Create production wallets** (separate from staging)
2. **Fund with full amounts**
3. **Set**: `BASIS_ENVIRONMENT=production`
4. **Fill in**: All `BASIS_PROD__*` variables
5. **Deploy**: Live trading with full amounts

---

## ⚠️ **Security Best Practices**

### **Wallet Security**
- ✅ **Use separate wallets** for each environment
- ✅ **Never reuse wallets** between environments
- ✅ **Keep private keys secure** (use hardware wallets for production)
- ✅ **Test with small amounts** before going live

### **API Key Security**
- ✅ **Use separate API keys** for each environment
- ✅ **Set IP restrictions** where possible
- ✅ **Enable only required permissions**
- ✅ **Monitor API usage** regularly

### **Environment Separation**
- ✅ **Never mix testnet/mainnet** in same environment
- ✅ **Use different wallets** for staging vs production
- ✅ **Test thoroughly** in dev before staging
- ✅ **Start small** in staging before production

---

**Ready to set up your wallets?** Start with dev environment and test the complete E2E flow with fake money! 🎯
