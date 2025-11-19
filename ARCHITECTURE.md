# System Architecture - 9:15 Breakout Trading System

## Overview

This document describes the detailed architecture of the 9:15 breakout trading system, including module interactions, data flows, and design decisions.

## Design Principles

1. **Ultra-Low Latency**: Tick-by-tick processing with minimal overhead
2. **Modular Design**: Independent, reusable components
3. **Thread Safety**: Lock-based synchronization for shared resources
4. **Equal Capital Distribution**: Fair allocation across opportunities
5. **Fail-Safe**: Error handling and graceful degradation

---

## Complete Module Reference

### 1. Main Orchestrator

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\main.py`

**Class**: `TradingSystem`

**Methods**:

- `__init__()` - Initialize system, load config, setup all modules
- `_initialize_kite()` → KiteConnect - Setup API connection
- `_initialize_modules()` - Initialize all trading modules
- `_setup_callbacks()` - Configure inter-module callbacks
- `_execute_entry(symbol, entry_price, stoploss)` - Execute breakout entry
- `_execute_exit(symbol, exit_price, reason)` - Execute position exit
- `fetch_historical_data()` - Fetch 14-day historical data
- `start_trading()` - Start live trading with WebSocket
- `print_stats()` - Display system statistics

**Function**: `main()`

- Entry point for system execution
- Manages pre-market and trading phases

---

### 2. Configuration Management

#### Settings Module

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\config\settings.py`

**No Classes** (Configuration constants)

**Constants**:

- `TOTAL_CAPITAL` - Total trading capital
- `MAX_TRADES_PER_DAY` - Maximum concurrent positions
- `VOLUME_MULTIPLIER` - Volume threshold multiplier
- `BREAKOUT_BUFFER_PERCENT` - Buffer for breakout detection
- `DRY_RUN_MODE` - Enable/disable paper trading
- `ORDER_TYPE` - Order type (MARKET/LIMIT)
- `PRODUCT_TYPE` - Product type (MIS/CNC)
- `EXCHANGE` - Trading exchange (NSE)
- `SLIPPAGE_PERCENT` - Slippage simulation
- `MAX_LOSS_PER_DAY` - Maximum daily loss limit
- `MARKET_OPEN_TIME` - Market opening time (9:15 AM)
- `MARKET_CLOSE_TIME` - Market closing time (3:30 PM)
- `HISTORICAL_DAYS` - Days of historical data
- `API_RATE_LIMIT` - API request rate limit
- `SYMBOLS_CSV_PATH` - Path to symbols CSV
- `OUTPUT_DIR` - Output directory for logs
- `TRADES_CSV_PREFIX` - Trade log file prefix
- `LOG_LEVEL` - Logging level
- `WS_RECONNECT_DELAY` - WebSocket reconnect delay
- `WS_RECONNECT_MAX_TRIES` - Max reconnection attempts

#### Token Generator

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\config\token_generator.py`

**No Classes** (Utility script)

**Function**: `get_access_token()`

- Generate Zerodha access token
- Update secrets.env file
- Return access token string

#### Secrets Configuration

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\config\secrets.env`

**Environment Variables**:

- `API_KEY` - Zerodha API key
- `API_SECRET` - Zerodha API secret
- `ACCESS_TOKEN` - Generated access token

---

### 3. Symbol Management

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\core\symbols.py`

**Class**: `SymbolManager`

**Methods**:

- `__init__(kite)` - Initialize with Kite connection
- `load_symbols_from_csv(csv_path)` - Load symbols from CSV file
- `map_tokens(exchange)` - Map symbols to instrument tokens
- `get_token(symbol)` → int - Get token for symbol (O(1))
- `get_symbol(token)` → str - Get symbol for token (O(1))
- `get_all_tokens()` → List[int] - Get all instrument tokens
- `get_all_symbols()` → List[str] - Get all symbol names
- `is_valid_symbol(symbol)` → bool - Check if symbol exists

**Data Structures**:

```python
symbols: List[str]              # ['RELIANCE', 'TCS', ...]
token_map: Dict[str, int]       # 'RELIANCE' → 738561
reverse_token_map: Dict[int, str]  # 738561 → 'RELIANCE'
```

---

### 4. Historical Data Management

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\core\historical.py`

**Class**: `HistoricalDataManager`

**Methods**:

- `__init__(kite, symbol_manager)` - Initialize with dependencies
- `fetch_single_symbol_data(symbol, token, days)` → tuple - Fetch data for one symbol
- `fetch_all_historical_data(days=14)` - Fetch data for all symbols (sequential)
- `get_avg_volume(symbol)` → float - Get 14-day average volume (O(1))
- `get_avg_range(symbol)` → float - Get 14-day average range % (O(1))
- `is_data_ready(symbol)` → bool - Check if data available

**Data Structures**:

```python
avg_volumes: Dict[str, float]   # symbol → 14-day avg volume
avg_ranges: Dict[str, float]    # symbol → 14-day avg range %
```

**Algorithm**:

```
For each symbol (sequential):
  1. Fetch last 14 days of daily candles
  2. Calculate: avg_volume = mean(volumes)
  3. Calculate: avg_range = mean((high-low)/low × 100)
  4. Store in hash maps
  5. Sleep to respect API rate limit (3 req/sec)
```

---

### 5. Candle Builder

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\core\candles.py`

**DataClass**: `Candle`

**Attributes**:

- `symbol: str` - Symbol name
- `timestamp: datetime` - Candle timestamp
- `open: float` - Open price
- `high: float` - High price
- `low: float` - Low price
- `close: float` - Close price
- `volume: int` - Volume

**Methods**:

- `range_percent()` → float - Calculate candle range %

**Class**: `CandleBuilder`

**Methods**:

- `__init__(symbol_manager)` - Initialize candle builder
- `set_on_candle_close_callback(callback)` - Set callback for candle close
- `process_tick(tick)` - Process incoming tick, update candles
- `_close_all_candles(minute)` - Close all candles for completed minute
- `get_candle(symbol)` → Optional[Candle] - Get last completed candle (O(1))
- `get_active_candle_data(symbol)` → Optional[dict] - Get current building candle
- `get_current_candle_open(symbol)` → Optional[float] - Get open of current candle (for SL)
- `force_close_candles()` - Force close all active candles

**Data Structures**:

```python
active_candles: Dict[int, dict]      # token → current candle data
completed_candles: Dict[int, Candle] # token → last completed candle
current_minute: Optional[time]       # Current minute tracker
lock: threading.Lock                 # Thread safety
```

**Real-time Processing**:

```
On each tick:
  1. Check if minute changed → close previous candles
  2. Update active candle:
     - First tick → set open
     - Every tick → high = max(high, price)
                   low = min(low, price)
                   close = price
  3. Store completed candles
```

---

### 6. Stock Marker

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\core\marker.py`

**Class**: `StockMarker`

**Methods**:

- `__init__(historical_manager, config)` - Initialize marker
- `evaluate_and_mark(candle)` - Evaluate 9:15 candle and mark if qualified
- `_check_volume_criterion(symbol, volume)` → bool - Check volume threshold
- `_check_range_criterion(symbol, candle_range)` → bool - Check range threshold
- `is_marked(symbol)` → bool - Check if symbol is marked
- `get_breakout_level(symbol)` → float - Get 9:15 high (breakout level)
- `get_stoploss_level(symbol)` → float - Get 9:15 low (fallback SL)
- `get_first_candle(symbol)` → Optional[Candle] - Get 9:15 candle
- `get_all_marked_symbols()` → List[str] - Get all marked symbols
- `unmark_symbol(symbol)` - Remove from marked list
- `get_stats()` → dict - Get marking statistics

**Data Structures**:

```python
marked_symbols: Dict[str, Candle]  # symbol → 9:15 candle
breakout_levels: Dict[str, float]  # symbol → 9:15 high
stoploss_levels: Dict[str, float]  # symbol → 9:15 low
total_evaluated: int               # Count of evaluated stocks
total_marked: int                  # Count of marked stocks
```

**Marking Criteria**:

```python
def should_mark(candle):
    # Only 9:15-9:16 candle
    if candle.timestamp.time() != time(9, 15):
        return False

    # Volume: current ≥ (14-day avg × multiplier)
    if candle.volume < (avg_volume × VOLUME_MULTIPLIER):
        return False

    # Range: current % ≥ 14-day avg %
    current_range = (candle.high - candle.low) / candle.low × 100
    if current_range < avg_range:
        return False

    return True
```

---

### 7. Breakout Detection Engine

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\core\breakout.py`

**Class**: `BreakoutEngine`

**Methods**:

- `__init__(marker, symbol_manager, config, candle_builder)` - Initialize engine
- `set_on_breakout_callback(callback)` - Set callback for breakout execution
- `process_tick(tick)` - Process tick for breakout detection
- `_trigger_breakout(symbol, entry_price)` - Trigger breakout entry
- `get_last_price(symbol)` → Optional[float] - Get last known price
- `is_breakout_triggered(symbol)` → bool - Check if already triggered
- `get_stats()` → dict - Get breakout statistics
- `reset()` - Reset for next trading day

**Data Structures**:

```python
last_prices: Dict[int, float]           # token → last price
breakout_triggered: Dict[str, bool]     # symbol → triggered status
lock: threading.Lock                    # Thread safety
breakouts_detected: int                 # Count of breakouts
```

**Detection Logic**:

```
On each tick:
  1. Get symbol from token
  2. Is marked? → No: skip
  3. Already triggered? → Yes: skip
  4. Price ≥ breakout_level? → Yes: TRIGGER
```

**Entry Execution**:

```
On breakout:
  1. Mark as triggered (prevent duplicates)
  2. Get current candle open → primary SL
  3. Fallback: Use 9:15 low → secondary SL
  4. Call on_breakout callback
  5. Unmark symbol (done monitoring)
```

---

### 8. Risk Management

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\core\risk.py`

**Class**: `RiskManager`

**Methods**:

- `__init__(portfolio, symbol_manager, config, marker)` - Initialize risk manager
- `set_on_exit_callback(callback)` - Set callback for exit execution
- `process_tick(tick)` - Monitor tick for stop-loss hits
- `_check_stoploss(position, current_price)` → bool - Check if SL hit
- `_trigger_exit(symbol, exit_price, reason)` - Trigger position exit
- `calculate_position_size(symbol, entry_price, stoploss)` → int - Calculate quantity
- `check_max_loss()` → bool - Check if max daily loss hit
- `get_stats()` → dict - Get risk statistics

**Data Structures**:

```python
stops_hit: int  # Count of stop-loss hits
```

**Position Sizing (Equal Capital Distribution)**:

```python
def calculate_position_size(symbol, entry_price, stoploss):
    num_marked = len(marker.get_all_marked_symbols())
    capital_per_stock = TOTAL_CAPITAL / num_marked
    quantity = int(capital_per_stock / entry_price)
    return quantity
```

**Example**:

```
Total Capital: ₹100,000
Marked: 4 stocks

Capital/stock: ₹100,000 / 4 = ₹25,000

RELIANCE @ ₹2500: 25,000 / 2500 = 10 shares
TCS @ ₹3500: 25,000 / 3500 = 7 shares
```

**Stop-Loss Monitoring**:

```
On each tick:
  1. Has position? → No: skip
  2. Update position price
  3. Check: price ≤ stoploss? → Yes: TRIGGER EXIT
```

---

### 9. Portfolio Management

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\core\portfolio.py`

**DataClass**: `Position`

**Attributes**:

- `symbol: str` - Symbol name
- `entry_price: float` - Entry price
- `stoploss: float` - Stop-loss level
- `quantity: int` - Quantity
- `entry_time: datetime` - Entry timestamp
- `current_price: float` - Current market price
- `unrealized_pnl: float` - Unrealized PNL
- `realized_pnl: float` - Realized PNL (after exit)
- `exit_price: Optional[float]` - Exit price
- `exit_time: Optional[datetime]` - Exit timestamp
- `exit_reason: Optional[str]` - Exit reason

**Methods**:

- `update_price(price)` - Update current price and unrealized PNL
- `close(exit_price, reason)` - Close position and calculate realized PNL

**Class**: `Portfolio`

**Methods**:

- `__init__(total_capital)` - Initialize portfolio
- `add_position(symbol, entry_price, stoploss, quantity)` → Position - Add new position
- `close_position(symbol, exit_price, reason)` → Optional[Position] - Close position
- `update_position_price(symbol, current_price)` - Update position price
- `get_position(symbol)` → Optional[Position] - Get active position
- `has_position(symbol)` → bool - Check if position exists
- `get_all_positions()` → List[Position] - Get all active positions
- `can_take_trade(max_trades)` → bool - Check if can open new position
- `get_stats()` → dict - Get portfolio statistics
- `reset()` - Reset for next trading day

**Data Structures**:

```python
positions: Dict[str, Position]      # Active positions
closed_positions: List[Position]    # Trade history
total_capital: float                # Total capital
total_pnl: float                   # Cumulative PNL
trades_today: int                  # Trades count
wins: int                          # Winning trades
losses: int                        # Losing trades
```

---

### 10. Order Execution (Live)

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\core\orders_live.py`

**Class**: `LiveOrderExecutor`

**Methods**:

- `__init__(kite, symbol_manager, config)` - Initialize executor
- `place_buy_order(symbol, quantity, price=None)` → Optional[str] - Place buy order
- `place_sell_order(symbol, quantity, price=None)` → Optional[str] - Place sell order
- `get_order_status(order_id)` → Optional[dict] - Get order details
- `cancel_order(order_id)` → bool - Cancel order
- `get_average_price(order_id)` → Optional[float] - Get execution price
- `get_stats()` → dict - Get execution statistics

**Data Structures**:

```python
orders: Dict[str, dict]  # order_id → order details
orders_placed: int       # Count of orders placed
orders_executed: int     # Count of executed orders
orders_failed: int       # Count of failed orders
```

---

### 11. Order Execution (Dry-Run)

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\core\orders_dryrun.py`

**Class**: `DryRunOrderExecutor`

**Methods**:

- `__init__(symbol_manager, config)` - Initialize dry-run executor
- `_apply_slippage(price, transaction_type)` → float - Apply slippage simulation
- `place_buy_order(symbol, quantity, price=None)` → Optional[str] - Simulate buy order
- `place_sell_order(symbol, quantity, price=None)` → Optional[str] - Simulate sell order
- `get_order_status(order_id)` → Optional[dict] - Get simulated order details
- `cancel_order(order_id)` → bool - Simulate cancellation
- `get_average_price(order_id)` → Optional[float] - Get simulated execution price
- `get_stats()` → dict - Get execution statistics
- `get_all_orders()` → list - Get all simulated orders

**Data Structures**:

```python
orders: Dict[str, dict]  # order_id → order details
orders_placed: int       # Count of orders
orders_executed: int     # Count of executed orders
```

**Slippage Model**:

```python
def _apply_slippage(price, transaction_type):
    slippage = price × (SLIPPAGE_PERCENT / 100)
    if transaction_type == 'BUY':
        return price + slippage  # Worse for buyer
    else:  # SELL
        return price - slippage  # Worse for seller
```

---

### 12. Trade Logging

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\core\trade_logger.py`

**Class**: `TradeLogger`

**Methods**:

- `__init__(config)` - Initialize logger
- `_get_log_filename()` → str - Generate daily log filename
- `_ensure_log_file()` - Create log file with headers
- `log_entry(symbol, quantity, price, order_id)` - Log entry trade
- `log_exit(symbol, quantity, entry_price, exit_price, reason, order_id)` - Log exit trade
- `_write_log(data)` - Write data to CSV file

**Log Format**:

```csv
timestamp,symbol,side,quantity,price,order_id,pnl,reason
2024-01-15 09:25:30,RELIANCE,BUY,13,2522.00,123456,,
2024-01-15 10:45:15,RELIANCE,SELL,13,2518.00,123457,-52.00,STOP_LOSS
```

---

### 13. Utility Functions

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\core\utils.py`

**Decorators**:

- `@timeit(func)` - Measure function execution time

**Functions**:

- `is_market_open(current_time=None)` → bool - Check if market is open
- `is_within_first_minute(current_time=None)` → bool - Check if within 9:15-9:16
- `wait_until(target_time, check_interval=1.0)` - Wait until specific time
- `format_price(price, decimals=2)` → str - Format price with currency
- `format_pnl(pnl)` → str - Format PNL with +/- sign
- `calculate_risk_reward_ratio(entry, stoploss, target)` → float - Calculate R:R ratio
- `round_to_tick_size(price, tick_size=0.05)` → float - Round to tick size

**Class**: `PerformanceMonitor`

**Methods**:

- `__init__()` - Initialize monitor
- `start_timer(name)` - Start timing operation
- `stop_timer(name)` → float - Stop timer and record
- `get_stats(name)` → dict - Get statistics for metric
- `print_stats()` - Print all statistics

**Global Instance**:

- `perf_monitor` - Global performance monitor instance

---

### 14. WebSocket Manager

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\websocket\ws_manager.py`

**Class**: `WebSocketManager`

**Methods**:

- `__init__(api_key, access_token, config)` - Initialize WebSocket
- `set_on_ticks_callback(callback)` - Set callback for tick data
- `subscribe(tokens)` - Subscribe to instrument tokens
- `unsubscribe(tokens)` - Unsubscribe from tokens
- `_on_ticks(ws, ticks)` - Handle incoming ticks
- `_on_connect(ws, response)` - Handle connection
- `_on_close(ws, code, reason)` - Handle disconnection
- `_on_error(ws, code, reason)` - Handle errors
- `start()` - Start WebSocket connection (blocking)
- `stop()` - Stop WebSocket connection

**Data Structures**:

```python
kws: KiteTicker              # WebSocket instance
subscribed_tokens: List[int] # Subscribed tokens
reconnect_count: int         # Reconnection counter
```

---

### 15. Tick Router

**File**: `c:\Users\91948\OneDrive\Desktop\9_15_breakout_system\websocket\tick_router.py`

**Class**: `TickRouter`

**Methods**:

- `__init__(candle_builder, breakout_engine, risk_manager)` - Initialize router
- `route_ticks(ticks)` - Route ticks to all modules

**Routing Logic**:

```python
def route_ticks(ticks):
    for tick in ticks:
        # Parallel routing
        candle_builder.process_tick(tick)
        breakout_engine.process_tick(tick)
        risk_manager.process_tick(tick)
```

---

## Complete Data Flow

### 1. System Initialization Flow

```
main.py::main()
  → TradingSystem.__init__()
    → _initialize_kite()
      → KiteConnect setup
      → Test connection
    → _initialize_modules()
      → SymbolManager.load_symbols_from_csv()
      → SymbolManager.map_tokens()
      → HistoricalDataManager.__init__
      → CandleBuilder.__init__
      → Portfolio.__init__
      → StockMarker.__init__
      → BreakoutEngine.__init__
      → RiskManager.__init__
      → OrderExecutor.__init__() (Live/DryRun)
      → TradeLogger.__init__
      → TickRouter.__init__
      → WebSocketManager.__init__
    → _setup_callbacks()
      → CandleBuilder.set_on_candle_close_callback()
      → BreakoutEngine.set_on_breakout_callback()
      → RiskManager.set_on_exit_callback()
      → WebSocketManager.set_on_ticks_callback()
```

### 2. Pre-Market Data Fetch Flow

```
main.py::main()
  → TradingSystem.fetch_historical_data()
    → HistoricalDataManager.fetch_all_historical_data()
      → For each symbol (sequential):
        → fetch_single_symbol_data()
          → kite.historical_data()
          → Calculate avg_volume
          → Calculate avg_range
          → Store in hash maps
          → Sleep for rate limiting
```

### 3. Live Trading Flow

```
main.py::main()
  → TradingSystem.start_trading()
    → WebSocketManager.subscribe(tokens)
    → WebSocketManager.start()
      → KiteTicker.connect() (blocking)

On Tick Received:
  → WebSocketManager._on_ticks()
    → TickRouter.route_ticks()
      → [Parallel Routing]

      [Branch 1: Candle Building]
      → CandleBuilder.process_tick()
        → Update/create active candle
        → Check minute change?
          → _close_all_candles()
            → Create Candle objects
            → Trigger callback: on_candle_close
              → StockMarker.evaluate_and_mark()
                → _check_volume_criterion()
                → _check_range_criterion()
                → Mark symbol if qualified

      [Branch 2: Breakout Detection]
      → BreakoutEngine.process_tick()
        → Is marked? → Check price ≥ breakout_level?
          → _trigger_breakout()
            → Get current candle open (SL)
            → Trigger callback: on_breakout
              → TradingSystem._execute_entry()
                → RiskManager.calculate_position_size()
                → OrderExecutor.place_buy_order()
                → Portfolio.add_position()
                → TradeLogger.log_entry()

      [Branch 3: Stop-Loss Monitoring]
      → RiskManager.process_tick()
        → Has position? → Update price
        → Check stoploss hit?
          → _trigger_exit()
            → Trigger callback: on_exit
              → TradingSystem._execute_exit()
                → OrderExecutor.place_sell_order()
                → Portfolio.close_position()
                → TradeLogger.log_exit()
```

### 4. Position Lifecycle Flow

```
ENTRY:
BreakoutEngine._trigger_breakout()
  → TradingSystem._execute_entry()
    → Portfolio.can_take_trade() ✓
    → RiskManager.check_max_loss() ✓
    → RiskManager.calculate_position_size()
    → OrderExecutor.place_buy_order()
    → OrderExecutor.get_average_price()
    → Portfolio.add_position()
    → TradeLogger.log_entry()

MONITORING:
RiskManager.process_tick()
  → Portfolio.update_position_price()
  → _check_stoploss()

EXIT:
RiskManager._trigger_exit()
  → TradingSystem._execute_exit()
    → Portfolio.get_position()
    → OrderExecutor.place_sell_order()
    → OrderExecutor.get_average_price()
    → Portfolio.close_position()
    → TradeLogger.log_exit()
```

---

## Thread Safety

### Synchronized Resources

1. **CandleBuilder.active_candles**

   - Protected by: `self.lock`
   - Operations: `process_tick()`, `_close_all_candles()`

2. **BreakoutEngine.last_prices**

   - Protected by: `self.lock`
   - Operations: `process_tick()`

3. **WebSocket Connection**
   - Single-threaded by design
   - No explicit locking needed

---

## Performance Optimizations

### O(1) Operations

- Symbol → Token lookup: `SymbolManager.get_token()`
- Token → Symbol lookup: `SymbolManager.get_symbol()`
- Average volume lookup: `HistoricalDataManager.get_avg_volume()`
- Average range lookup: `HistoricalDataManager.get_avg_range()`
- Marked symbol check: `StockMarker.is_marked()`
- Position lookup: `Portfolio.get_position()`
- Last candle lookup: `CandleBuilder.get_candle()`

### Fast-Path Checks

```python
# Early returns for non-relevant data
if not marker.is_marked(symbol):
    return  # Skip unmarked symbols

if not portfolio.has_position(symbol):
    return  # Skip if no position

if breakout_triggered.get(symbol):
    return  # Skip if already triggered
```

---

## Configuration Summary

**Capital Management**:

- `TOTAL_CAPITAL`: ₹100,000
- `MAX_TRADES_PER_DAY`: 5
- Equal distribution among marked stocks

**Marking Criteria**:

- `VOLUME_MULTIPLIER`: 1.5x (volume ≥ 14-day avg × 1.5)
- Range % ≥ 14-day avg range %

**Risk Parameters**:

- `MAX_LOSS_PER_DAY`: ₹2,000
- Stop-loss: Breakout candle open (primary), 9:15 low (fallback)

**Execution**:

- `DRY_RUN_MODE`: True (paper trading)
- `ORDER_TYPE`: MARKET
- `PRODUCT_TYPE`: MIS (intraday)
- `SLIPPAGE_PERCENT`: 0.1% (dry-run only)

**API Settings**:

- `API_RATE_LIMIT`: 3 requests/second
- `HISTORICAL_DAYS`: 14 days
- `WS_RECONNECT_MAX_TRIES`: 5
- `WS_RECONNECT_DELAY`: 5 seconds

---

## Deployment Checklist

- [ ] Test in dry-run mode for 1 week
- [ ] Verify all symbols in symbols.csv are valid
- [ ] Check capital allocation logic with test data
- [ ] Ensure ACCESS_TOKEN is fresh (regenerate if needed)
- [ ] Monitor first few live trades closely
- [ ] Have manual override/shutdown ready
- [ ] Verify stop-loss execution accuracy
- [ ] Check trade logging is working
- [ ] Test WebSocket reconnection
- [ ] Validate position sizing calculations

---

**Last Updated**: January 2024  
**System Version**: 1.0.0  
**Architecture Documentation**: Complete
