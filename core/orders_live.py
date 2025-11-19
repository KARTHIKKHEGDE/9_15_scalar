# core/orders_live.py
"""
Live order execution via Zerodha Kite
Optimized for minimal latency
"""
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LiveOrderExecutor:
    """
    Executes real orders via Kite API
    Handles order placement, confirmation, and error handling
    """
    
    def __init__(self, kite, symbol_manager, config):
        self.kite = kite
        self.symbol_manager = symbol_manager
        self.config = config
        
        # Order tracking
        self.pending_orders = {}  # order_id -> order_details
        self.executed_orders = {}  # symbol -> order_id
        
        # Stats
        self.orders_placed = 0
        self.orders_failed = 0
    
    def place_buy_order(self, symbol: str, quantity: int, price: Optional[float] = None) -> Optional[str]:
        """
        Place BUY order (MARKET or LIMIT)
        Returns order_id if successful, None otherwise
        """
        try:
            order_params = {
                'tradingsymbol': symbol,
                'exchange': self.config['EXCHANGE'],
                'transaction_type': 'BUY',
                'quantity': quantity,
                'product': self.config['PRODUCT_TYPE'],
                'order_type': self.config['ORDER_TYPE'],
            }
            
            # Add price for LIMIT orders
            if self.config['ORDER_TYPE'] == 'LIMIT' and price:
                order_params['price'] = price
            
            # Place order
            order_id = self.kite.place_order(
                variety='regular',
                **order_params
            )
            
            self.orders_placed += 1
            self.pending_orders[order_id] = {
                'symbol': symbol,
                'type': 'BUY',
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now()
            }
            
            logger.info(f"✓ BUY order placed: {symbol} x{quantity} | Order ID: {order_id}")
            return order_id
            
        except Exception as e:
            self.orders_failed += 1
            logger.error(f"✗ BUY order failed for {symbol}: {e}")
            return None
    
    def place_sell_order(self, symbol: str, quantity: int, price: Optional[float] = None) -> Optional[str]:
        """
        Place SELL order (MARKET or LIMIT)
        Returns order_id if successful, None otherwise
        """
        try:
            order_params = {
                'tradingsymbol': symbol,
                'exchange': self.config['EXCHANGE'],
                'transaction_type': 'SELL',
                'quantity': quantity,
                'product': self.config['PRODUCT_TYPE'],
                'order_type': 'MARKET',  # Always MARKET for exits (speed)
            }
            
            # Place order
            order_id = self.kite.place_order(
                variety='regular',
                **order_params
            )
            
            self.orders_placed += 1
            self.pending_orders[order_id] = {
                'symbol': symbol,
                'type': 'SELL',
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now()
            }
            
            logger.info(f"✓ SELL order placed: {symbol} x{quantity} | Order ID: {order_id}")
            return order_id
            
        except Exception as e:
            self.orders_failed += 1
            logger.error(f"✗ SELL order failed for {symbol}: {e}")
            return None
    
    def get_order_status(self, order_id: str) -> Optional[dict]:
        """Get order status from Kite"""
        try:
            orders = self.kite.orders()
            for order in orders:
                if order['order_id'] == order_id:
                    return order
            return None
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        try:
            self.kite.cancel_order(
                variety='regular',
                order_id=order_id
            )
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def get_average_price(self, order_id: str) -> Optional[float]:
        """Get average execution price for order"""
        order = self.get_order_status(order_id)
        if order and order['status'] == 'COMPLETE':
            return order['average_price']
        return None
    
    def get_stats(self) -> dict:
        """Get order execution statistics"""
        return {
            'orders_placed': self.orders_placed,
            'orders_failed': self.orders_failed,
            'pending_orders': len(self.pending_orders)
        }