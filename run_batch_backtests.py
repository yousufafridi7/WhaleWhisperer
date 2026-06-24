import pandas as pd
import numpy as np
from backtest import run_backtest_report
from rich.console import Console
from rich.table import Table
import warnings

# Suppress warnings for clean output
warnings.filterwarnings('ignore')

def main():
    console = Console()
    
    coins = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT"]
    timeframes = ["1h", "4h", "1d"]
    period_days = 180
    
    console.print("[bold cyan]🚀 Starting WhaleWhisperer Batch Backtesting...[/bold cyan]")
    console.print(f"[dim]Period: {period_days} Days | Commission: 0.04%[/dim]\n")
    
    results = []
    
    for symbol in coins:
        for tf in timeframes:
            console.print(f"[bold yellow]Running backtest for {symbol} ({tf})...[/bold yellow]")
            try:
                stats = run_backtest_report(symbol, timeframe=tf, since_days=period_days)
                if stats is not None:
                    win_rate = stats['Win Rate [%]']
                    win_rate_val = win_rate if not pd.isna(win_rate) else 0.0
                    
                    results.append({
                        'symbol': symbol,
                        'tf': tf,
                        'trades': int(stats['# Trades']),
                        'win_rate': win_rate_val,
                        'return': stats['Return [%]'],
                        'bh_return': stats['Buy & Hold Return [%]'],
                        'max_dd': stats['Max. Drawdown [%]'],
                        'sharpe': stats['Sharpe Ratio']
                    })
            except Exception as e:
                console.print(f"[bold red]Failed for {symbol} ({tf}): {e}[/bold red]")
                
    # Create rich table of results
    table = Table(title=f"🐋 WhaleWhisperer Batch Backtest Summary (180 Days)", header_style="bold magenta", border_style="dim")
    table.add_column("Symbol", style="cyan")
    table.add_column("Timeframe", style="white")
    table.add_column("Trades", justify="right", style="magenta")
    table.add_column("Win Rate", justify="right")
    table.add_column("Strategy Return", justify="right")
    table.add_column("Buy & Hold", justify="right")
    table.add_column("Max Drawdown", justify="right", style="red")
    table.add_column("Sharpe Ratio", justify="right")
    
    for r in results:
        # Style win rate (green if >= 45%, yellow if >= 30%, red if < 30%)
        wr_color = "green" if r['win_rate'] >= 45 else ("yellow" if r['win_rate'] >= 30 else "red")
        wr_str = f"[{wr_color}]{r['win_rate']:.2f}%[/]"
        
        # Style return (green if positive, red if negative)
        ret_color = "green" if r['return'] > 0 else "red"
        ret_str = f"[{ret_color}]{r['return']:.2f}%[/]"
        
        # Style buy & hold
        bh_color = "green" if r['bh_return'] > 0 else "red"
        bh_str = f"[{bh_color}]{r['bh_return']:.2f}%[/]"
        
        # Sharpe ratio
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
    console.print("\n[bold green]✅ Batch backtesting completed successfully![/bold green]")

if __name__ == "__main__":
    main()
