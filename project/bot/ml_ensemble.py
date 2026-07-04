"""
ML ENSEMBLE MODULE
Bir necha AI modellarni birlashtirib, aniqroq bashorat qilish
Sardor uchun maxsus!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import pickle
from datetime import datetime


class MLEnsemble:
    """
    Ensemble Learning - Bir necha AI model birgalikda qaror qabul qiladi
    
    Modellar:
    1. RandomForest (asosiy model)
    2. XGBoost (kuchli gradient boosting)
    3. LightGBM (tez va aniq)
    4. Extra Trees (RandomForest yaxshilangan versiyasi)
    
    Voting: Majority voting (ko'pchilik ovozi)
    """
    
    def __init__(self, models_dir="ai/models/ensemble"):
        self.models_dir = models_dir
        self.models = {}
        self.model_weights = {
            "randomforest": 1.0,   # Asosiy model
            "xgboost": 1.2,        # Eng aniq
            "lightgbm": 1.1,       # Tez va aniq
            "extratrees": 0.9      # Qo'shimcha
        }
        self.features_list = None
        self.load_models()
    
    def load_models(self):
        """Barcha modellarni yuklash"""
        
        # Model fayllarini tekshirish
        model_files = {
            "randomforest": "ensemble_rf.pkl",
            "xgboost": "ensemble_xgb.pkl",
            "lightgbm": "ensemble_lgb.pkl",
            "extratrees": "ensemble_et.pkl"
        }
        
        for model_name, filename in model_files.items():
            filepath = os.path.join(self.models_dir, filename)
            
            try:
                if os.path.exists(filepath):
                    with open(filepath, "rb") as f:
                        self.models[model_name] = pickle.load(f)
                    print(f"✅ {model_name} yuklandi")
                else:
                    print(f"⚠️ {model_name} topilmadi: {filepath}")
            
            except Exception as e:
                print(f"⚠️ {model_name} yuklashda xato: {str(e)}")
        
        # Features listini yuklash
        features_file = os.path.join(self.models_dir, "ensemble_features.pkl")
        if os.path.exists(features_file):
            with open(features_file, "rb") as f:
                self.features_list = pickle.load(f)
            print(f"✅ Features yuklandi: {len(self.features_list)} ta")
        
        if not self.models:
            print("⚠️ HECH QANDAY MODEL YUKLANMADI!")
            print(f"Modellarni {self.models_dir} papkasiga joylashtiring")
    
    def prepare_features(self, df):
        """Har bir modelga features tayyorlash"""
        
        if self.features_list is None:
            print("⚠️ Features list topilmadi")
            return None
        
        # Oxirgi qator (eng yangi ma'lumot)
        latest = df.iloc[-1]
        
        # Features yaratish (volume_analysis.py dan)
        features = {}
        
        # Narx o'zgarishi
        if len(df) >= 2:
            features["price_change"] = ((latest["close"] - df.iloc[-2]["close"]) / df.iloc[-2]["close"]) * 100
        else:
            features["price_change"] = 0
        
        # Volume
        if len(df) >= 20:
            avg_volume = df["volume"].tail(20).mean()
            features["volume_ratio"] = latest["volume"] / avg_volume if avg_volume > 0 else 1
        else:
            features["volume_ratio"] = 1
        
        # RSI
        features["rsi"] = latest.get("rsi", 50)
        
        # MACD
        features["macd"] = latest.get("macd", 0)
        features["macd_signal"] = latest.get("macd_signal", 0)
        features["macd_hist"] = latest.get("macd_hist", 0)
        
        # Bollinger Bands
        features["bb_upper"] = latest.get("bb_upper", latest["close"])
        features["bb_middle"] = latest.get("bb_middle", latest["close"])
        features["bb_lower"] = latest.get("bb_lower", latest["close"])
        features["bb_position"] = (latest["close"] - features["bb_lower"]) / (features["bb_upper"] - features["bb_lower"]) if (features["bb_upper"] - features["bb_lower"]) > 0 else 0.5
        
        # ATR (Volatility)
        features["atr"] = latest.get("atr", 0)
        
        # EMA
        features["ema_50"] = latest.get("ema_50", latest["close"])
        features["ema_200"] = latest.get("ema_200", latest["close"])
        
        # ADX (Trend strength)
        features["adx"] = latest.get("adx", 25)
        
        # Stochastic
        features["stoch_k"] = latest.get("stoch_k", 50)
        features["stoch_d"] = latest.get("stoch_d", 50)
        
        # Features listidagi tartibda joylashtirish
        X = []
        for feat_name in self.features_list:
            X.append(features.get(feat_name, 0))
        
        return np.array(X).reshape(1, -1)
    
    def predict_single_model(self, model_name, X):
        """Bitta model bilan bashorat"""
        
        if model_name not in self.models:
            return None, None
        
        model = self.models[model_name]
        
        try:
            # Predict
            prediction = model.predict(X)[0]  # 0 = SELL, 1 = HOLD, 2 = BUY
            
            # Probability
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(X)[0]
                confidence = probabilities[prediction]
            else:
                confidence = 0.5
            
            return prediction, confidence
        
        except Exception as e:
            print(f"⚠️ {model_name} bashoratda xato: {str(e)}")
            return None, None
    
    def predict_ensemble(self, df):
        """Ensemble bashorat - barcha modellar birgalikda"""
        
        if not self.models:
            return {
                "signal": None,
                "confidence": 0,
                "reason": "Modellar yuklanmagan"
            }
        
        # Features tayyorlash
        X = self.prepare_features(df)
        
        if X is None:
            return {
                "signal": None,
                "confidence": 0,
                "reason": "Features tayyorlanmadi"
            }
        
        # Har bir model bilan bashorat
        predictions = {}
        confidences = {}
        
        for model_name in self.models.keys():
            pred, conf = self.predict_single_model(model_name, X)
            
            if pred is not None:
                predictions[model_name] = pred
                confidences[model_name] = conf
        
        if not predictions:
            return {
                "signal": None,
                "confidence": 0,
                "reason": "Hech qanday model bashorat qilmadi"
            }
        
        # Weighted voting
        votes = {0: 0, 1: 0, 2: 0}  # SELL, HOLD, BUY
        
        for model_name, pred in predictions.items():
            weight = self.model_weights.get(model_name, 1.0)
            confidence = confidences[model_name]
            votes[pred] += weight * confidence
        
        # Final prediction (eng ko'p ovoz olgan)
        final_prediction = max(votes, key=votes.get)
        
        # Confidence (normalizatsiya)
        total_votes = sum(votes.values())
        final_confidence = votes[final_prediction] / total_votes if total_votes > 0 else 0
        
        # Signal
        signal_map = {0: "SHORT", 1: None, 2: "LONG"}
        signal = signal_map[final_prediction]
        
        # Voting details
        voting_details = {
            "SHORT": votes[0] / total_votes * 100 if total_votes > 0 else 0,
            "HOLD": votes[1] / total_votes * 100 if total_votes > 0 else 0,
            "LONG": votes[2] / total_votes * 100 if total_votes > 0 else 0
        }
        
        return {
            "signal": signal,
            "confidence": final_confidence,
            "reason": f"{len(predictions)} ta model: {signal or 'HOLD'}",
            "model_predictions": predictions,
            "model_confidences": confidences,
            "voting_details": voting_details,
            "total_models": len(predictions)
        }
    
    def get_ensemble_report(self, symbol, result):
        """Telegram uchun ensemble hisoboti"""
        
        report = f"<b>🤖 ML ENSEMBLE: {symbol.replace('/USDT', '')}</b>\n\n"
        
        if result["signal"]:
            emoji = "🟢" if result["signal"] == "LONG" else "🔴"
            report += f"{emoji} <b>Signal: {result['signal']}</b>\n"
            report += f"Ishonch: {result['confidence']*100:.1f}%\n\n"
        else:
            report += "⚪ Signal: HOLD (Kutib turing)\n\n"
        
        # Voting details
        report += "<b>📊 Ovozlar:</b>\n"
        for action, pct in result["voting_details"].items():
            if action == "LONG":
                report += f"🟢 LONG: {pct:.1f}%\n"
            elif action == "SHORT":
                report += f"🔴 SHORT: {pct:.1f}%\n"
            else:
                report += f"⚪ HOLD: {pct:.1f}%\n"
        
        # Model details
        report += f"\n<b>🤖 Modellar: {result['total_models']} ta</b>\n"
        for model_name, pred in result["model_predictions"].items():
            signal_map = {0: "SHORT", 1: "HOLD", 2: "LONG"}
            conf = result["model_confidences"][model_name]
            report += f"  • {model_name}: {signal_map[pred]} ({conf*100:.0f}%)\n"
        
        return report
    
    def check_ensemble_confirmation(self, signal_type, df):
        """Asosiy signal uchun ensemble tasdiqlash"""
        
        ensemble = self.predict_ensemble(df)
        
        # Agar asosiy signal LONG va ensemble ham LONG = KUCHLI ✅
        if signal_type == "LONG" and ensemble["signal"] == "LONG":
            return True, ensemble["confidence"] * 3, ensemble["reason"]
        
        # Agar asosiy signal SHORT va ensemble ham SHORT = KUCHLI ✅
        elif signal_type == "SHORT" and ensemble["signal"] == "SHORT":
            return True, ensemble["confidence"] * 3, ensemble["reason"]
        
        # Agar ensemble teskari = ZAIF ❌
        elif signal_type == "LONG" and ensemble["signal"] == "SHORT":
            return False, 0, f"Ensemble teskari: {ensemble['reason']}"
        
        elif signal_type == "SHORT" and ensemble["signal"] == "LONG":
            return False, 0, f"Ensemble teskari: {ensemble['reason']}"
        
        # Ensemble HOLD = O'rtacha ⚠️
        else:
            return True, 0.5, "Ensemble HOLD (neutral)"


# ============================================
# ENSEMBLE MODELLARNI O'QITISH
# ============================================
def train_ensemble_models():
    """
    Ensemble uchun modellarni o'qitish
    
    Bu funktsiya alohida ishga tushiriladi:
    python3 project/bot/ml_ensemble.py
    """
    
    print("=" * 60)
    print("ENSEMBLE MODELS TRAINING")
    print("=" * 60)
    
    # Bu qismni keyinroq to'ldiramiz
    # Hozircha faqat struktura
    
    print("\n⚠️ TRAINING FUNKTSIYASI HALI TAYYORLANMAGAN")
    print("Sardor, kerakmi bu qismni ham qo'shaylikmi?")
    print("\nYoki faqat asosiy AI model (RandomForest) dan foydalanamizmi?")


# ============================================
# TEST
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("ML ENSEMBLE TEST")
    print("=" * 60)
    
    # Ensemble yaratish
    ensemble = MLEnsemble(models_dir="ai/models/ensemble")
    
    print(f"\nYuklangan modellar: {len(ensemble.models)} ta")
    
    if ensemble.models:
        print("\n✅ Ensemble tayyor!")
    else:
        print("\n⚠️ Modellar yuklanmadi")
        print("Avval modellarni o'qitish kerak")
