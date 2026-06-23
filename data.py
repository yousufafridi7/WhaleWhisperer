import time
import ccxt
import pandas as pd
from datetime import datetime

def normalize_symbol(symbol: str) -> str:
    """
    Normalizes input symbol string to standard CCXT Binance pair format (e.g. BTC/USDT).
    """
    symbol = symbol.upper().strip().replace("-", "/")
    if "/" not in symbol:
        if symbol.endswith("USDT"):
            symbol = f"{symbol[:-4]}/USDT"
        elif symbol.endswith("BUSD"):
            symbol = f"{symbol[:-4]}/BUSD"
        elif symbol.endswith("USDC"):
            symbol = f"{symbol[:-4]}/USDC"
        else:
            symbol = f"{symbol}/USDT"
    return symbol

def fetch_ohlcv(symbol: str, timeframe: str = '1h', limit: int = 50) -> pd.DataFrame:
    """
    Fetches current OHLCV data from Binance using CCXT.
    No API keys required.
    Returns a pandas DataFrame.
    """
    norm_symbol = normalize_symbol(symbol)
    exchange = ccxt.binance({
        'enableRateLimit': True,
    })
    
    # Fetch candles from Binance
    ohlcv = exchange.fetch_ohlcv(norm_symbol, timeframe=timeframe, limit=limit)
    
    # Create DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Convert timestamp to datetime (UTC)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Ensure numeric types
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    return df

def fetch_historical_ohlcv(symbol: str, timeframe: str = '1h', since_days: int = 180) -> pd.DataFrame:
    """
    Fetches historical OHLCV data in pages from Binance to support backtesting.
    since_days: Number of days of history to fetch.
    """
    norm_symbol = normalize_symbol(symbol)
    exchange = ccxt.binance({
        'enableRateLimit': True,
    })
    
    # Calculate starting timestamp in milliseconds
    since_timestamp = exchange.milliseconds() - since_days * 24 * 60 * 60 * 1000
    all_candles = []
    
    limit = 1000  # Binance max limit per fetch
    current_since = since_timestamp
    
    while True:
        try:
            candles = exchange.fetch_ohlcv(norm_symbol, timeframe=timeframe, since=current_since, limit=limit)
            if not candles:
                break
            
            all_candles.extend(candles)
            
            last_timestamp = candles[-1][0]
            if last_timestamp == current_since:
                break
            current_since = last_timestamp + 1
            
            # Respect rate limit
            time.sleep(exchange.rateLimit / 1000.0)
            
            if len(candles) < limit:
                break
        except Exception as e:
            # If rate limit or network issues, wait and try once or break
            print(f"Error fetching page: {e}")
            break
            
    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df.drop_duplicates(subset=['timestamp'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    return df

if __name__ == "__main__":
    # Test script for Phase 1 verification
    print("Testing Phase 1 Data Fetching...")
    try:
        df = fetch_ohlcv("BTC/USDT", timeframe="1h", limit=50)
        print("\nLast 50 candles for BTC/USDT on 1h timeframe:")
        print(df)
        print(f"\nShape of DataFrame: {df.shape}")
        print("Phase 1 Data Layer works successfully!")
    except Exception as e:
        print(f"Error during Phase 1 testing: {e}")
