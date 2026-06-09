import sys
import os
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_keys import TELEGRAM_TOKEN

NL = chr(10)


class SignalChannel:
    """Telegram Signal Kanal - boshqalarga signal yuborish va pul ishlash
    
    Qanday ishlaydi:
    1. Bot signal topadi (AI tasdiqlagan)
    2. Sizning shaxsiy chatga xabar keladi (hozirgiday)
    3. Ochiq kanalga ham signal yuboriladi (obunachilarga)
    4. Obunachi oylik to'lov qiladi
    """

    def __init__(self, channel_id, bot_token=None):
        self.channel_id = channel_id
        self.bot_token = bot_token or TELEGRAM_TOKEN
        self.signals_sent = 0
        self.wins = 0
        self.losses = 0

    def send_to_channel(self, message):
        """Kanalga xabar yuborish"""
        try:
            url = "https://api.telegram.org/bot" + self.bot_token + "/sendMessage"
            data = {
                "chat_id": self.channel_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                self.signals_sent = self.signals_sent + 1
                return True
            return False
        except Exception as e:
            print("  Kanal xato: " + str(e))
            return False

    def send_signal(self, symbol, signal_type, strategy, ai_confidence, entry_price, sl_price, tp_price, sl_pct, tp_pct):
        """Signal yuborish (professional format)"""
        
        msg = "=============================" + NL
        msg = msg + "SIGNAL: " + symbol + " " + signal_type + NL
        msg = msg + "=============================" + NL + NL
        msg = msg + "Strategiya: " + strategy + NL
        msg = msg + "AI ishonch: " + str(round(ai_confidence * 100)) + "%" + NL + NL
        msg = msg + "Entry: $" + str(round(entry_price, 4)) + NL
        msg = msg + "Stop-Loss: $" + str(round(sl_price, 4)) + " (-" + str(sl_pct) + "%)" + NL
        msg = msg + "Take-Profit: $" + str(round(tp_price, 4)) + " (+" + str(tp_pct) + "%)" + NL + NL
        msg = msg + "Risk/Reward: 1:" + str(round(tp_pct / sl_pct, 1)) + NL
        msg = msg + "Vaqt: " + datetime.now().strftime("%Y-%m-%d %H:%M UTC") + NL + NL
        msg = msg + "=============================" + NL
        msg = msg + "Sardor Trading Signals" + NL
        msg = msg + "Win rate: " + str(round(self.get_win_rate(), 1)) + "%" + NL
        msg = msg + "============================="

        return self.send_to_channel(msg)

    def send_result(self, symbol, signal_type, entry_price, close_price, profit_pct, profit_usd, reason):
        """Signal natijasini yuborish"""
        
        result_text = "FOYDA" if profit_pct > 0 else "ZARAR"
        
        msg = "=============================" + NL
        msg = msg + "NATIJA: " + symbol + " " + result_text + NL
        msg = msg + "=============================" + NL + NL
        msg = msg + "Tur: " + signal_type + NL
        msg = msg + "Sabab: " + reason + NL
        msg = msg + "Kirish: $" + str(round(entry_price, 4)) + NL
        msg = msg + "Chiqish: $" + str(round(close_price, 4)) + NL
        msg = msg + "Natija: " + str(round(profit_pct, 2)) + "% ($" + str(round(profit_usd, 2)) + ")" + NL + NL

        if profit_pct > 0:
            self.wins = self.wins + 1
        else:
            self.losses = self.losses + 1

        msg = msg + "Umumiy: " + str(self.wins) + "W / " + str(self.losses) + "L" + NL
        msg = msg + "Win rate: " + str(round(self.get_win_rate(), 1)) + "%" + NL
        msg = msg + "=============================" + NL
        msg = msg + "Sardor Trading Signals"

        return self.send_to_channel(msg)

    def send_daily_report(self, balance, total_trades, win_rate, daily_profit):
        """Kunlik hisobot"""
        
        msg = "=============================" + NL
        msg = msg + "KUNLIK HISOBOT" + NL
        msg = msg + "=============================" + NL + NL
        msg = msg + "Sana: " + datetime.now().strftime("%Y-%m-%d") + NL
        msg = msg + "Bugungi savdolar: " + str(total_trades) + NL
        msg = msg + "Win rate: " + str(round(win_rate, 1)) + "%" + NL
        msg = msg + "Bugungi foyda: $" + str(round(daily_profit, 2)) + NL + NL
        msg = msg + "=============================" + NL
        msg = msg + "Sardor Trading Signals" + NL
        msg = msg + "Obuna: @sardor_trading_signals"

        return self.send_to_channel(msg)

    def get_win_rate(self):
        total = self.wins + self.losses
        if total == 0:
            return 0
        return (self.wins / total) * 100

    def get_stats(self):
        return {
            "signals_sent": self.signals_sent,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": self.get_win_rate()
        }
