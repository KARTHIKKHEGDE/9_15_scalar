# config/settings_options.py
"""
Options-specific settings for 9:15 breakout system
"""

# ============================================
# OPTIONS TRADING PARAMETERS
# ============================================
OPTIONS_ENABLED = True  # Enable options trading module
OPTIONS_MAX_TRADES_PER_DAY = 5

# ============================================
# OPTIONS STRATEGY PARAMETERS
# ============================================
OPTIONS_VOLUME_MULTIPLIER = 2  # Volume multiplier for NIFTY FUT
OPTIONS_QUANTITY = 50  # Lot size per trade
OPTIONS_TARGET_PERCENT = 0.30  # Target profit (30%)

# ============================================
# OPTIONS EXECUTION MODE
# ============================================
OPTIONS_DRY_RUN_MODE = True  # False for live trading, True for paper trading
OPTIONS_SLIPPAGE_PERCENT = 0.1  # Slippage simulation for dry-run (in %)

# ============================================
# OPTIONS ORDER PARAMETERS
# ============================================
OPTIONS_ORDER_TYPE = "MARKET"  # MARKET or LIMIT
OPTIONS_PRODUCT_TYPE = "NRML"  # MIS or NRML
OPTIONS_EXCHANGE = "NFO"

# ============================================
# OPTIONS INSTRUMENT PARAMETERS
# ============================================
OPTIONS_UNDERLYING_SYMBOL = "NIFTY FUT"  # Underlying to track for breakout
OPTIONS_STRIKE_SELECTION = "ATM"  # ATM, OTM1, OTM2, etc.
OPTIONS_EXPIRY_TYPE = "CURRENT_WEEK"  # CURRENT_WEEK, NEXT_WEEK, MONTHLY
