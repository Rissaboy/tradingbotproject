"""
CORRELATION CHECKER - Qaysi coinlar teskari harakatlanadi?
Sardor uchun maxsus!
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("=" * 60)
print("  CORRELATION CHECKER")
print("  30 kunlik ma'lumotlar tahlili")
print("=" * 60)
print()

# Binance ulanish
exchange = ccxt.binance()

# Tekshiriladigan coinlar
SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
    "ADA/USDT", "AVAX/USDT", "DOT/USDT", "LINK/USDT", "DOGE/USDT",
    "MATIC/USDT", "UNI/USDT", "LTC/USDT", "ATOM/USDT", "ETC/USDT",
    "XLM/USDT", "ALGO/USDT", "VET/USDT", "FIL/USDT", "AAVE/USDT"
]

# Ma'lumotlarni yuklash
print(">>> Ma'lumotlar yuklanmoqda (30 kun)...")
data = {}
for symbol in SYMBOLS:
    try:
        # 30 kunlik 1h sham
        ohlcv = exchange.fetch_ohlcv(symbol, "1h", limit=720)  # 30 kun * 24 soat
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        
        # Faqat close narxlar kerak
        data[symbol] = df[["timestamp", "close"]].set_index("timestamp")["close"]
        print(f"  ✅ {symbol}: {len(df)} ta sham")
    except Exception as e:
        print(f"  ❌ {symbol}: {e}")

print()
print(">>> Korrelyatsiya hisoblanmoqda...")
print()

# Barcha coinlarni birlashtirish
df_all = pd.DataFrame(data)

# Korrelyatsiya matritsasi
correlation_matrix = df_all.corr()

# Teskari korrelyatsiyalarni topish
inverse_pairs = []
for i in range(len(correlation_matrix.columns)):
    for j in range(i + 1, len(correlation_matrix.columns)):
        coin1 = correlation_matrix.columns[i]
        coin2 = correlation_matrix.columns[j]
        corr = correlation_matrix.iloc[i, j]
        
        # Faqat teskari korrelyatsiya (-0.3 dan past)
        if corr < -0.3:
            inverse_pairs.append({
                "coin1": coin1,
                "coin2": coin2,
                "correlation": corr
            })

# Eng kuchli teskari korrelyatsiyalar
inverse_pairs.sort(key=lambda x: x["correlation"])

print("=" * 80)
print("  ENG KUCHLI TESKARI KORRELYATSIYALAR (30 kun)")
print("=" * 80)
print()

if len(inverse_pairs) == 0:
    print("❌ Teskari korrelyatsiya topilmadi!")
    print("   Barcha coinlar bir xil yo'nalishda harakatlanmoqda.")
else:
    print(f"{'Coin 1':<15} {'Coin 2':<15} {'Korrelyatsiya':<15} {'Izoh'}")
    print("-" * 80)
    
    for pair in inverse_pairs[:20]:  # Eng kuchli 20 ta
        coin1 = pair["coin1"].replace("/USDT", "")
        coin2 = pair["coin2"].replace("/USDT", "")
        corr = pair["correlation"]
        
        if corr < -0.7:
            strength = "🔥 JUDA KUCHLI"
        elif corr < -0.5:
            strength = "✅ KUCHLI"
        else:
            strength = "⚠️ O'RTACHA"
        
        print(f"{coin1:<15} {coin2:<15} {corr:<15.2f} {strength}")

print()
print("=" * 80)
print("  IJOBIY KORRELYATSIYALAR (Bir xil yo'nalish)")
print("=" * 80)
print()

# Eng kuchli ijobiy korrelyatsiyalar
positive_pairs = []
for i in range(len(correlation_matrix.columns)):
    for j in range(i + 1, len(correlation_matrix.columns)):
        coin1 = correlation_matrix.columns[i]
        coin2 = correlation_matrix.columns[j]
        corr = correlation_matrix.iloc[i, j]
        
        # Faqat kuchli ijobiy (0.8 dan yuqori)
        if corr > 0.8 and coin1 != coin2:
            positive_pairs.append({
                "coin1": coin1,
                "coin2": coin2,
                "correlation": corr
            })

positive_pairs.sort(key=lambda x: x["correlation"], reverse=True)

print(f"{'Coin 1':<15} {'Coin 2':<15} {'Korrelyatsiya':<15} {'Izoh'}")
print("-" * 80)

for pair in positive_pairs[:10]:  # Eng kuchli 10 ta
    coin1 = pair["coin1"].replace("/USDT", "")
    coin2 = pair["coin2"].replace("/USDT", "")
    corr = pair["correlation"]
    
    if corr > 0.95:
        strength = "🔥 JUDA KUCHLI (bir xil)"
    elif corr > 0.90:
        strength = "✅ KUCHLI (bir xil)"
    else:
        strength = "⚠️ O'RTACHA (bir xil)"
    
    print(f"{coin1:<15} {coin2:<15} {corr:<15.2f} {strength}")

print()
print("=" * 80)
print("  XULOSA")
print("=" * 80)
print()
print("Teskari korrelyatsiya (-0.70 dan past):")
print(f"  Topildi: {len([p for p in inverse_pairs if p['correlation'] < -0.70])} ta juftlik")
print()
print("Agar teskari korrelyatsiya bo'lsa:")
print("  ✅ Pair Trading strategiyasi ishlaydi")
print("  ✅ Bir coin ko'tarilsa, ikkinchisiga SHORT ochish mumkin")
print()
print("Agar teskari korrelyatsiya yo'q bo'lsa:")
print("  ❌ Pair Trading ishlamaydi")
print("  ℹ️  Kripto bozorida ko'pincha barcha coinlar bir xil yo'nalishda harakatlanadi")
print("  ℹ️  Alternativa: BTC bilan altcoinlar korrelyatsiyasini ishlatish")
print()
print("=" * 80)
