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
    regime = sig_info.get('regime', 'BEAR')
    regime_color = "green" if regime == 'BULL' else "red"
    regime_emoji = "🐂" if regime == 'BULL' else "🐻"
    
    signal_text = Text()
    signal_text.append(f"Pair: {symbol} ({timeframe})\n", style="bold white")
    signal_text.append(f"Price: ${sig_info['close']:,.2f}\n", style="white")
    signal_text.append(f"Regime: ", style="bold white")
    signal_text.append(f"{regime_emoji} {regime} Mode\n\n", style=f"bold {regime_color}")
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
    table.add_row("[bold]Final Score[/bold]", "", f"[{sig_color}]{sig_info['final_score']:+g}[/]")
    
    console.print(table)
    
    # 2b. Trade Setup Card (only for active LONG/SHORT signals)
    if sig_info['signal'] in ['LONG', 'SHORT']:
        setup_text = Text()
        action = "BUY (LONG)" if sig_info['signal'] == 'LONG' else "SELL (SHORT)"
        action_style = "bold green" if sig_info['signal'] == 'LONG' else "bold red"
        regime_val = sig_info.get('regime', 'BEAR')
        
        tp_mult = "4.0x" if regime_val == 'BULL' else "3.0x"
        sl_mult = "2.0x" if regime_val == 'BULL' else "1.5x"
        rr_ratio = "1:2.0"  # Always 1:2 ratio
        
        setup_text.append("Action:          ", style="bold white")
        setup_text.append(f"{action}\n", style=action_style)
        
        setup_text.append("Optimal Entry:   ", style="bold white")
        setup_text.append(f"${sig_info['close']:,.2f}\n", style="bold cyan")
        
        setup_text.append("Take Profit (TP):", style="bold white")
        setup_text.append(f"${sig_info['tp']:,.2f}", style="bold green")
        setup_text.append(f" ({tp_mult} ATR target)\n", style="dim")
        
        setup_text.append("Stop Loss (SL):  ", style="bold white")
        setup_text.append(f"${sig_info['sl']:,.2f}", style="bold red")
        setup_text.append(f" ({sl_mult} ATR protection)\n\n", style="dim")
        
        setup_text.append("Risk/Reward:     ", style="bold white")
        setup_text.append(f"{rr_ratio} ({regime_val} Mode Adjusted)", style="bold yellow")
        
        console.print(Panel(
            setup_text,
            title="[bold green]🎯 ACTIVE TRADE SETUP[/bold green]" if sig_info['signal'] == 'LONG' else "[bold red]🎯 ACTIVE TRADE SETUP[/bold red]",
            border_style="green" if sig_info['signal'] == 'LONG' else "red",
            expand=False
        )),

def main():
    display_welcome()
    
    while True:
        # Prompt for coin (SOL removed from defaults/examples)
        symbol_input = Prompt.ask("\n[bold green]Enter crypto pair[/bold green] (e.g. BTC, ETH/USDT, ADA)", default="BTC")
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
                # Fetch 300 candles to ensure enough history for SMA 200
                df = fetch_ohlcv(symbol, timeframe=timeframe, limit=300)
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
        with console.status("[bold magenta]Requesting AI explanation from Gemini...[/bold magenta]"):
            explanation = get_explanation(symbol, timeframe, sig_info['signal'], sig_info['final_score'], sig_info['indicators'])
            
        console.print(Panel(
            Text(explanation),
            title="[bold magenta]🤖 AI WHISPER (Gemini 2.5 Flash)[/bold magenta]",
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
