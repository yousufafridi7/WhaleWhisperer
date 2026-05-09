import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import re
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class CryptoDataFetcher:
    def __init__(self, symbol):
        self.raw_symbol = symbol.upper().strip()
        self.symbol = self.raw_symbol.replace("/", "").replace("-", "")
        if not self.symbol.endswith("USDT") and not self.symbol.endswith("BUSD") and not self.symbol.endswith("USDC"):
            self.symbol += "USDT"
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
            
            # Indicators (Pure Pandas)
            # RSI
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["RSI"] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df["close"].ewm(span=12, adjust=False).mean()
            exp2 = df["close"].ewm(span=26, adjust=False).mean()
            df["MACD"] = exp1 - exp2
            df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
            df["MACDh"] = df["MACD"] - df["MACD_signal"]
            
            # Bollinger Bands
            df["BBM"] = df["close"].rolling(window=20).mean()
            df["BBSD"] = df["close"].rolling(window=20).std()
            df["BBU"] = df["BBM"] + (df["BBSD"] * 2)
            df["BBL"] = df["BBM"] - (df["BBSD"] * 2)
            
            # Volume SMA
            df["VOL_SMA_20"] = df["volume"].rolling(window=20).mean()
            return df
        except Exception as e:
            return None

    def analyze_trend(self, interval):
        df = self.get_klines_data(interval)
        if df is None or len(df) < 20: 
            return "Neutral", False, {}, 0
        
        last_rsi = df["RSI"].iloc[-1]
        last_macd = df["MACD"].iloc[-1]
        last_macdh = df["MACDh"].iloc[-1] # histogram
        last_close = df["close"].iloc[-1]
        last_sma = df["BBM"].iloc[-1]
        
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
            "BB_Upper": round(df["BBU"].iloc[-1], 2),
            "BB_Lower": round(df["BBL"].iloc[-1], 2)
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
            "messages": [
                {"role": "system", "content": "You are a trading bot. You MUST reply ONLY with the exact format requested. No pleasantries."},
                {"role": "user", "content": prompt}
            ],
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
    if reasoning_match:
        reasoning_raw = reasoning_match.group(1).strip().replace("\n", " ")
        sentences = re.split(r'(?<=[.!?])\s+', reasoning_raw)
        reasoning = sentences[0] if sentences else reasoning_raw
    else:
        reasoning = "No reasoning provided."

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
REASONING: [1 sentence of reasoning]
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
    
    agreeing_ais = [r for r in ai_results if r['decision'] in final_decision]
    risk_level = max(agreeing_ais, key=lambda x: x['confidence'])['risk'] if agreeing_ais else "MEDIUM"
    
    warnings = []
    if not vol_confirm: warnings.append("Volume not confirming move")
    if l_ratio > s_ratio and "LONG" not in final_decision: warnings.append("More longs than shorts — squeeze risk")
    elif s_ratio > l_ratio and "SHORT" not in final_decision: warnings.append("More shorts than longs — squeeze risk")
    if funding > 0.05: warnings.append("High positive funding rate — overleveraged longs.")
    elif funding < -0.05: warnings.append("High negative funding rate — overleveraged shorts.")
    if fg_val > 85: warnings.append("Extreme Greed (above 85) — market may be toppy.")
    elif fg_val < 15: warnings.append("Extreme Fear (below 15) — potential bounce area.")
    if ("LONG" in final_decision and whale_trend == "Sell") or ("SHORT" in final_decision and whale_trend == "Buy"): warnings.append("Whale activity contradicts AI decision.")
    if "Dropping" in oi_trend and "LONG" in final_decision: warnings.append("Open interest dropping while price rising (weakness).")

    print()
    print("═══════════════════════════════════")
    print(f"  🐋 WHALEWHISPERER — {fetcher.symbol}")
    print(f"  Price: ${price:,.0f} | Risk: {risk_level}")
    print("═══════════════════════════════════")
    print("  📊 TREND")
    print(f"  15m: {tf_15m} | 1hr: {tf_1h} | 4hr: {tf_4h}")
    print()
    print(f"  🐋 WHALES: {whale_trend}")
    print(f"  😱 SENTIMENT: {fg_desc} ({fg_val}/100)")
    print(f"  💰 FUNDING: {funding:+.4f}%")
    print(f"  📦 VOLUME: {'Confirming ✅' if vol_confirm else 'Not Confirming ⚠️'}")
    print(f"  ⚖️ LONGS vs SHORTS: {l_ratio*100:.0f}% / {s_ratio*100:.0f}%")
    print("═══════════════════════════════════")
    print("  🤖 AI VOTES")
    
    def format_vote(res):
        icon = "✅" if res['decision'] in final_decision and res['decision'] != "WAIT" else ("⚠️" if res['decision'] == "WAIT" else "❌")
        return f"{res['decision']:<5} {res['confidence']}%  {icon}"
        
    print(f"  Gemini:   {format_vote(gemini_res)}")
    print(f"  DeepSeek: {format_vote(deepseek_res)}")
    print(f"  Groq:     {format_vote(groq_res)}")
    print("═══════════════════════════════════")
    print(f"  📢 FINAL: {final_decision}")
    print(f"  Confidence: {avg_conf}%")
    
    if "WAIT" in final_decision and longs == 0 and shorts == 0:
        print("───────────────────────────────────")
        print("  🚫 NO TRADE — All AIs suggest waiting. Come back later.")
        print("═══════════════════════════════════")
        return
        
    if "LONG" in final_decision or "SHORT" in final_decision:
        print("───────────────────────────────────")
        entry_price = price
        if "LONG" in final_decision:
            sl_price = min(price * 0.98, ind_15m.get('BB_Lower', price * 0.95))
            tp1_price = price * 1.02
            tp2_price = price * 1.04
        else:
            sl_price = max(price * 1.02, ind_15m.get('BB_Upper', price * 1.05))
            tp1_price = price * 0.98
            tp2_price = price * 0.96
            
        risk_dist = abs(entry_price - sl_price)
        reward_dist = abs(tp1_price - entry_price)
        rr_ratio = reward_dist / risk_dist if risk_dist > 0 else 0
        
        print(f"  ENTRY:     ${entry_price:,.2f}")
        print(f"  STOP LOSS: ${sl_price:,.2f}  🔴")
        print(f"  TARGET 1:  ${tp1_price:,.2f}  🟢")
        print(f"  TARGET 2:  ${tp2_price:,.2f}  🟢")
        print(f"  R/R RATIO: 1:{rr_ratio:.1f}")
        print("───────────────────────────────────")
        
    print("  💬 WHY?")
    print(f"  Gemini:   {gemini_res['raw']}")
    print(f"  DeepSeek: {deepseek_res['raw']}")
    print(f"  Groq:     {groq_res['raw']}")
    print("═══════════════════════════════════")
    
    if warnings:
        print("  ⚠️ WARNINGS")
        for w in warnings: print(f"  - {w}")
        print("═══════════════════════════════════")
        
    print(f"  💡 SUMMARY: {max(longs, shorts)}/3 AIs say {'LONG' if longs > shorts else ('SHORT' if shorts > longs else 'WAIT')}.")

if __name__ == "__main__":
    while True:
        pair = input("Enter a crypto pair (e.g. BTC/USDT) or 'exit': ")
        if pair.lower() == 'exit':
            break
        run_bot(pair)
        
        again = input("\nAnalyze another coin? (yes/no): ")
        if again.lower() != 'yes':
            print("Happy trading! 🐋")
            break
