"""
ML ENSEMBLE MODELLARNI O'RGATISH
Bir necha AI model (RandomForest, XGBoost, LightGBM, ExtraTrees) birgalikda
Sardor uchun maxsus!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

print("=" * 60)
print("ML ENSEMBLE TRAINING")
print("=" * 60)


def train_ensemble_models():
    """Ensemble uchun barcha modellarni o'rgatish"""
    
    # 1. DATA YUKLASH
    print("\n📊 STEP 1: Data yuklash...")
    
    try:
        # Asosiy AI trainer dan data olish
        from bot.exchange import get_klines
        
        symbols = [
            "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT",
            "ADA/USDT", "AVAX/USDT", "DOT/USDT", "LINK/USDT", "UNI/USDT",
            "AAVE/USDT", "NEAR/USDT", "BCH/USDT", "LTC/USDT", "TON/USDT"
        ]
        
        all_data = []
        
        for symbol in symbols:
            print(f"  {symbol} yuklanmoqda...")
            try:
                # Data olish (get_klines faqat symbol qabul qiladi, timeframe yo'q)
                df = get_klines(symbol)
                
                if len(df) < 100:
                    continue
                
                # Indicators qo'shish
                from bot.indicators import calculate_indicators
                df = calculate_indicators(df)
                df = df.dropna()
                
                if len(df) < 50:
                    continue
                
                # Features va labels yaratish
                for i in range(20, len(df) - 5):
                    row = df.iloc[i]
                    future_price = df.iloc[i + 5]["close"]
                    current_price = row["close"]
                    
                    # Label: 5 period keyin narx qanday?
                    price_change_pct = ((future_price - current_price) / current_price) * 100
                    
                    if price_change_pct > 1.0:
                        label = 2  # BUY
                    elif price_change_pct < -1.0:
                        label = 0  # SELL
                    else:
                        label = 1  # HOLD
                    
                    # Features
                    features = {
                        "rsi": row.get("rsi", 50),
                        "macd": row.get("macd", 0),
                        "macd_signal": row.get("macd_signal", 0),
                        "macd_hist": row.get("macd_hist", 0),
                        "bb_position": (row["close"] - row.get("bb_lower", row["close"])) / (row.get("bb_upper", row["close"]) - row.get("bb_lower", row["close"])) if (row.get("bb_upper", row["close"]) - row.get("bb_lower", row["close"])) > 0 else 0.5,
                        "atr": row.get("atr", 0),
                        "adx": row.get("adx", 25),
                        "stoch_k": row.get("stoch_k", 50),
                        "stoch_d": row.get("stoch_d", 50),
                        "volume_ratio": row["volume"] / df["volume"].iloc[i-20:i].mean() if df["volume"].iloc[i-20:i].mean() > 0 else 1,
                        "price_change": ((row["close"] - df.iloc[i-1]["close"]) / df.iloc[i-1]["close"]) * 100,
                        "ema_50": row.get("ema_50", row["close"]),
                        "ema_200": row.get("ema_200", row["close"]),
                        "label": label
                    }
                    
                    all_data.append(features)
            
            except Exception as e:
                print(f"  ⚠️ {symbol}: {str(e)}")
                continue
        
        print(f"\n✅ Jami: {len(all_data)} ta record yuklandi")
        
        if len(all_data) < 1000:
            print("❌ Data kam! Kamida 1000 ta record kerak.")
            return None
        
        # DataFrame yaratish
        df = pd.DataFrame(all_data)
        
        # Features va labels
        X = df.drop("label", axis=1)
        y = df["label"]
        
        # Features list saqlash
        features_list = X.columns.tolist()
        
        print(f"Features: {len(features_list)} ta")
        print(f"Labels: {len(y)} ta")
        print(f"  SELL: {sum(y == 0)} ta")
        print(f"  HOLD: {sum(y == 1)} ta")
        print(f"  BUY: {sum(y == 2)} ta")
        
        # Train/Test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
        
    except Exception as e:
        print(f"❌ Data yuklashda xato: {str(e)}")
        return None
    
    # 2. MODELLARNI O'RGATISH
    print("\n🤖 STEP 2: Modellarni o'rgatish...")
    
    models = {}
    
    # Model 1: RandomForest
    print("\n  1. RandomForest...")
    try:
        rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        y_pred = rf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"     Accuracy: {accuracy*100:.1f}%")
        models["randomforest"] = rf
    except Exception as e:
        print(f"     ❌ Xato: {str(e)}")
    
    # Model 2: ExtraTrees
    print("\n  2. ExtraTrees...")
    try:
        et = ExtraTreesClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        et.fit(X_train, y_train)
        y_pred = et.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"     Accuracy: {accuracy*100:.1f}%")
        models["extratrees"] = et
    except Exception as e:
        print(f"     ❌ Xato: {str(e)}")
    
    # Model 3: XGBoost (agar o'rnatilgan bo'lsa)
    print("\n  3. XGBoost...")
    try:
        import xgboost as xgb
        xgb_model = xgb.XGBClassifier(n_estimators=100, max_depth=6, random_state=42, n_jobs=-1)
        xgb_model.fit(X_train, y_train)
        y_pred = xgb_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"     Accuracy: {accuracy*100:.1f}%")
        models["xgboost"] = xgb_model
    except ImportError:
        print("     ⚠️ XGBoost o'rnatilmagan. O'tkazib yuborildi.")
        print("     O'rnatish: pip install xgboost")
    except Exception as e:
        print(f"     ❌ Xato: {str(e)}")
    
    # Model 4: LightGBM (agar o'rnatilgan bo'lsa)
    print("\n  4. LightGBM...")
    try:
        import lightgbm as lgb
        lgb_model = lgb.LGBMClassifier(n_estimators=100, max_depth=6, random_state=42, n_jobs=-1)
        lgb_model.fit(X_train, y_train)
        y_pred = lgb_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"     Accuracy: {accuracy*100:.1f}%")
        models["lightgbm"] = lgb_model
    except ImportError:
        print("     ⚠️ LightGBM o'rnatilmagan. O'tkazib yuborildi.")
        print("     O'rnatish: pip install lightgbm")
    except Exception as e:
        print(f"     ❌ Xato: {str(e)}")
    
    if not models:
        print("\n❌ Hech qanday model o'rgatilmadi!")
        return None
    
    # 3. MODELLARNI SAQLASH
    print("\n💾 STEP 3: Modellarni saqlash...")
    
    ensemble_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "ensemble")
    os.makedirs(ensemble_dir, exist_ok=True)
    
    for model_name, model in models.items():
        filename = f"ensemble_{model_name[:3]}.pkl"
        filepath = os.path.join(ensemble_dir, filename)
        
        with open(filepath, "wb") as f:
            pickle.dump(model, f)
        
        print(f"  ✅ {model_name}: {filepath}")
    
    # Features list saqlash
    features_file = os.path.join(ensemble_dir, "ensemble_features.pkl")
    with open(features_file, "wb") as f:
        pickle.dump(features_list, f)
    print(f"  ✅ Features list: {features_file}")
    
    # 4. NATIJA
    print("\n" + "=" * 60)
    print("✅ ML ENSEMBLE TRAINING TUGADI!")
    print("=" * 60)
    print(f"\nO'rgatilgan modellar: {len(models)} ta")
    for model_name in models.keys():
        print(f"  • {model_name}")
    
    print(f"\nFayllar: {ensemble_dir}")
    print("\nIshlatish:")
    print("  1. settings.py da ML_ENSEMBLE_ENABLED = True qiling")
    print("  2. Bot qayta ishga tushiring: systemctl restart sardorbot")
    print("  3. Telegram: /features (tekshirish)")
    
    return models


if __name__ == "__main__":
    train_ensemble_models()
