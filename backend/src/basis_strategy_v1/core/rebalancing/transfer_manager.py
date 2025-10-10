"""Cross-Venue Transfer Manager - Execute intelligent transfers between venues.

TODO-REMOVE: STRATEGY MANAGER ARCHITECTURE VIOLATION - See docs/ARCHITECTURAL_DECISION_RECORDS.md
ISSUE: This component violates canonical architecture requirements and should be REMOVED:

1. STRATEGY MANAGER REFACTOR VIOLATIONS:
   - This 1068-line complex transfer manager should be completely removed
   - Too complex and strategy-agnostic generalization is not feasible
   - Should be replaced with inheritance-based strategy-specific implementations

2. REQUIRED REMOVAL (per ADR-007 + docs/MODES.md):
   - DELETE this entire file (1068 lines)
   - Remove all references to transfer_manager.py in strategy manager
   - Replace with inheritance-based strategy-specific implementations
   - Move venue routing logic to execution manager

3. REPLACEMENT ARCHITECTURE:
   - Create BaseStrategyManager with standardized wrapper actions
   - Create strategy-specific implementations: BTCBasisStrategyManager, ETHLeveragedStrategyManager, etc.
   - Create StrategyFactory for mode-based instantiation
   - Move venue routing to ExecutionManager
   - **Reference**: docs/MODES.md - Standardized Strategy Manager Architecture section

4. CURRENT VIOLATIONS:
   - Overly complex architecture that doesn't align with canonical principles
   - Strategy-agnostic generalization that is not feasible
   - Should be replaced with inheritance-based strategy modes

CURRENT STATE: This file should be DELETED and replaced with inheritance-based strategy architecture.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging
from pathlib import Path


@dataclass
class Trade:
    """Represents a trade to be executed."""
    trade_type: str
    venue: str
    token: str
    amount: Decimal
    side: str
    purpose: str
    expected_fee: float = 0.0

logger = logging.getLogger(__name__)

# Create dedicated transfer manager logger
transfer_logger = logging.getLogger('transfer_manager')
transfer_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

# Create file handler for transfer manager logs
transfer_handler = logging.FileHandler(logs_dir / 'transfer_manager.log')
transfer_handler.setLevel(logging.INFO)

# Create formatter
transfer_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
transfer_handler.setFormatter(transfer_formatter)

# Add handler to logger
transfer_logger.addHandler(transfer_handler)


class CrossVenueTransferManager:
    """Manage transfers between venues for rebalancing."""
    
    def __init__(self, config: Dict[str, Any], portfolio: Dict[str, Any]):
        """Initialize cross-venue transfer manager."""
        self.config = config
        self.portfolio = portfolio
        self.strategy_config = config.get('strategy', {})
        self.fees_config = config.get('fees', {})
        
        # Transfer constraints
        self.min_transfer_usd = self.strategy_config.get('min_trade_amount_usd', 5000)
        self.max_single_transfer_usd = 100000  # Safety limit
        self.gas_cost_usd = self.fees_config.get('gas_cost_usd', 50)
        
        logger.info("CrossVenueTransferManager initialized")
    
    async def execute_optimal_transfer(
        self,
        source_venue: str,
        target_venue: str,
        amount_usd: float,
        market_data,
        purpose: str = "Rebalancing"
    ) -> List[Trade]:
        """Execute optimal transfer between venues."""
        try:
            logger.info(f"🔄 Planning transfer: ${amount_usd:,.2f} from {source_venue} → {target_venue}")
            
            # Validate transfer safety
            is_safe, error_msg = await self._validate_transfer_safety(
                source_venue, target_venue, amount_usd, market_data
            )
            
            if not is_safe:
                raise ValueError(f"Transfer validation failed: {error_msg}")
            
            # Determine optimal asset and route
            transfer_plan = await self._plan_optimal_transfer(
                source_venue, target_venue, amount_usd, market_data
            )
            
            # Execute transfer sequence
            trades = await self._execute_transfer_sequence(transfer_plan, market_data, purpose)
            
            logger.info(f"✅ Transfer planned: {len(trades)} trades, cost: ${transfer_plan['total_cost']:.2f}")
            return trades
            
        except Exception as e:
            logger.error(f"❌ Transfer execution failed: {e}")
            raise
    
    async def _validate_transfer_safety(
        self,
        source_venue: str,
        target_venue: str,
        amount_usd: float,
        market_data
    ) -> Tuple[bool, Optional[str]]:
        """Validate that transfer won't create unsafe conditions."""
        
        # Constraint 1: Minimum transfer size
        if amount_usd < self.min_transfer_usd:
            return False, f"Transfer too small: ${amount_usd:,.2f} < ${self.min_transfer_usd:,.2f}"
        
        # Constraint 2: Maximum transfer size
        if amount_usd > self.max_single_transfer_usd:
            return False, f"Transfer too large: ${amount_usd:,.2f} > ${self.max_single_transfer_usd:,.2f}"
        
        # Constraint 3: Source venue safety
        if source_venue == "AAVE":
            # Check if withdrawal would breach LTV safety
            safe_withdrawal = await self._calculate_max_safe_aave_withdrawal(market_data)
            if amount_usd > safe_withdrawal:
                return False, f"AAVE withdrawal would breach LTV safety: ${amount_usd:,.2f} > ${safe_withdrawal:,.2f}"
        
        elif source_venue == "BYBIT":
            # Check if withdrawal would breach margin safety
            safe_withdrawal = await self._calculate_max_safe_bybit_withdrawal(market_data)
            if amount_usd > safe_withdrawal:
                return False, f"Bybit withdrawal would breach margin safety: ${amount_usd:,.2f} > ${safe_withdrawal:,.2f}"
        
        elif source_venue == "ETHERFI":
            # Check available staked balance
            available_value = await self._calculate_available_etherfi_value(market_data)
            if amount_usd > available_value:
                return False, f"Insufficient EtherFi balance: ${amount_usd:,.2f} > ${available_value:,.2f}"
        
        return True, None
    
    async def _plan_optimal_transfer(
        self,
        source_venue: str,
        target_venue: str,
        amount_usd: float,
        market_data
    ) -> Dict[str, Any]:
        """Plan optimal transfer route with cost analysis."""
        
        # Determine best asset for transfer
        optimal_asset = await self._determine_optimal_transfer_asset(
            source_venue, target_venue, amount_usd, market_data
        )
        
        # Calculate transfer costs
        transfer_cost = await self._calculate_transfer_cost(
            source_venue, target_venue, amount_usd, optimal_asset
        )
        
        # Build transfer plan
        return {
            'source_venue': source_venue,
            'target_venue': target_venue,
            'amount_usd': amount_usd,
            'asset': optimal_asset,
            'total_cost': transfer_cost,
            'cost_bps': (transfer_cost / amount_usd) * 10000 if amount_usd > 0 else 0,
            'route_description': self._describe_transfer_route(source_venue, target_venue, optimal_asset),
            'steps': await self._plan_transfer_steps(source_venue, target_venue, amount_usd, optimal_asset, market_data)
        }
    
    async def _determine_optimal_transfer_asset(
        self,
        source_venue: str,
        target_venue: str,
        amount_usd: float,
        market_data
    ) -> str:
        """Determine most efficient asset for cross-venue transfer."""
        
        # EtherFi transfers
        if source_venue == "ETHERFI":
            if target_venue == "BYBIT":
                # weETH → ETH → Bybit (free unstaking + ETH transfer)
                return "ETH"
            elif target_venue == "AAVE":
                # Keep as weETH for AAVE collateral (most efficient)
                return "weETH"
        
        # AAVE transfers
        elif source_venue == "AAVE":
            if target_venue == "BYBIT":
                # USDT withdrawal → Bybit margin (most efficient)
                return "USDT"
            elif target_venue == "ETHERFI":
                # USDT → ETH → stake (for increasing staking exposure)
                return "ETH"
        
        # Bybit transfers
        elif source_venue == "BYBIT":
            if target_venue == "AAVE":
                # Withdraw USDT margin → AAVE collateral
                return "USDT"
            elif target_venue == "ETHERFI":
                # Withdraw ETH → stake for yield
                return "ETH"
        
        return "USDT"  # Default to stablecoin for efficiency
    
    async def _plan_transfer_steps(
        self,
        source_venue: str,
        target_venue: str,
        amount_usd: float,
        asset: str,
        market_data
    ) -> List[Dict[str, Any]]:
        """Plan the sequence of trades needed for transfer."""
        steps = []
        
        if source_venue == "ETHERFI" and target_venue == "BYBIT":
            # Step 1: Unstake weETH → ETH
            eth_price = await market_data.get_price('ETH')
            eth_amount = amount_usd / eth_price
            
            steps.append({
                'step': 1,
                'action': 'unstake',
                'venue': 'ETHERFI',
                'from_token': 'weETH',
                'to_token': 'ETH',
                'amount': eth_amount,
                'description': f"Unstake {eth_amount:.6f} weETH → ETH (free)"
            })
            
            # Step 2: Transfer ETH to Bybit
            steps.append({
                'step': 2,
                'action': 'transfer',
                'venue': 'BYBIT',
                'token': 'ETH',
                'amount': eth_amount,
                'description': f"Transfer {eth_amount:.6f} ETH to Bybit margin"
            })
        
        elif source_venue == "AAVE" and target_venue == "BYBIT":
            # Step 1: Withdraw USDT from AAVE
            steps.append({
                'step': 1,
                'action': 'withdraw',
                'venue': 'AAVE',
                'token': 'USDT',
                'amount': amount_usd,
                'description': f"Withdraw ${amount_usd:,.2f} USDT from AAVE"
            })
            
            # Step 2: Transfer USDT to Bybit
            steps.append({
                'step': 2,
                'action': 'transfer',
                'venue': 'BYBIT',
                'token': 'USDT',
                'amount': amount_usd,
                'description': f"Transfer ${amount_usd:,.2f} USDT to Bybit margin"
            })
        
        elif source_venue == "BYBIT" and target_venue == "AAVE":
            # Step 1: Withdraw USDT from Bybit
            steps.append({
                'step': 1,
                'action': 'withdraw',
                'venue': 'BYBIT',
                'token': 'USDT',
                'amount': amount_usd,
                'description': f"Withdraw ${amount_usd:,.2f} USDT from Bybit margin"
            })
            
            # Step 2: Deposit USDT to AAVE
            steps.append({
                'step': 2,
                'action': 'deposit',
                'venue': 'AAVE',
                'token': 'USDT',
                'amount': amount_usd,
                'description': f"Deposit ${amount_usd:,.2f} USDT to AAVE collateral"
            })
        
        return steps
    
    async def _execute_transfer_sequence(
        self,
        transfer_plan: Dict[str, Any],
        market_data,
        purpose: str
    ) -> List[Trade]:
        """Execute the planned transfer sequence."""
        trades = []
        
        for step in transfer_plan['steps']:
            try:
                trade = await self._create_trade_from_step(step, market_data, purpose)
                trades.append(trade)
                
                logger.info(f"📋 Step {step['step']}: {step['description']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to create trade for step {step['step']}: {e}")
                raise
        
        return trades
    
    async def _create_trade_from_step(
        self,
        step: Dict[str, Any],
        market_data,
        purpose: str
    ) -> Trade:
        """Create a Trade object from a transfer step."""
        
        action = step['action']
        venue = step['venue']
        
        if action == 'unstake':
            return Trade(
                trade_type="unstaking",
                venue=venue,
                token=step['from_token'],
                amount=step['amount'],
                side="unstake",
                purpose=f"{purpose}: {step['description']}",
                expected_fee=0.0  # Unstaking is free
            )
        
        elif action == 'withdraw':
            return Trade(
                trade_type="lending_withdrawal",
                venue=venue,
                token=step['token'],
                amount=step['amount'],
                side="withdraw",
                purpose=f"{purpose}: {step['description']}",
                expected_fee=self.gas_cost_usd
            )
        
        elif action == 'deposit':
            return Trade(
                trade_type="lending_deposit",
                venue=venue,
                token=step['token'],
                amount=step['amount'],
                side="deposit",
                purpose=f"{purpose}: {step['description']}",
                expected_fee=self.gas_cost_usd
            )
        
        elif action == 'transfer':
            return Trade(
                trade_type="venue_transfer",
                venue=venue,
                token=step['token'],
                amount=step['amount'],
                side="deposit",
                purpose=f"{purpose}: {step['description']}",
                expected_fee=self.gas_cost_usd
            )
        
        else:
            raise ValueError(f"Unknown transfer action: {action}")
    
    async def _calculate_transfer_cost(
        self,
        source_venue: str,
        target_venue: str,
        amount_usd: float,
        asset: str
    ) -> float:
        """Calculate total cost of transfer including fees and opportunity costs."""
        
        # Base gas costs
        total_cost = self.gas_cost_usd * 2  # Assume 2 transactions
        
        # Venue-specific costs
        if source_venue == "ETHERFI":
            # Opportunity cost of lost staking yield
            daily_yield_rate = self.config['rates'].get('eeth_restaking_apr', 0.04) / 365.25
            opportunity_cost = amount_usd * daily_yield_rate * 7  # 1 week
            total_cost += opportunity_cost
            
        elif source_venue == "BYBIT":
            # Bybit withdrawal fees
            withdrawal_fee = amount_usd * self.fees_config.get('bybit_withdrawal_fee_bps', 10) / 10000
            total_cost += withdrawal_fee
        
        # Exchange fees if asset conversion needed
        if asset != "USDT":
            exchange_fee = amount_usd * self.fees_config.get('exchange_fee_bps', 5) / 10000
            total_cost += exchange_fee
        
        return total_cost
    
    def _describe_transfer_route(self, source_venue: str, target_venue: str, asset: str) -> str:
        """Generate human-readable description of transfer route."""
        if source_venue == "ETHERFI" and target_venue == "BYBIT":
            return f"Unstake weETH → {asset} → Bybit margin"
        elif source_venue == "AAVE" and target_venue == "BYBIT":
            return f"Withdraw {asset} from AAVE → Bybit margin"
        elif source_venue == "BYBIT" and target_venue == "AAVE":
            return f"Withdraw {asset} from Bybit → AAVE collateral"
        elif source_venue == "ETHERFI" and target_venue == "AAVE":
            return f"Unstake weETH → {asset} → AAVE collateral"
        else:
            return f"Transfer {asset}: {source_venue} → {target_venue}"
    
    async def _calculate_max_safe_aave_withdrawal(self, market_data) -> float:
        """Calculate maximum amount that can be safely withdrawn from AAVE."""
        try:
            # Get current AAVE state
            collateral_value = await self._calculate_aave_collateral_value(market_data)
            debt_value = await self._calculate_aave_debt_value(market_data)
            
            if collateral_value <= 0:
                return 0.0
            
            current_ltv = debt_value / collateral_value
            max_safe_ltv = Decimal("0.75")  # Conservative safe LTV
            
            # Calculate how much collateral can be withdrawn while staying safe
            required_collateral = debt_value / max_safe_ltv if max_safe_ltv > 0 else collateral_value
            safe_withdrawal = collateral_value - required_collateral
            
            return max(0.0, float(safe_withdrawal))
            
        except Exception as e:
            logger.error(f"Error calculating safe AAVE withdrawal: {e}")
            return 0.0
    
    async def _calculate_max_safe_bybit_withdrawal(self, market_data) -> float:
        """Calculate maximum amount that can be safely withdrawn from Bybit."""
        try:
            # Get current Bybit positions
            perp_positions = self._get_bybit_positions()
            
            if not perp_positions:
                # No positions - can withdraw all margin
                return float(self._get_bybit_margin_balance())
            
            # Calculate position value and margin requirements
            total_position_value = Decimal("0")
            for position_key, amount in perp_positions.items():
                symbol = position_key.replace('_PERP', '')
                base_token = symbol.replace('USDT', '')
                price = await market_data.get_price(base_token)
                total_position_value += abs(amount) * Decimal(str(price))
            
            # Required margin (20% for safety)
            required_margin = total_position_value * Decimal("0.20")
            available_margin = self._get_bybit_margin_balance()
            
            safe_withdrawal = available_margin - required_margin
            return max(0.0, float(safe_withdrawal))
            
        except Exception as e:
            logger.error(f"Error calculating safe Bybit withdrawal: {e}")
            return 0.0
    
    async def _calculate_available_etherfi_value(self, market_data) -> float:
        """Calculate available value at EtherFi for transfers."""
        try:
            weeth_balance = self.portfolio['positions'].get('weETH_ETHERFI', 0)
            if weeth_balance <= 0:
                return 0.0
            
            eth_price = await market_data.get_price('ETH')
            total_value = weeth_balance * eth_price
            
            # Reserve minimum staking balance
            min_staking_balance = self.strategy_config.get('min_staking_balance_usd', 10000)
            available_value = max(0, total_value - min_staking_balance)
            
            return float(available_value)
            
        except Exception as e:
            logger.error(f"Error calculating available EtherFi value: {e}")
            return 0.0
    
    async def _calculate_aave_collateral_value(self, market_data) -> Decimal:
        """Calculate total AAVE collateral value."""
        total_value = Decimal("0")
        
        for position_key, amount in self.portfolio['positions'].items():
            if '_AAVE' in position_key and 'DEBT' not in position_key and amount > 0:
                token = position_key.split('_')[0]
                price = await market_data.get_price(token)
                total_value += Decimal(str(amount)) * Decimal(str(price))
        
        return total_value
    
    async def _calculate_aave_debt_value(self, market_data) -> Decimal:
        """Calculate total AAVE debt value."""
        total_debt = Decimal("0")
        
        for position_key, amount in self.portfolio['positions'].items():
            if 'DEBT_AAVE' in position_key and amount > 0:
                token = position_key.split('_')[0]
                price = await market_data.get_price(token)
                total_debt += Decimal(str(amount)) * Decimal(str(price))
        
        return total_debt
    
    def _get_bybit_positions(self) -> Dict[str, float]:
        """Get all Bybit perpetual positions."""
        positions = {}
        for position_key, amount in self.portfolio['positions'].items():
            if '_PERP' in position_key and amount != 0:
                positions[position_key] = amount
        return positions
    
    def _get_bybit_margin_balance(self) -> Decimal:
        """Get available margin balance at Bybit."""
        usdt_bybit = self.portfolio['positions'].get('USDT_BYBIT', 0)
        return Decimal(str(usdt_bybit))


class ComplexScenarioRebalancer:
    """Advanced rebalancing for complex multi-venue leveraged scenarios."""
    
    def __init__(self, config: Dict[str, Any], portfolio: Dict[str, Any], transfer_manager: CrossVenueTransferManager):
        """Initialize complex scenario rebalancer."""
        self.config = config
        self.portfolio = portfolio
        self.transfer_manager = transfer_manager
        self.strategy_config = config.get('strategy', {})
        
        logger.info("ComplexScenarioRebalancer initialized")
    
    async def handle_complex_leveraged_rebalancing(
        self,
        health_assessment: Dict[str, Any],
        market_data
    ) -> List[Trade]:
        """Handle rebalancing for complex leveraged strategies with multiple debts."""
        try:
            trades = []
            
            aave_health = health_assessment.get('venue_breakdown', {}).get('aave', {})
            bybit_health = health_assessment.get('venue_breakdown', {}).get('bybit', {})
            
            # Check if this is a complex scenario (multiple debt types + restaking + basis trading)
            is_complex = self._is_complex_scenario(aave_health)
            
            if not is_complex:
                logger.info("Standard rebalancing scenario - using basic protocols")
                return trades
            
            logger.info("🏗️ Complex leveraged scenario detected - using advanced rebalancing")
            
            # Priority 1: Handle critical margin situations (Bybit)
            if bybit_health.get('health_status') in ['EMERGENCY', 'WARNING']:
                margin_trades = await self._handle_complex_margin_crisis(bybit_health, aave_health, market_data)
                trades.extend(margin_trades)
            
            # Priority 2: Optimize multi-debt LTV (AAVE)
            if aave_health.get('health_status') in ['EMERGENCY', 'WARNING', 'DRIFT']:
                ltv_trades = await self._handle_complex_ltv_optimization(aave_health, market_data)
                trades.extend(ltv_trades)
            
            # Priority 3: Cross-venue arbitrage with yield optimization
            arbitrage_trades = await self._handle_complex_arbitrage(health_assessment, market_data)
            trades.extend(arbitrage_trades)
            
            logger.info(f"🏗️ Complex rebalancing planned: {len(trades)} trades")
            return trades
            
        except Exception as e:
            logger.error(f"❌ Complex scenario rebalancing failed: {e}")
            raise
    
    def _is_complex_scenario(self, aave_health: Dict[str, Any]) -> bool:
        """Determine if this is a complex multi-debt scenario."""
        debt_breakdown = aave_health.get('debt_breakdown', {}).get('by_token', {})
        collateral_breakdown = aave_health.get('collateral_breakdown', {})
        
        # Complex if: multiple debt types + restaking + basis trading
        has_multiple_debts = len(debt_breakdown) > 1
        has_restaking = any(token in ['weETH', 'eETH'] for token in collateral_breakdown.keys())
        has_basis_trading = any('_PERP' in key for key in self.portfolio['positions'].keys())
        
        return has_multiple_debts and has_restaking and has_basis_trading
    
    async def _handle_complex_margin_crisis(
        self,
        bybit_health: Dict[str, Any],
        aave_health: Dict[str, Any],
        market_data
    ) -> List[Trade]:
        """Handle margin crisis in complex leveraged scenarios."""
        trades = []
        margin_shortfall = bybit_health.get('margin_shortfall_usd', 0)
        
        if margin_shortfall <= 0:
            return trades
        
        logger.warning(f"🚨 Complex margin crisis: ${margin_shortfall:,.2f} needed")
        
        # Strategy 1: Optimal debt reduction (reduce USDT debt for basis trade)
        usdt_debt = aave_health.get('debt_breakdown', {}).get('by_token', {}).get('USDT', {})
        if usdt_debt and margin_shortfall < usdt_debt.get('value_usd', 0) * 0.5:
            # Reduce USDT debt by repaying with Bybit gains
            logger.info("💡 Optimal: Reduce USDT debt to free margin capacity")
            
            # This would create debt repayment trades
            repayment_trade = Trade(
                trade_type="debt_repayment",
                venue="AAVE",
                token="USDT",
                amount=margin_shortfall,
                side="repay",
                purpose="Complex rebalancing: Reduce USDT debt for margin relief",
                expected_fee=self.config['fees']['gas_cost_usd']
            )
            trades.append(repayment_trade)
        
        # Strategy 2: Partial unstaking with yield optimization
        else:
            # Calculate optimal unstaking amount (minimize yield loss)
            optimal_unstaking = await self._calculate_optimal_unstaking_for_margin(
                margin_shortfall, aave_health, market_data
            )
            
            if optimal_unstaking > 0:
                unstaking_trades = await self.transfer_manager.execute_optimal_transfer(
                    "ETHERFI", "BYBIT", optimal_unstaking, market_data,
                    "Complex margin support: Yield-optimized unstaking"
                )
                trades.extend(unstaking_trades)
        
        return trades
    
    async def _handle_complex_ltv_optimization(
        self,
        aave_health: Dict[str, Any],
        market_data
    ) -> List[Trade]:
        """Handle LTV optimization for complex multi-debt scenarios."""
        trades = []
        
        current_ltv = aave_health.get('current_ltv', 0)
        target_ltv = aave_health.get('target_ltv', 0.5)
        debt_breakdown = aave_health.get('debt_breakdown', {}).get('by_token', {})
        
        logger.info(f"🏗️ Complex LTV optimization: {current_ltv:.2%} → {target_ltv:.2%}")
        
        # Strategy: Optimize debt composition for efficiency
        if current_ltv > target_ltv:
            # LTV too high - choose optimal debt reduction strategy
            
            # Analyze debt efficiency (yield/cost ratio)
            debt_efficiency = {}
            for token, debt_data in debt_breakdown.items():
                purpose = debt_data.get('purpose', '')
                annual_cost = debt_data.get('annual_cost_usd', 0)
                
                if purpose == 'LEVERAGED_STAKING':
                    # ETH debt for staking - calculate yield efficiency
                    staking_yield = self._estimate_staking_yield_from_debt(debt_data, market_data)
                    efficiency = staking_yield / max(annual_cost, 1)  # Yield/cost ratio
                elif purpose == 'BASIS_TRADE_LEVERAGE':
                    # USDT debt for basis trading - calculate funding efficiency  
                    funding_yield = self._estimate_funding_yield_from_debt(debt_data)
                    efficiency = funding_yield / max(annual_cost, 1)
                else:
                    efficiency = 0
                
                debt_efficiency[token] = {
                    'efficiency_ratio': efficiency,
                    'annual_cost': annual_cost,
                    'debt_value': debt_data['value_usd']
                }
            
            # Reduce least efficient debt first
            least_efficient = min(debt_efficiency.items(), key=lambda x: x[1]['efficiency_ratio'])
            token_to_reduce, efficiency_data = least_efficient
            
            reduction_amount = min(
                efficiency_data['debt_value'] * 0.3,  # Max 30% reduction
                (current_ltv - target_ltv) * aave_health.get('total_collateral_value', 0)
            )
            
            if reduction_amount > 1000:  # Minimum meaningful reduction
                repayment_trade = Trade(
                    trade_type="debt_repayment",
                    venue="AAVE", 
                    token=token_to_reduce,
                    amount=reduction_amount,
                    side="repay",
                    purpose=f"Complex LTV optimization: Reduce {efficiency_data['efficiency_ratio']:.2f} efficiency {token_to_reduce} debt",
                    expected_fee=self.config['fees']['gas_cost_usd']
                )
                trades.append(repayment_trade)
        
        return trades
    
    def _estimate_staking_yield_from_debt(self, debt_data: Dict[str, Any], market_data) -> float:
        """Estimate annual staking yield enabled by ETH debt."""
        debt_value = debt_data.get('value_usd', 0)
        restaking_apr = self.config.get('rates', {}).get('eeth_restaking_apr', 0.04)
        return debt_value * restaking_apr
    
    def _estimate_funding_yield_from_debt(self, debt_data: Dict[str, Any]) -> float:
        """Estimate annual funding yield from USDT debt used for basis trading."""
        debt_value = debt_data.get('value_usd', 0)
        funding_apr = self.config.get('rates', {}).get('bybit_eth_funding_apr', 0.08)
        return debt_value * funding_apr  # Simplified - assumes full utilization
    
    async def _calculate_optimal_unstaking_for_margin(
        self,
        margin_needed: float,
        aave_health: Dict[str, Any],
        market_data,
        bybit_health: Dict[str, Any] = None
    ) -> float:
        """Calculate optimal unstaking amount that minimizes yield loss."""
        
        # Get current staking positions
        weeth_balance = self.portfolio['positions'].get('weETH_ETHERFI', 0)
        if weeth_balance <= 0:
            return 0
        
        eth_price = await market_data.get_price('ETH')
        total_staking_value = weeth_balance * eth_price
        
        # Calculate yield loss per dollar unstaked
        restaking_apr = self.config.get('rates', {}).get('eeth_restaking_apr', 0.04)
        daily_yield_loss_rate = restaking_apr / 365.25
        
        # Calculate margin efficiency gain per dollar transferred
        current_margin_ratio = bybit_health.get('margin_ratio', 0.2) if bybit_health else 0.2
        margin_efficiency_gain = self._calculate_margin_efficiency_improvement(current_margin_ratio)
        
        # Optimal unstaking: minimize (yield_loss - margin_efficiency_gain)
        if margin_efficiency_gain > daily_yield_loss_rate * 30:  # 30-day breakeven
            # Efficient to unstake - transfer needed amount
            return min(margin_needed, total_staking_value * 0.3)  # Max 30% of staking
        else:
            # Inefficient to unstake - transfer minimum needed
            return min(margin_needed, total_staking_value * 0.1)  # Max 10% of staking
    
    def _calculate_margin_efficiency_improvement(self, current_margin_ratio: float) -> float:
        """Calculate efficiency improvement from better margin health."""
        if current_margin_ratio < 0.15:  # Critical margin
            return 0.02  # 2% annual efficiency improvement
        elif current_margin_ratio < 0.25:  # Warning margin
            return 0.01  # 1% annual efficiency improvement
        else:
            return 0.005  # 0.5% baseline improvement


class EmergencyRebalancingProtocols:
    """Emergency rebalancing protocols for critical situations."""
    
    def __init__(self, config: Dict[str, Any], portfolio: Dict[str, Any], transfer_manager: CrossVenueTransferManager):
        """Initialize emergency protocols."""
        self.config = config
        self.portfolio = portfolio
        self.transfer_manager = transfer_manager
        self.strategy_config = config.get('strategy', {})
        
        # Initialize complex scenario handler
        self.complex_rebalancer = ComplexScenarioRebalancer(config, portfolio, transfer_manager)
        
        logger.info("EmergencyRebalancingProtocols initialized with complex scenario support")
    
    async def execute_emergency_rebalancing(
        self,
        emergency_type: str,
        health_data: Dict[str, Any],
        market_data
    ) -> List[Trade]:
        """Execute emergency rebalancing protocols."""
        try:
            logger.warning(f"🚨 EMERGENCY REBALANCING: {emergency_type}")
            
            if emergency_type == "LTV_CRITICAL":
                return await self._emergency_ltv_reduction(health_data, market_data)
            elif emergency_type == "MARGIN_CRITICAL":
                return await self._emergency_margin_support(health_data, market_data)
            elif emergency_type == "CROSS_VENUE_CRITICAL":
                return await self._emergency_venue_rebalancing(health_data, market_data)
            else:
                raise ValueError(f"Unknown emergency type: {emergency_type}")
                
        except Exception as e:
            logger.error(f"❌ Emergency rebalancing failed: {e}")
            raise
    
    async def _emergency_ltv_reduction(
        self,
        health_data: Dict[str, Any],
        market_data
    ) -> List[Trade]:
        """Emergency LTV reduction to prevent liquidation."""
        trades = []
        
        aave_health = health_data['venue_breakdown']['aave']
        required_amount = aave_health.get('safety_distance', 0) * -1  # Negative distance = over limit
        
        logger.warning(f"🚨 LTV EMERGENCY: Need ${abs(required_amount):,.2f} collateral support")
        
        # Priority 1: Use all available USDT in wallet
        available_usdt = self.portfolio['positions'].get('USDT_WALLET', 0)
        if available_usdt > 0:
            trade = Trade(
                trade_type="lending_deposit",
                venue="AAVE",
                token="USDT",
                amount=available_usdt,
                side="deposit",
                purpose="EMERGENCY: LTV reduction - wallet USDT",
                expected_fee=self.config['fees']['gas_cost_usd']
            )
            trades.append(trade)
            required_amount -= available_usdt
            logger.warning(f"🔄 Emergency step 1: Deposit ${available_usdt:,.2f} USDT from wallet")
        
        # Priority 2: Emergency transfer from Bybit (if available)
        if required_amount > 0:
            bybit_available = await self.transfer_manager._calculate_max_safe_bybit_withdrawal(market_data)
            transfer_amount = min(required_amount, bybit_available)
            
            if transfer_amount > 1000:  # Minimum meaningful transfer
                bybit_trades = await self.transfer_manager.execute_optimal_transfer(
                    "BYBIT", "AAVE", transfer_amount, market_data, "EMERGENCY: LTV support"
                )
                trades.extend(bybit_trades)
                required_amount -= transfer_amount
                logger.warning(f"🔄 Emergency step 2: Transfer ${transfer_amount:,.2f} from Bybit")
        
        # Priority 3: Emergency unstaking from EtherFi
        if required_amount > 0:
            etherfi_available = await self.transfer_manager._calculate_available_etherfi_value(market_data)
            transfer_amount = min(required_amount, etherfi_available)
            
            if transfer_amount > 1000:
                etherfi_trades = await self.transfer_manager.execute_optimal_transfer(
                    "ETHERFI", "AAVE", transfer_amount, market_data, "EMERGENCY: LTV support"
                )
                trades.extend(etherfi_trades)
                logger.warning(f"🔄 Emergency step 3: Unstake ${transfer_amount:,.2f} from EtherFi")
        
        return trades
    
    async def _emergency_margin_support(
        self,
        health_data: Dict[str, Any],
        market_data
    ) -> List[Trade]:
        """Emergency margin support to prevent liquidation."""
        trades = []
        
        bybit_health = health_data['venue_breakdown']['bybit']
        margin_shortfall = bybit_health.get('margin_shortfall_usd', 0)
        
        logger.warning(f"🚨 MARGIN EMERGENCY: Need ${margin_shortfall:,.2f} margin support")
        
        # Priority 1: Fast AAVE withdrawal (if LTV allows)
        aave_available = await self.transfer_manager._calculate_max_safe_aave_withdrawal(market_data)
        if aave_available >= margin_shortfall:
            aave_trades = await self.transfer_manager.execute_optimal_transfer(
                "AAVE", "BYBIT", margin_shortfall, market_data, "EMERGENCY: Margin support"
            )
            trades.extend(aave_trades)
            logger.warning(f"🔄 Emergency margin: Transfer ${margin_shortfall:,.2f} from AAVE")
            return trades
        
        # Priority 2: Emergency unstaking from EtherFi
        etherfi_available = await self.transfer_manager._calculate_available_etherfi_value(market_data)
        if etherfi_available >= margin_shortfall:
            etherfi_trades = await self.transfer_manager.execute_optimal_transfer(
                "ETHERFI", "BYBIT", margin_shortfall, market_data, "EMERGENCY: Margin support"
            )
            trades.extend(etherfi_trades)
            logger.warning(f"🔄 Emergency margin: Unstake ${margin_shortfall:,.2f} from EtherFi")
            return trades
        
        # Priority 3: Reduce position size (last resort)
        logger.warning("🚨 LAST RESORT: Reducing perpetual positions to free margin")
        reduce_trade = Trade(
            trade_type="position_reduction",
            venue="BYBIT",
            token="ETH",
            amount=margin_shortfall / (await market_data.get_price('ETH')),
            side="reduce",
            purpose="EMERGENCY: Position reduction for margin",
            expected_fee=self.config['fees']['bybit_taker_fee_bps'] / 100  # Taker fee for emergency close
        )
        trades.append(reduce_trade)
        
        return trades
    
    async def _emergency_venue_rebalancing(
        self,
        health_data: Dict[str, Any],
        market_data
    ) -> List[Trade]:
        """Emergency rebalancing for critical cross-venue imbalances."""
        trades = []
        
        venue_pnl = health_data.get('cross_venue_pnl', {})
        max_imbalance = max(abs(pnl) for pnl in venue_pnl.values()) if venue_pnl else 0
        
        logger.warning(f"🚨 CROSS-VENUE EMERGENCY: ${max_imbalance:,.2f} imbalance")
        
        # Find largest excess and largest deficit
        excess_venue = max(venue_pnl.items(), key=lambda x: x[1])[0] if venue_pnl else None
        deficit_venue = min(venue_pnl.items(), key=lambda x: x[1])[0] if venue_pnl else None
        
        if excess_venue and deficit_venue and excess_venue != deficit_venue:
            excess_amount = venue_pnl[excess_venue]
            deficit_amount = abs(venue_pnl[deficit_venue])
            transfer_amount = min(excess_amount, deficit_amount)
            
            if transfer_amount > 5000:  # Minimum transfer
                emergency_trades = await self.transfer_manager.execute_optimal_transfer(
                    excess_venue, deficit_venue, transfer_amount, market_data,
                    "EMERGENCY: Cross-venue imbalance"
                )
                trades.extend(emergency_trades)
                logger.warning(f"🔄 Emergency rebalance: ${transfer_amount:,.2f} from {excess_venue} to {deficit_venue}")
        
        return trades


class RebalancingOptimizer:
    """Optimize rebalancing decisions for cost efficiency and yield preservation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize rebalancing optimizer."""
        self.config = config
        self.strategy_config = config.get('strategy', {})
        self.rates_config = config.get('rates', {})
        
    async def analyze_rebalancing_yield_impact(
        self,
        proposed_transfers: List[Dict[str, Any]],
        market_data
    ) -> Dict[str, Any]:
        """Analyze how rebalancing affects overall yield."""
        try:
            # Calculate current yield sources
            current_yield = await self._calculate_current_total_yield(market_data)
            
            # Project yield after rebalancing
            projected_yield = current_yield.copy()
            total_transfer_cost = 0.0
            
            for transfer in proposed_transfers:
                source = transfer['from_venue']
                amount = transfer['amount_usd']
                cost = transfer.get('estimated_cost', 0)
                total_transfer_cost += cost
                
                # Calculate yield impact
                if source == "ETHERFI":
                    # Lost staking yield
                    lost_yield_annual = amount * self.rates_config.get('eeth_restaking_apr', 0.04)
                    projected_yield['staking'] -= lost_yield_annual
                    
                elif source == "AAVE":
                    # Lost lending yield
                    lost_yield_annual = amount * self.rates_config.get('aave_usdt_supply_apr', 0.05)
                    projected_yield['lending'] -= lost_yield_annual
                
                # Add any gained yield at target venue
                target = transfer['to_venue']
                if target == "BYBIT":
                    # Improved margin efficiency might enable larger positions
                    efficiency_gain = self._calculate_margin_efficiency_gain(amount)
                    projected_yield['funding'] += efficiency_gain
            
            # Calculate net impact
            current_total = sum(current_yield.values())
            projected_total = sum(projected_yield.values())
            net_yield_impact = projected_total - current_total
            
            # Determine recommendation
            if net_yield_impact > total_transfer_cost:
                recommendation = 'EXECUTE'
                rationale = f"Net yield benefit: ${net_yield_impact:.2f} > cost: ${total_transfer_cost:.2f}"
            elif abs(net_yield_impact) < total_transfer_cost * 0.5:
                recommendation = 'NEUTRAL'
                rationale = f"Minimal yield impact vs cost"
            else:
                recommendation = 'DEFER'
                rationale = f"Yield cost: ${abs(net_yield_impact):.2f} > benefit"
            
            return {
                'current_yield_breakdown': current_yield,
                'projected_yield_breakdown': projected_yield,
                'net_yield_impact_usd': net_yield_impact,
                'total_transfer_cost_usd': total_transfer_cost,
                'net_benefit_usd': net_yield_impact - total_transfer_cost,
                'recommendation': recommendation,
                'rationale': rationale,
                'yield_impact_bps': (net_yield_impact / self.portfolio.get('initial_capital', 100000)) * 10000
            }
            
        except Exception as e:
            logger.error(f"Error analyzing yield impact: {e}")
            return {'recommendation': 'DEFER', 'error': str(e)}
    
    async def _calculate_current_total_yield(self, market_data) -> Dict[str, float]:
        """Calculate current annual yield from all sources."""
        yield_sources = {
            'lending': 0.0,
            'staking': 0.0,
            'funding': 0.0,
            'borrowing_cost': 0.0
        }
        
        try:
            # Lending yield (AAVE supply)
            usdt_aave = self.portfolio['positions'].get('USDT_AAVE', 0)
            if usdt_aave > 0:
                supply_rate = self.rates_config.get('aave_usdt_supply_apr', 0.05)
                yield_sources['lending'] = usdt_aave * supply_rate
            
            # Staking yield (EtherFi)
            weeth_balance = self.portfolio['positions'].get('weETH_ETHERFI', 0)
            if weeth_balance > 0:
                eth_price = await market_data.get_price('ETH')
                staking_rate = self.rates_config.get('eeth_restaking_apr', 0.04)
                yield_sources['staking'] = weeth_balance * eth_price * staking_rate
            
            # Funding yield (Bybit perpetuals)
            perp_positions = self._get_bybit_positions()
            for position_key, amount in perp_positions.items():
                if amount != 0:  # Short positions receive funding when positive
                    symbol = position_key.replace('_PERP', '')
                    base_token = symbol.replace('USDT', '')
                    price = await market_data.get_price(base_token)
                    position_value = abs(amount) * price
                    
                    funding_rate = self.rates_config.get('bybit_eth_funding_apr', 0.08)
                    if amount < 0:  # Short position
                        yield_sources['funding'] += position_value * funding_rate
            
            # Borrowing costs (AAVE debt)
            eth_debt = self.portfolio['positions'].get('ETH_DEBT_AAVE', 0)
            if eth_debt > 0:
                eth_price = await market_data.get_price('ETH')
                borrow_rate = self.rates_config.get('aave_eth_borrow_apr', 0.03)
                yield_sources['borrowing_cost'] = -(eth_debt * eth_price * borrow_rate)
            
        except Exception as e:
            logger.error(f"Error calculating current yield: {e}")
        
        return yield_sources
    
    def _calculate_margin_efficiency_gain(self, additional_margin: float) -> float:
        """Calculate yield gain from improved margin efficiency."""
        # Simplified: assume 1% yield improvement per $10k additional margin
        return (additional_margin / 10000) * 0.01 * self.portfolio.get('initial_capital', 100000)
    
    def _get_bybit_positions(self) -> Dict[str, float]:
        """Get Bybit positions for yield calculations."""
        positions = {}
        for position_key, amount in self.portfolio['positions'].items():
            if '_PERP' in position_key and amount != 0:
                positions[position_key] = amount
        return positions
