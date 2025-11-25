# websocket/ws_manager.py
"""
Zerodha WebSocket manager (non-blocking)
Optimized for high-frequency tick streaming.
Compatible with queue-based TickRouter.
"""

import logging
import time
from kiteconnect import KiteTicker
from typing import List, Callable

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages Zerodha WebSocket connection"""

    def __init__(self, api_key: str, access_token: str, config):
        self.api_key = api_key
        self.access_token = access_token
        self.config = config

        # Shutdown flag
        self.shutdown_requested = False

        # Initialize KiteTicker
        self.ticker = KiteTicker(api_key, access_token)

        # Subscription tokens
        self.subscribed_tokens: List[int] = []

        # TickRouter enqueue function (NOT slow callback)
        self.enqueue_fn: Callable = None

        # Connection state
        self.is_connected = False
        self.reconnect_attempts = 0

        # Setup low-level callbacks
        self._setup_callbacks()

    # ---------------------------------------------------------
    # Register TickRouter enqueue function
    # ---------------------------------------------------------
    def bind_tick_router(self, enqueue_fn: Callable):
        """Called by main.py → bind TickRouter.enqueue_ticks()"""
        self.enqueue_fn = enqueue_fn
        logger.info("✓ TickRouter bound to WebSocket")

    # ---------------------------------------------------------
    # Setup WebSocket callbacks
    # ---------------------------------------------------------
    def _setup_callbacks(self):
        """Setup KiteTicker internal callbacks"""

        def on_connect(ws, response):
            logger.info("✓ WebSocket connected")
            self.is_connected = True
            self.reconnect_attempts = 0

            # Subscribe immediately
            if self.subscribed_tokens:
                ws.subscribe(self.subscribed_tokens)
                ws.set_mode(ws.MODE_FULL, self.subscribed_tokens)
                logger.info(f"Subscribed to {len(self.subscribed_tokens)} instruments")

        def on_ticks(ws, ticks):
            """FAST HOT PATH — MUST NOT BLOCK"""

            if not ticks:
                return

            if self.enqueue_fn:
                try:
                    # Push ticks into queue — microsecond operation
                    self.enqueue_fn(ticks)
                except Exception as e:
                    logger.error(f"Error enqueueing ticks: {e}", exc_info=True)

        def on_close(ws, code, reason):
            logger.warning(f"✗ WebSocket closed: {code} - {reason}")
            self.is_connected = False

            if not self.shutdown_requested:
                self._attempt_reconnect()

        def on_error(ws, code, reason):
            logger.error(f"✗ WebSocket error: {code} - {reason}")

        def on_reconnect(ws, attempts):
            logger.info(f"Reconnecting (attempt {attempts})...")

        def on_noreconnect(ws):
            logger.critical("✗ Reconnection failed — max attempts reached")
            self.is_connected = False

        self.ticker.on_connect = on_connect
        self.ticker.on_ticks = on_ticks
        self.ticker.on_close = on_close
        self.ticker.on_error = on_error
        self.ticker.on_reconnect = on_reconnect
        self.ticker.on_noreconnect = on_noreconnect

    # ---------------------------------------------------------
    # Subscribe tokens
    # ---------------------------------------------------------
    def subscribe(self, tokens: List[int]):
        self.subscribed_tokens = tokens
        logger.info(f"Added {len(tokens)} tokens for subscription")

        if self.is_connected:
            self.ticker.subscribe(tokens)
            self.ticker.set_mode(self.ticker.MODE_FULL, tokens)

    # ---------------------------------------------------------
    # Start WebSocket
    # ---------------------------------------------------------
    def start(self, threaded=True):
        logger.info("Starting WebSocket connection...")
        self.shutdown_requested = False
        try:
            self.ticker.connect(threaded=threaded)
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            raise

    def start_threaded(self):
        self.start(threaded=True)

    # ---------------------------------------------------------
    # Stop WebSocket
    # ---------------------------------------------------------
    def stop(self):
        logger.info("Stopping WebSocket...")
        self.shutdown_requested = True

        try:
            self.ticker.close()
        except:
            pass

        self.is_connected = False

    # ---------------------------------------------------------
    # Auto-reconnect logic
    # ---------------------------------------------------------
    def _attempt_reconnect(self):
        if self.shutdown_requested:
            logger.info("Shutdown requested — not reconnecting")
            return

        max_attempts = self.config.get("WS_RECONNECT_MAX_TRIES", 3)
        delay = self.config.get("WS_RECONNECT_DELAY", 5)

        if self.reconnect_attempts >= max_attempts:
            logger.critical("Max reconnection attempts reached")
            return

        self.reconnect_attempts += 1
        logger.info(f"Reconnecting in {delay}s (Attempt {self.reconnect_attempts}/{max_attempts})")

        time.sleep(delay)

        try:
            self.ticker.connect(threaded=True)
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")

    # ---------------------------------------------------------
    def is_active(self):
        return self.is_connected
