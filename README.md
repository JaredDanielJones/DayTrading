# DayTrading Bot

An automated day trading bot using Alpaca's paper trading API to safely test trading algorithms without risking real money.

## 🚨 SAFETY FIRST 🚨

This bot is configured to use **PAPER TRADING ONLY**. It will never use real money. The bot connects to Alpaca's paper trading environment where you can test strategies with virtual money.

## Trading Algorithm: Simple Moving Average Crossover

The bot implements a classic and simple moving average crossover strategy:

### How It Works:
1. **Short-term Moving Average (5-period)**: Tracks recent price trends
2. **Long-term Moving Average (20-period)**: Tracks longer-term price trends
3. **Buy Signal**: When the short MA crosses above the long MA
4. **Sell Signal**: When the short MA crosses below the long MA

### Why This Strategy:
- **Simple to understand**: Easy to verify and debug
- **Well-tested**: Classic strategy used by many traders
- **Risk-aware**: Uses clear entry/exit signals
- **Conservative**: Only trades one symbol (SPY - S&P 500 ETF)

### Trading Rules:
- Only trades during market hours (9:30 AM - 4:00 PM ET)
- Uses small position sizes (10 shares) for testing
- Automatically closes positions on sell signals (no shorting for safety)
- Logs all activities for review

## Setup Instructions

### 1. Get Alpaca Paper Trading Account
1. Sign up for a free account at [Alpaca](https://alpaca.markets/)
2. Go to the dashboard and get your **Paper Trading** API keys
3. **Important**: Make sure you're using paper trading keys, not live trading keys

### 2. Configure GitHub Secrets
Add these secrets to your GitHub repository:
- `ALPACA_API_KEY`: Your paper trading API key
- `ALPACA_SECRET_KEY`: Your paper trading secret key

To add secrets:
1. Go to your GitHub repository
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add both keys

### 3. Local Development Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd DayTrading

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env file with your Alpaca paper trading keys
nano .env
```

### 4. Manual Testing
```bash
# Run the bot once manually
python trading_bot.py
```

## Automated Execution

The bot runs automatically every 5 minutes during market hours via GitHub Actions:
- **Schedule**: Every 5 minutes from 9:30 AM - 4:00 PM ET (Monday-Friday)
- **Logs**: Trading logs are automatically saved as artifacts
- **Manual trigger**: You can manually run the workflow from the Actions tab

## File Structure

```
DayTrading/
├── trading_bot.py           # Main trading bot script
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variable template
├── .github/
│   └── workflows/
│       └── trading.yml     # GitHub Actions workflow
└── README.md               # This documentation
```

## Monitoring Your Bot

### View Logs
1. Go to the Actions tab in GitHub
2. Click on the latest workflow run
3. Download the trading logs artifact

### Check Your Paper Account
- Log into your Alpaca paper trading dashboard
- Review positions, orders, and account balance
- All trades are simulated with virtual money

## Risk Management Features

✅ **Paper Trading Only**: Hardcoded to use paper trading API  
✅ **Small Position Sizes**: Only trades 10 shares at a time  
✅ **Single Symbol**: Only trades SPY (S&P 500 ETF)  
✅ **Market Hours Only**: No after-hours trading  
✅ **Comprehensive Logging**: All actions are logged  
✅ **No Leverage**: Simple buy/sell operations only  

## Customization

To modify the strategy, edit these parameters in `trading_bot.py`:

```python
self.symbol = 'SPY'          # Change trading symbol
self.short_window = 5        # Short MA period
self.long_window = 20        # Long MA period
self.position_size = 10      # Number of shares
```

## Disclaimer

This is for educational and testing purposes only. Past performance does not guarantee future results. Even though this uses paper trading, always understand the risks before implementing any trading strategy with real money.

## Next Steps

1. Monitor the bot's performance over several weeks
2. Analyze the trading logs to understand strategy effectiveness
3. Consider implementing additional risk management features
4. Experiment with different moving average periods
5. Add other technical indicators for more sophisticated strategies

Happy (paper) trading! 📈