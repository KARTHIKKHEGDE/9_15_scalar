# core/options/options_breakout.py
"""
Detect breakouts on marked NIFTY FUT candles
RED candle → Price crosses LOW → Signal PUT
GREEN candle → Price crosses HIGH → Signal CALL
"""

import logging
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class OptionsBreakoutEngine:
    """
    Monitor marked candles for breakouts
    Trigger CALL/PUT signals based on breakout direction
    """
    
    def __init__(self, marker, symbol_manager, config, candle_builder, options_chain_manager):
        self.marker = marker
        self.symbol_manager = symbol_manager
        self.config = config
        self.candle_builder = candle_builder
        self.options_chain = options_chain_manager
        
        # Callback for breakout signal
        self.on_breakout_callback: Optional[Callable] = None
        
        # Track triggered breakouts to avoid duplicates
        self.breakout_triggered: set = set()
        
        # Track last prices for dry-run order execution
        self.last_prices: dict = {}  # symbol -> last_price
        
        # Statistics
        self.breakouts_detected = 0
        self.call_signals = 0
        self.put_signals = 0
        
        logger.info("✓ OptionsBreakoutEngine initialized")
    
    def set_on_breakout_callback(self, callback: Callable):
        """Register callback for breakout signals"""
        self.on_breakout_callback = callback
        logger.info("✓ Breakout callback registered")
    
    def process_tick(self, tick: dict):
        """
        Process each tick to check for breakouts
        Only processes NIFTY FUT ticks
        
        Args:
            tick: Tick data with instrument_token, last_price, etc.
        """
        # Get symbol from tick
        token = tick.get("instrument_token")
        symbol = self.symbol_manager.get_symbol(token)
        
        # Only process NIFTY FUT ticks
        nifty_fut_symbol = self.config.get('OPTIONS_NIFTY_FUT_SYMBOL')
        if symbol != nifty_fut_symbol:
            return  # Ignore non-NIFTY FUT ticks
        
        price = tick["last_price"]
        
        # Get all marked candles
        marked_candles = self.marker.get_all_marked_candles()
        
        if not marked_candles:
            return
        
        # Check each marked candle for breakout
        for timestamp, marked_candle in list(marked_candles.items()):
            # Skip if already triggered
            if timestamp in self.breakout_triggered:
                continue
            
            # Check breakout based on direction
            if marked_candle.is_red():
                # RED candle: Check if price crossed LOW
                if price < marked_candle.low:
                    self._trigger_breakout("PUT", price, marked_candle, timestamp)
            
            elif marked_candle.is_green():
                # GREEN candle: Check if price crossed HIGH
                if price > marked_candle.high:
                    self._trigger_breakout("CALL", price, marked_candle, timestamp)
    
    def _trigger_breakout(self, option_type: str, breakout_price: float, 
                         marked_candle, timestamp: datetime):
        """
        Trigger breakout signal
        
        Args:
            option_type: "CALL" or "PUT"
            breakout_price: Price at which breakout occurred (NIFTY FUT price)
            marked_candle: The marked candle that was broken
            timestamp: Timestamp of marked candle
        """
        # Mark as triggered
        self.breakout_triggered.add(timestamp)
        self.breakouts_detected += 1
        
        if option_type == "CALL":
            self.call_signals += 1
        else:
            self.put_signals += 1
        
        logger.info(f"🔥 BREAKOUT DETECTED: {option_type} | "
                   f"Breakout Price: {breakout_price:.2f} | "
                   f"Marked Candle: {marked_candle.direction} @ {timestamp.strftime('%H:%M')} | "
                   f"High: {marked_candle.high:.2f} | Low: {marked_candle.low:.2f}")
        
        # Get ATM strike based on current NIFTY FUT price
        atm_strike = self.options_chain.get_atm_strike(breakout_price)
        
        # Determine direction
        direction = "BULLISH" if option_type == "CALL" else "BEARISH"
        
        # Get option symbol
        option_symbol = self.options_chain.get_option_symbol(atm_strike, option_type)
        
        # Get current option price (entry price)
        entry_price = self.options_chain.get_option_price(option_symbol)
        
        if entry_price == 0:
            logger.warning(f"Could not get option price for {option_symbol}, using fallback")
            # Fallback: estimate based on typical premium
            entry_price = 100.0  # Fallback value
        
        logger.info(f"📊 OPTIONS SIGNAL: {direction} {option_type} | "
                   f"Strike: {atm_strike} | Symbol: {option_symbol} | "
                   f"Entry Price: {entry_price:.2f} | Stop-Loss: {marked_candle.open:.2f}")
        
        # Fire callback with correct signature
        if self.on_breakout_callback:
            try:
                # Pass: direction, strike, option_type, entry_price, stoploss
                # Stop-loss = Opening price of the breakout candle
                stoploss = marked_candle.open
                self.on_breakout_callback(direction, atm_strike, option_type, entry_price, stoploss)
            except Exception as e:
                logger.error(f"Error in breakout callback: {e}", exc_info=True)
        
        # Remove marked candle (breakout triggered)
        self.marker.remove_marked_candle(timestamp)
    
    def get_stats(self) -> dict:
        """Get breakout statistics"""
        return {
            'breakouts_detected': self.breakouts_detected,
            'call_signals': self.call_signals,
            'put_signals': self.put_signals,
            'currently_monitoring': len(self.marker.get_all_marked_candles()),
            'breakouts_triggered': len(self.breakout_triggered)
        }
    
    def get_last_price(self, symbol: str) -> Optional[float]:
        """
        Get last known price for a symbol
        Used by DryRunOrderExecutor for realistic price simulation
        
        Args:
            symbol: Symbol to get price for
            
        Returns:
            Last price or None if not available
        """
        return self.last_prices.get(symbol)
