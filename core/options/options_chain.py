# core/options/options_chain.py
"""
Manage NIFTY options chain
Get ATM strike prices and option symbols
"""

import logging
from datetime import datetime
from typing import Optional
import math

logger = logging.getLogger(__name__)


class OptionsChainManager:
    """
    Manage NIFTY options chain
    Calculate ATM strikes and generate option symbols
    """
    
    def __init__(self, kite, config):
        self.kite = kite
        self.config = config
        self.exchange = config.get('OPTIONS_EXCHANGE', 'NFO')
        
        # NIFTY options parameters
        self.strike_gap = 50  # NIFTY strike gap is 50
        self.expiry = self._get_nearest_expiry()
        
        logger.info(f"✓ OptionsChainManager initialized | Expiry: {self.expiry}")
    
    def _get_nearest_expiry(self) -> str:
        """
        Get nearest Thursday expiry
        Format: DDMMMYY (e.g., 28DEC23)
        
        For now, using config value
        You can enhance this to automatically detect nearest Thursday
        """
        # Simple implementation: Use from config
        # Format: "28DEC23"
        # You can implement automatic expiry detection here
        
        # For now, extract from NIFTY FUT symbol
        fut_symbol = self.config.get('OPTIONS_NIFTY_FUT_SYMBOL', 'NIFTY24DECFUT')
        # Extract expiry from FUT symbol (e.g., NIFTY24DECFUT → 24DEC)
        # This is simplified - you should use proper date logic
        
        # Placeholder: Return current month expiry
        return "26DEC24"  # Update this based on actual expiry
    
    def get_atm_strike(self, fut_price: float) -> int:
        """
        Calculate ATM strike price
        Round to nearest 50
        
        Args:
            fut_price: Current NIFTY FUT price
            
        Returns:
            ATM strike price (e.g., 20000, 20050, etc.)
        """
        # Round to nearest 50
        atm_strike = round(fut_price / self.strike_gap) * self.strike_gap
        
        logger.debug(f"ATM Strike: {atm_strike} (FUT Price: {fut_price:.2f})")
        
        return int(atm_strike)
    
    def get_option_symbol(self, strike: int, option_type: str) -> str:
        """
        Generate option symbol
        
        Args:
            strike: Strike price (e.g., 20000)
            option_type: "CALL" or "PUT"
            
        Returns:
            Option symbol (e.g., "NIFTY26DEC2420000CE" or "NIFTY26DEC2420000PE")
        """
        # Determine CE or PE
        ce_pe = "CE" if option_type == "CALL" else "PE"
        
        # Format: NIFTY{expiry}{strike}{CE/PE}
        # Example: NIFTY26DEC2420000CE
        symbol = f"NIFTY{self.expiry}{strike}{ce_pe}"
        
        logger.info(f"Option Symbol: {symbol} ({option_type} @ {strike})")
        
        return symbol
    
    def get_option_price(self, symbol: str) -> float:
        """
        Get current option price from Kite API
        
        Args:
            symbol: Option symbol
            
        Returns:
            Current LTP of the option
        """
        try:
            # Get quote from Kite
            quote = self.kite.quote([f"{self.exchange}:{symbol}"])
            
            if quote and f"{self.exchange}:{symbol}" in quote:
                ltp = quote[f"{self.exchange}:{symbol}"]["last_price"]
                logger.debug(f"{symbol} LTP: {ltp:.2f}")
                return ltp
            
            logger.warning(f"Could not get price for {symbol}")
            return 0
            
        except Exception as e:
            logger.error(f"Error getting option price for {symbol}: {e}")
            return 0
    
    def get_instrument_token(self, symbol: str) -> Optional[int]:
        """
        Get instrument token for option symbol
        
        Args:
            symbol: Option symbol
            
        Returns:
            Instrument token or None
        """
        try:
            # Search for instrument
            instruments = self.kite.instruments(self.exchange)
            
            for instrument in instruments:
                if instrument['tradingsymbol'] == symbol:
                    return instrument['instrument_token']
            
            logger.warning(f"Instrument token not found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting instrument token for {symbol}: {e}")
            return None
