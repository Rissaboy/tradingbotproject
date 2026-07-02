# =====================================================
# SARDOR TRADING BOT - BARCHA SOZLAMALAR
# =====================================================

# Birja sozlamalari
EXCHANGE_NAME = "binance"        # binance, bybit, mexc, gateio, bingx
USE_TESTNET = True               # True = test, False = real

# Trading sozlamalari
TIMEFRAME = "5m"                 # 1m, 5m, 15m, 1h, 4h
STOP_LOSS_PCT = 2.0              # Stop-Loss % (TIGHTENED from 3.0)
TAKE_PROFIT_PCT = 4.0            # Take-Profit % (IMPROVED R:R ratio)
RISK_PER_TRADE = 0.8             # Har savdoda risk % (REDUCED from 1.5)
MAX_DAILY_LOSS_PCT = 3.0         # Kunlik max zarar % (REDUCED from 5.0)
MAX_CONSECUTIVE_LOSSES = 2       # Ketma-ket max zarar (REDUCED from 3)
MAX_OPEN_POSITIONS = 3           # Bir vaqtda max pozitsiya (REDUCED from 5)

# Indikator sozlamalari
EMA_SHORT = 50
EMA_LONG = 200
MIN_SIGNALS = 3                  # Minimum signal soni (INCREASED from 2 - more confirmation needed)

# Trailing Stop-Loss
TRAILING_ACTIVATE_PCT = 1.5      # Trailing yonadigan %
TRAILING_DISTANCE_PCT = 1.0      # SL masofasi %

# Dynamic SL/TP (ATR asosida)
DYNAMIC_SLTP_ENABLED = True      # True = har coin uchun alohida SL/TP
ATR_SL_MULTIPLIER = 1.5         # SL = ATR * 1.5 (TIGHTENED from 2.0)
ATR_TP_MULTIPLIER = 3.0         # TP = ATR * 3.0 (Better risk/reward ratio)
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
AI_MIN_CONFIDENCE = 0.80         # Minimum AI ishonch (INCREASED to 0.80 for better quality)
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
# GRID TRADING SOZLAMALARI (Eski bot uchun)
# =====================================================
GRID_TRADING_ENABLED = False     # Grid trading o'chirilgan
GRID_LEVELS = 10                 # Grid darajalari soni
GRID_SPACING_PCT = 0.5           # Gridlar orasidagi masofa %
GRID_POSITION_SIZE_PCT = 10.0    # Har bir grid uchun hajm %
GRID_ORDER_SIZE_PCT = 10.0       # Eski bot uchun (GRID_POSITION_SIZE_PCT bilan bir xil)
GRID_TAKE_PROFIT_PCT = 5.0       # Grid TP %
GRID_STOP_LOSS_PCT = 10.0        # Grid SL %
GRID_MIN_PROFIT_PCT = 0.5        # Grid minimal foyda %
GRID_MAX_ORDERS = 10             # Maksimal grid orderlar soni
GRID_SYMBOLS = []                # Grid uchun coinlar ro'yxati (bo'sh = barcha)

# =====================================================
# DCA TRADING SOZLAMALARI (Dollar Cost Averaging)
# =====================================================
DCA_ENABLED = False              # DCA trading o'chirilgan
DCA_MAX_ORDERS = 5               # Maksimal DCA orderlar soni
DCA_STEP_PCT = 2.0               # Har bir DCA qadami % (narx 2% tushganda)
DCA_SIZE_MULTIPLIER = 1.5        # Har bir DCA order hajmi multiplier
DCA_MULTIPLIER = 1.5             # DCA_SIZE_MULTIPLIER bilan bir xil (eski bot uchun)
DCA_TAKE_PROFIT_PCT = 3.0        # DCA umumiy TP %
DCA_MAX_DEVIATION_PCT = 10.0     # Maksimal narx og'ishi % (10% dan ortiq tushsa to'xtatish)

# =====================================================
# SIGNAL CHANNEL SOZLAMALARI (Telegram signal kanallar)
# =====================================================
SIGNAL_CHANNEL_ENABLED = False   # Signal channel o'chirilgan
SIGNAL_CHANNEL_ID = ""           # Telegram kanal ID (bo'sh = o'chiq)

# =====================================================
# QO'SHIMCHA SOZLAMALAR
# =====================================================
# Whale tracking (katta orderlar kuzatuvi)
WHALE_TRACKING_ENABLED = True    # Whale signallarini kuzatish
WHALE_MIN_SIZE_BTC = 50          # Minimum whale order hajmi (BTC)

# Smart Money sozlamalari
SMART_MONEY_ENABLED = True       # Smart Money flow kuzatuvi
SMART_MONEY_THRESHOLD = 1000000  # Min smart money hajm ($)

# Market regime detection
MARKET_REGIME_ENABLED = True     # Bozor holatini aniqlash (trending/ranging)
RANGING_ATR_THRESHOLD = 1.5      # ATR < 1.5% = ranging market
TRENDING_ATR_THRESHOLD = 3.5     # ATR > 3.5% = high volatility



# =====================================================
# LIVE TRADING SOZLAMALARI
# =====================================================
LIVE_TRADING = not USE_TESTNET  # True = real, False = testnet
ORDER_SIZE_USD = 100.0          # Order hajmi USD
MIN_BALANCE_USD = 50.0          # Minimal balans USD
