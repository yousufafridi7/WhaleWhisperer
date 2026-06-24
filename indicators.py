import pandas as pd
import numpy as np

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes technical indicators on the DataFrame and appends them as new columns.
    Standardized columns added:
    - ema_9, ema_21
    - rsi
    - macd, macd_signal, macd_hist
    - bb_upper, bb_middle, bb_lower
    - sqz_mom, sqz_on
    - vol_sma
    """
    df = df.copy()
    
    # 1. EMA 9 and EMA 21
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
    
    # 2. RSI (14) - standard Wilder's/EMA smoothed
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 3. MACD (12, 26, 9)
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # 4. Bollinger Bands (20, 2)
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std(ddof=0)
    df['bb_upper'] = df['bb_middle'] + 2 * bb_std
    df['bb_lower'] = df['bb_middle'] - 2 * bb_std
    
    # 5. Volume SMA (20)
    df['vol_sma'] = df['volume'].rolling(window=20).mean()
    
    # 6. Squeeze Momentum (Lazybear version)
    # Calculate Keltner Channels (20, 1.5)
    tr0 = abs(df["high"] - df["low"])
    tr1 = abs(df["high"] - df["close"].shift())
    tr2 = abs(df["low"] - df["close"].shift())
    tr = pd.concat([tr0, tr1, tr2], axis=1).max(axis=1)
    range_ma = tr.rolling(window=20).mean()
    
    kc_upper = df['bb_middle'] + range_ma * 1.5
    kc_lower = df['bb_middle'] - range_ma * 1.5
    
    # Squeeze state: Bollinger Bands inside Keltner Channels
    df['sqz_on'] = ((df['bb_lower'] > kc_lower) & (df['bb_upper'] < kc_upper)).astype(int)
    
    # Squeeze Momentum Value (Linear Regression of price difference from average)
    highest_high = df['high'].rolling(window=20).max()
    lowest_low = df['low'].rolling(window=20).min()
    midline = (highest_high + lowest_low) / 2
    value = df['close'] - (midline + df['bb_middle']) / 2
    
    # Linear regression formula for rolling window
    n = 20
    x = np.arange(n)
    x_mean = x.mean()
    x_dev = x - x_mean
    var_x = (x_dev ** 2).sum()
    
    def get_lr_value(y):
        y_mean = y.mean()
        slope = np.dot(x_dev, y - y_mean) / var_x
        intercept = y_mean - slope * x_mean
        return slope * (n - 1) + intercept
        
    df['sqz_mom'] = value.rolling(window=n).apply(get_lr_value, raw=True)
    
    # 7. ATR (Average True Range) - 14 period (Wilder's smoothing)
    df['atr'] = tr.ewm(alpha=1/14, adjust=False).mean()
    
    # 8. SMA 200 for Market Regime Detector
    df['sma_200'] = df['close'].rolling(window=200).mean()
    
    return df

if __name__ == "__main__":
    # Test script for Phase 2 verification
    print("Testing Phase 2 Indicators Calculation...")
    try:
        from data import fetch_ohlcv
        df = fetch_ohlcv("BTC/USDT", timeframe="1h", limit=100)
        df_ind = add_indicators(df)
        
        print("\nLast 5 rows showing all indicator columns:")
        cols_to_print = ['timestamp', 'close', 'ema_9', 'ema_21', 'rsi', 'macd', 'macd_hist', 'bb_upper', 'bb_lower', 'sqz_mom', 'sqz_on', 'vol_sma', 'atr']
        print(df_ind[cols_to_print].tail(5))
        print("\nAll indicators successfully computed!")
    except Exception as e:
        print(f"Error during Phase 2 testing: {e}")
