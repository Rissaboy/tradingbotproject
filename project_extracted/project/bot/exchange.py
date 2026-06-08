import ccxt
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import EXCHANGE_NAME, USE_TESTNET, TIMEFRAME
from config.api_keys import API_KEY, API_SECRET


def create_exchange():
    """Birjaga ulanish yaratish"""
    exchange_config = {
        "apiKey": API_KEY,
        "secret": API_SECRET,
        "enableRateLimit": True,
        "timeout": 30000,
    }

    if EXCHANGE_NAME == "binance":
        exchange = ccxt.binance(exchange_config)
        if USE_TESTNET:
            exchange.set_sandbox_mode(True)
    elif EXCHANGE_NAME == "bybit":
        exchange = ccxt.bybit(exchange_config)
        if USE_TESTNET:
            exchange.set_sandbox_mode(True)
    elif EXCHANGE_NAME == "mexc":
        exchange = ccxt.mexc(exchange_config)
    elif EXCHANGE_NAME == "gateio":
        exchange = ccxt.gateio(exchange_config)
    elif EXCHANGE_NAME == "bingx":
        exchange = ccxt.bingx(exchange_config)
    else:
        exchange = ccxt.binance(exchange_config)

    return exchange


# Global exchange obyekt
exchange = create_exchange()


def get_balance(asset="USDT"):
    """USDT balansni olish"""
    balance = exchange.fetch_balance()
    usdt = balance.get(asset, {})
    return float(usdt.get("free", 0))


def get_klines(symbol):
    """Narx ma'lumotlarini olish (OHLCV)"""
    ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=250)
    df = pd.DataFrame(ohlcv, columns=["time", "open", "high", "low", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["open"] = df["open"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df


def get_exchange_name():
    """Birja nomini qaytarish"""
    return EXCHANGE_NAME.upper()