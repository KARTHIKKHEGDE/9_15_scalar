# websocket/tick_router.py
"""
Ultra-low-latency tick routing
Routes ticks to candle builder, breakout engine, and risk manager
Optimized for sub-millisecond processing
"""
import logging
from typing import List
from datetime import datetime, time

logger = logging.getLogger(__name__)

class TickRouter:
    """
    Routes incoming ticks to appropriate engines
    Single-threaded for maximum speed (no context switching)
    """
    
    def __init__(self, candle_builder, breakout_engine, risk_manager):
        self.candle_builder = candle_builder
        self.breakout_engine = breakout_engine
        self.risk_manager = risk_manager
        
        # Performance tracking
        self.ticks_processed = 0
        self.last_tick_time = None
        
        # Market hours
        self.market_open = time(9, 15, 0)
        self.market_close = time(15, 30, 0)
    
    def route_ticks(self, ticks: List[dict]):
        """
        Route batch of ticks to all engines
        Called by WebSocket on_ticks callback
        
        CRITICAL: This is the HOT PATH - optimize heavily
        """
        if not ticks:
            return
        
        current_time = datetime.now().time()
        
        # Only process during market hours
        if not (self.market_open <= current_time <= self.market_close):
            return
        
        # Process each tick
        for tick in ticks:
            self._route_single_tick(tick)
        
        self.ticks_processed += len(ticks)
    
    def _route_single_tick(self, tick: dict):
        """
        Route single tick to all engines
        ULTRA CRITICAL: Keep this as fast as possible
        """
        try:
            # 1. Candle Builder (always update candles)
            self.candle_builder.process_tick(tick)
            
            # 2. Breakout Engine (only for marked symbols)
            self.breakout_engine.process_tick(tick)
            
            # 3. Risk Manager (only for active positions)
            self.risk_manager.process_tick(tick)
            
        except Exception as e:
            # Log but don't crash on single tick error
            logger.error(f"Error routing tick: {e}", exc_info=True)
    
    def get_stats(self) -> dict:
        """Get routing statistics"""
        return {
            'ticks_processed': self.ticks_processed,
            'candles_active': len(self.candle_builder.active_candles),
            'marked_symbols': len(self.breakout_engine.marker.marked_symbols)
        }