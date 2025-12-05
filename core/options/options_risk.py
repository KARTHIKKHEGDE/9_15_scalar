# core/options/options_risk.py
"""
Risk management for options positions
Target: Percentage-based (e.g., 20%)
Stop-loss: Opening price of breakout candle
"""

import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class OptionsRiskManager:
    """
    Manage options-specific risk
    - Target: Percentage-based
    - Stop-loss: Opening price of breakout candle
    """
    
    def __init__(self, portfolio, symbol_manager, config):
        self.portfolio = portfolio
        self.symbol_manager = symbol_manager
        self.config = config
        
        # Target percentage
        self.target_percent = config.get('OPTIONS_TARGET_PERCENT', 20)
        
        # Callback for exit signals
        self.on_exit_callback: Optional[Callable] = None
        
        # Statistics
        self.exits_triggered = 0
        self.target_hits = 0
        self.stoploss_hits = 0
        
        logger.info(f"✓ OptionsRiskManager initialized | Target: {self.target_percent}%")
    
    def set_on_exit_callback(self, callback: Callable):
        """Register callback for exit signals"""
        self.on_exit_callback = callback
        logger.info("✓ Exit callback registered")
    
    def process_tick(self, tick: dict):
        """
        Monitor options positions for target/stop-loss
        
        Args:
            tick: Tick data with instrument_token, last_price, etc.
        """
        token = tick["instrument_token"]
        symbol = self.symbol_manager.get_symbol(token)
        price = tick["last_price"]
        
        if not symbol:
            return
        
        # Check if we have a position
        if not self.portfolio.has_position(symbol):
            return
        
        # Update position with latest price
        self.portfolio.update_position_price(symbol, price)
        
        # Get position
        position = self.portfolio.get_position(symbol)
        if not position:
            return
        
        # Check target
        self._check_target(symbol, price, position)
        
        # Check stop-loss
        self._check_stop_loss(symbol, price, position)
    
    def _check_target(self, symbol: str, price: float, position):
        """
        Check if target is hit (percentage-based)
        
        Args:
            symbol: Option symbol
            price: Current price
            position: Position object
        """
        # Calculate target (percentage-based)
        target = position.entry_price * (1 + self.target_percent / 100)
        
        if price >= target:
            logger.info(f"🎯 TARGET HIT: {symbol} | "
                       f"Entry: {position.entry_price:.2f} | "
                       f"Current: {price:.2f} | "
                       f"Target: {target:.2f} ({self.target_percent}%)")
            
            self.exits_triggered += 1
            self.target_hits += 1
            
            # Fire exit callback
            if self.on_exit_callback:
                self.on_exit_callback(symbol, price, "Target Hit")
    
    def _check_stop_loss(self, symbol: str, price: float, position):
        """
        Check if stop-loss is hit
        Stop-loss = Opening price of breakout candle (stored in position.stoploss)
        
        Args:
            symbol: Option symbol
            price: Current price
            position: Position object
        """
        # Stop-loss is stored in position.stoploss
        # This is the opening price of the breakout candle
        stoploss = position.stoploss
        
        if price <= stoploss:
            logger.info(f"🛑 STOP-LOSS HIT: {symbol} | "
                       f"Entry: {position.entry_price:.2f} | "
                       f"Current: {price:.2f} | "
                       f"SL: {stoploss:.2f}")
            
            self.exits_triggered += 1
            self.stoploss_hits += 1
            
            # Fire exit callback
            if self.on_exit_callback:
                self.on_exit_callback(symbol, price, "Stop-Loss Hit")
    
    def get_stats(self) -> dict:
        """Get risk management statistics"""
        return {
            'exits_triggered': self.exits_triggered,
            'target_hits': self.target_hits,
            'stoploss_hits': self.stoploss_hits
        }
