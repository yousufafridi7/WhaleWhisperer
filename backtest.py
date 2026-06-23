import sys
import pandas as pd
from backtesting import Backtest, Strategy
from data import fetch_historical_ohlcv
from indicators import add_indicators
from signals import calculate_signals

# Fix Windows console encoding for emojis
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

class WhaleWhispererStrategy(Strategy):
    """
    Backtesting.py strategy implementing the rule-based signals of Phase 3.
    """
    def init(self):
        # Cache the signal column for speed
        self.signal = self.data.signal

    def next(self):
        sig = self.signal[-1]
        
        # Position execution based on rules
        if sig == 'LONG':
            # Close short position if open
            if self.position.is_short:
                self.position.close()
            # Open long position using 95% of equity
            if not self.position.is_long:
                self.buy(size=0.95)
                
        elif sig == 'SHORT':
            # Close long position if open
            if self.position.is_long:
                self.position.close()
            # Open short position using 95% of equity
            if not self.position.is_short:
                self.sell(size=0.95)

def run_backtest_report(symbol: str = "BTC/USDT", timeframe: str = "1h", since_days: int = 180):
    """
    Fetches historical data, calculates indicators + signals, runs the backtest, and prints the report.
    """
    print(f"Fetching historical {timeframe} data for {symbol} ({since_days} days)...")
    df_raw = fetch_historical_ohlcv(symbol, timeframe=timeframe, since_days=since_days)
    
    if df_raw.empty or len(df_raw) < 100:
        print("Not enough historical data fetched. Backtest failed.")
        return None
        
    print(f"Fetched {len(df_raw)} candles.")
    
    # Calculate indicators
    df_ind = add_indicators(df_raw)
    
    # Calculate signals
    df_signals = calculate_signals(df_ind)
    
    # Prep DataFrame for backtesting.py (requires capital columns and DatetimeIndex)
    df_backtest = df_signals.copy()
    df_backtest.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)
    
    df_backtest.set_index('timestamp', inplace=True)
    df_backtest.index = pd.to_datetime(df_backtest.index)
    
    # Run Backtest (Default cash: $10,000, commission: 0.04% - typical Binance futures fee)
    bt = Backtest(
        df_backtest, 
        WhaleWhispererStrategy, 
        cash=10000, 
        commission=0.0004,
        exclusive_orders=True
    )
    
    stats = bt.run()
    
    print("\n" + "="*40)
    print(f" 🐋 BACKTEST REPORT: {symbol} ({timeframe})")
    print(f" Period: {since_days} days | Candles: {len(df_backtest)}")
    print("="*40)
    print(f"  Final Equity:      ${stats['Equity Final [$]']:,.2f}")
    print(f"  Final Return:       {stats['Return [%]']:.2f}%")
    print(f"  Buy & Hold Return:  {stats['Buy & Hold Return [%]']:.2f}%")
    print(f"  Max Drawdown:       {stats['Max. Drawdown [%]']:.2f}%")
    print(f"  Total Trades:       {int(stats['# Trades'])}")
    print(f"  Win Rate:           {stats['Win Rate [%]']:.2f}%")
    print(f"  Sharpe Ratio:       {stats['Sharpe Ratio']:.2f}")
    print("="*40 + "\n")
    
    return stats

if __name__ == "__main__":
    # Test script for Phase 4 verification
    print("Testing Phase 4 Backtesting...")
    try:
        run_backtest_report("BTC/USDT", timeframe="1h", since_days=180)
        print("Phase 4 Backtesting verified successfully!")
    except Exception as e:
        print(f"Error during Phase 4 testing: {e}")
