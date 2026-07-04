import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_keys import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from config.settings import EXCHANGE_NAME, AI_ENABLED, AI_MIN_CONFIDENCE

NL = chr(10)
last_update_id = 0

def send_telegram(message):
    try:
        url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("  Telegram xato: " + str(e))

def check_telegram_commands(bot_active, open_positions, get_balance_func):
    global last_update_id
    try:
        url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/getUpdates"
        params = {"offset": last_update_id + 1, "timeout": 5}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if not data.get("ok"):
            return bot_active

        for update in data.get("result", []):
            last_update_id = update["update_id"]
            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = str(message.get("chat", {}).get("id", ""))

            if chat_id != TELEGRAM_CHAT_ID:
                continue

            if text == "/start":
                bot_active = True
                send_telegram("BOT YOQILDI! Savdo boshlandi.")
                print("  >>> TELEGRAM: Bot YOQILDI")
            elif text == "/stop":
                bot_active = False
                send_telegram("BOT TO'XTATILDI! Ochiq pozitsiyalar kuzatilmoqda.")
                print("  >>> TELEGRAM: Bot TO'XTATILDI")
            elif text == "/status":
                status = "YOQILGAN" if bot_active else "TO'XTATILGAN"
                ai_status = "AI: YOQILGAN (" + str(int(AI_MIN_CONFIDENCE * 100)) + "%)" if AI_ENABLED else "AI: O'CHIQ"
                send_telegram("Bot: " + status + " | " + ai_status + " | " + EXCHANGE_NAME.upper())
            elif text == "/balance":
                try:
                    bal = get_balance_func()
                    send_telegram("Balans: $" + str(round(bal, 2)) + " USDT | " + EXCHANGE_NAME.upper())
                except:
                    send_telegram("Balansni olishda xato")
            elif text == "/positions":
                if len(open_positions) == 0:
                    send_telegram("Ochiq pozitsiyalar yo'q")
                else:
                    msg = "Ochiq pozitsiyalar:" + NL
                    for sym, pos in open_positions.items():
                        msg = msg + sym + " " + pos["type"] + " @ $" + str(round(pos["entry_price"], 2)) + " (" + pos["strategy"] + ") AI:" + str(round(pos["ai_confidence"] * 100)) + "%" + NL
                    send_telegram(msg)
            
            # Advanced Features Commands
            elif text == "/sentiment":
                try:
                    from bot.sentiment_analysis import SentimentAnalyzer
                    analyzer = SentimentAnalyzer()
                    report = analyzer.get_sentiment_report()
                    send_telegram(report)
                except Exception as e:
                    send_telegram("Sentiment xato: " + str(e))
            
            elif text.startswith("/volume"):
                try:
                    from bot.volume_analysis import VolumeAnalyzer
                    from bot.exchange import get_klines
                    parts = text.split()
                    symbol = parts[1] + "/USDT" if len(parts) > 1 else "BTC/USDT"
                    
                    analyzer = VolumeAnalyzer()
                    df = get_klines(symbol)
                    result = analyzer.analyze_volume(df, symbol)
                    
                    msg = "<b>📊 VOLUME ANALYSIS: " + symbol.replace("/USDT", "") + "</b>" + NL + NL
                    if result.get("signal"):
                        emoji = "🟢" if result["signal"] == "LONG" else "🔴"
                        msg = msg + emoji + " Signal: " + result["signal"] + NL
                        msg = msg + "Kuch: " + str(round(result["strength"], 2)) + NL
                    msg = msg + "Sabab: " + result["reason"]
                    send_telegram(msg)
                except Exception as e:
                    send_telegram("Volume xato: " + str(e))
            
            elif text.startswith("/orderbook"):
                try:
                    from bot.orderbook_analysis import OrderBookAnalyzer
                    from bot.exchange import exchange as exc
                    parts = text.split()
                    symbol = parts[1] + "/USDT" if len(parts) > 1 else "BTC/USDT"
                    
                    analyzer = OrderBookAnalyzer(exc)
                    result = analyzer.analyze_orderbook(symbol)
                    
                    msg = "<b>📚 ORDER BOOK: " + symbol.replace("/USDT", "") + "</b>" + NL + NL
                    if result.get("signal"):
                        emoji = "🟢" if result["signal"] == "LONG" else "🔴"
                        msg = msg + emoji + " Signal: " + result["signal"] + NL
                        msg = msg + "Kuch: " + str(round(result["strength"], 2)) + NL
                    msg = msg + "Sabab: " + result["reason"] + NL + NL
                    if result.get("details"):
                        msg = msg + "Bid/Ask: " + str(round(result["details"].get("imbalance_ratio", 1), 2))
                    send_telegram(msg)
                except Exception as e:
                    send_telegram("OrderBook xato: " + str(e))
            
            elif text == "/arbitrage":
                try:
                    from bot.arbitrage import ArbitrageAnalyzer
                    analyzer = ArbitrageAnalyzer(min_profit_pct=0.5)
                    
                    test_symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT"]
                    opportunities = analyzer.scan_arbitrage_opportunities(test_symbols)
                    
                    report = analyzer.get_arbitrage_report(opportunities)
                    send_telegram(report)
                except Exception as e:
                    send_telegram("Arbitrage xato: " + str(e))
            
            elif text == "/retrain":
                try:
                    send_telegram("🤖 AI model qayta o'rgatilmoqda..." + NL + "Bu 5-10 daqiqa davom etadi...")
                    from ai.auto_retrain import retrain
                    accuracy = retrain()
                    
                    msg = "<b>✅ AI MODEL YANGILANDI</b>" + NL + NL
                    msg = msg + "Accuracy: " + str(round(accuracy * 100, 1)) + "%" + NL
                    msg = msg + "Model: ai/models/sardor_ai_model.pkl" + NL + NL
                    msg = msg + "Bot avtomatik yangi modeldan foydalanadi."
                    send_telegram(msg)
                except Exception as e:
                    send_telegram("❌ Retrain xato: " + str(e))
            
            elif text == "/features":
                from config.settings import VOLUME_ANALYSIS_ENABLED, ORDERBOOK_ANALYSIS_ENABLED, ARBITRAGE_ENABLED, SENTIMENT_ANALYSIS_ENABLED, ML_ENSEMBLE_ENABLED
                msg = "<b>🚀 ADVANCED FEATURES</b>" + NL + NL
                msg = msg + "1. Volume Analysis: " + ("✅" if VOLUME_ANALYSIS_ENABLED else "❌") + NL
                msg = msg + "2. Order Book: " + ("✅" if ORDERBOOK_ANALYSIS_ENABLED else "❌") + NL
                msg = msg + "3. Arbitrage: " + ("✅" if ARBITRAGE_ENABLED else "❌") + NL
                msg = msg + "4. Sentiment: " + ("✅" if SENTIMENT_ANALYSIS_ENABLED else "❌") + NL
                msg = msg + "5. ML Ensemble: " + ("✅" if ML_ENSEMBLE_ENABLED else "❌") + NL + NL
                msg = msg + "Buyruqlar:" + NL
                msg = msg + "/sentiment - Bozor kayfiyati" + NL
                msg = msg + "/volume BTC - Hajm tahlili" + NL
                msg = msg + "/orderbook ETH - Order book" + NL
                msg = msg + "/arbitrage - Arbitraj scan"
                send_telegram(msg)
            
            elif text == "/help":
                msg = "Buyruqlar:" + NL + NL
                msg = msg + "<b>Asosiy:</b>" + NL
                msg = msg + "/start - Savdoni yoqish" + NL
                msg = msg + "/stop - Savdoni to'xtatish" + NL
                msg = msg + "/status - Bot holati" + NL
                msg = msg + "/balance - Balans" + NL
                msg = msg + "/positions - Ochiq pozitsiyalar" + NL + NL
                msg = msg + "<b>Advanced:</b>" + NL
                msg = msg + "/features - Feature status" + NL
                msg = msg + "/sentiment - Bozor kayfiyati" + NL
                msg = msg + "/volume [COIN] - Hajm tahlili" + NL
                msg = msg + "/orderbook [COIN] - Order book" + NL
                msg = msg + "/arbitrage - Arbitraj scan" + NL
                msg = msg + "/retrain - AI modelni qayta o'rgatish" + NL + NL
                msg = msg + "/help - Yordam"
                send_telegram(msg)
    except Exception as e:
        pass
    return bot_active


 
def send_telegram_chart(symbol, df, entry_price=None, sl_price=None, tp_price=None):
    """Signal bilan birga grafik rasm yuborish"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import os
 
    try:
        chart_df = df.tail(50).copy()
        chart_df = chart_df.reset_index(drop=True)
 
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [3, 1]})
 
        ax1.plot(chart_df.index, chart_df["close"], color="white", linewidth=1.5, label="Narx")
        ax1.plot(chart_df.index, chart_df["bb_upper"], color="gray", linewidth=0.8, linestyle="--", label="BB Upper")
        ax1.plot(chart_df.index, chart_df["bb_lower"], color="gray", linewidth=0.8, linestyle="--", label="BB Lower")
        ax1.plot(chart_df.index, chart_df["ema_short"], color="cyan", linewidth=1, label="EMA 50")
        ax1.plot(chart_df.index, chart_df["ema_long"], color="orange", linewidth=1, label="EMA 200")
 
        if entry_price:
            ax1.axhline(y=entry_price, color="yellow", linewidth=1.5, linestyle="-", label="Entry: $" + str(round(entry_price, 2)))
        if sl_price:
            ax1.axhline(y=sl_price, color="red", linewidth=1.5, linestyle="--", label="SL: $" + str(round(sl_price, 2)))
        if tp_price:
            ax1.axhline(y=tp_price, color="green", linewidth=1.5, linestyle="--", label="TP: $" + str(round(tp_price, 2)))
 
        ax1.set_title(symbol + " | Signal", color="white", fontsize=14, fontweight="bold")
        ax1.set_facecolor("#1a1a2e")
        ax1.tick_params(colors="white")
        ax1.legend(loc="upper left", fontsize=8, facecolor="#1a1a2e", labelcolor="white")
        ax1.grid(True, alpha=0.2)
 
        ax2.plot(chart_df.index, chart_df["rsi"], color="magenta", linewidth=1.5)
        ax2.axhline(y=70, color="red", linewidth=0.8, linestyle="--")
        ax2.axhline(y=30, color="green", linewidth=0.8, linestyle="--")
        ax2.axhline(y=50, color="gray", linewidth=0.5, linestyle="-")
        ax2.fill_between(chart_df.index, 30, 70, alpha=0.1, color="gray")
        ax2.set_title("RSI (14)", color="white", fontsize=10)
        ax2.set_facecolor("#1a1a2e")
        ax2.tick_params(colors="white")
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.2)
 
        fig.patch.set_facecolor("#0f0f1a")
        plt.tight_layout()
 
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        chart_path = os.path.join(root_dir, "data", "chart_temp.png")
        plt.savefig(chart_path, dpi=100, bbox_inches="tight", facecolor="#0f0f1a")
        plt.close()
 
        url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendPhoto"
        with open(chart_path, "rb") as photo:
            files = {"photo": photo}
            data = {"chat_id": TELEGRAM_CHAT_ID}
            requests.post(url, files=files, data=data, timeout=30)
 
        if os.path.exists(chart_path):
            os.remove(chart_path)
 
    except Exception as e:
        print("  Chart xato: " + str(e))
