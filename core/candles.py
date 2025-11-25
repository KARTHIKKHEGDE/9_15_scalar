# core/candles.py
"""
Ultra-low-latency 1-minute candle builder
Optimized for high-frequency Zerodha tick streaming
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Callable
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)


# ============================================================
#                   CANDLE STRUCTURE
# ============================================================
@dataclass
class Candle:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    def range_percent(self) -> float:
        if self.low > 0:
            return ((self.high - self.low) / self.low) * 100
        return 0


# ============================================================
#                   CANDLE BUILDER CLASS
# ============================================================
class CandleBuilder:
    """
    Ultra-fast 1-minute candle builder.

    - Maintains active candles (current minute)
    - Closes candles when minute changes
    - Uses cumulative volume to compute per-minute volume
    """

    def __init__(self, symbol_manager):
        self.symbol_manager = symbol_manager

        # token → active candle data (dict)
        self.active_candles: Dict[int, dict] = {}

        # token → last completed candle
        self.completed_candles: Dict[int, Candle] = {}

        # token → previous cumulative volume (for volume delta calc)
        self.previous_volume: Dict[int, int] = {}

        # Thread safety
        self.lock = threading.Lock()

        # Callback
        self.on_candle_close: Optional[Callable[[Candle], None]] = None

        # Current minute tracker
        self.current_minute: Optional[datetime] = None

    # --------------------------------------------------------
    # Set callback
    # --------------------------------------------------------
    def set_on_candle_close_callback(self, callback: Callable[[Candle], None]):
        self.on_candle_close = callback

    # --------------------------------------------------------
    # Process incoming ticks
    # --------------------------------------------------------
    def process_tick(self, tick: dict):
        """
        Process a single Zerodha tick.
        tick contains:
        - instrument_token
        - last_price
        - volume_traded (cumulative)
        - exchange_timestamp / last_trade_time
        """
        token = tick["instrument_token"]
        price = tick["last_price"]

        # Zerodha timestamps
        timestamp = tick.get("exchange_timestamp") or tick.get("last_trade_time")
        if not timestamp:
            return

        # The minute the tick belongs to
        minute_start = timestamp.replace(second=0, microsecond=0)

        with self.lock:
            # --------------------------------------------------------
            # Detect minute change → close all candles
            # --------------------------------------------------------
            if self.current_minute and minute_start > self.current_minute:
                self._close_all_candles(self.current_minute)

            self.current_minute = minute_start

            # --------------------------------------------------------
            # New Candle
            # --------------------------------------------------------
            if token not in self.active_candles:

                symbol = self.symbol_manager.get_symbol(token)

                # Debug logging removed for performance
                # logger.debug(f"[CANDLE START] {symbol} @ {price}")

                cumulative_volume = tick.get("volume_traded", 0)
                prev_vol = self.previous_volume.get(token, 0)

                candle_volume = max(cumulative_volume - prev_vol, 0)

                self.active_candles[token] = {
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": candle_volume,
                    "cumulative_volume": cumulative_volume,
                    "first_tick_time": timestamp,
                }

            # --------------------------------------------------------
            # Update Existing Candle
            # --------------------------------------------------------
            else:
                candle = self.active_candles[token]

                candle["high"] = max(candle["high"], price)
                candle["low"] = min(candle["low"], price)
                candle["close"] = price

                candle["cumulative_volume"] = tick.get("volume_traded", 0)

    # --------------------------------------------------------
    # Close all candles (at minute change)
    # --------------------------------------------------------
    def _close_all_candles(self, minute: datetime):

        for token, candle_data in list(self.active_candles.items()):
            symbol = self.symbol_manager.get_symbol(token)
            if not symbol:
                continue

            # Debug logging removed for performance
            # logger.debug(f"[CANDLE CLOSE] {symbol}")

            completed = Candle(
                symbol=symbol,
                timestamp=minute,
                open=candle_data["open"],
                high=candle_data["high"],
                low=candle_data["low"],
                close=candle_data["close"],
                volume=candle_data["volume"],
            )

            self.completed_candles[token] = completed
            self.previous_volume[token] = candle_data["cumulative_volume"]

            # Fire callback
            if self.on_candle_close:
                try:
                    self.on_candle_close(completed)
                except Exception as e:
                    logger.error(f"Error in candle close callback for {symbol}: {e}")

        # Clear candles for new minute
        self.active_candles.clear()

    # --------------------------------------------------------
    # Public helpers
    # --------------------------------------------------------
    def get_candle(self, symbol: str) -> Optional[Candle]:
        token = self.symbol_manager.get_token(symbol)
        if token:
            return self.completed_candles.get(token)
        return None

    def get_active_candle_data(self, symbol: str) -> Optional[dict]:
        token = self.symbol_manager.get_token(symbol)
        if token:
            with self.lock:
                return self.active_candles.get(token)
        return None

    def get_current_candle_open(self, symbol: str) -> Optional[float]:
        token = self.symbol_manager.get_token(symbol)
        if not token:
            return None

        with self.lock:
            candle = self.active_candles.get(token)
            if candle:
                return candle["open"]

        return None

    def force_close_candles(self):
        if self.current_minute:
            with self.lock:
                self._close_all_candles(self.current_minute)
