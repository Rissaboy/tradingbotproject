import ccxt
import pandas as pd
import ta
import time
from datetime import datetime
import json

EXCHANGE_NAME = "binance"
MIN_VOLUME_24H = 10000000
MIN_PRICE = 0.001
MAX_COINS = 30
SCAN_TIMEFRAME = "1h"
QUOTE_CURRENCY = "USDT"

BLACKLIST = ["USDC/USDT", "BUSD/USDT", "TUSD/USDT", "USDP/USDT", "FDUSD/USDT", "DAI/USDT", "USDD/USDT"]

exchange = ccxt.binance({"enableRateLimit": True})

print("")
print("=" * 60)
print("  SARDOR MARKET SCANNER")
print("  1000+ coin ichidan eng yaxshilarini topish")
print("  Birja: " + EXCHANGE_NAME.upper())
print("=" * 60)
print("")

def get_all_usdt_pairs():
    print(">>> Barcha juftliklar yuklanmoqda...")
    markets = exchange.load_markets()
    usdt_pairs = []
    for symbol in markets:
        market = markets[symbol]
        if market["quote"] == QUOTE_CURRENCY and market["active"] and market["spot"]:
            if symbol not in BLACKLIST:
                usdt_pairs.append(symbol)
    print("  Jami USDT juftliklar: " + str(len(usdt_pairs)))
    return usdt_pairs

def get_24h_volume(symbols):
    print(">>> 24 soatlik ma'lumot yuklanmoqda...")
    coin_data = []
    chunk_size = 50
    for i in range(0, len(symbols), chunk_size):
        chunk = symbols[i:i + chunk_size]
        try:
            tickers = exchange.fetch_tickers(chunk)
            for symbol in tickers:
                ticker = tickers[symbol]
                volume_usd = float(ticker.get("quoteVolume", 0) or 0)
                price = float(ticker.get("last", 0) or 0)
                change_24h = float(ticker.get("percentage", 0) or 0)
                if volume_usd >= MIN_VOLUME_24H and price >= MIN_PRICE:
                    coin_data.append({
                        "symbol": symbol,
                        "price": price,
                        "volume_24h": volume_usd,
                        "change_24h": change_24h
                    })
        except Exception as e:
            print("  Chunk xato: " + str(e))
        time.sleep(0.5)
        if (i + chunk_size) % 100 == 0:
            print("  " + str(i + chunk_size) + "/" + str(len(symbols)) + " tekshirildi...")
    print("  Hajm filtri o'tgan: " + str(len(coin_data)) + " ta")
    return coin_data

def analyze_coin(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, SCAN_TIMEFRAME, limit=100)
        if len(ohlcv) < 50:
            return None

        df = pd.DataFrame(ohlcv, columns=["time", "open", "high", "low", "close", "volume"])
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["volume"] = df["volume"].astype(float)

        df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
        df["adx"] = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14).adx()
        df["atr"] = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
        df["ema_20"] = ta.trend.EMAIndicator(df["close"], window=20).ema_indicator()
        df["ema_50"] = ta.trend.EMAIndicator(df["close"], window=50).ema_indicator()

        last = df.iloc[-1]
        volatility = (last["atr"] / last["close"]) * 100

        trend = "FLAT"
        if last["ema_20"] > last["ema_50"]:
            trend = "UP"
        elif last["ema_20"] < last["ema_50"]:
            trend = "DOWN"

        score = 0

        if last["adx"] > 25:
            score = score + 30
        elif last["adx"] > 20:
            score = score + 20
        elif last["adx"] > 15:
            score = score + 10

        if 1.0 <= volatility <= 5.0:
            score = score + 25
        elif 0.5 <= volatility <= 7.0:
            score = score + 15

        if last["rsi"] < 35 or last["rsi"] > 65:
            score = score + 20
        elif last["rsi"] < 40 or last["rsi"] > 60:
            score = score + 10

        if trend != "FLAT":
            score = score + 25

        return {
            "symbol": symbol,
            "score": score,
            "trend": trend,
            "adx": round(last["adx"], 1),
            "rsi": round(last["rsi"], 1),
            "volatility": round(volatility, 2),
        }

    except Exception as e:
        return None

def run_scanner():
    start_time = time.time()

    all_pairs = get_all_usdt_pairs()
    coin_data = get_24h_volume(all_pairs)

    print("")
    print(">>> Texnik tahlil qilmoqda (" + str(len(coin_data)) + " ta coin)...")
    results = []
    count = 0
    for coin in coin_data:
        count = count + 1
        if count % 20 == 0:
            print("  " + str(count) + "/" + str(len(coin_data)) + " tahlil qilindi...")
        result = analyze_coin(coin["symbol"])
        if result is not None:
            result["volume_24h"] = coin["volume_24h"]
            result["change_24h"] = coin["change_24h"]
            result["price"] = coin["price"]
            results.append(result)
        time.sleep(0.3)

    results.sort(key=lambda x: x["score"], reverse=True)
    top_coins = results[:MAX_COINS]

    elapsed = round(time.time() - start_time, 1)
    print("")
    print("=" * 60)
    print("  MARKET SCANNER NATIJALARI")
    print("  Tahlil qilingan: " + str(len(results)) + " ta coin")
    print("  Tanlangan: " + str(len(top_coins)) + " ta eng yaxshi")
    print("  Vaqt: " + str(elapsed) + " soniya")
    print("=" * 60)
    print("")
    print("  TOP " + str(MAX_COINS) + " COINLAR:")
    print("  " + "-" * 70)
    print("  #   Symbol          Score  Trend  ADX    RSI    Vol%   24h%")
    print("  " + "-" * 70)

    for i, coin in enumerate(top_coins):
        num = str(i + 1)
        if len(num) == 1:
            num = " " + num
        sym = coin["symbol"]
        if len(sym) < 14:
            sym = sym + " " * (14 - len(sym))
        print("  " + num + ". " + sym + "  " + str(coin["score"]) + "     " + coin["trend"] + "    " + str(coin["adx"]) + "   " + str(coin["rsi"]) + "   " + str(coin["volatility"]) + "%  " + str(round(coin["change_24h"], 1)) + "%")

    print("  " + "-" * 70)

    symbols_list = [coin["symbol"] for coin in top_coins]
    output = {
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_analyzed": len(results),
        "top_coins": top_coins,
        "symbols": symbols_list
    }

    with open("scanner/top_coins.json", "w") as f:
        json.dump(output, f, indent=2)

    print("")
    print("  Saqlandi: sardor_top_coins.json")
    print("")
    print("  Bot uchun juftliklar ro'yxati:")
    print("  " + str(symbols_list))
    print("")
    print("=" * 60)
    print("  Shu ro'yxatni sardor_trading_bot.py da SYMBOLS ga nusxalang")
    print("  yoki bot avtomatik yuklaydi (sardor_top_coins.json dan)")
    print("=" * 60)

    return symbols_list

if __name__ == "__main__":
    run_scanner()
