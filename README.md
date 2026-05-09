# 🐋 WhaleWhisperer

> *Three AIs walk into a trading terminal...*

**WhaleWhisperer** is a free, locally-run crypto futures analysis bot that combines the power of three AI models — Gemini, DeepSeek, and Groq — with real-time whale activity detection, technical indicators, and market sentiment analysis to give you a majority-voted trading signal before you make your move.

No subscriptions. No cloud. Just you, your terminal, and three AIs whispering in your ear.

---

## 🧠 How It Works

```
Enter balance once → Type a coin → Bot fetches live data → 3 AIs analyze simultaneously
                                            ↓
                        Gemini says SHORT | DeepSeek says SHORT | Groq says WAIT
                                            ↓
                     Majority Vote → SHORT ✅✅ | Confidence: 70% | Risk: MEDIUM
                                            ↓
              Entry, Stop Loss, Take Profit, Leverage Guide — all calculated for you
```

---

## ✨ Features

**Multi-AI Ensemble Voting**
- Gemini, DeepSeek, and Groq analyze the same data independently
- Majority voting system — 2/3 or 3/3 agreement required for a signal
- Each AI gives its own confidence score and 1-sentence reasoning
- If one AI is unavailable, confidence is calculated from remaining AIs only

**Real-Time Market Data (No Login Required)**
- Live price from Binance public API
- RSI, MACD, Bollinger Bands calculated in real-time
- Multi-timeframe analysis — 15m, 1hr, and 4hr simultaneously
- Volume confirmation check
- Coin name auto-normalization — type `btc` or `BTC/USDT`, bot handles it

**🐋 Whale Activity Detection**
- Scans Binance order book for large buy/sell walls
- Flags individual trades above $500,000
- Detects if whales are accumulating or distributing
- Whale data fed directly into AI prompts for smarter decisions

**Futures-Specific Data**
- Funding rate — know if the market is overleveraged
- Open Interest tracking — confirms trend strength
- Long/Short ratio — spot potential squeeze setups
- Estimated liquidation levels

**⏱ Estimated Trade Duration**
- Bot estimates how long the trade will run based on timeframe signals
- Scalp (15m signal) / Intraday (1hr) / Swing (4hr) / Conflict warning

**⚡ Leverage Risk Guide**
- Enter your account balance once at startup
- Bot shows a full leverage table: 3x to 30x
- Each row shows liquidation price, loss if SL hit, profit if TP1 hit, profit if TP2 hit
- Risk level per leverage: Safe / Low / Medium / High / Extreme / Danger
- Bot suggests a leverage range — final decision is always yours

**Smart Warning System**
- Alerts when signals conflict with whale activity
- Warns on extreme Fear & Greed readings
- Flags when volume does not confirm price movement
- Catches skewed long/short ratios and high funding rates

**Fear & Greed Index**
- Live market sentiment from alternative.me
- Factored into AI analysis automatically

---

## 📊 Sample Output

```
💰 Enter your account balance (USDT): 500

Enter a crypto pair (e.g. BTC/USDT) or 'exit': btc
Fetching data for BTCUSDT...
Analyzing with AI Models...

═══════════════════════════════════
  🐋 WHALEWHISPERER — BTCUSDT
  Price: $80,497 | Risk: MEDIUM
═══════════════════════════════════
  📊 TREND
  15m: Bullish | 1hr: Bullish | 4hr: Bearish

  🐋 WHALES: Neutral
  😱 SENTIMENT: Fear (38/100)
  💰 FUNDING: +0.0018% (Normal)
  📦 VOLUME: Not Confirming ⚠️
  ⚖️ LONGS vs SHORTS: 44% / 56%
═══════════════════════════════════
  🤖 AI VOTES
  Gemini:   SHORT 70%  ✅
  DeepSeek: Unavailable ❌
  Groq:     SHORT 70%  ✅
═══════════════════════════════════
  📢 FINAL: SHORT ✅✅
  Confidence: 70%
───────────────────────────────────
  ENTRY:     $80,497
  STOP LOSS: $82,107  🔴
  TARGET 1:  $78,887  🟢
  TARGET 2:  $77,277  🟢
  R/R RATIO: 1:2.1
  ⏱ EST. DURATION: Unclear — monitor closely ⚠️
───────────────────────────────────
  ⚡ LEVERAGE GUIDE  (Balance: $500)

  Lev  │ Liq Price │ Loss if SL  │ Profit TP1  │ Profit TP2  │ Risk
  ─────┼───────────┼─────────────┼─────────────┼─────────────┼──────────
  3x   │ $83,130   │ -$25  (5%)  │ +$25  (5%)  │ +$50  (10%) │ 🟢 Safe
  5x   │ $84,472   │ -$42  (8%)  │ +$42  (8%)  │ +$83  (17%) │ 🟡 Low
  10x  │ $88,447   │ -$85  (17%) │ +$85  (17%) │ +$170 (34%) │ 🟠 Medium
  15x  │ $85,831   │ -$127 (25%) │ +$127 (25%) │ +$255 (51%) │ 🔴 High
  20x  │ $84,722   │ -$170 (34%) │ +$170 (34%) │ +$340 (68%) │ 🔴 Very High
  25x  │ $83,697   │ -$212 (42%) │ +$212 (42%) │ +$425 (85%) │ 💀 Extreme
  30x  │ $83,180   │ -$255 (51%) │ +$255 (51%) │ +$510 (102%)│ 💀 Danger

  💡 SUGGESTED: 3x — 5x (Final decision is yours)
───────────────────────────────────
  💬 WHY?
  Gemini:   Short-term overbought conditions lack volume confirmation against a bearish 4hr trend.
  DeepSeek: Unavailable ❌
  Groq:     Bearish 4hr structure with fear sentiment and high RSI suggests potential reversal.
═══════════════════════════════════
  ⚠️ WARNINGS
  - Volume not confirming move
═══════════════════════════════════
  💡 SUMMARY: 2/3 AIs say SHORT. Low volume — consider waiting.
═══════════════════════════════════

Analyze another coin? (yes/no):
```

---

## 🛠️ Installation

**Requirements**
- Python 3.10+
- Free API keys for Gemini, DeepSeek, and Groq (links below)

**Step 1 — Clone the repo**
```bash
git clone https://github.com/yousufafridi7/WhaleWhisperer.git
cd WhaleWhisperer
```

**Step 2 — Install dependencies**
```bash
python -m pip install requests python-dotenv google-genai groq pandas
```

**Step 3 — Set up your API keys**

Copy the template and fill in your keys:
```bash
cp .env.example .env
```

Edit `.env`:
```
GEMINI_API_KEY=your_gemini_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
GROQ_API_KEY=your_groq_key_here
```

**Step 4 — Run the bot**
```bash
python crypto_bot.py
```

When the bot starts, it will ask for your account balance once. After that, just type any coin and get your analysis!

---

## 🔑 Getting Free API Keys

| AI | Link | Cost |
|---|---|---|
| Gemini | [aistudio.google.com](https://aistudio.google.com) | ✅ Free |
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com) | ✅ Free credits |
| Groq | [console.groq.com](https://console.groq.com) | ✅ Free |

No credit card required for any of them to get started.

---

## 📁 Project Structure

```
WhaleWhisperer/
├── crypto_bot.py       # Main bot — everything runs from here
├── .env                # Your API keys (never commit this)
├── .env.example        # Template for API keys
├── .gitignore          # Keeps your .env safe
└── README.md           # You are here
```

---

## ⚠️ Disclaimer

WhaleWhisperer is a research and analysis tool. It does not execute trades automatically. All trading decisions are made by you. Crypto futures trading carries significant risk — never trade more than you can afford to lose. This tool is not financial advice.

---

## 🤝 Contributing

Pull requests are welcome. If you have ideas for improvements — new data sources, better indicators, additional AI models — feel free to open an issue or submit a PR.

---

## 📜 License

MIT License — free to use, modify, and share.

---

<p align="center">Built with 🐋 by <a href="https://github.com/yousufafridi7">yousufafridi7</a></p>
