def hourly_rank_update():
    if not os.path.exists(TICKER_LIST_FILE):
        rebalance_ticker_universe()
    active_tickers = pd.read_csv(TICKER_LIST_FILE)["Ticker"].tolist()
    valid_data = []
    market_history = yf.download(
        " ".join(active_tickers), period="30d", group_by="ticker", progress=False
    )
    for ticker in active_tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            history = (
                market_history[ticker].dropna()
                if ticker in market_history.columns.levels
                else stock.history(period="30d")
            )
            if len(history) < 20:
                continue
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
            if price > sma_20:
                base_risk *= 0.9
            if rsi_value > 80:
                base_risk *= 1.3
            if rsi_value >= 80.0 or rvol >= 4.0:
                trading_phase = "💥 TAKE PROFIT / SELL"
            elif (
                price > sma_20
                and rvol >= 1.8
                and 45.0 <= rsi_value <= 65.0
                and dtc > 5.0
            ):
                trading_phase = "🚨 READY TO SPRING"
            elif price > sma_20 and rvol >= 1.5 and rsi_value < 70.0:
                trading_phase = "🚨 BUY PHASE"
            else:
                trading_phase = "HOLD / ACCUMULATE"
            valid_data.append(
                {
                    "Ticker": ticker,
                    "Price ($)": price,
                    "Short Interest %": short_pct,
                    "Days to Cover": dtc,
                    "RVOL": rvol,
                    "RSI": rsi_value,
                    "Trading Phase": trading_phase,
                    "Risk_Score": base_risk,
                }
            )
        except:
            continue
    if valid_data:
        df_output = pd.DataFrame(valid_data).sort_values(
            by="Risk_Score", ascending=True
        )
        df_output.to_csv(OUTPUT_RANKINGS_FILE, index=False)
        generate_html_dashboard(df_output)


def rebalance_ticker_universe():
    master_list = get_master_universe()
    valid_companies, daily_phase_report = [], []
    market_history = yf.download(
        " ".join(master_list), period="30d", group_by="ticker", progress=False
    )
    for ticker in master_list:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            history = market_history[ticker].dropna()
            price = info.get("currentPrice", history["Close"].iloc[-1])
            if price == 0 or price > MAX_STOCK_PRICE:
                continue
            short_pct = info.get("shortPercentOfFloat", 0) * 100
            dtc = info.get("shortRatio", 0)
            close_prices = history["Close"].to_numpy()
            rvol = (
                info.get("volume", history["Volume"].iloc[-1])
                / history["Volume"].mean()
            )
            rsi_value = calculate_rsi(close_prices, period=14)
            sma_20 = history["Close"].tail(20).mean()
            valid_companies.append(
                {"Ticker": ticker, "Sorting_Score": short_pct * dtc}
            )
            if rsi_value >= 80.0 or rvol >= 4.0:
                daily_phase_report.append(
                    f"→ {ticker:5} | [SELL PHASE]: Overbought momentum peak."
                )
            elif price > sma_20 and rvol >= 1.5 and rsi_value < 70.0:
                daily_phase_report.append(
                    f"→ {ticker:5} | [BUY PHASE] : Strategic entry build phase."
                )
        except:
            continue
    df_universe = pd.DataFrame(valid_companies)
    if not df_universe.empty:
        df_universe = df_universe.sort_values(
            by="Sorting_Score", ascending=False
        ).head(100)
    df_universe[["Ticker"]].to_csv(TICKER_LIST_FILE, index=False)
    with open(DAILY_REPORT_FILE, "w") as f:
        f.write(
            "=================================================================\n"
            "   OPTION C DAILY SUMMARY CLOSING ENGINE ACTION REPORT\n"
            "=================================================================\n\n"
        )
        if daily_phase_report:
            f.write("\n".join(daily_phase_report))
        else:
            f.write("No monitored nodes triggered actionable close conditions.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv == "--rebalance":
        rebalance_ticker_universe()
    else:
        hourly_rank_update()
