# NEW SCRiPT

import datetime
import json
import os
import time
import numpy as np
import pandas as pd
import requests
import yfinance as yf

MAX_STOCK_PRICE = 150.0

TICKER_LIST_FILE = "active_100_tickers.csv"
OUTPUT_RANKINGS_FILE = "current_ai_rankings.csv"
HTML_DASHBOARD_FILE = "market_dashboard.html"
DAILY_REPORT_FILE = "daily_market_close_report.txt"

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50.0
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    if down == 0: return 100.0
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100.0 - (100.0 / (1.0 + rs))
    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        up_val = delta if delta > 0 else 0.0
        down_val = -delta if delta < 0 else 0.0
        up = (up * (period - 1) + up_val) / period
        down = (down * (period - 1) + down_val) / period
        if down == 0: return 100.0
        rs = up / down
        rsi[i] = 100.0 - (100.0 / (1.0 + rs))
    return rsi[-1]


def get_master_universe():
    return [
        "WULF", "INOD", "SOUN", "QUBT", "ACMR", "POET", "ATOM", "LWLG", 
        "MARA", "RIOT", "CORZ", "VRT", "SMCI", "C3AI", "PATH", "PSTG", 
        "NTAP", "STX", "WDC", "ANET", "JNPR", "CIEN", "EXTR", "LITE", 
        "FN", "CLS", "SANM", "FLEX", "PLAB", "CAMT", "COHR", "DIOD", 
        "MXL", "SGH", "VICR", "AMD", "INTC", "MU", "MRVL", "ADI", 
        "TXN", "MCHP", "NXPI", "ON", "MPWR", "SLAB", "AEHR", "AMKR", 
        "TER", "COGN", "IPG", "FORM", "CREE", "RMBS", "NVDA", "PLTR", 
        "SNOW", "AI", "BBAI", "SERV", "VERI", "CXM", "EGAN", "DT", 
        "NEWR", "SPLK", "CRWD", "NET", "DDOG", "OKTA", "ZS", "DOCU", 
        "MDB", "ESTC", "WK", "S", "ALTR", "CCCS", "UPST", "LYFT", 
        "KTOS", "AVAV", "NNDM", "BKSY", "PL", "RKLB", "ACHR", "JOBY", 
        "OUST", "AEVA", "MVIS", "REKR", "GCT", "ANY", "BITF", "HUT", 
        "MIGI", "CLSK", "SDIG", "BTDR"
    ]

def generate_html_dashboard(df):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Option C Alpha Universe Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #121212; color: #ffffff; margin: 10px; padding: 0; }}
        .container {{ width: 100%; max-width: 1100px; margin: 0 auto; }}
        h2 {{ text-align: center; color: #ffffff; font-weight: 400; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px; }}
        
        .clock-panel {{ display: flex; justify-content: space-around; background-color: #000000; border: 1px solid #333333; padding: 15px; margin-bottom: 20px; border-radius: 6px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.5); }}
        .clock-box {{ flex: 1; }}
        .clock-label {{ font-size: 11px; color: #888888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
        .clock-time {{ font-size: 20px; font-weight: bold; color: #ffffff; font-family: monospace; }}
        
        table {{ width: 100%; border-collapse: collapse; background-color: #ffffff; color: #000000; box-shadow: 0 4px 10px rgba(0,0,0,0.4); font-size: 14px; }}
        th {{ background-color: #000000; color: #ffffff; padding: 14px 10px; text-align: left; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; border-bottom: 2px solid #333333; }}
        td {{ padding: 12px 10px; border-bottom: 1px solid #e0e0e0; }}
        
        .row-white {{ background-color: #ffffff; color: #000000; }}
        .row-black {{ background-color: #000000; color: #ffffff; border-bottom: 1px solid #222222; }}
        
        /* Premium Custom High-Contrast Highlights */
        .spring-highlight {{ background-color: #1a5f20 !important; color: #ffffff !important; font-weight: bold; }}      /* Dark Green + White text */
        .signal-orange-highlight {{ background-color: #ffb84d !important; color: #000000 !important; font-weight: bold; }} /* Light Orange + Black text */
        .signal-red-highlight {{ background-color: #ff3333 !important; color: #000000 !important; font-weight: bold; }}    /* Bright Red + Black text */
        
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; display: inline-block; text-transform: uppercase; border: 1px solid rgba(0,0,0,0.2); }}
    </style>
</head>
<body>
    <div class="container">
        <h2>AI Processing Leaderboard</h2>
        <div class="clock-panel">
            <div class="clock-box">
                <div class="clock-label">Local Sydney Time (AEST)</div>
                <div class="clock-time" id="aest-clock">--:--:--</div>
            </div>
            <div class="clock-box" style="border-left: 1px solid #222222;">
                <div class="clock-label" id="countdown-label">US Market Clock</div>
                <div class="clock-time" id="countdown-clock">--:--:--</div>
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Node Ticker</th><th>Price Field</th><th>Short Float</th><th>DTC Window</th>
                    <th>RVOL Ratio</th><th>14D RSI</th><th>Computed Risk Score</th><th>Current Strategy Phase</th>
                </tr>
            </thead>
            <tbody>"""
    
    for idx, row in df.iterrows():
        row_class = "row-white" if idx % 2 == 0 else "row-black"
        
        # Apply strict requested phase colour themes
        if row["Trading Phase"] == "🚨 READY TO SPRING":
            row_class = "spring-highlight"
            badge = f'<span class="badge" style="background-color: #2e7d32; color: #ffffff;">{{row["Trading Phase"]}}</span>'
        elif row["Trading Phase"] == "🚨 BUY PHASE":
            row_class = "signal-orange-highlight"
            badge = f'<span class="badge" style="background-color: #ffa524; color: #000000;">{{row["Trading Phase"]}}</span>'
        elif row["Trading Phase"] == "💥 TAKE PROFIT / SELL":
            row_class = "signal-red-highlight"
            badge = f'<span class="badge" style="background-color: #cc0000; color: #ffffff;">{{row["Trading Phase"]}}</span>'
        else:
            badge = f'<span class="badge" style="background-color: #555555; color: #ffffff;">{{row["Trading Phase"]}}</span>'

        html_content += f"""
                <tr class="{{row_class}}">
                    <td><strong>{{row['Ticker']}}</strong></td><td>${{row['Price ($)']:.2f}}</td>
                    <td>{{row['Short Interest %']:.1f}}%</td><td>{{row['Days to Cover']:.1f}}d</td>
                    <td>{{row['RVOL']:.2f}x</td><td>{{row['RSI']:.1f}}</td>
                    <td><strong>{{row['Risk_Score']:.1f}}</strong></td><td>{{badge}}</td>
                </tr>"""
                
    html_content += """
            </tbody>
        </table>
    </div>
    <script>
    function updateClocks() {
        let now = new Date();
        document.getElementById("aest-clock").innerText = now.toLocaleTimeString("en-AU", {timeZone: "Australia/Sydney", hour12: false});
        let nyString = now.toLocaleString("en-US", {timeZone: "America/New_York"});
        let nyDate = new Date(nyString);
        let currentDay = nyDate.getDay();
        let currentHour = nyDate.getHours();
        let currentMinute = nyDate.getMinutes();
        let currentSecond = nyDate.getSeconds();
        let label = document.getElementById("countdown-label");
        let clock = document.getElementById("countdown-clock");
        let currentMinutesInDay = (currentHour * 60) + currentMinute;
        let marketOpenMinutes = (9 * 60) + 30;
        let marketCloseMinutes = (16 * 60) + 0;
        let isWeekend = (currentDay === 0 || currentDay === 6);
        let isMarketOpenHours = (!isWeekend && currentMinutesInDay >= marketOpenMinutes && currentMinutesInDay < marketCloseMinutes);

        if (isMarketOpenHours) {
            label.innerText = "Time Until Close (Market Open)";
            label.style.color = "#00cc44";
            clock.style.color = "#00cc44";
            let totalSecondsLeft = ((marketCloseMinutes - currentMinutesInDay) * 60) - currentSecond;
            clock.innerText = formatTimeDuration(totalSecondsLeft);
        } else {
            label.innerText = "Time Until Next Open (Market Closed)";
            label.style.color = "#ff3333";
            clock.style.color = "#ff3333";
            let targetDate = new Date(nyString);
            targetDate.setHours(9, 30, 0, 0);
            if (currentMinutesInDay >= marketCloseMinutes) targetDate.setDate(targetDate.getDate() + 1);
            while (targetDate.getDay() === 0 || targetDate.getDay() === 6) targetDate.setDate(targetDate.getDate() + 1);
            let diffMs = targetDate - new Date(now.toLocaleString("en-US", {timeZone: "America/New_York"}));
            clock.innerText = formatTimeDuration(Math.floor(diffMs / 1000));
        }
    }
    function formatTimeDuration(seconds) {
        let h = Math.floor(seconds / 3600);
        let m = Math.floor((seconds % 3600) / 60);
        let s = seconds % 60;
        return [h.toString().padStart(2, '0'), m.toString().padStart(2, '0'), s.toString().padStart(2, '0')].join(':');
    }
    setInterval(updateClocks, 1000);
    updateClocks();
    </script>
</body>
</html>"""
    with open(HTML_DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("📊 Dashboard visual formatting layout updated successfully.")


def hourly_rank_update():
    print("🕒 Accessing Active 100 Network Array for Hourly Update...")
    if not os.path.exists(TICKER_LIST_FILE):
        rebalance_ticker_universe()

    active_tickers = pd.read_csv(TICKER_LIST_FILE)["Ticker"].tolist()
    valid_data = []
    market_history = yf.download(" ".join(active_tickers), period="30d", group_by="ticker", progress=False)

    for ticker in active_tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            history = market_history[ticker].dropna() if ticker in market_history.columns.levels else stock.history(period="30d")
            if len(history) < 20: continue

            price = info.get("currentPrice", history["Close"].iloc[-1])
            short_pct = info.get("shortPercentOfFloat", 0) * 100
            dtc = info.get("shortRatio", 0)

            close_prices = history["Close"].to_numpy()
            current_volume = info.get("volume", history["Volume"].iloc[-1])
            avg_volume = info.get("averageVolume", history["Volume"].mean())

            rvol = current_volume / avg_volume if avg_volume > 0 else 1.0
            rsi_value = calculate_rsi(close_prices, period=14)
            sma_20 = history["Close"].tail(20).mean()

            base_risk = short_pct + (dtc * 2.0)
            if price > sma_20: base_risk *= 0.9
            if rsi_value > 80: base_risk *= 1.3

            if rsi_value >= 80.0 or rvol >= 4.0:
                trading_phase = "💥 TAKE PROFIT / SELL"
            elif price > sma_20 and rvol >= 1.8 and 45.0 <= rsi_value <= 65.0 and dtc > 5.0:
                trading_phase = "🚨 READY TO SPRING"
            elif price > sma_20 and rvol >= 1.5 and rsi_value < 70.0:
                trading_phase = "🚨 BUY PHASE"
            else:
                trading_phase = "HOLD / ACCUMULATE"

            valid_data.append({
                "Ticker": ticker, "Price ($)": price, "Short Interest %": short_pct,
                "Days to Cover": dtc, "RVOL": rvol, "RSI": rsi_value, 
                "Trading Phase": trading_phase, "Risk_Score": base_risk
            })
        except Exception:
            continue

    if valid_data:
        df_output = pd.DataFrame(valid_data)
        df_output = df_output.sort_values(by="Risk_Score", ascending=True).reset_index(drop=True)
        df_output.to_csv(OUTPUT_RANKINGS_FILE, index=False)
        generate_html_dashboard(df_output)

def rebalance_ticker_universe():
    print("🔄 Initialising End of Session Processing Operations...")
    master_list = get_master_universe()
    valid_companies = []
    daily_phase_report = []
    market_history = yf.download(" ".join(master_list), period="30d", group_by="ticker", progress=False)

    for ticker in master_list:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            history = market_history[ticker].dropna()

            price = info.get("currentPrice", history["Close"].iloc[-1])
            if price == 0 or price > MAX_STOCK_PRICE: continue

            short_pct = info.get("shortPercentOfFloat", 0) * 100
            dtc = info.get("shortRatio", 0)

            close_prices = history["Close"].to_numpy()
            rvol = info.get("volume", history["Volume"].iloc[-1]) / history["Volume"].mean()
            rsi_value = calculate_rsi(close_prices, period=14)
            sma_20 = history["Close"].tail(20).mean()

            sorting_score = short_pct * dtc
            valid_companies.append({"Ticker": ticker, "Sorting_Score": sorting_score})

            if rsi_value >= 80.0 or rvol >= 4.0:
                daily_phase_report.append(f"→ {ticker:5} | [SELL PHASE]: Overbought momentum peak.")
            elif price > sma_20 and rvol >= 1.5 and rsi_value < 70.0:
                daily_phase_report.append(f"→ {ticker:5} | [BUY PHASE] : Strategic entry build phase.")
        except Exception:
            continue

    df_universe = pd.DataFrame(valid_companies)
    if not df_universe.empty:
        df_universe = df_universe.sort_values(by="Sorting_Score", ascending=False).head(100)
    df_universe[["Ticker"]].to_csv(TICKER_LIST_FILE, index=False)

    with open(DAILY_REPORT_FILE, "w") as f:
        f.write("=================================================================\n"
                "   OPTION C DAILY SUMMARY CLOSING ENGINE ACTION REPORT\n"
                "=================================================================\n\n")
        if daily_phase_report: f.write("\n".join(daily_phase_report))
        else: f.write("No monitored nodes triggered actionable close conditions.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv == "--rebalance":
        rebalance_ticker_universe()
    else:
        hourly_rank_update()
