import ta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import EMA_SHORT, EMA_LONG

def calculate_indicators(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_diff"] = macd.macd_diff()

    bb = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["close"] * 100

    df["ema_short"] = ta.trend.EMAIndicator(df["close"], window=EMA_SHORT).ema_indicator()
    df["ema_long"] = ta.trend.EMAIndicator(df["close"], window=EMA_LONG).ema_indicator()
    df["ema_diff"] = (df["ema_short"] - df["ema_long"]) / df["close"] * 100

    df["volume_sma"] = df["volume"].rolling(window=20).mean()
    df["volume_now"] = df["volume"]
    df["volume_ratio"] = df["volume"] / df["volume_sma"]

    df["atr"] = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
    df["atr_pct"] = df["atr"] / df["close"] * 100

    df["change_1"] = df["close"].pct_change(1) * 100
    df["change_3"] = df["close"].pct_change(3) * 100
    df["change_5"] = df["close"].pct_change(5) * 100
    df["change_10"] = df["close"].pct_change(10) * 100

    stoch = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"])
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()

    adx = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14)
    df["adx"] = adx.adx()
    
    # Breakout uchun 24h High/Low (5min * 288 = 24 soat)
    df["high_24h"] = df["high"].rolling(window=288).max()
    df["low_24h"] = df["low"].rolling(window=288).min()

    return df

def get_trend(row):
    if row["ema_short"] > row["ema_long"]:
        return "UP"
    elif row["ema_short"] < row["ema_long"]:
        return "DOWN"
    return "FLAT"
