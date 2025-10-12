"""Strategy management endpoints - Config-driven approach."""

from fastapi import APIRouter, HTTPException, Request, Query
from pathlib import Path
from typing import Optional, Dict, Any
import structlog
import yaml

from ..models.responses import (
    StandardResponse,
    StrategyInfoResponse,
    StrategyListResponse
)
from ...infrastructure.config.config_manager import get_settings
from ...infrastructure.config.config_manager import load_strategy_config as load_merged_strategy_config
from ...infrastructure.config.config_manager import (
    get_available_strategies,
    get_strategy_file_path,
    validate_strategy_name
)
from ...infrastructure.config.config_validator import validate_configuration

logger = structlog.get_logger()
router = APIRouter()


# _load_strategy_config removed - using centralized load_strategy_config from strategy_discovery


def _derive_strategy_info_from_config(strategy_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Derive strategy information from config parameters."""
    strategy_params = config.get('strategy', {})  # OK - checking if section exists
    backtest_params = config.get('backtest', {})  # OK - checking if section exists
    
    # Extract key information from config
    share_class = strategy_params.get('share_class', 'USDT')
    
    # Determine risk level from configuration
    has_leverage = strategy_params.get('staking_leverage_enabled', False)
    has_basis_trading = strategy_params.get('basis_trade_enabled', False)
    has_staking = strategy_params.get('staking_enabled', False)
    
    if has_leverage or has_basis_trading:
        risk_level = "high"
    elif has_staking:
        risk_level = "medium"  
    else:
        risk_level = "low"
    
    # Determine strategy type from enabled features
    features = []
    if strategy_params.get('lending_enabled', False):
        features.append("lending")
    if has_staking:
        features.append("staking")
    if has_leverage:
        features.append("leverage")
    if has_basis_trading:
        features.append("basis_trading")
    
    strategy_type = "_".join(features) if features else "unknown"
    
    # Calculate expected return range based on features
    if risk_level == "low":
        expected_return = "4-12% APR"
    elif risk_level == "medium":
        expected_return = "8-25% APR"
    else:
        expected_return = "15-50% APR"
    
    return {
        "name": strategy_name,
        "display_name": strategy_name.replace("_", " ").title(),
        "description": f"Config-driven strategy: {strategy_type}",
        "share_class": share_class,
        "risk_level": risk_level,
        "expected_return": expected_return,
        "minimum_capital": backtest_params.get('initial_capital', 1000),
        "supported_venues": ["AAVE", "LIDO", "BYBIT"],  # From config if available
        "parameters": {
            "strategy_type": strategy_type,
            "complexity": "simple" if risk_level == "low" else "complex",
            "architecture": "config_driven_components",
            "features": {
                "lending_enabled": strategy_params.get('lending_enabled', False),
                "staking_enabled": strategy_params.get('staking_enabled', False),
                "leverage_enabled": strategy_params.get('staking_leverage_enabled', False),
                "basis_trade_enabled": strategy_params.get('basis_trade_enabled', False),
            }
        }
    }


@router.get(
    "/",
    response_model=StandardResponse[StrategyListResponse],
    summary="List available strategies",
    description="Get a list of all available trading strategies from config files"
)
async def list_strategies(
    request: Request,
    share_class: Optional[str] = Query(None, description="Filter by share class (ETH or USDT)"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
) -> StandardResponse[StrategyListResponse]:
    """
    List all available trading strategies by reading config files.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        logger.info(
            "Listing available strategies from config files",
            correlation_id=correlation_id,
            share_class_filter=share_class,
            risk_level_filter=risk_level
        )
        
        # Use centralized strategy discovery
        available_strategy_names = get_available_strategies()
        if not available_strategy_names:
            logger.warning("No strategies found in configs/scenarios/")
            return StandardResponse(
                success=True,
                data=StrategyListResponse(strategies=[], total=0)
            )
        
        strategies = []
        
        # Process each discovered strategy
        for strategy_name in available_strategy_names:
            # Load merged config and derive strategy info
            config = load_merged_strategy_config(strategy_name)
            if not config:
                continue  # Skip if config can't be loaded
                
            strategy_info = _derive_strategy_info_from_config(strategy_name, config)
            
            # Apply filters
            if share_class and strategy_info.get("share_class") != share_class:
                continue
            if risk_level and strategy_info.get("risk_level") != risk_level:
                continue
                
            strategies.append(StrategyInfoResponse(**strategy_info))
        
        return StandardResponse(
            success=True,
            data=StrategyListResponse(
                strategies=strategies,
                total=len(strategies)
            )
        )
        
    except Exception as e:
        logger.error(
            "Failed to list strategies", 
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to list strategies: {str(e)}")


@router.post(
    "/{strategy_name}/validate",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Validate strategy configuration",
    description="Validate strategy configuration parameters"
)
async def validate_strategy_config(
    strategy_name: str,
    config: Dict[str, Any],
    request: Request
) -> StandardResponse[Dict[str, Any]]:
    """
    Validate strategy configuration parameters.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        logger.info(
            "Validating strategy configuration",
            correlation_id=correlation_id,
            strategy_name=strategy_name
        )
        
        # Validate strategy name
        try:
            validate_strategy_name(strategy_name)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Load and validate the configuration
        merged_config = load_merged_strategy_config(strategy_name)
        if not merged_config:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy config not found: {strategy_name}"
            )
        
        # Apply the provided config overrides
        if 'strategy' in config:
            merged_config['strategy'].update(config['strategy'])
        if 'backtest' in config:
            merged_config['backtest'].update(config['backtest'])
        
        # Basic validation - check required fields
        validation_errors = []
        
        # Validate strategy section
        strategy_params = merged_config.get('strategy', {})
        if not strategy_params.get('share_class'):
            validation_errors.append("share_class is required")
        
        # Validate backtest section
        backtest_params = merged_config.get('backtest', {})
        if not backtest_params.get('initial_capital'):
            validation_errors.append("initial_capital is required")
        if not backtest_params.get('start_date'):
            validation_errors.append("start_date is required")
        if not backtest_params.get('end_date'):
            validation_errors.append("end_date is required")
        
        if validation_errors:
            return StandardResponse(
                success=False,
                data={
                    "valid": False,
                    "errors": validation_errors
                }
            )
        
        return StandardResponse(
            success=True,
            data={
                "valid": True,
                "config": merged_config
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to validate strategy configuration",
            correlation_id=correlation_id,
            strategy_name=strategy_name,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to validate strategy configuration: {str(e)}")


@router.get(
    "/{strategy_name}/parameters",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Get strategy parameters",
    description="Get configurable parameters for a strategy"
)
async def get_strategy_parameters(
    strategy_name: str,
    request: Request
) -> StandardResponse[Dict[str, Any]]:
    """
    Get configurable parameters for a strategy.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        logger.info(
            "Getting strategy parameters",
            correlation_id=correlation_id,
            strategy_name=strategy_name
        )
        
        # Validate strategy name
        try:
            validate_strategy_name(strategy_name)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        # Load strategy config
        config = load_merged_strategy_config(strategy_name)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy config not found: {strategy_name}"
            )
        
        # Extract configurable parameters
        parameters = {
            "strategy": {
                "share_class": {
                    "type": "string",
                    "options": ["USDT", "ETH"],
                    "default": config.get('strategy', {}).get('share_class', 'USDT'),
                    "description": "Share class for the strategy"
                },
                "target_apy": {
                    "type": "number",
                    "min": 0.0,
                    "max": 1.0,
                    "default": config.get('strategy', {}).get('target_apy', 0.1),
                    "description": "Target APY for the strategy"
                }
            },
            "backtest": {
                "initial_capital": {
                    "type": "number",
                    "min": 1000,
                    "max": 10000000,
                    "default": config.get('backtest', {}).get('initial_capital', 10000),
                    "description": "Initial capital for backtest"
                },
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "default": config.get('backtest', {}).get('start_date', '2024-01-01'),
                    "description": "Backtest start date"
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "default": config.get('backtest', {}).get('end_date', '2024-12-31'),
                    "description": "Backtest end date"
                }
            }
        }
        
        return StandardResponse(
            success=True,
            data=parameters
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get strategy parameters",
            correlation_id=correlation_id,
            strategy_name=strategy_name,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to get strategy parameters: {str(e)}")


@router.get(
    "/{strategy_name}",
    response_model=StandardResponse[StrategyInfoResponse],
    summary="Get strategy details",
    description="Get detailed information about a specific strategy from its config"
)
async def get_strategy(
    strategy_name: str,
    request: Request
) -> StandardResponse[StrategyInfoResponse]:
    """
    Get detailed information about a specific strategy by reading its config file.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        logger.info(
            "Getting strategy details from config",
            correlation_id=correlation_id,
            strategy_name=strategy_name
        )
        
        # Use centralized strategy discovery and validation
        try:
            validate_strategy_name(strategy_name)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        # Load merged config and derive strategy info
        config = load_merged_strategy_config(strategy_name)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy config file not found or invalid: {strategy_name}.yaml"
            )
            
        strategy_info = _derive_strategy_info_from_config(strategy_name, config)
        
        return StandardResponse(
            success=True,
            data=StrategyInfoResponse(**strategy_info)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get strategy details",
            correlation_id=correlation_id,
            strategy_name=strategy_name,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to get strategy details: {str(e)}")


"""Removed: validate and raw YAML endpoints to simplify API surface."""


"""Removed: YAML get endpoint."""


"""Removed: YAML save endpoint."""


# ---------------------------------------------------------------------------
# Config discovery endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{strategy_name}/config/merged",
    summary="Get merged validated config (JSON and YAML)",
    description=(
        "Return the merged configuration for a strategy (infrastructure + scenario), "
        "with optional query params applied, validated against the canonical schema."
    )
)
async def get_merged_config(
    strategy_name: str,
    request: Request,
    start_date: Optional[str] = Query(None, description="Backtest start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Backtest end date YYYY-MM-DD"),
    initial_capital: Optional[float] = Query(10000.0, description="Initial capital amount"),
    share_class: Optional[str] = Query("USDT", description="Share class (ETH or USDT)")
) -> StandardResponse[Dict[str, Any]]:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    try:
        logger.info(
            "Building merged validated config",
            correlation_id=correlation_id,
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            share_class=share_class,
        )
        
        # Debug: Log the exact received parameters
        logger.info(f"DEBUG: Received parameters - initial_capital={initial_capital} (type: {type(initial_capital)})")

        # Validate strategy name and load configs
        try:
            validate_strategy_name(strategy_name)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

        # Use canonical loader to merge infrastructure + scenario
        merged = load_merged_strategy_config(strategy_name) or {}

        # Ensure required sections
        merged.setdefault("backtest", {})
        merged.setdefault("strategy", {})

        # Apply query overrides if given (use existing values otherwise)
        if start_date:
            merged["backtest"]["start_date"] = start_date
        if end_date:
            merged["backtest"]["end_date"] = end_date
        if initial_capital is not None:
            merged["backtest"]["initial_capital"] = float(initial_capital)
        if share_class:
            merged["strategy"]["share_class"] = share_class

        # Return both JSON and YAML representations
        # Use the merged config directly since it's already validated
        validated = merged
        yaml_text = yaml.safe_dump(validated, sort_keys=False)

        return StandardResponse(
            success=True,
            data={
                "strategy_name": strategy_name,
                "config_json": validated,
                "config_yaml": yaml_text,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to build merged config",
            correlation_id=correlation_id,
            strategy_name=strategy_name,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to build merged config: {str(e)}")


@router.get(
    "/modes/{mode_name}",
    response_model=StandardResponse[Dict[str, Any]],
    summary="Get mode configuration",
    description="Get configuration for a specific mode including target_apy and max_drawdown"
)
async def get_mode_config(
    mode_name: str,
    request: Request
) -> StandardResponse[Dict[str, Any]]:
    """
    Get mode configuration including target_apy and max_drawdown.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        logger.info(
            "Getting mode configuration",
            correlation_id=correlation_id,
            mode_name=mode_name
        )
        
        # Load mode config from YAML file
        config_path = Path("configs/modes") / f"{mode_name}.yaml"
        if not config_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Mode config not found: {mode_name}.yaml"
            )
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Extract key information for frontend
        mode_info = {
            "mode": config.get("mode", mode_name),
            "description": config.get("description", ""),
            "target_apy": config.get("target_apy", 0.0),
            "max_drawdown": config.get("max_drawdown", 0.0),
            "share_class": config.get("share_class", "USDT"),
            "risk_level": "high" if config.get("leverage_enabled", False) else "medium",
            "features": {
                "lending_enabled": config.get("lending_enabled", False),
                "staking_enabled": config.get("staking_enabled", False),
                "leverage_enabled": config.get("leverage_enabled", False),
                "basis_trade_enabled": config.get("basis_trade_enabled", False),
            }
        }
        
        return StandardResponse(
            success=True,
            data=mode_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get mode configuration",
            correlation_id=correlation_id,
            mode_name=mode_name,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to get mode configuration: {str(e)}")


@router.get(
    "/modes/",
    response_model=StandardResponse[Dict[str, Any]],
    summary="List available modes",
    description="Get list of all available modes with their configurations"
)
async def list_modes(
    request: Request,
    share_class: Optional[str] = Query(None, description="Filter by share class (ETH or USDT)")
) -> StandardResponse[Dict[str, Any]]:
    """
    List all available modes with their configurations.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        logger.info(
            "Listing available modes",
            correlation_id=correlation_id,
            share_class_filter=share_class
        )
        
        modes_dir = Path("configs/modes")
        if not modes_dir.exists():
            raise HTTPException(status_code=404, detail="Modes directory not found")
        
        modes = []
        for yaml_file in modes_dir.glob("*.yaml"):
            mode_name = yaml_file.stem
            
            try:
                with open(yaml_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Apply share class filter
                if share_class and config.get("share_class") != share_class:
                    continue
                
                mode_info = {
                    "mode": config.get("mode", mode_name),
                    "description": config.get("description", ""),
                    "target_apy": config.get("target_apy", 0.0),
                    "max_drawdown": config.get("max_drawdown", 0.0),
                    "share_class": config.get("share_class", "USDT"),
                    "risk_level": "high" if config.get("leverage_enabled", False) else "medium",
                    "features": {
                        "lending_enabled": config.get("lending_enabled", False),
                        "staking_enabled": config.get("staking_enabled", False),
                        "leverage_enabled": config.get("leverage_enabled", False),
                        "basis_trade_enabled": config.get("basis_trade_enabled", False),
                    }
                }
                modes.append(mode_info)
                
            except Exception as e:
                logger.warning(f"Failed to load mode config {yaml_file}: {e}")
                continue
        
        return StandardResponse(
            success=True,
            data={"modes": modes, "total": len(modes)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to list modes",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to list modes: {str(e)}")