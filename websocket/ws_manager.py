# websocket/ws_manager.py
"""
Zerodha WebSocket manager with auto-reconnection
Handles real-time tick streaming with minimal latency
"""
import logging
from kiteconnect import KiteTicker
import time
from typing import Callable, List

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manages KiteTicker WebSocket connection
    Handles reconnection and error recovery
    """
    
    def __init__(self, api_key: str, access_token: str, config):
        self.api_key = api_key
        self.access_token = access_token
        self.config = config
        
        # Shutdown flag (CRITICAL)
        self.shutdown_requested = False

        # Initialize ticker
        self.ticker = KiteTicker(api_key, access_token)
        
        # Subscription tokens
        self.subscribed_tokens: List[int] = []
        
        # Callbacks
        self.on_ticks_callback: Callable = None
        
        # Connection state
        self.is_connected = False
        self.reconnect_attempts = 0
        
        # Setup callbacks
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Setup KiteTicker callbacks"""
        
        def on_connect(ws, response):
            logger.info("✓ WebSocket connected")
            self.is_connected = True
            self.reconnect_attempts = 0
            
            # Subscribe to tokens
            if self.subscribed_tokens:
                ws.subscribe(self.subscribed_tokens)
                ws.set_mode(ws.MODE_FULL, self.subscribed_tokens)
                logger.info(f"Subscribed to {len(self.subscribed_tokens)} instruments")
        
        def on_close(ws, code, reason):
            logger.warning(f"✗ WebSocket closed: {code} - {reason}")
            self.is_connected = False

            # Do NOT reconnect if shutdown requested
            if not self.shutdown_requested:
                self._attempt_reconnect()
            else:
                logger.info("Shutdown requested — skipping reconnection")
        
        def on_error(ws, code, reason):
            logger.error(f"✗ WebSocket error: {code} - {reason}")
        
        def on_reconnect(ws, attempts_count):
            logger.info(f"Reconnecting... (Attempt {attempts_count})")
        
        def on_noreconnect(ws):
            logger.critical("✗ Reconnection failed - max attempts reached")
            self.is_connected = False
        
        def on_ticks(ws, ticks):
            """CRITICAL HOT PATH"""
            if self.on_ticks_callback:
                try:
                    self.on_ticks_callback(ticks)
                except Exception as e:
                    logger.error(f"Error in ticks callback: {e}")
        
        # Assign callbacks
        self.ticker.on_connect = on_connect
        self.ticker.on_close = on_close
        self.ticker.on_error = on_error
        self.ticker.on_reconnect = on_reconnect
        self.ticker.on_noreconnect = on_noreconnect
        self.ticker.on_ticks = on_ticks
    
    def set_on_ticks_callback(self, callback: Callable):
        """Set callback for tick data"""
        self.on_ticks_callback = callback
    
    def subscribe(self, tokens: List[int]):
        """Subscribe to instrument tokens"""
        self.subscribed_tokens = tokens
        logger.info(f"Added {len(tokens)} tokens for subscription")
        
        # If already connected, subscribe immediately
        if self.is_connected:
            self.ticker.subscribe(tokens)
            self.ticker.set_mode(self.ticker.MODE_FULL, tokens)
    
    def start(self, threaded=False):
        """Start WebSocket connection"""
        logger.info("Starting WebSocket connection...")
        try:
            self.shutdown_requested = False   # reset on start
            self.ticker.connect(threaded=threaded)
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            raise
    
    def start_threaded(self):
        """Start WebSocket in separate thread (non-blocking)"""
        self.start(threaded=True)

    def stop(self):
        """Stop WebSocket connection"""
        logger.info("Stopping WebSocket...")
        self.shutdown_requested = True  # IMPORTANT
        try:
            self.ticker.close()
        except:
            pass
        self.is_connected = False
    
    def _attempt_reconnect(self):
        """Attempt to reconnect WebSocket"""
        
        # Do NOT reconnect if shutdown requested
        if self.shutdown_requested:
            logger.info("Shutdown requested — skipping reconnection.")
            return
        
        max_attempts = self.config.get('WS_RECONNECT_MAX_TRIES', 3)
        delay = self.config.get('WS_RECONNECT_DELAY', 5)
        
        if self.reconnect_attempts >= max_attempts:
            logger.critical("Max reconnection attempts reached")
            return
        
        self.reconnect_attempts += 1
        logger.info(f"Attempting reconnect in {delay}s (Attempt {self.reconnect_attempts}/{max_attempts})")
        time.sleep(delay)
        
        try:
            self.ticker.connect(threaded=True)
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
    
    def is_active(self) -> bool:
        return self.is_connected
