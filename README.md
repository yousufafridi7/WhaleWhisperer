# 🐋 WhaleWhisperer

> *Three AIs walk into a trading terminal...*

**WhaleWhisperer** is a free, locally-run crypto futures analysis bot that combines the power of three AI models — Gemini, DeepSeek, and Groq — with real-time whale activity detection, technical indicators, and market sentiment analysis to give you a majority-voted trading signal before you make your move.

No subscriptions. No cloud. Just you, your terminal, and three AIs whispering in your ear.

---

## 🧠 How It Works

```
You type a coin → Bot fetches live data → 3 AIs analyze simultaneously
        ↓
Gemini says LONG | DeepSeek says LONG | Groq says WAIT
        ↓
Majority Vote → LONG ✅✅ | Confidence: 73% | Risk: MEDIUM
        ↓
Entry, Stop Loss, Take Profit — all calculated for you
```

---

## ✨ Features

**Multi-AI Ensemble Voting**
- Gemini, DeepSeek, and Groq analyze the same data independently
- Majority voting system — 2/3 or 3/3 agreement required for a signal
- Each AI gives its own confidence score and reasoning

**Real-Time Market Data (No Login Required)**
- Live price from Binance public API
- RSI, MACD, Bollinger Bands calculated in real-time
- Multi-timeframe analysis — 15m, 1hr, and 4hr simultaneously
- Volume confirmation check

**🐋 Whale Activity Detection**
- Scans Binance order book for large buy/sell walls
- Flags individual trades above $500,000
- Detects if whales are accumulating or distributing
- Whale data is fed directly into AI prompts for smarter decisions

**Futures-Specific Data**
- Funding rate — know if the market is overleveraged
- Open Interest tracking — confirms trend strength
- Long/Short ratio — spot potential squeeze setups
- Estimated liquidation levels

**Smart Warning System**
- Alerts you when signals conflict with whale activity
- Warns on extreme Fear & Greed readings
- Flags when volume does not confirm price movement
- Catches skewed long/short ratios before you enter

**Fear & Greed Index**
- Live market sentiment from alternative.me
- Factored into AI analysis automatically

---

## 📊 Sample Output

```
═══════════════════════════════════════
COIN: BTC/USDT | Price: $96,842
═══════════════════════════════════════
TIMEFRAMES:  15m: Bullish | 1hr: Bullish | 4hr: Neutral
═══════════════════════════════════════
🐋 WHALE ACTIVITY: Heavy Buying Detected
🐋 Large buy wall at $95,000
💰 FUNDING RATE: +0.012% (Longs paying — slight bearish)
📊 OPEN INTEREST: Rising ✅
⚖️  LONG/SHORT RATIO: 58% Long / 42% Short
😱 MARKET SENTIMENT: Fear (32/100)
📦 VOLUME: Confirming ✅
═══════════════════════════════════════
AI DECISIONS:
GEMINI:    LONG  | 78% confidence
DEEPSEEK:  LONG  | 82% confidence
GROQ:      WAIT  | 55% confidence
═══════════════════════════════════════
FINAL DECISION: LONG ✅✅
OVERALL CONFIDENCE: 73%
RISK LEVEL: MEDIUM
───────────────────────────────────────
ENTRY:      $96,500
STOP LOSS:  $95,200
TARGET 1:   $98,000
TARGET 2:   $100,500
RISK/REWARD RATIO: 1:2.3
───────────────────────────────────────
REASONING:
Gemini:    Strong bullish structure on 1hr. Whale accumulation supports move.
DeepSeek:  RSI not overbought. MACD crossover confirmed. High confidence long.
Groq:      Mixed signals on 4hr. Suggest waiting for confirmation.
═══════════════════════════════════════
⚠️  WARNING: High funding rate — market may be overleveraged
═══════════════════════════════════════
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
