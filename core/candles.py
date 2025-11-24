# core/candles.py
"""
Ultra-low-latency 1-minute candle builder
Optimized for sub-second tick processing
"""
import logging
from datetime import datetime, time
from typing import Dict, Optional, Callable
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)

@dataclass
class Candle:
    """Immutable candle data structure"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    def range_percent(self) -> float:
        """Calculate candle range as percentage"""
        if self.low > 0:
            return ((self.high - self.low) / self.low) * 100
        return 0

class CandleBuilder:
    """
    Ultra-fast 1-minute candle builder
    Uses in-memory structures for O(1) access
    """
    
    def __init__(self, symbol_manager):
        self.symbol_manager = symbol_manager
        
        # Active candles being built (token -> current candle data)
        self.active_candles: Dict[int, dict] = {}
        
        # Lock for thread-safe updates
        self.lock = threading.Lock()
        
        # Completed candles buffer (token -> last completed candle)
        self.completed_candles: Dict[int, Candle] = {}
        
        # Callback for when candle closes
        self.on_candle_close: Optional[Callable[[Candle], None]] = None
        
        # Current minute tracker
        self.current_minute: Optional[time] = None

        self.previous_volume: Dict[int, int] = {}  # token -> cumulative volume
    
    
    def set_on_candle_close_callback(self, callback: Callable[[Candle], None]):
        """Set callback function to be called when candle closes"""
        self.on_candle_close = callback
    
    def process_tick(self, tick: dict):  # ← FIX INDENTATION (inside class)
        """
        Process incoming tick with minimal latency
        tick format: {
            'instrument_token': int,
            'last_price': float,
            'volume': int (CUMULATIVE since market open),
            'exchange_timestamp': datetime,  # Zerodha uses this key
            ...
        }
        """
        token = tick['instrument_token']
        price = tick['last_price']
        volume = tick.get('volume_traded', 0)  # Cumulative volume since 9:15 AM
        # Zerodha WebSocket uses 'exchange_timestamp' or 'last_trade_time'
        timestamp = tick.get('exchange_timestamp') or tick.get('last_trade_time')
        # Get current minute
        current_min = timestamp.replace(second=0, microsecond=0)
        
        with self.lock:
            # Check if minute has changed (candle close)
            if self.current_minute and current_min > self.current_minute:
                self._close_all_candles(self.current_minute)
            
            self.current_minute = current_min
            
            # Update or create candle
            if token not in self.active_candles:
                # NEW CANDLE - Calculate volume for this minute
                prev_vol = self.previous_volume.get(token, 0)
                candle_volume = volume - prev_vol  # Delta from previous candle
                
                self.active_candles[token] = {
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price,
                    'volume': candle_volume,       # Store this minute's volume
                    'cumulative_volume': volume,   # Also store cumulative
                    'first_tick_time': timestamp
                }
            else:
                # UPDATE EXISTING CANDLE
                candle = self.active_candles[token]
                candle['high'] = max(candle['high'], price)
                candle['low'] = min(candle['low'], price)
                candle['close'] = price
                candle['cumulative_volume'] = volume  # Keep updating cumulative
                # Note: candle['volume'] stays as initially calculated (delta)
    
    def _close_all_candles(self, minute: datetime):
        """
        Close all candles for the completed minute
        Called when new minute starts
        """
        for token, candle_data in list(self.active_candles.items()):
            symbol = self.symbol_manager.get_symbol(token)
            if not symbol:
                continue
            
            # Create completed candle
            completed = Candle(
                symbol=symbol,
                timestamp=minute,
                open=candle_data['open'],
                high=candle_data['high'],
                low=candle_data['low'],
                close=candle_data['close'],
                volume=candle_data['volume']
            )
            
            # Store in buffer
            self.completed_candles[token] = completed
            self.previous_volume[token] = candle_data['cumulative_volume']
            
            # Trigger callback
            if self.on_candle_close:
                try:
                    self.on_candle_close(completed)
                except Exception as e:
                    logger.error(f"Error in candle close callback for {symbol}: {e}")
        
        # Clear active candles for next minute
        self.active_candles.clear()
        logger.debug(f"Closed {len(self.completed_candles)} candles for minute {minute.strftime('%H:%M')}")
    
    def get_candle(self, symbol: str) -> Optional[Candle]:
        """Get last completed candle for symbol - O(1)"""
        token = self.symbol_manager.get_token(symbol)
        if token:
            return self.completed_candles.get(token)
            # Trigger callback
        if self.on_candle_close:
            try:
                self.on_candle_close(completed)
            except Exception as e:
                    logger.error(f"Error in candle close callback for {symbol}: {e}")
        
        # Clear active candles for next minute
        self.active_candles.clear()
        logger.debug(f"Closed {len(self.completed_candles)} candles for minute {minute.strftime('%H:%M')}")
    
    def get_candle(self, symbol: str) -> Optional[Candle]:
        """Get last completed candle for symbol - O(1)"""
        token = self.symbol_manager.get_token(symbol)
        if token:
            return self.completed_candles.get(token)
        return None
    
    def get_active_candle_data(self, symbol: str) -> Optional[dict]:
        """Get current building candle data - O(1)"""
        token = self.symbol_manager.get_token(symbol)
        if token:
            with self.lock:
                return self.active_candles.get(token)
        return None
    
    def get_current_candle_open(self, symbol: str) -> Optional[float]:
        """
        Get the open price of the currently building candle
        Used for setting stop-loss at breakout candle's open
        Returns None if no active candle exists
        """
        token = self.symbol_manager.get_token(symbol)
        if not token:
            return None
        
        with self.lock:
            candle_data = self.active_candles.get(token)
            if candle_data:
                return candle_data['open']
    
        return None
    
    def force_close_candles(self):
        """Force close all active candles (for testing/emergency)"""
        if self.current_minute:
            with self.lock:
                self._close_all_candles(self.current_minute)
    