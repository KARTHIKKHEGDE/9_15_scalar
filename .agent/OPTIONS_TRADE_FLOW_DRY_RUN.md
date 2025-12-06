# Options Trade Flow - Dry Run Mode
## Complete Execution Trace

This document traces the **complete flow** of what happens when an options trade triggers in **DRY-RUN mode**.

---

## 📊 **PHASE 1: NIFTY FUT Candle Building**

### Step 1.1: WebSocket Receives NIFTY FUT Tick
**File:** `websocket/ws_manager.py`
- WebSocket receives tick data for NIFTY25DECFUT
- Tick contains: `{instrument_token, last_price, volume, timestamp, ...}`

### Step 1.2: Tick Enqueued to Router
**File:** `websocket/tick_router.py` → `enqueue_ticks()`
```python
def enqueue_ticks(self, ticks: List[dict]):
    self.tick_queue.put_nowait(ticks)  # Non-blocking queue insertion
```
- Ticks are added to a high-capacity queue (5000 max)
- WebSocket thread remains non-blocking

### Step 1.3: Worker Thread Processes Tick
**File:** `websocket/tick_router.py` → `_worker_loop()` → `_route_single_tick()`
```python
def _route_single_tick(self, tick: dict):
    # 1. Build candles
    self.candle_builder.process_tick(tick)
    
    # 2. Check for breakouts (equity)
    self.breakout_engine.process_tick(tick)
    
    # 3. Monitor risk (equity)
    self.risk_manager.process_tick(tick)
```

### Step 1.4: Candle Builder Updates NIFTY FUT Candle
**File:** `core/candles.py` → `process_tick()`
```python
def process_tick(self, tick: dict):
    token = tick["instrument_token"]
    symbol = self.symbol_manager.get_symbol(token)
    
    # Update 1-minute candle for NIFTY25DECFUT
    candle = self.active_candles[symbol]
    candle.high = max(candle.high, tick["last_price"])
    candle.low = min(candle.low, tick["last_price"])
    candle.close = tick["last_price"]
    candle.volume = tick["volume_traded"]
```

### Step 1.5: Candle Close Event (Every 1 Minute)
**File:** `core/candles.py` → `_on_candle_close()`
```python
def _on_candle_close(self, symbol: str, candle):
    if self.on_candle_close_callback:
        self.on_candle_close_callback(candle)  # Triggers marker evaluation
```

---

## 🎯 **PHASE 2: Candle Marking (Options Marker)**

### Step 2.1: Options Marker Evaluates Candle
**File:** `core/options/options_marker.py` → `evaluate_and_mark()`
**Triggered by:** Candle close callback (setup in `main.py`)

```python
def evaluate_and_mark(self, candle) -> Optional[MarkedCandle]:
    # Check if volume meets threshold
    if self._should_mark(candle):
        # Determine direction
        direction = "RED" if candle.close < candle.open else "GREEN"
        
        # Create marked candle
        marked = MarkedCandle(
            timestamp=candle.timestamp,
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
            direction=direction
        )
        
        # Store for breakout monitoring
        self.marked_candles[candle.timestamp] = marked
        
        logger.info(f"✓ MARKED: {direction} candle @ {timestamp}")
        return marked
```

**Marking Criteria:**
```python
def _should_mark(self, candle) -> bool:
    threshold_volume = 50000  # Base threshold
    return candle.volume >= threshold_volume * self.volume_multiplier
```

**Example Log:**
```
13:16:00 | INFO | ✓ MARKED: RED candle @ 13:15 | O:24500.00 H:24520.00 L:24480.00 C:24485.00 | Vol:125,000
```

---

## 🔥 **PHASE 3: Breakout Detection**

### Step 3.1: Options Breakout Engine Monitors Price
**File:** `core/options/options_breakout.py` → `process_tick()`
**Triggered by:** Every NIFTY FUT tick (via tick router)

```python
def process_tick(self, tick: dict):
    price = tick["last_price"]
    
    # Get all marked candles
    marked_candles = self.marker.get_all_marked_candles()
    
    for timestamp, marked_candle in marked_candles.items():
        if timestamp in self.breakout_triggered:
            continue  # Already triggered
        
        # RED candle: Check if price crossed LOW
        if marked_candle.is_red():
            if price < marked_candle.low:
                self._trigger_breakout("PUT", price, marked_candle, timestamp)
        
        # GREEN candle: Check if price crossed HIGH
        elif marked_candle.is_green():
            if price > marked_candle.high:
                self._trigger_breakout("CALL", price, marked_candle, timestamp)
```

**Breakout Conditions:**
- **RED Candle:** Current price < Marked candle's LOW → Trigger **PUT**
- **GREEN Candle:** Current price > Marked candle's HIGH → Trigger **CALL**

### Step 3.2: Breakout Triggered
**File:** `core/options/options_breakout.py` → `_trigger_breakout()`

```python
def _trigger_breakout(self, option_type: str, breakout_price: float, 
                     marked_candle, timestamp: datetime):
    # Mark as triggered (prevent duplicates)
    self.breakout_triggered.add(timestamp)
    self.breakouts_detected += 1
    
    if option_type == "CALL":
        self.call_signals += 1
    else:
        self.put_signals += 1
    
    logger.info(f"🔥 BREAKOUT DETECTED: {option_type} | "
               f"Breakout Price: {breakout_price:.2f} | "
               f"Marked Candle: {marked_candle.direction} @ {timestamp}")
    
    # Fire callback to main.py
    if self.on_breakout_callback:
        self.on_breakout_callback(option_type, breakout_price, marked_candle)
    
    # Remove marked candle (breakout consumed)
    self.marker.remove_marked_candle(timestamp)
```

**Example Log:**
```
13:17:32 | INFO | 🔥 BREAKOUT DETECTED: PUT | Breakout Price: 24475.00 | 
                  Marked Candle: RED @ 13:15 | High: 24520.00 | Low: 24480.00
```

---

## ⚠️ **ISSUE DETECTED: Callback Signature Mismatch**

### Current Callback in `options_breakout.py` (Line 106):
```python
self.on_breakout_callback(option_type, breakout_price, marked_candle)
# Passes: ("PUT", 24475.00, MarkedCandle)
```

### Expected Callback in `main.py` (Line 244):
```python
def on_options_breakout(direction, strike, option_type, entry_price):
    self._execute_options_entry(direction, strike, option_type, entry_price)
# Expects: (direction, strike, option_type, entry_price)
```

**❌ MISMATCH:** The callback is passing 3 arguments but expecting 4 different arguments!

**This needs to be fixed!** The options breakout engine needs to:
1. Fetch ATM strike from options chain
2. Pass correct parameters to callback

---

## 💰 **PHASE 4: Options Entry Execution (After Fix)**

### Step 4.1: Callback Triggers Entry
**File:** `main.py` → `on_options_breakout()` → `_execute_options_entry()`

**Expected Flow (after fix):**
```python
def _execute_options_entry(self, direction: str, strike: int, 
                          option_type: str, entry_price: float):
    # Check max trades
    if not self.portfolio.can_take_trade(OPTIONS_MAX_TRADES_PER_DAY):
        logger.warning(f"Max options trades reached")
        return
    
    # Build option symbol
    symbol = f"NIFTY{strike}{option_type}"  # e.g., NIFTY24500PE
    quantity = OPTIONS_QUANTITY  # From config
    
    logger.info(f"[OPTIONS_ENTRY] {direction} {symbol} @ {entry_price:.2f}")
```

### Step 4.2: Dry-Run Order Placement
**File:** `core/orders_dryrun.py` → `place_buy_order()`

```python
def place_buy_order(self, symbol: str, quantity: int, price: Optional[float] = None):
    order_id = str(uuid.uuid4())[:8]  # Generate unique ID
    
    # Get REAL current market price from live ticks
    current_ltp = self._get_current_ltp(symbol)
    
    logger.info(f"[ORDER_EXEC] {symbol} BUY - Requested: {price:.2f}, LTP: {current_ltp:.2f}")
    
    # Use LTP if available, otherwise fallback to requested price
    execution_price = current_ltp if current_ltp else price
    
    # Create order record
    order = {
        'order_id': order_id,
        'symbol': symbol,
        'transaction_type': 'BUY',
        'quantity': quantity,
        'requested_price': price,           # Breakout level
        'execution_price': execution_price,  # Actual LTP
        'status': 'COMPLETE',
        'timestamp': datetime.now()
    }
    
    self.orders[order_id] = order
    
    logger.info(f"[DRY-RUN] ✓ BUY: {symbol} x{quantity} @ {execution_price:.2f}")
    return order_id
```

**Example Log:**
```
13:17:32 | INFO | [OPTIONS_ENTRY] BEARISH NIFTY24500PE @ 150.00
13:17:32 | INFO | [ORDER_EXEC] NIFTY24500PE BUY - Requested: 150.00, LTP: 152.50
13:17:32 | INFO | [DRY-RUN] ✓ BUY: NIFTY24500PE x50 @ 152.50 (Diff: +2.50) | ID: a3b4c5d6
```

### Step 4.3: Get Execution Price
**File:** `main.py` → `_execute_options_entry()`

```python
# Get actual execution price
actual_price = self.options_order_executor.get_average_price(order_id) or entry_price

# Calculate targets
target_price = actual_price * (1 + OPTIONS_TARGET_PERCENT / 100)  # e.g., 20%
stoploss = actual_price * 0.8  # 20% stop loss
```

**Example:**
- Entry: 152.50
- Target: 152.50 × 1.20 = **183.00** (20% profit)
- Stop-loss: 152.50 × 0.80 = **122.00** (20% loss)

### Step 4.4: Add Position to Portfolio
**File:** `core/portfolio.py` → `add_position()`

```python
self.portfolio.add_position(symbol, actual_price, stoploss, quantity)
```

**Position Object:**
```python
Position(
    symbol="NIFTY24500PE",
    entry_price=152.50,
    stoploss=122.00,
    quantity=50,
    entry_time=datetime.now()
)
```

### Step 4.5: Log Trade
**File:** `core/trade_logger.py` → `log_entry()`

```python
self.trade_logger.log_entry(symbol, quantity, actual_price, order_id)
```

**CSV Entry:**
```csv
timestamp,symbol,action,quantity,price,order_id,pnl,reason
2025-12-06 13:17:32,NIFTY24500PE,BUY,50,152.50,a3b4c5d6,0.00,Entry
```

**Final Log:**
```
13:17:32 | INFO | ✅ OPTIONS ENTRY: NIFTY24500PE x50 @ 152.50 | Target: 183.00
```

---

## 📈 **PHASE 5: Position Monitoring**

### Step 5.1: Options Risk Manager Monitors Position
**File:** `core/options/options_risk.py` → `process_tick()`
**Triggered by:** Every tick for NIFTY24500PE

```python
def process_tick(self, tick: dict):
    token = tick["instrument_token"]
    symbol = self.symbol_manager.get_symbol(token)
    price = tick["last_price"]
    
    # Check if we have a position
    if not self.portfolio.has_position(symbol):
        return
    
    # Update position with latest price
    self.portfolio.update_position_price(symbol, price)
    
    # Get position
    position = self.portfolio.get_position(symbol)
    
    # Check target
    self._check_target(symbol, price, position)
    
    # Check stop-loss
    self._check_stop_loss(symbol, price, position)
```

### Step 5.2: Target Hit Scenario
**File:** `core/options/options_risk.py` → `_check_target()`

```python
def _check_target(self, symbol: str, price: float, position):
    # Calculate target (percentage-based)
    target = position.entry_price * (1 + self.target_percent / 100)
    
    if price >= target:
        logger.info(f"🎯 TARGET HIT: {symbol} | "
                   f"Entry: {position.entry_price:.2f} | "
                   f"Current: {price:.2f} | "
                   f"Target: {target:.2f}")
        
        # Fire exit callback
        if self.on_exit_callback:
            self.on_exit_callback(symbol, price, "Target Hit")
```

**Example Log:**
```
13:45:12 | INFO | 🎯 TARGET HIT: NIFTY24500PE | Entry: 152.50 | Current: 183.50 | Target: 183.00
```

### Step 5.3: Stop-Loss Hit Scenario
**File:** `core/options/options_risk.py` → `_check_stop_loss()`

```python
def _check_stop_loss(self, symbol: str, price: float, position):
    stoploss = position.stoploss
    
    if price <= stoploss:
        logger.info(f"🛑 STOP-LOSS HIT: {symbol} | "
                   f"Entry: {position.entry_price:.2f} | "
                   f"Current: {price:.2f} | "
                   f"SL: {stoploss:.2f}")
        
        # Fire exit callback
        if self.on_exit_callback:
            self.on_exit_callback(symbol, price, "Stop-Loss Hit")
```

**Example Log:**
```
13:25:45 | INFO | 🛑 STOP-LOSS HIT: NIFTY24500PE | Entry: 152.50 | Current: 120.00 | SL: 122.00
```

---

## 🚪 **PHASE 6: Position Exit**

### Step 6.1: Exit Callback Triggered
**File:** `main.py` → `_execute_exit()`

```python
def _execute_exit(self, symbol: str, exit_price: float, reason: str):
    position = self.portfolio.get_position(symbol)
    
    logger.info(f"[EXIT_FLOW] {symbol} - Exit Price: {exit_price:.2f}")
    
    # Place exit order (using options executor)
    order_id = self.options_order_executor.place_sell_order(symbol, position.quantity, exit_price)
```

### Step 6.2: Dry-Run Sell Order
**File:** `core/orders_dryrun.py` → `place_sell_order()`

```python
def place_sell_order(self, symbol: str, quantity: int, price: Optional[float] = None):
    order_id = str(uuid.uuid4())[:8]
    
    # Get REAL current market price
    current_ltp = self._get_current_ltp(symbol)
    
    logger.info(f"[ORDER_EXEC] {symbol} SELL - Requested: {price:.2f}, LTP: {current_ltp:.2f}")
    
    execution_price = current_ltp if current_ltp else price
    
    order = {
        'order_id': order_id,
        'symbol': symbol,
        'transaction_type': 'SELL',
        'quantity': quantity,
        'execution_price': execution_price,
        'status': 'COMPLETE'
    }
    
    self.orders[order_id] = order
    
    logger.info(f"[DRY-RUN] ✓ SELL: {symbol} x{quantity} @ {execution_price:.2f}")
    return order_id
```

### Step 6.3: Close Position & Calculate P&L
**File:** `core/portfolio.py` → `close_position()`

```python
closed_position = self.portfolio.close_position(symbol, actual_price, reason)
```

**P&L Calculation:**
```python
# Target Hit Example:
entry_price = 152.50
exit_price = 183.50
quantity = 50
pnl = (exit_price - entry_price) * quantity
pnl = (183.50 - 152.50) * 50 = +1,550.00

# Stop-Loss Hit Example:
pnl = (120.00 - 152.50) * 50 = -1,625.00
```

### Step 6.4: Log Exit Trade
**File:** `core/trade_logger.py` → `log_exit()`

```python
self.trade_logger.log_exit(symbol, quantity, entry_price, exit_price, reason, order_id)
```

**CSV Entry:**
```csv
timestamp,symbol,action,quantity,price,order_id,pnl,reason
2025-12-06 13:45:12,NIFTY24500PE,SELL,50,183.50,b7c8d9e0,+1550.00,Target Hit
```

**Final Log:**
```
13:45:12 | INFO | ✅ EXIT: NIFTY24500PE @ 183.50 | Reason: Target Hit | PNL: +1,550.00
```

---

## 📋 **Summary of Complete Flow**

```
1. NIFTY FUT Tick → WebSocket
2. Tick → Queue → Worker Thread
3. Worker → CandleBuilder (builds 1-min candles)
4. Candle Close → OptionsMarker.evaluate_and_mark()
5. If volume > threshold → Mark candle (RED/GREEN)
6. Every tick → OptionsBreakoutEngine.process_tick()
7. If price crosses marked candle → Trigger breakout
8. Breakout → Callback → main._execute_options_entry()
9. Entry → DryRunOrderExecutor.place_buy_order()
10. Order → Portfolio.add_position()
11. Every tick → OptionsRiskManager.process_tick()
12. If target/SL hit → Callback → main._execute_exit()
13. Exit → DryRunOrderExecutor.place_sell_order()
14. Exit → Portfolio.close_position() → Calculate P&L
15. Log trade → CSV file
```

---

## 🐛 **CRITICAL BUG TO FIX**

**Location:** `core/options/options_breakout.py` line 106

**Current Code:**
```python
self.on_breakout_callback(option_type, breakout_price, marked_candle)
```

**Expected by main.py:**
```python
def on_options_breakout(direction, strike, option_type, entry_price):
```

**Fix Required:**
1. Fetch ATM strike from OptionsChainManager
2. Determine direction (BULLISH/BEARISH)
3. Pass correct parameters: `(direction, strike, option_type, entry_price)`

---

## 📊 **Configuration (Dry-Run Mode)**

**File:** `config/settings_options.py`

```python
OPTIONS_ENABLED = True
OPTIONS_DRY_RUN_MODE = True  # ← DRY-RUN MODE
OPTIONS_VOLUME_MULTIPLIER = 1.5
OPTIONS_QUANTITY = 50
OPTIONS_TARGET_PERCENT = 20  # 20% target
OPTIONS_MAX_TRADES_PER_DAY = 5
OPTIONS_EXCHANGE = "NFO"
OPTIONS_PRODUCT_TYPE = "NRML"
OPTIONS_ORDER_TYPE = "MARKET"
```

---

## ✅ **Dry-Run vs Live Mode Differences**

| Feature | Dry-Run Mode | Live Mode |
|---------|--------------|-----------|
| Order Executor | `DryRunOrderExecutor` | `LiveOrderExecutor` |
| Order Placement | Simulated (instant) | Real API call to Zerodha |
| Execution Price | Uses current LTP from ticks | Actual market execution |
| Order ID | UUID (fake) | Real Zerodha order ID |
| Risk | Zero (no real money) | Real money at stake |
| Logging | Same CSV format | Same CSV format |

**Switch Mode:** Change `OPTIONS_DRY_RUN_MODE` in `config/settings_options.py`

---

**End of Trace Document**
