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
        
        IMPORTANT: Stop-loss is based on NIFTY FUT price, not option price!
        - Target: Percentage-based on option price
        - Stop-loss: NIFTY FUT price crosses breakout candle's opening price
        
        Args:
            tick: Tick data with instrument_token, last_price, etc.
        """
        token = tick["instrument_token"]
        symbol = self.symbol_manager.get_symbol(token)
        price = tick["last_price"]
        
        if not symbol:
            return
        
        # Get NIFTY FUT symbol
        nifty_fut_symbol = self.config.get('OPTIONS_NIFTY_FUT_SYMBOL')
        
        # Case 1: This is a NIFTY FUT tick - check stop-loss for all option positions
        if symbol == nifty_fut_symbol:
            fut_price = price
            # Check all positions for stop-loss
            for pos_symbol in list(self.portfolio.positions.keys()):
                # Check if this is an option position (contains CE or PE)
                if 'CE' in pos_symbol or 'PE' in pos_symbol:
                    position = self.portfolio.get_position(pos_symbol)
                    if position:
                        # Stop-loss is NIFTY FUT price
                        self._check_stop_loss_fut(pos_symbol, fut_price, position)
        
        # Case 2: This is an option tick - check target and update position price
        elif 'CE' in symbol or 'PE' in symbol:
            # Check if we have a position in this option
            if not self.portfolio.has_position(symbol):
                return
            
            # Update position with latest option price
            self.portfolio.update_position_price(symbol, price)
            
            # Get position
            position = self.portfolio.get_position(symbol)
            if not position:
                return
            
            # Check target (based on option price)
            self._check_target(symbol, price, position)
    
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
    
    def _check_stop_loss_fut(self, symbol: str, fut_price: float, position):
        """
        Check if stop-loss is hit based on NIFTY FUT price
        Stop-loss = Opening price of breakout candle (NIFTY FUT price)
        
        IMPORTANT LOGIC:
        - PUT (bearish): Breakout when price falls. SL when price RISES back to candle open.
        - CALL (bullish): Breakout when price rises. SL when price FALLS back to candle open.
        
        Args:
            symbol: Option symbol (e.g., NIFTY26DEC2424500PE or NIFTY26DEC2424500CE)
            fut_price: Current NIFTY FUT price
            position: Position object
        """
        # Stop-loss is stored in position.stoploss (breakout candle's opening price)
        stoploss = position.stoploss
        
        # Determine if this is a CALL or PUT based on symbol
        is_put = 'PE' in symbol
        is_call = 'CE' in symbol
        
        # Check if NIFTY FUT crossed the stop-loss level
        stop_loss_hit = False
        
        if is_put:
            # PUT: Stop-loss when NIFTY FUT RISES back to or above the candle open
            stop_loss_hit = fut_price >= stoploss
        elif is_call:
            # CALL: Stop-loss when NIFTY FUT FALLS back to or below the candle open
            stop_loss_hit = fut_price <= stoploss
        
        if stop_loss_hit:
            # Get current option price for exit
            try:
                # We need to get the current option LTP
                # For now, we'll use the last updated price from the position
                option_price = position.current_price
                
                if option_price == 0:
                    logger.warning(f"Option price not available for {symbol}, using entry price")
                    option_price = position.entry_price
                
                option_type = "PUT" if is_put else "CALL"
                logger.info(f"🛑 STOP-LOSS HIT: {symbol} ({option_type}) | "
                           f"NIFTY FUT: {fut_price:.2f} crossed SL: {stoploss:.2f} | "
                           f"Option Entry: {position.entry_price:.2f} | "
                           f"Option Exit: {option_price:.2f}")
                
                self.exits_triggered += 1
                self.stoploss_hits += 1
                
                # Fire exit callback with option price
                if self.on_exit_callback:
                    self.on_exit_callback(symbol, option_price, "Stop-Loss Hit")
            except Exception as e:
                logger.error(f"Error processing stop-loss for {symbol}: {e}")
    
    def get_stats(self) -> dict:
        """Get risk management statistics"""
        return {
            'exits_triggered': self.exits_triggered,
            'target_hits': self.target_hits,
            'stoploss_hits': self.stoploss_hits
        }
