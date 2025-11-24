# Line-by-Line Execution Order
## Every Line of Code in Exact Execution Sequence
**Scenario: Running `python main.py` at 9:00 AM**

---

## EXECUTION SEQUENCE

### Line 1-3: Python Interpreter Starts
**File:** `main.py`
**Lines:** 325-327
```python
if __name__ == "__main__":
    try:
        main()
```
**Explanation:** Python checks if this is the main module being run (not imported). If yes, calls `main()` function inside a try-except block to catch errors.

---

### Line 4: main() Function Begins
**File:** `main.py`
**Line:** 306
```python
system = TradingSystem()
```
**Explanation:** Creates a new `TradingSystem` object. This triggers the `__init__()` constructor method.

---

### Line 5-7: Initialization Banner
**File:** `main.py`
**Lines:** 52-54
```python
logger.info("=" * 60)
logger.info("9:15 BREAKOUT TRADING SYSTEM - INITIALIZING")
logger.info("=" * 60)
```
**Explanation:** Prints startup banner to console.
**Output:**
```
09:00:00 | INFO | ============================================================
09:00:00 | INFO | 9:15 BREAKOUT TRADING SYSTEM - INITIALIZING
09:00:00 | INFO | ============================================================
```

---

### Line 8: Load Environment Variables
**File:** `main.py`
**Line:** 57
```python
load_dotenv('config/secrets.env')
```
**Explanation:** Loads API credentials from `config/secrets.env` file into environment variables. Sets `API_KEY` and `ACCESS_TOKEN`.

---

### Line 9: Initialize Kite Connection
**File:** `main.py`
**Line:** 60
```python
self.kite = self._initialize_kite()
```
**Explanation:** Calls `_initialize_kite()` method to connect to Zerodha.

---

### Line 10-11: Get API Credentials
**File:** `main.py`
**Lines:** 92-93
```python
api_key = os.getenv('API_KEY')
access_token = os.getenv('ACCESS_TOKEN')
```
**Explanation:** Retrieves API credentials from environment variables that were loaded in Line 8.

---

### Line 12-14: Validate Credentials
**File:** `main.py`
**Lines:** 95-97
```python
if not api_key or not access_token:
    logger.error("API_KEY or ACCESS_TOKEN not found in secrets.env")
    sys.exit(1)
```
**Explanation:** Checks if credentials exist. If missing, logs error and exits program with code 1.
**Possible Output (if missing):**
```
09:00:00 | ERROR | API_KEY or ACCESS_TOKEN not found in secrets.env
```

---

### Line 15-16: Create Kite Object
**File:** `main.py`
**Lines:** 99-100
```python
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
```
**Explanation:** Creates KiteConnect object with API key and sets the access token for authentication.

---

### Line 17-20: Test Connection
**File:** `main.py`
**Lines:** 103-106
```python
try:
    profile = kite.profile()
    logger.info(f"✓ Connected to Zerodha | User: {profile['user_name']}")
    return kite
```
**Explanation:** Makes API call to Zerodha to verify connection works. If successful, logs username and returns kite object.
**Output:**
```
09:00:00 | INFO | ✓ Connected to Zerodha | User: KARTHIK
```

---

### Line 21-23: Create Config Dictionary
**File:** `main.py`
**Lines:** 63-78
```python
self.config = {
    'MAX_TRADES_PER_DAY': MAX_TRADES_PER_DAY,
    'TOTAL_CAPITAL': TOTAL_CAPITAL,
    # ... all config values
}
```
**Explanation:** Creates dictionary with all configuration settings from `config/settings.py` for easy passing to modules.

---

### Line 24: Initialize All Modules
**File:** `main.py`
**Line:** 81
```python
self._initialize_modules()
```
**Explanation:** Calls method to create all trading components (symbol manager, candle builder, etc.).

---

### Line 25-26: Symbol Manager - Log
**File:** `main.py`
**Lines:** 115-116
```python
logger.info("Loading symbols...")
self.symbol_manager = SymbolManager(self.kite)
```
**Explanation:** Logs message and creates SymbolManager object.
**Output:**
```
09:00:00 | INFO | Loading symbols...
```

---

### Line 27: Symbol Manager - Load CSV
**File:** `main.py`
**Line:** 117
```python
self.symbol_manager.load_symbols_from_csv(SYMBOLS_CSV_PATH)
```
**Explanation:** Reads `data/symbols.csv` file and loads symbol names (RELIANCE, TCS, etc.).

---

### Line 28: Symbol Manager - Map Tokens
**File:** `main.py`
**Line:** 118
```python
self.symbol_manager.map_tokens(EXCHANGE)
```
**Explanation:** Maps each symbol name to its instrument token by querying Zerodha API.
**Result:** `symbols = {'RELIANCE': 738561, 'TCS': 2953217, ...}`

---

### Line 29-30: Historical Data Manager
**File:** `main.py`
**Lines:** 121-122
```python
logger.info("Initializing historical data manager...")
self.historical_manager = HistoricalDataManager(self.kite, self.symbol_manager)
```
**Explanation:** Creates manager for fetching historical data.
**Output:**
```
09:00:00 | INFO | Initializing historical data manager...
```

---

### Line 31: Candle Builder
**File:** `main.py`
**Line:** 125
```python
self.candle_builder = CandleBuilder(self.symbol_manager)
```
**Explanation:** Creates candle builder that will construct 1-minute candles from ticks.

---

### Line 32: Portfolio
**File:** `main.py`
**Line:** 128
```python
self.portfolio = Portfolio(TOTAL_CAPITAL)
```
**Explanation:** Creates portfolio tracker with initial capital (₹100,000).

---

### Line 33: Stock Marker
**File:** `main.py`
**Line:** 131
```python
self.marker = StockMarker(self.historical_manager, self.config)
```
**Explanation:** Creates marker that will evaluate and mark qualifying stocks at 9:16.

---

### Line 34: Breakout Engine
**File:** `main.py`
**Line:** 134
```python
self.breakout_engine = BreakoutEngine(self.marker, self.symbol_manager, self.config, self.candle_builder)
```
**Explanation:** Creates engine that monitors marked stocks for breakout.

---

### Line 35: Risk Manager
**File:** `main.py`
**Line:** 137
```python
self.risk_manager = RiskManager(self.portfolio, self.symbol_manager, self.config, self.marker)
```
**Explanation:** Creates risk manager for position sizing and stop-loss monitoring.

---

### Line 36-39: Order Executor
**File:** `main.py`
**Lines:** 140-145
```python
if DRY_RUN_MODE:
    self.order_executor = DryRunOrderExecutor(self.symbol_manager, self.config, self.breakout_engine)
    logger.info("✓ Dry-run order executor initialized")
else:
    self.order_executor = LiveOrderExecutor(self.kite, self.symbol_manager, self.config)
    logger.info("✓ Live order executor initialized")
```
**Explanation:** Creates order executor based on mode (dry-run or live).
**Output:**
```
09:00:00 | INFO | ✓ Dry-run order executor initialized
```

---

### Line 40: Trade Logger
**File:** `main.py`
**Line:** 148
```python
self.trade_logger = TradeLogger(self.config)
```
**Explanation:** Creates logger that writes trades to CSV file.

---

### Line 41: Tick Router
**File:** `main.py`
**Line:** 151
```python
self.tick_router = TickRouter(self.candle_builder, self.breakout_engine, self.risk_manager)
```
**Explanation:** Creates router that distributes incoming ticks to all engines.

---

### Line 42-43: WebSocket Manager
**File:** `main.py`
**Lines:** 154-156
```python
api_key = os.getenv('API_KEY')
access_token = os.getenv('ACCESS_TOKEN')
self.ws_manager = WebSocketManager(api_key, access_token, self.config)
```
**Explanation:** Creates WebSocket manager for receiving live tick data from Zerodha.

---

### Line 44: Modules Initialized Log
**File:** `main.py`
**Line:** 158
```python
logger.info("✓ All modules initialized")
```
**Output:**
```
09:00:00 | INFO | ✓ All modules initialized
```

---

### Line 45: Setup Callbacks
**File:** `main.py`
**Line:** 84
```python
self._setup_callbacks()
```
**Explanation:** Wires up event handlers between modules.

---

### Line 46-49: Candle Close Callback
**File:** `main.py`
**Lines:** 164-167
```python
def on_candle_close(candle):
    self.marker.evaluate_and_mark(candle)

self.candle_builder.set_on_candle_close_callback(on_candle_close)
```
**Explanation:** Sets up callback so when a candle closes, the marker evaluates it. **This is how stocks get marked at 9:16 AM.**

---

### Line 50-53: Breakout Callback
**File:** `main.py`
**Lines:** 170-173
```python
def on_breakout(symbol, entry_price, stoploss):
    self._execute_entry(symbol, entry_price, stoploss)

self.breakout_engine.set_on_breakout_callback(on_breakout)
```
**Explanation:** Sets up callback so when breakout is detected, entry is executed. **This is how trades get placed.**

---

### Line 54-57: Exit Callback
**File:** `main.py`
**Lines:** 176-179
```python
def on_exit(symbol, exit_price, reason):
    self._execute_exit(symbol, exit_price, reason)

self.risk_manager.set_on_exit_callback(on_exit)
```
**Explanation:** Sets up callback so when stop-loss is hit, exit is executed.

---

### Line 58: WebSocket Callback
**File:** `main.py`
**Line:** 182
```python
self.ws_manager.set_on_ticks_callback(self.tick_router.route_ticks)
```
**Explanation:** Sets up callback so when ticks arrive from WebSocket, they're routed to all engines. **This is the critical path for live data.**

---

### Line 59: Callbacks Configured Log
**File:** `main.py`
**Line:** 184
```python
logger.info("✓ Callbacks configured")
```
**Output:**
```
09:00:01 | INFO | ✓ Callbacks configured
```

---

### Line 60-62: Mode Summary
**File:** `main.py`
**Lines:** 86-88
```python
logger.info(f"Mode: {'DRY-RUN' if DRY_RUN_MODE else 'LIVE TRADING'}")
logger.info(f"Capital: ₹{TOTAL_CAPITAL:,.2f}")
logger.info(f"Max Trades: {MAX_TRADES_PER_DAY}")
```
**Output:**
```
09:00:01 | INFO | Mode: DRY-RUN
09:00:01 | INFO | Capital: ₹100,000.00
09:00:01 | INFO | Max Trades: 5
```

---

### Line 63: Get Current Time
**File:** `main.py`
**Line:** 309
```python
current_time = datetime.now().time()
```
**Explanation:** Gets current time (09:00:01).

---

### Line 64: Check if Before Market Open
**File:** `main.py`
**Line:** 311
```python
if current_time < MARKET_OPEN_TIME or current_time > MARKET_CLOSE_TIME:
```
**Explanation:** Checks if time is before 9:15 AM or after 3:30 PM.
**Evaluation:** `09:00:01 < 09:15:00` → **TRUE**, enters if block.

---

### Line 65-66: Pre-Market Logs
**File:** `main.py`
**Lines:** 312-313
```python
logger.info(f"Current time: {current_time.strftime('%H:%M:%S')} (outside market hours)")
logger.info("Fetching historical data...")
```
**Output:**
```
09:00:01 | INFO | Current time: 09:00:01 (outside market hours)
09:00:01 | INFO | Fetching historical data...
```

---

### Line 67: Fetch Historical Data
**File:** `main.py`
**Line:** 314
```python
system.fetch_historical_data()
```
**Explanation:** Calls method to fetch 14 days of historical data.

---

### Line 68-70: Historical Data Banner
**File:** `main.py`
**Lines:** 260-262
```python
logger.info("=" * 60)
logger.info("FETCHING HISTORICAL DATA")
logger.info("=" * 60)
```
**Output:**
```
09:00:01 | INFO | ============================================================
09:00:01 | INFO | FETCHING HISTORICAL DATA
09:00:01 | INFO | ============================================================
```

---

### Line 71: Fetch All Historical Data
**File:** `main.py`
**Line:** 264
```python
self.historical_manager.fetch_all_historical_data(days=HISTORICAL_DAYS)
```
**Explanation:** Fetches 14 days of data for all symbols. Takes ~10-15 seconds due to API rate limits.
**Output (for each symbol):**
```
09:00:02 | INFO | Fetching historical data for RELIANCE...
09:00:03 | INFO | ✓ RELIANCE: 14 days of data fetched
09:00:04 | INFO | Fetching historical data for TCS...
09:00:05 | INFO | ✓ TCS: 14 days of data fetched
...
```

---

### Line 72: Historical Data Ready
**File:** `main.py`
**Line:** 266
```python
logger.info("✓ Historical data ready")
```
**Output:**
```
09:00:15 | INFO | ✓ Historical data ready
```

---

### Line 73: Waiting Log
**File:** `main.py`
**Line:** 317
```python
logger.info("Waiting for market to open at 9:15 AM...")
```
**Output:**
```
09:00:15 | INFO | Waiting for market to open at 9:15 AM...
```

---

### Line 74-75: Wait Loop (RUNS FOR 14 MINUTES 45 SECONDS)
**File:** `main.py`
**Lines:** 318-319
```python
while datetime.now().time() < MARKET_OPEN_TIME or datetime.now().time() > MARKET_CLOSE_TIME:
    time_module.sleep(1)
```
**Explanation:** Loops every second checking if time >= 9:15:00. **System is idle here.**
**Loop iterations:**
```
09:00:15 → Check: 09:00:15 < 09:15:00? YES → Sleep 1 sec
09:00:16 → Check: 09:00:16 < 09:15:00? YES → Sleep 1 sec
...
09:14:59 → Check: 09:14:59 < 09:15:00? YES → Sleep 1 sec
09:15:00 → Check: 09:15:00 < 09:15:00? NO → Exit loop
```

---

### Line 76: Market Open Log
**File:** `main.py`
**Line:** 322
```python
logger.info("Market is open! Starting trading...")
```
**Output:**
```
09:15:00 | INFO | Market is open! Starting trading...
```

---

### Line 77: Start Trading
**File:** `main.py`
**Line:** 323
```python
system.start_trading()
```
**Explanation:** Calls method to start live trading.

---

### Line 78-80: Trading Banner
**File:** `main.py`
**Lines:** 270-272
```python
logger.info("=" * 60)
logger.info("STARTING LIVE TRADING")
logger.info("=" * 60)
```
**Output:**
```
09:15:00 | INFO | ============================================================
09:15:00 | INFO | STARTING LIVE TRADING
09:15:00 | INFO | ============================================================
```

---

### Line 81: Get All Tokens
**File:** `main.py`
**Line:** 275
```python
tokens = self.symbol_manager.get_all_tokens()
```
**Explanation:** Gets list of instrument tokens for all symbols.
**Result:** `[738561, 2953217, 408065, ...]`

---

### Line 82: Subscribe to Tokens
**File:** `main.py`
**Line:** 276
```python
self.ws_manager.subscribe(tokens)
```
**Explanation:** Tells WebSocket manager which tokens to subscribe to.

---

### Line 83-84: Store Tokens
**File:** `ws_manager.py`
**Lines:** 97-98
```python
self.subscribed_tokens = tokens
logger.info(f"Added {len(tokens)} tokens for subscription")
```
**Output:**
```
09:15:00 | INFO | Added 5 tokens for subscription
```

---

### Line 85-86: Start WebSocket Log
**File:** `main.py`
**Lines:** 279-280
```python
logger.info("Starting WebSocket connection...")
self.ws_manager.start()
```
**Output:**
```
09:15:00 | INFO | Starting WebSocket connection...
```

---

### Line 87-89: WebSocket Connect (BLOCKING)
**File:** `ws_manager.py`
**Lines:** 106-109
```python
def start(self):
    logger.info("Starting WebSocket connection...")
    try:
        self.ticker.connect(threaded=False)  # ← BLOCKS HERE
```
**Explanation:** Starts WebSocket connection. **threaded=False means this is BLOCKING - main thread stops here.** All further execution happens in callbacks.

---

### Line 90-92: WebSocket Connected Callback
**File:** `ws_manager.py`
**Lines:** 43-45
```python
def on_connect(ws, response):
    logger.info(f"✓ WebSocket connected")
    self.is_connected = True
```
**Output:**
```
09:15:01 | INFO | ✓ WebSocket connected  ← YOU SAW THIS!
```
**Explanation:** This callback is triggered when WebSocket successfully connects to Zerodha.

---

### Line 93: Reset Reconnect Counter
**File:** `ws_manager.py`
**Line:** 46
```python
self.reconnect_attempts = 0
```
**Explanation:** Resets reconnection attempt counter.

---

### Line 94: Check if Tokens Exist
**File:** `ws_manager.py`
**Line:** 49
```python
if self.subscribed_tokens:
```
**Explanation:** Checks if there are tokens to subscribe to.
**Evaluation:** `len(tokens) > 0` → **TRUE** (if symbols loaded correctly)

---

### Line 95: Subscribe to Tokens
**File:** `ws_manager.py`
**Line:** 50
```python
ws.subscribe(self.subscribed_tokens)
```
**Explanation:** Subscribes to all instrument tokens via WebSocket.

---

### Line 96: Set Full Mode
**File:** `ws_manager.py`
**Line:** 51
```python
ws.set_mode(ws.MODE_FULL, self.subscribed_tokens)
```
**Explanation:** Sets mode to FULL to receive complete tick data (price, volume, timestamp, etc.).

---

### Line 97: Subscription Confirmation
**File:** `ws_manager.py`
**Line:** 52
```python
logger.info(f"Subscribed to {len(self.subscribed_tokens)} instruments")
```
**Output:**
```
09:15:01 | INFO | Subscribed to 5 instruments  ← DID YOU SEE THIS?
```
**⚠️ CRITICAL:** If you didn't see this, subscription failed!

---

### Line 98-100: Ticks Arrive (NO LOGGING - SILENT!)
**File:** `ws_manager.py`
**Lines:** 69-71
```python
def on_ticks(ws, ticks):
    """CRITICAL: This is the HOT PATH"""
    if self.on_ticks_callback:
```
**Explanation:** This callback is triggered every time ticks arrive from Zerodha. **NO LOGGING HERE - you can't see when ticks arrive!**

---

### Line 101-104: Call Tick Router
**File:** `ws_manager.py`
**Lines:** 75-78
```python
try:
    self.on_ticks_callback(ticks)  # ← Calls tick_router.route_ticks()
except Exception as e:
    logger.error(f"Error in ticks callback: {e}")
```
**Explanation:** Calls the tick router to distribute ticks to all engines.

---

### Line 105-106: Check if Ticks Exist
**File:** `tick_router.py`
**Lines:** 39-40
```python
if not ticks:
    return
```
**Explanation:** If no ticks in batch, return immediately.

---

### Line 107: Get Current Time
**File:** `tick_router.py`
**Line:** 42
```python
current_time = datetime.now().time()
```
**Explanation:** Gets current system time.

---

### Line 108-109: Market Hours Check (CRITICAL FILTER!)
**File:** `tick_router.py`
**Lines:** 45-46
```python
if not (self.market_open <= current_time <= self.market_close):
    return  # ← SILENTLY IGNORES TICKS!
```
**Explanation:** Checks if time is between 9:15:00 and 15:30:00. **If outside these hours, ticks are SILENTLY IGNORED with NO LOGGING!**
**Evaluation at 09:15:02:**
- `09:15:00 <= 09:15:02 <= 15:30:00` → **TRUE**, continue processing

---

### Line 110-111: Process Each Tick
**File:** `tick_router.py`
**Lines:** 49-50
```python
for tick in ticks:
    self._route_single_tick(tick)
```
**Explanation:** Loops through each tick in the batch and routes it.

---

### Line 112: Route to Candle Builder
**File:** `tick_router.py`
**Line:** 61
```python
self.candle_builder.process_tick(tick)
```
**Explanation:** Sends tick to candle builder to update 1-minute candles.

---

### Line 113-115: Extract Tick Data
**File:** `candles.py`
**Lines:** 73-75
```python
token = tick['instrument_token']  # 738561 (RELIANCE)
price = tick['last_price']  # 2450.50
volume = tick.get('volume_traded', 0)  # 125000
```
**Explanation:** Extracts token, price, and volume from tick.

---

### Line 116-117: Get Timestamp
**File:** `candles.py`
**Lines:** 77-78
```python
timestamp = tick.get('exchange_timestamp') or tick.get('last_trade_time')
current_min = timestamp.replace(second=0, microsecond=0)  # 09:15:00
```
**Explanation:** Gets tick timestamp and rounds down to minute (09:15:02 → 09:15:00).

---

### Line 118-120: Check Minute Change
**File:** `candles.py`
**Lines:** 83-84
```python
if self.current_minute and current_min > self.current_minute:
    self._close_all_candles(self.current_minute)  # ← CANDLE CLOSE!
```
**Explanation:** Checks if minute has changed. **This is how candles close!**
**First tick at 09:15:02:**
- `self.current_minute = None`
- Condition is FALSE, no candle close yet

**First tick at 09:16:00:**
- `self.current_minute = 09:15:00`
- `current_min = 09:16:00`
- `09:16:00 > 09:15:00` → **TRUE**
- **Closes all 9:15 candles!**

---

### Line 121: Set Current Minute
**File:** `candles.py`
**Line:** 86
```python
self.current_minute = current_min
```
**Explanation:** Updates current minute tracker.

---

### Line 122-123: Check if New Candle
**File:** `candles.py`
**Lines:** 89-90
```python
if token not in self.active_candles:
    # NEW CANDLE
```
**Explanation:** Checks if this is the first tick for this symbol in this minute.

---

### Line 124-134: Create New Candle
**File:** `candles.py`
**Lines:** 91-102
```python
prev_vol = self.previous_volume.get(token, 0)  # 0 for first candle
candle_volume = volume - prev_vol  # 125000 - 0 = 125000

self.active_candles[token] = {
    'open': price,      # 2450.50
    'high': price,      # 2450.50
    'low': price,       # 2450.50
    'close': price,     # 2450.50
    'volume': candle_volume,  # 125000
    'cumulative_volume': volume,  # 125000
    'first_tick_time': timestamp
}
```
**Explanation:** Creates new candle with OHLCV data. **NO LOGGING - silent execution.**

---

### Line 135-140: Update Existing Candle (Subsequent Ticks)
**File:** `candles.py`
**Lines:** 104-110
```python
else:
    # UPDATE EXISTING CANDLE
    candle = self.active_candles[token]
    candle['high'] = max(candle['high'], price)
    candle['low'] = min(candle['low'], price)
    candle['close'] = price
    candle['cumulative_volume'] = volume
```
**Explanation:** Updates candle with new tick data. High/low are updated if price is higher/lower.

---

### Line 141: Route to Breakout Engine
**File:** `tick_router.py`
**Line:** 64
```python
self.breakout_engine.process_tick(tick)
```
**Explanation:** Sends tick to breakout engine.

---

### Line 142-144: Get Symbol
**File:** `breakout.py`
**Lines:** 51-52
```python
token = tick['instrument_token']
price = tick['last_price']
```

---

### Line 145-147: Get Symbol Name
**File:** `breakout.py`
**Lines:** 55-57
```python
symbol = self.symbol_manager.get_symbol(token)
if not symbol:
    return
```
**Explanation:** Converts token to symbol name (738561 → "RELIANCE").

---

### Line 148-149: Check if Marked (CRITICAL!)
**File:** `breakout.py`
**Lines:** 60-61
```python
if not self.marker.is_marked(symbol):
    return  # ← EXITS HERE before 9:16!
```
**Explanation:** Only monitors marked symbols. **Before 9:16, no symbols are marked yet, so this returns immediately!**

---

### Line 150: Route to Risk Manager
**File:** `tick_router.py`
**Line:** 67
```python
self.risk_manager.process_tick(tick)
```
**Explanation:** Sends tick to risk manager for stop-loss monitoring.

---

### Line 151: Increment Tick Counter
**File:** `tick_router.py`
**Line:** 52
```python
self.ticks_processed += len(ticks)
```
**Explanation:** Tracks total ticks processed.

---

## ⏰ AT 9:16:00 - FIRST TICK OF NEW MINUTE ARRIVES

### Line 152-154: Minute Changed - Close Candles!
**File:** `candles.py`
**Lines:** 83-84
```python
if self.current_minute and current_min > self.current_minute:
    self._close_all_candles(self.current_minute)
```
**Explanation:** First tick of 9:16 triggers candle close for 9:15.
**Evaluation:**
- `self.current_minute = 09:15:00`
- `current_min = 09:16:00`
- **Condition TRUE → Close all 9:15 candles!**

---

### Line 155-157: Loop Through Active Candles
**File:** `candles.py`
**Lines:** 117-120
```python
for token, candle_data in list(self.active_candles.items()):
    symbol = self.symbol_manager.get_symbol(token)
    if not symbol:
        continue
```
**Explanation:** Loops through all active candles to close them.

---

### Line 158-166: Create Completed Candle
**File:** `candles.py`
**Lines:** 123-131
```python
completed = Candle(
    symbol=symbol,              # "RELIANCE"
    timestamp=minute,           # 09:15:00
    open=candle_data['open'],   # 2450.50
    high=candle_data['high'],   # 2453.00
    low=candle_data['low'],     # 2449.50
    close=candle_data['close'], # 2452.80
    volume=candle_data['volume']  # 450000
)
```
**Explanation:** Creates immutable Candle object with final OHLCV values.

---

### Line 167-168: Store Completed Candle
**File:** `candles.py`
**Lines:** 134-135
```python
self.completed_candles[token] = completed
self.previous_volume[token] = candle_data['cumulative_volume']
```
**Explanation:** Stores completed candle in buffer for later retrieval.

---

### Line 169-173: Trigger Candle Close Callback (CRITICAL!)
**File:** `candles.py`
**Lines:** 138-142
```python
if self.on_candle_close:
    try:
        self.on_candle_close(completed)  # ← Calls marker.evaluate_and_mark()
    except Exception as e:
        logger.error(f"Error in candle close callback for {symbol}: {e}")
```
**Explanation:** **This is the KEY moment!** Triggers callback that evaluates if stock should be marked.

---

### Line 174: Clear Active Candles
**File:** `candles.py`
**Line:** 145
```python
self.active_candles.clear()
```
**Explanation:** Clears active candles to prepare for next minute.

---

### Line 175: Candle Close Log
**File:** `candles.py`
**Line:** 146
```python
logger.debug(f"Closed {len(self.completed_candles)} candles for minute {minute.strftime('%H:%M')}")
```
**Output (DEBUG level only):**
```
09:16:00 | DEBUG | Closed 5 candles for minute 09:15
```

---

## 🔍 STOCK EVALUATION & MARKING

### Line 176: Increment Evaluated Counter
**File:** `marker.py`
**Line:** 51
```python
self.total_evaluated += 1
```

---

### Line 177-178: Get Candle Time
**File:** `marker.py`
**Lines:** 54-55
```python
candle_time = candle.timestamp.time()  # 09:15:00
if not (time(9, 15) <= candle_time < time(9, 16)):
```
**Explanation:** Checks if this is a 9:15 candle.
**Evaluation:** `09:15:00 <= 09:15:00 < 09:16:00` → **TRUE**, continue.

---

### Line 179: Get Symbol
**File:** `marker.py`
**Line:** 58
```python
symbol = candle.symbol  # "RELIANCE"
```

---

### Line 180: Get Average Volume
**File:** `marker.py`
**Line:** 61
```python
avg_volume = self.historical_manager.get_avg_volume(symbol)
```
**Explanation:** Gets 14-day average volume from historical data.
**Example:** `200000` (average daily volume)

---

### Line 181-183: Check if Historical Data Exists
**File:** `marker.py`
**Lines:** 62-64
```python
if avg_volume == 0:
    logger.debug(f"{symbol}: No historical data available")
    return False
```

---

### Line 184: Calculate Volume Ratio
**File:** `marker.py`
**Line:** 67
```python
volume_ratio = candle.volume / avg_volume  # 450000 / 200000 = 2.25
```

---

### Line 185-187: Volume Check (CRITICAL FILTER!)
**File:** `marker.py`
**Lines:** 68-70
```python
if volume_ratio < self.config['VOLUME_MULTIPLIER']:  # 2.25 < 2.0?
    logger.debug(f"{symbol}: Volume {volume_ratio:.2f}x (need {self.config['VOLUME_MULTIPLIER']}x)")
    return False
```
**Explanation:** Checks if volume is at least 2x average.
**Scenario 1 - RELIANCE (High Volume):**
- `volume_ratio = 2.25`
- `2.25 < 2.0` → **FALSE**, continue to marking

**Scenario 2 - TCS (Low Volume):**
- `volume_ratio = 1.8`
- `1.8 < 2.0` → **TRUE**, return False
**Output:**
```
09:16:00 | DEBUG | TCS: Volume 1.80x (need 2.0x)
```

---

### Line 188-191: Mark Symbol
**File:** `marker.py`
**Lines:** 73-76
```python
with self.lock:
    self.marked_symbols.add(symbol)  # Add to set
    self.first_candles[symbol] = candle  # Store 9:15 candle
    self.total_marked += 1
```
**Explanation:** Adds symbol to marked set and stores its 9:15 candle.

---

### Line 192: Marked Log
**File:** `marker.py`
**Line:** 78
```python
logger.info(f"✓ MARKED: {symbol} | Vol: {volume_ratio:.2f}x | High: {candle.high:.2f}")
```
**Output:**
```
09:16:00 | INFO | ✓ MARKED: RELIANCE | Vol: 2.25x | High: 2453.00
09:16:00 | INFO | ✓ MARKED: INFY | Vol: 2.10x | High: 1450.50
```

---

## 🚀 BREAKOUT MONITORING (After Marking)

### Line 193-195: Breakout Engine - Check if Marked
**File:** `breakout.py`
**Lines:** 60-61
```python
if not self.marker.is_marked(symbol):
    return  # ← NOW PASSES for RELIANCE & INFY!
```
**Explanation:** Now that RELIANCE is marked, this check passes.

---

### Line 196-198: Check if Already Triggered
**File:** `breakout.py`
**Lines:** 64-65
```python
if symbol in self.breakout_triggered:
    return
```
**Explanation:** Prevents duplicate entries for same symbol.

---

### Line 199-201: Update Last Price
**File:** `breakout.py`
**Lines:** 68-69
```python
with self.lock:
    self.last_prices[token] = price
```

---

### Line 202: Get Breakout Level
**File:** `breakout.py`
**Line:** 72
```python
breakout_level = self.marker.get_breakout_level(symbol)
```

---

### Line 203-207: Calculate Breakout Level
**File:** `marker.py`
**Lines:** 99-104
```python
candle = self.first_candles.get(symbol)
if not candle:
    return 0

buffer = candle.high * (self.config['BREAKOUT_BUFFER_PERCENT'] / 100)
return candle.high + buffer
```
**Explanation:** Calculates breakout level as 9:15 high + 0.05% buffer.
**Example:**
- 9:15 high = 2453.00
- Buffer = 2453.00 × 0.05% = 1.23
- Breakout level = 2454.23

---

### Line 208-209: Check if Breakout
**File:** `breakout.py`
**Lines:** 75-76
```python
if price >= breakout_level:  # 2453.80 >= 2454.23?
    self._trigger_breakout(symbol, price)
```
**Explanation:** Checks if current price crossed breakout level.
**At 09:16:05:** Price = 2453.80, Breakout = 2454.23 → **FALSE**, no breakout yet

---

## 🎯 AT 9:16:08 - BREAKOUT TRIGGERED!

### Line 210-211: Breakout Detected!
**File:** `breakout.py`
**Lines:** 75-76
```python
if price >= breakout_level:  # 2454.50 >= 2454.23? TRUE!
    self._trigger_breakout(symbol, price)
```
**Explanation:** Price crossed breakout level!

---

### Line 212-213: Mark as Triggered
**File:** `breakout.py`
**Lines:** 84-85
```python
self.breakout_triggered[symbol] = True
self.breakouts_detected += 1
```

---

### Line 214: Get Stop-Loss
**File:** `breakout.py`
**Line:** 88
```python
stoploss = self.candle_builder.get_current_candle_open(symbol)
```
**Explanation:** Gets open price of current (9:16) candle for stop-loss.
**Result:** `2453.50`

---

### Line 215-218: Fallback Stop-Loss
**File:** `breakout.py`
**Lines:** 91-93
```python
if stoploss is None or stoploss == 0:
    stoploss = self.marker.get_stoploss_level(symbol)
    logger.warning(f"{symbol}: Using 9:15 candle open as SL")
```
**Explanation:** If current candle open not available, uses 9:15 candle open.

---

### Line 219: Get First Candle
**File:** `breakout.py`
**Line:** 96
```python
first_candle = self.marker.get_first_candle(symbol)
```

---

### Line 220-224: Breakout Log
**File:** `breakout.py`
**Lines:** 98-102
```python
logger.info(
    f"🚀 BREAKOUT: {symbol} @ {entry_price:.2f} | "
    f"SL: {stoploss:.2f} (Breakout Candle Open) | "
    f"9:15 High: {first_candle.high:.2f}"
)
```
**Output:**
```
09:16:08 | INFO | 🚀 BREAKOUT: RELIANCE @ 2454.50 | SL: 2453.50 | 9:15 High: 2453.00
```

---

### Line 225-229: Trigger Entry Callback
**File:** `breakout.py`
**Lines:** 105-109
```python
if self.on_breakout:
    try:
        self.on_breakout(symbol, entry_price, stoploss)
    except Exception as e:
        logger.error(f"Error in breakout callback for {symbol}: {e}")
```
**Explanation:** Calls entry execution callback.

---

### Line 230: Unmark Symbol
**File:** `breakout.py`
**Line:** 112
```python
self.marker.unmark_symbol(symbol)
```
**Explanation:** Removes from marked list (no longer need to monitor for breakout).

---

## 💰 ENTRY EXECUTION

### Line 231-233: Check Max Trades
**File:** `main.py`
**Lines:** 190-192
```python
if not self.portfolio.can_take_trade(MAX_TRADES_PER_DAY):
    logger.warning(f"Max trades reached ({MAX_TRADES_PER_DAY}) - skipping {symbol}")
    return
```
**Evaluation:** Current trades = 0, Max = 5 → **PASS**

---

### Line 234-236: Check Max Loss
**File:** `main.py`
**Lines:** 195-197
```python
if self.risk_manager.check_max_loss():
    logger.critical("Max daily loss reached - stopping trading")
    return
```
**Evaluation:** Daily loss = 0 → **PASS**

---

### Line 237: Calculate Position Size
**File:** `main.py`
**Line:** 200
```python
quantity = self.risk_manager.calculate_position_size(symbol, entry_price, stoploss)
```
**Explanation:** Calculates how many shares to buy based on risk.
**Calculation:**
- Risk per trade = ₹100,000 × 2% = ₹2,000
- Risk per share = 2454.50 - 2453.50 = ₹1.00
- Quantity = 2000 / 1.00 = **2000 shares**

---

### Line 238-240: Check Quantity
**File:** `main.py`
**Lines:** 202-204
```python
if quantity == 0:
    logger.warning(f"{symbol}: Position size = 0, skipping entry")
    return
```
**Evaluation:** Quantity = 2000 → **PASS**

---

### Line 241: Place Buy Order
**File:** `main.py`
**Line:** 207
```python
order_id = self.order_executor.place_buy_order(symbol, quantity, entry_price)
```

---

### Line 242-254: Dry-Run Order Execution
**File:** `orders_dryrun.py`
```python
def place_buy_order(self, symbol: str, quantity: int, price: float) -> str:
    order_id = f"DRY_{symbol}_{int(time.time())}"
    
    # Simulate slippage
    slippage = price * (self.config['SLIPPAGE_PERCENT'] / 100)
    execution_price = price + slippage  # 2454.50 + 2.45 = 2456.95
    
    self.orders[order_id] = {
        'symbol': symbol,
        'quantity': quantity,
        'price': execution_price,
        'status': 'COMPLETE'
    }
    
    logger.info(f"[DRY-RUN] BUY {symbol} x{quantity} @ {execution_price:.2f}")
    return order_id
```
**Output:**
```
09:16:08 | INFO | [DRY-RUN] BUY RELIANCE x2000 @ 2456.95
```

---

### Line 255-257: Check Order Success
**File:** `main.py`
**Lines:** 209-211
```python
if not order_id:
    logger.error(f"{symbol}: Entry order failed")
    return
```

---

### Line 258: Get Execution Price
**File:** `main.py`
**Line:** 214
```python
actual_price = self.order_executor.get_average_price(order_id) or entry_price
```
**Result:** `2456.95`

---

### Line 259: Add to Portfolio
**File:** `main.py`
**Line:** 217
```python
self.portfolio.add_position(symbol, actual_price, stoploss, quantity)
```

---

### Line 260: Log Trade
**File:** `main.py`
**Line:** 220
```python
self.trade_logger.log_entry(symbol, quantity, actual_price, order_id)
```
**Explanation:** Writes trade to CSV file.

---

### Line 261: Entry Success Log
**File:** `main.py`
**Line:** 222
```python
logger.info(f"✅ ENTRY: {symbol} x{quantity} @ {actual_price:.2f} | SL: {stoploss:.2f}")
```
**Output:**
```
09:16:08 | INFO | ✅ ENTRY: RELIANCE x2000 @ 2456.95 | SL: 2453.50
```

---

## 📊 CONTINUOUS MONITORING (9:16:09 - 15:30:00)

### Line 262+: Risk Manager Monitors Stop-Loss
**File:** `risk.py`
```python
def process_tick(self, tick: dict):
    symbol = self.symbol_manager.get_symbol(tick['instrument_token'])
    price = tick['last_price']
    
    position = self.portfolio.get_position(symbol)
    if not position:
        return
    
    position.current_price = price
    
    if price <= position.stoploss:
        self._trigger_exit(symbol, price, "STOP_LOSS")
```
**Explanation:** Every tick updates position price and checks if stop-loss hit.

---

## 🛑 STOP-LOSS HIT (Example)

**If price drops to 2453.40:**

### Exit Execution
**File:** `main.py` - `_execute_exit()`
```python
order_id = self.order_executor.place_sell_order(symbol, position.quantity, exit_price)
actual_price = self.order_executor.get_average_price(order_id) or exit_price
closed_position = self.portfolio.close_position(symbol, actual_price, reason)
self.trade_logger.log_exit(...)
```

**Output:**
```
09:16:15 | INFO | ⚠️ STOP-LOSS HIT: RELIANCE @ 2453.40
09:16:15 | INFO | [DRY-RUN] SELL RELIANCE x2000 @ 2453.40
09:16:15 | INFO | ✅ EXIT: RELIANCE @ 2453.40 | Reason: STOP_LOSS | PNL: -7100.00
```

---

## 🏁 END OF EXECUTION TRACE

**Total Lines Traced:** 261+ lines across 10+ files

**Key Takeaway:** After "WebSocket connected", everything happens in **callbacks** triggered by:
1. **Ticks arriving** → Candle building & breakout monitoring
2. **Minute changing** → Candle close → Stock marking
3. **Price crossing breakout** → Entry execution
4. **Price hitting stop-loss** → Exit execution

**Why you only saw "WebSocket connected":**
- Most likely: No ticks arriving (market closed, no symbols, or invalid token)
- Check if you saw: "Subscribed to X instruments" log
