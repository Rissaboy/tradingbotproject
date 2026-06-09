import numpy as np
import pandas as pd
import ccxt
import ta
import time
import os
import sys
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

try:
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
    from tensorflow.keras.optimizers import Adam
    from sklearn.preprocessing import MinMaxScaler
    import joblib
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("  TensorFlow o'rnatilmagan! pip install tensorflow")

LSTM_MODEL_FILE = os.path.join(ROOT_DIR, "ai", "models", "sardor_lstm_model.keras")
LSTM_SCALER_FILE = os.path.join(ROOT_DIR, "ai", "models", "sardor_lstm_scaler.pkl")
SEQUENCE_LENGTH = 60
SYMBOLS_TO_TRAIN = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT"]
DAYS_TO_FETCH = 60
TIMEFRAME = "1h"

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
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["open"] = df["open"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df


def prepare_features(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    macd = ta.trend.MACD(df["close"])
    df["macd_diff"] = macd.macd_diff()
    df["atr"] = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
    df["atr_pct"] = df["atr"] / df["close"] * 100
    df["volume_ratio"] = df["volume"] / df["volume"].rolling(20).mean()
    df["change_1"] = df["close"].pct_change(1) * 100
    df["change_5"] = df["close"].pct_change(5) * 100
    df["ema_diff"] = (ta.trend.EMAIndicator(df["close"], window=20).ema_indicator() - ta.trend.EMAIndicator(df["close"], window=50).ema_indicator()) / df["close"] * 100
    df = df.dropna().reset_index(drop=True)
    return df


def create_sequences(data, seq_length):
    X = []
    y = []
    for i in range(seq_length, len(data) - 1):
        X.append(data[i - seq_length:i])
        if data[i + 1][0] > data[i][0]:
            y.append(1)
        else:
            y.append(0)
    return np.array(X), np.array(y)


def train_lstm():
    if not TENSORFLOW_AVAILABLE:
        print("  TensorFlow o'rnatilmagan! pip install tensorflow")
        return None

    print("")
    print("=" * 60)
    print("  SARDOR LSTM DEEP LEARNING TRAINER")
    print("  Narx yo'nalishini bashorat qilish")
    print("=" * 60)
    print("")

    all_features = []
    for symbol in SYMBOLS_TO_TRAIN:
        print("  " + symbol + " yuklanmoqda...")
        df = fetch_data(symbol)
        df = prepare_features(df)
        feature_cols = ["close", "rsi", "macd_diff", "atr_pct", "volume_ratio", "change_1", "change_5", "ema_diff"]
        features = df[feature_cols].values
        all_features.append(features)
        print("    " + str(len(features)) + " ta sham")

    combined = np.concatenate(all_features, axis=0)
    print("")
    print("  Jami data: " + str(len(combined)) + " ta")

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(combined)

    X, y = create_sequences(scaled_data, SEQUENCE_LENGTH)
    print("  Sequences: " + str(len(X)) + " ta")
    print("  UP: " + str(sum(y)) + " | DOWN: " + str(len(y) - sum(y)))

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    print("")
    print("  Train: " + str(len(X_train)) + " | Test: " + str(len(X_test)))
    print("")
    print("  LSTM model qurilmoqda...")

    model = Sequential()
    model.add(Input(shape=(SEQUENCE_LENGTH, X.shape[2])))
    model.add(LSTM(128, return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(64, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(32, activation="relu"))
    model.add(Dense(1, activation="sigmoid"))

    model.compile(optimizer=Adam(learning_rate=0.001), loss="binary_crossentropy", metrics=["accuracy"])

    print("  O'qitish boshlandi (2-5 daqiqa)...")
    print("")

    history = model.fit(X_train, y_train, epochs=20, batch_size=32, validation_data=(X_test, y_test), verbose=1)

    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)

    print("")
    print("=" * 60)
    print("  LSTM NATIJALARI")
    print("=" * 60)
    print("")
    print("  Test Accuracy: " + str(round(accuracy * 100, 1)) + "%")
    print("  Test Loss: " + str(round(loss, 4)))

    model_dir = os.path.dirname(LSTM_MODEL_FILE)
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    model.save(LSTM_MODEL_FILE)
    joblib.dump(scaler, LSTM_SCALER_FILE)

    print("")
    print("  Model saqlandi: " + LSTM_MODEL_FILE)
    print("  Scaler saqlandi: " + LSTM_SCALER_FILE)
    print("")
    print("=" * 60)
    print("  TAYYOR! Bot endi LSTM bashoratdan foydalanadi.")
    print("=" * 60)

    return accuracy


lstm_model = None
lstm_scaler = None


def load_lstm_model():
    global lstm_model, lstm_scaler
    if not TENSORFLOW_AVAILABLE:
        return False
    try:
        if os.path.exists(LSTM_MODEL_FILE) and os.path.exists(LSTM_SCALER_FILE):
            lstm_model = load_model(LSTM_MODEL_FILE)
            lstm_scaler = joblib.load(LSTM_SCALER_FILE)
            print("  LSTM model yuklandi")
            return True
        return False
    except Exception as e:
        print("  LSTM yuklash xato: " + str(e))
        return False


def lstm_predict(df):
    global lstm_model, lstm_scaler
    if lstm_model is None or lstm_scaler is None:
        return 0.5, "LSTM o'chiq"

    try:
        df_copy = df.copy()
        df_copy = prepare_features(df_copy)
        feature_cols = ["close", "rsi", "macd_diff", "atr_pct", "volume_ratio", "change_1", "change_5", "ema_diff"]
        features = df_copy[feature_cols].tail(SEQUENCE_LENGTH).values

        if len(features) < SEQUENCE_LENGTH:
            return 0.5, "LSTM: data yetarli emas"

        scaled = lstm_scaler.transform(features)
        X = np.array([scaled])
        prediction = lstm_model.predict(X, verbose=0)[0][0]

        direction = "UP" if prediction > 0.5 else "DOWN"
        confidence = prediction if prediction > 0.5 else (1 - prediction)

        return float(prediction), "LSTM: " + direction + " (" + str(round(confidence * 100, 1)) + "%)"

    except Exception as e:
        return 0.5, "LSTM xato: " + str(e)


if __name__ == "__main__":
    train_lstm()
