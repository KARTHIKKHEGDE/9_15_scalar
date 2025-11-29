# Module & Function Reference - 9:15 Breakout Trading System

This document provides a detailed description of each file, its main classes/functions, and what each function does in the system, including logic, data structures, and module interactions.

---

## main.py

- **Purpose:** Central orchestrator; initializes all modules, manages trading lifecycle, and coordinates event-driven trading logic.
- **Key Class:** TradingSystem
  - `__init__`: Loads config, sets up all modules (symbol manager, historical data, candle builder, marker, breakout engine, risk manager, order executor, trade logger, tick router, websocket manager), and configures callbacks for inter-module communication. Logs system state and trading mode.
  - `_initialize_kite`: Reads API credentials from environment, connects to Zerodha Kite API, tests connection by fetching user profile, and handles errors gracefully.
  - `_initialize_modules`: Instantiates all system modules in dependency order. Loads symbols from CSV, maps tokens, prepares historical data manager, sets up candle builder for tick aggregation, initializes portfolio for position tracking, configures marker for breakout qualification, sets up breakout engine for event detection, risk manager for position sizing and stop-loss, order executor for live/dry-run trading, trade logger for CSV output, tick router for tick distribution, and websocket manager for real-time data.
  - `_setup_callbacks`: Registers event-driven callbacks: candle close triggers marker evaluation, breakout triggers entry execution, risk manager triggers exit execution, websocket tick triggers tick router. Ensures decoupled, modular event flow.
  - `_execute_entry`: Checks trade limits and risk, calculates position size, places buy order (live or dry-run), retrieves execution price, adds position to portfolio, logs trade, and reports entry. Called when a breakout is detected.
  - `_execute_exit`: Checks for active position, places sell order, retrieves execution price, closes position in portfolio, logs exit, and reports realized PNL. Called when stop-loss or exit condition is met.
  - `fetch_historical_data`: Downloads 14-day historical data for all symbols before market open, used for volume/range qualification. Calls HistoricalDataManager.
  - `start_trading`: Subscribes to all tokens, starts WebSocket connection, enters blocking tick-processing loop. Initiates live trading phase.
  - `print_stats`: Aggregates and logs system statistics: capital, PNL, trades, win rate, marked stocks, breakouts detected.
- **Function:** main
  - Entry point; creates TradingSystem instance, fetches historical data if outside market hours, waits for market open, then starts trading. Handles shutdown and fatal errors.

---

## config/settings.py

- **Purpose:** Central configuration file containing ALL system parameters. This is the CONTROL PANEL - changing values here affects system behavior without code changes. Organized into logical sections for easy management.

- **Configuration Sections:**

### Trading Parameters
- `MAX_TRADES_PER_DAY = 5`
  - **Purpose:** Maximum number of positions allowed per day
  - **Why:** Limits exposure and prevents over-trading
  - **Usage:** Portfolio.can_take_trade() checks this before entry

- `TOTAL_CAPITAL = 100000`
  - **Purpose:** Total capital available for trading (₹1,00,000)
  - **Why:** Used for position sizing and risk management
  - **Usage:** RiskManager divides this equally among marked stocks

### Strategy Parameters
- `VOLUME_MULTIPLIER = 2.0`
  - **Purpose:** 9:15 candle volume must be X times 14-day average
  - **Why:** Filters for high-volume breakouts (more reliable)
  - **Example:** If avg volume = 1M, candle needs ≥2M volume
  - **Usage:** StockMarker.evaluate_and_mark() uses this criterion

- `BREAKOUT_BUFFER_PERCENT = 0.05`
  - **Purpose:** Buffer above 9:15 high for breakout trigger (0.05%)
  - **Why:** Prevents false breakouts from minor fluctuations
  - **Example:** If high = ₹1000, breakout at ₹1000.50
  - **Usage:** StockMarker.get_breakout_level() adds this buffer

### Timing Parameters (IST)
- `MARKET_OPEN_TIME = time(9, 15, 0)`
  - **Purpose:** Market opening time
  - **Usage:** Time checks, waiting logic

- `FIRST_CANDLE_CLOSE_TIME = time(9, 16, 0)`
  - **Purpose:** When 9:15 candle closes
  - **Usage:** Marker identifies 9:15 candles

- `MARKET_CLOSE_TIME = time(15, 30, 0)`
  - **Purpose:** Market closing time
  - **Usage:** Stop processing ticks after this

- `API_RATE_LIMIT = 3`
  - **Purpose:** Maximum API requests per second
  - **Why:** Zerodha limits to 3 req/sec
  - **Usage:** HistoricalDataManager sleeps 333ms between calls

- `PREMARKET_FETCH_TIME = time(9, 0, 0)`
  - **Purpose:** When to fetch historical data
  - **Why:** Complete before market opens at 9:15
  - **Usage:** main.py scheduling

### Execution Mode
- `DRY_RUN_MODE = True`
  - **Purpose:** Toggle between simulation and live trading
  - **True:** Uses DryRunOrderExecutor (no real orders)
  - **False:** Uses LiveOrderExecutor (REAL MONEY)
  - **CRITICAL:** Always test with True first!

- `LOG_LEVEL = "INFO"`
  - **Purpose:** Logging verbosity
  - **Options:** DEBUG, INFO, WARNING, ERROR
  - **Usage:** Set to DEBUG for troubleshooting

### Order Parameters
- `ORDER_TYPE = "MARKET"`
  - **Purpose:** Order type for entries
  - **Options:** MARKET (instant) or LIMIT (at specific price)
  - **Why MARKET:** Speed is critical for breakouts

- `PRODUCT_TYPE = "MIS"`
  - **Purpose:** Product type for orders
  - **MIS:** Intraday (positions auto-squared off at 3:20 PM)
  - **NRML:** Delivery (positions held overnight)
  - **Usage:** All orders use this product type

- `EXCHANGE = "NSE"`
  - **Purpose:** Exchange for trading
  - **Options:** NSE, BSE
  - **Usage:** Symbol mapping, order placement

- `SLIPPAGE_PERCENT = 0.1`
  - **Purpose:** Simulated slippage for dry-run (0.1%)
  - **Note:** Current implementation uses real LTP instead
  - **Usage:** Legacy parameter (kept for compatibility)

### Risk Management
- `MAX_LOSS_PER_DAY = 5000`
  - **Purpose:** Stop trading if daily loss exceeds ₹5,000
  - **Why:** Capital preservation, prevents catastrophic losses
  - **Usage:** RiskManager.check_max_loss() enforces this

### Data Sources
- `SYMBOLS_CSV_PATH = "data/symbols.csv"`
  - **Purpose:** Path to CSV file with symbol list
  - **Format:** CSV with 'symbol' column
  - **Usage:** SymbolManager.load_symbols_from_csv()

- `HISTORICAL_DAYS = 14`
  - **Purpose:** Number of days for average calculations
  - **Why:** 14 days provides good statistical baseline
  - **Usage:** HistoricalDataManager.fetch_all_historical_data()

- `HISTORICAL_INTERVAL = "day"`
  - **Purpose:** Candle interval for historical data
  - **Options:** day, minute, hour
  - **Usage:** Kite API parameter

### WebSocket Parameters
- `WS_RECONNECT_DELAY = 5`
  - **Purpose:** Seconds to wait before reconnection attempt
  - **Why:** Prevents rapid reconnection loops
  - **Usage:** WebSocketManager._attempt_reconnect()

- `WS_RECONNECT_MAX_TRIES = 3`
  - **Purpose:** Maximum reconnection attempts
  - **Why:** Prevents infinite reconnection loops
  - **Usage:** WebSocketManager reconnection logic

### Performance Optimizations
- `USE_NUMPY = True`
  - **Purpose:** Use numpy for calculations (faster)
  - **Why:** Numpy is optimized for numerical operations
  - **Usage:** Historical data calculations

- `TICK_PROCESSING_BATCH_SIZE = 100`
  - **Purpose:** Process ticks in batches
  - **Note:** Currently processes individually
  - **Usage:** Future optimization parameter

- `ENABLE_PROFILING = False`
  - **Purpose:** Enable performance profiling
  - **True:** Logs execution times for all operations
  - **Usage:** Performance analysis, optimization

### Output Paths
- `OUTPUT_DIR = "output"`
  - **Purpose:** Directory for all output files
  - **Usage:** Trade logs, reports

- `LOGS_DIR = "output/logs"`
  - **Purpose:** Directory for system logs
  - **Usage:** Logging configuration

- `TRADES_CSV_PREFIX = "trades_"`
  - **Purpose:** Prefix for daily trade log files
  - **Result:** Files like trades_20250124.csv
  - **Usage:** TradeLogger filename generation

## config/token_generator.py

- **Purpose:** Interactive utility script for generating and refreshing Zerodha access tokens. Access tokens expire daily, so this script must be run before each trading session to obtain a fresh token. Automates the OAuth flow and updates the secrets.env file.

- **Why Needed:** Zerodha's security requires daily token refresh. This script handles the entire authentication flow.

- **Function:** `get_access_token()`
  
  - **Purpose:** Complete OAuth flow to generate fresh access token.
  - **Returns:** Access token string or None if failed
  
  - **Logic Flow:**
    
    1. **Load Credentials:**
       - Reads `config/secrets.env` file
       - Extracts API_KEY and API_SECRET
       - Validates both are present
    
    2. **Initialize Kite:**
       - Creates KiteConnect instance with API_KEY
       - Generates login URL
    
    3. **User Authentication:**
       - Opens login URL in browser automatically
       - User logs in with Zerodha credentials
       - User authorizes the app
       - Zerodha redirects to callback URL with request_token
    
    4. **Request Token Input:**
       - Prompts user to copy request_token from redirect URL
       - Example URL: `https://redirect.url/?status=success&request_token=xxxxx`
       - User pastes just the token part
    
    5. **Generate Session:**
       - Calls `kite.generate_session(request_token, api_secret)`
       - Receives access_token in response
       - Logs token details
    
    6. **Update secrets.env:**
       - Reads existing secrets.env file
       - Searches for ACCESS_TOKEN= line
       - Updates with new token or appends if not found
       - Writes back to file
       - Logs success
    
    7. **Error Handling:**
       - **TokenException:** Invalid or expired request_token
       - **Generic Exception:** Network errors, file errors, etc.
       - Returns None on any error
  
  - **Usage:** Run this script manually before starting the trading system each day
  
  - **Command:** `python config/token_generator.py`
  
  - **Interactive Steps:**
    1. Script opens browser with Zerodha login
    2. User logs in and authorizes
    3. User copies request_token from redirect URL
    4. User pastes token into terminal
    5. Script generates and saves access_token
    6. Ready to run main.py!

- **Main Block:**
  - **Purpose:** Entry point when script is run directly
  - **Logic:**
    - Calls `get_access_token()`
    - If successful, prints confirmation message
    - If failed, exits silently (errors already logged)
  
- **Auto-Install:**
  - **Purpose:** Automatically installs kiteconnect if not present
  - **Logic:** Try-except block at top of file
  - **Why:** Ensures script can run even on fresh Python installation

## config/secrets.env

- **Purpose:** Stores sensitive API credentials for Zerodha Kite API. This file should NEVER be committed to version control (listed in .gitignore).

- **Required Fields:**
  - `API_KEY=your_api_key_here`
    - **Source:** Zerodha Kite Connect developer console
    - **Format:** Alphanumeric string
    - **Security:** Keep secret, never share
  
  - `API_SECRET=your_api_secret_here`
    - **Source:** Zerodha Kite Connect developer console
    - **Format:** Alphanumeric string
    - **Security:** Keep secret, never share
  
  - `ACCESS_TOKEN=your_access_token_here`
    - **Source:** Generated by token_generator.py
    - **Validity:** 24 hours (expires daily)
    - **Auto-Updated:** token_generator.py updates this field

- **Security Notes:**
  - Add to .gitignore to prevent accidental commits
  - Never share this file or its contents
  - Rotate API credentials if compromised
  - Access token expires daily (automatic security)

---

## core/symbols.py

- **Purpose:** Manages the complete lifecycle of tradable symbols - from CSV loading to ultra-fast token lookups. This module is critical for converting between human-readable symbol names (like "RELIANCE") and Zerodha's instrument tokens (numeric IDs) used in WebSocket ticks and order placement. Optimized for O(1) lookups to minimize latency in the hot path.

- **Key Data Structures:**
  - `symbols: List[str]` - Sorted list of all loaded symbol names (e.g., ["RELIANCE", "TCS", "INFY"])
  - `token_map: Dict[str, int]` - Maps symbol → instrument token for O(1) forward lookup
  - `reverse_token_map: Dict[int, str]` - Maps instrument token → symbol for O(1) reverse lookup
  - `instrument_map: Dict[str, dict]` - Stores full instrument metadata (tick size, lot size, exchange info)

- **Class:** SymbolManager
  
  - `__init__(self, kite)`: 
    - **Purpose:** Initializes the symbol manager with Kite API connection and prepares empty data structures.
    - **Parameters:** `kite` - KiteConnect instance for fetching instrument data
    - **Logic:** Creates empty lists and dictionaries for symbols, tokens, and mappings. No API calls made yet.
    - **Usage:** Called once during TradingSystem initialization in main.py
  
  - `load_symbols_from_csv(self, csv_path: str) -> int`:
    - **Purpose:** Loads trading symbols from CSV file, handling multiple column name formats.
    - **Parameters:** `csv_path` - Path to CSV file containing symbol names
    - **Returns:** Count of successfully loaded symbols
    - **Logic Flow:**
      1. Opens CSV file using csv.DictReader for flexible column access
      2. Tries multiple column name variants: 'symbol', 'trading_symbol', 'tradingsymbol', 'Symbol', 'SYMBOL'
      3. Strips whitespace and converts to uppercase for consistency
      4. Uses a Set to automatically deduplicate symbols
      5. Sorts final list alphabetically for consistent ordering
      6. Logs count of loaded symbols
    - **Error Handling:** Catches file I/O errors and re-raises with context
    - **Data Structure:** Populates `self.symbols` list
  
  - `map_tokens(self, exchange: str = "NSE") -> Dict[str, int]`:
    - **Purpose:** Maps all loaded symbols to their instrument tokens by querying Kite API.
    - **Parameters:** `exchange` - Exchange name (default: "NSE")
    - **Returns:** Dictionary of symbol→token mappings
    - **Logic Flow:**
      1. Fetches ALL instruments for the exchange via `kite.instruments(exchange)` (single API call)
      2. Filters to only equity instruments (`instrument_type == 'EQ'`)
      3. Creates fast lookup dictionary: `{tradingsymbol: instrument_data}`
      4. Iterates through loaded symbols and looks up each in the dictionary
      5. For each match, populates three maps:
         - `token_map[symbol] = token` (for symbol→token lookup)
         - `reverse_token_map[token] = symbol` (for token→symbol lookup)
         - `instrument_map[symbol] = full_instrument_data` (for metadata)
      6. Logs warnings for symbols not found in exchange data
      7. Logs final mapping statistics (e.g., "Mapped 45/50 symbols")
    - **Performance:** Single API call + O(n) dictionary lookups = very fast
    - **Error Handling:** Catches API errors and re-raises with context
  
  - `get_token(self, symbol: str) -> int`:
    - **Purpose:** O(1) lookup to get instrument token for a symbol.
    - **Parameters:** `symbol` - Symbol name (e.g., "RELIANCE")
    - **Returns:** Instrument token (int) or None if not found
    - **Usage:** Called by order executor when placing orders, and by tick router for validation
    - **Performance:** Dictionary lookup = O(1), sub-microsecond latency
  
  - `get_symbol(self, token: int) -> str`:
    - **Purpose:** O(1) reverse lookup to get symbol name from instrument token.
    - **Parameters:** `token` - Instrument token from WebSocket tick
    - **Returns:** Symbol name (str) or None if not found
    - **Usage:** Called by tick router to decode incoming ticks (hot path - called thousands of times per second)
    - **Performance:** Dictionary lookup = O(1), critical for tick processing speed
  
  - `get_all_tokens(self) -> List[int]`:
    - **Purpose:** Returns list of all instrument tokens for WebSocket subscription.
    - **Returns:** List of all tokens (e.g., [738561, 2953217, ...])
    - **Usage:** Called once by WebSocketManager during subscription setup
    - **Logic:** Extracts values from `token_map` dictionary
  
  - `get_tick_size(self, symbol: str) -> float`:
    - **Purpose:** Gets the minimum price tick size for a symbol.
    - **Parameters:** `symbol` - Symbol name
    - **Returns:** Tick size (e.g., 0.05 for most NSE stocks)
    - **Usage:** Used for rounding order prices to valid tick increments
    - **Fallback:** Returns 0.05 if symbol not found (standard NSE tick size)
  
  - `get_lot_size(self, symbol: str) -> int`:
    - **Purpose:** Gets the lot size for a symbol.
    - **Returns:** Always 1 for equities (futures/options have different lot sizes)
    - **Usage:** Position size calculations
  
  - `get_instrument_data(self, symbol: str) -> dict`:
    - **Purpose:** Returns complete instrument metadata for a symbol.
    - **Returns:** Full instrument dictionary with exchange, segment, tick size, lot size, etc.
    - **Usage:** Advanced order placement or instrument analysis

---

## core/historical.py

- **Purpose:** Fetches and processes historical OHLCV (Open, High, Low, Close, Volume) data for all symbols to compute statistical baselines used in breakout qualification. Calculates 14-day average volume, which is critical for the marker module to identify qualifying stocks at 9:15 AM.

- **Key Data Structures:**
  - `avg_volumes: Dict[str, float]` - Maps symbol → 14-day average volume (e.g., {"RELIANCE": 5000000})

- **Class:** HistoricalDataManager
  
  - `__init__(self, kite, symbol_manager)`:
    - **Purpose:** Initializes the historical data manager with API connection and symbol manager reference.
    - **Parameters:** 
      - `kite` - KiteConnect instance for API calls
      - `symbol_manager` - SymbolManager instance for token lookups
    - **Logic:** Creates empty dictionaries for storing calculated averages
    - **Usage:** Called once during TradingSystem initialization
  
  - `fetch_single_symbol_data(self, symbol: str, token: int, days: int) -> tuple`:
    - **Purpose:** Fetches historical data for ONE symbol and calculates its average volume.
    - **Parameters:**
      - `symbol` - Symbol name (for logging)
      - `token` - Instrument token (for API call)
      - `days` - Number of days to fetch (typically 14)
    - **Returns:** Tuple of `(symbol, avg_volume)`
    - **Logic Flow:**
      1. Calculates date range: `to_date` = yesterday, `from_date` = yesterday - (days + 10 buffer)
      2. Calls `kite.historical_data()` with instrument token, date range, and 'day' interval
      3. Slices last N candles from response (handles cases where less than N days available)
      4. **Volume Calculation:** Extracts volume from each candle, computes mean using numpy
      5. Logs warning if fewer than requested days available
      6. Returns calculated average (returns 0 if no data)
    - **Error Handling:** Catches API errors, logs error, returns (symbol, 0) to prevent crash
    - **Performance:** Single API call per symbol, ~100-200ms per call
  
  - `fetch_all_historical_data(self, days: int = 14)`:
    - **Purpose:** Sequentially fetches historical data for ALL symbols with rate limiting.
    - **Why Sequential:** Parallel fetching would exceed API rate limits and cause errors
  
  - `get_avg_volume(self, symbol: str) -> float`:
    - **Purpose:** O(1) lookup for precomputed 14-day average volume.
    - **Parameters:** `symbol` - Symbol name
    - **Returns:** Average volume (float) or 0 if not available
    - **Usage:** Called by StockMarker during 9:15 candle evaluation to check volume criterion
    - **Performance:** Dictionary lookup = O(1), sub-microsecond
  

  
  - `is_data_ready(self, symbol: str) -> bool`:
    - **Purpose:** Validates that historical data is available for a symbol before trading.
    - **Parameters:** `symbol` - Symbol name
    - **Returns:** True if avg_volume > 0 (indicates successful data fetch)
    - **Usage:** Error checking before marking symbols for trading
    - **Logic:** Checks if symbol exists in avg_volumes dict AND value > 0

---

## core/candles.py

- **Purpose:** Aggregates real-time tick data into 1-minute OHLCV candles for each symbol. This is the foundation for all trading decisions - candles are used for marking stocks at 9:15, detecting breakouts, and calculating stop-loss levels. Optimized for ultra-low latency tick processing with thread-safe operations.

- **Key Data Structures:**
  - `active_candles: Dict[int, dict]` - Maps token → currently building candle data (updated on every tick)
  - `completed_candles: Dict[int, Candle]` - Maps token → last completed candle (immutable)
  - `previous_volume: Dict[int, int]` - Tracks cumulative volume to calculate per-minute volume delta
  - `current_minute: Optional[time]` - Tracks current minute boundary for candle closure detection

- **DataClass:** Candle
  - **Purpose:** Immutable data structure representing a completed 1-minute candle.
  - **Attributes:**
    - `symbol: str` - Symbol name
    - `timestamp: datetime` - Candle's minute timestamp (e.g., 9:15:00, 9:16:00)
    - `open: float` - First tick price of the minute
    - `high: float` - Highest tick price of the minute
    - `low: float` - Lowest tick price of the minute
    - `close: float` - Last tick price of the minute
    - `volume: int` - Total volume traded during this minute (NOT cumulative)
  
  - `range_percent(self) -> float`:
    - **Purpose:** Calculates candle's price range as a percentage of low price.
    - **Formula:** `((high - low) / low) * 100`
    - **Returns:** Range percentage (e.g., 2.5 means 2.5% range)
    - **Usage:** Used by StockMarker to check if 9:15 candle meets range criterion
    - **Edge Case:** Returns 0 if low price is 0 (prevents division by zero)

- **Class:** CandleBuilder
  
  - `__init__(self, symbol_manager)`:
    - **Purpose:** Initializes candle builder with empty data structures and thread lock.
    - **Parameters:** `symbol_manager` - For token↔symbol conversions
    - **Thread Safety:** Creates `threading.Lock()` for safe concurrent access
    - **Callback:** Initializes `on_candle_close` callback as None (set later)
    - **State:** Sets `current_minute` to None (will be set on first tick)
  
  - `set_on_candle_close_callback(self, callback: Callable[[Candle], None])`:
    - **Purpose:** Registers callback function to be invoked when any candle closes.
    - **Parameters:** `callback` - Function that accepts a Candle object
    - **Usage:** TradingSystem registers marker's `evaluate_and_mark` method here
    - **Event Flow:** Candle closes → callback triggered → marker evaluates → potential marking
  
  - `process_tick(self, tick: dict)`:
    - **Purpose:** CRITICAL HOT PATH - processes incoming tick and updates/creates candles.
    - **Parameters:** `tick` - Dictionary with keys: `instrument_token`, `last_price`, `volume_traded`, `exchange_timestamp`
    - **Called By:** TickRouter on EVERY tick (thousands per second during market hours)
    - **Logic Flow:**
      1. Extracts token, price, cumulative volume, and timestamp from tick
      2. Rounds timestamp to current minute (e.g., 9:15:37 → 9:15:00)
      3. **Minute Change Detection:** Compares `current_min` with `self.current_minute`
      4. **If minute changed:** Calls `_close_all_candles()` to finalize previous minute's candles
      5. Updates `self.current_minute` to new minute
      6. **New Candle Creation:** If token not in `active_candles`:
         - Calculates volume delta: `volume - previous_volume[token]`
         - Creates new candle dict with OHLC all set to current price
         - Stores both per-minute volume and cumulative volume
      7. **Existing Candle Update:** If token already in `active_candles`:
         - Updates `high` = max(current high, new price)
         - Updates `low` = min(current low, new price)
         - Updates `close` = new price
         - Updates cumulative volume (per-minute volume stays as initially calculated)
    - **Thread Safety:** All operations wrapped in `with self.lock:`
    - **Volume Handling:** Zerodha sends CUMULATIVE volume since 9:15 AM, so we calculate delta
    - **Performance:** O(1) dictionary operations, typically <100 microseconds
  
  - `_close_all_candles(self, minute: datetime)`:
    - **Purpose:** Finalizes all active candles when minute boundary is crossed.
    - **Parameters:** `minute` - The minute that just completed (e.g., 9:15:00)
    - **Called By:** `process_tick()` when minute changes
    - **Logic Flow:**
      1. Iterates through all active candles (all symbols being tracked)
      2. For each candle:
         - Gets symbol name from token via symbol_manager
         - Creates immutable `Candle` object with final OHLCV data
         - Stores in `completed_candles[token]` for later retrieval
         - Updates `previous_volume[token]` with cumulative volume for next candle
         - **Triggers callback:** Calls `on_candle_close(completed)` if callback is set
      3. Clears `active_candles` dictionary to prepare for next minute
      4. Logs completion with candle count
    - **Error Handling:** Wraps callback in try-except to prevent one symbol's error from crashing others
    - **Event Chain:** This triggers marker evaluation for 9:15 candles
  
  - `get_candle(self, symbol: str) -> Optional[Candle]`:
    - **Purpose:** Retrieves last completed candle for a symbol.
    - **Parameters:** `symbol` - Symbol name
    - **Returns:** Candle object or None if no completed candle exists
    - **Usage:** Called by StockMarker to get 9:15 candle for evaluation
    - **Performance:** O(1) token lookup + O(1) dictionary access
  
  - `get_active_candle_data(self, symbol: str) -> Optional[dict]`:
    - **Purpose:** Gets currently building (incomplete) candle data.
    - **Parameters:** `symbol` - Symbol name
    - **Returns:** Dictionary with current OHLCV or None
    - **Thread Safety:** Wrapped in lock to prevent reading during update
    - **Usage:** Real-time monitoring, debugging, or live price display
  
  - `get_current_candle_open(self, symbol: str) -> Optional[float]`:
    - **Purpose:** Gets the open price of the currently building candle.
    - **Parameters:** `symbol` - Symbol name
    - **Returns:** Open price (float) or None if no active candle
    - **Critical Usage:** Called by BreakoutEngine to set stop-loss at breakout candle's open price
    - **Why Important:** Stop-loss should be at the open of the breakout candle, not the 9:15 candle
    - **Thread Safety:** Wrapped in lock
  
  - `force_close_candles(self)`:
    - **Purpose:** Manually closes all active candles (emergency/testing).
    - **Usage:** Called during system shutdown or for testing candle close logic
    - **Logic:** Calls `_close_all_candles()` with current minute if available

---

## core/marker.py

- **Purpose:** Evaluates the 9:15 AM candle for each symbol and marks those that qualify for breakout trading. This is the GATEKEEPER - only marked symbols are monitored for breakouts. Uses volume and range criteria to filter high-probability setups. Thread-safe for concurrent access.

- **Key Data Structures:**
  - `marked_symbols: Set[str]` - Thread-safe set of currently marked symbols (actively monitored)
  - `marked_candles: Dict[str, Candle]` - Stores 9:15 candles for marked symbols (never deleted, used for stats)
  - `lock: threading.Lock` - Ensures thread-safe modifications to marked_symbols set

- **Class:** StockMarker
  
  - `__init__(self, historical_manager, config)`:
    - **Purpose:** Initializes marker with historical data reference and configuration.
    - **Parameters:**
      - `historical_manager` - For accessing 14-day average volume/range
      - `config` - Dictionary with VOLUME_MULTIPLIER and other settings
    - **State Initialization:**
      - Creates empty set for marked_symbols
      - Creates empty dict for marked_candles
      - Initializes counters: total_evaluated = 0, total_marked = 0
    - **Thread Safety:** Creates lock for protecting marked_symbols modifications
  
  - `get_total_marked_count(self) -> int`:
    - **Purpose:** Returns total count of stocks marked during the day (including already triggered).
    - **Returns:** Length of `marked_candles` dictionary
    - **Why Important:** Used by RiskManager for equal capital distribution across ALL marked stocks
    - **Key Insight:** This count NEVER decreases during the day (even after breakouts trigger)
    - **Usage:** Called during position sizing to ensure capital is divided equally
  
  - `evaluate_and_mark(self, candle: Candle) -> bool`:
    - **Purpose:** CRITICAL DECISION POINT - evaluates if a candle qualifies for marking.
    - **Parameters:** `candle` - Completed 1-minute candle from CandleBuilder
    - **Returns:** True if marked, False if rejected
    - **Called By:** CandleBuilder's callback when any candle closes
    - **Logic Flow:**
      1. Increments `total_evaluated` counter
      2. **Time Check:** Verifies candle timestamp is between 9:15:00 and 9:16:00
         - If not in this window, returns False immediately (not the 9:15 candle)
      3. **Historical Data Check:** Gets avg_volume from HistoricalDataManager
         - If avg_volume == 0, logs warning and returns False (no baseline data)
      4. **Criterion 1 - Volume Check:**
         - Calculates `volume_ratio = candle.volume / avg_volume`
         - Compares against `config['VOLUME_MULTIPLIER']` (typically 2.0)
         - If volume_ratio < multiplier, logs debug message and returns False
         - **Example:** If avg_volume = 1M and multiplier = 2.0, candle needs ≥2M volume
      5. **All Criteria Met - MARK IT:**
         - Adds symbol to `marked_symbols` set (thread-safe with lock)
         - Stores candle in `marked_candles` dict for later reference
         - Increments `total_marked` counter
         - Logs success with volume ratio and high price
      6. Returns True
    - **Thread Safety:** Uses `with self.lock:` when modifying marked_symbols
    - **Performance:** O(1) dictionary lookups, <1ms execution time
  
  - `is_marked(self, symbol: str) -> bool`:
    - **Purpose:** O(1) check if symbol is currently marked for breakout monitoring.
    - **Parameters:** `symbol` - Symbol name
    - **Returns:** True if in marked_symbols set
    - **Usage:** Called by BreakoutEngine on EVERY tick to filter which symbols to monitor
    - **Performance:** Set membership test = O(1), sub-microsecond
  
  - `get_marked_candle(self, symbol: str) -> Candle`:
    - **Purpose:** Retrieves the stored 9:15 candle for a marked symbol.
    - **Parameters:** `symbol` - Symbol name
    - **Returns:** Candle object or None
    - **Usage:** 
      - BreakoutEngine uses it for logging breakout details
      - RiskManager uses it as fallback for stop-loss if current candle unavailable
    - **Performance:** O(1) dictionary lookup
  
  - `get_all_marked_symbols(self) -> Set[str]`:
    - **Purpose:** Returns copy of all currently marked symbols.
    - **Returns:** Set of symbol names (copy to prevent external modification)
    - **Thread Safety:** Creates copy within lock to ensure consistency
    - **Usage:** Capital allocation, reporting, statistics
  
  - `get_breakout_level(self, symbol: str) -> float`:
    - **Purpose:** Calculates the price level at which breakout is triggered.
    - **Parameters:** `symbol` - Symbol name
    - **Returns:** Breakout price (high + buffer) or 0 if not marked
    - **Logic:**
      1. Gets 9:15 candle from marked_candles
      2. Calculates buffer: `candle.high * (BREAKOUT_BUFFER_PERCENT / 100)`
      3. Returns `candle.high + buffer`
    - **Example:** If high = 100 and buffer = 0.05%, breakout level = 100.05
    - **Why Buffer:** Prevents false breakouts from minor price fluctuations
    - **Usage:** Called by BreakoutEngine to check if price crossed breakout level
  
  - `get_stoploss_level(self, symbol: str) -> float`:
    - **Purpose:** Returns stop-loss level (open of 9:15 candle).
    - **Parameters:** `symbol` - Symbol name
    - **Returns:** Open price of 9:15 candle or 0 if not marked
    - **Usage:** Fallback stop-loss if breakout candle's open is unavailable
    - **Note:** Preferred stop-loss is breakout candle's open, this is backup
  
  - `unmark_symbol(self, symbol: str)`:
    - **Purpose:** Removes symbol from active monitoring after breakout triggers.
    - **Parameters:** `symbol` - Symbol name
    - **Logic:** Removes from marked_symbols set using `discard()` (no error if not present)
    - **Thread Safety:** Wrapped in lock
    - **Called By:** BreakoutEngine after breakout is triggered
    - **Important:** Does NOT remove from marked_candles (preserves total count)
  
  - `get_stats(self) -> dict`:
    - **Purpose:** Returns marking statistics for reporting.
    - **Returns:** Dictionary with:
      - `total_evaluated` - Total candles evaluated (all symbols × all minutes)
      - `total_marked` - Total symbols marked at 9:15
      - `currently_marked` - Symbols still being monitored (not yet triggered)
    - **Usage:** System statistics, end-of-day reporting
  
  - `reset(self)`:
    - **Purpose:** Resets all state for next trading day.
    - **Logic:** Clears all sets, dicts, and resets counters to 0
    - **Thread Safety:** Wrapped in lock
    - **Usage:** Called at end of trading day or for testing

---

## core/breakout.py

- **Purpose:** Monitors marked symbols for breakout events in real-time and triggers entry execution when price crosses the breakout level. This is the TRIGGER MODULE - it watches every tick for marked symbols and fires the entry signal. Optimized for millisecond-level latency to capture breakouts instantly.

- **Key Data Structures:**
  - `last_prices: Dict[int, float]` - Maps token → last seen price (for monitoring and LTP retrieval)
  - `breakout_triggered: Dict[str, bool]` - Maps symbol → triggered status (prevents duplicate entries)
  - `lock: threading.Lock` - Thread-safe price updates

- **Class:** BreakoutEngine
  
  - `__init__(self, marker, symbol_manager, config, candle_builder)`:
    - **Purpose:** Initializes breakout engine with references to all required modules.
    - **Parameters:**
      - `marker` - StockMarker for checking if symbol is marked and getting breakout levels
      - `symbol_manager` - For token↔symbol conversions
      - `config` - Configuration dictionary
      - `candle_builder` - For getting current candle's open price (stop-loss)
    - **State:** Creates empty dicts for last_prices and breakout_triggered
    - **Callback:** Initializes on_breakout callback as None
  
  - `set_on_breakout_callback(self, callback: Callable[[str, float, float], None])`:
    - **Purpose:** Registers callback to execute when breakout is detected.
    - **Parameters:** `callback` - Function signature: `(symbol, entry_price, stoploss_price)`
    - **Usage:** TradingSystem registers `_execute_entry` method here
    - **Event Chain:** Breakout detected → callback → order placement → position creation
  
  - `process_tick(self, tick: dict)`:
    - **Purpose:** HOT PATH - checks EVERY tick for breakout conditions.
    - **Parameters:** `tick` - Tick dictionary with token, price, etc.
    - **Called By:** TickRouter on every tick (thousands per second)
    - **Logic Flow:**
      1. Extracts token and price from tick
      2. Converts token → symbol via symbol_manager
      3. **Early Exit 1:** If symbol not marked, returns immediately (no monitoring needed)
      4. **Early Exit 2:** If breakout already triggered for this symbol, returns (prevents duplicates)
      5. Updates last_prices[token] with current price (thread-safe)
      6. Gets breakout level from marker
      7. **BREAKOUT DETECTION:** If `price >= breakout_level`, calls `_trigger_breakout()`
    - **Performance:** Multiple O(1) checks, typically <50 microseconds
    - **Thread Safety:** Price update wrapped in lock
  
  - `_trigger_breakout(self, symbol: str, entry_price: float)`:
    - **Purpose:** CRITICAL - executes breakout logic and triggers entry.
    - **Parameters:**
      - `symbol` - Symbol that broke out
      - `entry_price` - Price at which breakout occurred
    - **Logic Flow:**
      1. **Prevent Duplicates:** Sets `breakout_triggered[symbol] = True`
      2. Increments `breakouts_detected` counter
      3. **Stop-Loss Calculation:**
         - Gets current candle's open price via `candle_builder.get_current_candle_open()`
         - **Fallback:** If unavailable, uses 9:15 candle's open from marker
         - Logs warning if using fallback
      4. Gets 9:15 candle for logging details
      5. **Logs Breakout:** Displays symbol, entry price, stop-loss, and 9:15 high
      6. **Triggers Callback:** Calls `on_breakout(symbol, entry_price, stoploss)` to execute entry
      7. **Cleanup:** Unmarks symbol (no longer needs monitoring)
    - **Error Handling:** Wraps callback in try-except to prevent crash
    - **Why Current Candle Open:** Stop-loss at breakout candle's open is tighter and more accurate
  
  - `get_last_price(self, symbol: str) -> Optional[float]`:
    - **Purpose:** Returns last known price for a symbol.
    - **Parameters:** `symbol` - Symbol name
    - **Returns:** Last price (float) or None
    - **Usage:** 
      - DryRunOrderExecutor uses this for realistic order execution at current LTP
      - Real-time price monitoring
    - **Performance:** O(1) dictionary lookup
  
  - `is_breakout_triggered(self, symbol: str) -> bool`:
    - **Purpose:** Checks if breakout already triggered for symbol.
    - **Returns:** True if triggered
    - **Usage:** Prevents duplicate entry orders
  
  - `get_stats(self) -> dict`:
    - **Purpose:** Returns breakout statistics.
    - **Returns:** Dictionary with breakouts_detected, currently_monitoring, breakouts_triggered
  
  - `reset(self)`:
    - **Purpose:** Resets state for next trading day.
    - **Logic:** Clears all dictionaries and counters

---

## core/risk.py

- **Purpose:** Real-time risk management with two critical functions: (1) Calculate position sizes using equal capital distribution, and (2) Monitor all positions tick-by-tick for stop-loss hits. This module protects capital by enforcing strict risk controls.

- **Key Responsibilities:**
  - Position sizing based on equal capital allocation across ALL marked stocks
  - Tick-by-tick stop-loss monitoring for instant exits
  - Daily loss limit enforcement

- **Class:** RiskManager
  
  - `__init__(self, portfolio, symbol_manager, config, marker)`:
    - **Purpose:** Initializes risk manager with all required module references.
    - **Parameters:**
      - `portfolio` - For checking positions and updating prices
      - `symbol_manager` - For token↔symbol conversions
      - `config` - For MAX_LOSS_PER_DAY and TOTAL_CAPITAL
      - `marker` - For getting total marked count (position sizing)
    - **State:** Initializes stops_hit counter
  
  - `set_on_exit_callback(self, callback: Callable[[str, float, str], None])`:
    - **Purpose:** Registers callback for position exits.
    - **Parameters:** `callback` - Function signature: `(symbol, exit_price, reason)`
    - **Usage:** TradingSystem registers `_execute_exit` here
  
  - `process_tick(self, tick: dict)`:
    - **Purpose:** HOT PATH - monitors EVERY tick for stop-loss hits.
    - **Parameters:** `tick` - Tick dictionary
    - **Called By:** TickRouter on every tick
    - **Logic Flow:**
      1. Extracts token and price from tick
      2. Converts token → symbol
      3. **Early Exit:** If no position exists for symbol, returns immediately
      4. Updates position's current price via `portfolio.update_position_price()`
      5. Gets position object from portfolio
      6. **Stop-Loss Check:** Calls `_check_stoploss(position, price)`
      7. **If Hit:** Calls `_trigger_exit()` with STOP_LOSS reason
    - **Performance:** O(1) checks, <50 microseconds
    - **Critical:** Must be FAST to exit positions immediately when stop-loss hit
  
  - `_check_stoploss(self, position, current_price: float) -> bool`:
    - **Purpose:** Simple comparison to check if stop-loss is hit.
    - **Logic:** Returns `current_price <= position.stoploss`
    - **Note:** Uses <= (not <) to ensure exit at or below stop-loss
  
  - `_trigger_exit(self, symbol: str, exit_price: float, reason: str)`:
    - **Purpose:** Triggers position exit when stop-loss hit.
    - **Parameters:**
      - `symbol` - Symbol to exit
      - `exit_price` - Current price
      - `reason` - Exit reason ("STOP_LOSS", "MANUAL", etc.)
    - **Logic:**
      1. Increments stops_hit counter
      2. Gets position details for logging
      3. Logs exit with symbol, price, reason, and entry price
      4. **Calls Callback:** Triggers `on_exit()` to execute sell order
    - **Error Handling:** Wraps callback in try-except
  
  - `calculate_position_size(self, symbol: str, entry_price: float, stoploss: float) -> int`:
    - **Purpose:** CRITICAL - calculates how many shares to buy using equal capital distribution.
    - **Parameters:**
      - `symbol` - Symbol name
      - `entry_price` - Breakout price
      - `stoploss` - Stop-loss price
    - **Returns:** Quantity (number of shares)
    - **Logic Flow:**
      1. Gets total marked count from marker (e.g., 5 stocks marked today)
      2. **Equal Distribution:** `capital_per_stock = TOTAL_CAPITAL / total_marked`
         - Example: ₹100,000 / 5 = ₹20,000 per stock
      3. **Quantity Calculation:** `quantity = int(capital_per_stock / entry_price)`
         - Example: ₹20,000 / ₹500 = 40 shares
      4. Returns 0 if quantity would be 0 (price too high)
      5. Logs allocation details
    - **Why Equal Distribution:** Ensures each marked stock gets same capital allocation
    - **Key Insight:** Uses TOTAL marked count (not current), so capital per stock stays constant
  
  - `check_max_loss(self) -> bool`:
    - **Purpose:** Checks if daily loss limit exceeded.
    - **Returns:** True if should stop trading
    - **Logic:**
      1. Calculates total loss: `abs(min(0, portfolio.total_pnl))`
      2. Compares against MAX_LOSS_PER_DAY from config
      3. Logs critical alert if exceeded
    - **Usage:** Called before taking new trades
  
  - `get_stats(self) -> dict`:
    - **Purpose:** Returns risk management statistics.
    - **Returns:** Dictionary with stops_hit count

---

## core/portfolio.py

- **Purpose:** Tracks all active and closed positions with real-time PNL calculations, manages capital allocation, and provides comprehensive statistics. This is the ACCOUNTING MODULE - it knows exactly what positions are open, their current value, and all historical trades. Thread-safe for concurrent access.

- **Key Data Structures:**
  - `positions: Dict[str, Position]` - Maps symbol → active Position object
  - `closed_positions: List[Position]` - List of all closed positions (trade history)
  - `lock: threading.Lock` - Thread-safe modifications

- **DataClass:** Position
  - **Purpose:** Immutable data structure representing a single position (entry to exit lifecycle).
  - **Attributes:**
    - `symbol: str` - Symbol name
    - `entry_price: float` - Price at which position was entered
    - `stoploss: float` - Stop-loss price level
    - `quantity: int` - Number of shares
    - `entry_time: datetime` - When position was opened
    - `current_price: float` - Last known price (updated on every tick)
    - `highest_price: float` - Tracks highest price reached (for trailing analysis)
    - `exit_price: Optional[float]` - Price at exit (None if still open)
    - `exit_time: Optional[datetime]` - When position was closed
    - `exit_reason: Optional[str]` - Why position was closed ("STOP_LOSS", "TARGET", etc.)
    - `realized_pnl: float` - Final PNL after exit
  
  - `__post_init__(self)`:
    - **Purpose:** Initializes highest_price to entry_price when position is created.
    - **Called:** Automatically by dataclass after __init__
  
  - `update_price(self, price: float)`:
    - **Purpose:** Updates current price and tracks highest price seen.
    - **Parameters:** `price` - New price from tick
    - **Logic:** 
      - Sets `current_price = price`
      - If `price > highest_price`, updates `highest_price`
    - **Usage:** Called by portfolio on every tick for active positions
  
  - `get_unrealized_pnl(self) -> float`:
    - **Purpose:** Calculates current unrealized PNL.
    - **Formula:** `(current_price - entry_price) * quantity`
    - **Returns:** PNL in rupees (positive = profit, negative = loss)
    - **Usage:** Real-time PNL monitoring, portfolio statistics
  
  - `get_pnl_percent(self) -> float`:
    - **Purpose:** Calculates PNL as percentage of entry value.
    - **Formula:** `((price - entry_price) / entry_price) * 100`
    - **Returns:** Percentage (e.g., 5.0 = 5% profit)
    - **Logic:** Uses exit_price if closed, current_price if open

- **Class:** Portfolio
  
  - `__init__(self, initial_capital: float)`:
    - **Purpose:** Initializes portfolio with starting capital.
    - **Parameters:** `initial_capital` - Total capital available for trading
    - **State Initialization:**
      - Sets `available_capital = initial_capital`
      - Creates empty dicts/lists for positions
      - Initializes counters: trades_today, winning_trades, losing_trades, total_pnl
    - **Thread Safety:** Creates lock
  
  - `add_position(self, symbol: str, entry_price: float, stoploss: float, quantity: int) -> Position`:
    - **Purpose:** Opens a new position and allocates capital.
    - **Parameters:** All position details
    - **Returns:** Created Position object
    - **Logic Flow:**
      1. Creates Position object with entry details
      2. Adds to `positions` dictionary
      3. Increments `trades_today` counter
      4. **Capital Allocation:** Calculates `capital_used = entry_price * quantity`
      5. Deducts from `available_capital`
      6. Logs position opening with remaining capital
    - **Thread Safety:** Wrapped in lock
    - **Usage:** Called by TradingSystem._execute_entry after order execution
  
  - `update_position_price(self, symbol: str, price: float)`:
    - **Purpose:** Updates current price for an active position.
    - **Parameters:**
      - `symbol` - Symbol name
      - `price` - New price from tick
    - **Logic:** Calls position's `update_price()` method
    - **Thread Safety:** Wrapped in lock
    - **Usage:** Called by RiskManager on every tick
  
  - `close_position(self, symbol: str, exit_price: float, exit_reason: str) -> Optional[Position]`:
    - **Purpose:** Closes position, calculates realized PNL, and returns capital.
    - **Parameters:**
      - `symbol` - Symbol to close
      - `exit_price` - Exit price
      - `exit_reason` - Reason for exit
    - **Returns:** Closed Position object or None if not found
    - **Logic Flow:**
      1. Removes position from `positions` dict
      2. Sets exit_price, exit_time, exit_reason on position
      3. **PNL Calculation:** `realized_pnl = (exit_price - entry_price) * quantity`
      4. Adds realized_pnl to `total_pnl`
      5. **Win/Loss Tracking:** Increments winning_trades or losing_trades
      6. **Capital Return:** Calculates `capital_returned = exit_price * quantity`
      7. Adds to `available_capital`
      8. Moves position to `closed_positions` list
      9. Logs closure with PNL and percentage
    - **Thread Safety:** Wrapped in lock
    - **Usage:** Called by TradingSystem._execute_exit
  
  - `get_position(self, symbol: str) -> Optional[Position]`:
    - **Purpose:** O(1) lookup for active position.
    - **Returns:** Position object or None
  
  - `has_position(self, symbol: str) -> bool`:
    - **Purpose:** O(1) check if position exists.
    - **Returns:** True if active position exists
    - **Usage:** Called by RiskManager before monitoring for stop-loss
  
  - `get_all_positions(self) -> Dict[str, Position]`:
    - **Purpose:** Returns copy of all active positions.
    - **Returns:** Dictionary copy (prevents external modification)
    - **Thread Safety:** Creates copy within lock
  
  - `get_total_unrealized_pnl(self) -> float`:
    - **Purpose:** Sums unrealized PNL across all active positions.
    - **Logic:** Iterates through positions, calls get_unrealized_pnl() on each, sums results
    - **Usage:** Real-time portfolio value monitoring
  
  - `get_total_capital(self) -> float`:
    - **Purpose:** Calculates total portfolio value (available + invested).
    - **Logic:**
      1. Calculates invested capital: sum of (current_price * quantity) for all positions
      2. Returns `available_capital + invested`
    - **Usage:** Portfolio valuation, performance tracking
  
  - `can_take_trade(self, max_trades: int) -> bool`:
    - **Purpose:** Checks if daily trade limit reached.
    - **Parameters:** `max_trades` - Maximum trades per day from config
    - **Returns:** True if can take more trades
    - **Logic:** Returns `trades_today < max_trades`
  
  - `get_stats(self) -> dict`:
    - **Purpose:** Comprehensive portfolio statistics.
    - **Returns:** Dictionary with:
      - `initial_capital` - Starting capital
      - `available_capital` - Current available cash
      - `total_capital` - Total portfolio value
      - `total_pnl` - Realized PNL
      - `unrealized_pnl` - Current unrealized PNL
      - `trades_today` - Number of trades taken
      - `active_positions` - Count of open positions
      - `winning_trades` - Number of profitable trades
      - `losing_trades` - Number of losing trades
      - `win_rate` - Win percentage
    - **Usage:** End-of-day reporting, real-time monitoring

---

## core/orders_live.py

- **Purpose:** Executes REAL orders on Zerodha platform via Kite API. This module handles actual money and real positions. Includes order placement, status tracking, error handling, and execution price retrieval. Used when DRY_RUN_MODE = False.

- **Key Responsibilities:**
  - Place buy/sell orders with proper parameters (exchange, product type, order type)
  - Track pending orders and their status
  - Handle API errors gracefully
  - Retrieve execution prices for PNL calculation

- **Class:** LiveOrderExecutor
  
  - `__init__(self, kite, symbol_manager, config)`:
    - **Purpose:** Initializes live order executor with Kite API connection.
    - **Parameters:**
      - `kite` - KiteConnect instance (authenticated)
      - `symbol_manager` - For symbol validation
      - `config` - For ORDER_TYPE, PRODUCT_TYPE, EXCHANGE settings
    - **State:** Creates dicts for pending_orders and executed_orders
    - **Counters:** Initializes orders_placed and orders_failed
  
  - `place_buy_order(self, symbol: str, quantity: int, price: Optional[float] = None) -> Optional[str]`:
    - **Purpose:** Places BUY order on exchange.
    - **Parameters:**
      - `symbol` - Trading symbol (e.g., "RELIANCE")
      - `quantity` - Number of shares to buy
      - `price` - Limit price (optional, used only for LIMIT orders)
    - **Returns:** Order ID (str) if successful, None if failed
    - **Logic Flow:**
      1. Builds order_params dictionary:
         - `tradingsymbol` = symbol
         - `exchange` = config['EXCHANGE'] (NSE)
         - `transaction_type` = 'BUY'
         - `quantity` = quantity
         - `product` = config['PRODUCT_TYPE'] (MIS/NRML)
         - `order_type` = config['ORDER_TYPE'] (MARKET/LIMIT)
      2. If LIMIT order, adds `price` parameter
      3. **API Call:** `kite.place_order(variety='regular', **order_params)`
      4. Stores order details in pending_orders dict
      5. Increments orders_placed counter
      6. Logs success with order ID
    - **Error Handling:** Catches exceptions, increments orders_failed, logs error, returns None
    - **Usage:** Called by TradingSystem._execute_entry
  
  - `place_sell_order(self, symbol: str, quantity: int, price: Optional[float] = None) -> Optional[str]`:
    - **Purpose:** Places SELL order on exchange.
    - **Parameters:** Same as place_buy_order
    - **Returns:** Order ID or None
    - **Key Difference:** Always uses MARKET order for exits (speed priority)
    - **Logic:** Similar to buy order but with transaction_type='SELL'
    - **Why MARKET:** Exits need to be fast, especially for stop-losses
  
  - `get_order_status(self, order_id: str) -> Optional[dict]`:
    - **Purpose:** Fetches current status of an order from Kite.
    - **Parameters:** `order_id` - Order ID from place_order
    - **Returns:** Order dictionary with status, price, quantity, etc.
    - **Logic:**
      1. Calls `kite.orders()` to get all orders
      2. Searches for matching order_id
      3. Returns order dict if found
    - **Usage:** Check if order executed, get execution price
  
  - `cancel_order(self, order_id: str) -> bool`:
    - **Purpose:** Cancels a pending order.
    - **Parameters:** `order_id` - Order to cancel
    - **Returns:** True if successful
    - **API Call:** `kite.cancel_order(variety='regular', order_id=order_id)`
    - **Usage:** Cancel unfilled limit orders
  
  - `get_average_price(self, order_id: str) -> Optional[float]`:
    - **Purpose:** Gets actual execution price for completed order.
    - **Parameters:** `order_id` - Order ID
    - **Returns:** Average execution price (float) or None
    - **Logic:**
      1. Calls get_order_status()
      2. Checks if status == 'COMPLETE'
      3. Returns order['average_price']
    - **Critical:** Used for accurate PNL calculation
  
  - `get_stats(self) -> dict`:
    - **Purpose:** Returns order execution statistics.
    - **Returns:** Dictionary with orders_placed, orders_failed, pending_orders count

---

## core/orders_dryrun.py

- **Purpose:** Simulates order execution using REAL-TIME tick prices for ultra-realistic dry-run testing. Instead of artificial slippage, this uses actual Last Traded Price (LTP) from the market at order placement time. This provides the most accurate backtesting possible without risking real capital.

- **Key Innovation:** Uses BreakoutEngine's last_prices to get current LTP, simulating exactly what would happen in live trading.

- **Class:** DryRunOrderExecutor
  
  - `__init__(self, symbol_manager, config, breakout_engine)`:
    - **Purpose:** Initializes dry-run executor with LTP access.
    - **Parameters:**
      - `symbol_manager` - For symbol validation
      - `config` - For ORDER_TYPE, PRODUCT_TYPE settings
      - `breakout_engine` - **KEY:** For accessing real-time LTP via get_last_price()
    - **State:** Creates orders dict for tracking simulated orders
    - **Counters:** orders_placed, orders_executed
  
  - `_get_current_ltp(self, symbol: str) -> Optional[float]`:
    - **Purpose:** Gets REAL current market price from live ticks.
    - **Parameters:** `symbol` - Symbol name
    - **Returns:** Current LTP (float) or None
    - **Logic:** Calls `breakout_engine.get_last_price(symbol)`
    - **Why Important:** This makes dry-run execution realistic - uses actual market prices
    - **Logs:** Debug message with current LTP
  
  - `place_buy_order(self, symbol: str, quantity: int, price: Optional[float] = None) -> Optional[str]`:
    - **Purpose:** Simulates BUY order using real LTP.
    - **Parameters:** Same as live executor
    - **Returns:** Generated order ID (UUID)
    - **Logic Flow:**
      1. Generates unique order_id using uuid.uuid4()
      2. **Gets Real LTP:** Calls `_get_current_ltp(symbol)`
      3. **Execution Price:** Uses LTP if available, else falls back to requested price
      4. Creates order dict with:
         - order_id, symbol, transaction_type='BUY'
         - quantity, order_type, requested_price, execution_price
         - status='COMPLETE', timestamp
      5. Stores in orders dict
      6. Increments counters
      7. **Logs:** Shows execution price, requested price, and difference
    - **Realism:** Price difference shows realistic slippage from market movement
    - **Example Log:** `[DRY-RUN] ✓ BUY: RELIANCE x40 @ 2501.25 (Breakout: 2500.00, Diff: +1.25)`
  
  - `place_sell_order(self, symbol: str, quantity: int, price: Optional[float] = None) -> Optional[str]`:
    - **Purpose:** Simulates SELL order using real LTP.
    - **Logic:** Identical to buy order but with transaction_type='SELL'
    - **Market Order:** Always uses MARKET type for exits (matches live behavior)
    - **Realism:** Shows actual slippage when stop-loss hit
  
  - `get_order_status(self, order_id: str) -> Optional[dict]`:
    - **Purpose:** Returns simulated order details.
    - **Returns:** Order dict from orders dictionary
  
  - `cancel_order(self, order_id: str) -> bool`:
    - **Purpose:** Simulates order cancellation.
    - **Logic:** Sets order['status'] = 'CANCELLED'
  
  - `get_average_price(self, order_id: str) -> Optional[float]`:
    - **Purpose:** Returns execution price for PNL calculation.
    - **Logic:**
      1. Gets order from orders dict
      2. Checks if status == 'COMPLETE'
      3. Returns order['execution_price']
    - **Critical:** This is the REAL LTP at execution time
  
  - `get_stats(self) -> dict`:
    - **Purpose:** Returns execution statistics.
    - **Returns:** orders_placed, orders_executed, orders_failed (always 0)
  
  - `get_all_orders(self) -> list`:
    - **Purpose:** Returns all simulated orders for analysis.
    - **Returns:** List of all order dicts
    - **Usage:** Post-trade analysis, debugging, performance review

---

## core/trade_logger.py

- **Purpose:** Maintains a permanent audit trail of all trades in CSV format. Every entry and exit is logged with full details for compliance, analysis, and performance review. Thread-safe for concurrent logging. Creates daily log files automatically.

- **CSV Fields:** timestamp, symbol, action (BUY/SELL), quantity, price, value, pnl, pnl_percent, reason, order_id

- **Class:** TradeLogger
  
  - `__init__(self, config)`:
    - **Purpose:** Initializes logger and creates/opens daily CSV file.
    - **Parameters:** `config` - For OUTPUT_DIR and TRADES_CSV_PREFIX
    - **Logic Flow:**
      1. Creates output directory if not exists
      2. Generates filename: `{prefix}{YYYYMMDD}.csv` (e.g., trades_20250124.csv)
      3. Defines CSV field names
      4. Creates empty buffer list (for future batching)
      5. Creates thread lock for safe concurrent writes
      6. Calls `_initialize_csv()` to create file with headers
    - **Thread Safety:** Creates lock for write operations
  
  - `_initialize_csv(self)`:
    - **Purpose:** Creates CSV file with headers if it doesn't exist.
    - **Logic:**
      1. Checks if csv_path exists
      2. If not, creates file and writes header row
      3. Logs file creation
    - **Idempotent:** Safe to call multiple times
  
  - `log_entry(self, symbol: str, quantity: int, price: float, order_id: str)`:
    - **Purpose:** Logs a BUY (entry) trade.
    - **Parameters:**
      - `symbol` - Symbol entered
      - `quantity` - Shares bought
      - `price` - Entry price
      - `order_id` - Order ID from executor
    - **Logic:**
      1. Creates trade dict with:
         - timestamp = current time (ISO format)
         - action = 'BUY'
         - value = quantity × price
         - pnl = 0 (no PNL on entry)
         - reason = 'BREAKOUT'
      2. Calls `_write_trade()` to append to CSV
      3. Logs debug message
    - **Thread Safety:** Write operation is thread-safe
  
  - `log_exit(self, symbol: str, quantity: int, entry_price: float, exit_price: float, reason: str, order_id: str)`:
    - **Purpose:** Logs a SELL (exit) trade with PNL calculation.
    - **Parameters:**
      - `symbol` - Symbol exited
      - `quantity` - Shares sold
      - `entry_price` - Original entry price
      - `exit_price` - Exit price
      - `reason` - Exit reason ("STOP_LOSS", "TARGET", etc.)
      - `order_id` - Order ID
    - **Logic:**
      1. **PNL Calculation:**
         - `pnl = (exit_price - entry_price) × quantity`
         - `pnl_percent = ((exit_price - entry_price) / entry_price) × 100`
      2. Creates trade dict with:
         - action = 'SELL'
         - value = quantity × exit_price
         - Calculated PNL and percentage
         - Exit reason
      3. Writes to CSV
      4. Logs debug message with PNL
    - **Critical:** This is the permanent record of trade performance
  
  - `_write_trade(self, trade: Dict)`:
    - **Purpose:** Thread-safe write to CSV file.
    - **Parameters:** `trade` - Dictionary with all trade fields
    - **Logic:**
      1. Acquires lock
      2. Opens CSV in append mode
      3. Writes row using csv.DictWriter
      4. Releases lock
    - **Error Handling:** Catches and logs write errors
    - **Thread Safety:** Lock ensures no concurrent writes corrupt file
  
  - `get_log_path(self) -> Path`:
    - **Purpose:** Returns path to current day's log file.
    - **Usage:** For external analysis tools, reporting

---

## core/utils.py

- **Purpose:** Provides utility functions for time handling, price formatting, performance monitoring, and common calculations. These are helper functions used throughout the system for consistent behavior.

- **Decorators:**
  - `@timeit`: Performance profiling decorator that measures and logs function execution time in milliseconds. Useful for identifying bottlenecks.

- **Time Functions:**
  
  - `is_market_open(current_time: datetime = None) -> bool`:
    - **Purpose:** Checks if current time is within market trading hours.
    - **Parameters:** `current_time` - Optional time to check (defaults to now)
    - **Returns:** True if between 9:15 AM and 3:30 PM
    - **Logic:** Compares time against MARKET_OPEN (9:15) and MARKET_CLOSE (15:30)
    - **Usage:** Pre-flight checks, tick filtering
  
  - `is_within_first_minute(current_time: datetime = None) -> bool`:
    - **Purpose:** Checks if within the critical 9:15-9:16 window.
    - **Returns:** True if between 9:15:00 and 9:16:00
    - **Usage:** Marker uses this to identify 9:15 candles
  
  - `wait_until(target_time: dt_time, check_interval: float = 1.0)`:
    - **Purpose:** Blocks execution until a specific time is reached.
    - **Parameters:**
      - `target_time` - Time to wait for (e.g., 9:15 AM)
      - `check_interval` - How often to check (seconds)
    - **Logic:** Loops with sleep until current time >= target time
    - **Usage:** main.py uses this to wait for market open

- **Formatting Functions:**
  
  - `format_price(price: float, decimals: int = 2) -> str`:
    - **Purpose:** Formats price with rupee symbol and proper decimals.
    - **Returns:** String like "₹2,500.50"
    - **Usage:** Logging, reporting
  
  - `format_pnl(pnl: float) -> str`:
    - **Purpose:** Formats PNL with sign and rupee symbol.
    - **Returns:** String like "+₹1,250.00" or "-₹500.00"
    - **Logic:** Adds + sign for positive PNL
  
  - `calculate_risk_reward_ratio(entry: float, stoploss: float, target: float) -> float`:
    - **Purpose:** Calculates risk:reward ratio for a trade.
    - **Formula:** `(target - entry) / (entry - stoploss)`
    - **Returns:** Ratio (e.g., 2.0 means 1:2 risk:reward)
    - **Usage:** Trade evaluation, strategy analysis
  
  - `round_to_tick_size(price: float, tick_size: float = 0.05) -> float`:
    - **Purpose:** Rounds price to valid tick increment.
    - **Parameters:** `tick_size` - Minimum price increment (default 0.05 for NSE)
    - **Returns:** Rounded price
    - **Usage:** Order price validation

- **Class:** PerformanceMonitor
  - **Purpose:** Tracks execution times for performance profiling and optimization.
  
  - `__init__(self)`:
    - Creates empty dicts for metrics and start_times
  
  - `start_timer(self, name: str)`:
    - **Purpose:** Starts timing an operation.
    - **Logic:** Records current time in start_times[name]
  
  - `stop_timer(self, name: str)`:
    - **Purpose:** Stops timing and records elapsed time.
    - **Returns:** Elapsed time in milliseconds
    - **Logic:**
      1. Calculates elapsed = current_time - start_time
      2. Appends to metrics[name] list
      3. Removes from start_times
  
  - `get_stats(self, name: str) -> dict`:
    - **Purpose:** Returns statistics for a metric.
    - **Returns:** Dict with count, avg, min, max, last
    - **Usage:** Performance analysis
  
  - `print_stats(self)`:
    - **Purpose:** Logs all performance statistics.
    - **Output:** Formatted table with avg/min/max for each metric

- **Global Instance:** `perf_monitor` - Ready-to-use performance monitor instance

---

## websocket/ws_manager.py

- **Purpose:** Manages the KiteTicker WebSocket connection for receiving real-time market data. Handles connection lifecycle, auto-reconnection on failures, subscription management, and tick distribution. This is the DATA PIPELINE - all market data flows through this module.

- **Key Features:**
  - Auto-reconnection with configurable retry logic
  - Subscription management (can subscribe before or after connection)
  - Full tick mode for complete OHLC data
  - Error handling and logging

- **Class:** WebSocketManager
  
  - `__init__(self, api_key: str, access_token: str, config)`:
    - **Purpose:** Initializes WebSocket manager with Kite credentials.
    - **Parameters:**
      - `api_key` - Zerodha API key
      - `access_token` - Valid access token
      - `config` - For reconnection settings
    - **Logic:**
      1. Creates KiteTicker instance
      2. Initializes empty subscription list
      3. Sets up callback placeholders
      4. Initializes connection state variables
      5. Calls `_setup_callbacks()` to register event handlers
  
  - `_setup_callbacks(self)`:
    - **Purpose:** Registers all WebSocket event handlers.
    - **Callbacks Defined:**
      
      - `on_connect(ws, response)`: 
        - Logs connection success
        - Subscribes to all tokens in subscribed_tokens list
        - Sets MODE_FULL for complete tick data
        - Resets reconnect counter
      
      - `on_close(ws, code, reason)`:
        - Logs disconnection
        - Sets is_connected = False
        - Attempts reconnection
      
      - `on_error(ws, code, reason)`:
        - Logs error details
      
      - `on_reconnect(ws, attempts_count)`:
        - Logs reconnection attempt number
      
      - `on_noreconnect(ws)`:
        - Logs critical failure when max reconnection attempts reached
      
      - `on_ticks(ws, ticks)`: **HOT PATH**
        - Receives batch of ticks from WebSocket
        - Calls registered on_ticks_callback immediately
        - Error handling to prevent callback crashes
  
  - `set_on_ticks_callback(self, callback: Callable)`:
    - **Purpose:** Registers callback for tick data.
    - **Parameters:** `callback` - Function to call with tick list
    - **Usage:** TradingSystem registers TickRouter.route_ticks here
  
  - `subscribe(self, tokens: List[int])`:
    - **Purpose:** Subscribes to instrument tokens for tick streaming.
    - **Parameters:** `tokens` - List of instrument tokens
    - **Logic:**
      1. Stores tokens in subscribed_tokens
      2. If already connected, subscribes immediately
      3. If not connected, will subscribe on next connection
    - **Mode:** Sets MODE_FULL for complete OHLCV data
  
  - `start(self)`:
    - **Purpose:** Starts WebSocket connection (BLOCKING).
    - **Logic:** Calls `ticker.connect(threaded=False)`
    - **Usage:** Called by main.py to enter main trading loop
    - **Blocks:** This call blocks until connection closes
  
  - `start_threaded(self)`:
    - **Purpose:** Starts WebSocket in background thread (NON-BLOCKING).
    - **Logic:** Calls `ticker.connect(threaded=True)`
    - **Usage:** For testing or when running other operations concurrently
  
  - `stop(self)`:
    - **Purpose:** Gracefully closes WebSocket connection.
    - **Logic:** Calls ticker.close(), sets is_connected = False
    - **Usage:** System shutdown
  
  - `_attempt_reconnect(self)`:
    - **Purpose:** Handles reconnection logic after disconnection.
    - **Parameters:** Uses config['WS_RECONNECT_MAX_TRIES'] and ['WS_RECONNECT_DELAY']
    - **Logic:**
      1. Checks if max attempts exceeded
      2. Increments reconnect counter
      3. Sleeps for configured delay
      4. Attempts connection in threaded mode
    - **Error Handling:** Logs failure if reconnection fails
  
  - `is_active(self) -> bool`:
    - **Purpose:** Checks if WebSocket is currently connected.
    - **Returns:** True if connected
    - **Usage:** Health checks, monitoring

---

## websocket/tick_router.py

- **Purpose:** The TRAFFIC CONTROLLER - receives batches of ticks from WebSocket and distributes them to CandleBuilder, BreakoutEngine, and RiskManager. Ensures all modules receive real-time data with minimal latency. Single-threaded for maximum speed.

- **Design Philosophy:** Instead of each module connecting to WebSocket separately, TickRouter provides centralized distribution. This simplifies architecture and ensures consistent tick delivery.

- **Class:** TickRouter
  
  - `__init__(self, candle_builder, breakout_engine, risk_manager)`:
    - **Purpose:** Initializes router with references to all tick consumers.
    - **Parameters:**
      - `candle_builder` - For candle aggregation
      - `breakout_engine` - For breakout detection
      - `risk_manager` - For stop-loss monitoring
    - **State:** Initializes performance counters and market hours
  
  - `route_ticks(self, ticks: List[dict])`:
    - **Purpose:** CRITICAL HOT PATH - routes batch of ticks to all engines.
    - **Parameters:** `ticks` - List of tick dictionaries from WebSocket
    - **Called By:** WebSocketManager's on_ticks callback
    - **Logic Flow:**
      1. **Early Exit:** Returns if ticks list is empty
      2. **Market Hours Check:** Only processes during 9:15 AM - 3:30 PM
      3. **Batch Processing:** Iterates through each tick
      4. Calls `_route_single_tick()` for each
      5. Increments ticks_processed counter
    - **Performance:** Processes thousands of ticks per second
    - **Why Market Hours Check:** Prevents processing pre-market or post-market data
  
  - `_route_single_tick(self, tick: dict)`:
    - **Purpose:** ULTRA CRITICAL - routes one tick to all three engines.
    - **Parameters:** `tick` - Single tick dictionary
    - **Logic Flow:**
      1. **CandleBuilder:** Always processes (updates candles)
      2. **BreakoutEngine:** Processes (checks marked symbols only internally)
      3. **RiskManager:** Processes (checks positions only internally)
    - **Error Handling:** Wraps in try-except to prevent single tick error from crashing system
    - **Performance:** Must be <100 microseconds for real-time processing
    - **Sequential Processing:** Calls engines in order (candles first, then breakout, then risk)
  
  - `get_stats(self) -> dict`:
    - **Purpose:** Returns routing statistics.
    - **Returns:** Dictionary with:
      - `ticks_processed` - Total ticks routed
      - `candles_active` - Number of active candles being built
      - `marked_symbols` - Number of symbols marked for breakout
    - **Usage:** Performance monitoring, debugging

---

## data/symbols.csv

- **Purpose:** Contains the list of stocks to trade. This is your TRADING UNIVERSE - only symbols in this file will be monitored and traded.

- **Format:**
  - CSV file with header row
  - Column name: `symbol` (or `trading_symbol`, `tradingsymbol`, `Symbol`, `SYMBOL`)
  - One symbol per row
  - Example:
    ```csv
    symbol
    RELIANCE
    TCS
    INFY
    HDFCBANK
    ICICIBANK
    ```

- **Usage:**
  - **Loaded By:** SymbolManager.load_symbols_from_csv()
  - **When:** During system initialization in main.py
  - **Processing:** Symbols are deduplicated, sorted, and mapped to instrument tokens

- **Customization:**
  - **Add Symbols:** Add new rows to include more stocks
  - **Remove Symbols:** Delete rows to exclude stocks
  - **Recommendations:**
    - Use liquid stocks (high volume)
    - Avoid penny stocks (unreliable data)
    - Start with 10-20 symbols for testing
    - Expand to 50-100 for live trading
  
- **Symbol Format:**
  - Use exact NSE trading symbols
  - All uppercase (e.g., "RELIANCE" not "reliance")
  - No spaces or special characters
  - Verify symbols on NSE website or Zerodha Kite

- **Performance Impact:**
  - More symbols = longer historical data fetch time
  - More symbols = more ticks to process
  - Recommended: 50-100 symbols for optimal performance

---

## output/trades_*.csv

- **Purpose:** Daily trade logs generated automatically by TradeLogger. These are your PERMANENT RECORDS - every trade is logged here for audit, analysis, and compliance.

- **Filename Format:** `trades_YYYYMMDD.csv`
  - Example: `trades_20250124.csv` for January 24, 2025
  - New file created each day automatically
  - Files never overwritten (each day is separate)

- **CSV Structure:**
  - **Header Row:** timestamp, symbol, action, quantity, price, value, pnl, pnl_percent, reason, order_id
  
  - **Entry Row Example:**
    ```csv
    2025-01-24T09:17:35.123456,RELIANCE,BUY,40,2501.25,100050.00,0,0,BREAKOUT,abc123
    ```
  
  - **Exit Row Example:**
    ```csv
    2025-01-24T10:45:12.789012,RELIANCE,SELL,40,2495.50,99820.00,-230.00,-0.92,STOP_LOSS,def456
    ```

- **Field Descriptions:**
  - `timestamp`: ISO format datetime when trade executed
  - `symbol`: Stock symbol (e.g., RELIANCE)
  - `action`: BUY (entry) or SELL (exit)
  - `quantity`: Number of shares
  - `price`: Execution price per share
  - `value`: Total value (quantity × price)
  - `pnl`: Profit/Loss in rupees (0 for entries, calculated for exits)
  - `pnl_percent`: PNL as percentage (0 for entries, calculated for exits)
  - `reason`: BREAKOUT (entry) or STOP_LOSS/TARGET/MANUAL (exit)
  - `order_id`: Unique order identifier from executor

- **Usage:**
  - **Analysis:** Import into Excel/Python for performance analysis
  - **Compliance:** Audit trail for regulatory requirements
  - **Debugging:** Verify trade execution and timing
  - **Reporting:** Generate daily/weekly/monthly reports
  - **Backtesting:** Compare with expected results

- **Analysis Tips:**
  - Calculate win rate: (winning trades / total trades) × 100
  - Average PNL per trade: sum(pnl) / count(trades)
  - Best/worst trades: sort by pnl_percent
  - Time analysis: group by hour to find best trading times
  - Symbol analysis: group by symbol to find best performers

- **File Location:** `output/` directory (created automatically)

- **Thread Safety:** TradeLogger uses locks to ensure concurrent writes don't corrupt the file

---

This document provides a comprehensive, crystal-clear reference for understanding every file, class, function, data structure, and configuration parameter in the 9:15 Breakout Trading System. Each section explains not just WHAT the code does, but WHY it does it, HOW it works internally, and WHEN it's used in the system flow.
