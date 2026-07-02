import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Sahifa sozlamalari
st.set_page_config(page_title="Sardor Trading Bot", page_icon="📊", layout="wide")

# Loyiha papkasi
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

st.title("📊 Sardor Trading Bot Dashboard")
st.markdown("---")

# ===== 1. BOT HOLATI =====
col1, col2, col3, col4 = st.columns(4)

# Settings yuklash
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("settings", os.path.join(ROOT_DIR, "config", "settings.py"))
    settings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings)
    exchange_name = settings.EXCHANGE_NAME.upper()
    timeframe = settings.TIMEFRAME
    sl = settings.STOP_LOSS_PCT
    tp = settings.TAKE_PROFIT_PCT
except:
    exchange_name = "BINANCE"
    timeframe = "5m"
    sl = 3.0
    tp = 3.0

with col1:
    st.metric("Birja", exchange_name)
with col2:
    st.metric("Timeframe", timeframe)
with col3:
    st.metric("Stop-Loss", str(sl) + "%")
with col4:
    st.metric("Take-Profit", str(tp) + "%")

st.markdown("---")

# ===== 2. SCANNER NATIJALARI =====
st.subheader("🔍 Market Scanner - TOP Coinlar")

scanner_path = os.path.join(ROOT_DIR, "scanner", "top_coins.json")
if os.path.exists(scanner_path):
    with open(scanner_path, "r") as f:
        scanner_data = json.load(f)

    scan_time = scanner_data.get("scan_time", "Noma'lum")
    total_analyzed = scanner_data.get("total_analyzed", 0)
    top_coins = scanner_data.get("top_coins", [])

    st.write("Oxirgi skanerlash: **" + scan_time + "** | Tahlil qilingan: **" + str(total_analyzed) + "** ta coin")

    if top_coins:
        df_scanner = pd.DataFrame(top_coins)
        df_scanner = df_scanner[["symbol", "score", "trend", "adx", "rsi", "volatility", "change_24h"]]
        df_scanner.columns = ["Juftlik", "Ball", "Trend", "ADX", "RSI", "Volatillik %", "24h %"]

        # Rang berish
        st.dataframe(df_scanner, use_container_width=True, height=400)
else:
    st.warning("Scanner natijasi topilmadi. Avval `python scanner/market_scanner.py` ishga tushiring.")

st.markdown("---")

# ===== 3. SAVDOLAR TARIXI =====
st.subheader("📋 Savdolar Tarixi")

excel_path = os.path.join(ROOT_DIR, "data", "trades_history.xlsx")
if os.path.exists(excel_path):
    df_trades = pd.read_excel(excel_path)

    # Statistika
    if len(df_trades) > 0:
        col1, col2, col3, col4, col5 = st.columns(5)

        sell_trades = df_trades[df_trades["Tur"].str.contains("SELL|SL|TP|Signal|Trail|MR|Oxiri", na=False)]
        if len(sell_trades) > 0:
            total_trades = len(sell_trades)
            winning = len(sell_trades[sell_trades["Foyda_usd"] > 0])
            losing = len(sell_trades[sell_trades["Foyda_usd"] < 0])
            win_rate = (winning / total_trades * 100) if total_trades > 0 else 0
            total_profit = sell_trades["Foyda_usd"].sum()

            with col1:
                st.metric("Jami savdolar", str(total_trades))
            with col2:
                st.metric("Foydali", str(winning))
            with col3:
                st.metric("Zarali", str(losing))
            with col4:
                st.metric("Win rate", str(round(win_rate, 1)) + "%")
            with col5:
                st.metric("Umumiy foyda", "$" + str(round(total_profit, 2)))

        # Jadval
        st.dataframe(df_trades.tail(50).iloc[::-1], use_container_width=True, height=400)

        # Foyda grafik
        if "Foyda_usd" in df_trades.columns:
            st.subheader("📈 Foyda/Zarar grafigi")
            profit_data = sell_trades[["Sana", "Foyda_usd"]].copy()
            profit_data["Jami"] = profit_data["Foyda_usd"].cumsum()
            st.line_chart(profit_data.set_index("Sana")["Jami"])

else:
    st.info("Savdolar tarixi hali yo'q. Bot savdo qilgandan keyin bu yerda ko'rinadi.")

st.markdown("---")

# ===== 4. AI MODEL =====
st.subheader("🧠 AI Model")

ai_model_path = os.path.join(ROOT_DIR, "ai", "models", "sardor_ai_model.pkl")
if os.path.exists(ai_model_path):
    st.success("AI model yuklangan: sardor_ai_model.pkl")
    try:
        ai_min = 60
        st.write("Minimum ishonch: **" + str(ai_min) + "%**")
        st.write("AI yomon signallarni bloklaydi va faqat yaxshi signallarga ruxsat beradi.")
    except:
        pass
else:
    st.warning("AI model topilmadi. `python sardor_ai_trainer.py` ishga tushiring.")

st.markdown("---")

# ===== 5. SOZLAMALAR =====
st.subheader("⚙️ Sozlamalar")

col1, col2 = st.columns(2)

with col1:
    st.write("**Trading sozlamalari:**")
    st.write("- Birja: " + exchange_name)
    st.write("- Timeframe: " + timeframe)
    st.write("- Stop-Loss: " + str(sl) + "%")
    st.write("- Take-Profit: " + str(tp) + "%")
    st.write("- Risk/savdo: 1.5%")
    st.write("- Max pozitsiya: 5")

with col2:
    st.write("**AI sozlamalari:**")
    st.write("- AI: YOQILGAN")
    st.write("- Min ishonch: 60%")
    st.write("- Model: XGBoost")
    st.write("")
    st.write("**Telegram:**")
    st.write("- /start /stop /status")
    st.write("- /balance /positions")

st.markdown("---")
st.caption("Sardor Trading Bot v10 (Professional) | " + datetime.now().strftime("%Y-%m-%d %H:%M"))