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
            end = datetime.now()
            
            # First try to get minute data for recent days (free accounts have limited access)
            start = end - timedelta(days=5)
            
            try:
                bars = self.api.get_bars(
                    self.symbol,
                    TimeFrame.Minute,
                    start=start.strftime('%Y-%m-%d'),
                    end=end.strftime('%Y-%m-%d'),
                    limit=1000
                ).df
                
                if not bars.empty and len(bars) >= self.long_window:
                    logger.info(f"Retrieved {len(bars)} minute bars for {self.symbol}")
                    return bars
                else:
                    logger.warning("Insufficient minute data, trying daily data...")
                    
            except Exception as minute_error:
                # Check if this is a subscription error
                if "subscription" in str(minute_error).lower() or "sip" in str(minute_error).lower():
                    logger.warning(f"Minute data unavailable (subscription does not permit querying recent SIP data), falling back to daily data")
                else:
                    logger.warning(f"Minute data unavailable ({minute_error}), falling back to daily data")
            
            # Try recent daily data first
            start = end - timedelta(days=60)
            
            try:
                bars = self.api.get_bars(
                    self.symbol,
                    TimeFrame.Day,
                    start=start.strftime('%Y-%m-%d'),
                    end=end.strftime('%Y-%m-%d'),
                    limit=100
                ).df
                
                if not bars.empty and len(bars) >= self.long_window:
                    logger.info(f"Retrieved {len(bars)} daily bars for {self.symbol}")
                    return bars
                else:
                    logger.warning("Insufficient recent daily data, trying older historical data...")
                    
            except Exception as daily_error:
                # Check if this is also a subscription error
                if "subscription" in str(daily_error).lower() or "sip" in str(daily_error).lower():
                    logger.warning(f"Recent daily data unavailable (subscription does not permit querying recent SIP data), falling back to older historical data")
                else:
                    logger.warning(f"Recent daily data unavailable ({daily_error}), falling back to older historical data")
            
            # Fallback to older historical data (typically available for free accounts)
            # Use data from 3-6 months ago which should be available without premium subscription
            end_historical = end - timedelta(days=90)  # 3 months ago
            start_historical = end_historical - timedelta(days=60)  # Additional 60 days back
            
            logger.info(f"Attempting to fetch historical data from {start_historical.strftime('%Y-%m-%d')} to {end_historical.strftime('%Y-%m-%d')}")
            
            bars = self.api.get_bars(
                self.symbol,
                TimeFrame.Day,
                start=start_historical.strftime('%Y-%m-%d'),
                end=end_historical.strftime('%Y-%m-%d'),
                limit=100
            ).df
            
            if bars.empty:
                logger.error("No historical market data received - unable to proceed")
                return None
                
            logger.info(f"Retrieved {len(bars)} historical daily bars for {self.symbol}")
            logger.info("Note: Using historical data due to subscription limitations with recent SIP data")
            return bars
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return None
    
    def calculate_signals(self, data):
        """Calculate moving averages and trading signals"""
        if data is None or len(data) < self.long_window:
            logger.warning("Insufficient data for signal calculation")
            return None, None, None
        
        # Check if we're using historical data (more than 30 days old)
        latest_date = pd.to_datetime(data.index[-1])
        days_old = (datetime.now() - latest_date).days
        if days_old > 30:
            logger.info(f"Using historical data from {latest_date.strftime('%Y-%m-%d')} ({days_old} days old)")
            logger.info("Note: Signals are based on historical data due to subscription limitations")
        
        # Calculate moving averages
        data['short_ma'] = data['close'].rolling(window=self.short_window).mean()
        data['long_ma'] = data['close'].rolling(window=self.long_window).mean()
        
        # Calculate signal (1 = buy, -1 = sell, 0 = hold)
        data['signal'] = 0
        data.iloc[self.short_window:, data.columns.get_loc('signal')] = np.where(
            data['short_ma'].iloc[self.short_window:] > data['long_ma'].iloc[self.short_window:], 1, -1
        )
        
        # Detect crossover points
        data['position'] = data['signal'].diff()
        
        current_signal = data['signal'].iloc[-1]
        current_position = data['position'].iloc[-1]
        current_price = data['close'].iloc[-1]
        
        logger.info(f"Data date: {latest_date.strftime('%Y-%m-%d')}")
        logger.info(f"Historical price: ${current_price:.2f}")
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
        
        # Check if we're using historical data (more than 30 days old)
        latest_date = pd.to_datetime(data.index[-1])
        days_old = (datetime.now() - latest_date).days
        
        # Get current position
        current_qty = self.get_current_position()
        logger.info(f"Current position: {current_qty} shares")
        
        # Skip trading if using very old historical data
        if days_old > 30:
            logger.info(f"Skipping trading - using historical data from {days_old} days ago")
            logger.info("Trading signals are for educational/testing purposes only when using historical data")
        else:
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