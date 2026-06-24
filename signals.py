import pandas as pd
import numpy as np

def calculate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates rule-based signals and scores for each row in the DataFrame.
    Returns the DataFrame with additional columns:
    - ema_score, rsi_score, macd_score, bb_score, sqz_score
    - base_score, final_score, signal
    """
    df = df.copy()
    
    # Pre-shift columns for crossovers
    ema_9_prev = df['ema_9'].shift(1)
    ema_21_prev = df['ema_21'].shift(1)
    macd_hist_prev = df['macd_hist'].shift(1)
    sqz_mom_prev = df['sqz_mom'].shift(1)
    
    # 1. EMA Crossover Score (9 crosses above 21 -> +2, 9 crosses below 21 -> -2)
    ema_score = np.zeros(len(df))
    ema_score[(df['ema_9'] > df['ema_21']) & (ema_9_prev <= ema_21_prev)] = 2
    ema_score[(df['ema_9'] < df['ema_21']) & (ema_9_prev >= ema_21_prev)] = -2
    df['ema_score'] = ema_score
    
    # 2. RSI Score (RSI < 35 -> +2, RSI > 65 -> -2)
    rsi_score = np.zeros(len(df))
    rsi_score[df['rsi'] < 35] = 2
    rsi_score[df['rsi'] > 65] = -2
    df['rsi_score'] = rsi_score
    
    # 3. MACD Crossover Score (Bullish crossover -> +2, Bearish crossover -> -2)
    macd_score = np.zeros(len(df))
    macd_score[(df['macd_hist'] > 0) & (macd_hist_prev <= 0)] = 2
    macd_score[(df['macd_hist'] < 0) & (macd_hist_prev >= 0)] = -2
    df['macd_score'] = macd_score
    
    # 4. Bollinger Bands Score (Price below BB lower -> +1, above BB upper -> -1)
    bb_score = np.zeros(len(df))
    bb_score[df['close'] < df['bb_lower']] = 1
    bb_score[df['close'] > df['bb_upper']] = -1
    df['bb_score'] = bb_score
    
    # 5. Squeeze Momentum Firing Score (Firing bullish -> +3, bearish -> -3)
    sqz_score = np.zeros(len(df))
    sqz_score[(df['sqz_on'] == 0) & (df['sqz_mom'] > 0) & (df['sqz_mom'] > sqz_mom_prev)] = 3
    sqz_score[(df['sqz_on'] == 0) & (df['sqz_mom'] < 0) & (df['sqz_mom'] < sqz_mom_prev)] = -3
    df['sqz_score'] = sqz_score
    
    # Base Score sum
    df['base_score'] = df['ema_score'] + df['rsi_score'] + df['macd_score'] + df['bb_score'] + df['sqz_score']
    
    # 6. Volume Confirmation (Volume > 1.5x Volume SMA -> multiply score by 1.5)
    volume_mult = np.ones(len(df))
    volume_mult[df['volume'] > 1.5 * df['vol_sma']] = 1.5
    df['final_score'] = df['base_score'] * volume_mult
    
    # 6b. Market Regime Detection (BULL/BEAR based on SMA 200)
    regime = np.array(['BEAR'] * len(df), dtype=object)
    if 'sma_200' in df.columns:
        regime[(df['close'] > df['sma_200']) & df['sma_200'].notna()] = 'BULL'
    df['regime'] = regime
    
    # 7. Final Decision (Regime-based)
    signal = np.array(['NEUTRAL'] * len(df), dtype=object)
    
    # BULL Mode (Tighter neutral zone: >= 4 or <= -4)
    bull_mask = df['regime'] == 'BULL'
    signal[bull_mask & (df['final_score'] >= 4)] = 'LONG'
    signal[bull_mask & (df['final_score'] <= -4)] = 'SHORT'
    
    # BEAR Mode (As-is settings: >= 5 or <= -5)
    bear_mask = df['regime'] == 'BEAR'
    signal[bear_mask & (df['final_score'] >= 5)] = 'LONG'
    signal[bear_mask & (df['final_score'] <= -5)] = 'SHORT'
    
    df['signal'] = signal
    
    return df

def generate_signal(df: pd.DataFrame) -> dict:
    """
    Calculates signals and returns detailed signal information for the latest row.
    """
    df_signals = calculate_signals(df)
    latest = df_signals.iloc[-1]
    
    # Calculate dynamic SL/TP levels based on ATR and Market Regime
    sig = latest['signal']
    close_val = latest['close']
    atr_val = latest.get('atr', 0.0)
    regime_val = latest.get('regime', 'BEAR')
    
    sl_val = 0.0
    tp_val = 0.0
    
    if regime_val == 'BULL':
        # Wider TP (4.0x ATR), relaxed SL (2.0x ATR)
        if sig == 'LONG':
            sl_val = close_val - 2.0 * atr_val
            tp_val = close_val + 4.0 * atr_val
        elif sig == 'SHORT':
            sl_val = close_val + 2.0 * atr_val
            tp_val = close_val - 4.0 * atr_val
    else:
        # BEAR mode (as-is: 3.0x ATR TP, 1.5x ATR SL)
        if sig == 'LONG':
            sl_val = close_val - 1.5 * atr_val
            tp_val = close_val + 3.0 * atr_val
        elif sig == 'SHORT':
            sl_val = close_val + 1.5 * atr_val
            tp_val = close_val - 3.0 * atr_val
        
    return {
        'timestamp': latest['timestamp'],
        'close': latest['close'],
        'ema_score': latest['ema_score'],
        'rsi_score': latest['rsi_score'],
        'macd_score': latest['macd_score'],
        'bb_score': latest['bb_score'],
        'sqz_score': latest['sqz_score'],
        'base_score': latest['base_score'],
        'final_score': latest['final_score'],
        'signal': latest['signal'],
        'regime': regime_val,
        'atr': atr_val,
        'sl': sl_val,
        'tp': tp_val,
        'indicators': {
            'rsi': latest['rsi'],
            'macd_hist': latest['macd_hist'],
            'close_bb_lower': latest['close'] < latest['bb_lower'],
            'close_bb_upper': latest['close'] > latest['bb_upper'],
            'sqz_on': latest['sqz_on'],
            'sqz_mom': latest['sqz_mom'],
            'volume_confirmed': latest['volume'] > 1.5 * latest['vol_sma']
        }
    }

if __name__ == "__main__":
    # Test script for Phase 3 verification
    print("Testing Phase 3 Signal Engine...")
    try:
        from data import fetch_ohlcv
        from indicators import add_indicators
        
        df = fetch_ohlcv("BTC/USDT", timeframe="1h", limit=100)
        df_ind = add_indicators(df)
        sig_info = generate_signal(df_ind)
        
        print(f"\nTimestamp: {sig_info['timestamp']}")
        print(f"Close Price: ${sig_info['close']:,.2f}")
        print("\nScoring Details:")
        print(f"  EMA Crossover Score:  {sig_info['ema_score']:+g}")
        print(f"  RSI Score:            {sig_info['rsi_score']:+g}")
        print(f"  MACD Crossover Score: {sig_info['macd_score']:+g}")
        print(f"  Bollinger Band Score: {sig_info['bb_score']:+g}")
        print(f"  Squeeze Score:        {sig_info['sqz_score']:+g}")
        print(f"  -----------------------------")
        print(f"  Base Score:           {sig_info['base_score']:+g}")
        print(f"  Final Score (w/ Vol): {sig_info['final_score']:+g}")
        print(f"\nFinal Signal: {sig_info['signal']}")
        
        print("\nPhase 3 Signal Engine verified successfully!")
    except Exception as e:
        print(f"Error during Phase 3 testing: {e}")
