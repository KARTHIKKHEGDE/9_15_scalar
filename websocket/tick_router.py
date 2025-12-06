# websocket/tick_router.py
"""
Ultra-low-latency tick router with threaded queue processing.
Ensures WebSocket thread stays non-blocking while tick processing
runs in a dedicated worker thread.
"""

import logging
from typing import List, Dict
from datetime import datetime, time
import queue
import threading

logger = logging.getLogger(__name__)


class TickRouter:
    """
    High-performance tick router.

    NEW ARCHITECTURE:
    -----------------
    ✔ WebSocket thread → puts ticks into Queue (fast)
    ✔ Worker thread → consumes queue & routes ticks (heavy processing)
    ✔ Non-blocking & scalable
    """

    def __init__(self, candle_builder, breakout_engine, risk_manager, 
                 options_breakout=None, options_risk=None):
        self.candle_builder = candle_builder
        self.breakout_engine = breakout_engine
        self.risk_manager = risk_manager
        
        # Options modules (optional)
        self.options_breakout = options_breakout
        self.options_risk = options_risk

        # Queue for incoming ticks (high capacity)
        self.tick_queue: queue.Queue[List[Dict]] = queue.Queue(maxsize=5000)

        # Market hours
        self.market_open = time(9, 15, 0)
        self.market_close = time(15, 30, 0)

        # Stats
        self.ticks_processed = 0

        # Start worker thread
        worker = threading.Thread(target=self._worker_loop, daemon=True)
        worker.start()
        logger.info("✓ TickRouter worker thread started")

    # ---------------------------------------------------------
    # Called by WebSocket on_ticks callback
    # ---------------------------------------------------------
    def enqueue_ticks(self, ticks: List[dict]):
        """
        Insert tick batch into queue.
        Non-blocking. If queue is full, drop ticks to save CPU.
        """
        try:
            self.tick_queue.put_nowait(ticks)
        except queue.Full:
            logger.warning("⚠ Tick queue FULL — dropping ticks to avoid lag")

    # ---------------------------------------------------------
    # Worker thread continuously processes ticks
    # ---------------------------------------------------------
    def _worker_loop(self):
        while True:
            ticks = self.tick_queue.get()  # blocking but extremely fast
            try:
                self._process_tick_batch(ticks)
            except Exception as e:
                logger.error(f"Tick worker error: {e}", exc_info=True)

    # ---------------------------------------------------------
    # Process a batch of ticks
    # ---------------------------------------------------------
    def _process_tick_batch(self, ticks: List[dict]):
        if not ticks:
            return

        current_time = datetime.now().time()
        if not (self.market_open <= current_time <= self.market_close):
            return

        for tick in ticks:
            self._route_single_tick(tick)

        self.ticks_processed += len(ticks)

    # ---------------------------------------------------------
    # Route ONE tick
    # ---------------------------------------------------------
    def _route_single_tick(self, tick: dict):
        try:
            # Candle Builder (for all symbols)
            self.candle_builder.process_tick(tick)

            # Equity Breakout Engine
            self.breakout_engine.process_tick(tick)

            # Equity Risk Manager
            self.risk_manager.process_tick(tick)
            
            # Options Breakout Engine (if enabled)
            if self.options_breakout:
                self.options_breakout.process_tick(tick)
            
            # Options Risk Manager (if enabled)
            if self.options_risk:
                self.options_risk.process_tick(tick)

        except Exception as e:
            logger.error(f"⚠ Tick routing exception: {e}", exc_info=True)

    # ---------------------------------------------------------
    # Stats helper
    # ---------------------------------------------------------
    def get_stats(self) -> dict:
        return {
            "ticks_processed": self.ticks_processed,
            "active_candles": len(self.candle_builder.active_candles),
            "marked_symbols": len(self.breakout_engine.marker.marked_symbols),
        }
