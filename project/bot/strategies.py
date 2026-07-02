import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    RSI_OVERSOLD, RSI_OVERBOUGHT, MIN_SIGNALS,
    DYNAMIC_SLTP_ENABLED, ATR_SL_MULTIPLIER, ATR_TP_MULTIPLIER,
    MIN_SL_PCT, MAX_SL_PCT, MIN_TP_PCT, MAX_TP_PCT,
    STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    SESSION_FILTER_ENABLED, ACTIVE_HOURS_START, ACTIVE_HOURS_END,
    PORTFOLIO_BALANCE_ENABLED, MAX_SAME_DIRECTION, MAX_PER_SECTOR, SECTOR_MAP
)
from bot.indicators import get_trend
 
def is_trading_session():
    """Hozir savdo qilish vaqtimi? (UTC bo'yicha)"""
    if not SESSION_FILTER_ENABLED:
        return True, "Filter o'chiq"
 
    utc_now = datetime.now(timezone.utc)
    current_hour = utc_now.hour
 
    if ACTIVE_HOURS_START <= ACTIVE_HOURS_END:
        # Oddiy holat: masalan 7-22
        is_active = ACTIVE_HOURS_START <= current_hour < ACTIVE_HOURS_END
    else:
        # Tun oralig'i: masalan 22-7
        is_active = current_hour >= ACTIVE_HOURS_START or current_hour < ACTIVE_HOURS_END
 
    if is_active:
        return True, "Aktiv session"
    else:
        return False, "Session yopiq (UTC " + str(ACTIVE_HOURS_START) + "-" + str(ACTIVE_HOURS_END) + ")"

def calculate_dynamic_sltp(row):
    """ATR ga qarab har coin uchun alohida SL/TP hisoblash"""
    if not DYNAMIC_SLTP_ENABLED:
        return STOP_LOSS_PCT, TAKE_PROFIT_PCT
 
    atr_pct = row["atr_pct"]
 
    # SL va TP hisoblash
    sl = atr_pct * ATR_SL_MULTIPLIER
    tp = atr_pct * ATR_TP_MULTIPLIER
 
    # Chegaralar (juda kichik yoki katta bo'lmasin)
    sl = max(MIN_SL_PCT, min(MAX_SL_PCT, sl))
    tp = max(MIN_TP_PCT, min(MAX_TP_PCT, tp))
 
    return round(sl, 2), round(tp, 2)

def check_trend_buy(row, prev):
    b = 0
    if row["rsi"] < 35:
        b += 1
    if prev["macd_diff"] < 0 and row["macd_diff"] > 0:
        b += 1
    if row["close"] <= row["bb_lower"]:
        b += 1
    if row["volume_now"] > row["volume_sma"] * 1.2:
        b += 1
    return b

def check_trend_sell(row, prev):
    s = 0
    if row["rsi"] > 65:
        s += 1
    if prev["macd_diff"] > 0 and row["macd_diff"] < 0:
        s += 1
    if row["close"] >= row["bb_upper"]:
        s += 1
    if row["volume_now"] > row["volume_sma"] * 1.2:
        s += 1
    return s

def check_mean_reversion(row, prev):
    if row["rsi"] < RSI_OVERSOLD and row["close"] <= row["bb_lower"]:
        return "BUY"
    if row["rsi"] > RSI_OVERBOUGHT and row["close"] >= row["bb_upper"]:
        return "SELL"
    return None
 
def check_breakout(row, prev):
    """Breakout strategiyasi - 24h High/Low sindirilganda"""
    if "high_24h" not in row or "low_24h" not in row:
        return None
 
    # Narx 24h yuqori chekkani sindirsa = BUY
    if row["close"] > row["high_24h"] * 0.998 and row["volume_ratio"] > 1.5:
        return "BUY"
 
    # Narx 24h pastki chekkani sindirsa = SELL
    if row["close"] < row["low_24h"] * 1.002 and row["volume_ratio"] > 1.5:
        return "SELL"
    return None

def get_signal(row, prev, trend):
    signal_type = None
    signal_dir = None
    strategy_name = ""

    if trend == "UP" and check_trend_buy(row, prev) >= MIN_SIGNALS:
        signal_type = "LONG"
        signal_dir = "UP"
        strategy_name = "Trend"
    elif trend == "DOWN" and check_trend_sell(row, prev) >= MIN_SIGNALS:
        signal_type = "SHORT"
        signal_dir = "DOWN"
        strategy_name = "Trend"

    if signal_type is None:
        mr_signal = check_mean_reversion(row, prev)
        if mr_signal == "BUY":
            signal_type = "LONG"
            signal_dir = "MR"
            strategy_name = "MeanRev"
        elif mr_signal == "SELL":
            signal_type = "SHORT"
            signal_dir = "MR"
            strategy_name = "MeanRev"

  # Strategiya 3: Breakout
    if signal_type is None:
        bo_signal = check_breakout(row, prev)
        if bo_signal == "BUY":
            signal_type = "LONG"
            signal_dir = "BO"
            strategy_name = "Breakout"
        elif bo_signal == "SELL":
            signal_type = "SHORT"
            signal_dir = "BO"
            strategy_name = "Breakout"

    return signal_type, signal_dir, strategy_name

def get_coin_sector(symbol):
    """Coinning sektorini aniqlash"""
    for sector, coins in SECTOR_MAP.items():
        if symbol in coins:
            return sector
    return "other"

def check_portfolio_balance(symbol, signal_type, open_positions):
    """Portfolio diversifikatsiyasini tekshirish"""
    if not PORTFOLIO_BALANCE_ENABLED:
        return True, "Filter o'chiq"
 
    # 1. Bir yo'nalishda juda ko'p pozitsiya bormi?
    same_direction_count = 0
    for sym, pos in open_positions.items():
        if pos["type"] == signal_type:
            same_direction_count += 1
 
    if same_direction_count >= MAX_SAME_DIRECTION:
        return False, "Max " + signal_type + " (" + str(MAX_SAME_DIRECTION) + ") to'ldi"
 
    # 2. Bir sektorda juda ko'p pozitsiya bormi?
    coin_sector = get_coin_sector(symbol)
    sector_count = 0
    for sym, pos in open_positions.items():
        if get_coin_sector(sym) == coin_sector:
            sector_count += 1
 
    if sector_count >= MAX_PER_SECTOR:
        return False, "Sektor '" + coin_sector + "' to'ldi (" + str(MAX_PER_SECTOR) + " max)"
 
    return True, "OK"

def check_multi_timeframe(symbol, exchange, signal_type):
    """Yuqori timeframlarda trend mos kelishini tekshirish"""
    from config.settings import MULTI_TIMEFRAME_ENABLED, TIMEFRAMES
    from bot.indicators import calculate_indicators, get_trend
    import pandas as pd
 
    if not MULTI_TIMEFRAME_ENABLED:
        return True, "MTF o'chiq"
 
    confirmations = 0
    total_checks = 0
 
    # 15m va 1h timeframlarni tekshirish (5m dan tashqari)
    higher_timeframes = [tf for tf in TIMEFRAMES if tf != "5m"]
 
    for tf in higher_timeframes:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=100)
            df = pd.DataFrame(ohlcv, columns=["time", "open", "high", "low", "close", "volume"])
            df["close"] = df["close"].astype(float)
            df["high"] = df["high"].astype(float)
            df["low"] = df["low"].astype(float)
            df["open"] = df["open"].astype(float)
            df["volume"] = df["volume"].astype(float)
 
            df = calculate_indicators(df)
            df = df.dropna().reset_index(drop=True)
 
            if len(df) < 2:
                continue
 
            row = df.iloc[-1]
            trend = get_trend(row)
            total_checks += 1
 
            # LONG signal uchun trend UP bo'lishi kerak
            if signal_type == "LONG" and trend == "UP":
                confirmations += 1
            # SHORT signal uchun trend DOWN bo'lishi kerak
            elif signal_type == "SHORT" and trend == "DOWN":
                confirmations += 1
 
        except Exception as e:
            pass
 
    # Kamida 1 ta yuqori timeframe tasdiqlashi kerak
    if total_checks == 0:
        return True, "MTF: data yo'q"
 
    if confirmations >= 1:
        return True, "MTF: " + str(confirmations) + "/" + str(total_checks) + " tasdiqladi"
    else:
        return False, "MTF: trend mos kelmadi (" + str(confirmations) + "/" + str(total_checks) + ")"
    
def check_btc_correlation(exchange):
    """BTC bilan korrelyatsiya tekshirish - BTC tushsa altcoinlar ham tushadi"""
    from config.settings import TIMEFRAME
    from bot.indicators import calculate_indicators, get_trend
    import pandas as pd
 
    try:
        ohlcv = exchange.fetch_ohlcv("BTC/USDT", TIMEFRAME, limit=50)
        df = pd.DataFrame(ohlcv, columns=["time", "open", "high", "low", "close", "volume"])
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["open"] = df["open"].astype(float)
        df["volume"] = df["volume"].astype(float)
 
        df = calculate_indicators(df)
        df = df.dropna().reset_index(drop=True)
 
        if len(df) < 2:
            return "NEUTRAL", "BTC: data yetarli emas"
 
        row = df.iloc[-1]
        btc_change = row["change_5"]
        btc_rsi = row["rsi"]
 
        if btc_change < -2.0 and btc_rsi < 35:
            return "BEARISH", "BTC kuchli tushmoqda (" + str(round(btc_change, 1)) + "%)"
 
        if btc_change > 2.0 and btc_rsi > 65:
            return "BULLISH", "BTC kuchli ko'tarilmoqda (+" + str(round(btc_change, 1)) + "%)"
 
        return "NEUTRAL", "BTC: normal (" + str(round(btc_change, 1)) + "%)"
 
    except Exception as e:
        return "NEUTRAL", "BTC tekshirish xato"
 
def check_correlation_filter(symbol, signal_type, exchange):
    """Korrelyatsiya filtri - BTC holatiga qarab altcoin savdosini tekshirish"""
    if symbol == "BTC/USDT":
        return True, "BTC - filtr o'tkazildi"
 
    btc_state, btc_msg = check_btc_correlation(exchange)
 
    if btc_state == "BEARISH" and signal_type == "LONG":
        return False, "Korrelatsiya: " + btc_msg + " - LONG xavfli"
 
    if btc_state == "BULLISH" and signal_type == "SHORT":
        return False, "Korrelatsiya: " + btc_msg + " - SHORT xavfli"
 
    return True, "Korrelatsiya: OK"
 
 
def get_fear_greed_index():
    """Crypto Fear & Greed Index olish (0-100)
    0-25: Extreme Fear (juda qo'rquv)
    25-45: Fear (qo'rquv)
    45-55: Neutral
    55-75: Greed (ochko'zlik)
    75-100: Extreme Greed (juda ochko'zlik)
    """
    import requests
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        value = int(data["data"][0]["value"])
        classification = data["data"][0]["value_classification"]
        return value, classification
    except Exception as e:
        return 50, "Neutral"
 
def check_sentiment_filter(signal_type):
    """Bozor kayfiyatiga qarab savdo qilish
    Extreme Fear (0-20): Faqat LONG (tushgan bozor — sotib olish vaqti)
    Extreme Greed (80-100): Faqat SHORT (ko'tarilgan bozor — sotish vaqti)
    Normal (20-80): Ikkalasi ham ruxsat
    """
    value, classification = get_fear_greed_index()
 
    # Extreme Fear — faqat BUY (tushgan narxda sotib olish)
    if value <= 20:
        if signal_type == "SHORT":
            return False, "Sentiment: Extreme Fear (" + str(value) + ") - SHORT xavfli"
        return True, "Sentiment: Extreme Fear (" + str(value) + ") - LONG yaxshi!"
 
    # Extreme Greed — faqat SELL (oshgan narxda sotish)
    if value >= 80:
        if signal_type == "LONG":
            return False, "Sentiment: Extreme Greed (" + str(value) + ") - LONG xavfli"
        return True, "Sentiment: Extreme Greed (" + str(value) + ") - SHORT yaxshi!"
 
    # Normal zona — hammasi ruxsat
    return True, "Sentiment: " + classification + " (" + str(value) + ")"    

 
def detect_order_blocks(df):
    """Order Block aniqlash - Institutional treyderlar savdo qilgan zonalar"""
    last_10 = df.tail(15).reset_index(drop=True)
    ob_buy = None
    ob_sell = None
 
    for i in range(2, len(last_10) - 1):
        # Bullish Order Block: kuchli pastga sham + keyin kuchli yuqoriga
        if (last_10.iloc[i]["close"] < last_10.iloc[i]["open"] and
            last_10.iloc[i + 1]["close"] > last_10.iloc[i + 1]["open"] and
            last_10.iloc[i + 1]["close"] > last_10.iloc[i]["open"]):
            ob_buy = last_10.iloc[i]["low"]
 
        # Bearish Order Block: kuchli yuqoriga sham + keyin kuchli pastga
        if (last_10.iloc[i]["close"] > last_10.iloc[i]["open"] and
            last_10.iloc[i + 1]["close"] < last_10.iloc[i + 1]["open"] and
            last_10.iloc[i + 1]["close"] < last_10.iloc[i]["open"]):
            ob_sell = last_10.iloc[i]["high"]
 
    return ob_buy, ob_sell
 
 
def detect_fair_value_gap(df):
    """Fair Value Gap (FVG) aniqlash - narxda bo'shliq"""
    last = df.tail(5).reset_index(drop=True)
    fvg_buy = None
    fvg_sell = None
 
    for i in range(1, len(last) - 1):
        # Bullish FVG: 1-sham high < 3-sham low (bo'shliq yuqoriga)
        if last.iloc[i - 1]["high"] < last.iloc[i + 1]["low"]:
            fvg_buy = (last.iloc[i - 1]["high"] + last.iloc[i + 1]["low"]) / 2
 
        # Bearish FVG: 1-sham low > 3-sham high (bo'shliq pastga)
        if last.iloc[i - 1]["low"] > last.iloc[i + 1]["high"]:
            fvg_sell = (last.iloc[i - 1]["low"] + last.iloc[i + 1]["high"]) / 2
 
    return fvg_buy, fvg_sell
 
 
def detect_liquidity_sweep(df):
    """Liquidity Sweep aniqlash - yolg'on sindirish"""
    last_20 = df.tail(20).reset_index(drop=True)
    last = df.iloc[-1]
 
    # Oxirgi 20 shamning eng past va eng yuqori nuqtalari
    recent_low = last_20["low"].min()
    recent_high = last_20["high"].max()
 
    sweep_buy = False
    sweep_sell = False
 
    # Narx pastki likvidlikni yig'ib, qaytib ko'tarilsa = BUY signal
    if last["low"] <= recent_low * 1.001 and last["close"] > last["open"]:
        sweep_buy = True
 
    # Narx yuqori likvidlikni yig'ib, qaytib tushsa = SELL signal
    if last["high"] >= recent_high * 0.999 and last["close"] < last["open"]:
        sweep_sell = True
 
    return sweep_buy, sweep_sell
 
 
def check_smart_money(row, prev, df):
    """Smart Money Concepts strategiyasi
    Order Blocks + FVG + Liquidity Sweep
    """
    current_price = row["close"]
 
    # Order Blocks
    ob_buy, ob_sell = detect_order_blocks(df)
 
    # Fair Value Gap
    fvg_buy, fvg_sell = detect_fair_value_gap(df)
 
    # Liquidity Sweep
    sweep_buy, sweep_sell = detect_liquidity_sweep(df)
 
    # BUY signal: narx OB yaqinida + FVG yoki Sweep
    buy_score = 0
    if ob_buy and current_price <= ob_buy * 1.005:
        buy_score += 1
    if fvg_buy and current_price <= fvg_buy * 1.003:
        buy_score += 1
    if sweep_buy:
        buy_score += 1
    if row["rsi"] < 40:
        buy_score += 1
 
    # SELL signal: narx OB yaqinida + FVG yoki Sweep
    sell_score = 0
    if ob_sell and current_price >= ob_sell * 0.995:
        sell_score += 1
    if fvg_sell and current_price >= fvg_sell * 0.997:
        sell_score += 1
    if sweep_sell:
        sell_score += 1
    if row["rsi"] > 60:
        sell_score += 1
 
    # Kamida 2 ta SMC signal mos kelishi kerak
    if buy_score >= 2:
        return "BUY"
    if sell_score >= 2:
        return "SELL"
 
    return None