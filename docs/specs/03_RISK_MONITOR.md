# Component Spec: Risk Monitor ⚠️

**Component**: Risk Monitor  
**Responsibility**: Calculate risk metrics from exposure data and trigger alerts  
**Priority**: ⭐⭐⭐ CRITICAL (Prevents liquidations)  
**Backend File**: `backend/src/basis_strategy_v1/core/rebalancing/risk_monitor.py` ✅ **CORRECT**

---

## 🎯 **Purpose**

Monitor three types of risk using exposure data:
1. **AAVE LTV Risk** - Loan-to-value ratio on lending protocol
2. **CEX Margin Risk** - Margin ratios on perpetual futures
3. **Net Delta Risk** - Deviation from target delta (market neutrality)

**Key Principles**:
- **Reactive**: Triggered by Exposure Monitor updates
- **Multi-venue**: Track each CEX separately
- **Threshold-based**: Warning, urgent, critical levels
- **Fail-safe**: Conservative thresholds (user buffer above venue liquidation)

**Data Flow Integration**:
- **Input**: Receives `exposure` and `market_data` as parameters
- **Method**: `assess_risk(exposure, market_data=None)`
- **No Direct Dependencies**: Doesn't hold DataProvider references
- **Data Source**: Exposure data from ExposureMonitor, market data from EventDrivenStrategyEngine

---

## 📊 **Data Structures**

### **Input**: Exposure Data (from Exposure Monitor)

```python
{
    'timestamp': timestamp,
    'exposures': {...},  # Per-token breakdown
    'net_delta_eth': -5.118,
    'erc20_wallet_net_delta_eth': +3.104,
    'cex_wallet_net_delta_eth': -8.222,
    'total_value_usd': 99753.45
}
```

### **Output**: Risk Metrics

```python
{
    'timestamp': timestamp,
    
    # AAVE Risk
    'aave': {
        'ltv': 0.892,                    # Current LTV (debt / collateral)
        'health_factor': 1.067,          # (LT × collateral) / debt
        'collateral_value_eth': 107.44,
        'debt_value_eth': 95.796,
        'safe_ltv_threshold': 0.91,      # From config (target operating LTV)
        'max_ltv': 0.93,                 # AAVE protocol max (can't withdraw above this)
        'liquidation_threshold': 0.95,   # LTV where liquidation happens (weETH E-mode)
        'liquidation_bonus': 0.01,       # Penalty if liquidated (1% for E-mode)
        'buffer_to_max_ltv': 0.038,      # 93% - 89.2% = 3.8%
        'pct_move_to_liquidation': 6.25, # % ETH can drop before liquidation (based on HF)
        'status': 'SAFE',                # 'SAFE', 'WARNING', 'CRITICAL'
        'warning': False,                # ltv > 85%
        'critical': False                # ltv > 90%
    },
    
    # CEX Margin Risk (per exchange)
    'cex_margin': {
        'binance': {
            'balance_usdt': 24992.50,
            'exposure_usdt': 28299.47,      # Mark-to-market value of perps
            'margin_ratio': 0.883,          # balance / exposure
            'required_margin': 4244.92,     # 15% initial margin
            'free_margin': 20747.58,        # balance - required
            'maintenance_margin': 0.10,     # Binance liquidation threshold
            'buffer_to_liquidation': 0.783, # 88.3% - 10% = 78.3%
            'status': 'SAFE',
            'warning': False,               # ratio < 20%
            'critical': False               # ratio < 12%
        },
        'bybit': {
            'balance_usdt': 24985.30,
            'exposure_usdt': 28277.38,
            'margin_ratio': 0.884,
            'status': 'SAFE',
            'warning': False,
            'critical': False
        },
        'okx': {
            'balance_usdt': 24980.15,
            'exposure_usdt': 28267.89,
            'margin_ratio': 0.884,
            'status': 'SAFE',
            'warning': False,
            'critical': False
        },
        'min_margin_ratio': 0.883,          # Worst exchange
        'any_warning': False,
        'any_critical': False
    },
    
    # Net Delta Risk
    'delta': {
        'net_delta_eth': -5.118,
        'target_delta_eth': 0.0,            # From mode (0 for market-neutral)
        'delta_drift_eth': -5.118,          # Current - target
        'delta_drift_pct': -3.01,           # vs initial capital in ETH
        'drift_threshold_pct': 5.0,         # From config
        'status': 'SAFE',                   # < 5% is safe
        'warning': False,                   # > 3%
        'critical': False                   # > 5%
    },
    
    # Overall status (worst of all risks)
    'overall_status': 'SAFE',               # 'SAFE', 'WARNING', 'CRITICAL'
    'any_warnings': False,
    'any_critical_alerts': False,
    
    # Alerts (list of triggered alerts)
    'alerts': []  # e.g., ['binance_margin_warning', 'delta_drift_warning']
}
```

---

## 💻 **Core Functions**

```python
class RiskMonitor:
    """Monitor all risk metrics."""
    
    def __init__(self, config, exposure_monitor=None, data_provider=None):
        self.config = config
        self.exposure_monitor = exposure_monitor
        self.data_provider = data_provider
        
        # Risk thresholds from config (FAIL-FAST - no .get() defaults!)
        self.aave_safe_ltv = config['strategy']['target_ltv']  # Fail if missing
        self.aave_ltv_warning = config['risk']['aave_ltv_warning']  # Fail if missing
        self.aave_ltv_critical = config['risk']['aave_ltv_critical']  # Fail if missing
        
        # Load AAVE risk parameters (liquidation bonuses)
        import json
        from pathlib import Path
        risk_params_path = Path(config.get('data_dir', 'data')) / 'protocol_data/aave/risk_params/aave_v3_risk_parameters.json'
        with open(risk_params_path, 'r') as f:
            self.aave_risk_params = json.load(f)
        self.aave_liquidation_bonus_emode = self.aave_risk_params['emode']['liquidation_bonus']['weETH_WETH']  # 0.01
        self.aave_liquidation_threshold_emode = self.aave_risk_params['emode']['liquidation_thresholds']['weETH_WETH']  # 0.95
        
        self.margin_warning_threshold = config['risk']['margin_warning_pct']  # e.g., 0.20
        self.margin_critical_threshold = config['risk']['margin_critical_pct']  # e.g., 0.12
        self.margin_liquidation = 0.10  # Venue constant (all CEXs)
        
        self.delta_threshold_pct = config['strategy']['rebalance_threshold_pct']  # e.g., 5.0
        
        # Redis
        self.redis = redis.Redis()
        self.redis.subscribe('exposure:calculated', self._on_exposure_update)
    
    async def assess_risk(self, exposure_data: Dict, timestamp: pd.Timestamp = None) -> Dict:
        """
        Unified risk assessment (PUBLIC API - called by EventDrivenStrategyEngine).
        
        This is a wrapper that calls calculate_overall_risk() internally.
        """
        return await self.calculate_overall_risk(exposure_data)
    
    async def calculate_risks(self, exposure_data: Dict) -> Dict:
        """
        Calculate all risk metrics from exposure data.
        
        Triggered by: Exposure Monitor updates
        
        Returns: Complete risk assessment
        """
        risks = {
            'timestamp': exposure_data['timestamp'],
            'aave': self._calculate_aave_risk(exposure_data),
            'cex_margin': self._calculate_cex_margin_risk(exposure_data),
            'delta': self._calculate_delta_risk(exposure_data),
        }
        
        # Overall status (worst of all)
        all_statuses = [
            risks['aave']['status'],
            risks['cex_margin'].get('min_status', 'SAFE'),
            risks['delta']['status']
        ]
        
        if 'CRITICAL' in all_statuses:
            risks['overall_status'] = 'CRITICAL'
        elif 'WARNING' in all_statuses:
            risks['overall_status'] = 'WARNING'
        else:
            risks['overall_status'] = 'SAFE'
        
        # Collect all alerts
        risks['alerts'] = self._collect_alerts(risks)
        risks['any_warnings'] = any(s['warning'] for s in [risks['aave'], risks['delta']] + list(risks['cex_margin'].values()) if isinstance(s, dict) and 'warning' in s)
        risks['any_critical_alerts'] = any(s['critical'] for s in [risks['aave'], risks['delta']] + list(risks['cex_margin'].values()) if isinstance(s, dict) and 'critical' in s)
        
        # Publish to Redis
        await self.redis.set('risk:current', json.dumps(risks))
        await self.redis.publish('risk:calculated', json.dumps({
            'timestamp': risks['timestamp'].isoformat(),
            'overall_status': risks['overall_status'],
            'alerts': risks['alerts']
        }))
        
        return risks
    
    def _calculate_aave_risk(self, exposure_data: Dict) -> Dict:
        """Calculate AAVE LTV and health factor risk."""
        # Get AAVE exposures
        aave_collateral_eth = 0.0
        aave_debt_eth = 0.0
        
        for token, exp in exposure_data['exposures'].items():
            if 'aWeETH' in token or 'awstETH' in token:
                aave_collateral_eth += exp['exposure_eth']
            elif 'variableDebt' in token:
                aave_debt_eth += exp['exposure_eth']
        
        # Calculate metrics
        if aave_collateral_eth > 0 and aave_debt_eth > 0:
            ltv = aave_debt_eth / aave_collateral_eth
            
            # Health Factor = (LT × collateral) / debt
            liquidation_threshold = 0.95  # E-mode for weETH/wstETH (this is the LTV where liquidation happens)
            health_factor = (liquidation_threshold * aave_collateral_eth) / aave_debt_eth
            
            # Calculate % move to liquidation
            # HF = 1 means liquidation
            # Current HF = 1.067
            # ETH can drop by: (1 - 1/HF) × 100 = (1 - 1/1.067) × 100 = 6.28%
            pct_move_to_liquidation = (1 - 1/health_factor) * 100 if health_factor > 1 else 0
        else:
            ltv = 0.0
            health_factor = float('inf')
            pct_move_to_liquidation = 100.0  # No risk
        
        # Check thresholds
        warning = ltv > self.aave_ltv_warning
        critical = ltv > self.aave_ltv_critical
        
        if critical:
            status = 'CRITICAL'
        elif warning:
            status = 'WARNING'
        else:
            status = 'SAFE'
        
        return {
            'ltv': ltv,
            'health_factor': health_factor,
            'collateral_value_eth': aave_collateral_eth,
            'debt_value_eth': aave_debt_eth,
            'safe_ltv_threshold': self.aave_safe_ltv,
            'liquidation_ltv': 0.93,  # AAVE E-mode max
            'liquidation_threshold': liquidation_threshold,
            'buffer_to_liquidation': 0.93 - ltv,
            'status': status,
            'warning': warning,
            'critical': critical
        }
    
    def _calculate_cex_margin_risk(self, exposure_data: Dict) -> Dict:
        """Calculate CEX margin ratios per exchange."""
        cex_risks = {}
        
        for venue in ['binance', 'bybit', 'okx']:
            # Get CEX balance
            balance_key = f'{venue}_USDT'
            balance_usdt = exposure_data['exposures'].get(balance_key, {}).get('balance', 0)
            
            # Get perp exposure (mark-to-market)
            exposure_usdt = 0.0
            for token, exp in exposure_data['exposures'].items():
                if token.startswith(f'{venue}_') and 'PERP' in token:
                    exposure_usdt += abs(exp['exposure_usd'])
            
            if exposure_usdt > 0:
                margin_ratio = balance_usdt / exposure_usdt
                required_margin = exposure_usdt * 0.15  # 15% initial margin
                free_margin = balance_usdt - required_margin
            else:
                margin_ratio = 1.0
                required_margin = 0.0
                free_margin = balance_usdt
            
            # Check thresholds
            warning = margin_ratio < self.margin_warning_threshold
            critical = margin_ratio < self.margin_critical_threshold
            
            if critical:
                status = 'CRITICAL'
            elif warning:
                status = 'WARNING'
            else:
                status = 'SAFE'
            
            cex_risks[venue] = {
                'balance_usdt': balance_usdt,
                'exposure_usdt': exposure_usdt,
                'margin_ratio': margin_ratio,
                'required_margin': required_margin,
                'free_margin': free_margin,
                'maintenance_margin': self.margin_liquidation,
                'buffer_to_liquidation': margin_ratio - self.margin_liquidation,
                'status': status,
                'warning': warning,
                'critical': critical
            }
        
        # Find worst exchange
        ratios = [v['margin_ratio'] for v in cex_risks.values() if v['exposure_usdt'] > 0]
        min_margin_ratio = min(ratios) if ratios else 1.0
        
        cex_risks['min_margin_ratio'] = min_margin_ratio
        cex_risks['any_warning'] = any(v.get('warning', False) for v in cex_risks.values())
        cex_risks['any_critical'] = any(v.get('critical', False) for v in cex_risks.values())
        
        return cex_risks
    
    def _calculate_delta_risk(self, exposure_data: Dict) -> Dict:
        """Calculate net delta risk."""
        net_delta_eth = exposure_data['net_delta_eth']
        
        # Target delta depends on mode
        # (From config or Strategy Manager)
        target_delta_eth = self.config['strategy'].get('target_delta_eth', 0.0)
        
        # Calculate drift
        delta_drift_eth = net_delta_eth - target_delta_eth
        
        # As percentage of TOKEN EQUITY (not initial capital!)
        # This scales properly with deposits/withdrawals
        token_equity_eth = exposure_data['token_equity_eth']
        
        if token_equity_eth > 0:
            delta_drift_pct = (abs(delta_drift_eth) / token_equity_eth) * 100
        else:
            delta_drift_pct = 0.0
        
        # Check thresholds
        warning = delta_drift_pct > (self.delta_threshold_pct * 0.6)  # 60% of threshold
        critical = delta_drift_pct > self.delta_threshold_pct
        
        if critical:
            status = 'CRITICAL'
        elif warning:
            status = 'WARNING'
        else:
            status = 'SAFE'
        
        return {
            'net_delta_eth': net_delta_eth,
            'target_delta_eth': target_delta_eth,
            'delta_drift_eth': delta_drift_eth,
            'delta_drift_pct': delta_drift_pct,
            'drift_threshold_pct': self.delta_threshold_pct,
            'status': status,
            'warning': warning,
            'critical': critical
        }
```

---

## 🔔 **Alert Generation**

```python
def _collect_alerts(self, risks: Dict) -> List[str]:
    """Collect all triggered alerts."""
    alerts = []
    
    # AAVE alerts
    if risks['aave']['critical']:
        alerts.append('AAVE_LTV_CRITICAL')
    elif risks['aave']['warning']:
        alerts.append('AAVE_LTV_WARNING')
    
    # CEX margin alerts (per exchange)
    for venue in ['binance', 'bybit', 'okx']:
        venue_risk = risks['cex_margin'][venue]
        if venue_risk['critical']:
            alerts.append(f'{venue.upper()}_MARGIN_CRITICAL')
        elif venue_risk['warning']:
            alerts.append(f'{venue.upper()}_MARGIN_WARNING')
    
    # Delta alerts
    if risks['delta']['critical']:
        alerts.append('DELTA_DRIFT_CRITICAL')
    elif risks['delta']['warning']:
        alerts.append('DELTA_DRIFT_WARNING')
    
    return alerts
```

---

    def simulate_liquidation(
        self,
        collateral_eth: float,
        debt_eth: float,
        eth_price_drop_pct: float
    ) -> Optional[Dict]:
        """
        Simulate AAVE liquidation if ETH drops by X%.
        
        AAVE v3 Liquidation Logic:
        1. If HF < 1, position can be liquidated
        2. Liquidator repays up to 50% of debt on your behalf
        3. Liquidator seizes: debt_repaid × (1 + liquidation_bonus) of collateral
        4. You lose collateral > debt repaid (the bonus is your penalty)
        
        Example:
        - Liquidator repays 100 WETH debt
        - Liquidator seizes 101 WETH worth of weETH (1% bonus)
        - You lose 1 WETH extra (incentive for liquidators)
        
        Args:
            collateral_eth: Current AAVE collateral in ETH
            debt_eth: Current AAVE debt in ETH
            eth_price_drop_pct: How much ETH drops (e.g., 10 for 10%)
        
        Returns:
            Liquidation result dict or None if position remains safe
        """
        # Simulate price drop (collateral value drops)
        new_collateral_eth = collateral_eth * (1 - eth_price_drop_pct / 100)
        
        # Debt unchanged (denominated in ETH/WETH)
        new_debt_eth = debt_eth
        
        # Calculate new health factor
        liquidation_threshold = 0.95  # weETH E-mode
        new_hf = (liquidation_threshold * new_collateral_eth) / new_debt_eth if new_debt_eth > 0 else float('inf')
        
        if new_hf >= 1.0:
            return None  # Safe, no liquidation
        
        # Liquidation triggered!
        logger.warning(f"🚨 LIQUIDATION SIMULATED: HF={new_hf:.3f} after {eth_price_drop_pct}% ETH drop")
        
        # Liquidator repays up to 50% of debt (AAVE protocol rule)
        max_debt_repaid_eth = new_debt_eth * 0.50
        
        # Liquidator seizes collateral (with bonus)
        liquidation_bonus = 0.01  # 1% for E-mode (5-7% for normal mode)
        collateral_seized_eth = max_debt_repaid_eth * (1 + liquidation_bonus)
        
        # Position after liquidation
        remaining_collateral_eth = new_collateral_eth - collateral_seized_eth
        remaining_debt_eth = new_debt_eth - max_debt_repaid_eth
        
        # Health factor after liquidation (should be > 1 now)
        post_liquidation_hf = (liquidation_threshold * remaining_collateral_eth) / remaining_debt_eth if remaining_debt_eth > 0 else float('inf')
        post_liquidation_ltv = remaining_debt_eth / remaining_collateral_eth if remaining_collateral_eth > 0 else 0
        
        return {
            'liquidated': True,
            'trigger': f'ETH dropped {eth_price_drop_pct}%, HF fell below 1.0',
            'pre_liquidation': {
                'collateral_eth': new_collateral_eth,
                'debt_eth': new_debt_eth,
                'health_factor': new_hf,
                'ltv': new_debt_eth / new_collateral_eth if new_collateral_eth > 0 else 0
            },
            'liquidation_details': {
                'debt_repaid_eth': max_debt_repaid_eth,
                'collateral_seized_eth': collateral_seized_eth,
                'liquidation_bonus': liquidation_bonus,
                'user_loss_eth': collateral_seized_eth - max_debt_repaid_eth  # Penalty
            },
            'post_liquidation': {
                'remaining_collateral_eth': remaining_collateral_eth,
                'remaining_debt_eth': remaining_debt_eth,
                'health_factor': post_liquidation_hf,
                'ltv': post_liquidation_ltv
            }
        }

    
    def simulate_cex_liquidation(
        self,
        venue: str,
        current_margin_usdt: float,
        position_exposure_usdt: float
    ) -> Optional[Dict]:
        """
        Simulate CEX liquidation (catastrophic - lose ALL margin).
        
        CEX Liquidation (Binance/Bybit/OKX):
        - Maintenance margin: 10%
        - If margin_ratio < 10%: LIQUIDATION TRIGGERED
        - Result: Account balance → 0 (ALL margin lost)
        - Position closed at market
        
        Args:
            venue: Exchange (binance, bybit, okx)
            current_margin_usdt: Current margin balance
            position_exposure_usdt: Mark-to-market position value
            
        Returns:
            Liquidation result or None if safe
        """
        maintenance_margin = 0.10
        margin_ratio = current_margin_usdt / position_exposure_usdt if position_exposure_usdt > 0 else 1.0
        
        if margin_ratio >= maintenance_margin:
            return None  # Safe
        
        # CATASTROPHIC LIQUIDATION
        return {
            'liquidated': True,
            'venue': venue,
            'margin_lost': current_margin_usdt,  # ALL
            'remaining_balance': 0.0,
            'balance_updates': {
                f'{venue}_USDT': 0.0  # Account wiped
            }
        }

---

## 🔗 **Integration**

### **Triggered By**:
- Exposure Monitor updates (sync chain: position → exposure → risk)

### **Uses Data From**:
- **Exposure Monitor** ← Exposure breakdown
- **Config** ← Risk thresholds

### **Publishes To**:
- **Strategy Manager** ← Risk metrics (for rebalancing decisions)
- **Event Logger** ← Risk alerts

### **Redis**:

**Subscribes**:
- `exposure:calculated` → Triggers risk calculation

**Publishes**:
- `risk:calculated` (channel) → Notifies Strategy Manager
- `risk:current` (key) → Latest risk metrics

---

## 🧪 **Testing**

```python
def test_aave_ltv_calculation():
    """Test AAVE LTV and HF calculations."""
    exposure = {
        'exposures': {
            'aWeETH': {'exposure_eth': 107.44},
            'variableDebtWETH': {'exposure_eth': 95.796}
        }
    }
    
    risk = RiskMonitor(config, exposure_monitor)
    aave_risk = risk._calculate_aave_risk(exposure)
    
    # LTV = debt / collateral
    expected_ltv = 95.796 / 107.44
    assert aave_risk['ltv'] == pytest.approx(expected_ltv, abs=0.001)
    
    # HF = (0.95 × 107.44) / 95.796
    expected_hf = (0.95 * 107.44) / 95.796
    assert aave_risk['health_factor'] == pytest.approx(expected_hf, abs=0.001)

def test_margin_ratio_warning():
    """Test CEX margin warnings trigger correctly."""
    exposure = {
        'exposures': {
            'binance_USDT': {'balance': 5000},  # Low balance
            'binance_ETHUSDT-PERP': {'exposure_usd': 28000}  # High exposure
        }
    }
    
    risk = RiskMonitor(config, exposure_monitor)
    cex_risk = risk._calculate_cex_margin_risk(exposure)
    
    # Margin ratio = 5000 / 28000 = 17.9% (below 20% warning!)
    assert cex_risk['binance']['margin_ratio'] < 0.20
    assert cex_risk['binance']['warning'] == True
    assert cex_risk['binance']['status'] == 'WARNING'
```

---

## 🎯 **Mode-Specific Behavior**

### **Pure Lending**:
```python
# Only AAVE risk matters
# No CEX margin risk (no perps)
# No delta risk (no hedging)
```

### **BTC Basis**:
```python
# No AAVE risk (no lending)
# CEX margin risk (BTC perps)
# Delta risk (should be ~0 for market-neutral)
```

### **ETH Leveraged** (ETH share class):
```python
# AAVE risk (leveraged staking)
# No CEX margin risk (no hedging)
# No delta risk (directional ETH exposure is the strategy!)
```

### **USDT Market-Neutral**:
```python
# All three risks monitored!
# Most complex
```

---

## 🔄 **Backtest vs Live**

### **Backtest**:
- Triggered by exposure updates (sync chain)
- Calculates once per hour
- Logs warnings to console + event log

### **Live**:
- Same calculation logic
- But also:
  - Triggers real-time alerts (email, Telegram, etc.)
  - Can trigger emergency stops
  - Logs to monitoring system (Prometheus)

---

## 🎯 **Success Criteria**

- [ ] Calculates AAVE LTV correctly
- [ ] Calculates AAVE health factor correctly (HF = LT × C / D)
- [ ] Calculates margin ratios per exchange
- [ ] Calculates delta drift
- [ ] Triggers warnings at correct thresholds
- [ ] Triggers critical alerts before liquidation
- [ ] Mode-aware (only relevant risks per mode)
- [ ] Publishes to Strategy Manager via Redis
- [ ] Conservative thresholds (user buffer above venue limits)

---

**Status**: Specification complete! ✅

