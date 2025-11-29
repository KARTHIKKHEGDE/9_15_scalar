# core/historical.py
"""
Ultra-fast historical data fetching with rate limiting (single-threaded)
Fetches 9:15 AM 1-minute candle data for volume comparison
"""
import logging
from datetime import datetime, timedelta
from typing import Dict
import numpy as np
import time
from config.settings import API_RATE_LIMIT

logger = logging.getLogger(__name__)

class HistoricalDataManager:
    """Fetches 9:15 AM 1-minute candle data and calculates 14-day averages (single-threaded)"""

    def __init__(self, kite, symbol_manager):
        self.kite = kite
        self.symbol_manager = symbol_manager
        self.avg_volumes: Dict[str, float] = {}  # symbol -> 14-day avg volume of 9:15 candle

    def fetch_single_symbol_data(self, symbol: str, token: int, days: int) -> tuple:
        """
        Fetch 9:15 AM 1-minute candle data for the last N days.
        Returns (symbol, avg_volume_of_915_candle)
        Calculates average volume of ONLY the 9:15-9:16 candle over last N trading days.
        """
        try:
            to_date = datetime.now().date()
            from_date = to_date - timedelta(days=days + 30)  # Extra buffer for weekends/holidays

            # Fetch 1-minute candle data
            data = self.kite.historical_data(
                instrument_token=token,
                from_date=from_date,
                to_date=to_date,
                interval='minute'
            )

            if not data:
                logger.warning(f"{symbol}: No historical data available")
                return (symbol, 0)

            # Filter for only 9:15 AM candles (9:15:00 to 9:16:00)
            nine_fifteen_candles = []
            for candle in data:
                candle_time = candle['date'].time()
                # Check if candle is the 9:15 candle
                if candle_time.hour == 9 and candle_time.minute == 15:
                    nine_fifteen_candles.append(candle)

            if not nine_fifteen_candles:
                logger.warning(f"{symbol}: No 9:15 candles found in historical data")
                return (symbol, 0)

            # Use last N days of 9:15 candles
            recent_915_candles = nine_fifteen_candles[-days:]

            if len(recent_915_candles) < days:
                logger.warning(f"{symbol}: Only {len(recent_915_candles)} 9:15 candles available (requested {days})")

            # Calculate average volume of 9:15 candles
            volumes = [candle['volume'] for candle in recent_915_candles]
            avg_volume = np.mean(volumes) if volumes else 0

            logger.debug(f"{symbol}: Found {len(recent_915_candles)} 9:15 candles, avg volume: {avg_volume:.0f}")

            return (symbol, avg_volume)

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return (symbol, 0)

    def fetch_all_historical_data(self, days: int = 14):
        """
        Fetch 9:15 candle data for all symbols sequentially (single-threaded)
        Calculates average volume of 9:15 candle over last N trading days
        Respects API rate limit using time.sleep
        """
        logger.info(f"Fetching {days}-day 9:15 candle data for {len(self.symbol_manager.symbols)} symbols...")

        start_time = datetime.now()
        success_count = 0

        for symbol in self.symbol_manager.symbols:
            token = self.symbol_manager.get_token(symbol)
            symbol, avg_volume = self.fetch_single_symbol_data(symbol, token, days)

            # Respect API rate limit
            time.sleep(1 / API_RATE_LIMIT)

            if avg_volume > 0:
                self.avg_volumes[symbol] = avg_volume
                success_count += 1

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"9:15 candle data fetch complete: {success_count}/{len(self.symbol_manager.symbols)} symbols in {elapsed:.2f}s")

    def get_avg_volume(self, symbol: str) -> float:
        """O(1) lookup for average 9:15 candle volume"""
        return self.avg_volumes.get(symbol, 0)

    def is_data_ready(self, symbol: str) -> bool:
        """Check if historical 9:15 candle data is available for symbol"""
        return symbol in self.avg_volumes and self.avg_volumes[symbol] > 0
