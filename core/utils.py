# core/utils.py
"""
Utility functions for time handling and performance optimization
"""
import time
from datetime import datetime, time as dt_time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def timeit(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        logger.debug(f"{func.__name__} took {elapsed:.2f}ms")
        return result
    return wrapper

def is_market_open(current_time: datetime = None) -> bool:
    """Check if market is currently open"""
    if not current_time:
        current_time = datetime.now()
    
    time_now = current_time.time()
    
    # Market hours: 9:15 AM - 3:30 PM
    market_open = dt_time(9, 15, 0)
    market_close = dt_time(15, 30, 0)
    
    return market_open <= time_now <= market_close

def is_within_first_minute(current_time: datetime = None) -> bool:
    """Check if within first minute of market (9:15-9:16)"""
    if not current_time:
        current_time = datetime.now()
    
    time_now = current_time.time()
    return dt_time(9, 15, 0) <= time_now < dt_time(9, 16, 0)

def wait_until(target_time: dt_time, check_interval: float = 1.0):
    """
    Wait until specific time
    check_interval: seconds between checks
    """
    while datetime.now().time() < target_time:
        time.sleep(check_interval)

def format_price(price: float, decimals: int = 2) -> str:
    """Format price with proper decimals"""
    return f"₹{price:,.{decimals}f}"

def format_pnl(pnl: float) -> str:
    """Format PNL with color indicator"""
    sign = "+" if pnl >= 0 else ""
    return f"{sign}₹{pnl:,.2f}"

def calculate_risk_reward_ratio(entry: float, stoploss: float, target: float) -> float:
    """Calculate risk:reward ratio"""
    risk = abs(entry - stoploss)
    reward = abs(target - entry)
    
    if risk == 0:
        return 0
    
    return reward / risk

def round_to_tick_size(price: float, tick_size: float = 0.05) -> float:
    """Round price to nearest tick size"""
    return round(price / tick_size) * tick_size

class PerformanceMonitor:
    """Monitor system performance metrics"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, name: str):
        """Start timing an operation"""
        self.start_times[name] = time.perf_counter()
    
    def stop_timer(self, name: str):
        """Stop timing and record"""
        if name in self.start_times:
            elapsed = (time.perf_counter() - self.start_times[name]) * 1000
            
            if name not in self.metrics:
                self.metrics[name] = []
            
            self.metrics[name].append(elapsed)
            del self.start_times[name]
            
            return elapsed
        return 0
    
    def get_stats(self, name: str) -> dict:
        """Get statistics for a metric"""
        if name not in self.metrics or not self.metrics[name]:
            return {}
        
        values = self.metrics[name]
        return {
            'count': len(values),
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'last': values[-1]
        }
    
    def print_stats(self):
        """Print all statistics"""
        logger.info("=" * 60)
        logger.info("PERFORMANCE STATISTICS")
        logger.info("=" * 60)
        
        for name, values in self.metrics.items():
            if values:
                stats = self.get_stats(name)
                logger.info(f"{name}: avg={stats['avg']:.2f}ms min={stats['min']:.2f}ms max={stats['max']:.2f}ms")

# Global performance monitor
perf_monitor = PerformanceMonitor()