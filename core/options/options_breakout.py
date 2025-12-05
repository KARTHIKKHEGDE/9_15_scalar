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
    
    def __init__(self, marker, symbol_manager, config, candle_builder):
        self.marker = marker
        self.symbol_manager = symbol_manager
        self.config = config
        self.candle_builder = candle_builder
        
        # Callback for breakout signal
        self.on_breakout_callback: Optional[Callable] = None
        
        # Track triggered breakouts to avoid duplicates
        self.breakout_triggered: set = set()
        
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
        
        Args:
            tick: Tick data with instrument_token, last_price, etc.
        """
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
            breakout_price: Price at which breakout occurred
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
        
        # Fire callback
        if self.on_breakout_callback:
            try:
                # Pass: option_type, breakout_price, marked_candle
                self.on_breakout_callback(option_type, breakout_price, marked_candle)
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
