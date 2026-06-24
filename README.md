# 🐋 WhaleWhisperer V2

**WhaleWhisperer V2** is a modular, high-performance crypto quant engine that implements a dual-mode, volatility-adjusted trading strategy. It combines multi-indicator technical scoring with AI-driven market regime explanations powered by **Gemini 1.5 Pro** and Wilder's Average True Range (ATR).

Designed for swing traders and active quant simulation, WhaleWhisperer V2 determines whether the market is in a structural uptrend (BULL mode) or downtrend (BEAR mode) using a 200-period Simple Moving Average, adjusting all risk management levels, stop-losses, and entry signals dynamically.

---

## 🚀 Architectural Overview

The engine is built modularly for transparency and easy extension:
* **`main.py`**: CLI Entrypoint, coordinates the live data fetching, rendering, and AI whispers.
* **`data.py`**: Fetching live and paginated historical OHLCV data using the CCXT Binance client.
* **`indicators.py`**: Technical indicators pipeline (EMA 9/21, RSI 14, MACD, Bollinger Bands, Squeeze Momentum, Volume SMA, Wilder's ATR 14, SMA 200).
* **`signals.py`**: Custom scoring model, Market Regime Detector, and dynamic SL/TP calculation.
* **`explainer.py`**: AI explanation layer powered by the official `google-genai` SDK and Gemini 1.5 Pro, featuring cache optimization.
* **`backtest.py`**: Historical simulation engine using `backtesting.py` to verify strategies with margin management.

---

## ⚡ V2 Features & Strategies

### 1. 📊 Market Regime Detector (SMA 200)
The system calculates the 200-period Simple Moving Average to determine the current macro market regime:
* **BULL Mode:** Price is above the 200 SMA.
* **BEAR Mode:** Price is below the 200 SMA.

### 2. 🎯 Mode-Based Dynamic Risk Strategy
Depending on the detected market regime, WhaleWhisperer V2 adjusts risk parameters on-the-fly:

| Parameter | BULL Mode (Aggressive) | BEAR Mode (Defensive) |
| :--- | :---: | :---: |
| **Take Profit (TP)** | **4.0x ATR** (Wider targets) | **3.0x ATR** (Standard targets) |
| **Stop Loss (SL)** | **2.0x ATR** (Relaxed protection) | **1.5x ATR** (Tight protection) |
| **Neutral Zone** | **Tight** (LONG score $\ge 4$, SHORT $\le -4$) | **Normal** (LONG score $\ge 5$, SHORT $\le -5$) |
| **Target Risk/Reward** | **1:2.0** | **1:2.0** |

### 3. 🎯 Active Trade Setup Cards
For non-neutral signals, the CLI generates a ready-to-execute trade setup containing the optimal entry, stop loss, and take profit prices, adjusted for current market volatility (ATR).

---

## 📊 Backtest Performance Verification

WhaleWhisperer V2 has been rigorously backtested across two distinct market cycles using a starting equity of **$1,000,000** and a realistic fee commission of **0.04%**.

### 1. Bear Market Period (Last 180 Days)
This period was highly bearish (ADA -58%, ETH -43%, BTC -29%). WhaleWhisperer V2 successfully acted as a capital protection shield, dramatically outperforming Buy & Hold.

| Asset | Timeframe | Trades | Win Rate | Strategy Return | Buy & Hold Return | Max Drawdown | Sharpe |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BTC/USDT** | 1h | 81 | **37.04%** | **-0.29%** | -29.43% | **-12.37%** | -0.03 |
| **ADA/USDT** | 4h | 19 | **36.84%** | **+6.73%** | -56.97% | **-18.73%** | 0.47 |
| **ETH/USDT** | 1h | 76 | **31.58%** | **-18.91%** | -43.74% | **-21.84%** | -2.07 |

### 2. Bull Market Period (Oct 1, 2023 - Apr 1, 2024)
A massive upward trend where BTC went from $26k to $73k and altcoins went parabolic. V2 settings successfully captured strong swings.

| Asset | Timeframe | Trades | Win Rate | Strategy Return | Buy & Hold Return | Max Drawdown | Sharpe |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **SOL/USDT** | 1h | 110 | **43.64%** | **+50.81%** | +847.42% | **-37.06%** | 0.82 |
| **ADA/USDT** | 1h | 83 | **38.55%** | **+29.77%** | +154.77% | **-20.08%** | 0.90 |
| **BTC/USDT** | 4h | 21 | **33.33%** | **-1.75%** | +161.00% | **-23.40%** | -0.12 |

---

## 🛠️ Installation & Setup

### Requirements
* Python 3.10+
* CCXT & Pandas libraries
* Google Gemini API Key

### Step 1: Clone and Prepare Virtual Env
```bash
git clone https://github.com/yousufafridi7/WhaleWhisperer.git
cd WhaleWhisperer
python -m venv venv
source venv/Scripts/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Environment `.env`
Create your `.env` file based on `.env.example`:
```env
GEMINI_API_KEY=AIzaSy...
```

### Step 3: Run the CLI Interface
```bash
python main.py
```

### Step 4: Run Batch Backtesting
To run comparative backtest reports over the last 180 days across multiple pairs:
```bash
python run_batch_backtests.py
```
To run backtests over the 2023-2024 bull run:
```bash
python run_bull_market_backtests.py
```

---

## ⚠️ Disclaimer
WhaleWhisperer V2 is an educational research tool. It generates analytical insights and simulations but does not execute live trades automatically. Futures trading is highly risky. Trade responsibly.
