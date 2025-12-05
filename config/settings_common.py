# config/settings_common.py
"""
Common settings shared between equity and options trading
"""
from datetime import time

# ============================================
# TIMING PARAMETERS (IST)
# ============================================
MARKET_OPEN_TIME = time(9, 15, 0)
FIRST_CANDLE_CLOSE_TIME = time(9, 16, 0)
MARKET_CLOSE_TIME = time(15, 30, 0)
API_RATE_LIMIT = 3  # requests per second

# Pre-market data fetch time (run before 9:15)
PREMARKET_FETCH_TIME = time(9, 0, 0)

# ============================================
# LOGGING
# ============================================
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# ============================================
# DATA SOURCES
# ============================================
SYMBOLS_CSV_PATH = "data/symbols.csv"  # CSV with symbol names
HISTORICAL_DAYS = 14  # Days for volume average calculation
HISTORICAL_INTERVAL = "day"

# ============================================
# WEBSOCKET PARAMETERS
# ============================================
WS_RECONNECT_DELAY = 5  # Seconds
WS_RECONNECT_MAX_TRIES = 3

# ============================================
# PERFORMANCE OPTIMIZATIONS
# ============================================
USE_NUMPY = True  # Use numpy for calculations (faster)
TICK_PROCESSING_BATCH_SIZE = 100  # Process ticks in batches
ENABLE_PROFILING = False  # Enable performance profiling

# ============================================
# OUTPUT PATHS
# ============================================
OUTPUT_DIR = "output"
LOGS_DIR = "output/logs"
TRADES_CSV_PREFIX = "trades_"
