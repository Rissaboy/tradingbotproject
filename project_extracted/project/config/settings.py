# =====================================================
# SARDOR TRADING BOT - BARCHA SOZLAMALAR
# =====================================================

# Birja sozlamalari
EXCHANGE_NAME = "binance"        # binance, bybit, mexc, gateio, bingx
USE_TESTNET = True               # True = test, False = real

# REAL SAVDO sozlamalari (MUHIM!)
LIVE_TRADING = False             # False = simulyatsiya, True = HAQIQIY order!
# DIQQAT: LIVE_TRADING = True qilsangiz bot HAQIQIY pul bilan savdo qiladi!
# Avval USE_TESTNET = True bilan sinab ko'ring
ORDER_SIZE_USD = 10              # Har bir savdo uchun summa ($)
MIN_BALANCE_USD = 20             # Bundan kam balansda savdo qilmaydi

# Trading sozlamalari
TIMEFRAME = "5m"                 # 1m, 5m, 15m, 1h, 4h
STOP_LOSS_PCT = 3.0              # Stop-Loss %
TAKE_PROFIT_PCT = 3.0            # Take-Profit %
RISK_PER_TRADE = 1.5             # Har savdoda risk %
MAX_DAILY_LOSS_PCT = 5.0         # Kunlik max zarar %
MAX_CONSECUTIVE_LOSSES = 3       # Ketma-ket max zarar
MAX_OPEN_POSITIONS = 5           # Bir vaqtda max pozitsiya

# Indikator sozlamalari
EMA_SHORT = 50
EMA_LONG = 200
MIN_SIGNALS = 2                  # Minimum signal soni

# Trailing Stop-Loss
TRAILING_ACTIVATE_PCT = 1.5      # Trailing yonadigan %
TRAILING_DISTANCE_PCT = 1.0      # SL masofasi %

# Dynamic SL/TP (ATR asosida)
DYNAMIC_SLTP_ENABLED = True      # True = har coin uchun alohida SL/TP
ATR_SL_MULTIPLIER = 2.0         # SL = ATR * 2
ATR_TP_MULTIPLIER = 2.5         # TP = ATR * 2.5
MIN_SL_PCT = 1.0                # Minimum SL (juda kichik bo'lmasin)
MAX_SL_PCT = 8.0                # Maximum SL (juda katta bo'lmasin)
MIN_TP_PCT = 1.5                # Minimum TP
MAX_TP_PCT = 10.0               # Maximum TP

 # Multi-timeframe sozlamalari
MULTI_TIMEFRAME_ENABLED = True   # True = bir necha timeframe tekshirish
TIMEFRAMES = ["5m", "15m", "1h"] # Qaysi timeframlarni tekshirish
# Qoida: signal 5m da topilsa, 15m va 1h da trend mos kelishi kerak
# 5m = kirish signal
# 15m = trend tasdiqlash
# 1h = katta trend yo'nalishi

# Mean Reversion
RSI_OVERSOLD = 25                # RSI pastki zona
RSI_OVERBOUGHT = 75              # RSI yuqori zona

# AI sozlamalari
AI_ENABLED = True                # AI yoqish/o'chirish
AI_MIN_CONFIDENCE = 0.55         # Minimum AI ishonch (0.0 - 1.0)
AI_MODEL_FILE = "ai/models/sardor_ai_model.pkl"
AI_FEATURES_FILE = "ai/models/sardor_ai_features.pkl"

# Scanner sozlamalari
SCANNER_FILE = "scanner/top_coins.json"
MIN_VOLUME_24H = 10000000        # Min 24h hajm ($)
MIN_PRICE = 0.001                # Min narx ($)
MAX_COINS = 30                   # Nechta coin tanlash
SCAN_TIMEFRAME = "1h"            # Scanner timeframe

 
# Session filter (savdo soatlari)
SESSION_FILTER_ENABLED = False   # False = 24/7 savdo (kripto doim ishlaydi)
# Kripto 24/7 ishlaydi, lekin eng aktiv vaqtlar:
# Asia session: 00:00 - 08:00 UTC (Toshkent: 05:00 - 13:00)
# Europe session: 07:00 - 16:00 UTC (Toshkent: 12:00 - 21:00)
# US session: 13:00 - 22:00 UTC (Toshkent: 18:00 - 03:00)
# Eng yaxshi vaqt: Europe + US overlap = 13:00-16:00 UTC
TRADING_HOURS_UTC = [
    (0, 2),     # Asia session boshi (tinch, kam savdo)
    (7, 16),    # Europe session (yaxshi)
    (13, 22),   # US session (eng aktiv)
]
# Yoki sodda: faqat shu soatlarda savdo qilsin (UTC)
ACTIVE_HOURS_START = 7    # UTC 07:00 (Toshkent 12:00)
ACTIVE_HOURS_END = 22     # UTC 22:00 (Toshkent 03:00)
# Bu oraliqda savdo qiladi, qolgan vaqtda faqat ochiq pozitsiyalarni kuzatadi

# Fayl joylashuvi
EXCEL_FILE = "data/trades_history.xlsx"
LOG_FILE = "data/logs/bot.log"
 
# Portfolio balancing
PORTFOLIO_BALANCE_ENABLED = True  # True = diversifikatsiya
MAX_SAME_DIRECTION = 3           # Max 3 ta LONG yoki 3 ta SHORT bir vaqtda
MAX_PER_SECTOR = 2               # Bir sektorda max 2 ta pozitsiya
# Sektorlar (o'xshash coinlar birgalikda harakat qiladi)
SECTOR_MAP = {
    "layer1": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "NEAR/USDT", "SUI/USDT"],
    "defi": ["AAVE/USDT", "UNI/USDT", "LINK/USDT", "INJ/USDT"],
    "meme": ["DOGE/USDT", "PENGU/USDT", "WLD/USDT", "BONK/USDT"],
    "layer2": ["ARB/USDT", "OP/USDT", "POL/USDT"],
    "ai_tokens": ["FET/USDT", "TAO/USDT", "RENDER/USDT"],
    "other": []
}

# Qora ro'yxat (stablecoinlar)
BLACKLIST = [
    "USDC/USDT",
    "BUSD/USDT",
    "TUSD/USDT",
    "USDP/USDT",
    "FDUSD/USDT",
    "DAI/USDT",
    "USDD/USDT"
]

# Default juftliklar (scanner ishlamasa)
DEFAULT_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "DOGE/USDT",
    "ADA/USDT",
    "AVAX/USDT",
    "DOT/USDT",
    "LINK/USDT",
    "POL/USDT"
]


# Grid Trading sozlamalari
GRID_TRADING_ENABLED = True      # Grid bot yoqish/o'chirish
GRID_LEVELS = 5                  # Har tomonga 5 ta daraja (jami 10)
GRID_SPACING_PCT = 0.5           # Darajalar orasidagi masofa (0.5%)
GRID_ORDER_SIZE_PCT = 2.0        # Har grid orderda balansning 2%
GRID_TAKE_PROFIT_PCT = 0.8       # Har grid savdoda 0.8% foyda olish
GRID_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]  # Grid uchun juftliklar
GRID_RESET_DISTANCE = 5.0       # Grid qayta yaratish masofasi (%)


# DCA (Dollar Cost Averaging) sozlamalari
DCA_ENABLED = True               # DCA yoqish/o'chirish
DCA_MAX_ORDERS = 5               # Maksimum DCA orderlar soni
DCA_STEP_PCT = 2.0               # Har 2% tushganda yangi order
DCA_MULTIPLIER = 1.5             # Har keyingi order 1.5x katta
DCA_TAKE_PROFIT_PCT = 1.5        # O'rtacha narxdan 1.5% foyda = yopish


# Telegram Signal Kanal sozlamalari
SIGNAL_CHANNEL_ENABLED = True    # Signal kanalga yuborish
SIGNAL_CHANNEL_ID = "@sardor_trading_signals"  # Kanal username yoki ID
# Kanal yaratish:
# 1. Telegram da yangi kanal yarating
# 2. Botni kanalga admin qiling
# 3. Kanal username ni shu yerga yozing (@kanal_nomi)
