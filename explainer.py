import os
import sys
from groq import Groq
from dotenv import load_dotenv
from cache import ExplanationCache

# Fix Windows console encoding for emojis
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Module level cache instance (5 minutes TTL)
explanation_cache = ExplanationCache(ttl_seconds=300)

def get_explanation(symbol: str, timeframe: str, signal: str, score: float, indicators: dict) -> str:
    """
    Generates a 2-3 line explanation for the signal using Groq API.
    Caches the explanation to avoid redundant API calls.
    """
    # 1. Check cache first
    cached = explanation_cache.get(symbol, timeframe, signal)
    if cached:
        return cached

    # 2. Check API Key
    if not GROQ_API_KEY:
        return "LLM Explanation unavailable: GROQ_API_KEY not set in .env file."

    # 3. Format compact inputs
    rsi = round(indicators.get('rsi', 50.0), 1)
    macd = "Bullish" if indicators.get('macd_hist', 0.0) > 0 else "Bearish"
    
    bb = "Inside"
    if indicators.get('close_bb_lower'):
        bb = "Below Lower Band"
    elif indicators.get('close_bb_upper'):
        bb = "Above Upper Band"
        
    sqz = "Squeeze OFF"
    if indicators.get('sqz_on'):
        sqz = "Squeeze ON"
    sqz_mom = round(indicators.get('sqz_mom', 0.0), 1)
    
    vol = "Confirmed" if indicators.get('volume_confirmed') else "Unconfirmed"
    
    # User message (very compact ~35 tokens)
    user_prompt = (
        f"Coin: {symbol} | TF: {timeframe} | Signal: {signal} | Score: {score:+.1f} | "
        f"RSI: {rsi} | MACD: {macd} | BB: {bb} | Sqz: {sqz} ({sqz_mom:+.1f}) | Vol: {vol}"
    )

    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        # Call Groq API
        chat_completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are a quant trading analyst. Explain the rule-based signal in 2 to 3 lines. Be direct, professional, and focus only on the provided technicals. Do not give financial advice or warning disclaimers."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.2,
            max_tokens=150
        )
        
        explanation = chat_completion.choices[0].message.content.strip()
        
        # Save to cache
        explanation_cache.set(symbol, timeframe, signal, explanation)
        
        return explanation
    except Exception as e:
        return f"Error fetching explanation from Groq: {e}"

if __name__ == "__main__":
    # Test script for Phase 5 verification
    print("Testing Phase 5 LLM Explainer...")
    test_indicators = {
        'rsi': 28.5,
        'macd_hist': -12.4,
        'close_bb_lower': True,
        'close_bb_upper': False,
        'sqz_on': 0,
        'sqz_mom': -450.2,
        'volume_confirmed': True
    }
    
    # Test execution (should display message if key is missing, or fetch if key is present)
    explanation = get_explanation("BTC/USDT", "1h", "SHORT", -4.5, test_indicators)
    print("\nGenerated Explanation:")
    print(explanation)
    
    # Test cache hit
    print("\nTesting Cache Hit (should return immediately without API call)...")
    cached_explanation = get_explanation("BTC/USDT", "1h", "SHORT", -4.5, test_indicators)
    print(cached_explanation)
