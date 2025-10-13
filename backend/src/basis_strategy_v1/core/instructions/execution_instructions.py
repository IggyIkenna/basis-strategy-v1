"""
Execution Instruction System

Two-component execution architecture:
1. WalletTransferInstruction - Simple wallet-to-venue transfers
2. SmartContractInstruction - Complex smart contract operations (AAVE, EtherFi, Flash loans)

Key Principles:
- Wallet transfers and smart contract operations are separate (can't be atomic together)
- Strategy Manager generates clear instruction blocks
- Execution interfaces are simple executors
- Atomic support for smart contract operations only
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

from ...core.logging.base_logging_interface import StandardizedLoggingMixin, LogLevel, EventType


class ExecutionMode(Enum):
    """Execution mode for instructions."""
    SEQUENTIAL = "sequential"
    ATOMIC = "atomic"


class InstructionType(Enum):
    """Types of execution instructions."""
    # Wallet transfers
    WALLET_TRANSFER = "WALLET_TRANSFER"
    
    # CEX trades
    SPOT_TRADE = "SPOT_TRADE"
    PERP_TRADE = "PERP_TRADE"
    
    # Smart contract operations
    AAVE_SUPPLY = "AAVE_SUPPLY"
    AAVE_BORROW = "AAVE_BORROW"
    AAVE_REPAY = "AAVE_REPAY"
    AAVE_WITHDRAW = "AAVE_WITHDRAW"
    STAKE = "STAKE"
    UNSTAKE = "UNSTAKE"
    SWAP = "SWAP"
    FLASH_BORROW = "FLASH_BORROW"
    FLASH_REPAY = "FLASH_REPAY"
    
    # Complex atomic operations
    ATOMIC_LEVERAGE_ENTRY = "ATOMIC_LEVERAGE_ENTRY"
    ATOMIC_LEVERAGE_EXIT = "ATOMIC_LEVERAGE_EXIT"


@dataclass
class WalletTransferInstruction(StandardizedLoggingMixin):
    """
    Instruction for simple wallet-to-venue transfers.
    
    These operations are always sequential and can't be bundled with smart contract operations.
    Examples: wallet → binance USDT, binance → wallet ETH
    """
    source_venue: str  # 'wallet', 'binance', 'bybit', 'okx'
    target_venue: str  # 'wallet', 'binance', 'bybit', 'okx'
    token: str  # 'USDT', 'ETH', 'BTC'
    amount: float
    purpose: str  # 'btc_basis_setup', 'margin_support', 'rebalancing'
    timestamp_group: str  # 'phase_1_funding', 'phase_3_return'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for interface compatibility."""
        return {
            'type': InstructionType.WALLET_TRANSFER.value,
            'source_venue': self.source_venue,
            'target_venue': self.target_venue,
            'token': self.token,
            'amount': self.amount,
            'purpose': self.purpose,
            'timestamp_group': self.timestamp_group
        }


@dataclass
class CEXTradeInstruction(StandardizedLoggingMixin):
    """
    Instruction for CEX spot and perpetual trades.
    
    These operations are executed via CEX execution interface.
    """
    venue: str  # 'binance', 'bybit', 'okx'
    pair: str  # 'BTC/USDT', 'ETH/USDT', 'BTCUSDT', 'ETHUSDT'
    side: str  # 'BUY', 'SELL'
    amount: float
    trade_type: str  # 'SPOT', 'PERP'
    execution_mode: str = ExecutionMode.SEQUENTIAL.value
    timestamp_group: str = 'default'
    price: Optional[float] = None  # For limit orders
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for interface compatibility."""
        return {
            'type': self.trade_type + '_TRADE',
            'venue': self.venue,
            'pair': self.pair,
            'side': self.side,
            'amount': float(self.amount),  # Ensure regular Python float, not numpy
            'trade_type': self.trade_type,
            'execution_mode': self.execution_mode,
            'timestamp_group': self.timestamp_group,
            'price': float(self.price) if self.price is not None else None
        }


@dataclass
class SmartContractInstruction(StandardizedLoggingMixin):
    """
    Instruction for smart contract operations (AAVE, EtherFi, Flash loans, DEX swaps).
    
    These operations can be atomic (single transaction) or sequential (multiple transactions).
    """
    operation: str  # 'AAVE_SUPPLY', 'STAKE', 'SWAP', 'FLASH_BORROW', etc.
    execution_mode: str  # 'atomic' or 'sequential'
    venue: str  # 'AAVE', 'ETHERFI', 'UNISWAP', 'INSTADAPP'
    token_in: Optional[str] = None
    token_out: Optional[str] = None
    amount: float = 0.0
    timestamp_group: str = 'default'
    atomic_group_id: Optional[str] = None  # Groups operations into single transaction
    
    # Additional parameters for specific operations
    ltv_target: Optional[float] = None  # For AAVE operations
    slippage_tolerance: Optional[float] = None  # For swaps
    flash_fee_bps: Optional[float] = None  # For flash loans
    gas_cost_type: Optional[str] = None  # 'ATOMIC_ENTRY', 'ATOMIC_EXIT', etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for interface compatibility."""
        return {
            'type': InstructionType(self.operation).value,
            'operation': self.operation,
            'execution_mode': self.execution_mode,
            'venue': self.venue,
            'token_in': self.token_in,
            'token_out': self.token_out,
            'amount': self.amount,
            'timestamp_group': self.timestamp_group,
            'atomic_group_id': self.atomic_group_id,
            'ltv_target': self.ltv_target,
            'slippage_tolerance': self.slippage_tolerance,
            'flash_fee_bps': self.flash_fee_bps,
            'gas_cost_type': self.gas_cost_type
        }


@dataclass
class InstructionBlock(StandardizedLoggingMixin):
    """
    A block of related instructions to be executed together.
    
    Supports both wallet transfers and smart contract operations,
    but they can't be mixed in atomic blocks.
    """
    block_type: str  # 'wallet_transfers', 'cex_trades', 'smart_contracts'
    execution_mode: str  # 'sequential' or 'atomic'
    timestamp_group: str
    instructions: List[Any]  # WalletTransferInstruction, CEXTradeInstruction, or SmartContractInstruction
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for interface compatibility."""
        return {
            'block_type': self.block_type,
            'execution_mode': self.execution_mode,
            'timestamp_group': self.timestamp_group,
            'instructions': [instr.to_dict() for instr in self.instructions]
        }


class InstructionGenerator(StandardizedLoggingMixin):
    """
    Helper class for generating instruction blocks for different strategies.
    
    Used by Strategy Manager to create clear, structured instruction sequences.
    """
    
    @staticmethod
    def create_btc_basis_setup_instructions(desired_positions: Dict) -> List[InstructionBlock]:
        """Generate instruction blocks for BTC basis initial setup."""
        blocks = []
        
        # Phase 1: Wallet transfers (sequential)
        wallet_transfers = []
        for transfer in desired_positions.get('transfers', []):
            wallet_transfers.append(WalletTransferInstruction(
                source_venue=transfer['source_venue'],
                target_venue=transfer['target_venue'],
                token=transfer['token'],
                amount=transfer['amount_usd'],
                purpose='btc_basis_setup',
                timestamp_group='phase_1_funding'
            ))
        
        if wallet_transfers:
            blocks.append(InstructionBlock(
                block_type='wallet_transfers',
                execution_mode=ExecutionMode.SEQUENTIAL.value,
                timestamp_group='phase_1_funding',
                instructions=wallet_transfers
            ))
        
        # Phase 2: Spot trades (sequential)
        spot_trades = []
        for spot_trade in desired_positions.get('spot_trades', []):
            spot_trades.append(CEXTradeInstruction(
                venue=spot_trade['venue'],
                pair='BTC/USDT',
                side=spot_trade['side'].upper(),
                amount=spot_trade['amount'],
                trade_type='SPOT',
                execution_mode=ExecutionMode.SEQUENTIAL.value,
                timestamp_group='phase_2_spot_trades'
            ))
        
        if spot_trades:
            blocks.append(InstructionBlock(
                block_type='cex_trades',
                execution_mode=ExecutionMode.SEQUENTIAL.value,
                timestamp_group='phase_2_spot_trades',
                instructions=spot_trades
            ))
        
        # Phase 3: Perp trades (sequential)
        perp_trades = []
        for perp_trade in desired_positions.get('perp_trades', []):
            perp_trades.append(CEXTradeInstruction(
                venue=perp_trade['venue'],
                pair='BTCUSDT',  # Perp format
                side=perp_trade['side'].upper(),
                amount=perp_trade['amount'],
                trade_type='PERP',
                execution_mode=ExecutionMode.SEQUENTIAL.value,
                timestamp_group='phase_3_perp_trades'
            ))
        
        if perp_trades:
            blocks.append(InstructionBlock(
                block_type='cex_trades',
                execution_mode=ExecutionMode.SEQUENTIAL.value,
                timestamp_group='phase_3_perp_trades',
                instructions=perp_trades
            ))
        
        return blocks
    
    @staticmethod
    def create_atomic_leverage_instructions(
        equity_usd: float,
        ltv_target: float,
        eth_price: float,
        weeth_price: float,
        flash_source: str = 'BALANCER'
    ) -> List[InstructionBlock]:
        """Generate instruction blocks for atomic leveraged staking."""
        
        # Calculate flash loan sizing (from atomic_recursive_loop.md)
        E = equity_usd
        λ = ltv_target
        F_usd = (λ / (1 - λ)) * E
        S_usd = E + F_usd
        B_usd = F_usd  # Must equal flash amount to repay
        
        # Convert to ETH/WETH units
        F_weth = F_usd / eth_price
        S_eth = S_usd / eth_price
        B_weth = B_usd / eth_price
        S_weeth = S_eth / weeth_price
        
        blocks = []
        
        # Atomic flash loan block (single transaction)
        atomic_operations = [
            SmartContractInstruction(
                operation='FLASH_BORROW',
                execution_mode=ExecutionMode.ATOMIC.value,
                venue='INSTADAPP',
                token_in=None,
                token_out='WETH',
                amount=F_weth,
                timestamp_group='atomic_leverage_entry',
                atomic_group_id='atomic_1',
                flash_fee_bps=0.0 if flash_source in ['BALANCER', 'MORPHO'] else 5.0,
                gas_cost_type='ATOMIC_ENTRY'
            ),
            SmartContractInstruction(
                operation='STAKE',
                execution_mode=ExecutionMode.ATOMIC.value,
                venue='ETHERFI',
                token_in='ETH',
                token_out='weETH',
                amount=S_eth,
                timestamp_group='atomic_leverage_entry',
                atomic_group_id='atomic_1'
            ),
            SmartContractInstruction(
                operation='AAVE_SUPPLY',
                execution_mode=ExecutionMode.ATOMIC.value,
                venue='AAVE',
                token_in='weETH',
                token_out='aWeETH',
                amount=S_weeth,
                timestamp_group='atomic_leverage_entry',
                atomic_group_id='atomic_1'
            ),
            SmartContractInstruction(
                operation='AAVE_BORROW',
                execution_mode=ExecutionMode.ATOMIC.value,
                venue='AAVE',
                token_in=None,
                token_out='WETH',
                amount=B_weth,
                timestamp_group='atomic_leverage_entry',
                atomic_group_id='atomic_1',
                ltv_target=λ
            ),
            SmartContractInstruction(
                operation='FLASH_REPAY',
                execution_mode=ExecutionMode.ATOMIC.value,
                venue='INSTADAPP',
                token_in='WETH',
                token_out=None,
                amount=F_weth,
                timestamp_group='atomic_leverage_entry',
                atomic_group_id='atomic_1'
            )
        ]
        
        blocks.append(InstructionBlock(
            block_type='smart_contracts',
            execution_mode=ExecutionMode.ATOMIC.value,
            timestamp_group='atomic_leverage_entry',
            instructions=atomic_operations
        ))
        
        return blocks
    
    @staticmethod
    def create_aave_supply_instructions(asset: str, amount: float) -> List[InstructionBlock]:
        """Generate instructions for simple AAVE supply (pure lending mode)."""
        blocks = []
        
        smart_contract_operations = [
            SmartContractInstruction(
                operation='AAVE_SUPPLY',
                execution_mode=ExecutionMode.SEQUENTIAL.value,
                venue='AAVE',
                token_in=asset,
                token_out=f'a{asset}',
                amount=amount,
                timestamp_group='aave_supply',
                gas_cost_type='COLLATERAL_SUPPLIED'
            )
        ]
        
        blocks.append(InstructionBlock(
            block_type='smart_contracts',
            execution_mode=ExecutionMode.SEQUENTIAL.value,
            timestamp_group='aave_supply',
            instructions=smart_contract_operations
        ))
        
        return blocks
