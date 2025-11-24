# Complete Line-by-Line Execution Trace
## Scenario: Running `python main.py` at 9:00 AM

---

## 🕘 9:00:00 AM - SYSTEM STARTUP

### Entry Point: `main.py` Line 325-327
```python
if __name__ == "__main__":
    try:
        main()  # ← EXECUTION STARTS HERE
```

**What happens:** Python interpreter starts executing the `main()` function.

---

## 🕘 9:00:00.100 AM - main() Function Begins

### `main.py` Line 306
```python
system = TradingSystem()  # ← Initialize entire system
```

**What happens:** Creates a new `TradingSystem` object, which triggers `__init__()`.

---

## 🕘 9:00:00.150 AM - TradingSystem.__init__() Begins

### `main.py` Lines 52-54
```python
logger.info("=" * 60)
logger.info("9:15 BREAKOUT TRADING SYSTEM - INITIALIZING")
logger.info("=" * 60)
```

**Console Output:**
```
09:00:00 | INFO | ============================================================
09:00:00 | INFO | 9:15 BREAKOUT TRADING SYSTEM - INITIALIZING
09:00:00 | INFO | ============================================================
```

---

### `main.py` Line 57
```python
load_dotenv('config/secrets.env')
```

**What happens:** 
- Loads environment variables from `config/secrets.env`
- Sets `API_KEY` and `ACCESS_TOKEN` in environment

---

### `main.py` Line 60
```python
self.kite = self._initialize_kite()
```

**What happens:** Calls `_initialize_kite()` method.

---

## 🕘 9:00:00.200 AM - Kite Connection

### `main.py` Lines 92-93
```python
api_key = os.getenv('API_KEY')
access_token = os.getenv('ACCESS_TOKEN')
```

**What happens:** Retrieves credentials from environment.

---

### `main.py` Lines 95-97
```python
if not api_key or not access_token:
    logger.error("API_KEY or ACCESS_TOKEN not found in secrets.env")
    sys.exit(1)
```

**What happens:** 
- **IF** credentials missing → System exits with error
- **ELSE** → Continues

---

### `main.py` Lines 99-100
```python
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)
```

**What happens:** Creates Kite connection object with credentials.

---

### `main.py` Lines 103-106
```python
try:
    profile = kite.profile()
    logger.info(f"✓ Connected to Zerodha | User: {profile['user_name']}")
    return kite
```

**Console Output:**
```
09:00:00 | INFO | ✓ Connected to Zerodha | User: KARTHIK
```

**What happens:** 
- Makes API call to Zerodha to verify connection
- **IF** successful → Returns kite object
- **IF** fails → Goes to exception handler (lines 107-109) and exits

---

## 🕘 9:00:00.500 AM - Module Initialization

### `main.py` Line 81
```python
self._initialize_modules()
```

**What happens:** Calls `_initialize_modules()` to set up all trading components.

---

### `main.py` Lines 115-118 - Symbol Manager
```python
logger.info("Loading symbols...")
self.symbol_manager = SymbolManager(self.kite)
self.symbol_manager.load_symbols_from_csv(SYMBOLS_CSV_PATH)
self.symbol_manager.map_tokens(EXCHANGE)
```

**Console Output:**
```
09:00:00 | INFO | Loading symbols...
```

**What happens:**
1. Creates `SymbolManager` object
2. Reads `data/symbols.csv` file
3. Maps each symbol (e.g., "RELIANCE") to its instrument token (e.g., 738561)

**Example symbols.csv:**
```
RELIANCE
TCS
INFY
HDFCBANK
ICICIBANK
```

**After this:** `symbol_manager.symbols` contains:
```python
{
    'RELIANCE': 738561,
    'TCS': 2953217,
    'INFY': 408065,
    # ... etc
}
```

---

### `main.py` Lines 121-122 - Historical Data Manager
```python
logger.info("Initializing historical data manager...")
self.historical_manager = HistoricalDataManager(self.kite, self.symbol_manager)
```

**Console Output:**
```
09:00:00 | INFO | Initializing historical data manager...
```

**What happens:** Creates manager to fetch 14-day historical data later.

---

### `main.py` Lines 125-148 - Other Modules
```python
self.candle_builder = CandleBuilder(self.symbol_manager)
self.portfolio = Portfolio(TOTAL_CAPITAL)
self.marker = StockMarker(self.historical_manager, self.config)
self.breakout_engine = BreakoutEngine(...)
self.risk_manager = RiskManager(...)
self.order_executor = DryRunOrderExecutor(...) or LiveOrderExecutor(...)
self.trade_logger = TradeLogger(self.config)
self.tick_router = TickRouter(...)
self.ws_manager = WebSocketManager(api_key, access_token, self.config)
```

**Console Output:**
```
09:00:00 | INFO | ✓ Dry-run order executor initialized
09:00:00 | INFO | ✓ All modules initialized
```

**What happens:** All trading components are created and ready.

---

### `main.py` Lines 86-88 - Configuration Summary
```python
logger.info(f"Mode: {'DRY-RUN' if DRY_RUN_MODE else 'LIVE TRADING'}")
logger.info(f"Capital: ₹{TOTAL_CAPITAL:,.2f}")
logger.info(f"Max Trades: {MAX_TRADES_PER_DAY}")
```

**Console Output:**
```
09:00:00 | INFO | Mode: DRY-RUN
09:00:00 | INFO | Capital: ₹100,000.00
09:00:00 | INFO | Max Trades: 5
```

---

## 🕘 9:00:01 AM - Callback Setup

### `main.py` Line 84
```python
self._setup_callbacks()
```

**What happens:** Wires up event handlers between modules.

---

### `main.py` Lines 164-167 - Candle Close Callback
```python
def on_candle_close(candle):
    self.marker.evaluate_and_mark(candle)

self.candle_builder.set_on_candle_close_callback(on_candle_close)
```

**What happens:** 
- When a candle closes → `marker.evaluate_and_mark()` will be called
- This is how stocks get marked at 9:16 when 9:15 candle closes

---

### `main.py` Lines 170-173 - Breakout Callback
```python
def on_breakout(symbol, entry_price, stoploss):
    self._execute_entry(symbol, entry_price, stoploss)

self.breakout_engine.set_on_breakout_callback(on_breakout)
```

**What happens:**
- When breakout detected → `_execute_entry()` will be called
- This is how trades get placed

---

### `main.py` Lines 176-179 - Exit Callback
```python
def on_exit(symbol, exit_price, reason):
    self._execute_exit(symbol, exit_price, reason)

self.risk_manager.set_on_exit_callback(on_exit)
```

**What happens:**
- When stop-loss hit → `_execute_exit()` will be called

---

### `main.py` Line 182 - WebSocket Callback
```python
self.ws_manager.set_on_ticks_callback(self.tick_router.route_ticks)
```

**What happens:**
- When ticks arrive from WebSocket → `tick_router.route_ticks()` will be called
- **THIS IS THE CRITICAL PATH FOR LIVE DATA**

---

### `main.py` Line 184
```python
logger.info("✓ Callbacks configured")
```

**Console Output:**
```
09:00:01 | INFO | ✓ Callbacks configured
```

---

## 🕘 9:00:01 AM - Back to main() Function

### `main.py` Line 309
```python
current_time = datetime.now().time()
```

**What happens:** Gets current time = `09:00:01`

---

### `main.py` Line 311
```python
if current_time < MARKET_OPEN_TIME or current_time > MARKET_CLOSE_TIME:
```

**Evaluation:**
- `current_time` = `09:00:01`
- `MARKET_OPEN_TIME` = `09:15:00` (from `config/settings.py` line 22)
- `MARKET_CLOSE_TIME` = `15:30:00`
- **Condition:** `09:00:01 < 09:15:00` → **TRUE**

**What happens:** Enters the if block (lines 312-319)

---

## 🕘 9:00:01 AM - Pre-Market Phase

### `main.py` Lines 312-313
```python
logger.info(f"Current time: {current_time.strftime('%H:%M:%S')} (outside market hours)")
logger.info("Fetching historical data...")
```

**Console Output:**
```
09:00:01 | INFO | Current time: 09:00:01 (outside market hours)
09:00:01 | INFO | Fetching historical data...
```

---

### `main.py` Line 314
```python
system.fetch_historical_data()
```

**What happens:** Calls `fetch_historical_data()` method.

---

## 🕘 9:00:01 AM - Historical Data Fetch

### `main.py` Lines 260-264
```python
logger.info("=" * 60)
logger.info("FETCHING HISTORICAL DATA")
logger.info("=" * 60)

self.historical_manager.fetch_all_historical_data(days=HISTORICAL_DAYS)
```

**Console Output:**
```
09:00:01 | INFO | ============================================================
09:00:01 | INFO | FETCHING HISTORICAL DATA
09:00:01 | INFO | ============================================================
```

**What happens:** Fetches 14 days of historical data for all symbols.

---

### Inside `historical.py` - For Each Symbol

**For RELIANCE:**
```
09:00:02 | INFO | Fetching historical data for RELIANCE...
09:00:03 | INFO | ✓ RELIANCE: 14 days of data fetched
```

**For TCS:**
```
09:00:04 | INFO | Fetching historical data for TCS...
09:00:05 | INFO | ✓ TCS: 14 days of data fetched
```

**... and so on for all symbols**

**What's stored:**
- 14 days of daily candles for each symbol
- Used to calculate average volume: `sum(14 days volume) / 14`

---

### `main.py` Line 266
```python
logger.info("✓ Historical data ready")
```

**Console Output:**
```
09:00:15 | INFO | ✓ Historical data ready
```

**Time taken:** ~14 seconds (assuming 5 symbols, ~3 sec each due to API rate limits)

---

## 🕘 9:00:15 AM - Waiting for Market Open

### `main.py` Lines 317-319
```python
logger.info("Waiting for market to open at 9:15 AM...")
while datetime.now().time() < MARKET_OPEN_TIME or datetime.now().time() > MARKET_CLOSE_TIME:
    time_module.sleep(1)
```

**Console Output:**
```
09:00:15 | INFO | Waiting for market to open at 9:15 AM...
```

**What happens:**
- System enters a **LOOP**
- Every second, checks if time >= 9:15:00
- **Sleeps for 1 second** between checks

**Loop iterations:**
```
09:00:15 → Check: 09:00:15 < 09:15:00? YES → Sleep 1 sec
09:00:16 → Check: 09:00:16 < 09:15:00? YES → Sleep 1 sec
09:00:17 → Check: 09:00:17 < 09:15:00? YES → Sleep 1 sec
...
09:14:58 → Check: 09:14:58 < 09:15:00? YES → Sleep 1 sec
09:14:59 → Check: 09:14:59 < 09:15:00? YES → Sleep 1 sec
09:15:00 → Check: 09:15:00 < 09:15:00? NO → Exit loop
```

**⏰ System is IDLE for 14 minutes and 45 seconds**

---

## 🕘 9:15:00 AM - Market Opens!

### `main.py` Line 322
```python
logger.info("Market is open! Starting trading...")
```

**Console Output:**
```
09:15:00 | INFO | Market is open! Starting trading...
```

---

### `main.py` Line 323
```python
system.start_trading()
```

**What happens:** Calls `start_trading()` method.

---

## 🕘 9:15:00 AM - Starting Live Trading

### `main.py` Lines 270-272
```python
logger.info("=" * 60)
logger.info("STARTING LIVE TRADING")
logger.info("=" * 60)
```

**Console Output:**
```
09:15:00 | INFO | ============================================================
09:15:00 | INFO | STARTING LIVE TRADING
09:15:00 | INFO | ============================================================
```

---

### `main.py` Line 275
```python
tokens = self.symbol_manager.get_all_tokens()
```

**What happens:** Gets list of all instrument tokens.

**Example:**
```python
tokens = [738561, 2953217, 408065, 341249, 1270529]  # RELIANCE, TCS, INFY, etc.
```

---

### `main.py` Line 276
```python
self.ws_manager.subscribe(tokens)
```

**What happens:** Tells WebSocket manager which tokens to subscribe to.

---

### Inside `ws_manager.py` Lines 97-98
```python
self.subscribed_tokens = tokens
logger.info(f"Added {len(tokens)} tokens for subscription")
```

**Console Output:**
```
09:15:00 | INFO | Added 5 tokens for subscription
```

**What happens:** Stores tokens for later subscription when WebSocket connects.

---

### `main.py` Lines 279-280
```python
logger.info("Starting WebSocket connection...")
self.ws_manager.start()
```

**Console Output:**
```
09:15:00 | INFO | Starting WebSocket connection...
```

---

### Inside `ws_manager.py` Lines 106-109
```python
def start(self):
    logger.info("Starting WebSocket connection...")
    try:
        self.ticker.connect(threaded=False)  # ← BLOCKING CALL
```

**What happens:**
- Calls KiteTicker's `connect()` method
- **threaded=False** means this is a **BLOCKING** call
- **Main thread is now STUCK HERE** until WebSocket closes
- All further execution happens in **callbacks**

---

## 🕘 9:15:01 AM - WebSocket Connects

### Inside `ws_manager.py` Line 43-52 (on_connect callback)
```python
def on_connect(ws, response):
    logger.info(f"✓ WebSocket connected")
    self.is_connected = True
    self.reconnect_attempts = 0
    
    # Subscribe to tokens
    if self.subscribed_tokens:
        ws.subscribe(self.subscribed_tokens)
        ws.set_mode(ws.MODE_FULL, self.subscribed_tokens)
        logger.info(f"Subscribed to {len(self.subscribed_tokens)} instruments")
```

**Console Output:**
```
09:15:01 | INFO | ✓ WebSocket connected  ← YOU SAW THIS!
09:15:01 | INFO | Subscribed to 5 instruments  ← DID YOU SEE THIS?
```

**What happens:**
- WebSocket connection established with Zerodha
- Subscribes to all 5 tokens (RELIANCE, TCS, INFY, etc.)
- Sets mode to FULL (gets complete tick data including volume, timestamps, etc.)

**⚠️ CRITICAL QUESTION:** Did you see "Subscribed to 5 instruments"?
- **If NO:** Subscription failed - likely `subscribed_tokens` was empty
- **If YES:** Subscription successful, waiting for ticks...

---

## 🕘 9:15:02 AM - First Ticks Arrive

### Inside `ws_manager.py` Lines 69-78 (on_ticks callback)
```python
def on_ticks(ws, ticks):
    """
    CRITICAL: This is the HOT PATH
    Route ticks immediately with zero delay
    """
    if self.on_ticks_callback:
        try:
            self.on_ticks_callback(ticks)  # ← Calls tick_router.route_ticks()
        except Exception as e:
            logger.error(f"Error in ticks callback: {e}")
```

**What happens:**
- Zerodha sends batch of ticks (usually 1-50 ticks per batch)
- **NO LOGGING HERE** - Silent execution
- Calls `tick_router.route_ticks(ticks)`

**Example tick data:**
```python
ticks = [
    {
        'instrument_token': 738561,  # RELIANCE
        'last_price': 2450.50,
        'volume_traded': 125000,  # Cumulative since 9:15
        'exchange_timestamp': datetime(2025, 11, 24, 9, 15, 2),
        'last_trade_time': datetime(2025, 11, 24, 9, 15, 2),
        ...
    },
    {
        'instrument_token': 2953217,  # TCS
        'last_price': 3650.20,
        'volume_traded': 85000,
        'exchange_timestamp': datetime(2025, 11, 24, 9, 15, 2),
        ...
    },
    # ... more ticks
]
```

---

## 🕘 9:15:02 AM - Tick Routing

### Inside `tick_router.py` Lines 32-46
```python
def route_ticks(self, ticks: List[dict]):
    if not ticks:
        return
    
    current_time = datetime.now().time()
    
    # Only process during market hours
    if not (self.market_open <= current_time <= self.market_close):
        return  # ← SILENTLY IGNORES TICKS
    
    # Process each tick
    for tick in ticks:
        self._route_single_tick(tick)
    
    self.ticks_processed += len(ticks)
```

**What happens:**
- **Check 1:** Are there ticks? YES → Continue
- **Check 2:** Is time between 9:15:00 and 15:30:00?
  - `current_time` = `09:15:02`
  - `self.market_open` = `09:15:00`
  - `self.market_close` = `15:30:00`
  - **Condition:** `09:15:00 <= 09:15:02 <= 15:30:00` → **TRUE**
  - **Result:** Continue processing

**⚠️ IF TIME WAS 09:14:59:**
- Condition would be FALSE
- Ticks would be **SILENTLY IGNORED**
- **NO LOGGING** to tell you this happened

---

### Inside `tick_router.py` Lines 54-71 (For each tick)
```python
def _route_single_tick(self, tick: dict):
    try:
        # 1. Candle Builder (always update candles)
        self.candle_builder.process_tick(tick)
        
        # 2. Breakout Engine (only for marked symbols)
        self.breakout_engine.process_tick(tick)
        
        # 3. Risk Manager (only for active positions)
        self.risk_manager.process_tick(tick)
        
    except Exception as e:
        logger.error(f"Error routing tick: {e}", exc_info=True)
```

**What happens:** Each tick is sent to 3 engines simultaneously.

---

## 🕘 9:15:02 AM - Candle Building (First Tick)

### Inside `candles.py` Lines 73-79
```python
token = tick['instrument_token']  # 738561 (RELIANCE)
price = tick['last_price']  # 2450.50
volume = tick.get('volume_traded', 0)  # 125000
timestamp = tick.get('exchange_timestamp') or tick.get('last_trade_time')  # 09:15:02
current_min = timestamp.replace(second=0, microsecond=0)  # 09:15:00
```

**What happens:** Extracts data from tick.

---

### Inside `candles.py` Lines 81-86
```python
with self.lock:
    # Check if minute has changed (candle close)
    if self.current_minute and current_min > self.current_minute:
        self._close_all_candles(self.current_minute)
    
    self.current_minute = current_min  # Set to 09:15:00
```

**What happens:**
- **First tick:** `self.current_minute` is `None`
- **Condition:** `None and ...` → **FALSE**
- **No candle close yet**
- Sets `self.current_minute = 09:15:00`

---

### Inside `candles.py` Lines 89-102 (Create new candle)
```python
if token not in self.active_candles:
    # NEW CANDLE
    prev_vol = self.previous_volume.get(token, 0)  # 0 (first candle)
    candle_volume = volume - prev_vol  # 125000 - 0 = 125000
    
    self.active_candles[token] = {
        'open': price,      # 2450.50
        'high': price,      # 2450.50
        'low': price,       # 2450.50
        'close': price,     # 2450.50
        'volume': candle_volume,  # 125000
        'cumulative_volume': volume,  # 125000
        'first_tick_time': timestamp  # 09:15:02
    }
```

**What happens:**
- Creates first candle for RELIANCE
- **NO LOGGING** - Silent execution

**State after first tick:**
```python
self.active_candles = {
    738561: {  # RELIANCE
        'open': 2450.50,
        'high': 2450.50,
        'low': 2450.50,
        'close': 2450.50,
        'volume': 125000
    }
}
```

---

## 🕘 9:15:03-9:15:59 AM - Continuous Tick Processing

**What happens:**
- Ticks arrive every few milliseconds
- Each tick updates the active candle:

### Inside `candles.py` Lines 104-110 (Update existing candle)
```python
else:
    # UPDATE EXISTING CANDLE
    candle = self.active_candles[token]
    candle['high'] = max(candle['high'], price)  # Update if higher
    candle['low'] = min(candle['low'], price)    # Update if lower
    candle['close'] = price                       # Always update close
    candle['cumulative_volume'] = volume
```

**Example progression:**
```
09:15:02 → RELIANCE: O=2450.50, H=2450.50, L=2450.50, C=2450.50, V=125000
09:15:05 → RELIANCE: O=2450.50, H=2451.20, L=2450.30, C=2450.80, V=145000
09:15:10 → RELIANCE: O=2450.50, H=2452.00, L=2450.00, C=2451.50, V=180000
...
09:15:59 → RELIANCE: O=2450.50, H=2453.00, L=2449.50, C=2452.80, V=450000
```

**⚠️ CRITICAL:** Candle is still **OPEN** - Not evaluated yet!

---

## 🕘 9:15:02-9:15:59 AM - Breakout Monitoring (No Action Yet)

### Inside `breakout.py` Lines 46-65
```python
def process_tick(self, tick: dict):
    token = tick['instrument_token']
    price = tick['last_price']
    
    symbol = self.symbol_manager.get_symbol(token)  # "RELIANCE"
    if not symbol:
        return
    
    # Only monitor marked symbols
    if not self.marker.is_marked(symbol):
        return  # ← EXITS HERE (no stocks marked yet)
```

**What happens:**
- Checks if RELIANCE is marked
- **NOT MARKED YET** (marking happens when 9:15 candle closes)
- **Returns immediately** - No breakout monitoring yet

---

## 🕘 9:16:00 AM - THE CRITICAL MOMENT (Candle Close)

### First tick of 9:16 arrives

**Tick data:**
```python
{
    'instrument_token': 738561,
    'last_price': 2453.50,
    'volume_traded': 460000,
    'exchange_timestamp': datetime(2025, 11, 24, 9, 16, 0),  # ← NEW MINUTE!
}
```

---

### Inside `candles.py` Lines 79-84
```python
current_min = timestamp.replace(second=0, microsecond=0)  # 09:16:00

with self.lock:
    # Check if minute has changed
    if self.current_minute and current_min > self.current_minute:
        self._close_all_candles(self.current_minute)  # ← TRIGGERS!
```

**Evaluation:**
- `self.current_minute` = `09:15:00`
- `current_min` = `09:16:00`
- **Condition:** `09:15:00 and 09:16:00 > 09:15:00` → **TRUE**
- **Action:** Close all candles for 09:15:00

---

## 🕘 9:16:00.100 AM - Closing 9:15 Candles

### Inside `candles.py` Lines 112-146
```python
def _close_all_candles(self, minute: datetime):
    for token, candle_data in list(self.active_candles.items()):
        symbol = self.symbol_manager.get_symbol(token)  # "RELIANCE"
        if not symbol:
            continue
        
        # Create completed candle
        completed = Candle(
            symbol=symbol,              # "RELIANCE"
            timestamp=minute,           # 09:15:00
            open=candle_data['open'],   # 2450.50
            high=candle_data['high'],   # 2453.00
            low=candle_data['low'],     # 2449.50
            close=candle_data['close'], # 2452.80
            volume=candle_data['volume']  # 450000
        )
        
        # Store in buffer
        self.completed_candles[token] = completed
        self.previous_volume[token] = candle_data['cumulative_volume']
        
        # Trigger callback ← THIS IS THE KEY!
        if self.on_candle_close:
            try:
                self.on_candle_close(completed)  # ← Calls marker.evaluate_and_mark()
            except Exception as e:
                logger.error(f"Error in candle close callback for {symbol}: {e}")
    
    # Clear active candles for next minute
    self.active_candles.clear()
    logger.debug(f"Closed {len(self.completed_candles)} candles for minute {minute.strftime('%H:%M')}")
```

**Console Output:**
```
09:16:00 | DEBUG | Closed 5 candles for minute 09:15
```

**⚠️ NOTE:** This is DEBUG level - you won't see it unless `LOG_LEVEL = "DEBUG"`

**What happens:**
- Creates completed Candle object for RELIANCE (and all other symbols)
- **Triggers callback:** `marker.evaluate_and_mark(completed)`

---

## 🕘 9:16:00.150 AM - Stock Evaluation & Marking

### Inside `marker.py` Lines 41-56
```python
def evaluate_and_mark(self, candle: Candle) -> bool:
    self.total_evaluated += 1
    
    # Check if it's the 9:15 candle
    candle_time = candle.timestamp.time()  # 09:15:00
    if not (time(9, 15) <= candle_time < time(9, 16)):
        return False  # ← Only marks 9:15 candles
```

**Evaluation:**
- `candle_time` = `09:15:00`
- **Condition:** `09:15:00 <= 09:15:00 < 09:16:00` → **TRUE**
- **Continue to volume check**

---

### Inside `marker.py` Lines 58-70
```python
symbol = candle.symbol  # "RELIANCE"

# Get historical data
avg_volume = self.historical_manager.get_avg_volume(symbol)
# Returns: sum of 14 days volume / 14
# Example: 200000 (average daily volume)

if avg_volume == 0:
    logger.debug(f"{symbol}: No historical data available")
    return False

# Criterion 1: Volume check
volume_ratio = candle.volume / avg_volume  # 450000 / 200000 = 2.25
if volume_ratio < self.config['VOLUME_MULTIPLIER']:  # 2.25 < 2.0?
    logger.debug(f"{symbol}: Volume {volume_ratio:.2f}x (need {self.config['VOLUME_MULTIPLIER']}x)")
    return False
```

**Scenario 1: RELIANCE has high volume (2.25x)**
- `volume_ratio` = `2.25`
- `VOLUME_MULTIPLIER` = `2.0`
- **Condition:** `2.25 < 2.0` → **FALSE**
- **Continue to marking**

**Scenario 2: TCS has low volume (1.8x)**
- `volume_ratio` = `1.8`
- **Condition:** `1.8 < 2.0` → **TRUE**
- **Console Output:**
```
09:16:00 | DEBUG | TCS: Volume 1.80x (need 2.0x)
```
- **Returns FALSE** - Not marked

---

### Inside `marker.py` Lines 72-79 (RELIANCE gets marked)
```python
# All criteria met - MARK IT!
with self.lock:
    self.marked_symbols.add(symbol)  # Add "RELIANCE" to set
    self.first_candles[symbol] = candle  # Store 9:15 candle
    self.total_marked += 1

logger.info(f"✓ MARKED: {symbol} | Vol: {volume_ratio:.2f}x | High: {candle.high:.2f}")
return True
```

**Console Output:**
```
09:16:00 | INFO | ✓ MARKED: RELIANCE | Vol: 2.25x | High: 2453.00
09:16:00 | INFO | ✓ MARKED: INFY | Vol: 2.10x | High: 1450.50
```

**What happens:**
- RELIANCE and INFY are marked (high volume)
- TCS, HDFCBANK, ICICIBANK are NOT marked (low volume)

**State after marking:**
```python
self.marked_symbols = {'RELIANCE', 'INFY'}
self.first_candles = {
    'RELIANCE': Candle(symbol='RELIANCE', timestamp=09:15:00, high=2453.00, ...),
    'INFY': Candle(symbol='INFY', timestamp=09:15:00, high=1450.50, ...)
}
```

---

## 🕘 9:16:01-9:16:05 AM - Breakout Monitoring Begins

### Ticks continue arriving for all symbols

**For RELIANCE (marked):**

### Inside `breakout.py` Lines 46-76
```python
def process_tick(self, tick: dict):
    token = tick['instrument_token']  # 738561
    price = tick['last_price']  # 2453.80
    
    symbol = self.symbol_manager.get_symbol(token)  # "RELIANCE"
    
    # Only monitor marked symbols
    if not self.marker.is_marked(symbol):
        return  # ← NOW PASSES (RELIANCE is marked)
    
    # Check if already triggered
    if symbol in self.breakout_triggered:
        return  # ← Not triggered yet
    
    # Update last price
    with self.lock:
        self.last_prices[token] = price  # Store 2453.80
    
    # Get breakout level
    breakout_level = self.marker.get_breakout_level(symbol)
```

---

### Inside `marker.py` Lines 94-104 (Calculate breakout level)
```python
def get_breakout_level(self, symbol: str) -> float:
    candle = self.first_candles.get(symbol)  # Get 9:15 candle
    if not candle:
        return 0
    
    buffer = candle.high * (self.config['BREAKOUT_BUFFER_PERCENT'] / 100)
    # buffer = 2453.00 * (0.05 / 100) = 1.2265
    
    return candle.high + buffer
    # return 2453.00 + 1.23 = 2454.23
```

**Breakout level for RELIANCE:** `2454.23`

---

### Back in `breakout.py` Line 75-76
```python
# BREAKOUT DETECTION
if price >= breakout_level:  # 2453.80 >= 2454.23?
    self._trigger_breakout(symbol, price)
```

**Evaluation:**
- `price` = `2453.80`
- `breakout_level` = `2454.23`
- **Condition:** `2453.80 >= 2454.23` → **FALSE**
- **No breakout yet** - Price needs to go higher

---

## 🕘 9:16:08 AM - BREAKOUT TRIGGERED!

### New tick arrives for RELIANCE
```python
{
    'instrument_token': 738561,
    'last_price': 2454.50,  # ← PRICE CROSSED BREAKOUT LEVEL!
    'exchange_timestamp': datetime(2025, 11, 24, 9, 16, 8),
}
```

---

### Inside `breakout.py` Line 75
```python
if price >= breakout_level:  # 2454.50 >= 2454.23?
    self._trigger_breakout(symbol, price)  # ← TRIGGERS!
```

**Condition:** `2454.50 >= 2454.23` → **TRUE**

---

## 🕘 9:16:08.100 AM - Breakout Execution

### Inside `breakout.py` Lines 78-112
```python
def _trigger_breakout(self, symbol: str, entry_price: float):
    # Mark as triggered
    self.breakout_triggered[symbol] = True
    self.breakouts_detected += 1
    
    # Get stop loss from CURRENT breakout candle's open
    stoploss = self.candle_builder.get_current_candle_open(symbol)
    # Returns: Open price of 9:16 candle (currently building)
    # Example: 2453.50
    
    # Fallback: If not available, use 9:15 candle open
    if stoploss is None or stoploss == 0:
        stoploss = self.marker.get_stoploss_level(symbol)
        # Returns: 2450.50 (9:15 candle open)
    
    # Get 9:15 candle for logging
    first_candle = self.marker.get_first_candle(symbol)
    
    logger.info(
        f"🚀 BREAKOUT: {symbol} @ {entry_price:.2f} | "
        f"SL: {stoploss:.2f} (Breakout Candle Open) | "
        f"9:15 High: {first_candle.high:.2f}"
    )
```

**Console Output:**
```
09:16:08 | INFO | 🚀 BREAKOUT: RELIANCE @ 2454.50 | SL: 2453.50 (Breakout Candle Open) | 9:15 High: 2453.00
```

---

### Inside `breakout.py` Lines 105-109
```python
# Execute entry via callback
if self.on_breakout:
    try:
        self.on_breakout(symbol, entry_price, stoploss)  # ← Calls _execute_entry()
    except Exception as e:
        logger.error(f"Error in breakout callback for {symbol}: {e}")
```

**What happens:** Triggers entry execution callback.

---

## 🕘 9:16:08.150 AM - Entry Execution

### Inside `main.py` Lines 186-222
```python
def _execute_entry(self, symbol: str, entry_price: float, stoploss: float):
    # Check if can take trade
    if not self.portfolio.can_take_trade(MAX_TRADES_PER_DAY):  # 0 < 5?
        logger.warning(f"Max trades reached ({MAX_TRADES_PER_DAY}) - skipping {symbol}")
        return
```

**Check:** Current trades = 0, Max = 5 → **PASS**

---

```python
    # Check max loss
    if self.risk_manager.check_max_loss():  # Daily loss > 5000?
        logger.critical("Max daily loss reached - stopping trading")
        return
```

**Check:** Daily loss = 0 → **PASS**

---

```python
    # Calculate position size
    quantity = self.risk_manager.calculate_position_size(symbol, entry_price, stoploss)
    # Calculates: How many shares to buy based on risk
    # Example: 50 shares
```

**Inside `risk.py`:**
```python
risk_per_trade = TOTAL_CAPITAL * 0.02  # 100000 * 0.02 = 2000
risk_per_share = entry_price - stoploss  # 2454.50 - 2453.50 = 1.00
quantity = risk_per_trade / risk_per_share  # 2000 / 1.00 = 2000 shares
```

---

```python
    if quantity == 0:
        logger.warning(f"{symbol}: Position size = 0, skipping entry")
        return
```

**Check:** Quantity = 2000 → **PASS**

---

```python
    # Place order
    order_id = self.order_executor.place_buy_order(symbol, quantity, entry_price)
```

**DRY-RUN MODE:**

### Inside `orders_dryrun.py`
```python
def place_buy_order(self, symbol: str, quantity: int, price: float) -> str:
    order_id = f"DRY_{symbol}_{int(time.time())}"
    
    # Simulate slippage
    slippage = price * (self.config['SLIPPAGE_PERCENT'] / 100)
    execution_price = price + slippage  # 2454.50 + 2.45 = 2456.95
    
    # Store order
    self.orders[order_id] = {
        'symbol': symbol,
        'quantity': quantity,
        'price': execution_price,
        'status': 'COMPLETE'
    }
    
    logger.info(f"[DRY-RUN] BUY {symbol} x{quantity} @ {execution_price:.2f}")
    return order_id
```

**Console Output:**
```
09:16:08 | INFO | [DRY-RUN] BUY RELIANCE x2000 @ 2456.95
```

---

### Back in `main.py` Lines 214-222
```python
    # Get actual execution price
    actual_price = self.order_executor.get_average_price(order_id) or entry_price
    # Returns: 2456.95
    
    # Add to portfolio
    self.portfolio.add_position(symbol, actual_price, stoploss, quantity)
    
    # Log trade
    self.trade_logger.log_entry(symbol, quantity, actual_price, order_id)
    
    logger.info(f"✅ ENTRY: {symbol} x{quantity} @ {actual_price:.2f} | SL: {stoploss:.2f}")
```

**Console Output:**
```
09:16:08 | INFO | ✅ ENTRY: RELIANCE x2000 @ 2456.95 | SL: 2453.50
```

**What happens:**
- Order placed (dry-run simulated)
- Position added to portfolio
- Trade logged to CSV file

---

## 🕘 9:16:08 AM - Post-Entry State

**Portfolio:**
```python
{
    'RELIANCE': Position(
        symbol='RELIANCE',
        entry_price=2456.95,
        stoploss=2453.50,
        quantity=2000,
        current_price=2456.95,
        unrealized_pnl=0
    )
}
```

**Marked symbols:**
```python
# RELIANCE removed from marked_symbols (line 112 in breakout.py)
self.marked_symbols = {'INFY'}  # Only INFY remains
```

---

## 🕘 9:16:09-15:30:00 - Continuous Monitoring

### For RELIANCE (active position):

**Every tick:**

### Inside `risk.py` - Stop-Loss Monitoring
```python
def process_tick(self, tick: dict):
    symbol = self.symbol_manager.get_symbol(tick['instrument_token'])
    price = tick['last_price']
    
    position = self.portfolio.get_position(symbol)
    if not position:
        return  # No position
    
    # Update current price
    position.current_price = price
    
    # Check stop-loss
    if price <= position.stoploss:  # Hit stop-loss?
        self._trigger_exit(symbol, price, "STOP_LOSS")
```

**Scenario: Price drops to 2453.40**
```
09:16:15 | INFO | ⚠️ STOP-LOSS HIT: RELIANCE @ 2453.40
09:16:15 | INFO | [DRY-RUN] SELL RELIANCE x2000 @ 2453.40
09:16:15 | INFO | ✅ EXIT: RELIANCE @ 2453.40 | Reason: STOP_LOSS | PNL: -7100.00
```

---

### For INFY (still marked, waiting for breakout):

**Every tick:**
- Monitors if price crosses breakout level
- If YES → Triggers entry (same flow as RELIANCE)
- If NO → Continues monitoring

---

## 🕘 15:30:00 - Market Close

**What happens:**
- Ticks stop arriving
- WebSocket may disconnect
- System remains running (blocking on `ticker.connect()`)

**To stop:**
- Press `Ctrl+C` → Triggers `KeyboardInterrupt` (line 328-330)

---

## Summary of Complete Flow

```
09:00:00 → System starts
09:00:01 → Kite connected
09:00:01 → Modules initialized
09:00:01 → Historical data fetch starts
09:00:15 → Historical data ready
09:00:15 → Waiting for 9:15...
09:15:00 → Market opens!
09:15:00 → WebSocket connecting...
09:15:01 → ✓ WebSocket connected
09:15:01 → Subscribed to 5 instruments
09:15:02 → First ticks arrive (silent)
09:15:02-59 → Building 9:15 candles (silent)
09:16:00 → 9:15 candles close
09:16:00 → ✓ MARKED: RELIANCE, INFY
09:16:01-08 → Monitoring for breakout
09:16:08 → 🚀 BREAKOUT: RELIANCE
09:16:08 → ✅ ENTRY: RELIANCE x2000
09:16:09+ → Monitoring stop-loss
15:30:00 → Market closes
```

---

## Why You Saw Only "WebSocket connected"

**Most likely causes:**

1. **No "Subscribed to X instruments" log**
   - Means: `subscribed_tokens` was empty
   - Reason: No symbols loaded from CSV

2. **Ticks arriving but silent**
   - No logging in `on_ticks()` callback
   - Can't tell if ticks are coming

3. **Ticks filtered out**
   - Time was before 9:15:00 or after 15:30:00
   - Silent filtering in `tick_router.py`

4. **Market was closed**
   - Weekend, holiday, or outside hours
   - No ticks sent by Zerodha

**Next step:** Check your logs for "Subscribed to X instruments" message!
