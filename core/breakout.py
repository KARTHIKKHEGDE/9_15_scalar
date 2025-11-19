# core/breakout.py
"""
Ultra-fast breakout detection and entry execution
Millisecond-level latency for order placement
"""
import logging
from typing import Dict, Optional, Callable
from datetime import datetime
import threading
from core.candles import CandleBuilder

logger = logging.getLogger(__name__)

class BreakoutEngine:
    """
    Monitors marked symbols for breakout
    Executes entries with minimal latency
    """
    
    def __init__(self, marker, symbol_manager, config, candle_builder):
        self.marker = marker
        self.symbol_manager = symbol_manager
        self.config = config
        self.candle_builder = candle_builder  # NEW: Add candle builder reference
        
        # Track last price for each marked symbol (token -> price)
        self.last_prices: Dict[int, float] = {}
        self.lock = threading.Lock()
        
        # Breakout detection state
        self.breakout_triggered: Dict[str, bool] = {}  # symbol -> triggered
        
        # Callback for entry execution
        self.on_breakout: Optional[Callable[[str, float, float], None]] = None
        
        # Stats
        self.breakouts_detected = 0
    
    def set_on_breakout_callback(self, callback: Callable[[str, float, float], None]):
        """
        Set callback for breakout execution
        callback(symbol, entry_price, stoploss_price)
        """
        self.on_breakout = callback
    
    def process_tick(self, tick: dict):
        """
        Process tick for breakout detection
        ULTRA LOW LATENCY - called on every tick
        """
        token = tick['instrument_token']
        price = tick['last_price']
        
        # Get symbol
        symbol = self.symbol_manager.get_symbol(token)
        if not symbol:
            return
        
        # Only monitor marked symbols
        if not self.marker.is_marked(symbol):
            return
        
        # Check if already triggered
        if symbol in self.breakout_triggered:
            return
        
        # Update last price (for monitoring)
        with self.lock:
            self.last_prices[token] = price
        
        # Get breakout level
        breakout_level = self.marker.get_breakout_level(symbol)
        
        # BREAKOUT DETECTION
        if price >= breakout_level:
            self._trigger_breakout(symbol, price)
    
def _trigger_breakout(self, symbol: str, entry_price: float):
    """
    Trigger breakout entry
    CRITICAL: This must execute FAST
    """
    # Mark as triggered to prevent duplicate entries
    self.breakout_triggered[symbol] = True
    self.breakouts_detected += 1
    
    # Get stop loss from CURRENT breakout candle's open
    stoploss = self.candle_builder.get_current_candle_open(symbol)
    
    # Fallback: If current candle open not available, use 9:15 candle open
    if stoploss is None or stoploss == 0:
        stoploss = self.marker.get_stoploss_level(symbol)
        logger.warning(f"{symbol}: Using 9:15 candle open as SL (breakout candle open not available)")
    
    # Get 9:15 candle details for logging
    first_candle = self.marker.get_first_candle(symbol)
    
    logger.info(
        f"🚀 BREAKOUT: {symbol} @ {entry_price:.2f} | "
        f"SL: {stoploss:.2f} (Breakout Candle Open) | "
        f"9:15 High: {first_candle.high:.2f}"
    )
    
    # Execute entry via callback (non-blocking)
    if self.on_breakout:
        try:
            self.on_breakout(symbol, entry_price, stoploss)
        except Exception as e:
            logger.error(f"Error in breakout callback for {symbol}: {e}")
    
    # Unmark symbol (no longer need to monitor)
    self.marker.unmark_symbol(symbol)
    def get_last_price(self, symbol: str) -> Optional[float]:
        """Get last known price for symbol"""
        token = self.symbol_manager.get_token(symbol)
        if token:
            return self.last_prices.get(token)
        return None
    
    def is_breakout_triggered(self, symbol: str) -> bool:
        """Check if breakout already triggered for symbol"""
        return symbol in self.breakout_triggered
    
    def get_stats(self) -> dict:
        """Get breakout statistics"""
        return {
            'breakouts_detected': self.breakouts_detected,
            'currently_monitoring': len(self.marker.get_all_marked_symbols()),
            'breakouts_triggered': len(self.breakout_triggered)
        }
    
    def reset(self):
        """Reset for next trading day"""
        with self.lock:
            self.last_prices.clear()
            self.breakout_triggered.clear()
            self.breakouts_detected = 0