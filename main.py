#!/usr/bin/env python3
"""
9:15 Breakout Trading System - Main Orchestrator
Ultra-low-latency execution with modular design
Run before 9:15 AM to prepare data
System automatically starts trading at 9:15 AM
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, time
import time as time_module
from kiteconnect import KiteConnect
from dotenv import load_dotenv
import os
import signal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import all modules
from config.settings import *
from core.symbols import SymbolManager
from core.historical import HistoricalDataManager
from core.candles import CandleBuilder
from core.marker import StockMarker
from core.breakout import BreakoutEngine
from core.risk import RiskManager
from core.portfolio import Portfolio
from core.orders_live import LiveOrderExecutor
from core.orders_dryrun import DryRunOrderExecutor
from core.trade_logger import TradeLogger
from websocket.ws_manager import WebSocketManager
from websocket.tick_router import TickRouter

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class TradingSystem:
    """
    Central orchestrator for 9:15 breakout system
    Coordinates all modules with minimal latency
    """
    
    def __init__(self):
        self.shutdown_requested = False
        logger.info("=" * 60)
        logger.info("9:15 BREAKOUT TRADING SYSTEM - INITIALIZING")
        logger.info("=" * 60)
        
        # Load environment variables
        load_dotenv('config/secrets.env')
        
        # Initialize Kite connection
        self.kite = self._initialize_kite()
        
        # Create config dictionary
        self.config = {
            'MAX_TRADES_PER_DAY': MAX_TRADES_PER_DAY,
            'TOTAL_CAPITAL': TOTAL_CAPITAL,
            'VOLUME_MULTIPLIER': VOLUME_MULTIPLIER,
            'BREAKOUT_BUFFER_PERCENT': BREAKOUT_BUFFER_PERCENT,
            'DRY_RUN_MODE': DRY_RUN_MODE,
            'ORDER_TYPE': ORDER_TYPE,
            'PRODUCT_TYPE': PRODUCT_TYPE,
            'EXCHANGE': EXCHANGE,
            'SLIPPAGE_PERCENT': SLIPPAGE_PERCENT,
            'MAX_LOSS_PER_DAY': MAX_LOSS_PER_DAY,
            'OUTPUT_DIR': OUTPUT_DIR,
            'TRADES_CSV_PREFIX': TRADES_CSV_PREFIX,
            'WS_RECONNECT_DELAY': WS_RECONNECT_DELAY,
            'WS_RECONNECT_MAX_TRIES': WS_RECONNECT_MAX_TRIES
        }
        
        # Initialize all modules
        self._initialize_modules()
        
        # Setup callbacks
        self._setup_callbacks()
        
        logger.info(f"Mode: {'DRY-RUN' if DRY_RUN_MODE else 'LIVE TRADING'}")
        logger.info(f"Capital: ₹{TOTAL_CAPITAL:,.2f}")
        logger.info(f"Max Trades: {MAX_TRADES_PER_DAY}")
    
    def _initialize_kite(self) -> KiteConnect:
        """Initialize Kite connection"""
        api_key = os.getenv('API_KEY')
        access_token = os.getenv('ACCESS_TOKEN')
        
        if not api_key or not access_token:
            logger.error("API_KEY or ACCESS_TOKEN not found in secrets.env")
            sys.exit(1)
        
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Test connection
        try:
            profile = kite.profile()
            logger.info(f"✓ Connected to Zerodha | User: {profile['user_name']}")
            return kite
        except Exception as e:
            logger.error(f"✗ Kite connection failed: {e}")
            sys.exit(1)
    
    def _initialize_modules(self):
        """Initialize all trading modules"""
        
        # 1. Symbol Management
        logger.info("Loading symbols...")
        self.symbol_manager = SymbolManager(self.kite)
        self.symbol_manager.load_symbols_from_csv(SYMBOLS_CSV_PATH)
        self.symbol_manager.map_tokens(EXCHANGE)
        
        # 2. Historical Data
        logger.info("Initializing historical data manager...")
        self.historical_manager = HistoricalDataManager(self.kite, self.symbol_manager)
        
        # 3. Candle Builder
        self.candle_builder = CandleBuilder(self.symbol_manager)
        
        # 4. Portfolio
        self.portfolio = Portfolio(TOTAL_CAPITAL)
        
        # 5. Stock Marker
        self.marker = StockMarker(self.historical_manager, self.config)
        
        # 6. Breakout Engine
        self.breakout_engine = BreakoutEngine(self.marker, self.symbol_manager, self.config, self.candle_builder)
        
        # 7. Risk Manager
        self.risk_manager = RiskManager(self.portfolio, self.symbol_manager, self.config, self.marker)
        
        # 8. Order Executor
        if DRY_RUN_MODE:
            self.order_executor = DryRunOrderExecutor(self.symbol_manager, self.config, self.breakout_engine)
            logger.info("✓ Dry-run order executor initialized")
        else:
            self.order_executor = LiveOrderExecutor(self.kite, self.symbol_manager, self.config)
            logger.info("✓ Live order executor initialized")
        
        # 9. Trade Logger
        self.trade_logger = TradeLogger(self.config)
        
        # 10. Tick Router
        self.tick_router = TickRouter(self.candle_builder, self.breakout_engine, self.risk_manager)
        
        # 11. WebSocket Manager
        api_key = os.getenv('API_KEY')
        access_token = os.getenv('ACCESS_TOKEN')
        self.ws_manager = WebSocketManager(api_key, access_token, self.config)
        
        logger.info("✓ All modules initialized")
    
    def _setup_callbacks(self):
        """Setup callbacks between modules"""
        
        # Candle close -> Marker
        def on_candle_close(candle):
            self.marker.evaluate_and_mark(candle)
        
        self.candle_builder.set_on_candle_close_callback(on_candle_close)
        
        # Breakout -> Entry Execution
        def on_breakout(symbol, entry_price, stoploss):
            self._execute_entry(symbol, entry_price, stoploss)
        
        self.breakout_engine.set_on_breakout_callback(on_breakout)
        
        # Risk Manager -> Exit Execution
        def on_exit(symbol, exit_price, reason):
            self._execute_exit(symbol, exit_price, reason)
        
        self.risk_manager.set_on_exit_callback(on_exit)
        
        # WebSocket -> Tick Router
        self.ws_manager.bind_tick_router(self.tick_router.enqueue_ticks)
        
        logger.info("✓ Callbacks configured")
    
    def _execute_entry(self, symbol: str, entry_price: float, stoploss: float):
        """Execute breakout entry"""
        
        # Check if can take trade
        if not self.portfolio.can_take_trade(MAX_TRADES_PER_DAY):
            logger.warning(f"Max trades reached ({MAX_TRADES_PER_DAY}) - skipping {symbol}")
            return
        
        # Check max loss
        if self.risk_manager.check_max_loss():
            logger.critical("Max daily loss reached - stopping trading")
            return
        
        logger.info(f"[ENTRY_FLOW] {symbol} - Breakout Entry Price: {entry_price:.2f}, Stop Loss: {stoploss:.2f}")
        
        # Calculate position size
        quantity = self.risk_manager.calculate_position_size(symbol, entry_price, stoploss)
        
        if quantity == 0:
            logger.warning(f"{symbol}: Position size = 0, skipping entry")
            return
        
        # Place order
        order_id = self.order_executor.place_buy_order(symbol, quantity, entry_price)
        
        if not order_id:
            logger.error(f"{symbol}: Entry order failed")
            return
        
        # Get actual execution price (for dry-run, it's immediate)
        actual_price = self.order_executor.get_average_price(order_id) or entry_price
        
        logger.info(f"[ENTRY_FLOW] {symbol} - Order Executor Actual Price: {actual_price:.2f}")
        
        # Add to portfolio
        self.portfolio.add_position(symbol, actual_price, stoploss, quantity)
        
        # Log trade
        self.trade_logger.log_entry(symbol, quantity, actual_price, order_id)
        
        logger.info(f"✅ ENTRY: {symbol} x{quantity} @ {actual_price:.2f} | SL: {stoploss:.2f}")
    
    def _execute_exit(self, symbol: str, exit_price: float, reason: str):
        """Execute position exit"""
        
        position = self.portfolio.get_position(symbol)
        if not position:
            logger.warning(f"{symbol}: No position to exit")
            return
        
        logger.info(f"[EXIT_FLOW] {symbol} - Risk Manager Exit Price: {exit_price:.2f}, Entry Price: {position.entry_price:.2f}")
        
        # Place exit order
        order_id = self.order_executor.place_sell_order(symbol, position.quantity, exit_price)
        
        if not order_id:
            logger.error(f"{symbol}: Exit order failed")
            return
        
        # Get actual execution price
        actual_price = self.order_executor.get_average_price(order_id) or exit_price
        
        logger.info(f"[EXIT_FLOW] {symbol} - Order Executor Actual Price: {actual_price:.2f}")
        
        # Close position in portfolio
        closed_position = self.portfolio.close_position(symbol, actual_price, reason)
        
        # Log trade
        if closed_position:
            self.trade_logger.log_exit(
                symbol, 
                closed_position.quantity,
                closed_position.entry_price,
                actual_price,
                reason,
                order_id
            )
        
        logger.info(f"✅ EXIT: {symbol} @ {actual_price:.2f} | Reason: {reason} | PNL: {closed_position.realized_pnl:.2f}")
    def _fetch_and_update_opening_prices(self):
        """
        Fetch actual opening prices from Kite API and update 9:15 candles.
        Called at 9:15:02 in a background thread.
        """
        try:
            logger.info("Fetching actual opening prices for 9:15 candles...")
            
            # Get all tokens
            tokens = self.symbol_manager.get_all_tokens()
            
            # Fetch OHLC data from Kite API
            # This gives us the actual opening price at 9:15:00
            ohlc_data = self.kite.ohlc(tokens)
            
            updated_count = 0
            for token_str, data in ohlc_data.items():
                token = int(token_str)
                symbol = self.symbol_manager.get_symbol(token)
                
                if symbol and 'ohlc' in data:
                    actual_open = data['ohlc']['open']
                    
                    # Update the candle builder with correct opening price
                    self.candle_builder.update_candle_open_price(symbol, actual_open)
                    updated_count += 1
            
            logger.info(f"✓ Updated opening prices for {updated_count} symbols")
            
        except Exception as e:
            logger.error(f"Error fetching opening prices: {e}", exc_info=True)

    def fetch_historical_data(self):
        """Fetch 14-day historical data (run before 9:15)"""
        logger.info("=" * 60)
        logger.info("FETCHING HISTORICAL DATA")
        logger.info("=" * 60)
        
        self.historical_manager.fetch_all_historical_data(days=HISTORICAL_DAYS)
        
        logger.info("✓ Historical data ready")
    
    def start_trading(self):
        """Start live trading (non-blocking websocket + keep-alive loop)"""
        logger.info("=" * 60)
        logger.info("STARTING LIVE TRADING")
        logger.info("=" * 60)
        
        # Subscribe to all tokens
        tokens = self.symbol_manager.get_all_tokens()
        self.ws_manager.subscribe(tokens)
        
        # Start WebSocket in threaded/non-blocking mode.
        # Prefer a dedicated start_threaded() if the WS manager exposes it;
        # otherwise call start(threaded=True).
        logger.info("Starting WebSocket connection (threaded)...")
        if hasattr(self.ws_manager, 'start_threaded'):
            self.ws_manager.start_threaded()
        else:
            # attempt to call start with threaded=True (backwards-compatible)
            try:
                self.ws_manager.start(threaded=True)
            except TypeError:
                # Fallback: call start() but this will block (not desired)
                logger.warning("WebSocket manager does not support threaded start; calling blocking start(). Consider updating ws_manager.")
                self.ws_manager.start()
                return
        # Schedule opening price correction at 9:15:02
        def schedule_opening_price_update():
            """Wait until 9:15:02, then fetch and update opening prices"""
            import time as time_module
            from datetime import datetime, time
            
            # Wait until exactly 9:15:02
            while True:
                now = datetime.now().time()
                if now >= time(9, 15, 2) and now < time(9, 15, 10):
                    # We're in the window, fetch prices
                    self._fetch_and_update_opening_prices()
                    break
                elif now >= time(9, 15, 10):
                    # Too late, skip
                    logger.warning("Missed 9:15:02 window for opening price update")
                    break
                time_module.sleep(0.1)  # Check every 100ms
        # Start background thread for opening price update
        import threading
        opening_price_thread = threading.Thread(
            target=schedule_opening_price_update,
            daemon=True,
            name="OpeningPriceUpdater"
        )
        opening_price_thread.start()
        logger.info("✓ Opening price updater thread started")
        # Keep main thread alive and respond to shutdown requests
        logger.info("Trading system running. Press Ctrl+C to stop.")
        try:
            while not self.shutdown_requested:
                time_module.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n\nShutdown signal received (KeyboardInterrupt).")
            self.shutdown()
        except Exception as e:
            logger.error(f"Error in main keep-alive loop: {e}", exc_info=True)
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the trading system"""
        if self.shutdown_requested:
            return  # already shutting down
        logger.info("Shutting down trading system...")
        self.shutdown_requested = True
        
        # Stop WebSocket
        try:
            if self.ws_manager:
                logger.info("Stopping WebSocket...")
                self.ws_manager.stop()
        except Exception as e:
            logger.debug(f"Error stopping WebSocket: {e}")
        
        # (Optional) Close all open positions safely if required
        # try:
        #     self.portfolio.close_all_positions()
        # except Exception as e:
        #     logger.debug(f"Error closing positions: {e}")
        
        # Print final stats
        try:
            self.print_stats()
        except Exception as e:
            logger.debug(f"Error printing stats: {e}")
        
        logger.info("✓ Shutdown complete")
    
    def print_stats(self):
        """Print current statistics"""
        logger.info("=" * 60)
        logger.info("SYSTEM STATISTICS")
        logger.info("=" * 60)
        
        # Portfolio stats
        portfolio_stats = self.portfolio.get_stats()
        logger.info(f"Capital: ₹{portfolio_stats['total_capital']:,.2f} | PNL: ₹{portfolio_stats['total_pnl']:,.2f}")
        logger.info(f"Trades: {portfolio_stats['trades_today']} | Active: {portfolio_stats['active_positions']}")
        logger.info(f"Win Rate: {portfolio_stats['win_rate']:.1f}%")
        
        # Marker stats
        marker_stats = self.marker.get_stats()
        logger.info(f"Marked: {marker_stats['total_marked']}/{marker_stats['total_evaluated']}")
        
        # Breakout stats
        breakout_stats = self.breakout_engine.get_stats()
        logger.info(f"Breakouts: {breakout_stats['breakouts_detected']}")

def main(system):
    """Main entry point"""
    
    # Phase 1: Fetch historical data (before 9:15)
    current_time = datetime.now().time()
    
    if current_time < MARKET_OPEN_TIME or current_time > MARKET_CLOSE_TIME:
        logger.info(f"Current time: {current_time.strftime('%H:%M:%S')} (outside market hours)")
        logger.info("Fetching historical data...")
        system.fetch_historical_data()
        
        # Wait until market opens
        logger.info("Waiting for market to open at 9:15 AM...")
        while datetime.now().time() < MARKET_OPEN_TIME or datetime.now().time() > MARKET_CLOSE_TIME:
            time_module.sleep(1)
    
    # Phase 2: Start live trading
    logger.info("Market is open! Starting trading...")
    system.start_trading()

if __name__ == "__main__":
    trading_system = None

    def _sigint_handler(signum, frame):
        logger.info("\n\nShutdown requested by user (SIGINT)")
        # set flag and let the main loop call shutdown
        try:
            if trading_system:
                trading_system.shutdown_requested = True
            else:
                # if not initialized, exit immediately
                sys.exit(0)
        except Exception:
            sys.exit(0)

    # Register SIGINT handler so Ctrl+C sets the flag reliably
    signal.signal(signal.SIGINT, _sigint_handler)

    try:
        trading_system = TradingSystem()
        main(trading_system)
    except KeyboardInterrupt:
        logger.info("\n\nShutdown requested by user (KeyboardInterrupt)")
        if trading_system:
            trading_system.shutdown()
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        # ensure clean shutdown attempt
        try:
            if trading_system:
                trading_system.shutdown()
        finally:
            sys.exit(1)
