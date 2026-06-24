import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv
from cache import ExplanationCache

# Fix Windows console encoding for emojis
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Module level cache instance (5 minutes TTL)
explanation_cache = ExplanationCache(ttl_seconds=300)

def get_explanation(symbol: str, timeframe: str, signal: str, score: float, indicators: dict) -> str:
    """
    Generates a 2-3 line explanation for the signal using Gemini 2.5 Flash.
    Caches the explanation to avoid redundant API calls.
    """
    # 1. Check cache first
    cached = explanation_cache.get(symbol, timeframe, signal)
    if cached:
        return cached

    # 2. Check API Key
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return "LLM Explanation unavailable: GEMINI_API_KEY not set in .env file."

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
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are a quant trading analyst. Explain the rule-based signal in 2 to 3 lines. Be direct, professional, and focus only on the provided technicals. Do not give financial advice or warning disclaimers.",
                temperature=0.2,
                max_output_tokens=1000,
            ),
        )
        
        explanation = response.text.strip()
        
        # Save to cache
        explanation_cache.set(symbol, timeframe, signal, explanation)
        
        return explanation
    except Exception as e:
        return f"Error fetching explanation from Gemini: {e}"

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
