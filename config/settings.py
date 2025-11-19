# config/settings.py
"""
Ultra-low-latency settings for 9:15 breakout system
"""
from datetime import time

# ============================================
# TRADING PARAMETERS
# ============================================
MAX_TRADES_PER_DAY = 5
RISK_PER_TRADE_PERCENT = 1.0  # % of capital per trade
TOTAL_CAPITAL = 100000

# ============================================
# STRATEGY PARAMETERS
# ============================================
VOLUME_MULTIPLIER = 2.0  # Volume must be X times 14-day avg
MIN_CANDLE_RANGE_PERCENT = 0.5  # Minimum % range for 9:15 candle
BREAKOUT_BUFFER_PERCENT = 0.05  # Buffer above high for breakout (to avoid false breakouts)

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
# EXECUTION MODE
# ============================================
DRY_RUN_MODE = True  # False for live trading
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# ============================================
# ORDER PARAMETERS
# ============================================
ORDER_TYPE = "MARKET"  # MARKET or LIMIT
PRODUCT_TYPE = "MIS"  # MIS or NRML
EXCHANGE = "NSE"

# Slippage simulation for dry-run (in %)
SLIPPAGE_PERCENT = 0.1

# ============================================
# RISK MANAGEMENT
# ============================================
TRAILING_SL_PERCENT = None  # Set to number for trailing SL, None to disable
MAX_LOSS_PER_DAY = 5000  # Stop trading if daily loss exceeds this

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