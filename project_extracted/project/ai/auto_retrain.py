import ccxt
import pandas as pd
import numpy as np
import ta
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import time
import os
import sys
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from config.settings import AI_MODEL_FILE, AI_FEATURES_FILE

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT", "ADA/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT", "BNB/USDT"]
TIMEFRAME = "5m"
DAYS_TO_FETCH = 30

exchange = ccxt.binance({"enableRateLimit": True})


def fetch_data(symbol):
    all_data = []
    since = exchange.milliseconds() - (DAYS_TO_FETCH * 24 * 60 * 60 * 1000)
    while since < exchange.milliseconds():
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, since=since, limit=1000)
            if len(ohlcv) == 0:
                break
            all_data = all_data + ohlcv
            since = ohlcv[-1][0] + 1
            time.sleep(0.3)
        except:
            time.sleep(5)
            break
    df = pd.DataFrame(all_data, columns=["time", "open", "high", "low", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["open"] = df["open"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df


def add_features(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    df["rsi_7"] = ta.momentum.RSIIndicator(df["close"], window=7).rsi()
    df["rsi_21"] = ta.momentum.RSIIndicator(df["close"], window=21).rsi()
    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_diff"] = macd.macd_diff()
    bb = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["close"] * 100
    df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])
    df["ema_short"] = ta.trend.EMAIndicator(df["close"], window=50).ema_indicator()
    df["ema_long"] = ta.trend.EMAIndicator(df["close"], window=200).ema_indicator()
    df["ema_diff"] = (df["ema_short"] - df["ema_long"]) / df["close"] * 100
    df["ema_9"] = ta.trend.EMAIndicator(df["close"], window=9).ema_indicator()
    df["ema_21"] = ta.trend.EMAIndicator(df["close"], window=21).ema_indicator()
    df["ema_9_21_diff"] = (df["ema_9"] - df["ema_21"]) / df["close"] * 100
    df["volume_sma"] = df["volume"].rolling(window=20).mean()
    df["volume_ratio"] = df["volume"] / df["volume_sma"]
    df["volume_change"] = df["volume"].pct_change(1) * 100
    df["atr"] = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
    df["atr_pct"] = df["atr"] / df["close"] * 100
    df["change_1"] = df["close"].pct_change(1) * 100
    df["change_3"] = df["close"].pct_change(3) * 100
    df["change_5"] = df["close"].pct_change(5) * 100
    df["change_10"] = df["close"].pct_change(10) * 100
    df["change_20"] = df["close"].pct_change(20) * 100
    stoch = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"])
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()
    adx = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14)
    df["adx"] = adx.adx()
    df["adx_pos"] = adx.adx_pos()
    df["adx_neg"] = adx.adx_neg()
    df["cci"] = ta.trend.CCIIndicator(df["high"], df["low"], df["close"], window=20).cci()
    df["williams_r"] = ta.momentum.WilliamsRIndicator(df["high"], df["low"], df["close"], lbp=14).williams_r()
    df["obv"] = ta.volume.OnBalanceVolumeIndicator(df["close"], df["volume"]).on_balance_volume()
    df["obv_change"] = df["obv"].pct_change(5) * 100
    df["body_size"] = abs(df["close"] - df["open"]) / df["close"] * 100
    df["upper_shadow"] = (df["high"] - df[["close", "open"]].max(axis=1)) / df["close"] * 100
    df["lower_shadow"] = (df[["close", "open"]].min(axis=1) - df["low"]) / df["close"] * 100
    df["high_distance"] = (df["high"].rolling(24).max() - df["close"]) / df["close"] * 100
    df["low_distance"] = (df["close"] - df["low"].rolling(24).min()) / df["close"] * 100
    return df


def create_labels(df):
    df["future_max"] = df["high"].rolling(window=6).max().shift(-6)
    df["future_min"] = df["low"].rolling(window=6).min().shift(-6)
    df["future_profit"] = (df["future_max"] - df["close"]) / df["close"] * 100
    df["future_loss"] = (df["close"] - df["future_min"]) / df["close"] * 100
    df["label"] = 0
    df.loc[(df["future_profit"] >= 0.8) & (df["future_profit"] > df["future_loss"] * 1.5), "label"] = 1
    return df


def retrain():
    print("")
    print("=" * 60)
    print("  AUTO AI RETRAINING")
    print("  Vaqt: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 60)
    print("")

    all_dfs = []
    for symbol in SYMBOLS:
        print("  " + symbol + " yuklanmoqda...")
        df = fetch_data(symbol)
        df = add_features(df)
        df = create_labels(df)
        all_dfs.append(df)

    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df = full_df.dropna().reset_index(drop=True)

    features = [
        "rsi", "rsi_7", "rsi_21",
        "macd", "macd_signal", "macd_diff",
        "bb_width", "bb_position",
        "ema_diff", "ema_9_21_diff",
        "volume_ratio", "volume_change",
        "atr_pct",
        "change_1", "change_3", "change_5", "change_10", "change_20",
        "stoch_k", "stoch_d",
        "adx", "adx_pos", "adx_neg",
        "cci", "williams_r",
        "obv_change",
        "body_size", "upper_shadow", "lower_shadow",
        "high_distance", "low_distance"
    ]

    X = full_df[features]
    y = full_df["label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

    model = XGBClassifier(
        n_estimators=300,
        max_depth=7,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.7,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        scale_pos_weight=len(y_train[y_train == 0]) / max(len(y_train[y_train == 1]), 1),
        random_state=42,
        eval_metric="logloss"
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("")
    print("  Yangi model Accuracy: " + str(round(accuracy * 100, 1)) + "%")
    print("  Data: " + str(len(full_df)) + " ta")

    # Eski model bilan solishtirish
    model_path = os.path.join(ROOT_DIR, AI_MODEL_FILE)
    features_path = os.path.join(ROOT_DIR, AI_FEATURES_FILE)

    old_accuracy = 0
    if os.path.exists(model_path):
        try:
            old_model = joblib.load(model_path)
            old_pred = old_model.predict(X_test)
            old_accuracy = accuracy_score(y_test, old_pred)
            print("  Eski model Accuracy: " + str(round(old_accuracy * 100, 1)) + "%")
        except:
            old_accuracy = 0

    # Yangi model yaxshiroq bo'lsagina saqlash
    if accuracy >= old_accuracy:
        model_dir = os.path.dirname(model_path)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        joblib.dump(model, model_path)
        joblib.dump(features, features_path)
        print("")
        print("  YANGI MODEL SAQLANDI! (" + str(round(accuracy * 100, 1)) + "% >= " + str(round(old_accuracy * 100, 1)) + "%)")
    else:
        print("")
        print("  Eski model yaxshiroq. Saqlanmadi. (" + str(round(accuracy * 100, 1)) + "% < " + str(round(old_accuracy * 100, 1)) + "%)")

    print("")
    print("  Keyingi retraining: 7 kundan keyin")
    print("=" * 60)

    return accuracy


if __name__ == "__main__":
    retrain()