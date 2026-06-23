import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt

# Import module functions
from data import fetch_ohlcv, normalize_symbol
from indicators import add_indicators
from signals import generate_signal
from explainer import get_explanation
from backtest import run_backtest_report

# Reconfigure stdout for Windows console emoji support
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

console = Console()

def display_welcome():
    welcome_text = Text()
    welcome_text.append("🐋 Welcome to WhaleWhisperer Quant Engine\n", style="bold cyan")
    welcome_text.append("Local multi-indicator scoring & LLM analysis system", style="italic white")
    
    console.print(Panel(
        welcome_text,
        title="[bold green]WhaleWhisperer v2.0[/bold green]",
        border_style="cyan",
        expand=False
    ))

def display_signal(sig_info, symbol, timeframe):
    # Set signal color
    sig = sig_info['signal']
    if sig == 'LONG':
        sig_color = "bold green"
        sig_icon = "📈 LONG"
    elif sig == 'SHORT':
        sig_color = "bold red"
        sig_icon = "📉 SHORT"
    else:
        sig_color = "bold yellow"
        sig_icon = "⚖️ NEUTRAL"

    # 1. Main Signal Panel
    signal_text = Text()
    signal_text.append(f"Pair: {symbol} ({timeframe})\n", style="bold white")
    signal_text.append(f"Price: ${sig_info['close']:,.2f}\n\n", style="white")
    signal_text.append(f"SIGNAL: ", style="bold white")
    signal_text.append(f"{sig_icon}\n", style=sig_color)
    signal_text.append(f"Final Score: {sig_info['final_score']:+g}", style="bold cyan")
    
    console.print(Panel(
        signal_text,
        title="[bold]TRADING SIGNAL[/bold]",
        border_style=sig_color.split()[-1],
        expand=False
    ))

    # 2. Indicators Summary Table
    table = Table(title="[bold]Technical Indicators Summary[/bold]", border_style="dim")
    table.add_column("Indicator", style="cyan")
    table.add_column("Value/State", style="white")
    table.add_column("Score contribution", justify="right")

    ind = sig_info['indicators']
    
    # EMA Crossover
    ema_state = "Bullish Cross" if sig_info['ema_score'] > 0 else ("Bearish Cross" if sig_info['ema_score'] < 0 else "No Cross")
    table.add_row("EMA 9/21 Crossover", ema_state, f"{sig_info['ema_score']:+g}")
    
    # RSI
    rsi_val = f"{ind['rsi']:.2f}"
    rsi_style = "green" if ind['rsi'] < 35 else ("red" if ind['rsi'] > 65 else "white")
    table.add_row("RSI (14)", Text(rsi_val, style=rsi_style), f"{sig_info['rsi_score']:+g}")
    
    # MACD
    macd_state = "Bullish Cross" if sig_info['macd_score'] > 0 else ("Bearish Cross" if sig_info['macd_score'] < 0 else "No Cross")
    table.add_row("MACD Crossover", macd_state, f"{sig_info['macd_score']:+g}")
    
    # Bollinger Bands
    bb_state = "Below Lower Band" if ind['close_bb_lower'] else ("Above Upper Band" if ind['close_bb_upper'] else "Inside Bands")
    bb_style = "green" if ind['close_bb_lower'] else ("red" if ind['close_bb_upper'] else "white")
    table.add_row("Bollinger Bands", Text(bb_state, style=bb_style), f"{sig_info['bb_score']:+g}")
    
    # Squeeze Momentum
    sqz_state = "Squeeze ON" if ind['sqz_on'] else "Squeeze OFF"
    sqz_style = "yellow" if ind['sqz_on'] else "white"
    sqz_desc = f"{sqz_state} (Mom: {ind['sqz_mom']:.1f})"
    table.add_row("Squeeze Momentum", Text(sqz_desc, style=sqz_style), f"{sig_info['sqz_score']:+g}")
    
    # Base Score Subtotal
    table.add_section()
    table.add_row("[bold]Base Score[/bold]", "", f"[bold]{sig_info['base_score']:+g}[/bold]")
    
    # Volume Confirmation
    vol_state = "HIGH (1.5x SMA ✅)" if ind['volume_confirmed'] else "LOW (Below 1.5x SMA ⚠️)"
    vol_score_effect = "Score * 1.5" if ind['volume_confirmed'] else "No multiplier"
    table.add_row("Volume Confirmation", vol_state, vol_score_effect)
    
    # Final Score
    table.add_section()
    table.add_row("[bold]Final Score[/bold]", "", f"[bold {sig_color.split()[-1]}]{sig_info['final_score']:+g}[/bold]")
    
    console.print(table)

def main():
    display_welcome()
    
    while True:
        # Prompt for coin
        symbol_input = Prompt.ask("\n[bold green]Enter crypto pair[/bold green] (e.g. BTC, ETH/USDT, SOL)", default="BTC")
        symbol = normalize_symbol(symbol_input)
        
        # Prompt for timeframe
        timeframe = Prompt.ask(
            "[bold green]Select timeframe[/bold green]", 
            choices=["1m", "5m", "15m", "1h", "4h", "1d"], 
            default="1h"
        )
        
        # Fetching & Calculation Spinner
        with console.status(f"[bold yellow]Fetching live data and running indicators for {symbol}...[/bold yellow]"):
            try:
                # Fetch 100 candles to compute indicators
                df = fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
                if df.empty or len(df) < 50:
                    console.print(f"[bold red]Error:[/bold red] Could not fetch sufficient data for {symbol}.")
                    continue
                    
                # Compute Indicators
                df_ind = add_indicators(df)
                
                # Generate signal
                sig_info = generate_signal(df_ind)
            except Exception as e:
                console.print(f"[bold red]Exception occurred:[/bold red] {e}")
                continue
        
        # Display Signal Details
        display_signal(sig_info, symbol, timeframe)
        
        # LLM Explanation Spinner
        with console.status("[bold magenta]Requesting AI explanation from Groq...[/bold magenta]"):
            explanation = get_explanation(symbol, timeframe, sig_info['signal'], sig_info['final_score'], sig_info['indicators'])
            
        console.print(Panel(
            explanation,
            title="[bold magenta]🤖 AI WHISPER (Llama-3)[/bold magenta]",
            border_style="magenta",
            expand=False
        ))
        
        # Option to run backtest
        run_bt = Prompt.ask("\nRun a 6-month historical backtest for this pair? (y/n)", choices=["y", "n"], default="n")
        if run_bt == "y":
            with console.status(f"[bold blue]Running backtest for {symbol} on {timeframe} timeframe (180 days)...[/bold blue]"):
                try:
                    run_backtest_report(symbol, timeframe=timeframe, since_days=180)
                except Exception as e:
                    console.print(f"[bold red]Backtest failed:[/bold red] {e}")
                    
        # Option to analyze another or exit
        another = Prompt.ask("\nAnalyze another coin? (y/n)", choices=["y", "n"], default="y")
        if another == "n":
            console.print("[bold cyan]Happy trading! 🐋[/bold cyan]")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Exiting WhaleWhisperer.[/bold red]")
        sys.exit(0)
