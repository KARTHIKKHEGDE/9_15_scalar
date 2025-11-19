# 9:15 Breakout Trading System

**Ultra-low-latency algorithmic trading system** for detecting and executing breakout trades based on the first candle (9:15-9:16 AM) of the Indian stock market.

## 🎯 Strategy Overview

1. **Pre-Market (Before 9:15 AM)**: Fetch 14-day average volume/range for all symbols
2. **9:15-9:16 AM**: Monitor first 1-minute candle formation
3. **9:16 AM**: Mark symbols that qualify (high volume + good range)
4. **After 9:16 AM**: Monitor marked symbols for breakout above 9:15 candle high
5. **Entry**: When price breaks above high (with buffer)
6. **Stop-Loss**: 9:15 candle open/low

## ⚡ Performance Optimizations

- **Zero-copy tick processing** with in-memory data structures
- **O(1) lookups** using hashmaps for symbols, tokens, and positions
- **Single-threaded tick routing** (no context switching overhead)
- **Parallel historical data fetching** (10 concurrent threads)
- **WebSocket streaming** for real-time ticks (no polling)
- **Instant breakout detection** on every tick
- **Pre-calculated thresholds** before market opens

## 📁 Project Structure

```
9_15_breakout_system/
│
├── config/
│   ├── settings.py              # Strategy parameters, risk settings
│   └── secrets.env              # Zerodha API credentials
│
├── core/
│   ├── symbols.py               # Symbol/token management (O(1) lookups)
│   ├── historical.py            # 14-day data fetcher (parallel)
│   ├── candles.py               # 1-min candle builder (real-time)
│   ├── marker.py                # Qualify stocks at 9:15 close
│   ├── breakout.py              # Breakout detection engine
│   ├── risk.py                  # Stop-loss & position sizing
│   ├── orders_live.py           # Live order execution (Zerodha)
│   ├── orders_dryrun.py         # Paper trading simulator
│   ├── trade_logger.py          # CSV trade logging
│   ├── portfolio.py             # Position & PNL tracking
│   └── utils.py                 # Helper functions
│
├── websocket/
│   ├── tick_router.py           # Route ticks to engines
│   └── ws_manager.py            # WebSocket connection manager
│
├── main.py                      # Central orchestrator
├── symbols.csv                  # Symbols to trade
│
└── output/
    ├── trades_YYYYMMDD.csv     # Daily trade logs
    └── logs/                    # System logs
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install kiteconnect python-dotenv numpy
```

### 2. Setup Credentials

Copy the template and add your Zerodha credentials:

```bash
cp config/secrets.env.template config/secrets.env
```

Edit `config/secrets.env`:
```bash
API_KEY=your_api_key
API_SECRET=your_api_secret
ACCESS_TOKEN=your_access_token
```

### 3. Configure Strategy

Edit `config/settings.py`:

```python
# Capital & Risk
TOTAL_CAPITAL = 100000
RISK_PER_TRADE_PERCENT = 1.0
MAX_TRADES_PER_DAY = 5

# Strategy Parameters
VOLUME_MULTIPLIER = 2.0          # Volume must be 2x of 14-day avg
MIN_CANDLE_RANGE_PERCENT = 0.5   # Minimum 0.5% range
BREAKOUT_BUFFER_PERCENT = 0.05   # 0.05% buffer above high

# Trading Mode
DRY_RUN_MODE = True              # Set False for live trading
```

### 4. Add Symbols

Edit `symbols.csv`:
```csv
symbol
RELIANCE
TCS
INFY
HDFCBANK
```

### 5. Run System

**Run before 9:15 AM** to fetch historical data:

```bash
python main.py
```

The system will:
1. Fetch 14-day historical data
2. Wait until 9:15 AM
3. Start monitoring live ticks
4. Execute trades automatically

## 📊 How It Works

### Phase 1: Pre-Market (Before 9:15)
```
[main.py] → [historical.py] → Fetch 14-day data for all symbols (parallel)
                            → Calculate average volume & range
                            → Store in memory for O(1) access
```

### Phase 2: Market Open (9:15 onwards)
```
[WebSocket] → Receive ticks
    ↓
[tick_router.py] → Route to engines
    ↓
    ├─→ [candles.py] → Build 1-min candles
    │       ↓
    │   (On 9:16 candle close)
    │       ↓
    │   [marker.py] → Check volume & range
    │       ↓
    │   (If qualified) → MARK SYMBOL
    │
    ├─→ [breakout.py] → Monitor marked symbols
    │       ↓
    │   (Price > High?) → TRIGGER ENTRY
    │       ↓
    │   [orders_*.py] → Place BUY order
    │       ↓
    │   [portfolio.py] → Track position
    │
    └─→ [risk.py] → Monitor positions
            ↓
        (Price < SL?) → TRIGGER EXIT
            ↓
        [orders_*.py] → Place SELL order
```

## 🎛️ Configuration Options

### Risk Management
```python
RISK_PER_TRADE_PERCENT = 1.0     # Risk 1% capital per trade
MAX_LOSS_PER_DAY = 5000           # Stop trading if loss > 5000
TRAILING_SL_PERCENT = None        # Set to % for trailing SL
```

### Entry Criteria
```python
VOLUME_MULTIPLIER = 2.0           # 2x volume of 14-day avg
MIN_CANDLE_RANGE_PERCENT = 0.5    # 0.5% minimum range
BREAKOUT_BUFFER_PERCENT = 0.05    # Buffer to avoid false breakouts
```

### Order Execution
```python
ORDER_TYPE = "MARKET"             # MARKET or LIMIT
PRODUCT_TYPE = "MIS"              # MIS or NRML
SLIPPAGE_PERCENT = 0.1            # Slippage for dry-run
```

## 📈 Trade Logging

All trades are logged to `output/trades_YYYYMMDD.csv`:

```csv
timestamp,symbol,action,quantity,price,value,pnl,pnl_percent,reason,order_id
2025-01-15 09:16:23,RELIANCE,BUY,50,2450.30,122515.00,0,0,BREAKOUT,abc123
2025-01-15 09:45:12,RELIANCE,SELL,50,2475.80,123790.00,1275.00,1.04,STOP_LOSS,def456
```

## 🔧 Advanced Features

### Dry-Run Mode (Paper Trading)

Perfect for testing with **realistic simulations**:
- Slippage modeling
- Order execution delays
- Real-time PNL tracking

```python
DRY_RUN_MODE = True  # in settings.py
```

### Live Trading

```python
DRY_RUN_MODE = False  # Switch to live
```

### Performance Monitoring

```python
from core.utils import perf_monitor

# System tracks:
# - Tick processing latency
# - Candle building speed
# - Order execution time
```

## ⚠️ Important Notes

### Latency Considerations

1. **Network Latency**: 10-50ms (depends on ISP)
2. **Tick Processing**: <1ms (in-memory operations)
3. **Order Execution**: 50-200ms (Zerodha API)
4. **Total Entry Latency**: ~100-300ms from breakout detection

### Risk Warnings

- Test thoroughly in **DRY-RUN mode** before live trading
- Markets can be volatile, especially in first few minutes
- Always use stop-losses
- Never risk more than you can afford to lose
- Past performance doesn't guarantee future results

### Best Practices

1. **Run before 9:15 AM** to fetch historical data
2. **Monitor first few days** in dry-run mode
3. **Check internet connection** stability
4. **Keep capital limits** reasonable
5. **Review trades daily** in CSV logs

## 🐛 Troubleshooting

### "Symbol not found in NSE instruments"
- Check symbol spelling in `symbols.csv`
- Use exact NSE trading symbols (e.g., "HDFCBANK" not "HDFC BANK")

### "WebSocket connection failed"
- Check internet connectivity
- Verify API credentials in `secrets.env`
- Ensure access token is valid (generate new if expired)

### "No historical data available"
- Zerodha API may have rate limits
- Reduce number of symbols
- Increase `max_workers` parameter

### Orders not executing
- Check if DRY_RUN_MODE is correct
- Verify sufficient capital
- Check market hours (9:15-15:30)

## 📞 Support

For issues related to:
- **Zerodha API**: https://kite.trade/docs
- **KiteConnect Library**: https://github.com/zerodhatech/pykiteconnect

## 📄 License

This is educational software for learning algorithmic trading. Use at your own risk.

---

**Built for speed. Optimized for performance. Ready for breakouts.** ⚡🚀