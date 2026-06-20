import datetime
import os
import numpy as np
import pandas as pd
import yfinance as yf

MAX_STOCK_PRICE = 150.0
TICKER_LIST_FILE = "active_100_tickers.csv"
OUTPUT_RANKINGS_FILE = "current_ai_rankings.csv"
HTML_DASHBOARD_FILE = "market_dashboard.html"
DAILY_REPORT_FILE = "daily_market_close_report.txt"


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
        "WULF",
        "INOD",
        "SOUN",
        "QUBT",
        "ACMR",
        "POET",
        "ATOM",
        "LWLG",
        "MARA",
        "RIOT",
        "CORZ",
        "VRT",
        "SMCI",
        "C3AI",
        "PATH",
        "PSTG",
        "NTAP",
        "STX",
        "WDC",
        "ANET",
        "JNPR",
        "CIEN",
        "EXTR",
        "LITE",
        "FN",
        "CLS",
        "SANM",
        "FLEX",
        "PLAB",
        "CAMT",
        "COHR",
        "DIOD",
        "MXL",
        "SGH",
        "VICR",
        "AMD",
        "INTC",
        "MU",
        "MRVL",
        "ADI",
        "TXN",
        "MCHP",
        "NXPI",
        "ON",
        "MPWR",
        "SLAB",
        "AEHR",
        "AMKR",
        "TER",
        "COGN",
        "IPG",
        "FORM",
        "CREE",
        "RMBS",
        "NVDA",
        "PLTR",
        "SNOW",
        "AI",
        "BBAI",
        "SERV",
        "VERI",
        "CXM",
        "EGAN",
        "DT",
        "NEWR",
        "SPLK",
        "CRWD",
        "NET",
        "DDOG",
        "OKTA",
        "ZS",
        "DOCU",
        "MDB",
        "ESTC",
        "WK",
        "S",
        "ALTR",
        "CCCS",
        "UPST",
        "LYFT",
        "KTOS",
        "AVAV",
        "NNDM",
        "BKSY",
        "PL",
        "RKLB",
        "ACHR",
        "JOBY",
        "OUST",
        "AEVA",
        "MVIS",
        "REKR",
        "GCT",
        "ANY",
        "BITF",
        "HUT",
        "MIGI",
        "CLSK",
        "SDIG",
        "BTDR",
    ]
