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


# ===================== REAL ORDER FUNKSIYALARI =====================

def get_market_info(symbol):
    """Coin uchun bozor ma'lumotlarini olish (min order, precision)"""
    try:
        markets = exchange.load_markets()
        if symbol in markets:
            market = markets[symbol]
            min_amount = market.get("limits", {}).get("amount", {}).get("min", 0)
            min_cost = market.get("limits", {}).get("cost", {}).get("min", 5)
            amount_precision = market.get("precision", {}).get("amount", 6)
            price_precision = market.get("precision", {}).get("price", 2)
            return {
                "min_amount": min_amount if min_amount else 0,
                "min_cost": min_cost if min_cost else 5,
                "amount_precision": amount_precision,
                "price_precision": price_precision
            }
        return {"min_amount": 0, "min_cost": 5, "amount_precision": 6, "price_precision": 2}
    except Exception as e:
        return {"min_amount": 0, "min_cost": 5, "amount_precision": 6, "price_precision": 2}


def calculate_quantity(symbol, usd_amount, current_price):
    """USD summani coin miqdoriga aylantirish (precision bilan)"""
    info = get_market_info(symbol)
    quantity = usd_amount / current_price
    precision = info["amount_precision"]
    if isinstance(precision, int):
        quantity = round(quantity, precision)
    else:
        quantity = float(exchange.amount_to_precision(symbol, quantity))
    return quantity


def check_min_order(symbol, usd_amount, current_price):
    """Order minimum talablarga javob beradimi?"""
    info = get_market_info(symbol)
    quantity = usd_amount / current_price
    if usd_amount < info["min_cost"]:
        return False, "Min order: $" + str(info["min_cost"]) + " (siz: $" + str(round(usd_amount, 2)) + ")"
    if info["min_amount"] and quantity < info["min_amount"]:
        return False, "Min miqdor: " + str(info["min_amount"])
    return True, "OK"


def place_market_buy(symbol, usd_amount):
    """HAQIQIY market BUY order qo'yish"""
    try:
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker["last"]
        ok, msg = check_min_order(symbol, usd_amount, current_price)
        if not ok:
            return None, msg
        quantity = calculate_quantity(symbol, usd_amount, current_price)
        order = exchange.create_market_buy_order(symbol, quantity)
        return order, "BUY bajarildi: " + str(quantity) + " " + symbol
    except Exception as e:
        return None, "BUY xato: " + str(e)


def place_market_sell(symbol, quantity):
    """HAQIQIY market SELL order qo'yish"""
    try:
        order = exchange.create_market_sell_order(symbol, quantity)
        return order, "SELL bajarildi: " + str(quantity) + " " + symbol
    except Exception as e:
        return None, "SELL xato: " + str(e)


def get_asset_quantity(symbol):
    """Coin dan qancha borligini olish (sotish uchun)"""
    try:
        base_asset = symbol.split("/")[0]
        balance = exchange.fetch_balance()
        asset = balance.get(base_asset, {})
        return float(asset.get("free", 0))
    except Exception as e:
        return 0


def emergency_close_all():
    """FAVQULODDA: barcha ochiq pozitsiyalarni yopish"""
    closed = []
    try:
        balance = exchange.fetch_balance()
        for asset in balance.get("total", {}):
            if asset in ["USDT", "BUSD", "USDC"]:
                continue
            amount = float(balance["free"].get(asset, 0))
            if amount > 0:
                symbol = asset + "/USDT"
                try:
                    order, msg = place_market_sell(symbol, amount)
                    if order:
                        closed.append(symbol)
                except:
                    pass
    except Exception as e:
        pass
    return closed