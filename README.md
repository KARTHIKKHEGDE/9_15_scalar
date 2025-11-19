# 9:15 Breakout Trading System

Ultra-low-latency breakout trading system for Indian equity markets.

## 🎯 Strategy Overview

### Entry Logic

1. **Pre-Market Analysis** (Before 9:15 AM)

   - Fetch 14-day historical data for all symbols
   - Calculate average volume and range for each symbol

2. **9:15 AM Candle Evaluation**
   - Wait for first 1-minute candle (9:15-9:16 AM)
   - Mark symbols that meet criteria:
     - Volume > 2x 14-day average
     - Range > 0.5% AND > 14-day average range
3. **Breakout Detection**
   - Monitor marked symbols in real-time
   - Entry when price crosses 9:15 candle high
   - Buffer: 0.1% above high to avoid false breakouts

### Stop-Loss Logic (Enhanced)

- **Primary**: Breakout candle's **open price**
  - Uses the open of the candle where breakout occurs
  - More dynamic, adapts to current market conditions
- **Fallback**: 9:15 candle's open price
  - Used when:
    - No active candle data available
    - Candle open = 0 (data issue)
    - Symbol not found in candle builder
- **Thread-Safe**: Uses existing lock mechanism in CandleBuilder

### Exit Logic

- Stop-loss hit
- Target hit (Risk:Reward based)
- Trailing stop-loss (optional)
- Market close (3:25 PM - square off all positions)
- Max loss per day reached

## 📊 Position Sizing

- Risk per trade: 1% of capital
- Position size = (Capital × Risk%) / (Entry - Stoploss)
- Automatic lot size calculation

## 🏗️ Architecture

### Core Modules

#### 1. Symbol Manager (`core/symbols.py`)

- Loads symbols from CSV
- Maps symbols to instrument tokens
- O(1) token lookups

#### 2. Historical Data Manager (`core/historical.py`)

- Fetches 14-day historical data
- Calculates average volume and range
- Single-threaded with rate limiting

#### 3. Candle Builder (`core/candles.py`)

- Builds 1-minute candles from ticks
- Detects candle closes
- **Stores current candle open for stop-loss calculation**
- Thread-safe implementation
- Triggers callbacks on candle close

#### 4. Stock Marker (`core/marker.py`)

- Evaluates 9:15 candle against criteria
- Marks qualified symbols for monitoring
- Stores 9:15 candle data as fallback
- O(1) mark/unmark operations

#### 5. Breakout Engine (`core/breakout.py`)

- Monitors marked symbols for breakout
- **Uses breakout candle open as stop-loss**
- **Falls back to 9:15 candle open if needed**
- Ultra-low-latency execution (<10ms)
- Prevents duplicate entries

#### 6. Risk Manager (`core/risk.py`)

- Calculates position sizes
- Monitors stop-loss and targets
- Implements trailing stop-loss
- Tracks daily loss limits

#### 7. Portfolio (`core/portfolio.py`)

- Tracks all active positions
- Calculates real-time PNL
- Maintains trade statistics
- Thread-safe operations

#### 8. Order Executor (`core/orders_*.py`)

- **Live Mode**: Real order placement via Zerodha Kite
- **Dry-Run Mode**: Simulated execution for testing
- Order status tracking

#### 9. WebSocket Manager (`websocket/ws_manager.py`)

- Real-time tick data streaming
- Auto-reconnection logic
- Subscription management

#### 10. Tick Router (`websocket/tick_router.py`)

- Routes ticks to appropriate modules:
  - Candle Builder (all ticks)
  - Breakout Engine (marked symbols only)
  - Risk Manager (active positions only)

### Data Flow

```
WebSocket Ticks
    ↓
Tick Router
    ↓
    ├─→ Candle Builder → (stores current candle open)
    │       ↓
    │   Candle Close Event
    │       ↓
    │   Stock Marker (evaluates & marks)
    │       ↓
    ├─→ Breakout Engine (monitors marked symbols)
    │       ↓
    │   Breakout Detected
    │       ↓
    │   Entry Execution (uses breakout candle open as SL)
    │       ↓
    │   Portfolio Updated
    │       ↓
    └─→ Risk Manager (monitors active positions)
            ↓
        Exit Triggered
            ↓
        Exit Execution
```

### Stop-Loss Calculation Flow

```
Breakout Detected
    ↓
Get Breakout Candle Open from CandleBuilder
    ↓
    ├─ Available? → Use as Stop-Loss ✓
    │
    └─ Not Available? → Fallback to 9:15 Candle Open
            ↓
        Warning Logged
```

## 🚀 Performance Optimizations

1. **O(1) Lookups**

   - Token-to-symbol mappings
   - Symbol-to-token mappings
   - Marked symbols tracking

2. **Minimal Latency**

   - Direct tick processing (no queues)
   - Selective routing (only relevant modules)
   - Fast breakout detection (<10ms)

3. **Thread Safety**

   - Locks only where necessary
   - Lock-free reads where possible
   - Atomic operations for critical sections

4. **Memory Efficient**
   - In-memory candle storage (cleared after close)
   - Efficient tick data structures
   - Minimal historical data retention

## 📁 Project Structure

```
9_15_breakout_system/
├── config/
│   ├── settings.py          # All configuration parameters
│   ├── secrets.env          # API credentials (gitignored)
│   └── token_generator.py   # Helper to generate access tokens
│
├── core/
│   ├── symbols.py           # Symbol management
│   ├── historical.py        # Historical data fetching
│   ├── candles.py          # Real-time candle building
│   ├── marker.py           # Stock marking logic
│   ├── breakout.py         # Breakout detection & execution
│   ├── risk.py             # Risk management
│   ├── portfolio.py        # Position tracking
│   ├── orders_live.py      # Live order execution
│   ├── orders_dryrun.py    # Simulated execution
│   ├── trade_logger.py     # CSV logging
│   └── utils.py            # Utility functions
│
├── websocket/
│   ├── ws_manager.py       # WebSocket connection manager
│   └── tick_router.py      # Tick routing logic
│
├── data/
│   ├── symbols.csv         # List of symbols to trade
│   └── trades/             # Trade logs (generated)
│
├── main.py                 # Main orchestrator
└── README.md              # This file
```

## 🔧 Configuration

Edit `config/settings.py` to customize:

```python
# Capital & Risk
TOTAL_CAPITAL = 100000
RISK_PER_TRADE_PERCENT = 1.0
MAX_TRADES_PER_DAY = 5
MAX_LOSS_PER_DAY = 3000

# Entry Criteria
VOLUME_MULTIPLIER = 2.0
MIN_CANDLE_RANGE_PERCENT = 0.5
BREAKOUT_BUFFER_PERCENT = 0.1

# Execution
DRY_RUN_MODE = True  # Set False for live trading
ORDER_TYPE = "MARKET"
PRODUCT_TYPE = "MIS"  # Intraday
```

## 📝 Usage

### 1. Setup

```bash
# Install dependencies
pip install kiteconnect pandas numpy python-dotenv

# Configure credentials in config/secrets.env
API_KEY=your_api_key
API_SECRET=your_api_secret
ACCESS_TOKEN=your_access_token
```

### 2. Generate Access Token (Daily)

```bash
python config/token_generator.py
```

### 3. Run System

```bash
# Dry-run mode (recommended for testing)
python main.py

# Live trading (change DRY_RUN_MODE = False in settings.py)
python main.py
```

### 4. Monitor

- Logs show real-time events
- Trade logs saved in `data/trades/`
- System statistics printed periodically

## ⚠️ Risk Warnings

1. **Market Risk**: Past performance doesn't guarantee future results
2. **Execution Risk**: Slippage and partial fills possible
3. **Technical Risk**: Internet/API failures can occur
4. **Capital Risk**: Only trade with capital you can afford to lose
5. **Testing**: Always test in DRY_RUN mode first

## 📈 Future Enhancements

- [ ] Multi-timeframe analysis
- [ ] Machine learning for symbol selection
- [ ] Advanced order types (limit orders)
- [ ] Telegram notifications
- [ ] Web dashboard for monitoring
- [ ] Backtesting framework

## 📄 License

Private use only. Not for commercial distribution.

## 🙋 Support

For issues or questions, review the code documentation and logs first.

```

```
