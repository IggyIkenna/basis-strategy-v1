"""
Unit tests for Execution Instructions.

Tests the execution instructions component in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from basis_strategy_v1.core.instructions.execution_instructions import (
    ExecutionMode,
    InstructionType,
    WalletTransferInstruction,
    CEXTradeInstruction,
    SmartContractInstruction,
    InstructionBlock,
    InstructionGenerator
)


class TestExecutionMode:
    """Test ExecutionMode enum."""
    
    def test_execution_mode_values(self):
        """Test execution mode enum values."""
        assert ExecutionMode.SEQUENTIAL.value == "sequential"
        assert ExecutionMode.ATOMIC.value == "atomic"
    
    def test_execution_mode_enumeration(self):
        """Test execution mode enumeration."""
        modes = list(ExecutionMode)
        assert len(modes) == 2
        assert ExecutionMode.SEQUENTIAL in modes
        assert ExecutionMode.ATOMIC in modes


class TestInstructionType:
    """Test InstructionType enum."""
    
    def test_instruction_type_values(self):
        """Test instruction type enum values."""
        assert InstructionType.WALLET_TRANSFER.value == "WALLET_TRANSFER"
        assert InstructionType.SPOT_TRADE.value == "SPOT_TRADE"
        assert InstructionType.PERP_TRADE.value == "PERP_TRADE"
        assert InstructionType.AAVE_SUPPLY.value == "AAVE_SUPPLY"
        assert InstructionType.AAVE_BORROW.value == "AAVE_BORROW"
        assert InstructionType.STAKE.value == "STAKE"
        assert InstructionType.UNSTAKE.value == "UNSTAKE"
        assert InstructionType.SWAP.value == "SWAP"
        assert InstructionType.ATOMIC_LEVERAGE_ENTRY.value == "ATOMIC_LEVERAGE_ENTRY"
        assert InstructionType.ATOMIC_LEVERAGE_EXIT.value == "ATOMIC_LEVERAGE_EXIT"
    
    def test_instruction_type_enumeration(self):
        """Test instruction type enumeration."""
        types = list(InstructionType)
        assert len(types) >= 10
        assert InstructionType.WALLET_TRANSFER in types
        assert InstructionType.SPOT_TRADE in types
        assert InstructionType.AAVE_SUPPLY in types


class TestWalletTransferInstruction:
    """Test WalletTransferInstruction dataclass."""
    
    def test_initialization(self):
        """Test wallet transfer instruction initialization."""
        instruction = WalletTransferInstruction(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0"),
            gas_limit=21000
        )
        
        assert instruction.instruction_id == "transfer_001"
        assert instruction.from_address == "0x123"
        assert instruction.to_address == "0x456"
        assert instruction.token == "USDT"
        assert instruction.amount == Decimal("1000.0")
        assert instruction.gas_limit == 21000
    
    def test_validation_success(self):
        """Test successful wallet transfer instruction validation."""
        instruction = WalletTransferInstruction(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0"),
            gas_limit=21000
        )
        
        errors = instruction.validate()
        assert len(errors) == 0
    
    def test_validation_missing_instruction_id(self):
        """Test validation with missing instruction ID."""
        instruction = WalletTransferInstruction(
            instruction_id="",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0"),
            gas_limit=21000
        )
        
        errors = instruction.validate()
        assert len(errors) > 0
        assert any('instruction_id is required' in error for error in errors)
    
    def test_validation_invalid_addresses(self):
        """Test validation with invalid addresses."""
        instruction = WalletTransferInstruction(
            instruction_id="transfer_001",
            from_address="invalid_address",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0"),
            gas_limit=21000
        )
        
        errors = instruction.validate()
        assert len(errors) > 0
        assert any('from_address must be valid' in error for error in errors)
    
    def test_validation_invalid_amount(self):
        """Test validation with invalid amount."""
        instruction = WalletTransferInstruction(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("0.0"),
            gas_limit=21000
        )
        
        errors = instruction.validate()
        assert len(errors) > 0
        assert any('amount must be positive' in error for error in errors)
    
    def test_validation_invalid_gas_limit(self):
        """Test validation with invalid gas limit."""
        instruction = WalletTransferInstruction(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0"),
            gas_limit=0
        )
        
        errors = instruction.validate()
        assert len(errors) > 0
        assert any('gas_limit must be positive' in error for error in errors)


class TestCEXTradeInstruction:
    """Test CEXTradeInstruction dataclass."""
    
    def test_initialization(self):
        """Test CEX trade instruction initialization."""
        instruction = CEXTradeInstruction(
            instruction_id="trade_001",
            venue="binance",
            instruction_type=InstructionType.SPOT_TRADE,
            symbol="BTCUSDT",
            side="buy",
            amount=Decimal("1.0"),
            price=Decimal("50000.0")
        )
        
        assert instruction.instruction_id == "trade_001"
        assert instruction.venue == "binance"
        assert instruction.instruction_type == InstructionType.SPOT_TRADE
        assert instruction.symbol == "BTCUSDT"
        assert instruction.side == "buy"
        assert instruction.amount == Decimal("1.0")
        assert instruction.price == Decimal("50000.0")
    
    def test_validation_success(self):
        """Test successful CEX trade instruction validation."""
        instruction = CEXTradeInstruction(
            instruction_id="trade_001",
            venue="binance",
            instruction_type=InstructionType.SPOT_TRADE,
            symbol="BTCUSDT",
            side="buy",
            amount=Decimal("1.0"),
            price=Decimal("50000.0")
        )
        
        errors = instruction.validate()
        assert len(errors) == 0
    
    def test_validation_missing_venue(self):
        """Test validation with missing venue."""
        instruction = CEXTradeInstruction(
            instruction_id="trade_001",
            venue="",
            instruction_type=InstructionType.SPOT_TRADE,
            symbol="BTCUSDT",
            side="buy",
            amount=Decimal("1.0"),
            price=Decimal("50000.0")
        )
        
        errors = instruction.validate()
        assert len(errors) > 0
        assert any('venue is required' in error for error in errors)
    
    def test_validation_invalid_side(self):
        """Test validation with invalid side."""
        instruction = CEXTradeInstruction(
            instruction_id="trade_001",
            venue="binance",
            instruction_type=InstructionType.SPOT_TRADE,
            symbol="BTCUSDT",
            side="invalid_side",
            amount=Decimal("1.0"),
            price=Decimal("50000.0")
        )
        
        errors = instruction.validate()
        assert len(errors) > 0
        assert any('side must be buy or sell' in error for error in errors)
    
    def test_validation_invalid_amount(self):
        """Test validation with invalid amount."""
        instruction = CEXTradeInstruction(
            instruction_id="trade_001",
            venue="binance",
            instruction_type=InstructionType.SPOT_TRADE,
            symbol="BTCUSDT",
            side="buy",
            amount=Decimal("0.0"),
            price=Decimal("50000.0")
        )
        
        errors = instruction.validate()
        assert len(errors) > 0
        assert any('amount must be positive' in error for error in errors)


class TestSmartContractInstruction:
    """Test SmartContractInstruction dataclass."""
    
    def test_initialization(self):
        """Test smart contract instruction initialization."""
        instruction = SmartContractInstruction(
            instruction_id="contract_001",
            instruction_type=InstructionType.AAVE_SUPPLY,
            contract_address="0x123",
            function_name="supply",
            parameters={"token": "USDT", "amount": "1000"},
            gas_limit=200000
        )
        
        assert instruction.instruction_id == "contract_001"
        assert instruction.instruction_type == InstructionType.AAVE_SUPPLY
        assert instruction.contract_address == "0x123"
        assert instruction.function_name == "supply"
        assert instruction.parameters == {"token": "USDT", "amount": "1000"}
        assert instruction.gas_limit == 200000
    
    def test_validation_success(self):
        """Test successful smart contract instruction validation."""
        instruction = SmartContractInstruction(
            instruction_id="contract_001",
            instruction_type=InstructionType.AAVE_SUPPLY,
            contract_address="0x123",
            function_name="supply",
            parameters={"token": "USDT", "amount": "1000"},
            gas_limit=200000
        )
        
        errors = instruction.validate()
        assert len(errors) == 0
    
    def test_validation_missing_contract_address(self):
        """Test validation with missing contract address."""
        instruction = SmartContractInstruction(
            instruction_id="contract_001",
            instruction_type=InstructionType.AAVE_SUPPLY,
            contract_address="",
            function_name="supply",
            parameters={"token": "USDT", "amount": "1000"},
            gas_limit=200000
        )
        
        errors = instruction.validate()
        assert len(errors) > 0
        assert any('contract_address is required' in error for error in errors)
    
    def test_validation_missing_function_name(self):
        """Test validation with missing function name."""
        instruction = SmartContractInstruction(
            instruction_id="contract_001",
            instruction_type=InstructionType.AAVE_SUPPLY,
            contract_address="0x123",
            function_name="",
            parameters={"token": "USDT", "amount": "1000"},
            gas_limit=200000
        )
        
        errors = instruction.validate()
        assert len(errors) > 0
        assert any('function_name is required' in error for error in errors)
    
    def test_validation_invalid_gas_limit(self):
        """Test validation with invalid gas limit."""
        instruction = SmartContractInstruction(
            instruction_id="contract_001",
            instruction_type=InstructionType.AAVE_SUPPLY,
            contract_address="0x123",
            function_name="supply",
            parameters={"token": "USDT", "amount": "1000"},
            gas_limit=0
        )
        
        errors = instruction.validate()
        assert len(errors) > 0
        assert any('gas_limit must be positive' in error for error in errors)


class TestInstructionBlock:
    """Test InstructionBlock dataclass."""
    
    def test_initialization(self):
        """Test instruction block initialization."""
        wallet_instruction = WalletTransferInstruction(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0"),
            gas_limit=21000
        )
        
        block = InstructionBlock(
            block_id="block_001",
            execution_mode=ExecutionMode.SEQUENTIAL,
            instructions=[wallet_instruction]
        )
        
        assert block.block_id == "block_001"
        assert block.execution_mode == ExecutionMode.SEQUENTIAL
        assert len(block.instructions) == 1
        assert block.instructions[0] == wallet_instruction
    
    def test_validation_success(self):
        """Test successful instruction block validation."""
        wallet_instruction = WalletTransferInstruction(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0"),
            gas_limit=21000
        )
        
        block = InstructionBlock(
            block_id="block_001",
            execution_mode=ExecutionMode.SEQUENTIAL,
            instructions=[wallet_instruction]
        )
        
        errors = block.validate()
        assert len(errors) == 0
    
    def test_validation_missing_block_id(self):
        """Test validation with missing block ID."""
        wallet_instruction = WalletTransferInstruction(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0"),
            gas_limit=21000
        )
        
        block = InstructionBlock(
            block_id="",
            execution_mode=ExecutionMode.SEQUENTIAL,
            instructions=[wallet_instruction]
        )
        
        errors = block.validate()
        assert len(errors) > 0
        assert any('block_id is required' in error for error in errors)
    
    def test_validation_empty_instructions(self):
        """Test validation with empty instructions."""
        block = InstructionBlock(
            block_id="block_001",
            execution_mode=ExecutionMode.SEQUENTIAL,
            instructions=[]
        )
        
        errors = block.validate()
        assert len(errors) > 0
        assert any('instructions cannot be empty' in error for error in errors)
    
    def test_validation_invalid_instructions(self):
        """Test validation with invalid instructions."""
        invalid_instruction = WalletTransferInstruction(
            instruction_id="",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0"),
            gas_limit=21000
        )
        
        block = InstructionBlock(
            block_id="block_001",
            execution_mode=ExecutionMode.SEQUENTIAL,
            instructions=[invalid_instruction]
        )
        
        errors = block.validate()
        assert len(errors) > 0
        assert any('instruction validation failed' in error for error in errors)


class TestInstructionGenerator:
    """Test InstructionGenerator class."""
    
    def test_initialization(self):
        """Test instruction generator initialization."""
        generator = InstructionGenerator()
        
        assert generator is not None
    
    def test_generate_wallet_transfer(self):
        """Test wallet transfer instruction generation."""
        generator = InstructionGenerator()
        
        instruction = generator.generate_wallet_transfer(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0")
        )
        
        assert instruction is not None
        assert instruction.instruction_id == "transfer_001"
        assert instruction.from_address == "0x123"
        assert instruction.to_address == "0x456"
        assert instruction.token == "USDT"
        assert instruction.amount == Decimal("1000.0")
    
    def test_generate_cex_trade(self):
        """Test CEX trade instruction generation."""
        generator = InstructionGenerator()
        
        instruction = generator.generate_cex_trade(
            instruction_id="trade_001",
            venue="binance",
            instruction_type=InstructionType.SPOT_TRADE,
            symbol="BTCUSDT",
            side="buy",
            amount=Decimal("1.0"),
            price=Decimal("50000.0")
        )
        
        assert instruction is not None
        assert instruction.instruction_id == "trade_001"
        assert instruction.venue == "binance"
        assert instruction.instruction_type == InstructionType.SPOT_TRADE
        assert instruction.symbol == "BTCUSDT"
        assert instruction.side == "buy"
        assert instruction.amount == Decimal("1.0")
        assert instruction.price == Decimal("50000.0")
    
    def test_generate_smart_contract_instruction(self):
        """Test smart contract instruction generation."""
        generator = InstructionGenerator()
        
        instruction = generator.generate_smart_contract_instruction(
            instruction_id="contract_001",
            instruction_type=InstructionType.AAVE_SUPPLY,
            contract_address="0x123",
            function_name="supply",
            parameters={"token": "USDT", "amount": "1000"}
        )
        
        assert instruction is not None
        assert instruction.instruction_id == "contract_001"
        assert instruction.instruction_type == InstructionType.AAVE_SUPPLY
        assert instruction.contract_address == "0x123"
        assert instruction.function_name == "supply"
        assert instruction.parameters == {"token": "USDT", "amount": "1000"}
    
    def test_generate_instruction_block(self):
        """Test instruction block generation."""
        generator = InstructionGenerator()
        
        wallet_instruction = generator.generate_wallet_transfer(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0")
        )
        
        block = generator.generate_instruction_block(
            block_id="block_001",
            execution_mode=ExecutionMode.SEQUENTIAL,
            instructions=[wallet_instruction]
        )
        
        assert block is not None
        assert block.block_id == "block_001"
        assert block.execution_mode == ExecutionMode.SEQUENTIAL
        assert len(block.instructions) == 1
        assert block.instructions[0] == wallet_instruction
    
    def test_generate_atomic_instruction_block(self):
        """Test atomic instruction block generation."""
        generator = InstructionGenerator()
        
        contract_instruction = generator.generate_smart_contract_instruction(
            instruction_id="contract_001",
            instruction_type=InstructionType.AAVE_SUPPLY,
            contract_address="0x123",
            function_name="supply",
            parameters={"token": "USDT", "amount": "1000"}
        )
        
        block = generator.generate_instruction_block(
            block_id="block_001",
            execution_mode=ExecutionMode.ATOMIC,
            instructions=[contract_instruction]
        )
        
        assert block is not None
        assert block.block_id == "block_001"
        assert block.execution_mode == ExecutionMode.ATOMIC
        assert len(block.instructions) == 1
        assert block.instructions[0] == contract_instruction
    
    def test_generate_instruction_block_with_multiple_instructions(self):
        """Test instruction block generation with multiple instructions."""
        generator = InstructionGenerator()
        
        wallet_instruction = generator.generate_wallet_transfer(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0")
        )
        
        cex_instruction = generator.generate_cex_trade(
            instruction_id="trade_001",
            venue="binance",
            instruction_type=InstructionType.SPOT_TRADE,
            symbol="BTCUSDT",
            side="buy",
            amount=Decimal("1.0"),
            price=Decimal("50000.0")
        )
        
        block = generator.generate_instruction_block(
            block_id="block_001",
            execution_mode=ExecutionMode.SEQUENTIAL,
            instructions=[wallet_instruction, cex_instruction]
        )
        
        assert block is not None
        assert block.block_id == "block_001"
        assert block.execution_mode == ExecutionMode.SEQUENTIAL
        assert len(block.instructions) == 2
        assert block.instructions[0] == wallet_instruction
        assert block.instructions[1] == cex_instruction
    
    def test_generate_instruction_block_validation(self):
        """Test instruction block generation with validation."""
        generator = InstructionGenerator()
        
        # Create invalid instruction
        invalid_instruction = generator.generate_wallet_transfer(
            instruction_id="",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0")
        )
        
        with pytest.raises(ValueError):
            generator.generate_instruction_block(
                block_id="block_001",
                execution_mode=ExecutionMode.SEQUENTIAL,
                instructions=[invalid_instruction]
            )
    
    def test_generate_instruction_block_empty_instructions(self):
        """Test instruction block generation with empty instructions."""
        generator = InstructionGenerator()
        
        with pytest.raises(ValueError):
            generator.generate_instruction_block(
                block_id="block_001",
                execution_mode=ExecutionMode.SEQUENTIAL,
                instructions=[]
            )
    
    def test_generate_instruction_block_missing_block_id(self):
        """Test instruction block generation with missing block ID."""
        generator = InstructionGenerator()
        
        wallet_instruction = generator.generate_wallet_transfer(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0")
        )
        
        with pytest.raises(ValueError):
            generator.generate_instruction_block(
                block_id="",
                execution_mode=ExecutionMode.SEQUENTIAL,
                instructions=[wallet_instruction]
            )
    
    def test_generate_instruction_block_invalid_execution_mode(self):
        """Test instruction block generation with invalid execution mode."""
        generator = InstructionGenerator()
        
        wallet_instruction = generator.generate_wallet_transfer(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0")
        )
        
        with pytest.raises(ValueError):
            generator.generate_instruction_block(
                block_id="block_001",
                execution_mode="invalid_mode",
                instructions=[wallet_instruction]
            )
    
    def test_generate_instruction_block_atomic_with_wallet_transfer(self):
        """Test atomic instruction block generation with wallet transfer (should fail)."""
        generator = InstructionGenerator()
        
        wallet_instruction = generator.generate_wallet_transfer(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0")
        )
        
        with pytest.raises(ValueError):
            generator.generate_instruction_block(
                block_id="block_001",
                execution_mode=ExecutionMode.ATOMIC,
                instructions=[wallet_instruction]
            )
    
    def test_generate_instruction_block_sequential_with_smart_contract(self):
        """Test sequential instruction block generation with smart contract instruction."""
        generator = InstructionGenerator()
        
        contract_instruction = generator.generate_smart_contract_instruction(
            instruction_id="contract_001",
            instruction_type=InstructionType.AAVE_SUPPLY,
            contract_address="0x123",
            function_name="supply",
            parameters={"token": "USDT", "amount": "1000"}
        )
        
        block = generator.generate_instruction_block(
            block_id="block_001",
            execution_mode=ExecutionMode.SEQUENTIAL,
            instructions=[contract_instruction]
        )
        
        assert block is not None
        assert block.block_id == "block_001"
        assert block.execution_mode == ExecutionMode.SEQUENTIAL
        assert len(block.instructions) == 1
        assert block.instructions[0] == contract_instruction
    
    def test_generate_instruction_block_mixed_instructions_sequential(self):
        """Test sequential instruction block generation with mixed instruction types."""
        generator = InstructionGenerator()
        
        wallet_instruction = generator.generate_wallet_transfer(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0")
        )
        
        cex_instruction = generator.generate_cex_trade(
            instruction_id="trade_001",
            venue="binance",
            instruction_type=InstructionType.SPOT_TRADE,
            symbol="BTCUSDT",
            side="buy",
            amount=Decimal("1.0"),
            price=Decimal("50000.0")
        )
        
        contract_instruction = generator.generate_smart_contract_instruction(
            instruction_id="contract_001",
            instruction_type=InstructionType.AAVE_SUPPLY,
            contract_address="0x123",
            function_name="supply",
            parameters={"token": "USDT", "amount": "1000"}
        )
        
        block = generator.generate_instruction_block(
            block_id="block_001",
            execution_mode=ExecutionMode.SEQUENTIAL,
            instructions=[wallet_instruction, cex_instruction, contract_instruction]
        )
        
        assert block is not None
        assert block.block_id == "block_001"
        assert block.execution_mode == ExecutionMode.SEQUENTIAL
        assert len(block.instructions) == 3
        assert block.instructions[0] == wallet_instruction
        assert block.instructions[1] == cex_instruction
        assert block.instructions[2] == contract_instruction
    
    def test_generate_instruction_block_mixed_instructions_atomic(self):
        """Test atomic instruction block generation with mixed instruction types (should fail)."""
        generator = InstructionGenerator()
        
        wallet_instruction = generator.generate_wallet_transfer(
            instruction_id="transfer_001",
            from_address="0x123",
            to_address="0x456",
            token="USDT",
            amount=Decimal("1000.0")
        )
        
        contract_instruction = generator.generate_smart_contract_instruction(
            instruction_id="contract_001",
            instruction_type=InstructionType.AAVE_SUPPLY,
            contract_address="0x123",
            function_name="supply",
            parameters={"token": "USDT", "amount": "1000"}
        )
        
        with pytest.raises(ValueError):
            generator.generate_instruction_block(
                block_id="block_001",
                execution_mode=ExecutionMode.ATOMIC,
                instructions=[wallet_instruction, contract_instruction]
            )
    
    def test_generate_instruction_block_atomic_with_multiple_smart_contracts(self):
        """Test atomic instruction block generation with multiple smart contract instructions."""
        generator = InstructionGenerator()
        
        supply_instruction = generator.generate_smart_contract_instruction(
            instruction_id="supply_001",
            instruction_type=InstructionType.AAVE_SUPPLY,
            contract_address="0x123",
            function_name="supply",
            parameters={"token": "USDT", "amount": "1000"}
        )
        
        borrow_instruction = generator.generate_smart_contract_instruction(
            instruction_id="borrow_001",
            instruction_type=InstructionType.AAVE_BORROW,
            contract_address="0x123",
            function_name="borrow",
            parameters={"token": "USDT", "amount": "500"}
        )
        
        block = generator.generate_instruction_block(
            block_id="block_001",
            execution_mode=ExecutionMode.ATOMIC,
            instructions=[supply_instruction, borrow_instruction]
        )
        
        assert block is not None
        assert block.block_id == "block_001"
        assert block.execution_mode == ExecutionMode.ATOMIC
        assert len(block.instructions) == 2
        assert block.instructions[0] == supply_instruction
        assert block.instructions[1] == borrow_instruction
