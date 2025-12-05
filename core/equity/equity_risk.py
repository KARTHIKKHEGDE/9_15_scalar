# core/risk.py
"""
Real-time stop-loss and risk management
Ultra-fast tick-by-tick monitoring
"""
import logging
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Monitors positions for stop-loss hits
    Executes exits with minimal latency
    """
    
    def __init__(self, portfolio, symbol_manager, config, marker):
        self.portfolio = portfolio
        self.symbol_manager = symbol_manager
        self.config = config
        self.marker = marker  # NEW: Add marker reference for getting marked stock count
        
        # Callback for exit execution
        self.on_exit: Optional[Callable[[str, float, str], None]] = None
        
        # Stats
        self.stops_hit = 0
    
    def set_on_exit_callback(self, callback: Callable[[str, float, str], None]):
        """
        Set callback for position exit
        callback(symbol, exit_price, reason)
        """
        self.on_exit = callback
    
    def process_tick(self, tick: dict):
        """
        Check for stop-loss hits on every tick
        ULTRA CRITICAL: Must be FAST
        """
        token = tick['instrument_token']
        price = tick['last_price']
        
        # Get symbol
        symbol = self.symbol_manager.get_symbol(token)
        if not symbol:
            return
        
        # Only monitor if we have a position
        if not self.portfolio.has_position(symbol):
            return
        
        # Update position price
        self.portfolio.update_position_price(symbol, price)
        
        # Get position
        position = self.portfolio.get_position(symbol)
        if not position:
            return
        
        # Check stop-loss
        if self._check_stoploss(position, price):
            self._trigger_exit(symbol, price, "STOP_LOSS")
    
    def _check_stoploss(self, position, current_price: float) -> bool:
        """Check if stop-loss is hit"""
        return current_price <= position.stoploss
    
    def _trigger_exit(self, symbol: str, exit_price: float, reason: str):
        """
        Trigger position exit
        CRITICAL: Must execute FAST
        """
        self.stops_hit += 1
        
        position = self.portfolio.get_position(symbol)
        if not position:
            return
        
        logger.warning(f"🛑 EXIT: {symbol} @ {exit_price:.2f} | Reason: {reason} | Entry: {position.entry_price:.2f}")
        
        # Execute exit via callback
        if self.on_exit:
            try:
                self.on_exit(symbol, exit_price, reason)
            except Exception as e:
                logger.error(f"Error in exit callback for {symbol}: {e}")
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                        stoploss: float) -> int:
        """
        Calculate position size based on EQUAL CAPITAL DISTRIBUTION
        Uses total marked count which stays constant throughout the day
        """
        # Get total marked count (stays constant even after breakouts)
        total_marked = self.marker.get_total_marked_count()
        
        if total_marked == 0:
            logger.warning(f"{symbol}: No stocks marked for trading")
            return 0
        
        # Divide capital equally among ALL marked stocks
        capital_per_stock = self.config['TOTAL_CAPITAL'] / total_marked
        
        # Calculate quantity
        quantity = int(capital_per_stock / entry_price)*5
        
        if quantity == 0:
            logger.warning(f"{symbol}: Quantity = 0 (price too high for ₹{capital_per_stock:.2f})")
            return 0
        
        logger.info(
            f"{symbol}: Position size = {quantity} shares | "
            f"Capital allocated: ₹{capital_per_stock:.2f} | "
            f"Total marked: {total_marked} stocks"
        )
        
        return quantity
    
    def check_max_loss(self) -> bool:
        """Check if max daily loss is hit"""
        if 'MAX_LOSS_PER_DAY' not in self.config:
            return False
        
        total_loss = abs(min(0, self.portfolio.total_pnl))
        
        if total_loss >= self.config['MAX_LOSS_PER_DAY']:
            logger.critical(f"🚨 MAX DAILY LOSS HIT: {total_loss:.2f}")
            return True
        
        return False
    
    def get_stats(self) -> dict:
        """Get risk management statistics"""
        return {
            'stops_hit': self.stops_hit
        }