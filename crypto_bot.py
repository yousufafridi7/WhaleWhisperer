import os
import re
import time
import requests
import pandas as pd
import pandas_ta as ta
from dotenv import load_dotenv

# Optional: suppress warnings for pandas-ta
import warnings
warnings.filterwarnings("ignore")

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class CryptoDataFetcher:
    def __init__(self, symbol):
        self.raw_symbol = symbol.upper()
        self.symbol = symbol.replace("/", "").upper()
        self.base_url_spot = "https://api.binance.com/api/v3"
        self.base_url_fapi = "https://fapi.binance.com/fapi/v1"
        self.base_url_fdata = "https://fapi.binance.com/futures/data"

    def get_current_price(self):
        try:
            res = requests.get(f"{self.base_url_spot}/ticker/price?symbol={self.symbol}").json()
            return float(res["price"])
        except: return 0.0

    def get_klines_data(self, interval="15m", limit=100):
        try:
            res = requests.get(f"{self.base_url_spot}/klines?symbol={self.symbol}&interval={interval}&limit={limit}").json()
            df = pd.DataFrame(res, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "qav", "num_trades", "taker_base_vol", "taker_quote_vol", "ignore"])
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col])
            
            # Indicators
            df.ta.rsi(length=14, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            df.ta.bbands(length=20, std=2, append=True)
            df.ta.sma(length=20, close="volume", append=True, prefix="VOL")
            return df
        except Exception as e:
            return None

    def analyze_trend(self, interval):
        df = self.get_klines_data(interval)
        if df is None or len(df) < 20: 
            return "Neutral", False, {}, 0
        
        last_rsi = df["RSI_14"].iloc[-1]
        last_macd = df["MACD_12_26_9"].iloc[-1]
        last_macdh = df["MACDh_12_26_9"].iloc[-1] # histogram
        last_close = df["close"].iloc[-1]
        last_sma = df["BBM_20_2.0"].iloc[-1]
        
        last_vol = df["volume"].iloc[-1]
        avg_vol = df["VOL_SMA_20"].iloc[-1]
        vol_confirming = last_vol > avg_vol
        
        trend = "Neutral"
        if last_rsi > 55 and last_macdh > 0 and last_close > last_sma:
            trend = "Bullish"
        elif last_rsi < 45 and last_macdh < 0 and last_close < last_sma:
            trend = "Bearish"
            
        indicators = {
            "RSI": round(last_rsi, 2),
            "MACD": round(last_macd, 2),
            "BB_Upper": round(df["BBU_20_2.0"].iloc[-1], 2),
            "BB_Lower": round(df["BBL_20_2.0"].iloc[-1], 2)
        }
            
        return trend, vol_confirming, indicators, last_close

    def detect_whales(self):
        whale_data = []
        heavy_buy = 0
        heavy_sell = 0
        try:
            # Order book walls
            ob = requests.get(f"{self.base_url_spot}/depth?symbol={self.symbol}&limit=20").json()
            for price, qty in ob.get("bids", []):
                if float(price) * float(qty) > 500000:
                    whale_data.append(f"🐋 Large buy wall at ${float(price):,.2f}")
            for price, qty in ob.get("asks", []):
                if float(price) * float(qty) > 500000:
                    whale_data.append(f"🐋 Large sell wall at ${float(price):,.2f} — potential resistance")

            # Recent trades
            trades = requests.get(f"{self.base_url_spot}/trades?symbol={self.symbol}&limit=100").json()
            for t in trades:
                val = float(t["price"]) * float(t["qty"])
                if val > 500000:
                    if t["isBuyerMaker"]:
                        heavy_sell += val
                    else:
                        heavy_buy += val
            
            if heavy_buy > heavy_sell and heavy_buy > 0:
                whale_data.insert(0, "🐋 WHALE ACTIVITY: Heavy Buying Detected")
            elif heavy_sell > heavy_buy and heavy_sell > 0:
                whale_data.insert(0, "🐋 WHALE ACTIVITY: Heavy Selling Detected")
            else:
                whale_data.insert(0, "🐋 WHALE ACTIVITY: Neutral/No Major Moves")
                
        except Exception as e:
            whale_data.append("Error detecting whales.")
        
        whale_trend = "Buy" if heavy_buy > heavy_sell else ("Sell" if heavy_sell > heavy_buy else "Neutral")
        return whale_data, whale_trend

    def get_funding_rate(self):
        try:
            res = requests.get(f"{self.base_url_fapi}/fundingRate?symbol={self.symbol}&limit=1").json()
            return float(res[0]["fundingRate"]) if res else 0.0
        except: return 0.0

    def get_open_interest_data(self):
        oi_current = 0
        oi_trend = "Stable"
        try:
            res = requests.get(f"{self.base_url_fapi}/openInterest?symbol={self.symbol}").json()
            oi_current = float(res.get("openInterest", 0))
            
            hist = requests.get(f"{self.base_url_fdata}/openInterestHist?symbol={self.symbol}&period=15m&limit=2").json()
            if len(hist) == 2:
                prev = float(hist[0]["sumOpenInterestValue"])
                curr = float(hist[1]["sumOpenInterestValue"])
                if curr > prev * 1.01: oi_trend = "Rising ✅"
                elif curr < prev * 0.99: oi_trend = "Dropping 📉"
        except: pass
        return oi_current, oi_trend

    def get_ls_ratio(self):
        try:
            res = requests.get(f"{self.base_url_fdata}/globalLongShortAccountRatio?symbol={self.symbol}&period=15m&limit=1").json()
            if res:
                return float(res[0]["longAccount"]), float(res[0]["shortAccount"])
        except: pass
        return 0.5, 0.5
        
    def estimate_liquidation_levels(self, current_price):
        long_liq_25x = current_price * 0.96
        long_liq_50x = current_price * 0.98
        short_liq_25x = current_price * 1.04
        short_liq_50x = current_price * 1.02
        return {
            "lower": f"${long_liq_50x:,.2f} - ${long_liq_25x:,.2f} (Longs Liq)",
            "upper": f"${short_liq_50x:,.2f} - ${short_liq_25x:,.2f} (Shorts Liq)"
        }

def get_fear_greed():
    try:
        res = requests.get("https://api.alternative.me/fng/?limit=1").json()
        val = int(res["data"][0]["value"])
        desc = res["data"][0]["value_classification"]
        return val, desc
    except:
        return 50, "Neutral"

def get_gemini_analysis(prompt):
    if not GEMINI_API_KEY: return None
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error: {e}"

def get_deepseek_analysis(prompt):
    if not DEEPSEEK_API_KEY: return None
    try:
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload).json()
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {e}"

def get_groq_analysis(prompt):
    if not GROQ_API_KEY: return None
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def parse_ai_response(text, ai_name):
    def extract(pattern, default=""):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    decision = extract(r"DECISION:\s*(LONG|SHORT|WAIT)", "WAIT").upper()
    conf_str = extract(r"CONFIDENCE:\s*(\d+)", "0")
    confidence = int(conf_str) if conf_str.isdigit() else 0
    risk = extract(r"RISK:\s*(LOW|MEDIUM|HIGH)", "MEDIUM").upper()
    
    entry = extract(r"ENTRY:\s*([\d\.,]+)", "0").replace(",", "")
    sl = extract(r"SL:\s*([\d\.,]+)", "0").replace(",", "")
    tp1 = extract(r"TP1:\s*([\d\.,]+)", "0").replace(",", "")
    tp2 = extract(r"TP2:\s*([\d\.,]+)", "0").replace(",", "")
    
    reasoning_match = re.search(r"REASONING:\s*(.*)", text, re.IGNORECASE | re.DOTALL)
    reasoning = reasoning_match.group(1).strip().replace("\\n", " ")[:200] if reasoning_match else "No reasoning provided."

    return {
        "ai": ai_name,
        "decision": decision,
        "confidence": confidence,
        "risk": risk,
        "entry": float(entry) if entry.replace(".", "").isdigit() else 0.0,
        "sl": float(sl) if sl.replace(".", "").isdigit() else 0.0,
        "tp1": float(tp1) if tp1.replace(".", "").isdigit() else 0.0,
        "tp2": float(tp2) if tp2.replace(".", "").isdigit() else 0.0,
        "raw": reasoning
    }

def generate_prompt(data):
    return f"""
You are an expert crypto futures trader. Analyze this market data and provide a trading decision.

Data for {data['symbol']}:
Price: ${data['price']:,.2f}
Timeframes:
- 15m: {data['tf_15m']} (RSI: {data['ind_15m'].get('RSI')}, MACD: {data['ind_15m'].get('MACD')})
- 1hr: {data['tf_1h']} (RSI: {data['ind_1h'].get('RSI')}, MACD: {data['ind_1h'].get('MACD')})
- 4hr: {data['tf_4h']} (RSI: {data['ind_4h'].get('RSI')}, MACD: {data['ind_4h'].get('MACD')})

Volume Confirming Move: {data['vol_confirm']}
Funding Rate: {data['funding_rate']:+.4f}%
Open Interest: {data['oi_trend']}
Long/Short Ratio: {data['ls_long'] * 100:.1f}% Long / {data['ls_short'] * 100:.1f}% Short
Fear/Greed: {data['fg_val']} ({data['fg_desc']})
Whale Activity: {', '.join(data['whales'])}
Est. Liquidation Levels: Upper {data['liq']['upper']}, Lower {data['liq']['lower']}

Provide your response EXACTLY in the following format (do not add markdown formatting outside of these fields):
DECISION: [LONG, SHORT, or WAIT]
CONFIDENCE: [0-100]%
RISK: [LOW, MEDIUM, HIGH]
ENTRY: [Price]
SL: [Price]
TP1: [Price]
TP2: [Price]
REASONING: [2-3 lines of reasoning]
"""

def print_separator():
    print("═══════════════════════════════════════")

def run_bot(symbol_input):
    fetcher = CryptoDataFetcher(symbol_input)
    print(f"\nFetching data for {fetcher.symbol}...")
    
    price = fetcher.get_current_price()
    if price == 0:
        print("Invalid symbol or error fetching data.")
        return

    tf_15m, vol_confirm, ind_15m, _ = fetcher.analyze_trend("15m")
    tf_1h, _, ind_1h, _ = fetcher.analyze_trend("1h")
    tf_4h, _, ind_4h, _ = fetcher.analyze_trend("4h")
    
    whales, whale_trend = fetcher.detect_whales()
    funding = fetcher.get_funding_rate() * 100
    oi_current, oi_trend = fetcher.get_open_interest_data()
    l_ratio, s_ratio = fetcher.get_ls_ratio()
    fg_val, fg_desc = get_fear_greed()
    liq_levels = fetcher.estimate_liquidation_levels(price)
    
    market_data = {
        "symbol": fetcher.symbol, "price": price,
        "tf_15m": tf_15m, "tf_1h": tf_1h, "tf_4h": tf_4h,
        "ind_15m": ind_15m, "ind_1h": ind_1h, "ind_4h": ind_4h,
        "vol_confirm": "Yes ✅" if vol_confirm else "No ⚠️",
        "funding_rate": funding, "whales": whales,
        "oi_trend": oi_trend,
        "ls_long": l_ratio, "ls_short": s_ratio,
        "fg_val": fg_val, "fg_desc": fg_desc,
        "liq": liq_levels
    }
    
    prompt = generate_prompt(market_data)
    
    print("Analyzing with AI Models...")
    gemini_res = parse_ai_response(get_gemini_analysis(prompt) or "", "GEMINI")
    deepseek_res = parse_ai_response(get_deepseek_analysis(prompt) or "", "DEEPSEEK")
    groq_res = parse_ai_response(get_groq_analysis(prompt) or "", "GROQ")
    
    # Voting System
    ai_results = [gemini_res, deepseek_res, groq_res]
    decisions = [r['decision'] for r in ai_results]
    longs = decisions.count("LONG")
    shorts = decisions.count("SHORT")
    waits = decisions.count("WAIT")
    
    final_decision = "WAIT ❌"
    if longs == 3: final_decision = "LONG ✅✅✅"
    elif longs == 2: final_decision = "LONG ✅✅"
    elif longs == 1 and shorts == 0: final_decision = "LONG ⚠️"
    elif shorts == 3: final_decision = "SHORT ✅✅✅"
    elif shorts == 2: final_decision = "SHORT ✅✅"
    elif shorts == 1 and longs == 0: final_decision = "SHORT ⚠️"
    
    avg_conf = int(sum(r['confidence'] for r in ai_results) / 3)
    
    # Best setup extraction based on final decision
    best_setup = None
    agreeing_ais = [r for r in ai_results if r['decision'] in final_decision]
    if agreeing_ais:
        best_setup = max(agreeing_ais, key=lambda x: x['confidence'])
    
    # Terminal Output
    print()
    print_separator()
    print(f"COIN: {fetcher.symbol} | Price: ${price:,.2f}")
    print_separator()
    print(f"TIMEFRAMES:  15m: {tf_15m} | 1hr: {tf_1h} | 4hr: {tf_4h}")
    print_separator()
    for w in whales: print(w)
    print(f"💰 FUNDING RATE: {funding:+.4f}%")
    print(f"📊 OPEN INTEREST: {oi_trend} (Total: {oi_current:,.0f})")
    print(f"⚖️  LONG/SHORT RATIO: {l_ratio*100:.0f}% Long / {s_ratio*100:.0f}% Short")
    print(f"😱 MARKET SENTIMENT: {fg_desc} ({fg_val}/100)")
    print(f"📦 VOLUME: {'Confirming ✅' if vol_confirm else 'Not Confirming ⚠️'}")
    print(f"💥 EST. LIQUIDATIONS: {liq_levels['lower']} | {liq_levels['upper']}")
    print_separator()
    print("AI DECISIONS:")
    print(f"GEMINI:    {gemini_res['decision']:<5} | {gemini_res['confidence']}% confidence")
    print(f"DEEPSEEK:  {deepseek_res['decision']:<5} | {deepseek_res['confidence']}% confidence")
    print(f"GROQ:      {groq_res['decision']:<5} | {groq_res['confidence']}% confidence")
    print_separator()
    print(f"FINAL DECISION: {final_decision}")
    print(f"OVERALL CONFIDENCE: {avg_conf}%")
    
    if best_setup and best_setup['decision'] != "WAIT" and best_setup['entry'] > 0:
        print(f"RISK LEVEL: {best_setup['risk']}")
        print("───────────────────────────────────────")
        print(f"ENTRY:      ${best_setup['entry']:,.2f}")
        print(f"STOP LOSS:  ${best_setup['sl']:,.2f}")
        print(f"TARGET 1:   ${best_setup['tp1']:,.2f}")
        print(f"TARGET 2:   ${best_setup['tp2']:,.2f}")
        
        # Risk/Reward Ratio Calculation
        risk = abs(best_setup['entry'] - best_setup['sl'])
        reward = abs(best_setup['tp1'] - best_setup['entry'])
        if risk > 0:
            print(f"RISK/REWARD RATIO: 1:{reward/risk:.1f}")
        print("───────────────────────────────────────")
        
    print("REASONING:")
    print(f"Gemini: {gemini_res['raw']}")
    print(f"DeepSeek: {deepseek_res['raw']}")
    print(f"Groq: {groq_res['raw']}")
    print_separator()
    
    # Smart Warnings
    warnings = []
    if funding > 0.05: warnings.append("High positive funding rate — overleveraged longs.")
    elif funding < -0.05: warnings.append("High negative funding rate — overleveraged shorts.")
    if l_ratio > 0.7: warnings.append("Extreme Long Ratio (above 70%) — squeeze risk.")
    elif s_ratio > 0.7: warnings.append("Extreme Short Ratio (above 70%) — squeeze risk.")
    if fg_val > 85: warnings.append("Extreme Greed (above 85) — market may be toppy.")
    elif fg_val < 15: warnings.append("Extreme Fear (below 15) — potential bounce area.")
    if not vol_confirm and ("LONG" in final_decision or "SHORT" in final_decision):
        warnings.append("Volume is not confirming the price move.")
    if ("LONG" in final_decision and whale_trend == "Sell") or ("SHORT" in final_decision and whale_trend == "Buy"):
        warnings.append("Whale activity contradicts AI decision.")
    if "Dropping" in oi_trend and "LONG" in final_decision:
        warnings.append("Open interest is dropping while price is rising (weakness).")
    
    if warnings:
        print("⚠️  WARNING: Conflicting signals detected")
        for w in warnings: print(f"    - {w}")
        print_separator()

if __name__ == "__main__":
    while True:
        pair = input("Enter a crypto pair (e.g. BTC/USDT) or 'exit': ")
        if pair.lower() == 'exit':
            break
        run_bot(pair)
        
        again = input("\\nAnalyze another coin? (yes/no): ")
        if again.lower() != 'yes':
            print("Exiting...")
            break
