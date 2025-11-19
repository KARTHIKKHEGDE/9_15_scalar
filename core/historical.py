# core/historical.py
"""
Ultra-fast historical data fetching with rate limiting (single-threaded)
"""
import logging
from datetime import datetime, timedelta
from typing import Dict
import numpy as np
import time
from config.settings import API_RATE_LIMIT

logger = logging.getLogger(__name__)

class HistoricalDataManager:
    """Fetches and calculates 14-day averages sequentially (single-threaded)"""

    def __init__(self, kite, symbol_manager):
        self.kite = kite
        self.symbol_manager = symbol_manager
        self.avg_volumes: Dict[str, float] = {}  # symbol -> 14-day avg volume
        self.avg_ranges: Dict[str, float] = {}   # symbol -> 14-day avg range %

    def fetch_single_symbol_data(self, symbol: str, token: int, days: int) -> tuple:
        """
        Fetch historical data for a single symbol.
        Returns (symbol, avg_volume, avg_range)
        If less than `days` candles are available, use whatever is available.
        """
        try:
            to_date = datetime.now().date()-timedelta(days=1)  # Yesterday
            from_date = to_date - timedelta(days=days + 10)  # Extra days for safety

            data = self.kite.historical_data(
                instrument_token=token,
                from_date=from_date,
                to_date=to_date,
                interval='day'
            )

            if not data:
                logger.warning(f"{symbol}: No historical data available")
                return (symbol, 0, 0)

            # Use all available data (slice last `days` candles if possible)
            recent_data = data[-days:]

            if len(recent_data) < days:
                logger.warning(f"{symbol}: Only {len(recent_data)} days of data available (requested {days})")

            # Calculate average volume
            volumes = [candle['volume'] for candle in recent_data]
            avg_volume = np.mean(volumes) if volumes else 0

            # Calculate average range %
            ranges = [
                ((candle['high'] - candle['low']) / candle['low'] * 100)
                for candle in recent_data if candle['low'] > 0
            ]
            avg_range = np.mean(ranges) if ranges else 0

            return (symbol, avg_volume, avg_range)

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return (symbol, 0, 0)

    def fetch_all_historical_data(self, days: int = 14):
        """
        Fetch historical data for all symbols sequentially (single-threaded)
        Respects API rate limit using time.sleep
        """
        logger.info(f"Fetching {days}-day historical data for {len(self.symbol_manager.symbols)} symbols (single-threaded)...")

        start_time = datetime.now()
        success_count = 0

        for symbol in self.symbol_manager.symbols:
            token = self.symbol_manager.get_token(symbol)
            symbol, avg_volume, avg_range = self.fetch_single_symbol_data(symbol, token, days)

            # Respect API rate limit
            time.sleep(1 / API_RATE_LIMIT)

            if avg_volume > 0:
                self.avg_volumes[symbol] = avg_volume
                self.avg_ranges[symbol] = avg_range
                success_count += 1

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Historical data fetch complete: {success_count}/{len(self.symbol_manager.symbols)} symbols in {elapsed:.2f}s")

    def get_avg_volume(self, symbol: str) -> float:
        """O(1) lookup for average volume"""
        return self.avg_volumes.get(symbol, 0)

    def get_avg_range(self, symbol: str) -> float:
        """O(1) lookup for average range"""
        return self.avg_ranges.get(symbol, 0)

    def is_data_ready(self, symbol: str) -> bool:
        """Check if historical data is available for symbol"""
        return symbol in self.avg_volumes and self.avg_volumes[symbol] > 0
