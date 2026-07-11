import sys
import os
import time
import json
from datetime import datetime

# Loyiha root papkasini path ga qo'shish
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from config.settings import (
    EXCHANGE_NAME, USE_TESTNET, TIMEFRAME, STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    RISK_PER_TRADE, MAX_OPEN_POSITIONS, TRAILING_ACTIVATE_PCT,
    TRAILING_DISTANCE_PCT, AI_ENABLED, AI_MIN_CONFIDENCE,
    SCANNER_FILE, DEFAULT_SYMBOLS, EXCEL_FILE,
    # Advanced Features
    VOLUME_ANALYSIS_ENABLED, ORDERBOOK_ANALYSIS_ENABLED,
    ARBITRAGE_ENABLED, SENTIMENT_ANALYSIS_ENABLED, ML_ENSEMBLE_ENABLED
)

# Auto retraining
AUTO_RETRAIN_ENABLED = True
RETRAIN_INTERVAL_DAYS = 7
last_retrain_date = None
from bot.exchange import get_balance, get_klines, get_exchange_name
from bot.indicators import calculate_indicators, get_trend
from bot.strategies import get_signal, check_trend_buy, check_trend_sell, calculate_dynamic_sltp, is_trading_session, check_portfolio_balance, check_multi_timeframe, check_correlation_filter, check_sentiment_filter
from bot.risk_manager import RiskManager
from bot.telegram_bot import send_telegram, check_telegram_commands, send_telegram_chart
from ai.predictor import load_ai_model, ai_predict

# Advanced Features
from bot.volume_analysis import VolumeAnalyzer
from bot.orderbook_analysis import OrderBookAnalyzer
from bot.sentiment_analysis import SentimentAnalyzer
if ML_ENSEMBLE_ENABLED:
    from bot.ml_ensemble import MLEnsemble

import pandas as pd

NL = chr(10)


def save_to_excel(trade_data):
    """Savdoni Excel ga saqlash"""
    try:
        filepath = os.path.join(ROOT_DIR, EXCEL_FILE)
        dirpath = os.path.dirname(filepath)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        if os.path.exists(filepath):
            df = pd.read_excel(filepath)
            df = pd.concat([df, pd.DataFrame([trade_data])], ignore_index=True)
        else:
            df = pd.DataFrame([trade_data])
        df.to_excel(filepath, index=False)
    except Exception as e:
        print("  Excel xato: " + str(e))


def load_symbols():
    """Scanner natijasidan yoki default juftliklarni yuklash"""
    scanner_path = os.path.join(ROOT_DIR, SCANNER_FILE)
    if os.path.exists(scanner_path):
        try:
            with open(scanner_path, "r") as f:
                scanner_data = json.load(f)
            symbols = scanner_data.get("symbols", DEFAULT_SYMBOLS)
            print("  Scanner dan " + str(len(symbols)) + " ta coin yuklandi")
            return symbols
        except:
            return DEFAULT_SYMBOLS
    return DEFAULT_SYMBOLS


# ===================== ASOSIY BOT =====================
open_positions = {}

# Advanced Features initialization
volume_analyzer = None
orderbook_analyzer = None
sentiment_analyzer = None
ml_ensemble = None


def run_bot():
    global open_positions, volume_analyzer, orderbook_analyzer, sentiment_analyzer, ml_ensemble

    bot_active = True

    # Juftliklarni yuklash
    symbols = load_symbols()

    # AI model yuklash
    ai_loaded = False
    if AI_ENABLED:
        ai_loaded = load_ai_model()
    
    # Advanced Features yuklash
    if VOLUME_ANALYSIS_ENABLED:
        volume_analyzer = VolumeAnalyzer()
        print("  ✅ Volume Analysis yuklandi")
    
    if ORDERBOOK_ANALYSIS_ENABLED:
        from bot.exchange import exchange as exc
        orderbook_analyzer = OrderBookAnalyzer(exc)
        print("  ✅ Order Book Analysis yuklandi")
    
    if SENTIMENT_ANALYSIS_ENABLED:
        sentiment_analyzer = SentimentAnalyzer()
        print("  ✅ Sentiment Analysis yuklandi")
    
    if ML_ENSEMBLE_ENABLED:
        ml_ensemble = MLEnsemble()
        print("  ✅ ML Ensemble yuklandi")

    # Balans
    balance = get_balance()
    risk_manager = RiskManager(balance)

    print("")
    print("=" * 60)
    print("  SARDOR TRADING BOT v10 (Professional)")
    print("  Birja: " + get_exchange_name())
    print("  Testnet: " + str(USE_TESTNET))
    print("  Juftliklar: " + str(len(symbols)) + " ta")
    print("  Strategiya: Trend + Mean Reversion + AI")
    print("  AI: " + ("YOQILGAN (min " + str(int(AI_MIN_CONFIDENCE * 100)) + "%)" if ai_loaded else "O'CHIQ"))
    print("  Timeframe: " + TIMEFRAME)
    print("  SL: " + str(STOP_LOSS_PCT) + "% | TP: " + str(TAKE_PROFIT_PCT) + "%")
    print("  Trailing: " + str(TRAILING_ACTIVATE_PCT) + "%/" + str(TRAILING_DISTANCE_PCT) + "%")
    print("  Risk/savdo: " + str(RISK_PER_TRADE) + "%")
    print("  Max pozitsiya: " + str(MAX_OPEN_POSITIONS))
    print("  Telegram: /start /stop /status /balance /positions")
    print("=" * 60)
    print("  Boshlangich balans: $" + str(round(balance, 2)))
    print("")

    msg = "<b>Sardor Trading Bot v10 (Pro)</b> ishga tushdi!" + NL + NL
    msg = msg + "Birja: " + get_exchange_name() + NL
    msg = msg + "AI: " + ("YOQILGAN (" + str(int(AI_MIN_CONFIDENCE * 100)) + "%)" if ai_loaded else "O'CHIQ") + NL
    msg = msg + "Juftliklar: " + str(len(symbols)) + " ta" + NL
    msg = msg + "Balans: $" + str(round(balance, 2)) + NL
    msg = msg + "/help - buyruqlar"
    send_telegram(msg)

    while True:
        try:
            # Telegram buyruqlar
            bot_active = check_telegram_commands(bot_active, open_positions, get_balance)

            # Auto AI Retraining (har 7 kunda)
            global last_retrain_date
            if AUTO_RETRAIN_ENABLED and AI_ENABLED:
                today = datetime.now().date()
                if last_retrain_date is None:
                    last_retrain_date = today
                days_since_retrain = (today - last_retrain_date).days
                if days_since_retrain >= RETRAIN_INTERVAL_DAYS:
                    print("  >>> AI QAYTA O'RGATILMOQDA...")
                    try:
                        from ai.auto_retrain import retrain
                        new_accuracy = retrain()
                        last_retrain_date = today
                        ai_loaded = load_ai_model()
                        send_telegram("AI model qayta o'rgatildi! Accuracy: " + str(round(new_accuracy * 100, 1)) + "%")
                    except Exception as e:
                        print("  Retrain xato: " + str(e))
                        
            # Balans
            current_balance = get_balance()

            # Yangi kun
            is_new_day, yesterday_stats = risk_manager.new_day_check(current_balance)
            if is_new_day:
                msg = "🌅 <b>YANGI KUN BOSHLANDI!</b>" + NL + NL
                
                if yesterday_stats and yesterday_stats["trades"] > 0:
                    # Kecha statistikasi
                    msg = msg + "📊 <b>KECHA NATIJALAR</b>" + NL
                    msg = msg + "Sana: " + yesterday_stats["date"] + NL + NL
                    
                    msg = msg + "Savdolar: " + str(yesterday_stats["trades"]) + " ta" + NL
                    msg = msg + "Yutdi: " + str(yesterday_stats["wins"]) + " ta ✅" + NL
                    msg = msg + "Yutqazdi: " + str(yesterday_stats["losses"]) + " ta ❌" + NL
                    msg = msg + "Win rate: " + str(round(yesterday_stats["win_rate"], 1)) + "%" + NL + NL
                    
                    profit = yesterday_stats["profit"]
                    profit_emoji = "💰" if profit >= 0 else "📉"
                    profit_sign = "+" if profit >= 0 else ""
                    msg = msg + profit_emoji + " <b>Foyda: " + profit_sign + "$" + str(round(profit, 2)) + "</b>" + NL + NL
                    
                    msg = msg + "━━━━━━━━━━━━━━━━━━" + NL + NL
                
                msg = msg + "💵 Bugungi balans: $" + str(round(current_balance, 2))
                send_telegram(msg)

            # Status
            status_text = "YOQILGAN" if bot_active else "TO'XTATILGAN"
            ai_text = " | AI" if ai_loaded else ""
            session_ok, session_msg = is_trading_session()
            session_text = " | " + session_msg
            print("")
            print("[" + datetime.now().strftime("%H:%M:%S") + "] " + get_exchange_name() + ai_text + session_text + " | $" + str(round(current_balance, 2)) + " | Ochiq: " + str(len(open_positions)) + "/" + str(MAX_OPEN_POSITIONS) + " | " + status_text)

            # Har bir juftlikni tekshirish
            for symbol in symbols:
                try:
                    df = get_klines(symbol)
                    df = calculate_indicators(df)
                    df = df.dropna().reset_index(drop=True)

                    if len(df) < 2:
                        continue

                    row = df.iloc[-1]
                    prev = df.iloc[-2]
                    current_price = row["close"]
                    trend = get_trend(row)

                    # ===== OCHIQ POZITSIYA =====
                    if symbol in open_positions:
                        pos = open_positions[symbol]
                        position_type = pos["type"]
                        entry_price = pos["entry_price"]

                        # Foyda hisoblash
                        if position_type == "LONG":
                            profit_pct = ((current_price - entry_price) / entry_price) * 100
                            if current_price > pos["max_profit_price"]:
                                pos["max_profit_price"] = current_price
                            if profit_pct >= TRAILING_ACTIVATE_PCT:
                                pos["trailing_active"] = True
                                new_sl = pos["max_profit_price"] * (1 - TRAILING_DISTANCE_PCT / 100)
                                if new_sl > pos["trailing_sl"]:
                                    pos["trailing_sl"] = new_sl
                        else:
                            profit_pct = ((entry_price - current_price) / entry_price) * 100
                            if current_price < pos["max_profit_price"]:
                                pos["max_profit_price"] = current_price
                            if profit_pct >= TRAILING_ACTIVATE_PCT:
                                pos["trailing_active"] = True
                                new_sl = pos["max_profit_price"] * (1 + TRAILING_DISTANCE_PCT / 100)
                                if pos["trailing_sl"] == 0 or new_sl < pos["trailing_sl"]:
                                    pos["trailing_sl"] = new_sl

                        # Chiqish sababi
                        close_reason = ""
                        if pos["trailing_active"]:
                            if position_type == "LONG" and current_price <= pos["trailing_sl"]:
                                close_reason = "Trailing SL"
                            elif position_type == "SHORT" and current_price >= pos["trailing_sl"]:
                                close_reason = "Trailing SL"

                            if not close_reason and profit_pct <= -pos.get("sl_pct", STOP_LOSS_PCT):
                                close_reason = "Stop-Loss"
                        elif not close_reason and profit_pct >= pos.get("tp_pct", TAKE_PROFIT_PCT):
                            close_reason = "Take-Profit"
                        elif not close_reason:
                            if position_type == "LONG" and check_trend_sell(row, prev) >= 2:
                                close_reason = "Signal"
                            elif position_type == "SHORT" and check_trend_buy(row, prev) >= 2:
                                close_reason = "Signal"
                        if not close_reason and pos["strategy"] == "MeanRev":
                            if position_type == "LONG" and row["rsi"] > 50:
                                close_reason = "MR Exit"
                            elif position_type == "SHORT" and row["rsi"] < 50:
                                close_reason = "MR Exit"

                        # Pozitsiyani yopish
                        if close_reason:
                            profit_loss = current_balance * (RISK_PER_TRADE / 100) * (profit_pct / STOP_LOSS_PCT)
                            risk_manager.record_trade(profit_loss)
                            emoji = "[+]" if profit_loss >= 0 else "[-]"
                            print("  " + emoji + " " + symbol + " " + position_type + " YOPILDI (" + close_reason + ") " + str(round(profit_pct, 2)) + "% $" + str(round(profit_loss, 2)))

                            msg2 = "<b>" + symbol + " " + position_type + " YOPILDI</b>" + NL + NL
                            msg2 = msg2 + "Sabab: " + close_reason + NL
                            msg2 = msg2 + "Strategiya: " + pos["strategy"] + NL
                            msg2 = msg2 + "AI: " + str(round(pos["ai_confidence"] * 100)) + "%" + NL
                            msg2 = msg2 + "Kirish: $" + str(round(entry_price, 2)) + NL
                            msg2 = msg2 + "Chiqish: $" + str(round(current_price, 2)) + NL
                            msg2 = msg2 + "Foyda: " + str(round(profit_pct, 2)) + "% ($" + str(round(profit_loss, 2)) + ")" + NL
                            msg2 = msg2 + "Win rate: " + str(round(risk_manager.get_win_rate(), 1)) + "%"
                            send_telegram(msg2)

                            save_to_excel({"Sana": datetime.now().strftime("%Y-%m-%d %H:%M"), "Birja": EXCHANGE_NAME, "Juftlik": symbol, "Tur": position_type + " (" + close_reason + ")", "Strategiya": pos["strategy"], "AI": round(pos["ai_confidence"] * 100, 1), "Kirish": entry_price, "Chiqish": current_price, "Foyda_pct": round(profit_pct, 2), "Foyda_usd": round(profit_loss, 2), "Balans": round(current_balance + profit_loss, 2)})
                            del open_positions[symbol]

                        else:
                            trail_text = " [TRAIL]" if pos["trailing_active"] else ""
                            print("  " + symbol + " " + position_type + " " + pos["strategy"] + ": " + str(round(profit_pct, 2)) + "%" + trail_text)

                    # ===== YANGI POZITSIYA =====
                    elif bot_active:
                        if len(open_positions) >= MAX_OPEN_POSITIONS:
                            continue

                        can_trade, reason = risk_manager.can_trade()
                        if not can_trade:
                             continue
 
                        # Session filter
                        session_ok, session_msg = is_trading_session()
                        if not session_ok:
                            continue

                        # Signal olish
                        signal_type, signal_dir, strategy_name = get_signal(row, prev, trend)

                        # Portfolio balance filter
                        if signal_type is not None:
                            pf_ok, pf_msg = check_portfolio_balance(symbol, signal_type, open_positions)
                            if not pf_ok:
                                print("  [SKIP] " + symbol + " " + signal_type + " - " + pf_msg)
                                signal_type = None
                        
                        # ===== ADVANCED FEATURES =====
                        signal_strength = 1.0  # Asosiy signal kuchi
                        feature_confirmations = []
                        
                        # Feature 1: Volume Analysis
                        if signal_type is not None and VOLUME_ANALYSIS_ENABLED and volume_analyzer:
                            vol_result = volume_analyzer.analyze_volume(df, symbol)
                            if vol_result.get("signal"):
                                if vol_result["signal"] == signal_type:
                                    signal_strength += vol_result["strength"]
                                    feature_confirmations.append("Volume(" + vol_result["reason"] + ")")
                                elif vol_result["signal"] != signal_type:
                                    # Teskari signal = zaiflashtirish
                                    signal_strength -= 0.5
                                    print("  [WARN] " + symbol + " - Volume teskari: " + vol_result["reason"])
                        
                        # Feature 2: Order Book Analysis
                        if signal_type is not None and ORDERBOOK_ANALYSIS_ENABLED and orderbook_analyzer:
                            ob_result = orderbook_analyzer.analyze_orderbook(symbol)
                            if ob_result.get("signal"):
                                if ob_result["signal"] == signal_type:
                                    signal_strength += ob_result["strength"]
                                    feature_confirmations.append("OrderBook(" + ob_result["reason"] + ")")
                                elif ob_result["signal"] != signal_type:
                                    signal_strength -= 0.5
                                    print("  [WARN] " + symbol + " - OrderBook teskari: " + ob_result["reason"])
                        
                        # Feature 4: Sentiment Analysis (Global market sentiment)
                        if signal_type is not None and SENTIMENT_ANALYSIS_ENABLED and sentiment_analyzer:
                            sent_result = sentiment_analyzer.analyze_sentiment()
                            if sent_result.get("signal"):
                                if sent_result["signal"] == signal_type:
                                    signal_strength += sent_result["strength"]
                                    feature_confirmations.append("Sentiment(" + sent_result["reason"] + ")")
                                elif sent_result["signal"] != signal_type:
                                    # Sentiment teskari = warning faqat
                                    print("  [WARN] " + symbol + " - Sentiment teskari: " + sent_result["reason"])
                        
                        # Feature 5: ML Ensemble
                        if signal_type is not None and ML_ENSEMBLE_ENABLED and ml_ensemble:
                            ens_result = ml_ensemble.predict_ensemble(df)
                            if ens_result.get("signal"):
                                if ens_result["signal"] == signal_type:
                                    signal_strength += ens_result["confidence"] * 3
                                    feature_confirmations.append("Ensemble(" + str(round(ens_result["confidence"]*100)) + "%)")
                                elif ens_result["signal"] != signal_type:
                                    # Ensemble teskari = bekor qilish
                                    print("  [SKIP] " + symbol + " " + signal_type + " - Ensemble teskari")
                                    signal_type = None
                        
                        # Signal strength check (minimum 1.0 kerak)
                        if signal_type is not None and signal_strength < 1.0:
                            print("  [SKIP] " + symbol + " " + signal_type + " - Signal zaif (" + str(round(signal_strength, 2)) + " < 1.0)")
                            signal_type = None

                        # AI filtr
                        ai_confidence = 1.0
                        ai_text_msg = "AI o'chiq"
                        if signal_type is not None and AI_ENABLED and ai_loaded:
                            ai_confidence, ai_text_msg = ai_predict(df)
                            if ai_confidence < AI_MIN_CONFIDENCE:
                                print("  [SKIP] " + symbol + " " + signal_type + " - " + ai_text_msg + " (min " + str(int(AI_MIN_CONFIDENCE * 100)) + "% kerak)")
                                signal_type = None
 
                        # Correlation filtr (BTC)
                        if signal_type is not None:
                            from bot.exchange import exchange as exc
                            corr_ok, corr_msg = check_correlation_filter(symbol, signal_type, exc)
                            if not corr_ok:
                                print("  [SKIP] " + symbol + " " + signal_type + " - " + corr_msg)
                                signal_type = None
 
                        # Sentiment filtr (Fear & Greed)
                        if signal_type is not None:
                            sent_ok, sent_msg = check_sentiment_filter(signal_type)
                            if not sent_ok:
                                print("  [SKIP] " + symbol + " " + signal_type + " - " + sent_msg)
                                signal_type = None

                        # Pozitsiya ochish
                        if signal_type == "LONG":
                            # Dynamic SL/TP hisoblash
                            sl_pct, tp_pct = calculate_dynamic_sltp(row)
                            open_positions[symbol] = {"type": "LONG", "entry_price": current_price, "max_profit_price": current_price, "trailing_sl": 0, "trailing_active": False, "strategy": strategy_name, "ai_confidence": ai_confidence, "sl_pct": sl_pct, "tp_pct": tp_pct, "signal_strength": signal_strength}
                            
                            features_text = " | " + ", ".join(feature_confirmations) if feature_confirmations else ""
                            print("  [BUY] " + symbol + " LONG @ $" + str(round(current_price, 2)) + " | " + strategy_name + " | " + ai_text_msg + " | SL:" + str(sl_pct) + "% TP:" + str(tp_pct) + "%" + features_text)

                            msg3 = "<b>" + symbol + " LONG OCHILDI</b>" + NL + NL
                            msg3 = msg3 + "Birja: " + get_exchange_name() + NL
                            msg3 = msg3 + "Strategiya: " + strategy_name + NL
                            msg3 = msg3 + "Signal kuchi: " + str(round(signal_strength, 2)) + NL
                            msg3 = msg3 + "AI: " + str(round(ai_confidence * 100)) + "%" + NL
                            if feature_confirmations:
                                msg3 = msg3 + "Tasdiqlar: " + ", ".join(feature_confirmations) + NL
                            msg3 = msg3 + "Narx: $" + str(round(current_price, 2)) + NL
                            msg3 = msg3 + "SL: $" + str(round(current_price * (1 - sl_pct / 100), 2)) + " (" + str(sl_pct) + "%)" + NL
                            msg3 = msg3 + "TP: $" + str(round(current_price * (1 + tp_pct / 100), 2)) + " (" + str(tp_pct) + "%)"
                            send_telegram(msg3)
                            send_telegram_chart(symbol, df, entry_price=current_price, sl_price=current_price * (1 - sl_pct / 100), tp_price=current_price * (1 + tp_pct / 100))

                            save_to_excel({"Sana": datetime.now().strftime("%Y-%m-%d %H:%M"), "Birja": EXCHANGE_NAME, "Juftlik": symbol, "Tur": "LONG BUY", "Strategiya": strategy_name, "AI": round(ai_confidence * 100, 1), "Kirish": current_price, "Chiqish": "-", "Foyda_pct": 0, "Foyda_usd": 0, "Balans": current_balance})

                        elif signal_type == "SHORT":
                            sl_pct, tp_pct = calculate_dynamic_sltp(row)
                            open_positions[symbol] = {"type": "SHORT", "entry_price": current_price, "max_profit_price": current_price, "trailing_sl": 0, "trailing_active": False, "strategy": strategy_name, "ai_confidence": ai_confidence, "sl_pct": sl_pct, "tp_pct": tp_pct, "signal_strength": signal_strength}
                            
                            features_text = " | " + ", ".join(feature_confirmations) if feature_confirmations else ""
                            print("  [SELL] " + symbol + " SHORT @ $" + str(round(current_price, 2)) + " | " + strategy_name + " | " + ai_text_msg + " | SL:" + str(sl_pct) + "% TP:" + str(tp_pct) + "%" + features_text)

                            msg4 = "<b>" + symbol + " SHORT OCHILDI</b>" + NL + NL
                            msg4 = msg4 + "Birja: " + get_exchange_name() + NL
                            msg4 = msg4 + "Strategiya: " + strategy_name + NL
                            msg4 = msg4 + "Signal kuchi: " + str(round(signal_strength, 2)) + NL
                            msg4 = msg4 + "AI: " + str(round(ai_confidence * 100)) + "%" + NL
                            if feature_confirmations:
                                msg4 = msg4 + "Tasdiqlar: " + ", ".join(feature_confirmations) + NL
                            msg4 = msg4 + "Narx: $" + str(round(current_price, 2)) + NL
                            msg4 = msg4 + "SL: $" + str(round(current_price * (1 + sl_pct / 100), 2)) + " (" + str(sl_pct) + "%)" + NL
                            msg4 = msg4 + "TP: $" + str(round(current_price * (1 - tp_pct / 100), 2)) + " (" + str(tp_pct) + "%)"
                            send_telegram(msg4)
                            send_telegram_chart(symbol, df, entry_price=current_price, sl_price=current_price * (1 + sl_pct / 100), tp_price=current_price * (1 - tp_pct / 100))

                            save_to_excel({"Sana": datetime.now().strftime("%Y-%m-%d %H:%M"), "Birja": EXCHANGE_NAME, "Juftlik": symbol, "Tur": "SHORT SELL", "Strategiya": strategy_name, "AI": round(ai_confidence * 100, 1), "Kirish": current_price, "Chiqish": "-", "Foyda_pct": 0, "Foyda_usd": 0, "Balans": current_balance})

                except Exception as e:
                    print("  " + symbol + " xato: " + str(e))

            time.sleep(30)

        except KeyboardInterrupt:
            stats = risk_manager.get_stats()
            print("")
            print("=" * 60)
            print("  BOT TO'XTATILDI")
            print("  Jami: " + str(stats["total"]) + " | Win: " + str(stats["wins"]) + " | Loss: " + str(stats["losses"]))
            print("  Win rate: " + str(round(stats["win_rate"], 1)) + "%")
            print("  Balans: $" + str(round(get_balance(), 2)))
            print("=" * 60)

            msg5 = "<b>Bot to'xtatildi</b>" + NL + NL
            msg5 = msg5 + "Jami: " + str(stats["total"]) + " savdo" + NL
            msg5 = msg5 + "Win rate: " + str(round(stats["win_rate"], 1)) + "%" + NL
            msg5 = msg5 + "Balans: $" + str(round(get_balance(), 2))
            send_telegram(msg5)
            break

        except Exception as e:
            print("  XATO: " + str(e))
            send_telegram("XATO: " + str(e))
            time.sleep(30)


if __name__ == "__main__":
    run_bot()