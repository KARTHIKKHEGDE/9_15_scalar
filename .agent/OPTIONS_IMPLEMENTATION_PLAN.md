# 🎯 Options Trading System - Implementation Plan

## 📋 Requirements

### **New Feature: NIFTY Futures-based Options Trading**

1. **Track NIFTY FUT (nearest month)** - Build 1-minute candles
2. **Volume-based marking** - If candle volume ≥ current_volume × multiplier → Mark candle (with direction: red/green)
3. **Breakout detection:**
   - **Red candle marked** → Future candle crosses LOW → Buy ATM PUT
   - **Green candle marked** → Future candle crosses HIGH → Buy ATM CALL
4. **Trade parameters:**
   - Quantity: X (configurable)
   - Target: Y% (configurable)
   - Stop-loss: Opening price of breakout candle

---

## 🏗️ File Structure

```
9_15_breakout_system/
├── config/
│   ├── settings.py (UPDATE - Add options config)
│   └── options_symbols.csv (NEW - NIFTY FUT symbol)
│
├── core/
│   ├── candles.py (REUSE - Same candle builder)
│   ├── options/
│   │   ├── __init__.py (NEW)
│   │   ├── options_marker.py (NEW - Mark NIFTY FUT candles)
│   │   ├── options_breakout.py (NEW - Detect breakouts)
│   │   ├── options_chain.py (NEW - Get ATM strike)
│   │   └── options_risk.py (NEW - Manage options positions)
│   │
│   └── ... (existing files)
│
├── main_options.py (NEW - Options trading orchestrator)
└── ... (existing files)
```

---

## 🔄 Reusable Components

### **From Existing System:**

1. **`CandleBuilder`** - Reuse for NIFTY FUT candles
2. **`Portfolio`** - Reuse for options positions
3. **`WebSocketManager`** - Reuse for NIFTY FUT ticks
4. **`TickRouter`** - Reuse for tick routing
5. **`TradeLogger`** - Reuse for logging options trades
6. **`OrderExecutor`** - Reuse for placing options orders

### **New Components:**

1. **`OptionsMarker`** - Mark NIFTY FUT candles based on volume
2. **`OptionsBreakoutEngine`** - Detect breakouts and determine CALL/PUT
3. **`OptionsChainManager`** - Get ATM strike prices
4. **`OptionsRiskManager`** - Manage options-specific risk (% target, opening SL)

---

## 📝 Implementation Steps

### **Step 1: Configuration (settings.py)**
```python
# Add options-specific config
OPTIONS_ENABLED = True
OPTIONS_NIFTY_FUT_SYMBOL = "NIFTY24DECFUT"  # Nearest month
OPTIONS_VOLUME_MULTIPLIER = 1.5
OPTIONS_QUANTITY = 50  # Lot size
OPTIONS_TARGET_PERCENT = 20  # 20% target
OPTIONS_MAX_TRADES_PER_DAY = 5
```

### **Step 2: Options Marker (options_marker.py)**
- Similar to `StockMarker`
- Mark candles based on volume multiplier
- Track candle direction (red/green)
- Store marked candle with direction

### **Step 3: Options Breakout Engine (options_breakout.py)**
- Similar to `BreakoutEngine`
- Monitor marked candles for breakouts
- **Red candle** → Check if price crosses LOW → Signal PUT
- **Green candle** → Check if price crosses HIGH → Signal CALL
- Fire callback with: `(direction, strike, entry_price, stoploss)`

### **Step 4: Options Chain Manager (options_chain.py)**
- Get current NIFTY FUT price
- Calculate ATM strike (round to nearest 50)
- Return option symbol (e.g., "NIFTY24DEC20000PE" or "NIFTY24DEC20000CE")

### **Step 5: Options Risk Manager (options_risk.py)**
- Calculate target based on % (not 2x risk)
- Stop-loss = Opening price of breakout candle
- Monitor positions for target/SL hit

### **Step 6: Main Orchestrator (main_options.py)**
- Initialize all modules
- Setup callbacks
- Start trading

---

## 🎯 Detailed Logic Flow

### **Marking Logic:**

```python
# In OptionsMarker
def evaluate_and_mark(self, candle: Candle):
    # Check volume condition
    if candle.volume >= current_volume * OPTIONS_VOLUME_MULTIPLIER:
        # Determine direction
        direction = "RED" if candle.close < candle.open else "GREEN"
        
        # Mark candle
        self.marked_candles[candle.timestamp] = {
            "candle": candle,
            "direction": direction,
            "high": candle.high,
            "low": candle.low
        }
```

### **Breakout Logic:**

```python
# In OptionsBreakoutEngine
def process_tick(self, tick: dict):
    price = tick["last_price"]
    
    for timestamp, marked_data in self.marked_candles.items():
        direction = marked_data["direction"]
        
        if direction == "RED":
            # Check if price crossed LOW
            if price < marked_data["low"]:
                # Breakout! Buy PUT
                self._trigger_breakout("PUT", price, marked_data)
        
        elif direction == "GREEN":
            # Check if price crossed HIGH
            if price > marked_data["high"]:
                # Breakout! Buy CALL
                self._trigger_breakout("CALL", price, marked_data)
```

### **Entry Logic:**

```python
# In main_options.py
def on_breakout(self, option_type, fut_price, breakout_candle):
    # Get ATM strike
    atm_strike = self.options_chain.get_atm_strike(fut_price)
    
    # Get option symbol
    option_symbol = self.options_chain.get_option_symbol(
        atm_strike, 
        option_type  # "CE" or "PE"
    )
    
    # Calculate stop-loss (opening of breakout candle)
    stoploss = breakout_candle.open
    
    # Place order
    self._execute_entry(option_symbol, OPTIONS_QUANTITY, stoploss)
```

### **Exit Logic:**

```python
# In OptionsRiskManager
def process_tick(self, tick: dict):
    # Update position price
    position = self.portfolio.get_position(symbol)
    
    # Calculate target (% based)
    target = position.entry_price * (1 + OPTIONS_TARGET_PERCENT / 100)
    
    # Check target
    if price >= target:
        self.on_exit_callback(symbol, price, "Target Hit")
    
    # Check stop-loss (opening of breakout candle)
    if price <= position.stoploss:
        self.on_exit_callback(symbol, price, "Stop-Loss Hit")
```

---

## 🔧 Configuration Example

```python
# config/settings.py

# ============================================
# OPTIONS TRADING PARAMETERS
# ============================================
OPTIONS_ENABLED = True
OPTIONS_NIFTY_FUT_SYMBOL = "NIFTY24DECFUT"
OPTIONS_VOLUME_MULTIPLIER = 1.5  # Mark if volume >= current * 1.5
OPTIONS_QUANTITY = 50  # Lot size (50 for NIFTY)
OPTIONS_TARGET_PERCENT = 20  # 20% target
OPTIONS_MAX_TRADES_PER_DAY = 5
OPTIONS_EXCHANGE = "NFO"  # Options exchange
```

---

## 📊 Data Flow

```
NIFTY FUT Tick
    ↓
CandleBuilder (reused)
    ↓
1-Minute Candle
    ↓
OptionsMarker
    ↓
Mark if volume >= current * multiplier
    ↓
Store with direction (RED/GREEN)
    ↓
OptionsBreakoutEngine
    ↓
Monitor for breakout
    ↓
RED → Price crosses LOW → Signal PUT
GREEN → Price crosses HIGH → Signal CALL
    ↓
OptionsChainManager
    ↓
Get ATM strike
    ↓
main_options.py
    ↓
Execute entry (Buy CALL/PUT)
    ↓
OptionsRiskManager
    ↓
Monitor for target (%) or SL (opening price)
    ↓
Execute exit
```

---

## ✅ Implementation Checklist

- [ ] Update `config/settings.py` with options parameters
- [ ] Create `core/options/__init__.py`
- [ ] Create `core/options/options_marker.py`
- [ ] Create `core/options/options_breakout.py`
- [ ] Create `core/options/options_chain.py`
- [ ] Create `core/options/options_risk.py`
- [ ] Create `main_options.py`
- [ ] Test with dry-run mode
- [ ] Integrate with existing system

---

**Ready to implement?** Let me know and I'll start building! 🚀
