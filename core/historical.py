# core/historical.py
"""
Ultra-fast historical data fetching with parallel processing
"""
import logging
from datetime import datetime, timedelta
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

logger = logging.getLogger(__name__)

class HistoricalDataManager:
    """Fetches and calculates 14-day averages with parallel processing"""
    
    def __init__(self, kite, symbol_manager):
        self.kite = kite
        self.symbol_manager = symbol_manager
        self.avg_volumes: Dict[str, float] = {}  # symbol -> 14-day avg volume
        self.avg_ranges: Dict[str, float] = {}   # symbol -> 14-day avg range %
    
    def fetch_single_symbol_data(self, symbol: str, token: int, days: int) -> tuple:
        """
        Fetch historical data for a single symbol
        Returns (symbol, avg_volume, avg_range)
        """
        try:
            to_date = datetime.now().date()
            from_date = to_date - timedelta(days=days + 5)  # Extra days for safety
            
            # Fetch historical data
            data = self.kite.historical_data(
                instrument_token=token,
                from_date=from_date,
                to_date=to_date,
                interval='day'
            )
            
            if not data or len(data) < days:
                logger.warning(f"{symbol}: Insufficient data ({len(data) if data else 0} days)")
                return (symbol, 0, 0)
            
            # Take last 'days' candles
            recent_data = data[-days:]
            
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
    
    def fetch_all_historical_data(self, days: int = 14, max_workers: int = 10):
        """
        Fetch historical data for all symbols in parallel
        max_workers: Number of parallel threads (optimize based on API rate limits)
        """
        logger.info(f"Fetching {days}-day historical data for {len(self.symbol_manager.symbols)} symbols...")
        
        start_time = datetime.now()
        success_count = 0
        
        # Parallel execution for speed
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(
                    self.fetch_single_symbol_data,
                    symbol,
                    self.symbol_manager.get_token(symbol),
                    days
                ): symbol
                for symbol in self.symbol_manager.symbols
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_symbol):
                symbol, avg_volume, avg_range = future.result()
                
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