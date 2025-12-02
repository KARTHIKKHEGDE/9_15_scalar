# core/marker.py
"""
Mark qualifying stocks at 9:15 candle close
Optimized for instant decision-making
"""
import logging
from typing import Set, Dict
from datetime import time
import threading
from core.candles import Candle

logger = logging.getLogger(__name__)

class StockMarker:
    """
    Marks stocks that qualify for breakout trading
    Uses thread-safe sets for O(1) lookups
    """
    
    def __init__(self, historical_manager, config):
        self.historical_manager = historical_manager
        self.config = config
        
        # Marked symbols (thread-safe set)
        self.marked_symbols: Set[str] = set()
        self.lock = threading.Lock()
        
        # Store 9:15 candles for marked symbols
        self.marked_candles: Dict[str, Candle] = {}
        
        # Track marking stats
        self.total_evaluated = 0
        self.total_marked = 0
    
    def get_total_marked_count(self) -> int:
        """
        Get total marked count (including already triggered)
        Use marked_candles dict which keeps all marked stocks even after unmark
        """
        return len(self.marked_candles)  # This never decreases!
    
    def evaluate_and_mark(self, candle: Candle) -> bool:
        """
        Evaluate if candle qualifies for marking
        Returns True if marked, False otherwise
        
        Criteria:
        1. Volume > X times 14-day average
        2. Within time window (9:15-9:16)
        """
        self.total_evaluated += 1
        
        # Check if it's the 9:15 candle
        candle_time = candle.timestamp.time()
        if not (time(9, 15) <= candle_time < time(9, 16)):
            return False
        
        symbol = candle.symbol
        
        # Get historical data
        avg_volume = self.historical_manager.get_avg_volume(symbol)
        if avg_volume == 0:
            logger.debug(f"{symbol}: No historical data available")
            return False
        
        # Criterion 1: Volume check
        volume_ratio = candle.volume / avg_volume
        if volume_ratio < self.config['VOLUME_MULTIPLIER']:
            logger.debug(f"{symbol}: Volume {volume_ratio:.2f}x (need {self.config['VOLUME_MULTIPLIER']}x)")
            return False
        
        # Criterion 2: Candle must be GREEN (bullish)
        if candle.close <= candle.open:
            logger.debug(f"{symbol}: Red/Flat candle (Open: {candle.open:.2f}, Close: {candle.close:.2f})")
            return False
        
        # All criteria met - MARK IT!
        with self.lock:
            self.marked_symbols.add(symbol)
            self.marked_candles[symbol] = candle
            self.total_marked += 1
        
        logger.info(f"✓ MARKED: {symbol} | Vol: {volume_ratio:.2f}x | High: {candle.high:.2f}")
        return True
    
    def is_marked(self, symbol: str) -> bool:
        """O(1) check if symbol is marked"""
        return symbol in self.marked_symbols
    
    def get_marked_candle(self, symbol: str) -> Candle:
        """Get the 9:15 candle for marked symbol - O(1)"""
        return self.marked_candles.get(symbol)
    
    def get_all_marked_symbols(self) -> Set[str]:
        """Get all marked symbols"""
        with self.lock:
            return self.marked_symbols.copy()
    
    def get_breakout_level(self, symbol: str) -> float:
        """
        Get breakout price level for symbol
        Returns high of 9:15 candle + buffer
        """
        candle = self.marked_candles.get(symbol)
        if not candle:
            return 0
        
        buffer = candle.high * (self.config['BREAKOUT_BUFFER_PERCENT'] / 100)
        return candle.high + buffer
    
    def get_stoploss_level(self, symbol: str) -> float:
        """Get stop-loss level (open of 9:15 candle)"""
        candle = self.marked_candles.get(symbol)
        if not candle:
            return 0
        return candle.open
    
    def unmark_symbol(self, symbol: str):
        """Remove symbol from marked list (after entry or rejection)"""
        with self.lock:
            self.marked_symbols.discard(symbol)
    
    def get_stats(self) -> dict:
        """Get marking statistics"""
        return {
            'total_evaluated': self.total_evaluated,
            'total_marked': self.total_marked,
            'currently_marked': len(self.marked_symbols)
        }
    
    def reset(self):
        """Reset for next trading day"""
        with self.lock:
            self.marked_symbols.clear()
            self.marked_candles.clear()
            self.total_evaluated = 0
            self.total_marked = 0