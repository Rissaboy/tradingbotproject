import ccxt
import pandas as pd
import numpy as np
import ta
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import time
import os

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT", "ADA/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT", "BNB/USDT"]
TIMEFRAME = "5m"
DAYS_TO_FETCH = 60

MODEL_DIR = "ai/models"
MODEL_FILE = os.path.join(MODEL_DIR, "sardor_ai_model.pkl")
FEATURES_FILE = os.path.join(MODEL_DIR, "sardor_ai_features.pkl")

exchange = ccxt.binance({"enableRateLimit": True})

print("")
print("=" * 60)
print("  SARDOR AI MODEL TRAINER v2")
print("  XGBoost - kuchaytirilgan versiya")
print("  Juftliklar: " + str(len(SYMBOLS)) + " ta")
print("  Davr: " + str(DAYS_TO_FETCH) + " kun")
print("=" * 60)
print("")

def fetch_data(symbol):
    print("  " + symbol + " yuklanmoqda...")
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
        except Exception as e:
            print("    Xato: " + str(e))
            time.sleep(5)
            break

    df = pd.DataFrame(all_data, columns=["time", "open", "high", "low", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["open"] = df["open"].astype(float)
    df["volume"] = df["volume"].astype(float)
    print("    " + str(len(df)) + " ta sham yuklandi")
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

def create_labels(df, forward_periods=6, profit_threshold=0.8):
    df["future_max"] = df["high"].rolling(window=forward_periods).max().shift(-forward_periods)
    df["future_min"] = df["low"].rolling(window=forward_periods).min().shift(-forward_periods)

    df["future_profit"] = (df["future_max"] - df["close"]) / df["close"] * 100
    df["future_loss"] = (df["close"] - df["future_min"]) / df["close"] * 100

    df["label"] = 0
    df.loc[(df["future_profit"] >= profit_threshold) & (df["future_profit"] > df["future_loss"] * 1.5), "label"] = 1

    return df

def train_model():
    print(">>> Ma'lumot yig'ilmoqda (bu 5-10 daqiqa olishi mumkin)...")
    print("")

    all_dfs = []
    for symbol in SYMBOLS:
        df = fetch_data(symbol)
        df = add_features(df)
        df = create_labels(df)
        df["symbol"] = symbol
        all_dfs.append(df)

    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df = full_df.dropna().reset_index(drop=True)

    print("")
    print(">>> Jami: " + str(len(full_df)) + " ta ma'lumot")
    print(">>> Foydali signallar: " + str(len(full_df[full_df["label"] == 1])) + " (" + str(round(len(full_df[full_df["label"] == 1]) / len(full_df) * 100, 1)) + "%)")
    print(">>> Zarali signallar: " + str(len(full_df[full_df["label"] == 0])) + " (" + str(round(len(full_df[full_df["label"] == 0]) / len(full_df) * 100, 1)) + "%)")
    print("")

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

    print(">>> Model o'qitilmoqda...")
    print("  Train: " + str(len(X_train)) + " ta")
    print("  Test: " + str(len(X_test)) + " ta")
    print("  Features: " + str(len(features)) + " ta")
    print("")

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
    y_prob = model.predict_proba(X_test)[:, 1]
    accuracy = accuracy_score(y_test, y_pred)

    print("=" * 60)
    print("  AI MODEL v2 NATIJALARI")
    print("=" * 60)
    print("")
    print("  Aniqlik (Accuracy): " + str(round(accuracy * 100, 1)) + "%")
    print("")
    print("  Tafsilot:")
    print(classification_report(y_test, y_pred, target_names=["Zarali (0)", "Foydali (1)"]))

    print("")
    print("  THRESHOLD BO'YICHA NATIJALAR:")
    print("  " + "-" * 50)
    for threshold in [0.5, 0.6, 0.7, 0.8]:
        pred_at_threshold = (y_prob >= threshold).astype(int)
        total_signals = pred_at_threshold.sum()
        if total_signals > 0:
            correct = ((pred_at_threshold == 1) & (y_test == 1)).sum()
            precision = correct / total_signals * 100
            print("  Threshold " + str(int(threshold * 100)) + "%: " + str(total_signals) + " signal | Aniqlik: " + str(round(precision, 1)) + "%")
    print("  " + "-" * 50)

    print("")
    print("  ENG MUHIM INDIKATORLAR (TOP 15):")
    print("  " + "-" * 50)
    importance = model.feature_importances_
    feature_importance = sorted(zip(features, importance), key=lambda x: x[1], reverse=True)
    for i, (feat, imp) in enumerate(feature_importance[:15]):
        bar = "#" * int(imp * 50)
        print("  " + str(i + 1) + ". " + feat + ": " + str(round(imp * 100, 1)) + "% " + bar)
    print("  " + "-" * 50)

    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    joblib.dump(model, MODEL_FILE)
    joblib.dump(features, FEATURES_FILE)

    print("")
    print("  Model saqlandi: " + MODEL_FILE)
    print("  Features saqlandi: " + FEATURES_FILE)
    print("")

    print("  " + "-" * 50)
    print("  VERSIYALAR SOLISHTIRISH:")
    print("  v1: 5 juftlik | 30 kun | 15 feature | Accuracy: 95.4%")
    print("  v2: " + str(len(SYMBOLS)) + " juftlik | " + str(DAYS_TO_FETCH) + " kun | " + str(len(features)) + " feature | Accuracy: " + str(round(accuracy * 100, 1)) + "%")
    print("  " + "-" * 50)
    print("")
    print("=" * 60)
    print("  TAYYOR! Botda yangi AI model ishlatiladi.")
    print("=" * 60)

    return model, features

if __name__ == "__main__":
    train_model()
