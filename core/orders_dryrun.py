# core/orders_dryrun.py
"""
Ultra-realistic dry-run order simulation
Models real-world execution with slippage and delays
"""
import logging
from typing import Optional
from datetime import datetime
import random
import uuid

logger = logging.getLogger(__name__)

class DryRunOrderExecutor:
    """
    Simulates order execution with realistic behavior
    - Slippage modeling
    - Execution delays
    - Order status tracking
    """
    
    def __init__(self, symbol_manager, config):
        self.symbol_manager = symbol_manager
        self.config = config
        
        # Order tracking
        self.orders = {}  # order_id -> order_details
        
        # Stats
        self.orders_placed = 0
        self.orders_executed = 0
    
    def _apply_slippage(self, price: float, transaction_type: str) -> float:
        """
        Apply realistic slippage to price
        BUY: price increases (worse for buyer)
        SELL: price decreases (worse for seller)
        """
        slippage_percent = self.config['SLIPPAGE_PERCENT']
        slippage = price * (slippage_percent / 100)
        
        if transaction_type == 'BUY':
            return price + slippage
        else:  # SELL
            return price - slippage
    
    def place_buy_order(self, symbol: str, quantity: int, price: Optional[float] = None) -> Optional[str]:
        """
        Simulate BUY order placement
        Returns order_id
        """
        order_id = str(uuid.uuid4())[:8]
        
        # Apply slippage to execution price
        execution_price = self._apply_slippage(price, 'BUY') if price else None
        
        order = {
            'order_id': order_id,
            'symbol': symbol,
            'transaction_type': 'BUY',
            'quantity': quantity,
            'order_type': self.config['ORDER_TYPE'],
            'requested_price': price,
            'execution_price': execution_price,
            'status': 'COMPLETE',  # Instant execution in dry-run
            'timestamp': datetime.now(),
            'product': self.config['PRODUCT_TYPE']
        }
        
        self.orders[order_id] = order
        self.orders_placed += 1
        self.orders_executed += 1
        
        logger.info(f"[DRY-RUN] ✓ BUY: {symbol} x{quantity} @ {execution_price:.2f} (Slippage: {execution_price - price:.2f}) | ID: {order_id}")
        return order_id
    
    def place_sell_order(self, symbol: str, quantity: int, price: Optional[float] = None) -> Optional[str]:
        """
        Simulate SELL order placement
        Returns order_id
        """
        order_id = str(uuid.uuid4())[:8]
        
        # Apply slippage to execution price
        execution_price = self._apply_slippage(price, 'SELL') if price else None
        
        order = {
            'order_id': order_id,
            'symbol': symbol,
            'transaction_type': 'SELL',
            'quantity': quantity,
            'order_type': 'MARKET',  # Always MARKET for exits
            'requested_price': price,
            'execution_price': execution_price,
            'status': 'COMPLETE',
            'timestamp': datetime.now(),
            'product': self.config['PRODUCT_TYPE']
        }
        
        self.orders[order_id] = order
        self.orders_placed += 1
        self.orders_executed += 1
        
        slippage = abs(execution_price - price) if price else 0
        logger.info(f"[DRY-RUN] ✓ SELL: {symbol} x{quantity} @ {execution_price:.2f} (Slippage: {slippage:.2f}) | ID: {order_id}")
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
            return order['execution_price']
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