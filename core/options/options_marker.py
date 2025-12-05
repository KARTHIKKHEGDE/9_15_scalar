# core/options/options_marker.py
"""
Mark NIFTY FUT candles based on volume multiplier
Tracks candle direction (RED/GREEN) for breakout detection
"""

import logging
from datetime import datetime, time
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MarkedCandle:
    """Marked candle with direction"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    direction: str  # "RED" or "GREEN"
    
    def is_red(self) -> bool:
        return self.direction == "RED"
    
    def is_green(self) -> bool:
        return self.direction == "GREEN"


class OptionsMarker:
    """
    Mark NIFTY FUT candles based on volume condition
    Similar to StockMarker but for options trading
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.volume_multiplier = config.get('OPTIONS_VOLUME_MULTIPLIER', 1.5)
        
        # Marked candles (timestamp → MarkedCandle)
        self.marked_candles: Dict[datetime, MarkedCandle] = {}
        
        # Statistics
        self.total_evaluated = 0
        self.total_marked = 0
        self.red_marked = 0
        self.green_marked = 0
        
        logger.info(f"✓ OptionsMarker initialized | Volume Multiplier: {self.volume_multiplier}x")
    
    def evaluate_and_mark(self, candle) -> Optional[MarkedCandle]:
        """
        Evaluate candle and mark if volume condition is met
        
        Args:
            candle: Candle object from CandleBuilder
            
        Returns:
            MarkedCandle if marked, None otherwise
        """
        self.total_evaluated += 1
        
        # Get previous candle volume (for comparison)
        # For simplicity, we'll use a rolling average or just mark based on absolute volume
        # You can enhance this by tracking historical volumes
        
        # Check volume condition
        # For now, we'll mark if volume is significant (you can add historical comparison)
        if self._should_mark(candle):
            # Determine direction
            direction = "RED" if candle.close < candle.open else "GREEN"
            
            # Create marked candle
            marked = MarkedCandle(
                timestamp=candle.timestamp,
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume,
                direction=direction
            )
            
            # Store marked candle
            self.marked_candles[candle.timestamp] = marked
            self.total_marked += 1
            
            if direction == "RED":
                self.red_marked += 1
            else:
                self.green_marked += 1
            
            logger.info(f"✓ MARKED: {direction} candle @ {candle.timestamp.strftime('%H:%M')} | "
                       f"O:{candle.open:.2f} H:{candle.high:.2f} L:{candle.low:.2f} C:{candle.close:.2f} | "
                       f"Vol:{candle.volume:,}")
            
            return marked
        
        return None
    
    def _should_mark(self, candle) -> bool:
        """
        Check if candle should be marked
        
        For now, using simple volume threshold
        You can enhance this with historical volume comparison
        """
        # Simple threshold: Mark if volume > 100,000 (adjust based on NIFTY FUT typical volume)
        # Or you can implement historical average comparison like in StockMarker
        
        # For better implementation, you'd want to:
        # 1. Track previous candle volumes
        # 2. Calculate rolling average
        # 3. Compare current volume against average * multiplier
        
        # Simple implementation:
        threshold_volume = 50000  # Adjust based on NIFTY FUT typical volume
        return candle.volume >= threshold_volume * self.volume_multiplier
    
    def get_marked_candle(self, timestamp: datetime) -> Optional[MarkedCandle]:
        """Get marked candle by timestamp"""
        return self.marked_candles.get(timestamp)
    
    def get_all_marked_candles(self) -> Dict[datetime, MarkedCandle]:
        """Get all marked candles"""
        return self.marked_candles.copy()
    
    def remove_marked_candle(self, timestamp: datetime):
        """Remove marked candle (after breakout triggered)"""
        if timestamp in self.marked_candles:
            del self.marked_candles[timestamp]
    
    def get_stats(self) -> dict:
        """Get marking statistics"""
        return {
            'total_evaluated': self.total_evaluated,
            'total_marked': self.total_marked,
            'red_marked': self.red_marked,
            'green_marked': self.green_marked,
            'currently_marked': len(self.marked_candles)
        }
