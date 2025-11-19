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
    
    def __init__(self, portfolio, symbol_manager, config):
        self.portfolio = portfolio
        self.symbol_manager = symbol_manager
        self.config = config
        
        # Callback for exit execution
        self.on_exit: Optional[Callable[[str, float, str], None]] = None
        
        # Trailing stop-loss tracking (symbol -> trailing_sl_price)
        self.trailing_stops = {}
        
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
        
        # Check trailing stop if enabled
        elif self.config.get('TRAILING_SL_PERCENT'):
            self._update_trailing_stop(position, price)
            if self._check_trailing_stop(position, price):
                self._trigger_exit(symbol, price, "TRAILING_STOP")
    
    def _check_stoploss(self, position, current_price: float) -> bool:
        """Check if stop-loss is hit"""
        return current_price <= position.stoploss
    
    def _update_trailing_stop(self, position, current_price: float):
        """Update trailing stop-loss"""
        trailing_percent = self.config['TRAILING_SL_PERCENT']
        
        # Calculate new trailing stop
        new_trailing = current_price * (1 - trailing_percent / 100)
        
        # Update if price moved up
        if position.symbol not in self.trailing_stops:
            self.trailing_stops[position.symbol] = position.stoploss
        
        if new_trailing > self.trailing_stops[position.symbol]:
            self.trailing_stops[position.symbol] = new_trailing
            logger.debug(f"{position.symbol}: Trailing SL updated to {new_trailing:.2f}")
    
    def _check_trailing_stop(self, position, current_price: float) -> bool:
        """Check if trailing stop is hit"""
        if position.symbol in self.trailing_stops:
            return current_price <= self.trailing_stops[position.symbol]
        return False
    
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
        Calculate position size based on risk
        Risk = RISK_PER_TRADE_PERCENT of capital
        """
        risk_amount = self.portfolio.available_capital * (self.config['RISK_PER_TRADE_PERCENT'] / 100)
        
        # Calculate risk per share
        risk_per_share = entry_price - stoploss
        
        if risk_per_share <= 0:
            logger.warning(f"{symbol}: Invalid risk calculation (SL >= Entry)")
            return 0
        
        # Calculate quantity
        quantity = int(risk_amount / risk_per_share)
        
        # Ensure we have enough capital
        required_capital = quantity * entry_price
        if required_capital > self.portfolio.available_capital:
            quantity = int(self.portfolio.available_capital / entry_price)
        
        logger.debug(f"{symbol}: Position size = {quantity} shares (Risk: {risk_amount:.2f})")
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
            'stops_hit': self.stops_hit,
            'trailing_stops_active': len(self.trailing_stops)
        }