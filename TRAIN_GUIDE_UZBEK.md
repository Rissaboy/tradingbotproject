# 🎓 SERVERDA AI NI TRAIN QILISH QO'LLANMASI

## 📌 Muhim Ma'lumot
- **Bot joyi serverda**: 24/7 ishlab turibdi
- **AI modelni qayta o'rgatish**: Har 7 kunda avtomatik yoki qo'lda
- **Training vaqti**: 5-10 daqiqa (internetga bog'liq)

---

## 🔧 SERVERGA KIRISH

```bash
# SSH orqali serveringizga kiring
ssh username@your_server_ip

# Yoki cloud provideringiz dashboardidan terminal oching
# (AWS, DigitalOcean, Hetzner, etc.)

# Bot papkasiga o'ting
cd /path/to/tradingbotproject/project
```

---

## ✅ 1-USUL: BIRINCHI MARTA TO'LIQ TRAIN (Tavsiya etiladi)

Agar modelingiz yo'q yoki juda eski bo'lsa, **to'liq train** qiling:

```bash
# Botni to'xtating (majburiy emas, lekin tavsiya)
# Agar screen/tmux ishlatayotgan bo'lsangiz:
screen -r bot   # yoki tmux attach -t bot
# Ctrl+C bosib botni to'xtating

# AI modelni o'rgating
python ai/sardor_ai_trainer.py
```

### 📊 Natija Qanday Ko'rinadi:

```
============================================================
  SARDOR AI MODEL TRAINER v2
  XGBoost - kuchaytirilgan versiya
  Juftliklar: 10 ta
  Davr: 60 kun
============================================================

>>> Ma'lumot yig'ilmoqda (bu 5-10 daqiqa olishi mumkin)...

  BTC/USDT yuklanmoqda...
    17280 ta sham yuklandi
  ETH/USDT yuklanmoqda...
    17280 ta sham yuklandi
  ... (8 ta coin yana)

>>> Jami: 155,234 ta ma'lumot
>>> Foydali signallar: 23,451 (15.1%)
>>> Zarali signallar: 131,783 (84.9%)

>>> Model o'qitilmoqda...
  Train: 124,187 ta
  Test: 31,047 ta
  Features: 33 ta

============================================================
  AI MODEL v2 NATIJALARI
============================================================

  Aniqlik (Accuracy): 96.3%

  THRESHOLD BO'YICHA NATIJALAR:
  --------------------------------------------------
  Threshold 50%: 8,234 signal | Aniqlik: 61.2%
  Threshold 60%: 5,123 signal | Aniqlik: 68.7%
  Threshold 70%: 2,891 signal | Aniqlik: 74.3%
  Threshold 80%: 1,234 signal | Aniqlik: 82.1%
  --------------------------------------------------

  ENG MUHIM INDIKATORLAR (TOP 15):
  --------------------------------------------------
  1. change_3: 8.3% ###########
  2. ema_diff: 7.1% ##########
  3. rsi: 6.8% #########
  4. volume_ratio: 6.2% ########
  5. atr_pct: 5.9% ########
  ... (10 ta yana)
  --------------------------------------------------

  Model saqlandi: ai/models/sardor_ai_model.pkl
  Features saqlandi: ai/models/sardor_ai_features.pkl

============================================================
  TAYYOR! Botda yangi AI model ishlatiladi.
============================================================
```

### ✅ Keyin Botni Qayta Ishga Tushiring:

```bash
# Botni yangi model bilan ishga tushiring
python bot/main.py

# Yoki screen/tmux ichida:
screen -S bot python bot/main.py
# Ctrl+A+D bosib chiqing (bot fonda ishlaydi)
```

---

## ✅ 2-USUL: TEZKOR QAYTA O'RGATISH (Auto-retrain)

Har 7 kunda avtomatik yoki qo'lda:

```bash
cd /path/to/tradingbotproject/project
python ai/auto_retrain.py
```

### 📊 Natija:

```
============================================================
  AUTO AI RETRAINING
  Vaqt: 2026-07-02 18:45
============================================================

  BTC/USDT yuklanmoqda...
  ETH/USDT yuklanmoqda...
  ... (10 ta coin)

  Yangi model Accuracy: 95.8%
  Data: 145,123 ta
  Eski model Accuracy: 94.2%

  YANGI MODEL SAQLANDI! (95.8% >= 94.2%)

  Keyingi retraining: 7 kundan keyin
============================================================
```

### ⚠️ Muhim:
- **Agar yangi model yomonroq** bo'lsa, eski model saqlanib qoladi
- **Botni to'xtatish shart emas** - model almashtirish avtomatik

---

## ✅ 3-USUL: CRON JOB BILAN AVTOMATLASHTIRISH

Har 7 kunda avtomatik train qilsin:

```bash
# Crontab ochish
crontab -e

# Quyidagi qatorni qo'shing:
# Har dushanba kuni soat 03:00 da (serveringiz UTC vaqti bo'yicha)
0 3 * * 1 cd /path/to/tradingbotproject/project && /usr/bin/python3 ai/auto_retrain.py >> /path/to/logs/retrain.log 2>&1

# Saqlab chiqing: Ctrl+X, Y, Enter
```

### 📝 Tushuntirish:
- `0 3 * * 1` = Har dushanba soat 03:00 da
- `cd /path/to/...` = Bot papkasiga o'tish
- `python3 ai/auto_retrain.py` = Skriptni ishga tushirish
- `>> logs/retrain.log` = Natijalarni faylga yozish

---

## 🔍 MODEL ISHLAYAPTIMI TEKSHIRISH

```bash
cd /path/to/tradingbotproject/project

# Model fayllari bormi?
ls -lh ai/models/

# Natija:
# -rw-r--r-- 1 user user 2.3M Jul  2 18:45 sardor_ai_model.pkl
# -rw-r--r-- 1 user user 1.2K Jul  2 18:45 sardor_ai_features.pkl

# Model qachon o'zgartirilgan?
stat ai/models/sardor_ai_model.pkl

# Bot loglarini ko'ring
tail -f data/logs/bot.log

# AI ishlatayaptimi?
# Logda shu qatorlarni qidiring:
# "✅ AI signal: 0.78 (78%)" - AI ishlayapti
```

---

## 🛠️ MUAMMOLARNI HAL QILISH

### ❌ Xato: "ModuleNotFoundError: No module named 'xgboost'"

```bash
# Python kutubxonalarni o'rnating
cd /path/to/tradingbotproject/project
pip install -r requirements.txt

# Yoki alohida:
pip install xgboost scikit-learn pandas numpy ta ccxt joblib
```

---

### ❌ Xato: "ccxt.errors.RequestTimeout"

**Sabab:** Internet sekin yoki Binance APIga ulanish muammosi

**Yechim:**
```bash
# 1. Internetni tekshiring
ping binance.com

# 2. API limitga taqilganmisiz?
# Binance: 1200 requests/minute
# Har bir coin uchun ~20 request kerak
# 10 coins = 200 requests = OK ✅

# 3. Yana urinib ko'ring
python ai/sardor_ai_trainer.py
```

---

### ❌ Xato: "FileNotFoundError: ai/models/"

```bash
# models papkasini yarating
mkdir -p ai/models

# Qayta urinib ko'ring
python ai/sardor_ai_trainer.py
```

---

### ❌ Model yaratildi, lekin bot ishlatmayapti

```bash
# 1. Model fayl joyi to'g'rimi?
ls ai/models/sardor_ai_model.pkl

# 2. settings.py da yo'l to'g'rimi?
cat config/settings.py | grep AI_MODEL_FILE
# Natija: AI_MODEL_FILE = "ai/models/sardor_ai_model.pkl"

# 3. AI yoqilganmi?
cat config/settings.py | grep AI_ENABLED
# Natija: AI_ENABLED = True

# 4. Botni qayta ishga tushiring
pkill -f "python bot/main.py"  # Eski botni to'xtating
python bot/main.py              # Yangi botni ishga tushiring
```

---

## 📊 QAYSI USULNI TANLASH?

| Holat | Usul | Vaqt | Qachon? |
|-------|------|------|---------|
| **Birinchi marta** | `sardor_ai_trainer.py` | 5-10 min | 1 marta |
| **Har 7 kunda qo'lda** | `auto_retrain.py` | 3-5 min | Kerak bo'lganda |
| **Avtomatik har 7 kunda** | Cron job | 3-5 min | Serverda o'rnatib qo'yish |

---

## ✅ TAVSIYALAR

### 1. **Birinchi Marta To'liq Train Qiling**
```bash
python ai/sardor_ai_trainer.py
```
- 60 kunlik ma'lumot
- 10 ta coin
- Eng yaxshi model

### 2. **Har 7 Kunda Auto-Retrain Qiling**
```bash
# Crontab qo'shing:
0 3 * * 1 cd /path/to/project && python3 ai/auto_retrain.py >> logs/retrain.log 2>&1
```
- Avtomatik yangilanadi
- Bot to'xtamaydi
- Eski model yaxshiroq bo'lsa, saqlanadi

### 3. **Loglarni Tekshiring**
```bash
# Retraining loglari
tail -f logs/retrain.log

# Bot loglari (AI ishlatayaptimi?)
tail -f data/logs/bot.log | grep AI
```

### 4. **Modelni Backup Qiling**
```bash
# Har safar train qilganda eskisini saqlang
cp ai/models/sardor_ai_model.pkl ai/models/backup_$(date +%Y%m%d).pkl

# Agar yangi model yomon bo'lsa, eskisini qaytaring
cp ai/models/backup_20260702.pkl ai/models/sardor_ai_model.pkl
```

---

## 🎯 OPTIMAL SOZLAMALAR (settings.py)

Serverda 24/7 ishlashi uchun:

```python
# Training
DAYS_TO_FETCH = 60              # ✅ 60 kun (eski: 30)

# AI
AI_ENABLED = True               # ✅ Yoqilgan
AI_MIN_CONFIDENCE = 0.75        # ✅ 75% (eski: 70%)

# Risk
RISK_PER_TRADE = 0.8            # ✅ 0.8% (eski: 1.5%)
MAX_OPEN_POSITIONS = 3          # ✅ 3 ta (eski: 5)
STOP_LOSS_PCT = 2.0             # ✅ 2% (eski: 3%)
TAKE_PROFIT_PCT = 4.0           # ✅ 4% (eski: 3%)

# Signallar
MIN_SIGNALS = 3                 # ✅ 3 ta (eski: 2)
```

---

## 📞 SAVOL-JAVOBLAR

**Q: Har safar train qilganda botni to'xtatish kerakmi?**  
A: Yo'q, `auto_retrain.py` ishlatayotgan bo'lsangiz shart emas. Lekin `sardor_ai_trainer.py` ishlatayotgan bo'lsangiz, to'xtatish yaxshi (resurslar tejash uchun).

**Q: Train qilish qancha vaqt oladi?**  
A: 5-10 daqiqa (internetga bog'liq). Binance API dan 60 kunlik ma'lumot yuklanadi.

**Q: Model qancha hajm?**  
A: ~2-3 MB (kichik, tezkor)

**Q: Serverda RAM yetadimi?**  
A: 1-2 GB RAM yetadi. Agar 512 MB bo'lsa, qisqa muddatda 2 GB ga ko'tariladi (training paytida).

**Q: VPS qayerdan olish yaxshi?**  
A: 
- **Arzon**: Contabo, Hetzner (~$3-5/oy)
- **Tezkor**: DigitalOcean, Vultr (~$5-10/oy)
- **Kuchli**: AWS, Google Cloud (~$10-20/oy)

**Q: Training paytida internet uzilsa?**  
A: Script xato beradi. Qayta ishga tushiring, davom etadi.

**Q: Bir necha coin qo'shsam, ko'proq vaqt oladimi?**  
A: Ha. 10 coin = 5-10 min, 20 coin = 10-20 min, 50 coin = 30-60 min.

---

## 🚀 KEYINGI QADAMLAR

1. ✅ **Hozir**: AI modelni train qiling (`sardor_ai_trainer.py`)
2. ✅ **Keyin**: Yangi parametrlarni testnetda sinab ko'ring
3. ✅ **Oxirida**: Real hisobda ishga tushiring
4. ✅ **Har 7 kunda**: Auto-retrain avtomatik ishlaydi (cron job)

---

**Tayyor! Savollaringiz bormi, Sardor?** 😊
