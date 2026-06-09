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
    SCANNER_FILE, DEFAULT_SYMBOLS, EXCEL_FILE
)

# Auto retraining
AUTO_RETRAIN_ENABLED = True
RETRAIN_INTERVAL_DAYS = 7
last_retrain_date = None
from bot.exchange import get_balance, get_klines, get_exchange_name, exchange as exc
from bot.indicators import calculate_indicators, get_trend
from bot.strategies import get_signal, check_trend_buy, check_trend_sell, calculate_dynamic_sltp, is_trading_session, check_portfolio_balance, check_multi_timeframe, check_correlation_filter, check_sentiment_filter
from bot.risk_manager import RiskManager
from bot.telegram_bot import send_telegram, check_telegram_commands, send_telegram_chart
from ai.predictor import load_ai_model, ai_predict
from bot.regime_detector import RegimeDetector
from bot.whale_tracker import WhaleTracker
from bot.grid_trading import GridBot
from bot.dca_trading import DCABot
from bot.signal_channel import SignalChannel
from config.settings import GRID_TRADING_ENABLED, GRID_SYMBOLS, DCA_ENABLED, SIGNAL_CHANNEL_ENABLED, SIGNAL_CHANNEL_ID

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


def run_bot():
    global open_positions

    bot_active = True

    # Juftliklarni yuklash
    symbols = load_symbols()

    # AI model yuklash
    ai_loaded = False
    if AI_ENABLED:
        ai_loaded = load_ai_model()

    # Balans
    balance = get_balance()
    risk_manager = RiskManager(balance)

    # Yangi modullarni ishga tushirish
    regime_detector = RegimeDetector()
    whale_tracker = WhaleTracker()
    grid_bots = {}
    dca_positions = {}
    signal_channel = None

    if SIGNAL_CHANNEL_ENABLED:
        signal_channel = SignalChannel(SIGNAL_CHANNEL_ID)
        print("  Signal kanal ulandi: " + SIGNAL_CHANNEL_ID)

    if GRID_TRADING_ENABLED:
        print("  Grid Trading: YOQILGAN (" + str(len(GRID_SYMBOLS)) + " coin)")

    if DCA_ENABLED:
        print("  DCA: YOQILGAN")

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
            if risk_manager.new_day_check(current_balance):
                send_telegram("Yangi kun boshlandi! Balans: $" + str(round(current_balance, 2)))

            # Status
            status_text = "YOQILGAN" if bot_active else "TO'XTATILGAN"
            ai_text = " | AI" if ai_loaded else ""
            session_ok, session_msg = is_trading_session()
            session_text = " | " + session_msg

            # Regime Detection
            sample_df = get_klines("BTC/USDT")
            sample_df = calculate_indicators(sample_df)
            sample_df = sample_df.dropna().reset_index(drop=True)
            current_regime = "UNKNOWN"
            if len(sample_df) > 50:
                current_regime, regime_details = regime_detector.detect_regime(sample_df)

            print("")
            print("[" + datetime.now().strftime("%H:%M:%S") + "] " + get_exchange_name() + ai_text + " | " + current_regime + session_text + " | $" + str(round(current_balance, 2)) + " | Ochiq: " + str(len(open_positions)) + "/" + str(MAX_OPEN_POSITIONS) + " | " + status_text)

            # Grid Trading tekshirish
            if GRID_TRADING_ENABLED and regime_detector.should_use_grid(current_regime):
                for grid_symbol in GRID_SYMBOLS:
                    try:
                        grid_df = get_klines(grid_symbol)
                        grid_price = float(grid_df["close"].iloc[-1])

                        if grid_symbol not in grid_bots:
                            grid_bots[grid_symbol] = GridBot(grid_symbol, grid_price, current_balance)

                        grid_bot = grid_bots[grid_symbol]

                        if grid_bot.should_reset_grid(grid_price):
                            grid_bot.reset_grid(grid_price)

                        grid_signals = grid_bot.check_grid(grid_price)
                        for gs in grid_signals:
                            if gs["action"] == "GRID_TP":
                                print("  [GRID_TP] " + grid_symbol + " +" + str(gs["profit_pct"]) + "% (+$" + str(gs["profit_usd"]) + ")")
                            elif gs["action"] in ["GRID_BUY", "GRID_SELL"]:
                                print("  [GRID] " + grid_symbol + " " + gs["action"] + " @ $" + str(round(gs["price"], 2)) + " Level:" + str(gs["level"]))
                    except Exception as e:
                        pass

            # DCA tekshirish
            if DCA_ENABLED:
                for dca_sym in list(dca_positions.keys()):
                    try:
                        dca_df = get_klines(dca_sym)
                        dca_price = float(dca_df["close"].iloc[-1])
                        dca_bot = dca_positions[dca_sym]
                        dca_signals = dca_bot.check_dca(dca_price)
                        for ds in dca_signals:
                            if ds["action"] == "DCA_BUY":
                                print("  [DCA #" + str(ds["order_num"]) + "] " + dca_sym + " BUY @ $" + str(round(ds["price"], 2)) + " | Avg: $" + str(ds["avg_price"]))
                            elif ds["action"] == "DCA_CLOSE":
                                print("  [DCA CLOSE] " + dca_sym + " +" + str(ds["profit_pct"]) + "% (+$" + str(ds["profit_usd"]) + ") | " + str(ds["orders_count"]) + " orders")
                                del dca_positions[dca_sym]
                    except:
                        pass

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
                        signal_type, signal_dir, strategy_name = get_signal(row, prev, trend, df)

                        # Portfolio balance filter
                        if signal_type is not None:
                            pf_ok, pf_msg = check_portfolio_balance(symbol, signal_type, open_positions)
                            if not pf_ok:
                                print("  [SKIP] " + symbol + " " + signal_type + " - " + pf_msg)
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

                        # Whale Tracker filtr
                        if signal_type is not None:
                            whale_ok, whale_msg = whale_tracker.check_whale_filter(signal_type)
                            if not whale_ok:
                                print("  [SKIP] " + symbol + " " + signal_type + " - " + whale_msg)
                                signal_type = None

                        # Regime Detection filtr
                        if signal_type is not None:
                            regime_ok, regime_msg = regime_detector.should_trade(current_regime, strategy_name)
                            if not regime_ok:
                                print("  [SKIP] " + symbol + " " + signal_type + " - " + regime_msg)
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
                            open_positions[symbol] = {"type": "LONG", "entry_price": current_price, "max_profit_price": current_price, "trailing_sl": 0, "trailing_active": False, "strategy": strategy_name, "ai_confidence": ai_confidence, "sl_pct": sl_pct, "tp_pct": tp_pct}
                            print("  [BUY] " + symbol + " LONG @ $" + str(round(current_price, 2)) + " | " + strategy_name + " | " + ai_text_msg + " | SL:" + str(sl_pct) + "% TP:" + str(tp_pct) + "%")

                            # DCA yoqish
                            if DCA_ENABLED and regime_detector.should_use_dca(current_regime):
                                dca_size = current_balance * (RISK_PER_TRADE / 100)
                                dca_positions[symbol] = DCABot(symbol, current_price, dca_size, strategy_name, ai_confidence)

                            # Signal kanalga yuborish
                            if signal_channel:
                                signal_channel.send_signal(symbol, "LONG", strategy_name, ai_confidence, current_price, current_price * (1 - sl_pct / 100), current_price * (1 + tp_pct / 100), sl_pct, tp_pct)

                            msg3 = "<b>" + symbol + " LONG OCHILDI</b>" + NL + NL
                            msg3 = msg3 + "Birja: " + get_exchange_name() + NL
                            msg3 = msg3 + "Strategiya: " + strategy_name + NL
                            msg3 = msg3 + "AI: " + str(round(ai_confidence * 100)) + "%" + NL
                            msg3 = msg3 + "Narx: $" + str(round(current_price, 2)) + NL
                            msg3 = msg3 + "SL: $" + str(round(current_price * (1 - sl_pct / 100), 2)) + " (" + str(sl_pct) + "%)" + NL
                            msg3 = msg3 + "TP: $" + str(round(current_price * (1 + tp_pct / 100), 2)) + " (" + str(tp_pct) + "%)"
                            send_telegram(msg3)
                            send_telegram_chart(symbol, df, entry_price=current_price, sl_price=current_price * (1 - sl_pct / 100), tp_price=current_price * (1 + tp_pct / 100))

                            save_to_excel({"Sana": datetime.now().strftime("%Y-%m-%d %H:%M"), "Birja": EXCHANGE_NAME, "Juftlik": symbol, "Tur": "LONG BUY", "Strategiya": strategy_name, "AI": round(ai_confidence * 100, 1), "Kirish": current_price, "Chiqish": "-", "Foyda_pct": 0, "Foyda_usd": 0, "Balans": current_balance})

                        elif signal_type == "SHORT":
                            sl_pct, tp_pct = calculate_dynamic_sltp(row)
                            open_positions[symbol] = {"type": "SHORT", "entry_price": current_price, "max_profit_price": current_price, "trailing_sl": 0, "trailing_active": False, "strategy": strategy_name, "ai_confidence": ai_confidence, "sl_pct": sl_pct, "tp_pct": tp_pct}
                            print("  [SELL] " + symbol + " SHORT @ $" + str(round(current_price, 2)) + " | " + strategy_name + " | " + ai_text_msg + " | SL:" + str(sl_pct) + "% TP:" + str(tp_pct) + "%")

                            # Signal kanalga yuborish
                            if signal_channel:
                                signal_channel.send_signal(symbol, "SHORT", strategy_name, ai_confidence, current_price, current_price * (1 + sl_pct / 100), current_price * (1 - tp_pct / 100), sl_pct, tp_pct)

                            msg4 = "<b>" + symbol + " SHORT OCHILDI</b>" + NL + NL
                            msg4 = msg4 + "Birja: " + get_exchange_name() + NL
                            msg4 = msg4 + "Strategiya: " + strategy_name + NL
                            msg4 = msg4 + "AI: " + str(round(ai_confidence * 100)) + "%" + NL
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