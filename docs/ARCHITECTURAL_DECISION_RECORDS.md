# Architectural Decision Records (ADRs)

**Status**: Historical Record - Referenced by REFERENCE_ARCHITECTURE_CANONICAL.md
**Updated**: October 13, 2025
**Purpose**: Complete historical record of all architectural decisions

## Overview
This document contains the full details of all architectural decisions made for the basis-strategy-v1 platform.

**Canonical Source**: REFERENCE_ARCHITECTURE_CANONICAL.md contains principle summaries and references these detailed ADRs.

---

## ADR-001: Position Monitor Live Integration Architecture

**Date**: December 2024  
**Status**: Accepted  
**Context**: Position Monitor currently only simulates positions in backtest mode. Live trading requires real position data from venue APIs.

**Decision**: Extend Execution Interface Factory to create position monitoring interfaces rather than creating a separate Position Interface Factory.

**Rationale**: 
- Reuses existing venue configuration and credentials
- Maintains consistency with execution interfaces
- Reduces code duplication
- Simplifies venue management

**Consequences**:
- Execution Interface Factory becomes responsible for both execution and position monitoring
- Position Monitor depends on Execution Interface Factory
- Venue configuration is shared between execution and position monitoring

---

## ADR-002: Tight Loop Architecture Redefinition

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: The original tight loop definition was unclear and didn't properly address execution reconciliation.

**Decision**: Redefine tight loop as the execution reconciliation pattern that ensures position updates are verified before proceeding to the next instruction.

**Tight Loop Definition**:
```
execution_manager → execution_interface_manager → position_update_handler → position_monitor → reconciliation_component
```

**Key Principles**:
- Execution manager sends ONE instruction at a time
- Execution Manager orchestrates Execution Interface Manager which routes to venue-specific interfaces
- Position Update Handler orchestrates tight loop reconciliation handshake
- Execution manager awaits reconciliation success before proceeding to next instruction
- Move to next instruction ONLY after reconciliation
- Happens WITHIN the broader full loop for each execution instruction
- Ensures no race conditions via sequential execution

**Rationale**:
- Eliminates race conditions in position updates
- Ensures data consistency between execution and position monitoring
- Provides clear execution flow with proper error handling
- Maintains sequential execution for predictability

**Consequences**:
- All execution must go through tight loop reconciliation
- Position updates are verified before proceeding
- Sequential execution is enforced
- Error handling is centralized in reconciliation component

---

## ADR-003: Reference-Based Architecture

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Components were passing configuration and other components as method parameters, creating tight coupling and inconsistent interfaces.

**Decision**: Implement Reference-Based Architecture where all component references are set once during initialization and accessed directly throughout the component lifecycle.

**Core Principle**: Components NEVER pass config, data_provider, or other components to each other. All shared resources are set as references during initialization and accessed directly throughout the component lifecycle.

**Singleton Pattern Per Request**:
- ONE config instance (mode-filtered + overrides applied) per request
- ONE data_provider instance (mode-specific data) per request
- ONE instance of each of the 11 components per request
- All components share these singleton instances via references

**Rationale**:
- Eliminates parameter passing complexity
- Ensures consistent component interfaces
- Reduces coupling between components
- Simplifies component initialization
- Makes dependencies explicit and immutable

**Consequences**:
- All components must be initialized with references
- No runtime parameter passing of shared resources
- Clear dependency injection pattern
- Immutable references after initialization

---

## ADR-004: Shared Clock Pattern

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Components were using different timestamps, leading to inconsistent data and timing issues.

**Decision**: Implement Shared Clock Pattern where a single authoritative timestamp is passed to all component method calls.

**Core Principle**: All components receive the same timestamp for each request, ensuring data consistency and proper sequencing.

**Implementation**:
- Single timestamp created at request start
- Passed to all component method calls
- Used for all data queries and updates
- Ensures consistent time-based operations

**Rationale**:
- Eliminates timestamp inconsistencies
- Ensures data consistency across components
- Simplifies debugging and logging
- Provides clear request boundaries

**Consequences**:
- All component methods must accept timestamp parameter
- No component should generate its own timestamps
- Clear request lifecycle with shared timing
- Consistent data across all components

---

## ADR-005: Request Isolation Pattern

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Components were sharing state between requests, leading to data contamination and unpredictable behavior.

**Decision**: Implement Request Isolation Pattern where fresh instances of components and data are created for each request.

**Core Principle**: Each request gets completely fresh instances of all components and data, ensuring no state contamination between requests.

**Implementation**:
- Fresh component instances for each request
- Fresh data provider instances for each request
- Fresh configuration instances for each request
- No shared mutable state between requests

**Rationale**:
- Eliminates state contamination between requests
- Ensures predictable behavior
- Simplifies testing and debugging
- Provides clear request boundaries

**Consequences**:
- All components must be stateless or properly isolated
- No shared mutable state between requests
- Fresh instances for each request
- Clear request lifecycle

---

## ADR-006: Synchronous Component Execution

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Components were mixing synchronous and asynchronous execution, leading to complexity and potential race conditions.

**Decision**: Remove async/await from all internal component methods. Keep async only for external API entry points, request queuing, and I/O operations.

**Core Principle**: Internal component methods are synchronous, with async reserved for I/O operations and external API interactions.

**Implementation**:
- All internal component methods are synchronous
- Async only for external API calls
- Async only for I/O operations (file, database)
- Async only for request queuing and orchestration

**Rationale**:
- Eliminates async/await complexity in business logic
- Reduces potential race conditions
- Simplifies testing and debugging
- Clear separation of concerns

**Consequences**:
- All business logic is synchronous
- Async only for I/O and external APIs
- Simplified component interfaces
- Clear execution model

---

## ADR-007: Mode-Aware Component Behavior

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Components needed to behave differently in backtest vs live mode, but the implementation was inconsistent.

**Decision**: Implement Mode-Aware Component Behavior where components use BASIS_EXECUTION_MODE for conditional logic.

**Core Principle**: Components use BASIS_EXECUTION_MODE to conditionally execute backtest vs live logic. Same component, same code path, different behavior based on mode.

**Implementation**:
1. Store `self.execution_mode` at initialization (from BASIS_EXECUTION_MODE env var)
2. Use `if self.execution_mode == 'backtest':` / `elif self.execution_mode == 'live':` for conditional logic
3. Same component handles both modes with conditional behavior

**Rationale**:
- Single component handles both backtest and live modes
- Consistent behavior across modes
- Simplified testing and maintenance
- Clear mode-based logic separation

**Consequences**:
- All components must be mode-aware
- Conditional logic based on execution mode
- Single component for both modes
- Clear mode-based behavior

---

## ADR-008: Three-Way Venue Interaction

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Venue interactions were not clearly defined, leading to confusion about data flow and responsibilities.

**Decision**: Define three distinct venue interaction types with clear responsibilities and data flow.

**Three-Way Venue Interaction**:
1. **Market Data Feed** (public, read-only)
   - Real-time price feeds
   - Order book data
   - Market statistics
   - No authentication required

2. **Order Handling** (private, read-write)
   - Place orders
   - Cancel orders
   - Order status updates
   - Requires authentication

3. **Position Updates** (private, read-only)
   - Account balances
   - Position sizes
   - P&L information
   - Requires authentication

**Rationale**:
- Clear separation of concerns
- Different authentication requirements
- Different data access patterns
- Simplified venue interface design

**Consequences**:
- Three distinct interface types per venue
- Clear authentication requirements
- Separate data flow patterns
- Simplified venue implementation

---

## ADR-009: Separate Data Source from Execution Mode

**Date**: January 9, 2025  
**Status**: Accepted  
**Context**: Data source and execution mode were conflated, making it difficult to test different combinations.

**Decision**: Separate BASIS_DATA_MODE (csv/db) from BASIS_EXECUTION_MODE (backtest/live) to create clear separation of concerns.

**Environment Variables**:
- `BASIS_EXECUTION_MODE` - Execution mode (backtest/live) - controls venue execution behavior
- `BASIS_DATA_MODE` - Data source mode (csv/db) - controls data source for backtest mode only, NOT related to data persistence or execution routing. Can be set independently of BASIS_ENVIRONMENT (dev can use db, prod can use csv).

**Valid Combinations**:
- `BASIS_EXECUTION_MODE='backtest'` + `BASIS_DATA_MODE='csv'` = simulated execution with CSV data
- `BASIS_EXECUTION_MODE='live'` + `BASIS_DATA_MODE='api'` = real execution with API data

**Rationale**:
- Clear separation of data source and execution behavior
- Flexible testing combinations
- Independent configuration of data and execution
- Simplified mode management

**Consequences**:
- Two independent environment variables
- Flexible mode combinations
- Clear separation of concerns
- Simplified testing scenarios

---

## ADR-010: Execution Interface Architecture

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Execution interfaces needed to support both backtest and live modes with seamless switching.

**Decision**: Implement execution interfaces with seamless backtest/live switching using factory pattern.

**Implementation**:
- Execution Interface Factory creates mode-specific interfaces
- Same interface for both backtest and live modes
- Mode-specific behavior handled internally
- Seamless switching between modes

**Rationale**:
- Single interface for both modes
- Seamless mode switching
- Simplified venue management
- Consistent behavior across modes

**Consequences**:
- Factory pattern for interface creation
- Mode-specific internal behavior
- Single interface for both modes
- Seamless mode switching

---

## ADR-011: Configuration Architecture

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Configuration was scattered across multiple files and formats, making it difficult to manage and validate.

**Decision**: Implement centralized configuration architecture with YAML files and Pydantic validation.

**Implementation**:
- All configuration in YAML files
- Pydantic models for validation
- Environment variable overrides
- Centralized configuration loading

**Rationale**:
- Centralized configuration management
- Strong validation with Pydantic
- Environment-specific overrides
- Simplified configuration handling

**Consequences**:
- YAML-based configuration
- Pydantic validation
- Environment variable support
- Centralized configuration loading

---

## ADR-012: Component Factory Architecture

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Component creation was scattered and inconsistent, making it difficult to manage dependencies and initialization.

**Decision**: Implement centralized component factory with dependency injection and configuration validation.

**Implementation**:
- Centralized component factory
- Dependency injection pattern
- Configuration validation
- Proper initialization order

**Rationale**:
- Centralized component creation
- Proper dependency management
- Configuration validation
- Consistent initialization

**Consequences**:
- Factory pattern for components
- Dependency injection
- Configuration validation
- Proper initialization order

---

## ADR-013: Data Provider Factory Architecture

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Data providers needed to support multiple data sources and modes with proper validation.

**Decision**: Implement data provider factory with mode-specific data providers and validation.

**Implementation**:
- Data Provider Factory creates mode-specific providers
- Validation of data requirements
- Support for multiple data sources
- Mode-specific behavior

**Rationale**:
- Centralized data provider creation
- Validation of data requirements
- Support for multiple sources
- Mode-specific behavior

**Consequences**:
- Factory pattern for data providers
- Data requirement validation
- Multiple data source support
- Mode-specific providers

---

## ADR-014: ML Strategy Integration Architecture

**Date**: January 10, 2025  
**Status**: Accepted  
**Context**: ML strategies needed to integrate with the existing strategy framework while maintaining their unique requirements.

**Decision**: Implement ML strategy integration with specialized data providers and risk management.

**Implementation**:
- ML-specific data providers
- Specialized risk management
- Integration with existing strategy framework
- Support for ML-specific features

**Rationale**:
- Seamless ML strategy integration
- Specialized ML requirements
- Integration with existing framework
- Support for ML features

**Consequences**:
- ML-specific components
- Specialized data providers
- Integration with strategy framework
- ML-specific features

---

## ADR-015: Validation Philosophy

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Validation was inconsistent across components, leading to runtime errors and data inconsistencies.

**Decision**: Implement comprehensive validation philosophy with fail-fast principles and Pydantic models.

**Implementation**:
- Fail-fast validation at startup
- Pydantic models for all data structures
- Comprehensive input validation
- Clear error messages

**Rationale**:
- Early detection of configuration errors
- Strong data validation
- Clear error messages
- Consistent validation approach

**Consequences**:
- Fail-fast validation
- Pydantic models everywhere
- Comprehensive validation
- Clear error handling

---

## ADR-016: Testing Granularity

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Testing was inconsistent and didn't provide adequate coverage of component behavior.

**Decision**: Implement comprehensive testing strategy with unit, integration, and end-to-end tests.

**Implementation**:
- Unit tests for all components
- Integration tests for component interactions
- End-to-end tests for complete workflows
- Comprehensive test coverage

**Rationale**:
- Comprehensive test coverage
- Early detection of issues
- Confidence in component behavior
- Simplified debugging

**Consequences**:
- Comprehensive test suite
- Multiple test levels
- High test coverage
- Simplified debugging

---

## ADR-017: Plot Format

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Plotting was inconsistent and didn't provide clear visualization of strategy performance.

**Decision**: Implement standardized plot format with consistent styling and data presentation.

**Implementation**:
- Standardized plot styling
- Consistent data presentation
- Clear performance visualization
- Professional appearance

**Rationale**:
- Consistent visualization
- Clear performance metrics
- Professional appearance
- Simplified plot creation

**Consequences**:
- Standardized plot format
- Consistent styling
- Clear visualization
- Professional appearance

---

## ADR-018: Margin Ratio Thresholds

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Margin ratio thresholds were hardcoded and not configurable, making it difficult to adjust risk parameters.

**Decision**: Implement configurable margin ratio thresholds with proper validation and defaults.

**Implementation**:
- Configurable margin ratio thresholds
- Pydantic validation
- Sensible defaults
- Environment-specific overrides

**Rationale**:
- Configurable risk parameters
- Proper validation
- Sensible defaults
- Environment-specific settings

**Consequences**:
- Configurable thresholds
- Validation of thresholds
- Default values
- Environment overrides

---

## ADR-019: Shared Calculator Logic

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Calculator logic was duplicated across components, leading to inconsistencies and maintenance issues.

**Decision**: Implement shared calculator logic with centralized calculations and consistent results.

**Implementation**:
- Centralized calculator logic
- Shared calculation methods
- Consistent results across components
- Proper validation

**Rationale**:
- Eliminate code duplication
- Consistent calculations
- Centralized logic
- Simplified maintenance

**Consequences**:
- Shared calculator logic
- Consistent results
- Centralized calculations
- Simplified maintenance

---

## ADR-020: Data File Naming Strategy

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Data file naming was inconsistent, making it difficult to locate and manage data files.

**Decision**: Implement standardized data file naming strategy with clear conventions and organization.

**Implementation**:
- Standardized naming conventions
- Clear file organization
- Consistent file structure
- Easy file location

**Rationale**:
- Consistent file naming
- Clear organization
- Easy file location
- Simplified data management

**Consequences**:
- Standardized naming
- Clear organization
- Consistent structure
- Easy file location

---

## ADR-021: Config Validation: Fail-Fast

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Configuration validation was happening at runtime, leading to late detection of errors.

**Decision**: Implement fail-fast configuration validation at startup with comprehensive error reporting.

**Implementation**:
- Validation at startup
- Comprehensive error reporting
- Clear error messages
- Early error detection

**Rationale**:
- Early error detection
- Clear error messages
- Comprehensive validation
- Simplified debugging

**Consequences**:
- Startup validation
- Early error detection
- Clear error messages
- Comprehensive validation

---

## ADR-022: Configuration Architecture

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Configuration was scattered and inconsistent, making it difficult to manage and validate.

**Decision**: Implement centralized configuration architecture with YAML files and proper validation.

**Implementation**:
- Centralized YAML configuration
- Pydantic validation
- Environment variable overrides
- Clear configuration structure

**Rationale**:
- Centralized configuration
- Strong validation
- Environment overrides
- Clear structure

**Consequences**:
- YAML-based configuration
- Pydantic validation
- Environment overrides
- Centralized management

---

## ADR-023: Exposure Monitor Outputs

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Exposure monitor outputs were not clearly defined, leading to confusion about data structure and usage.

**Decision**: Define standardized exposure monitor outputs with clear data structure and validation.

**Implementation**:
- Standardized output format
- Clear data structure
- Pydantic validation
- Consistent data presentation

**Rationale**:
- Standardized outputs
- Clear data structure
- Consistent presentation
- Proper validation

**Consequences**:
- Standardized format
- Clear structure
- Consistent data
- Proper validation

---

## ADR-024: BacktestService Configuration

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: BacktestService configuration was not clearly defined, making it difficult to configure and use.

**Decision**: Define comprehensive BacktestService configuration with proper validation and defaults.

**Implementation**:
- Comprehensive configuration
- Pydantic validation
- Sensible defaults
- Clear configuration structure

**Rationale**:
- Comprehensive configuration
- Proper validation
- Sensible defaults
- Clear structure

**Consequences**:
- Comprehensive config
- Validation
- Default values
- Clear structure

---

## ADR-025: Component Data Flow Architecture

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Component data flow was not clearly defined, leading to confusion about data dependencies and flow.

**Decision**: Define clear component data flow architecture with explicit dependencies and data flow patterns.

**Implementation**:
- Clear data flow patterns
- Explicit dependencies
- Standardized interfaces
- Proper data validation

**Rationale**:
- Clear data flow
- Explicit dependencies
- Standardized interfaces
- Proper validation

**Consequences**:
- Clear data flow
- Explicit dependencies
- Standardized interfaces
- Proper validation

---

## ADR-026: Config Infrastructure Components

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Configuration infrastructure components were not clearly defined, making it difficult to manage configuration.

**Decision**: Define clear configuration infrastructure components with proper responsibilities and interfaces.

**Implementation**:
- Clear component responsibilities
- Standardized interfaces
- Proper validation
- Centralized configuration management

**Rationale**:
- Clear responsibilities
- Standardized interfaces
- Proper validation
- Centralized management

**Consequences**:
- Clear responsibilities
- Standardized interfaces
- Proper validation
- Centralized management

---

## ADR-027: Live Trading Service Architecture

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Live trading service architecture was not clearly defined, making it difficult to implement and maintain.

**Decision**: Define comprehensive live trading service architecture with proper components and data flow.

**Implementation**:
- Comprehensive service architecture
- Clear component responsibilities
- Proper data flow
- Standardized interfaces

**Rationale**:
- Comprehensive architecture
- Clear responsibilities
- Proper data flow
- Standardized interfaces

**Consequences**:
- Comprehensive architecture
- Clear responsibilities
- Proper data flow
- Standardized interfaces

---

## ADR-028: Deployment to GCloud

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Deployment strategy was not clearly defined, making it difficult to deploy and manage the application.

**Decision**: Define comprehensive deployment strategy for Google Cloud Platform with proper infrastructure and monitoring.

**Implementation**:
- GCloud deployment strategy
- Proper infrastructure setup
- Monitoring and logging
- Scalability considerations

**Rationale**:
- Clear deployment strategy
- Proper infrastructure
- Monitoring and logging
- Scalability

**Consequences**:
- GCloud deployment
- Proper infrastructure
- Monitoring and logging
- Scalability

---

## ADR-029: Component Communication Standard

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Component communication was not standardized, leading to inconsistent interfaces and data flow.

**Decision**: Define standardized component communication patterns with clear interfaces and data flow.

**Implementation**:
- Standardized communication patterns
- Clear interfaces
- Consistent data flow
- Proper validation

**Rationale**:
- Standardized communication
- Clear interfaces
- Consistent data flow
- Proper validation

**Consequences**:
- Standardized patterns
- Clear interfaces
- Consistent flow
- Proper validation

---

## ADR-030: Error Logging Standard

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Error logging was inconsistent across components, making it difficult to debug and monitor issues.

**Decision**: Define standardized error logging with consistent format and comprehensive information.

**Implementation**:
- Standardized error format
- Comprehensive error information
- Consistent logging levels
- Proper error handling

**Rationale**:
- Standardized error logging
- Comprehensive information
- Consistent format
- Proper handling

**Consequences**:
- Standardized format
- Comprehensive info
- Consistent levels
- Proper handling

---

## ADR-031: Liquidation Simulation

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Liquidation simulation was not properly implemented, making it difficult to test risk scenarios.

**Decision**: Implement comprehensive liquidation simulation with proper risk modeling and testing.

**Implementation**:
- Comprehensive liquidation simulation
- Proper risk modeling
- Testing scenarios
- Realistic liquidation logic

**Rationale**:
- Comprehensive simulation
- Proper risk modeling
- Testing scenarios
- Realistic logic

**Consequences**:
- Comprehensive simulation
- Proper risk modeling
- Testing scenarios
- Realistic logic

---

## ADR-032: Live Trading Data Flow Integration

**Date**: January 6, 2025  
**Status**: Accepted  
**Context**: Live trading data flow was not properly integrated with the existing architecture.

**Decision**: Integrate live trading data flow with existing architecture while maintaining consistency and reliability.

**Implementation**:
- Integrated data flow
- Consistent architecture
- Reliable data handling
- Proper error handling

**Rationale**:
- Integrated data flow
- Consistent architecture
- Reliable handling
- Proper error handling

**Consequences**:
- Integrated flow
- Consistent architecture
- Reliable handling
- Proper error handling

---

## ADR-033: Config-Driven Mode-Agnostic Components

**Date**: October 11, 2025  
**Status**: Accepted  
**Context**: Components needed to be mode-agnostic while still supporting different execution modes.

**Decision**: Implement config-driven mode-agnostic components that use configuration to determine behavior rather than hardcoded mode checks.

**Implementation**:
- Configuration-driven behavior
- Mode-agnostic components
- Flexible configuration
- Consistent interfaces

**Rationale**:
- Configuration-driven behavior
- Mode-agnostic design
- Flexible configuration
- Consistent interfaces

**Consequences**:
- Configuration-driven
- Mode-agnostic
- Flexible config
- Consistent interfaces

---

## ADR-034: DataProvider Factory with Data Requirements Validation

**Date**: October 11, 2025  
**Status**: Accepted  
**Context**: Data providers needed to validate data requirements and provide clear error messages for missing data.

**Decision**: Implement DataProvider factory with comprehensive data requirements validation and clear error reporting.

**Implementation**:
- Data requirements validation
- Clear error messages
- Comprehensive validation
- Proper error handling

**Rationale**:
- Data requirements validation
- Clear error messages
- Comprehensive validation
- Proper error handling

**Consequences**:
- Data validation
- Clear errors
- Comprehensive validation
- Proper handling

---

## ADR-035: Graceful Data Handling in Components

**Date**: October 11, 2025  
**Status**: Accepted  
**Context**: Components needed to handle missing or invalid data gracefully without crashing.

**Decision**: Implement graceful data handling in all components with proper fallbacks and error recovery.

**Implementation**:
- Graceful data handling
- Proper fallbacks
- Error recovery
- Robust operation

**Rationale**:
- Graceful handling
- Proper fallbacks
- Error recovery
- Robust operation

**Consequences**:
- Graceful handling
- Proper fallbacks
- Error recovery
- Robust operation

---

## ADR-036: Component Factory with Config Validation

**Date**: October 11, 2025  
**Status**: Accepted  
**Context**: Component factory needed to validate configuration before creating components.

**Decision**: Implement component factory with comprehensive configuration validation and proper error handling.

**Implementation**:
- Configuration validation
- Proper error handling
- Comprehensive validation
- Clear error messages

**Rationale**:
- Configuration validation
- Proper error handling
- Comprehensive validation
- Clear error messages

**Consequences**:
- Config validation
- Proper handling
- Comprehensive validation
- Clear errors

---

## ADR-037: Core vs Supporting Components Architecture

**Date**: October 11, 2025  
**Status**: Accepted  
**Context**: Components needed to be categorized as core or supporting to clarify dependencies and responsibilities.

**Decision**: Define clear architecture with core components (required for operation) and supporting components (optional features).

**Implementation**:
- Core component identification
- Supporting component identification
- Clear dependencies
- Proper architecture

**Rationale**:
- Clear component categorization
- Proper dependencies
- Clear architecture
- Simplified management

**Consequences**:
- Clear categorization
- Proper dependencies
- Clear architecture
- Simplified management

---

## ADR-038: ML Strategy Integration Architecture

**Date**: January 10, 2025  
**Status**: Accepted  
**Context**: ML strategies needed to integrate with the existing strategy framework while maintaining their unique requirements.

**Decision**: Implement ML strategy integration with specialized data providers and risk management.

**Implementation**:
- ML-specific data providers
- Specialized risk management
- Integration with existing strategy framework
- Support for ML-specific features

**Rationale**:
- Seamless ML strategy integration
- Specialized ML requirements
- Integration with existing framework
- Support for ML features

**Consequences**:
- ML-specific components
- Specialized data providers
- Integration with strategy framework
- ML-specific features

---

## ADR-058: Unified Order/Trade System

**Date**: October 13, 2025  
**Status**: Accepted  
**Context**: The existing strategy-to-execution flow had multiple abstractions (StrategyAction, execution_instructions) that created confusion and complexity. The system needed a unified, clean interface for all trading operations.

**Decision**: Implement a unified Order/Trade system that replaces StrategyAction and execution_instructions with a single, clean interface using Pydantic models.

**Implementation**:
- **Order Model**: Pydantic model representing a single execution command with comprehensive validation
- **Trade Model**: Pydantic model representing execution results and outcomes
- **Strategy Interface**: `make_strategy_decision()` returns `List[Order]` instead of `StrategyAction`
- **Execution Modes**: Sequential (default) and Atomic (for flash loans, complex DeFi operations)
- **Atomic Groups**: Orders can be grouped with `atomic_group_id` and `sequence_in_group`
- **Operation Types**: SPOT_TRADE, PERP_TRADE, SUPPLY, BORROW, REPAY, WITHDRAW, STAKE, UNSTAKE, SWAP, FLASH_BORROW, FLASH_REPAY, TRANSFER
- **Risk Management**: Built-in support for take_profit and stop_loss
- **Venue Support**: Works with CEX, DeFi, and wallet operations

**Rationale**:
- Eliminates multiple abstractions and confusion
- Provides single, clean interface for all trading operations
- Supports both sequential and atomic execution patterns
- Comprehensive validation with Pydantic models
- Clear separation between order intent and execution results
- Supports complex DeFi operations with atomic groups
- Maintains backward compatibility during transition

**Consequences**:
- All strategies must be refactored to return `List[Order]`
- VenueManager must be updated to process `List[Order]` and return `List[Trade]`
- Legacy StrategyAction and execution_instructions must be removed
- All documentation must be updated to reflect new system
- Quality gate scripts must be updated to validate new system
- Comprehensive testing required for all refactored components

---

## ADR Summary Table

| ADR | Title | Date | Status | Priority |
|-----|-------|------|--------|----------|
| ADR-001 | Position Monitor Live Integration Architecture | 2024-12-01 | Accepted | High |
| ADR-002 | Tight Loop Architecture Redefinition | 2025-01-06 | Accepted | High |
| ADR-003 | Reference-Based Architecture | 2025-01-06 | Accepted | High |
| ADR-004 | Shared Clock Pattern | 2025-01-06 | Accepted | High |
| ADR-005 | Request Isolation Pattern | 2025-01-06 | Accepted | High |
| ADR-006 | Synchronous Component Execution | 2025-01-06 | Accepted | High |
| ADR-007 | Mode-Aware Component Behavior | 2025-01-06 | Accepted | High |
| ADR-008 | Three-Way Venue Interaction | 2025-01-06 | Accepted | High |
| ADR-009 | Separate Data Source from Execution Mode | 2025-01-09 | Accepted | High |
| ADR-010 | Execution Interface Architecture | 2025-01-06 | Accepted | High |
| ADR-011 | Configuration Architecture | 2025-01-06 | Accepted | High |
| ADR-012 | Execution Interface Architecture | 2025-01-06 | Accepted | High |
| ADR-013 | Data Provider Factory Architecture | 2025-01-06 | Accepted | High |
| ADR-014 | ML Strategy Integration Architecture | 2025-01-10 | Accepted | High |
| ADR-015 | Validation Philosophy | 2025-01-06 | Accepted | High |
| ADR-016 | Testing Granularity | 2025-01-06 | Accepted | High |
| ADR-017 | Plot Format | 2025-01-06 | Accepted | High |
| ADR-018 | Margin Ratio Thresholds | 2025-01-06 | Accepted | High |
| ADR-019 | Shared Calculator Logic | 2025-01-06 | Accepted | High |
| ADR-020 | Data File Naming Strategy | 2025-01-06 | Accepted | High |
| ADR-021 | Config Validation: Fail-Fast | 2025-01-06 | Accepted | High |
| ADR-022 | Configuration Architecture | 2025-01-06 | Accepted | High |
| ADR-023 | Exposure Monitor Outputs | 2025-01-06 | Accepted | High |
| ADR-024 | BacktestService Configuration | 2025-01-06 | Accepted | High |
| ADR-025 | Component Data Flow Architecture | 2025-01-06 | Accepted | High |
| ADR-026 | Config Infrastructure Components | 2025-01-06 | Accepted | High |
| ADR-027 | Live Trading Service Architecture | 2025-01-06 | Accepted | High |
| ADR-028 | Deployment to GCloud | 2025-01-06 | Accepted | High |
| ADR-029 | Component Communication Standard | 2025-01-06 | Accepted | High |
| ADR-030 | Error Logging Standard | 2025-01-06 | Accepted | High |
| ADR-031 | Liquidation Simulation | 2025-01-06 | Accepted | High |
| ADR-032 | Live Trading Data Flow Integration | 2025-01-06 | Accepted | High |
| ADR-033 | Config-Driven Mode-Agnostic Components | 2025-10-11 | Accepted | High |
| ADR-034 | DataProvider Factory with Data Requirements Validation | 2025-10-11 | Accepted | High |
| ADR-035 | Graceful Data Handling in Components | 2025-10-11 | Accepted | High |
| ADR-036 | Component Factory with Config Validation | 2025-10-11 | Accepted | High |
| ADR-037 | Core vs Supporting Components Architecture | 2025-10-11 | Accepted | High |
| ADR-038 | ML Strategy Integration Architecture | 2025-01-10 | Accepted | High |
| ADR-058 | Unified Order/Trade System | 2025-10-13 | Accepted | High |