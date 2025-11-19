# core/portfolio.py
"""
Track active positions and real-time PNL
Thread-safe portfolio management
"""
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Single position data structure"""
    symbol: str
    entry_price: float
    stoploss: float
    quantity: int
    entry_time: datetime
    
    # Real-time tracking
    current_price: float = 0
    highest_price: float = 0
    
    # Exit tracking
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[str] = None
    
    # PNL
    realized_pnl: float = 0
    
    def __post_init__(self):
        self.highest_price = self.entry_price
    
    def update_price(self, price: float):
        """Update current price and track highest"""
        self.current_price = price
        if price > self.highest_price:
            self.highest_price = price
    
    def get_unrealized_pnl(self) -> float:
        """Calculate unrealized PNL"""
        if self.current_price > 0:
            return (self.current_price - self.entry_price) * self.quantity
        return 0
    
    def get_pnl_percent(self) -> float:
        """Get PNL as percentage"""
        if self.exit_price:
            return ((self.exit_price - self.entry_price) / self.entry_price) * 100
        elif self.current_price > 0:
            return ((self.current_price - self.entry_price) / self.entry_price) * 100
        return 0

class Portfolio:
    """
    Real-time portfolio tracking
    Thread-safe for concurrent access
    """
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.available_capital = initial_capital
        
        # Active positions (symbol -> Position)
        self.positions: Dict[str, Position] = {}
        self.lock = threading.Lock()
        
        # Closed positions history
        self.closed_positions: list[Position] = []
        
        # Daily stats
        self.trades_today = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0
    
    def add_position(self, symbol: str, entry_price: float, stoploss: float, 
                     quantity: int) -> Position:
        """Add new position to portfolio"""
        with self.lock:
            position = Position(
                symbol=symbol,
                entry_price=entry_price,
                stoploss=stoploss,
                quantity=quantity,
                entry_time=datetime.now()
            )
            
            self.positions[symbol] = position
            self.trades_today += 1
            
            # Update capital
            capital_used = entry_price * quantity
            self.available_capital -= capital_used
            
            logger.info(f"Position opened: {symbol} x{quantity} @ {entry_price:.2f} | Capital: {self.available_capital:.2f}")
            return position
    
    def update_position_price(self, symbol: str, price: float):
        """Update current price for position - O(1)"""
        with self.lock:
            if symbol in self.positions:
                self.positions[symbol].update_price(price)
    
    def close_position(self, symbol: str, exit_price: float, exit_reason: str) -> Optional[Position]:
        """Close position and calculate PNL"""
        with self.lock:
            if symbol not in self.positions:
                return None
            
            position = self.positions.pop(symbol)
            position.exit_price = exit_price
            position.exit_time = datetime.now()
            position.exit_reason = exit_reason
            
            # Calculate realized PNL
            position.realized_pnl = (exit_price - position.entry_price) * position.quantity
            self.total_pnl += position.realized_pnl
            
            # Update win/loss stats
            if position.realized_pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            # Return capital
            capital_returned = exit_price * position.quantity
            self.available_capital += capital_returned
            
            # Store in history
            self.closed_positions.append(position)
            
            logger.info(f"Position closed: {symbol} @ {exit_price:.2f} | PNL: {position.realized_pnl:.2f} ({position.get_pnl_percent():.2f}%) | Reason: {exit_reason}")
            return position
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get active position - O(1)"""
        return self.positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """Check if symbol has active position - O(1)"""
        return symbol in self.positions
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all active positions"""
        with self.lock:
            return self.positions.copy()
    
    def get_total_unrealized_pnl(self) -> float:
        """Get total unrealized PNL across all positions"""
        with self.lock:
            return sum(pos.get_unrealized_pnl() for pos in self.positions.values())
    
    def get_total_capital(self) -> float:
        """Get total capital (available + invested)"""
        invested = sum(
            pos.current_price * pos.quantity if pos.current_price > 0 
            else pos.entry_price * pos.quantity
            for pos in self.positions.values()
        )
        return self.available_capital + invested
    
    def can_take_trade(self, max_trades: int) -> bool:
        """Check if can take new trade"""
        return self.trades_today < max_trades
    
    def get_stats(self) -> dict:
        """Get portfolio statistics"""
        total_trades = self.winning_trades + self.losing_trades
        win_rate = (self.winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'initial_capital': self.initial_capital,
            'available_capital': self.available_capital,
            'total_capital': self.get_total_capital(),
            'total_pnl': self.total_pnl,
            'unrealized_pnl': self.get_total_unrealized_pnl(),
            'trades_today': self.trades_today,
            'active_positions': len(self.positions),
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate
        }