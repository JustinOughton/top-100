import datetime
import json
import os
import time
import sys
import numpy as np
import pandas as pd
import requests
import yfinance as yf

MAX_STOCK_PRICE = 150.0
TICKER_LIST_FILE = "active_100_tickers.csv"
OUTPUT_RANKINGS_FILE = "current_ai_rankings.csv"
HTML_DASHBOARD_FILE = "index.html"
DAILY_REPORT_FILE = "daily_market_close_report.txt"
MEMORY_FILE = "market_state_memory.json"

def calculate_rsi(prices, period=14):
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


def load_memory_cache():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_memory_cache(cache_data):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=4)
    except:
        pass


def generate_html_dashboard(df):
    t_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    table_rows = ""
    for idx, row in df.iterrows():
        phase = row["Trading Phase"]
        if phase == "🚨 READY TO SPRING":
            r_cls = "spring-highlight"
            badge = f'<span class="badge" style="background-color:#2e7d32;color:#ffffff;">{phase}</span>'
        elif phase == "🚨 BUY PHASE":
            r_cls = "signal-orange-highlight"
            badge = f'<span class="badge" style="background-color:#ffa524;color:#000000;">{phase}</span>'
        elif phase == "💥 TAKE PROFIT / SELL":
            r_cls = "signal-red-highlight"
            badge = f'<span class="badge" style="background-color:#cc0000;color:#ffffff;">{phase}</span>'
        else:
            r_cls = "row-white" if idx % 2 == 0 else "row-black"
            badge = f'<span class="badge" style="background-color:#555555;color:#ffffff;">{phase}</span>'

        table_rows += f'<tr class="{r_cls}"><td><strong>{row["Ticker"]}</strong></td><td>${row["Price ($)"]:.2f}</td><td>{row["Short Interest %"]:.1f}%</td><td>{row["Days to Cover"]:.1f}d</td><td>{row["RVOL"]:.2f}x</td><td>{row["RSI"]:.1f}</td><td><strong>{row["Risk_Score"]:.1f}</strong></td><td>{badge}</td></tr>'

    html_content = (
        "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1.0'><title>Option C Live</title><style>"
        "body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background-color:#121212;color:#fff;margin:10px;}}"
        ".container{{width:100%;max-width:1100px;margin:0 auto;}}"
        "h2{{text-align:center;text-transform:uppercase;letter-spacing:1px;margin-bottom:2px;}}"
        ".timestamp{{text-align:center;color:#888;font-size:12px;margin-bottom:15px;font-family:monospace;}}"
        ".clock-panel{{display:flex;justify-content:space-around;background-color:#000;border:1px solid #333;padding:15px;margin-bottom:20px;border-radius:6px;text-align:center;}}"
        ".clock-box{{flex:1;}}.clock-label{{font-size:11px;color:#888;text-transform:uppercase;margin-bottom:4px;}}.clock-time{{font-size:20px;font-weight:bold;font-family:monospace;}}"
        "table{{width:100%;border-collapse:collapse;background-color:#fff;color:#000;font-size:14px;}}"
        "th{{background-color:#000;color:#fff;padding:14px 10px;text-align:left;font-size:11px;text-transform:uppercase;border-bottom:2px solid #333;}}"
        "td{{padding:12px 10px;border-bottom:1px solid #e0e0e0;}}"
        ".row-white{{background-color:#fff;color:#000;}}.row-black{{background-color:#000;color:#fff;border-bottom:1px solid #222;}}"
        ".spring-highlight{{background-color:#1a5f20!important;color:#fff!important;font-weight:bold;}}"
        ".signal-orange-highlight{{background-color:#ffb84d!important;color:#000!important;font-weight:bold;}}"
        ".signal-red-highlight{{background-color:#ff3333!important;color:#000!important;font-weight:bold;}}"
        ".badge{{padding:4px 8px;border-radius:4px;font-size:11px;font-weight:bold;display:inline-block;text-transform:uppercase;}}"
        "</style></head><body><div class='container'><h2>AI Processing Leaderboard</h2>"
        f"<div class='timestamp'>ENGINE DATA LAST SYNCED: {t_stamp}</div><div class='clock-panel'>"
        "<div class='clock-box'><div class='clock-label'>Local Sydney Time (AEST)</div><div class='clock-time' id='aest-clock'>--:--:--</div></div>"
        "<div class='clock-box' style='border-left:1px solid #222;'><div class='clock-label' id='countdown-label'>US Market Clock</div><div class='clock-time' id='countdown-clock'>--:--:--</div></div>"
        "</div><table><thead><tr><th>Node Ticker</th><th>Price Field</th><th>Short Float</th><th>DTC Window</th><th>RVOL Ratio</th><th>14D RSI</th><th>Computed Risk Score</th><th>Current Strategy Phase</th></tr></thead><tbody>"
        + table_rows
        + "</tbody></table></div><script>"
        "function updateClocks(){{"
        "let e=new Date();document.getElementById('aest-clock').innerText=e.toLocaleTimeString('en-AU',{{timeZone:'Australia/Sydney',hour12:false}});"
        "let t=e.toLocaleString('en-US',{{timeZone:'America/New_York'}}),n=new Date(t),r=n.getDay(),o=n.getHours(),a=n.getMinutes(),l=n.getSeconds(),i=60*o+a,C=570,c=960,u=0===r||6===r,d=!u&&i>=C&&i<c,s=document.getElementById('countdown-label'),m=document.getElementById('countdown-clock');"
        "if(d){{s.innerText='Market Status: OPEN (Time Until Close)',s.style.color='#00cc44',m.style.color='#00cc44';"
        "let g=60*(c-i)-l;m.innerText=formatTimeDuration(g)}}"
        "else{{s.innerText='Market Status: CLOSED (Time Until Next Open)',s.style.color='#ff3333',m.style.color='#ff3333';"
        "let f=new Date(t);f.setHours(9,30,0,0),i>=c&&f.setDate(f.getDate()+1);while(0===f.getDay()||6===f.getDay())f.setDate(f.getDate()+1);"
        "let T=f-new Date(e.toLocaleString('en-US',{{timeZone:'America/New_York'}}));m.innerText=formatTimeDuration(Math.floor(T/1000))}}"
        "}}function formatTimeDuration(e){{let t=Math.floor(e/3600), Richmond=Math.floor(e%3600/60),n=e%60;return[t.toString().padStart(2,'0'),Richmond.toString().padStart(2,'0'),n.toString().padStart(2,'0')].join(':')}}"
        "setInterval(updateClocks,1000);updateClocks();"
        "</script></body></html>"
    )
    with open(HTML_DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

def hourly_rank_update():
    if not os.path.exists(TICKER_LIST_FILE):
        rebalance_ticker_universe()
        
    active_tickers = pd.read_csv(TICKER_LIST_FILE)["Ticker"].tolist()
    valid_data = []
    memory_cache = load_memory_cache()
    
    market_history = yf.download(
        " ".join(active_tickers), period="30d", group_by="ticker", progress=False
    )
    
    for ticker in active_tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if ticker in market_history.columns.levels:
                history = market_history[ticker].dropna()
            else:
                history = stock.history(period="30d")
                
            if history.empty and ticker not in memory_cache:
                continue
                
            # Historical backup for Price fields
            price = info.get("currentPrice") if info else None
            if price is None or price == 0:
                price = history["Close"].iloc[-1] if not history.empty else memory_cache[ticker]["Price ($)"]
                
            # Smart Fallback Memory Integration for short float metrics
            short_pct = info.get("shortPercentOfFloat") if info else None
            if short_pct is not None:
                short_pct = short_pct * 100
            else:
                short_pct = memory_cache.get(ticker, {}).get("Short Interest %", 5.0)
                
            dtc = info.get("shortRatio") if info else None
            if dtc is None:
                dtc = memory_cache.get(ticker, {}).get("Days to Cover", 1.5)
                
            if not history.empty:
                close_prices = history["Close"].to_numpy()
                current_volume = info.get("volume", history["Volume"].iloc[-1]) if info else history["Volume"].iloc[-1]
                if current_volume is None or current_volume == 0:
                    current_volume = history["Volume"].iloc[-1]
                avg_volume = history["Volume"].mean()
                rvol = current_volume / avg_volume if (avg_volume and avg_volume > 0) else 1.0
                rsi_value = calculate_rsi(close_prices, period=14)
                sma_20 = history["Close"].tail(20).mean()
            else:
                # Emergency hard swap down to historical matrix cache frame
                rvol = memory_cache.get(ticker, {}).get("RVOL", 1.0)
                rsi_value = memory_cache.get(ticker, {}).get("RSI", 50.0)
                sma_20 = price

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

            ticker_metrics = {
                "Ticker": ticker,
                "Price ($)": price,
                "Short Interest %": short_pct,
                "Days to Cover": dtc,
                "RVOL": rvol,
                "RSI": rsi_value,
                "Trading Phase": trading_phase,
                "Risk_Score": base_risk,
            }
            valid_data.append(ticker_metrics)
            memory_cache[ticker] = ticker_metrics  # Update persistent cache snapshot
        except:
            continue

    if valid_data:
        save_memory_cache(memory_cache)
        df_output = pd.DataFrame(valid_data).sort_values(by="Risk_Score", ascending=False)
        df_output.to_csv(OUTPUT_RANKINGS_FILE, index=False)
        generate_html_dashboard(df_output)
        
        for _, row in df_output.iterrows():
            if row["Trading Phase"] in ["🚨 READY TO SPRING", "🚨 BUY PHASE", "💥 TAKE PROFIT / SELL"]:
                send_discord_phase_alert(
                    row["Ticker"],
                    row["Trading Phase"],
                    row["Price ($)"],
                    row["RVOL"],
                    row["RSI"],
                    row["Risk_Score"],
                )


def rebalance_ticker_universe():
    master_list = get_master_universe()
    valid_companies, daily_phase_report = [], []
    memory_cache = load_memory_cache()
    
    try:
        market_history = yf.download(" ".join(master_list), period="30d", group_by="ticker", progress=False)
    except:
        market_history = None

    for ticker in master_list:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if market_history is not None and ticker in market_history.columns.levels:
                history = market_history[ticker].dropna()
            else:
                history = stock.history(period="30d")
                
            if history.empty and ticker not in memory_cache:
                continue
                
            price = info.get("currentPrice") if info else None
            if price is None or price == 0:
                price = history["Close"].iloc[-1] if not history.empty else memory_cache[ticker]["Price ($)"]
                
            if price == 0 or price > MAX_STOCK_PRICE:
                continue
                
            short_pct = info.get("shortPercentOfFloat") if info else None
            if short_pct is not None:
                short_pct = short_pct * 100
            else:
                short_pct = memory_cache.get(ticker, {}).get("Short Interest %", 5.0)
                
            dtc = info.get("shortRatio") if info else None
            if dtc is None:
                dtc = memory_cache.get(ticker, {}).get("Days to Cover", 1.5)
                
            if not history.empty:
                close_prices = history["Close"].to_numpy()
                current_volume = info.get("volume", history["Volume"].iloc[-1]) if info else history["Volume"].iloc[-1]
                rvol = current_volume / history["Volume"].mean() if history["Volume"].mean() > 0 else 1.0
                rsi_value = calculate_rsi(close_prices, period=14)
                sma_20 = history["Close"].tail(20).mean()
            else:
                rvol = memory_cache.get(ticker, {}).get("RVOL", 1.0)
                rsi_value = memory_cache.get(ticker, {}).get("RSI", 50.0)
            
            valid_companies.append({"Ticker": ticker, "Sorting_Score": short_pct * dtc})
            
            if rsi_value >= 80.0 or rvol >= 4.0:
                daily_phase_report.append(f"→ {ticker:5} | [SELL PHASE]: Overbought peak.")
            elif price > sma_20 and rvol >= 1.5 and rsi_value < 70.0:
                daily_phase_report.append(f"→ {ticker:5} | [BUY PHASE] : Strategic entry setup.")
        except:
            continue
            
    if not valid_companies:
        df_universe = pd.DataFrame([{"Ticker": t} for t in master_list])
    else:
        df_universe = pd.DataFrame(valid_companies)
        df_universe = df_universe.sort_values(by="Sorting_Score", ascending=False).head(100)
        
    df_universe[["Ticker"]].to_csv(TICKER_LIST_FILE, index=False)
    
    with open(DAILY_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(
            "=================================================================\n"
            "   OPTION C DAILY SUMMARY CLOSING ENGINE ACTION REPORT\n"
            "=================================================================\n\n"
        )
        if daily_phase_report:
            f.write("\n".join(daily_phase_report))
        else:
            f.write("No monitored nodes triggered actionable close conditions.")
            
    send_discord_text_report()


def send_discord_text_report():
    url = "https://discord.com/api/webhooks/1517340239700562022/_aCg9ik-HyQSE50HKMXIplZ7zUp84RnEefYWEN-CDCR_GXRob9d3kRBN94e5qbaGQktb"
    if not url or "webhooks" not in url or not os.path.exists(DAILY_REPORT_FILE):
        return
    with open(DAILY_REPORT_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    payload = {
        "username": "Option C Closing Engine",
        "content": f"¼📝 **New Closing Action Report Generated**\n```text\n{content}\n```"
    }
    try:
        requests.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=10)
    except:
        pass


def send_discord_phase_alert(ticker, phase, price, rvol, rsi, score):
    url = "https://discord.com/api/webhooks/1517340239700562022/_aCg9ik-HyQSE50HKMXIplZ7zUp84RnEefYWEN-CDCR_GXRob9d3kRBN94e5qbaGQktb"
    if not url or "webhooks" not in url:
        return
    if phase == "🚨 READY TO SPRING":
        color, advice = (3066993, "🟢 **COMPRESSION DETECTED**\\nTight breakout pattern forming.")
    elif phase == "🚨 BUY PHASE":
        color, advice = (16753997, "🟠 **ENTRY POSITION OPEN**\\nBuying pressure is scaling up.")
    elif phase == "💥 TAKE PROFIT / SELL":
        color, advice = (16724787, "🔴 **EXHAUSTION PEAK REACHED**\\nLock in profit targets.")
    else:
        return
    payload = {
        "username": "Option C Phase Engine",
        "embeds": [
            {
                "title": f"📈 PHASE TRANSITION: {ticker} ({phase})",
                "color": color,
                "fields": [
                    {"name": "Current Price", "value": f"${price:.2f}", "inline": True},
                    {"name": "Risk Score", "value": f"**{score:.1f}**", "inline": True},
                    {"name": "RVOL", "value": f"{rvol:.2f}x", "inline": True},
                    {"name": "14D RSI", "value": f"{rsi:.1f}", "inline": True},
                    {"name": "Execution Profile Advice", "value": advice},
                ],
            }
        ],
    }
    try:
        requests.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=10)
    except:
        pass


if __name__ == "__main__":
    if len(sys.argv) > 1 and "--rebalance" in sys.argv:
        print("🚀 Executing Task 1: Force Universe Rebalance Pipeline...")
        rebalance_ticker_universe()
    else:
        print("📈 Executing Task 2: Hourly Cloud Matrix Refresh Engine...")
        hourly_rank_update()
