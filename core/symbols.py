# core/symbols.py
"""
Ultra-fast symbol loading and token mapping
"""
import csv
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)

class SymbolManager:
    """Manages symbols and their instrument tokens with O(1) lookups"""
    
    def __init__(self, kite):
        self.kite = kite
        self.symbols: List[str] = []
        self.token_map: Dict[str, int] = {}  # symbol -> token
        self.reverse_token_map: Dict[int, str] = {}  # token -> symbol
        self.instrument_map: Dict[str, dict] = {}  # symbol -> full instrument data
        
    def load_symbols_from_csv(self, csv_path: str) -> int:
        """
        Load symbols from CSV (expects column: symbol or trading_symbol)
        Returns count of loaded symbols
        """
        symbols_set: Set[str] = set()
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Try different column names
                    symbol = (row.get('symbol') or 
                             row.get('trading_symbol') or 
                             row.get('tradingsymbol') or
                             row.get('Symbol') or
                             row.get('SYMBOL'))
                    
                    if symbol:
                        symbols_set.add(symbol.strip().upper())
            
            self.symbols = sorted(list(symbols_set))
            logger.info(f"Loaded {len(self.symbols)} symbols from CSV")
            return len(self.symbols)
            
        except Exception as e:
            logger.error(f"Error loading symbols from CSV: {e}")
            raise
    
    def add_symbol(self, symbol: str):
        """
        Add a single symbol programmatically
        Useful for adding NIFTY FUT or other specific symbols
        """
        symbol = symbol.strip().upper()
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            logger.info(f"Added symbol: {symbol}")

    
    def map_tokens(self, exchange: str = "NSE") -> Dict[str, int]:
        """
        Map symbols to instrument tokens using Kite instruments
        Optimized for speed with dictionary lookups
        """
        try:
            # Fetch NSE instruments for equities
            logger.info("Fetching NSE instruments...")
            nse_instruments = self.kite.instruments(exchange)
            
            # Create fast lookup dictionary for equities
            instrument_lookup = {
                inst['tradingsymbol']: inst 
                for inst in nse_instruments 
                if inst['instrument_type'] == 'EQ'  # Only equities
            }
            
            # Also fetch NFO instruments for NIFTY FUT (if present in symbols)
            # Check if any symbol looks like NIFTY FUT
            has_nifty_fut = any('NIFTY' in symbol and 'FUT' in symbol for symbol in self.symbols)
            
            if has_nifty_fut:
                logger.info("Fetching NFO instruments for NIFTY FUT...")
                nfo_instruments = self.kite.instruments('NFO')
                
                # Add NFO futures to lookup
                for inst in nfo_instruments:
                    if inst['instrument_type'] == 'FUT':
                        instrument_lookup[inst['tradingsymbol']] = inst
            
            # Map tokens for our symbols
            mapped_count = 0
            for symbol in self.symbols:
                if symbol in instrument_lookup:
                    inst = instrument_lookup[symbol]
                    token = inst['instrument_token']
                    
                    self.token_map[symbol] = token
                    self.reverse_token_map[token] = symbol
                    self.instrument_map[symbol] = inst
                    mapped_count += 1
                else:
                    logger.warning(f"Symbol {symbol} not found in {exchange} instruments")
            
            logger.info(f"Mapped {mapped_count}/{len(self.symbols)} symbols to tokens")
            return self.token_map
            
        except Exception as e:
            logger.error(f"Error mapping tokens: {e}")
            raise
    
    def get_token(self, symbol: str) -> int:
        """O(1) token lookup"""
        return self.token_map.get(symbol)
    
    def get_symbol(self, token: int) -> str:
        """O(1) symbol lookup"""
        return self.reverse_token_map.get(token)
    
    def get_all_tokens(self) -> List[int]:
        """Get list of all tokens for WebSocket subscription"""
        return list(self.token_map.values())
    
    def get_tick_size(self, symbol: str) -> float:
        """Get tick size for a symbol"""
        inst = self.instrument_map.get(symbol)
        return inst['tick_size'] if inst else 0.05
    
    def get_lot_size(self, symbol: str) -> int:
        """Get lot size (always 1 for equities)"""
        return 1
    
    def get_instrument_data(self, symbol: str) -> dict:
        """Get full instrument data"""
        return self.instrument_map.get(symbol, {})
    def get_nearest_nifty_fut(self) -> str:
        """
        Automatically fetch nearest month NIFTY FUT symbol
        Returns symbol like 'NIFTY24DECFUT'
        """
        try:
            from datetime import datetime
            
            # Fetch all NFO instruments
            logger.info("Fetching nearest NIFTY FUT symbol...")
            instruments = self.kite.instruments('NFO')
            
            # Filter NIFTY futures
            nifty_futs = [
                inst for inst in instruments
                if inst['name'] == 'NIFTY' and inst['instrument_type'] == 'FUT'
            ]
            
            if not nifty_futs:
                logger.error("No NIFTY FUT instruments found")
                return None
            
            # Sort by expiry date (nearest first)
            nifty_futs.sort(key=lambda x: x['expiry'])
            
            # Get nearest expiry
            nearest_fut = nifty_futs[0]
            symbol = nearest_fut['tradingsymbol']
            
            logger.info(f"✓ Nearest NIFTY FUT: {symbol} | Expiry: {nearest_fut['expiry']}")
            return symbol
            
        except Exception as e:
            logger.error(f"Error fetching nearest NIFTY FUT: {e}")
            return None