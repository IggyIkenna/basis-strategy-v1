"""
Mode-Agnostic Data Subscriptions Manager

Provides mode-agnostic data subscription management that works for both backtest and live modes.
Manages data subscriptions across all venues and provides generic subscription logic.

Reference: docs/REFERENCE_ARCHITECTURE_CANONICAL.md - Section 7 (Generic vs Mode-Specific)
Reference: docs/specs/08_DATA_SUBSCRIPTIONS.md - Mode-agnostic data subscription management
"""

from typing import Dict, List, Any, Optional
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class DataSubscriptions:
    """Mode-agnostic data subscriptions manager that works for both backtest and live modes"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Dict[str, Any], data_provider, utility_manager):
        """
        Initialize data subscriptions manager.
        
        Args:
            config: Strategy configuration
            data_provider: Data provider instance
            utility_manager: Centralized utility manager
        """
        self.config = config
        self.data_provider = data_provider
        self.utility_manager = utility_manager
        
        # Subscription tracking
        self.active_subscriptions = {}
        self.subscription_history = []
        
        logger.info("DataSubscriptions initialized (mode-agnostic)")
    
    def subscribe_to_data(self, data_type: str, venue: str, symbol: str, 
                         timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Subscribe to data regardless of mode (backtest or live).
        
        Args:
            data_type: Type of data (spot, futures, funding, etc.)
            venue: Venue name (binance, bybit, okx, etc.)
            symbol: Trading symbol (ETHUSDT, BTCUSDT, etc.)
            timestamp: Current timestamp
            
        Returns:
            Dictionary with subscription result
        """
        try:
            # Create subscription key
            subscription_key = f"{data_type}_{venue}_{symbol}"
            
            # Check if already subscribed
            if subscription_key in self.active_subscriptions:
                logger.info(f"Already subscribed to {subscription_key}")
                return {
                    'subscription_key': subscription_key,
                    'status': 'already_subscribed',
                    'timestamp': timestamp
                }
            
            # Subscribe to data
            subscription_result = self._subscribe_to_data_internal(
                data_type, venue, symbol, timestamp
            )
            
            if subscription_result['success']:
                # Add to active subscriptions
                self.active_subscriptions[subscription_key] = {
                    'data_type': data_type,
                    'venue': venue,
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'status': 'active'
                }
                
                # Add to history
                self.subscription_history.append({
                    'subscription_key': subscription_key,
                    'data_type': data_type,
                    'venue': venue,
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'action': 'subscribe',
                    'status': 'success'
                })
                
                logger.info(f"Successfully subscribed to {subscription_key}")
            else:
                # Add to history with failure
                self.subscription_history.append({
                    'subscription_key': subscription_key,
                    'data_type': data_type,
                    'venue': venue,
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'action': 'subscribe',
                    'status': 'failed',
                    'error': subscription_result.get('error', 'Unknown error')
                })
                
                logger.error(f"Failed to subscribe to {subscription_key}: {subscription_result.get('error', 'Unknown error')}")
            
            return {
                'subscription_key': subscription_key,
                'status': 'success' if subscription_result['success'] else 'failed',
                'timestamp': timestamp,
                'result': subscription_result
            }
            
        except Exception as e:
            logger.error(f"Error subscribing to data: {e}")
            return {
                'subscription_key': f"{data_type}_{venue}_{symbol}",
                'status': 'error',
                'timestamp': timestamp,
                'error': str(e)
            }
    
    def unsubscribe_from_data(self, data_type: str, venue: str, symbol: str, 
                             timestamp: pd.Timestamp) -> Dict[str, Any]:
        """
        Unsubscribe from data regardless of mode (backtest or live).
        
        Args:
            data_type: Type of data (spot, futures, funding, etc.)
            venue: Venue name (binance, bybit, okx, etc.)
            symbol: Trading symbol (ETHUSDT, BTCUSDT, etc.)
            timestamp: Current timestamp
            
        Returns:
            Dictionary with unsubscription result
        """
        try:
            # Create subscription key
            subscription_key = f"{data_type}_{venue}_{symbol}"
            
            # Check if subscribed
            if subscription_key not in self.active_subscriptions:
                logger.info(f"Not subscribed to {subscription_key}")
                return {
                    'subscription_key': subscription_key,
                    'status': 'not_subscribed',
                    'timestamp': timestamp
                }
            
            # Unsubscribe from data
            unsubscription_result = self._unsubscribe_from_data_internal(
                data_type, venue, symbol, timestamp
            )
            
            if unsubscription_result['success']:
                # Remove from active subscriptions
                del self.active_subscriptions[subscription_key]
                
                # Add to history
                self.subscription_history.append({
                    'subscription_key': subscription_key,
                    'data_type': data_type,
                    'venue': venue,
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'action': 'unsubscribe',
                    'status': 'success'
                })
                
                logger.info(f"Successfully unsubscribed from {subscription_key}")
            else:
                # Add to history with failure
                self.subscription_history.append({
                    'subscription_key': subscription_key,
                    'data_type': data_type,
                    'venue': venue,
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'action': 'unsubscribe',
                    'status': 'failed',
                    'error': unsubscription_result.get('error', 'Unknown error')
                })
                
                logger.error(f"Failed to unsubscribe from {subscription_key}: {unsubscription_result.get('error', 'Unknown error')}")
            
            return {
                'subscription_key': subscription_key,
                'status': 'success' if unsubscription_result['success'] else 'failed',
                'timestamp': timestamp,
                'result': unsubscription_result
            }
            
        except Exception as e:
            logger.error(f"Error unsubscribing from data: {e}")
            return {
                'subscription_key': f"{data_type}_{venue}_{symbol}",
                'status': 'error',
                'timestamp': timestamp,
                'error': str(e)
            }
    
    def get_active_subscriptions(self) -> Dict[str, Any]:
        """Get all active subscriptions."""
        try:
            return {
                'active_subscriptions': self.active_subscriptions,
                'subscription_count': len(self.active_subscriptions),
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting active subscriptions: {e}")
            return {
                'active_subscriptions': {},
                'subscription_count': 0,
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def get_subscription_history(self) -> Dict[str, Any]:
        """Get subscription history."""
        try:
            return {
                'subscription_history': self.subscription_history,
                'history_count': len(self.subscription_history),
                'mode_agnostic': True
            }
        except Exception as e:
            logger.error(f"Error getting subscription history: {e}")
            return {
                'subscription_history': [],
                'history_count': 0,
                'mode_agnostic': True,
                'error': str(e)
            }
    
    def _subscribe_to_data_internal(self, data_type: str, venue: str, symbol: str, 
                                   timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Internal method to subscribe to data."""
        try:
            # Get data subscription configuration
            subscription_config = self._get_subscription_config(data_type, venue, symbol)
            
            if not subscription_config:
                return {
                    'success': False,
                    'error': f"No subscription config found for {data_type}_{venue}_{symbol}"
                }
            
            # Subscribe based on data type
            if data_type == 'spot':
                return self._subscribe_to_spot_data(venue, symbol, timestamp, subscription_config)
            elif data_type == 'futures':
                return self._subscribe_to_futures_data(venue, symbol, timestamp, subscription_config)
            elif data_type == 'funding':
                return self._subscribe_to_funding_data(venue, symbol, timestamp, subscription_config)
            elif data_type == 'lending':
                return self._subscribe_to_lending_data(venue, symbol, timestamp, subscription_config)
            elif data_type == 'staking':
                return self._subscribe_to_staking_data(venue, symbol, timestamp, subscription_config)
            else:
                return {
                    'success': False,
                    'error': f"Unsupported data type: {data_type}"
                }
                
        except Exception as e:
            logger.error(f"Error in internal subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _unsubscribe_from_data_internal(self, data_type: str, venue: str, symbol: str, 
                                       timestamp: pd.Timestamp) -> Dict[str, Any]:
        """Internal method to unsubscribe from data."""
        try:
            # Get data subscription configuration
            subscription_config = self._get_subscription_config(data_type, venue, symbol)
            
            if not subscription_config:
                return {
                    'success': False,
                    'error': f"No subscription config found for {data_type}_{venue}_{symbol}"
                }
            
            # Unsubscribe based on data type
            if data_type == 'spot':
                return self._unsubscribe_from_spot_data(venue, symbol, timestamp, subscription_config)
            elif data_type == 'futures':
                return self._unsubscribe_from_futures_data(venue, symbol, timestamp, subscription_config)
            elif data_type == 'funding':
                return self._unsubscribe_from_funding_data(venue, symbol, timestamp, subscription_config)
            elif data_type == 'lending':
                return self._unsubscribe_from_lending_data(venue, symbol, timestamp, subscription_config)
            elif data_type == 'staking':
                return self._unsubscribe_from_staking_data(venue, symbol, timestamp, subscription_config)
            else:
                return {
                    'success': False,
                    'error': f"Unsupported data type: {data_type}"
                }
                
        except Exception as e:
            logger.error(f"Error in internal unsubscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_subscription_config(self, data_type: str, venue: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get subscription configuration for data type, venue, and symbol."""
        try:
            # Get venue configuration
            venue_config = self.config.get('venues', {}).get(venue)
            if not venue_config:
                return None
            
            # Get data type configuration
            data_type_config = venue_config.get('data_types', {}).get(data_type)
            if not data_type_config:
                return None
            
            # Get symbol configuration
            symbol_config = data_type_config.get('symbols', {}).get(symbol)
            if not symbol_config:
                return None
            
            return symbol_config
        except Exception as e:
            logger.error(f"Error getting subscription config: {e}")
            return None
    
    def _subscribe_to_spot_data(self, venue: str, symbol: str, timestamp: pd.Timestamp, 
                               config: Dict[str, Any]) -> Dict[str, Any]:
        """Subscribe to spot data."""
        try:
            # Placeholder for actual spot data subscription
            # In real implementation, this would set up WebSocket connections or polling
            logger.info(f"Subscribing to spot data for {venue}_{symbol}")
            
            return {
                'success': True,
                'data_type': 'spot',
                'venue': venue,
                'symbol': symbol,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error subscribing to spot data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _subscribe_to_futures_data(self, venue: str, symbol: str, timestamp: pd.Timestamp, 
                                  config: Dict[str, Any]) -> Dict[str, Any]:
        """Subscribe to futures data."""
        try:
            # Placeholder for actual futures data subscription
            # In real implementation, this would set up WebSocket connections or polling
            logger.info(f"Subscribing to futures data for {venue}_{symbol}")
            
            return {
                'success': True,
                'data_type': 'futures',
                'venue': venue,
                'symbol': symbol,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error subscribing to futures data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _subscribe_to_funding_data(self, venue: str, symbol: str, timestamp: pd.Timestamp, 
                                  config: Dict[str, Any]) -> Dict[str, Any]:
        """Subscribe to funding data."""
        try:
            # Placeholder for actual funding data subscription
            # In real implementation, this would set up WebSocket connections or polling
            logger.info(f"Subscribing to funding data for {venue}_{symbol}")
            
            return {
                'success': True,
                'data_type': 'funding',
                'venue': venue,
                'symbol': symbol,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error subscribing to funding data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _subscribe_to_lending_data(self, venue: str, symbol: str, timestamp: pd.Timestamp, 
                                  config: Dict[str, Any]) -> Dict[str, Any]:
        """Subscribe to lending data."""
        try:
            # Placeholder for actual lending data subscription
            # In real implementation, this would set up WebSocket connections or polling
            logger.info(f"Subscribing to lending data for {venue}_{symbol}")
            
            return {
                'success': True,
                'data_type': 'lending',
                'venue': venue,
                'symbol': symbol,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error subscribing to lending data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _subscribe_to_staking_data(self, venue: str, symbol: str, timestamp: pd.Timestamp, 
                                  config: Dict[str, Any]) -> Dict[str, Any]:
        """Subscribe to staking data."""
        try:
            # Placeholder for actual staking data subscription
            # In real implementation, this would set up WebSocket connections or polling
            logger.info(f"Subscribing to staking data for {venue}_{symbol}")
            
            return {
                'success': True,
                'data_type': 'staking',
                'venue': venue,
                'symbol': symbol,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error subscribing to staking data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _unsubscribe_from_spot_data(self, venue: str, symbol: str, timestamp: pd.Timestamp, 
                                   config: Dict[str, Any]) -> Dict[str, Any]:
        """Unsubscribe from spot data."""
        try:
            # Placeholder for actual spot data unsubscription
            # In real implementation, this would close WebSocket connections or stop polling
            logger.info(f"Unsubscribing from spot data for {venue}_{symbol}")
            
            return {
                'success': True,
                'data_type': 'spot',
                'venue': venue,
                'symbol': symbol,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error unsubscribing from spot data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _unsubscribe_from_futures_data(self, venue: str, symbol: str, timestamp: pd.Timestamp, 
                                      config: Dict[str, Any]) -> Dict[str, Any]:
        """Unsubscribe from futures data."""
        try:
            # Placeholder for actual futures data unsubscription
            # In real implementation, this would close WebSocket connections or stop polling
            logger.info(f"Unsubscribing from futures data for {venue}_{symbol}")
            
            return {
                'success': True,
                'data_type': 'futures',
                'venue': venue,
                'symbol': symbol,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error unsubscribing from futures data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _unsubscribe_from_funding_data(self, venue: str, symbol: str, timestamp: pd.Timestamp, 
                                      config: Dict[str, Any]) -> Dict[str, Any]:
        """Unsubscribe from funding data."""
        try:
            # Placeholder for actual funding data unsubscription
            # In real implementation, this would close WebSocket connections or stop polling
            logger.info(f"Unsubscribing from funding data for {venue}_{symbol}")
            
            return {
                'success': True,
                'data_type': 'funding',
                'venue': venue,
                'symbol': symbol,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error unsubscribing from funding data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _unsubscribe_from_lending_data(self, venue: str, symbol: str, timestamp: pd.Timestamp, 
                                      config: Dict[str, Any]) -> Dict[str, Any]:
        """Unsubscribe from lending data."""
        try:
            # Placeholder for actual lending data unsubscription
            # In real implementation, this would close WebSocket connections or stop polling
            logger.info(f"Unsubscribing from lending data for {venue}_{symbol}")
            
            return {
                'success': True,
                'data_type': 'lending',
                'venue': venue,
                'symbol': symbol,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error unsubscribing from lending data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _unsubscribe_from_staking_data(self, venue: str, symbol: str, timestamp: pd.Timestamp, 
                                      config: Dict[str, Any]) -> Dict[str, Any]:
        """Unsubscribe from staking data."""
        try:
            # Placeholder for actual staking data unsubscription
            # In real implementation, this would close WebSocket connections or stop polling
            logger.info(f"Unsubscribing from staking data for {venue}_{symbol}")
            
            return {
                'success': True,
                'data_type': 'staking',
                'venue': venue,
                'symbol': symbol,
                'timestamp': timestamp
            }
        except Exception as e:
            logger.error(f"Error unsubscribing from staking data: {e}")
            return {
                'success': False,
                'error': str(e)
            }

