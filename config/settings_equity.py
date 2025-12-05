# config/settings_equity.py
"""
Equity-specific settings for 9:15 breakout system
"""

# ============================================
# EQUITY TRADING PARAMETERS
# ============================================
EQUITY_ENABLED = True  # Enable equity trading module
EQUITY_MAX_TRADES_PER_DAY = 20
EQUITY_TOTAL_CAPITAL = 100000

# ============================================
# EQUITY STRATEGY PARAMETERS
# ============================================
EQUITY_VOLUME_MULTIPLIER = 3  # Volume must be X times 14-day avg
EQUITY_BREAKOUT_BUFFER_PERCENT = 0.05  # Buffer above high for breakout

# ============================================
# EQUITY EXECUTION MODE
# ============================================
EQUITY_DRY_RUN_MODE = False  # False for live trading, True for paper trading
EQUITY_SLIPPAGE_PERCENT = 0.1  # Slippage simulation for dry-run (in %)

# ============================================
# EQUITY ORDER PARAMETERS
# ============================================
EQUITY_ORDER_TYPE = "MARKET"  # MARKET or LIMIT
EQUITY_PRODUCT_TYPE = "MIS"  # MIS or NRML
EQUITY_EXCHANGE = "NSE"

# ============================================
# EQUITY RISK MANAGEMENT
# ============================================
EQUITY_MAX_LOSS_PER_DAY = 5000  # Stop trading if daily loss exceeds this
