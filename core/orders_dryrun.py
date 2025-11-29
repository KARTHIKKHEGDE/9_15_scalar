# core/orders_dryrun.py
"""
Ultra-realistic dry-run order simulation
Uses real-time tick prices instead of artificial slippage
"""
import logging
from typing import Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class DryRunOrderExecutor:
    """
    Simulates order execution with realistic behavior
    Uses actual market prices from live ticks
    """
    
    def __init__(self, symbol_manager, config, breakout_engine):
        self.symbol_manager = symbol_manager
        self.config = config
        self.breakout_engine = breakout_engine  # To fetch current LTP
        
        # Order tracking
        self.orders = {}  # order_id -> order_details
        
        # Stats
        self.orders_placed = 0
        self.orders_executed = 0
    
    def _get_current_ltp(self, symbol: str) -> Optional[float]:
        """
        Get current LTP from breakout engine's last_prices
        This is the REAL tick price, not simulated
        """
        price = self.breakout_engine.get_last_price(symbol)
        if price:
            logger.debug(f"{symbol}: Current LTP = {price:.2f}")
            return price
        return None
    
    def place_buy_order(self, symbol: str, quantity: int, price: Optional[float] = None) -> Optional[str]:
        """
        Simulate BUY order placement
        Uses REAL LTP at order placement time
        """
        order_id = str(uuid.uuid4())[:8]
        
        # Get REAL current market price
        current_ltp = self._get_current_ltp(symbol)
        
        logger.info(f"[ORDER_EXEC] {symbol} BUY - Requested Price: {price:.2f if price else 0}, Current LTP: {current_ltp:.2f if current_ltp else 0}")
        
        # Use LTP if available, otherwise fallback to requested price
        execution_price = current_ltp if current_ltp else price
        
        order = {
            'order_id': order_id,
            'symbol': symbol,
            'transaction_type': 'BUY',
            'quantity': quantity,
            'order_type': self.config['ORDER_TYPE'],
            'requested_price': price,           # Breakout level
            'execution_price': execution_price,  # Actual LTP
            'status': 'COMPLETE',
            'timestamp': datetime.now(),
            'product': self.config['PRODUCT_TYPE']
        }
        
        self.orders[order_id] = order
        self.orders_placed += 1
        self.orders_executed += 1
        
        price_diff = execution_price - price if price else 0
        logger.info(
            f"[DRY-RUN] ✓ BUY: {symbol} x{quantity} @ {execution_price:.2f} "
            f"(Breakout: {price:.2f}, Diff: {price_diff:+.2f}) | ID: {order_id}"
        )
        return order_id
    
    def place_sell_order(self, symbol: str, quantity: int, price: Optional[float] = None) -> Optional[str]:
        """
        Simulate SELL order placement
        Uses REAL LTP at order placement time
        """
        order_id = str(uuid.uuid4())[:8]
        
        # Get REAL current market price
        current_ltp = self._get_current_ltp(symbol)
        
        logger.info(f"[ORDER_EXEC] {symbol} SELL - Requested Price: {price:.2f if price else 0}, Current LTP: {current_ltp:.2f if current_ltp else 0}")
        
        # Use LTP if available, otherwise fallback to requested price
        execution_price = current_ltp if current_ltp else price
        
        order = {
            'order_id': order_id,
            'symbol': symbol,
            'transaction_type': 'SELL',
            'quantity': quantity,
            'order_type': 'MARKET',
            'requested_price': price,           # Stop-loss level
            'execution_price': execution_price,  # Actual LTP
            'status': 'COMPLETE',
            'timestamp': datetime.now(),
            'product': self.config['PRODUCT_TYPE']
        }
        
        self.orders[order_id] = order
        self.orders_placed += 1
        self.orders_executed += 1
        
        price_diff = execution_price - price if price else 0
        logger.info(
            f"[DRY-RUN] ✓ SELL: {symbol} x{quantity} @ {execution_price:.2f} "
            f"(Stop-loss: {price:.2f}, Diff: {price_diff:+.2f}) | ID: {order_id}"
        )
        return order_id
    
    def get_order_status(self, order_id: str) -> Optional[dict]:
        """Get order details"""
        return self.orders.get(order_id)
    
    def cancel_order(self, order_id: str) -> bool:
        """Simulate order cancellation"""
        if order_id in self.orders:
            self.orders[order_id]['status'] = 'CANCELLED'
            logger.info(f"[DRY-RUN] Order cancelled: {order_id}")
            return True
        return False
    
    def get_average_price(self, order_id: str) -> Optional[float]:
        """Get execution price for order"""
        order = self.orders.get(order_id)
        if order and order['status'] == 'COMPLETE':
            logger.info(f"[ORDER_EXEC] Returning execution price for {order_id}: {order['execution_price']:.2f}")
            return order['execution_price']
        logger.warning(f"[ORDER_EXEC] Could not get execution price for {order_id}")
        return None
    
    def get_stats(self) -> dict:
        """Get order execution statistics"""
        return {
            'orders_placed': self.orders_placed,
            'orders_executed': self.orders_executed,
            'orders_failed': 0
        }
    
    def get_all_orders(self) -> list:
        """Get all simulated orders"""
        return list(self.orders.values())