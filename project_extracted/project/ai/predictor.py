import os
import pandas as pd
import joblib
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import AI_MODEL_FILE, AI_FEATURES_FILE, AI_ENABLED

ai_model = None
ai_features = None

def load_ai_model():
    global ai_model, ai_features
    if not AI_ENABLED:
        print("  AI: O'CHIRILGAN")
        return False
    try:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(root_dir, AI_MODEL_FILE)
        features_path = os.path.join(root_dir, AI_FEATURES_FILE)
        if os.path.exists(model_path) and os.path.exists(features_path):
            ai_model = joblib.load(model_path)
            ai_features = joblib.load(features_path)
            print("  AI model yuklandi: " + AI_MODEL_FILE)
            return True
        else:
            print("  AI model topilmadi! AI o'chirildi.")
            return False
    except Exception as e:
        print("  AI yuklash xato: " + str(e))
        return False

def ai_predict(df):
    if ai_model is None or ai_features is None:
        return 1.0, "AI o'chiq"
    try:
        row = df.iloc[-1]
        feature_values = []
        for feat in ai_features:
            feature_values.append(row[feat])
        X = pd.DataFrame([feature_values], columns=ai_features)
        probability = ai_model.predict_proba(X)[0][1]
        return probability, "AI: " + str(round(probability * 100, 1)) + "%"
    except Exception as e:
        return 1.0, "AI xato: " + str(e)
