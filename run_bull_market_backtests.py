import pandas as pd
import numpy as np
from backtesting import Backtest
from data import fetch_historical_ohlcv
from indicators import add_indicators
from signals import calculate_signals
from backtest import WhaleWhispererStrategy
from rich.console import Console
from rich.table import Table
import warnings
import time

warnings.filterwarnings('ignore')

def run_bull_backtest(symbol: str, timeframe: str):
    # Fetch 1000 days of data to cover Oct 2023 to Apr 2024
    df_raw = fetch_historical_ohlcv(symbol, timeframe=timeframe, since_days=1000)
    if df_raw.empty or len(df_raw) < 100:
        return None
        
    # Filter for the bull market period: Oct 1, 2023 to Apr 1, 2024
    start_date = pd.to_datetime("2023-10-01")
    end_date = pd.to_datetime("2024-04-01")
    
    # Run indicators and signals on full data so boundaries are calculated properly
    df_ind = add_indicators(df_raw)
    df_signals = calculate_signals(df_ind)
    
    # Filter the signals DataFrame for the bull market period
    df_signals['timestamp'] = pd.to_datetime(df_signals['timestamp'])
    df_filtered = df_signals[(df_signals['timestamp'] >= start_date) & (df_signals['timestamp'] <= end_date)].copy()
    
    if len(df_filtered) < 50:
        return None
        
    # Prep for backtesting.py
    df_backtest = df_filtered.copy()
    df_backtest.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)
    df_backtest.set_index('timestamp', inplace=True)
    df_backtest.index = pd.to_datetime(df_backtest.index)
    
    bt = Backtest(
        df_backtest, 
        WhaleWhispererStrategy, 
        cash=1000000, 
        commission=0.0004,
        exclusive_orders=True
    )
    
    stats = bt.run()
    return stats, len(df_filtered)

def main():
    console = Console()
    coins = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT"]
    timeframes = ["1h", "4h", "1d"]
    
    console.print("[bold green]🐂 Starting WhaleWhisperer Bull Market Backtesting...[/bold green]")
    console.print("[dim]Period: Oct 1, 2023 to Apr 1, 2024 (180 days of pure uptrend)[/dim]\n")
    
    results = []
    
    for symbol in coins:
        for tf in timeframes:
            console.print(f"[bold yellow]Running bull market backtest for {symbol} ({tf})...[/bold yellow]")
            try:
                res = run_bull_backtest(symbol, tf)
                if res is not None:
                    stats, num_candles = res
                    win_rate = stats['Win Rate [%]']
                    win_rate_val = win_rate if not pd.isna(win_rate) else 0.0
                    
                    results.append({
                        'symbol': symbol,
                        'tf': tf,
                        'candles': num_candles,
                        'trades': int(stats['# Trades']),
                        'win_rate': win_rate_val,
                        'return': stats['Return [%]'],
                        'bh_return': stats['Buy & Hold Return [%]'],
                        'max_dd': stats['Max. Drawdown [%]'],
                        'sharpe': stats['Sharpe Ratio']
                    })
                # Respect rate limit
                time.sleep(1.0)
            except Exception as e:
                console.print(f"[bold red]Failed for {symbol} ({tf}): {e}[/bold red]")
                
    table = Table(title="🐂 WhaleWhisperer Bull Market Summary (Oct 2023 - Apr 2024)", header_style="bold green", border_style="dim")
    table.add_column("Symbol", style="cyan")
    table.add_column("Timeframe", style="white")
    table.add_column("Trades", justify="right", style="magenta")
    table.add_column("Win Rate", justify="right")
    table.add_column("Strategy Return", justify="right")
    table.add_column("Buy & Hold", justify="right")
    table.add_column("Max Drawdown", justify="right", style="red")
    table.add_column("Sharpe Ratio", justify="right")
    
    for r in results:
        wr_color = "green" if r['win_rate'] >= 45 else ("yellow" if r['win_rate'] >= 30 else "red")
        wr_str = f"[{wr_color}]{r['win_rate']:.2f}%[/]"
        
        ret_color = "green" if r['return'] > 0 else "red"
        ret_str = f"[{ret_color}]{r['return']:.2f}%[/]"
        
        bh_color = "green" if r['bh_return'] > 0 else "red"
        bh_str = f"[{bh_color}]{r['bh_return']:.2f}%[/]"
        
        sharpe_str = f"{r['sharpe']:.2f}" if not pd.isna(r['sharpe']) else "N/A"
        
        table.add_row(
            r['symbol'],
            r['tf'],
            str(r['trades']),
            wr_str,
            ret_str,
            bh_str,
            f"{r['max_dd']:.2f}%",
            sharpe_str
        )
        
    console.print("\n")
    console.print(table)
    console.print("\n[bold green]✅ Bull market backtesting completed successfully![/bold green]")

if __name__ == "__main__":
    main()
