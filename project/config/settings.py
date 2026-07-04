# =====================================================
# SARDOR TRADING BOT - BARCHA SOZLAMALAR
# =====================================================

# Birja sozlamalari
EXCHANGE_NAME = "binance"        # binance, bybit, mexc, gateio, bingx
USE_TESTNET = True               # True = test, False = real

# Trading sozlamalari
TIMEFRAME = "5m"                 # 1m, 5m, 15m, 1h, 4h
STOP_LOSS_PCT = 2.0              # Stop-Loss % (OPTIMIZED: 3.0 → 2.0)
TAKE_PROFIT_PCT = 4.0            # Take-Profit % (OPTIMIZED: 3.0 → 4.0)
RISK_PER_TRADE = 0.8             # Har savdoda risk % (OPTIMIZED: 1.5 → 0.8)
MAX_DAILY_LOSS_PCT = 5.0         # Kunlik max zarar %
MAX_CONSECUTIVE_LOSSES = 3       # Ketma-ket max zarar
MAX_OPEN_POSITIONS = 3           # Bir vaqtda max pozitsiya (OPTIMIZED: 5 → 3)

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
AI_MIN_CONFIDENCE = 0.80         # Minimum AI ishonch (OPTIMIZED: 0.70 → 0.80)
AI_MODEL_FILE = "ai/models/sardor_ai_model.pkl"
AI_FEATURES_FILE = "ai/models/sardor_ai_features.pkl"

# Scanner sozlamalari
SCANNER_FILE = "scanner/top_coins.json"
MIN_VOLUME_24H = 10000000        # Min 24h hajm ($)
MIN_PRICE = 0.001                # Min narx ($)
MAX_COINS = 30                   # Nechta coin tanlash
SCAN_TIMEFRAME = "1h"            # Scanner timeframe

 
# Session filter (savdo soatlari)
SESSION_FILTER_ENABLED = True    # True = faqat aktiv soatlarda savdo
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

# =====================================================
# ADVANCED FEATURES (5 TA YANGI FUNKSIYA)
# =====================================================

# Feature 1: Volume Analysis (Hajm tahlili - kitlarni topish)
VOLUME_ANALYSIS_ENABLED = True
VOLUME_LOOKBACK_PERIODS = 20        # O'rtacha hajm uchun nechtaga qarash
VOLUME_SPIKE_MULTIPLIER = 3.0       # Spike = 3x o'rtachadan katta

# Feature 2: Order Book Analysis (Support/Resistance tahlili)
ORDERBOOK_ANALYSIS_ENABLED = True
ORDERBOOK_DEPTH_LIMIT = 20          # Order book chuqurligi
ORDERBOOK_IMBALANCE_THRESHOLD = 2.0 # Bid/Ask nomutanosiblik (2x)

# Feature 3: Multi-Exchange Arbitrage (Bir necha birjalar orasida narx farqi)
ARBITRAGE_ENABLED = False            # ⚠️ Ehtiyotkorlik bilan yoqing!
ARBITRAGE_MIN_PROFIT_PCT = 0.5      # Minimum foyda (komissiyadan keyin)
ARBITRAGE_EXCHANGES = {
    "binance": {"testnet": True},
    "bybit": {"testnet": True},
    # "gateio": {"testnet": False},
    # "mexc": {"testnet": False},
}
ARBITRAGE_SCAN_INTERVAL = 60        # Har 60 sekundda skaner (rate limit uchun)

# Feature 4: Sentiment Analysis (Bozor kayfiyati tahlili)
SENTIMENT_ANALYSIS_ENABLED = True
SENTIMENT_SOURCES = ["alternative.me"]  # Fear & Greed Index
SENTIMENT_UPDATE_INTERVAL = 3600    # Har 1 soatda yangilash
SENTIMENT_MIN_INFLUENCE = 2.0       # Sentiment ta'siri (kuch koeffitsenti)

# Feature 5: ML Ensemble (Bir necha AI modellar)
ML_ENSEMBLE_ENABLED = False          # ⚠️ Avval modellarni o'qitish kerak!
ML_ENSEMBLE_MODELS_DIR = "ai/models/ensemble"
ML_ENSEMBLE_MIN_CONFIDENCE = 0.65   # Minimum ishonch (ensemble dan)
ML_ENSEMBLE_MODELS = {
    "randomforest": 1.0,   # Og'irlik (asosiy model)
    "xgboost": 1.2,        # Eng aniq
    "lightgbm": 1.1,       # Tez va aniq
    "extratrees": 0.9      # Qo'shimcha
}

# Advanced Features ni birga ishlatish
# Agar bitta feature signal bersa va boshqasi tasdiqlasa = KUCHLI signal
# Feature Priority (qaysi biri muhimroq):
# 1. AI Model (asosiy)
# 2. Volume Analysis (kitlar harakati)
# 3. Order Book (support/resistance)
# 4. Sentiment (bozor kayfiyati)
# 5. ML Ensemble (agar o'qitilgan bo'lsa)
# 6. Arbitrage (alohida strategiya)
