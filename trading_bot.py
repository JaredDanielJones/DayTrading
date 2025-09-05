#!/usr/bin/env python3
"""
Simple Day Trading Bot using Alpaca Paper Trading API
Implements a Moving Average Crossover Strategy
"""

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from alpaca_trade_api import REST, TimeFrame
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleMovingAverageBot:
    """
    A simple day trading bot that uses moving average crossover strategy.
    
    Strategy:
    - When 5-period MA crosses above 20-period MA: BUY signal
    - When 5-period MA crosses below 20-period MA: SELL signal
    - Only trades during market hours
    - Uses paper trading only for safety
    """
    
    def __init__(self):
        # Initialize Alpaca API (Paper Trading)
        self.api = REST(
            key_id=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            base_url='https://paper-api.alpaca.markets'  # Paper trading URL
        )
        
        # Trading parameters
        self.symbol = 'SPY'  # S&P 500 ETF - liquid and safe for testing
        self.short_window = 5   # Short-term moving average period
        self.long_window = 20   # Long-term moving average period
        self.position_size = 10  # Number of shares to trade
        
        logger.info(f"Initialized trading bot for {self.symbol}")
        logger.info(f"Using paper trading account: {self.api.get_account().account_number}")
    
    def get_market_data(self):
        """Fetch recent market data for analysis"""
        try:
            # Get bars for the last 30 days to have enough data for moving averages
            end = datetime.now()
            start = end - timedelta(days=30)
            
            bars = self.api.get_bars(
                self.symbol,
                TimeFrame.Minute,  # 1-minute bars for day trading
                start=start.strftime('%Y-%m-%d'),
                end=end.strftime('%Y-%m-%d'),
                limit=1000
            ).df
            
            if bars.empty:
                logger.warning("No market data received")
                return None
                
            logger.info(f"Retrieved {len(bars)} bars for {self.symbol}")
            return bars
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return None
    
    def calculate_signals(self, data):
        """Calculate moving averages and trading signals"""
        if data is None or len(data) < self.long_window:
            logger.warning("Insufficient data for signal calculation")
            return None, None, None
        
        # Calculate moving averages
        data['short_ma'] = data['close'].rolling(window=self.short_window).mean()
        data['long_ma'] = data['close'].rolling(window=self.long_window).mean()
        
        # Calculate signal (1 = buy, -1 = sell, 0 = hold)
        data['signal'] = 0
        data['signal'][self.short_window:] = np.where(
            data['short_ma'][self.short_window:] > data['long_ma'][self.short_window:], 1, -1
        )
        
        # Detect crossover points
        data['position'] = data['signal'].diff()
        
        current_signal = data['signal'].iloc[-1]
        current_position = data['position'].iloc[-1]
        current_price = data['close'].iloc[-1]
        
        logger.info(f"Current price: ${current_price:.2f}")
        logger.info(f"Short MA: ${data['short_ma'].iloc[-1]:.2f}")
        logger.info(f"Long MA: ${data['long_ma'].iloc[-1]:.2f}")
        logger.info(f"Signal: {current_signal}, Position change: {current_position}")
        
        return current_signal, current_position, current_price
    
    def get_current_position(self):
        """Get current position in the symbol"""
        try:
            positions = self.api.list_positions()
            for position in positions:
                if position.symbol == self.symbol:
                    return int(position.qty)
            return 0
        except Exception as e:
            logger.error(f"Error getting current position: {e}")
            return 0
    
    def place_order(self, side, qty):
        """Place a market order"""
        try:
            order = self.api.submit_order(
                symbol=self.symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='day'
            )
            logger.info(f"Order placed: {side} {qty} shares of {self.symbol}")
            logger.info(f"Order ID: {order.id}")
            return order
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def is_market_open(self):
        """Check if market is currently open"""
        try:
            clock = self.api.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Error checking market status: {e}")
            return False
    
    def run_strategy(self):
        """Main strategy execution"""
        logger.info("=" * 50)
        logger.info("Running trading strategy...")
        
        # Check if market is open
        if not self.is_market_open():
            logger.info("Market is closed. No trading.")
            return
        
        # Get market data
        data = self.get_market_data()
        if data is None:
            return
        
        # Calculate signals
        signal, position_change, current_price = self.calculate_signals(data)
        if signal is None:
            return
        
        # Get current position
        current_qty = self.get_current_position()
        logger.info(f"Current position: {current_qty} shares")
        
        # Execute trades based on signals
        if position_change == 2:  # Signal changed from -1 to 1 (buy signal)
            if current_qty <= 0:  # Not already long
                # Close any short position first
                if current_qty < 0:
                    self.place_order('buy', abs(current_qty))
                # Open long position
                self.place_order('buy', self.position_size)
                logger.info("BUY signal executed")
                
        elif position_change == -2:  # Signal changed from 1 to -1 (sell signal)
            if current_qty >= 0:  # Not already short
                # Close any long position first
                if current_qty > 0:
                    self.place_order('sell', current_qty)
                # Open short position (only if allowed by your broker)
                # Note: For safety, we'll just close positions instead of shorting
                logger.info("SELL signal executed (position closed)")
        
        else:
            logger.info("No trading signal - holding current position")
        
        # Log account status
        try:
            account = self.api.get_account()
            logger.info(f"Account equity: ${float(account.equity):.2f}")
            logger.info(f"Buying power: ${float(account.buying_power):.2f}")
        except Exception as e:
            logger.error(f"Error getting account info: {e}")

def main():
    """Main execution function"""
    logger.info("Starting Alpaca Paper Trading Bot")
    
    # Verify environment variables
    if not os.getenv('ALPACA_API_KEY') or not os.getenv('ALPACA_SECRET_KEY'):
        logger.error("Missing Alpaca API credentials. Please set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables.")
        return
    
    try:
        bot = SimpleMovingAverageBot()
        bot.run_strategy()
        logger.info("Strategy execution completed")
    except Exception as e:
        logger.error(f"Bot execution failed: {e}")
        raise

if __name__ == "__main__":
    main()