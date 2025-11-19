# 9:15 Breakout Trading System

Ultra-low-latency automated trading system for NSE equity breakout strategies. Optimized for millisecond-level execution with equal capital distribution across marked stocks.

## 🎯 System Overview

This system implements a **first-minute breakout strategy** that:

- Analyzes the 9:15-9:16 AM candle for all configured stocks
- Marks stocks meeting volume and range criteria
- Distributes capital equally among marked stocks
- Executes breakout trades when price crosses 9:15 candle high
- Manages risk with dynamic stop-loss at breakout candle's open price

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        MAIN ORCHESTRATOR                     │
│  (Coordinates all modules, manages system lifecycle)         │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼─────┐
│ KITE   │      │ CONFIG   │
│ CONNECT│      │ MANAGER  │
└───┬────┘      └──────────┘
    │
    ├─────────────────────────────────────────────────────────┐
    │                                                           │
┌───▼──────────────┐  ┌──────────────────┐  ┌────────────────▼┐
│ SYMBOL MANAGER   │  │ HISTORICAL DATA  │  │ WEBSOCKET        │
│ - Token mapping  │  │ - 14-day avg     │  │ - Live ticks     │
│ - Symbol lookup  │  │ - Volume/Range   │  │ - Reconnection   │
└───┬──────────────┘  └────┬─────────────┘  └────┬─────────────┘
    │                      │                      │
    │                      │                      │
┌───▼──────────────┐  ┌───▼─────────────┐  ┌────▼─────────────┐
│ CANDLE BUILDER   │  │ STOCK MARKER     │  │ TICK ROUTER      │
│ - 1-min candles  │  │ - Mark 9:15      │  │ - Route to       │
│ - Real-time OHLC │  │ - Filter stocks  │  │   modules        │
└───┬──────────────┘  └───┬─────────────┘  └────┬─────────────┘
    │                     │                      │
    └─────────┬───────────┴──────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼─────────────┐  ┌─▼──────────────┐
│ BREAKOUT ENGINE │  │ RISK MANAGER   │
│ - Detect break  │  │ - Stop-loss    │
│ - Equal capital │  │ - Position size│
└───┬─────────────┘  └─┬──────────────┘
    │                  │
    └────────┬─────────┘
             │
    ┌────────▼────────┐
    │ ORDER EXECUTOR  │
    │ - Live/Dry-run  │
    │ - Entry/Exit    │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │ PORTFOLIO       │
    │ - Positions     │
    │ - PNL tracking  │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │ TRADE LOGGER    │
    │ - CSV logging   │
    │ - Audit trail   │
    └─────────────────┘
```

## 📁 Project Structure

```
9_15_breakout_system/
├── main.py                      # Main orchestrator
├── config/
│   ├── settings.py             # System configuration
│   ├── secrets.env             # API credentials
│   ├── token_generator.py      # Access token generator
│   └── symbols.csv             # Trading universe
├── core/
│   ├── symbols.py              # Symbol management
│   ├── historical.py           # Historical data fetching
│   ├── candles.py              # 1-minute candle builder
│   ├── marker.py               # Stock marking logic
│   ├── breakout.py             # Breakout detection
│   ├── risk.py                 # Risk management
│   ├── portfolio.py            # Position tracking
│   ├── orders_live.py          # Live order execution
│   ├── orders_dryrun.py        # Simulated orders
│   ├── trade_logger.py         # Trade logging
│   └── utils.py                # Utility functions
├── websocket/
│   ├── ws_manager.py           # WebSocket connection
│   └── tick_router.py          # Tick distribution
├── data/
│   └── trades/                 # Trade logs
└── README.md
```

## 🚀 Features

### Core Capabilities

- ✅ **Equal Capital Distribution**: Capital divided equally among all marked stocks
- ✅ **Dynamic Position Sizing**: Quantity calculated based on allocated capital per stock
- ✅ **Dual-Mode Operation**: Live trading and dry-run testing
- ✅ **Ultra-Low Latency**: Tick-by-tick processing with minimal overhead
- ✅ **Automatic Token Refresh**: Generate Zerodha access tokens
- ✅ **Historical Analysis**: 14-day volume and range averages
- ✅ **Real-time Monitoring**: WebSocket-based live data feed
- ✅ **Risk Management**: Stop-loss at breakout candle open
- ✅ **Trade Logging**: Complete audit trail in CSV format

### Stock Selection Criteria (9:15-9:16 AM)

1. **Volume Filter**: Current volume ≥ (14-day avg × multiplier)
2. **Range Filter**: Current range % ≥ 14-day avg range %
3. **Equal Capital**: Total capital / Number of marked stocks

### Entry Logic

- **Trigger**: Price crosses above 9:15 candle high
- **Entry Price**: Market price at breakout
- **Stop Loss**: Open price of the breakout candle
- **Position Size**: (Capital per stock) / Entry price

### Exit Logic

- **Stop Loss Hit**: Price ≤ Stop loss level
- **Manual Exit**: User intervention (if needed)

## 📋 Prerequisites

- Python 3.8+
- Zerodha Kite Connect account
- Active trading account with API access

## 🔧 Installation

1. **Clone the repository**

```bash
cd c:\Users\91948\OneDrive\Desktop
# System is already in: 9_15_breakout_system
```

2. **Install dependencies**

```bash
pip install kiteconnect python-dotenv numpy
```

3. **Configure API credentials**

   - Edit `config/secrets.env`:

   ```env
   API_KEY=your_api_key
   API_SECRET=your_api_secret
   ACCESS_TOKEN=your_access_token
   ```

4. **Generate access token**

```bash
python config/token_generator.py
```

5. **Configure symbols**

   - Edit `config/symbols.csv` with your trading universe

   ```csv
   symbol
   RELIANCE
   TCS
   INFY
   ```

6. **Adjust settings**
   - Edit `config/settings.py` for capital, risk parameters, etc.

## 🎮 Usage

### Basic Operation

```bash
# Run the system (will fetch historical data and wait for market open)
python main.py
```

### System Workflow

1. **Pre-Market (Before 9:15 AM)**

   - Fetches 14-day historical data
   - Calculates average volumes and ranges
   - Waits for market open

2. **9:15-9:16 AM**

   - Builds first-minute candle for all symbols
   - Evaluates and marks qualifying stocks
   - Distributes capital equally among marked stocks

3. **Post 9:16 AM**

   - Monitors marked stocks for breakout
   - Executes entries when price crosses 9:15 high
   - Sets stop-loss at breakout candle's open
   - Manages positions with real-time risk monitoring

4. **Position Management**
   - Tracks all open positions
   - Monitors stop-loss levels tick-by-tick
   - Executes exits on stop-loss hit
   - Logs all trades to CSV

## ⚙️ Configuration

### Key Settings (config/settings.py)

```python
# Capital Management
TOTAL_CAPITAL = 100000          # Total capital
MAX_TRADES_PER_DAY = 5          # Maximum concurrent positions

# Marking Criteria
VOLUME_MULTIPLIER = 1.5         # Volume must be 1.5x 14-day avg
# Range must exceed 14-day avg

# Risk Management
MAX_LOSS_PER_DAY = 2000        # Max daily loss limit

# Execution
DRY_RUN_MODE = True            # True = Paper trading, False = Live
ORDER_TYPE = "MARKET"          # Market orders
PRODUCT_TYPE = "MIS"           # Intraday
```

## 📊 Example Trade Flow

```
1. Market opens at 9:15 AM
2. System analyzes first minute (9:15-9:16)

   Stock: RELIANCE
   - 9:15 Open: 2500, High: 2520, Low: 2495, Close: 2515
   - Volume: 150,000 (14-day avg: 100,000)
   - Range: 1.0% (14-day avg: 0.8%)
   ✅ MARKED (meets criteria)

   Stock: TCS
   - Volume too low
   ❌ NOT MARKED

3. Capital Distribution
   - 3 stocks marked: RELIANCE, INFY, HDFCBANK
   - Capital per stock: ₹100,000 / 3 = ₹33,333

4. Breakout Detection
   - RELIANCE crosses 2520 at 9:25 AM
   - Entry: ₹2522 (market price)
   - Quantity: 33,333 / 2522 = 13 shares
   - Stop Loss: ₹2518 (9:25 candle open)

5. Exit
   - Stop loss hit at ₹2518
   - Exit executed
   - Loss: (2522 - 2518) × 13 = ₹52
```

## 📈 Performance Monitoring

The system provides real-time statistics:

```
=============================================================
SYSTEM STATISTICS
=============================================================
Capital: ₹100,000.00 | PNL: ₹+1,250.00
Trades: 3 | Active: 1
Win Rate: 66.7%
Marked: 5/50
Breakouts: 3
```

## 🔍 Trade Logs

All trades are logged to CSV files in `data/trades/`:

```csv
timestamp,symbol,side,quantity,price,order_id,pnl,reason
2024-01-15 09:25:30,RELIANCE,BUY,13,2522.00,123456,,
2024-01-15 10:45:15,RELIANCE,SELL,13,2518.00,123457,-52.00,STOP_LOSS
```

## 🛡️ Risk Management

- **Position Sizing**: Equal capital distribution prevents over-concentration
- **Stop Loss**: Automatic exit at breakout candle open
- **Max Loss**: System stops trading if daily loss exceeds limit
- **Max Positions**: Limits concurrent trades

## ⚠️ Important Notes

1. **Market Timing**: Run before 9:15 AM to fetch historical data
2. **API Rate Limits**: Historical data fetch respects Zerodha limits (3 req/sec)
3. **WebSocket**: Auto-reconnects on disconnection
4. **Dry-Run Testing**: Always test in dry-run mode first
5. **Capital Management**: Ensure sufficient funds for all potential entries

## 🐛 Troubleshooting

### Common Issues

**WebSocket disconnects**

- System auto-reconnects
- Check internet connectivity

**No stocks marked**

- Lower VOLUME_MULTIPLIER in settings
- Check if symbols.csv has valid symbols

**Orders not executing**

- Verify DRY_RUN_MODE setting
- Check Zerodha account status
- Verify ACCESS_TOKEN is valid

**Historical data errors**

- Run token_generator.py to refresh token
- Check symbols.csv format
- Verify API credentials

## 📝 License

This is a personal trading system. Use at your own risk.

## ⚠️ Disclaimer

**This system is for educational purposes only. Trading involves substantial risk.**

- Past performance does not guarantee future results
- Always test thoroughly in dry-run mode
- Start with small capital
- Monitor system performance closely
- Understand all risks before live trading

---

**Built with**: Python, Kite Connect API, WebSocket
**Optimized for**: Ultra-low latency, Real-time execution
