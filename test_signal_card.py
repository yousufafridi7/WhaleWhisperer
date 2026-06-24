import pandas as pd
from data import fetch_ohlcv
from indicators import add_indicators
from signals import calculate_signals, generate_signal
from main import display_signal

def run_test():
    symbol = "ADA/USDT"
    timeframe = "1h"
    print(f"Fetching candles for {symbol} to run WhaleWhisperer V2...")
    
    df_raw = fetch_ohlcv(symbol, timeframe=timeframe, limit=300)
    df_ind = add_indicators(df_raw)
    
    # CASE 1: BEAR Mode (Simulated)
    sig_info_bear = generate_signal(df_ind)
    sig_info_bear['regime'] = 'BEAR'
    sig_info_bear['signal'] = 'LONG'
    close_val = sig_info_bear['close']
    atr_val = sig_info_bear.get('atr', 1.0)
    sig_info_bear['sl'] = close_val - 1.5 * atr_val
    sig_info_bear['tp'] = close_val + 3.0 * atr_val
    
    print("\n--- CASE 1: RENDERED SIGNAL CARD (BEAR MODE LONG) ---")
    display_signal(sig_info_bear, symbol, timeframe)
    
    # CASE 2: BULL Mode (Simulated)
    sig_info_bull = generate_signal(df_ind)
    sig_info_bull['regime'] = 'BULL'
    sig_info_bull['signal'] = 'LONG'
    sig_info_bull['sl'] = close_val - 2.0 * atr_val
    sig_info_bull['tp'] = close_val + 4.0 * atr_val
    
    print("\n--- CASE 2: RENDERED SIGNAL CARD (BULL MODE LONG) ---")
    display_signal(sig_info_bull, symbol, timeframe)

if __name__ == "__main__":
    run_test()
