import datetime
import json
import os
import pandas as pd
import yfinance as yf

MAX_STOCK_PRICE = 150.0
MEMORY_FILE = "market_state_memory.json"


def get_master_universe():
    return [
        "WULF", "INOD", "SOUN", "QUBT", "ACMR", "POET", "ATOM", "LWLG", "MARA", "RIOT",
        "CORZ", "VRT", "SMCI", "C3AI", "PATH", "PSTG", "NTAP", "STX", "WDC", "ANET",
        "JNPR", "CIEN", "EXTR", "LITE", "FN", "CLS", "SANM", "FLEX", "PLAB", "CAMT",
        "COHR", "DIOD", "MXL", "SGH", "VICR", "AMD", "INTC", "MU", "MRVL", "ADI",
        "TXN", "MCHP", "NXPI", "ON", "MPWR", "SLAB", "AEHR", "AMKR", "TER", "COGN",
        "IPG", "FORM", "CREE", "RMBS", "NVDA", "PLTR", "SNOW", "AI", "BBAI", "SERV",
        "VERI", "CXM", "EGAN", "DT", "NEWR", "SPLK", "CRWD", "NET", "DDOG", "OKTA",
        "ZS", "DOCU", "MDB", "ESTC", "WK", "S", "ALTR", "CCCS", "UPST", "LYFT",
        "KTOS", "AVAV", "NNDM", "BKSY", "PL", "RKLB", "ACHR", "JOBY", "OUST", "AEVA",
        "MVIS", "REKR", "GCT", "ANY", "BITF", "HUT", "MIGI", "CLSK", "SDIG", "BTDR"
    ]


def calculate_rsi(prices, period=14):
    import numpy as np
    if len(prices) < period + 1:
        return 50.0
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    if down == 0:
        return 100.0
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100.0 - (100.0 / (1.0 + rs))
    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        up_val = delta if delta > 0 else 0.0
        down_val = -delta if delta < 0 else 0.0
        up = (up * (period - 1) + up_val) / period
        down = (down * (period - 1) + down_val) / period
        if down == 0:
            return 100.0
        rs = up / down
        rsi[i] = 100.0 - (100.0 / (1.0 + rs))
    return rsi[-1]

if __name__ == "__main__":
    print("⏳ Starting Master Cache Injection Engine...")
    tickers = get_master_universe()
    memory_cache = {}
    
    print(f"📦 Fetching 30-day historical data for {len(tickers)} assets...")
    market_history = yf.download(" ".join(tickers), period="30d", group_by="ticker", progress=False)
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info if stock else None
            
            if ticker in market_history.columns.levels:
                history = market_history[ticker].dropna()
            else:
                history = stock.history(period="30d") if stock else pd.DataFrame()
                
            if history.empty:
                continue
                
            # Always grab the last available real closing price from trading history
            price = history["Close"].iloc[-1]
            
            # If market is closed, scrape last known valid info fields, or default safely
            short_pct = info.get("shortPercentOfFloat") if info else None
            short_pct = short_pct * 100 if short_pct is not None else 5.0
            
            dtc = info.get("shortRatio") if info else 1.5
            dtc = dtc if dtc is not None else 1.5
            
            close_prices = history["Close"].to_numpy()
            current_volume = history["Volume"].iloc[-1]
            avg_volume = history["Volume"].mean()
            rvol = current_volume / avg_volume if (avg_volume and avg_volume > 0) else 1.0
            rsi_value = calculate_rsi(close_prices, period=14)
            sma_20 = history["Close"].tail(20).mean()

            base_risk = short_pct + (dtc * 2.0)
            if price > sma_20:
                base_risk *= 0.9
            if rsi_value > 80:
                base_risk *= 1.3

            if rsi_value >= 80.0 or rvol >= 4.0:
                trading_phase = "💥 TAKE PROFIT / SELL"
            elif (price > sma_20 and rvol >= 1.8 and 45.0 <= rsi_value <= 65.0 and dtc > 5.0):
                trading_phase = "🚨 READY TO SPRING"
            elif price > sma_20 and rvol >= 1.5 and rsi_value < 70.0:
                trading_phase = "🚨 BUY PHASE"
            else:
                trading_phase = "HOLD / ACCUMULATE"

            memory_cache[ticker] = {
                "Ticker": ticker,
                "Price ($)": float(price),
                "Short Interest %": float(short_pct),
                "Days to Cover": float(dtc),
                "RVOL": float(rvol),
                "RSI": float(rsi_value),
                "Trading Phase": trading_phase,
                "Risk_Score": float(base_risk),
            }
            print(f"✅ Cached: {ticker} (${price:.2f})")
        except Exception as e:
            print(f"⚠️ Skipped {ticker}: {str(e)}")
            continue

    if memory_cache:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory_cache, f, indent=4)
        print(f"🎉 Success! Forcibly populated {len(memory_cache)} elements inside {MEMORY_FILE}")
    else:
        print("❌ Critical Failure: No data could be compiled.")
