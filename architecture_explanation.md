# 9:15 Breakout System - Architecture Explanation

## Core Design Pattern: Composition + Dependency Injection

### Object Creation Flow

```python
# 1. main.py creates ALL objects
system = TradingSystem()
    ├─ symbol_manager = SymbolManager(kite)
    ├─ historical_manager = HistoricalDataManager(kite, symbol_manager)
    ├─ candle_builder = CandleBuilder(symbol_manager)
    ├─ portfolio = Portfolio(capital)
    ├─ marker = StockMarker(historical_manager, config)
    ├─ breakout_engine = BreakoutEngine(marker, symbol_manager, config)
    ├─ risk_manager = RiskManager(portfolio, symbol_manager, config)
    ├─ order_executor = LiveOrderExecutor(kite, symbol_manager, config)
    ├─ trade_logger = TradeLogger(config)
    ├─ tick_router = TickRouter(candle_builder, breakout_engine, risk_manager)
    └─ ws_manager = WebSocketManager(api_key, access_token, config)
```

### Communication Pattern: Callbacks (Event-Driven)

Instead of objects directly calling each other, they communicate via **callbacks**:

```
WebSocket Tick → TickRouter → [CandleBuilder, BreakoutEngine, RiskManager]
                                      ↓                ↓              ↓
                              Candle Close      Breakout        Stop-Loss
                                      ↓                ↓              ↓
                                  Marker       Entry Execution  Exit Execution
```

## Example Flow

### 1. **Candle Close Event**

```python
# main.py sets up callback
def on_candle_close(candle):
    marker.evaluate_and_mark(candle)

candle_builder.set_on_candle_close_callback(on_candle_close)

# Later, when candle closes:
candle_builder → triggers → on_candle_close() → calls marker.evaluate_and_mark()
```

### 2. **Breakout Detection**

```python
# main.py sets up callback
def on_breakout(symbol, entry_price, stoploss):
    _execute_entry(symbol, entry_price, stoploss)

breakout_engine.set_on_breakout_callback(on_breakout)

# When breakout detected:
breakout_engine → triggers → on_breakout() → calls _execute_entry()
```

### 3. **Stop-Loss Hit**

```python
# main.py sets up callback
def on_exit(symbol, exit_price, reason):
    _execute_exit(symbol, exit_price, reason)

risk_manager.set_on_exit_callback(on_exit)

# When SL hit:
risk_manager → triggers → on_exit() → calls _execute_exit()
```

## Why This Design?

### ✅ Advantages

1. **Loose Coupling**

   - Each class is independent
   - Easy to test in isolation
   - Can swap implementations (e.g., DryRun ↔ Live)

2. **Single Responsibility**

   - `CandleBuilder` only builds candles
   - `Marker` only evaluates stocks
   - `BreakoutEngine` only detects breakouts

3. **Easy to Extend**

   ```python
   # Want to add email alerts? Just add a callback!
   def on_breakout(symbol, price, sl):
       _execute_entry(symbol, price, sl)
       email_service.send_alert(f"Breakout: {symbol}")
   ```

4. **Testability**
   ```python
   # Test CandleBuilder without WebSocket
   builder = CandleBuilder(mock_symbol_manager)
   builder.set_on_candle_close_callback(my_test_handler)
   builder.process_tick(mock_tick)
   ```

### ⚠️ Potential Issues

1. **Callback Hell**

   - Too many nested callbacks can be confusing
   - **Solution**: Keep callbacks simple, delegate to methods

2. **Debugging**

   - Event flow can be hard to trace
   - **Solution**: Add logging at each callback trigger

3. **Error Handling**
   - Errors in callbacks can crash the chain
   - **Solution**: Wrap callbacks in try-except (already done!)

## Alternative Patterns (Not Used Here)

### 1. **Direct Method Calls** (Tighter Coupling)

```python
# ❌ What you DIDN'T do
class BreakoutEngine:
    def __init__(self, order_executor, portfolio):
        self.order_executor = order_executor  # Direct dependency

    def process_tick(self, tick):
        if breakout_detected:
            self.order_executor.place_order()  # Direct call
            self.portfolio.add_position()      # Direct call
```

### 2. **Message Queue** (Over-engineered for this)

```python
# ❌ Overkill for this system
from queue import Queue

event_queue = Queue()
event_queue.put({"type": "BREAKOUT", "symbol": "RELIANCE"})
# Consumer processes events...
```

### 3. **Observer Pattern** (Similar to what you have)

```python
# ✅ Your callback pattern is basically this
class Observable:
    def __init__(self):
        self.observers = []

    def subscribe(self, observer):
        self.observers.append(observer)

    def notify(self, event):
        for observer in self.observers:
            observer.on_event(event)
```

## Your Implementation Strengths

1. ✅ **Clean separation** - Each file/class has ONE job
2. ✅ **No circular imports** - Proper dependency direction
3. ✅ **Thread-safe** - Using locks where needed
4. ✅ **Fast** - O(1) lookups everywhere
5. ✅ **Testable** - Can mock any component

## How Data Flows Through System

```
┌──────────────┐
│  WebSocket   │ ← Receives ticks from Zerodha
└──────┬───────┘
       │
       ↓
┌──────────────┐
│  TickRouter  │ ← Routes ticks to 3 modules
└──┬───┬───┬───┘
   │   │   │
   ↓   ↓   ↓
┌────┐┌────┐┌────┐
│Can││Brk││Rsk│ ← Process ticks in parallel
│dle││out││Mgr│
└─┬──┘└─┬──┘└─┬──┘
  │     │     │
  ↓     ↓     ↓
Candle  Entry Exit
Close   Order Order
  │       │     │
  ↓       ↓     ↓
Marker  Portfolio
```

## Summary

Your architecture is:

- ✅ **Event-driven** (callbacks)
- ✅ **Modular** (each class is independent)
- ✅ **Composable** (main.py assembles everything)
- ✅ **Professional-grade** (used in production systems)

This is exactly how trading systems SHOULD be built!
