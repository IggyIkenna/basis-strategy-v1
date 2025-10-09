"""
Event Logger Component

TODO-REFACTOR: TIGHT LOOP ARCHITECTURE VIOLATION - 10_tight_loop_architecture_requirements.md
ISSUE: This component may violate tight loop architecture requirements:

1. TIGHT LOOP ARCHITECTURE REQUIREMENTS:
   - Components must follow strict tight loop sequence
   - Proper event processing order
   - No state clearing between iterations
   - Consistent processing flow

2. REQUIRED VERIFICATION:
   - Verify tight loop sequence is enforced
   - Check for proper event processing order
   - Ensure no state clearing violations
   - Validate consistent processing flow

3. CANONICAL SOURCE:
   - .cursor/tasks/10_tight_loop_architecture_requirements.md
   - Tight loop sequence must be enforced

Detailed audit-grade event tracking with balance snapshots.
Logs all events with complete context for audit trail.

Key Principles:
- Global order: Every event gets unique sequence number
- Balance snapshots: Include position snapshot in every event (optional)
- Atomic bundles: Support wrapper + detail events (flash loans, leverage loops)
- Hourly timestamps: All events on the hour in backtest
- Future-proof: Optional fields for live trading (tx_hash, confirmation, etc.)
"""

from typing import Dict, List, Optional, Any
import redis
import json
import logging
import asyncio
import csv
from datetime import datetime
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

# Error codes for Event Logger
ERROR_CODES = {
    'EVENT-001': 'Event serialization failed',
    'EVENT-002': 'Redis publish failed',
    'EVENT-003': 'Event order conflict (duplicate order)',
    'EVENT-004': 'Balance snapshot serialization failed',
    'EVENT-005': 'Event storage limit exceeded'
}


class EventLogger:
    """Audit-grade event logging."""
    
    def __init__(self, execution_mode: str = 'backtest', include_balance_snapshots: bool = True):
        self.execution_mode = execution_mode
        self.include_balance_snapshots = include_balance_snapshots
        self.events = []
        self.global_order = 0  # Auto-increment for every event
        self._order_lock = asyncio.Lock()  # Thread-safe order assignment
        
        # Redis for publishing
        self.redis = None
        if execution_mode == 'live':
            try:
                self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                # Test connection
                self.redis.ping()
                logger.info("Redis connection established for Event Logger")
            except Exception as e:
                logger.warning(f"Redis not available for Event Logger: {e}")
                self.redis = None
        
        logger.info(f"Event Logger initialized in {execution_mode} mode")
    
    async def log_event(
        self,
        timestamp: pd.Timestamp,
        event_type: str,
        venue: str,
        token: str = None,
        amount: float = None,
        position_snapshot: Optional[Dict] = None,
        **event_data
    ) -> int:
        """
        Log an event with automatic order assignment.
        
        Args:
            timestamp: Event time (on the hour in backtest)
            event_type: Type of event
            venue: Where it happened
            token: Token involved
            amount: Primary amount
            position_snapshot: Current position state (from Position Monitor)
            **event_data: Additional event-specific data
        
        Returns:
            Event order number (for correlation)
        """
        async with self._order_lock:
            self.global_order += 1
            
            event = {
                'timestamp': timestamp,
                'order': self.global_order,
                'event_type': event_type,
                'venue': venue,
                'token': token,
                'amount': amount,
                'status': 'completed' if self.execution_mode == 'backtest' else 'pending',
                **event_data
            }
            
            # Add balance snapshot if provided and enabled
            if self.include_balance_snapshots and position_snapshot:
                # Include full Position Monitor output for complete audit trail
                event['wallet_balance_after'] = position_snapshot  # Full Position Monitor output
                event['cex_balance_after'] = position_snapshot.get('cex_accounts')
                event['aave_position_after'] = {
                    'wallet': position_snapshot.get('wallet'),
                    'perp_positions': position_snapshot.get('perp_positions')
                }
                # Could add more derived data (AAVE positions, etc.)
            
            self.events.append(event)
            
            # Publish to Redis
            if self.redis:
                await self._publish_event(event)
            
            logger.debug(f"Event logged: {event_type} at {venue} (order: {self.global_order})")
            return self.global_order
    
    async def _publish_event(self, event: Dict):
        """Publish event to Redis."""
        try:
            # Publish to events:logged channel
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.redis.publish,
                'events:logged',
                json.dumps({
                    'order': event['order'],
                    'event_type': event['event_type'],
                    'timestamp': event['timestamp'].isoformat() if hasattr(event['timestamp'], 'isoformat') else str(event['timestamp']),
                    'venue': event['venue']
                })
            )
            
            # If it's an atomic transaction, also publish to atomic_bundle channel
            if event['event_type'] == 'ATOMIC_TRANSACTION':
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.redis.publish,
                    'events:atomic_bundle',
                    json.dumps({
                        'wrapper_order': event['order'],
                        'bundle_name': event.get('bundle_name', 'UNKNOWN'),
                        'detail_orders': event.get('detail_orders', []),
                        'timestamp': event['timestamp'].isoformat() if hasattr(event['timestamp'], 'isoformat') else str(event['timestamp'])
                    })
                )
                
        except Exception as e:
            logger.error(f"Error publishing event to Redis: {e}")
    
    # Typed Event Logging Methods
    
    async def log_gas_fee(
        self,
        timestamp: pd.Timestamp,
        gas_cost_eth: float,
        gas_cost_usd: float,
        operation_type: str,
        gas_units: int,
        gas_price_gwei: float,
        position_snapshot: Optional[Dict] = None
    ) -> int:
        """Log gas fee payment."""
        return await self.log_event(
            timestamp=timestamp,
            event_type='GAS_FEE_PAID',
            venue='ETHEREUM',
            token='ETH',
            amount=gas_cost_eth,
            gas_cost_eth=gas_cost_eth,
            gas_cost_usd=gas_cost_usd,
            gas_units=gas_units,
            gas_price_gwei=gas_price_gwei,
            fee_type=operation_type,
            purpose=f"Gas fee for {operation_type}",
            transaction_type='GAS_FEE',
            position_snapshot=position_snapshot
        )
    
    async def log_stake(
        self,
        timestamp: pd.Timestamp,
        venue: str,  # 'ETHERFI' or 'LIDO'
        eth_in: float,
        lst_out: float,
        oracle_price: float,
        iteration: Optional[int] = None,
        position_snapshot: Optional[Dict] = None
    ) -> int:
        """Log staking operation."""
        return await self.log_event(
            timestamp=timestamp,
            event_type='STAKE_DEPOSIT',
            venue=venue,
            token='ETH',
            amount=eth_in,
            input_token='ETH',
            output_token='weETH' if venue == 'ETHERFI' else 'wstETH',
            amount_out=lst_out,
            oracle_price=oracle_price,
            iteration=iteration,
            purpose=f"Stake {eth_in} ETH to {venue}",
            transaction_type='STAKE',
            position_snapshot=position_snapshot
        )
    
    async def log_aave_supply(
        self,
        timestamp: pd.Timestamp,
        token: str,
        amount_supplied: float,
        atoken_received: float,
        liquidity_index: float,
        iteration: Optional[int] = None,
        position_snapshot: Optional[Dict] = None
    ) -> int:
        """
        Log AAVE collateral supply.
        
        CRITICAL: aToken amount depends on liquidity index!
        """
        return await self.log_event(
            timestamp=timestamp,
            event_type='COLLATERAL_SUPPLIED',
            venue='AAVE',
            token=token,
            amount=amount_supplied,
            atoken_received=atoken_received,
            liquidity_index=liquidity_index,
            conversion_note=f'{amount_supplied} {token} → {atoken_received} a{token} (index={liquidity_index})',
            iteration=iteration,
            purpose=f"Supply {amount_supplied} {token} to AAVE",
            transaction_type='AAVE_SUPPLY',
            position_snapshot=position_snapshot
        )
    
    async def log_aave_borrow(
        self,
        timestamp: pd.Timestamp,
        token: str,
        amount_borrowed: float,
        debt_token_received: float,
        liquidity_index: float,
        iteration: Optional[int] = None,
        position_snapshot: Optional[Dict] = None
    ) -> int:
        """Log AAVE borrowing operation."""
        return await self.log_event(
            timestamp=timestamp,
            event_type='LOAN_CREATED',
            venue='AAVE',
            token=token,
            amount=amount_borrowed,
            debt_token_received=debt_token_received,
            liquidity_index=liquidity_index,
            conversion_note=f'{amount_borrowed} {token} borrowed → {debt_token_received} debt token (index={liquidity_index})',
            iteration=iteration,
            purpose=f"Borrow {amount_borrowed} {token} from AAVE",
            transaction_type='AAVE_BORROW',
            position_snapshot=position_snapshot
        )
    
    async def log_atomic_transaction(
        self,
        timestamp: pd.Timestamp,
        bundle_name: str,
        detail_events: List[Dict],
        net_result: Dict,
        position_snapshot: Optional[Dict] = None
    ) -> List[int]:
        """
        Log atomic transaction (flash loan bundle).
        
        Creates wrapper event + detail events.
        
        Args:
            bundle_name: 'ATOMIC_LEVERAGE_ENTRY', 'ATOMIC_DELEVERAGE', etc.
            detail_events: List of individual operations
            net_result: Summary of net effect
        
        Returns:
            List of event order numbers [wrapper_order, detail_orders...]
        """
        # Log wrapper event
        wrapper_order = await self.log_event(
            timestamp=timestamp,
            event_type='ATOMIC_TRANSACTION',
            venue='INSTADAPP',
            token='COMPOSITE',
            amount=1,
            bundle_name=bundle_name,
            net_result=net_result,
            detail_count=len(detail_events),
            purpose=f"Atomic transaction: {bundle_name}",
            transaction_type='ATOMIC_BUNDLE',
            position_snapshot=position_snapshot
        )
        
        # Log detail events
        detail_orders = []
        for detail in detail_events:
            detail_order = await self.log_event(
                timestamp=timestamp,
                parent_event=wrapper_order,
                **detail
            )
            detail_orders.append(detail_order)
        
        # Update wrapper event with detail orders
        if self.events:
            wrapper_event = self.events[wrapper_order - 1]  # Order is 1-indexed
            wrapper_event['detail_orders'] = detail_orders
        
        return [wrapper_order] + detail_orders
    
    async def log_perp_trade(
        self,
        timestamp: pd.Timestamp,
        venue: str,
        instrument: str,
        side: str,
        size_eth: float,
        entry_price: float,
        notional_usd: float,
        execution_cost_usd: float,
        position_snapshot: Optional[Dict] = None
    ) -> int:
        """Log perpetual futures trade."""
        return await self.log_event(
            timestamp=timestamp,
            event_type='TRADE_EXECUTED',
            venue=venue.upper(),
            token='ETH',
            amount=abs(size_eth),
            side=side,  # 'SHORT' or 'LONG'
            instrument=instrument,
            entry_price=entry_price,
            notional_usd=notional_usd,
            execution_cost_usd=execution_cost_usd,
            purpose=f"{side} {abs(size_eth)} ETH on {venue} at {entry_price}",
            transaction_type='PERP_TRADE',
            position_snapshot=position_snapshot
        )
    
    async def log_funding_payment(
        self,
        timestamp: pd.Timestamp,
        venue: str,
        funding_rate: float,
        notional_usd: float,
        pnl_usd: float,
        position_snapshot: Optional[Dict] = None
    ) -> int:
        """Log funding rate payment (8-hourly)."""
        pnl_type = 'RECEIVED' if pnl_usd > 0 else 'PAID'
        
        return await self.log_event(
            timestamp=timestamp,
            event_type='FUNDING_PAYMENT',
            venue=venue.upper(),
            token='USDT',
            amount=abs(pnl_usd),
            funding_rate=funding_rate,
            notional_usd=notional_usd,
            pnl_usd=pnl_usd,
            pnl_type=pnl_type,
            purpose=f"Funding payment: {pnl_type} {abs(pnl_usd)} USDT",
            transaction_type='FUNDING',
            position_snapshot=position_snapshot
        )
    
    async def log_venue_transfer(
        self,
        timestamp: pd.Timestamp,
        from_venue: str,
        to_venue: str,
        token: str,
        amount: float,
        purpose: str = "Transfer between venues",
        position_snapshot: Optional[Dict] = None
    ) -> int:
        """Log transfer between venues (wallet ↔ CEX)."""
        return await self.log_event(
            timestamp=timestamp,
            event_type='VENUE_TRANSFER',
            venue=f"{from_venue}→{to_venue}",
            token=token,
            amount=amount,
            from_venue=from_venue,
            to_venue=to_venue,
            purpose=purpose,
            transaction_type='TRANSFER',
            position_snapshot=position_snapshot
        )
    
    async def log_rebalance(
        self,
        timestamp: pd.Timestamp,
        rebalance_type: str,
        delta_exposure: float,
        actions_taken: List[str],
        position_snapshot: Optional[Dict] = None
    ) -> int:
        """Log rebalancing operation."""
        return await self.log_event(
            timestamp=timestamp,
            event_type='REBALANCE_EXECUTED',
            venue='STRATEGY',
            token='COMPOSITE',
            amount=abs(delta_exposure),
            rebalance_type=rebalance_type,
            delta_exposure=delta_exposure,
            actions_taken=actions_taken,
            purpose=f"Rebalance: {rebalance_type} (delta: {delta_exposure})",
            transaction_type='REBALANCE',
            position_snapshot=position_snapshot
        )
    
    async def log_risk_alert(
        self,
        timestamp: pd.Timestamp,
        risk_type: str,
        current_value: float,
        threshold: float,
        severity: str = 'WARNING',
        position_snapshot: Optional[Dict] = None
    ) -> int:
        """Log risk threshold breach."""
        return await self.log_event(
            timestamp=timestamp,
            event_type='RISK_ALERT',
            venue='RISK_MONITOR',
            token='COMPOSITE',
            amount=current_value,
            risk_type=risk_type,
            current_value=current_value,
            threshold=threshold,
            severity=severity,
            purpose=f"Risk alert: {risk_type} = {current_value} (threshold: {threshold})",
            transaction_type='RISK_ALERT',
            position_snapshot=position_snapshot
        )
    
    async def log_seasonal_reward_distribution(
        self,
        timestamp: pd.Timestamp,
        reward_type: str,
        amount: float,
        weeth_balance_avg: float,
        period_start: pd.Timestamp,
        period_end: pd.Timestamp,
        position_snapshot: Optional[Dict] = None
    ) -> int:
        """
        Log seasonal reward distribution as discrete event.
        
        Data source: data/protocol_data/staking/restaking_final/etherfi_seasonal_rewards_2024-01-01_2025-09-18.csv
        
        Columns used:
        - period_start, period_end, payout_date
        - eigen_per_eeth_weekly (for EIGEN rewards)
        - ethfi_per_eeth (for ETHFI rewards)
        
        Calculation:
        - reward_amount = distribution_rate × avg_weeth_balance
        - Applied on exact payout_date
        
        Args:
            timestamp: Payout date (from seasonal_rewards.csv)
            reward_type: 'EIGEN' or 'ETHFI'
            amount: Reward amount in tokens
            weeth_balance_avg: Average weETH balance during period
            period_start: Reward period start
            period_end: Reward period end
            position_snapshot: Current position snapshot (optional)
            
        Returns:
            Event order number
        """
        return await self.log_event(
            timestamp=timestamp,
            event_type='SEASONAL_REWARD_DISTRIBUTION',
            venue='ETHERFI_KING_PROTOCOL',
            token=reward_type,
            amount=amount,
            position_snapshot=position_snapshot,
            details={
                'reward_type': reward_type,
                'amount': amount,
                'weeth_balance_avg': weeth_balance_avg,
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
                'distribution_mechanism': 'king_protocol_weekly',
                'data_source': 'etherfi_seasonal_rewards'
            },
            severity='INFO',
            purpose=f"Seasonal {reward_type} reward distribution: {amount} tokens",
            transaction_type='REWARD_DISTRIBUTION'
        )
    
    async def update_event(self, order: int, updates: Dict):
        """Update an existing event (for live mode status updates)."""
        if order < 1 or order > len(self.events):
            logger.warning(f"Invalid event order for update: {order}")
            return
        
        event = self.events[order - 1]  # Order is 1-indexed
        event.update(updates)
        
        logger.debug(f"Event {order} updated: {updates}")
    
    def get_events_by_type(self, event_type: str) -> List[Dict]:
        """Get all events of a specific type."""
        return [event for event in self.events if event['event_type'] == event_type]
    
    def get_events_by_venue(self, venue: str) -> List[Dict]:
        """Get all events for a specific venue."""
        return [event for event in self.events if event['venue'] == venue]
    
    def get_events_by_order_range(self, start_order: int, end_order: int) -> List[Dict]:
        """Get events within an order range."""
        return [event for event in self.events if start_order <= event['order'] <= end_order]
    
    def get_all_events(self) -> List[Dict]:
        """Get all logged events."""
        return self.events.copy()
    
    def export_to_csv(self, filepath: str = None) -> str:
        """Export all events to CSV file."""
        if not filepath:
            filepath = f"event_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if not self.events:
            logger.warning("No events to export")
            return filepath
        
        # Get all unique field names across all events
        all_fields = set()
        for event in self.events:
            all_fields.update(event.keys())
        
        # Sort fields for consistent column order
        fieldnames = sorted(list(all_fields))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for event in self.events:
                # Convert complex objects to strings for CSV
                row = {}
                for field in fieldnames:
                    value = event.get(field)
                    if isinstance(value, (dict, list)):
                        row[field] = json.dumps(value)
                    elif hasattr(value, 'isoformat'):  # pandas Timestamp
                        row[field] = value.isoformat()
                    else:
                        row[field] = value
                writer.writerow(row)
        
        logger.info(f"Exported {len(self.events)} events to {filepath}")
        return filepath
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics of logged events."""
        if not self.events:
            return {}
        
        event_types = {}
        venues = {}
        total_amount = 0
        
        for event in self.events:
            # Count event types
            event_type = event['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Count venues
            venue = event['venue']
            venues[venue] = venues.get(venue, 0) + 1
            
            # Sum amounts (where applicable)
            if event.get('amount') and isinstance(event['amount'], (int, float)):
                total_amount += event['amount']
        
        return {
            'total_events': len(self.events),
            'event_types': event_types,
            'venues': venues,
            'total_amount': total_amount,
            'first_event_order': self.events[0]['order'] if self.events else None,
            'last_event_order': self.events[-1]['order'] if self.events else None
        }


# Convenience function for creating Event Logger
def create_event_logger(execution_mode: str = 'backtest', include_balance_snapshots: bool = True) -> EventLogger:
    """Create a new Event Logger instance."""
    return EventLogger(execution_mode=execution_mode, include_balance_snapshots=include_balance_snapshots)