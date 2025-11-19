# core/trade_logger.py
"""
Fast CSV trade logging with buffering
Logs all trades for analysis
"""
import logging
import csv
from datetime import datetime
from pathlib import Path
import threading
from typing import List, Dict

logger = logging.getLogger(__name__)

class TradeLogger:
    """
    Logs trades to CSV with buffering
    Thread-safe for concurrent access
    """
    
    def __init__(self, config):
        self.config = config
        
        # Create output directory
        self.output_dir = Path(config['OUTPUT_DIR'])
        self.output_dir.mkdir(exist_ok=True)
        
        # Generate filename with date
        date_str = datetime.now().strftime('%Y%m%d')
        self.csv_path = self.output_dir / f"{config['TRADES_CSV_PREFIX']}{date_str}.csv"
        
        # CSV fields
        self.fields = [
            'timestamp',
            'symbol',
            'action',  # BUY/SELL
            'quantity',
            'price',
            'value',
            'pnl',
            'pnl_percent',
            'reason',  # BREAKOUT/STOP_LOSS/etc
            'order_id'
        ]
        
        # Trade buffer
        self.buffer: List[Dict] = []
        self.lock = threading.Lock()
        
        # Initialize CSV file
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Create CSV file with headers if it doesn't exist"""
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.fields)
                writer.writeheader()
            logger.info(f"Trade log created: {self.csv_path}")
    
    def log_entry(self, symbol: str, quantity: int, price: float, order_id: str):
        """Log entry trade"""
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': 'BUY',
            'quantity': quantity,
            'price': price,
            'value': quantity * price,
            'pnl': 0,
            'pnl_percent': 0,
            'reason': 'BREAKOUT',
            'order_id': order_id
        }
        
        self._write_trade(trade)
        logger.debug(f"Logged entry: {symbol} x{quantity} @ {price:.2f}")
    
    def log_exit(self, symbol: str, quantity: int, entry_price: float, 
                 exit_price: float, reason: str, order_id: str):
        """Log exit trade with PNL"""
        pnl = (exit_price - entry_price) * quantity
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': 'SELL',
            'quantity': quantity,
            'price': exit_price,
            'value': quantity * exit_price,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'reason': reason,
            'order_id': order_id
        }
        
        self._write_trade(trade)
        logger.debug(f"Logged exit: {symbol} x{quantity} @ {exit_price:.2f} | PNL: {pnl:.2f}")
    
    def _write_trade(self, trade: Dict):
        """Write trade to CSV (thread-safe)"""
        with self.lock:
            try:
                with open(self.csv_path, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=self.fields)
                    writer.writerow(trade)
            except Exception as e:
                logger.error(f"Error writing trade to CSV: {e}")
    
    def get_log_path(self) -> Path:
        """Get path to current log file"""
        return self.csv_path