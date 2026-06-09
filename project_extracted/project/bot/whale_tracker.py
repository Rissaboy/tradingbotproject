import sys
import os
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class WhaleTracker:
    """On-Chain Whale Tracking - katta hamyonlarning harakatini kuzatish

    Qanday ishlaydi:
    1. Katta tranzaksiyalarni kuzatish (whale alert)
    2. Birjaga pul o'tkazish = SOTISH niyati (BEARISH)
    3. Birjadan pul chiqarish = SAQLASH niyati (BULLISH)
    4. Katta miqdor harakati = narx o'zgarishi kutilmoqda

    Manbalar:
    - Blockchain.com API (bepul)
    - Whale Alert API (bepul trial)
    - Binance katta orderlarni kuzatish
    """

    def __init__(self):
        self.whale_alerts = []
        self.bullish_signals = 0
        self.bearish_signals = 0

    def get_btc_large_transactions(self):
        """BTC da katta tranzaksiyalarni tekshirish (blockchain.com)"""
        try:
            # Blockchain.com API - oxirgi katta tranzaksiyalar
            url = "https://blockchain.info/unconfirmed-transactions?format=json"
            response = requests.get(url, timeout=15)

            if response.status_code != 200:
                return []

            data = response.json()
            large_txs = []

            for tx in data.get("txs", [])[:50]:
                total_output = 0
                for output in tx.get("out", []):
                    total_output = total_output + output.get("value", 0)

                # BTC value (satoshi -> BTC)
                btc_amount = total_output / 100000000

                # Faqat 10+ BTC tranzaksiyalar (whale)
                if btc_amount >= 10:
                    large_txs.append({
                        "hash": tx.get("hash", "")[:16],
                        "btc_amount": round(btc_amount, 2),
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "inputs": len(tx.get("inputs", [])),
                        "outputs": len(tx.get("out", []))
                    })

            return large_txs[:10]

        except Exception as e:
            return []

    def get_exchange_flows(self):
        """Birjalarga pul oqimini tekshirish (CryptoQuant alternative)"""
        try:
            # Binance order book dan katta orderlarni tekshirish
            url = "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=20"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return None

            data = response.json()

            # Katta BUY orderlar (bids)
            total_bid_volume = 0
            large_bids = 0
            for bid in data.get("bids", []):
                qty = float(bid[1])
                total_bid_volume = total_bid_volume + qty
                if qty >= 1.0:  # 1+ BTC order
                    large_bids = large_bids + 1

            # Katta SELL orderlar (asks)
            total_ask_volume = 0
            large_asks = 0
            for ask in data.get("asks", []):
                qty = float(ask[1])
                total_ask_volume = total_ask_volume + qty
                if qty >= 1.0:  # 1+ BTC order
                    large_asks = large_asks + 1

            # Buy/Sell ratio
            if total_ask_volume > 0:
                ratio = total_bid_volume / total_ask_volume
            else:
                ratio = 1.0

            return {
                "bid_volume": round(total_bid_volume, 2),
                "ask_volume": round(total_ask_volume, 2),
                "ratio": round(ratio, 2),
                "large_bids": large_bids,
                "large_asks": large_asks,
                "signal": "BULLISH" if ratio > 1.2 else ("BEARISH" if ratio < 0.8 else "NEUTRAL")
            }

        except Exception as e:
            return None

    def get_whale_signal(self):
        """Umumiy whale signal olish"""
        # 1. Exchange flow
        flow = self.get_exchange_flows()

        if flow is None:
            return "NEUTRAL", "Whale data olinmadi", {}

        signal = flow["signal"]
        ratio = flow["ratio"]

        details = {
            "bid_volume": flow["bid_volume"],
            "ask_volume": flow["ask_volume"],
            "ratio": ratio,
            "large_bids": flow["large_bids"],
            "large_asks": flow["large_asks"]
        }

        if signal == "BULLISH":
            self.bullish_signals = self.bullish_signals + 1
            msg = "Whale BULLISH: BUY hajm " + str(ratio) + "x katta (kitlar olmoqda)"
        elif signal == "BEARISH":
            self.bearish_signals = self.bearish_signals + 1
            msg = "Whale BEARISH: SELL hajm kuchli (kitlar sotmoqda)"
        else:
            msg = "Whale NEUTRAL: balans (ratio: " + str(ratio) + ")"

        return signal, msg, details

    def check_whale_filter(self, signal_type):
        """Whale ma'lumotiga qarab savdo filtrlash"""
        whale_signal, whale_msg, details = self.get_whale_signal()

        # Agar kitlar SOTAYOTGAN bo'lsa - LONG xavfli
        if whale_signal == "BEARISH" and signal_type == "LONG":
            return False, "Whale: " + whale_msg

        # Agar kitlar OLAYOTGAN bo'lsa - SHORT xavfli
        if whale_signal == "BULLISH" and signal_type == "SHORT":
            return False, "Whale: " + whale_msg

        return True, "Whale: " + whale_msg

    def get_stats(self):
        """Statistika"""
        return {
            "bullish_signals": self.bullish_signals,
            "bearish_signals": self.bearish_signals,
            "total_alerts": len(self.whale_alerts)
        }


def print_whale_report():
    """Whale hisobot chiqarish"""
    tracker = WhaleTracker()

    print("")
    print("=" * 60)
    print("  WHALE TRACKER HISOBOT")
    print("  Vaqt: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 60)
    print("")

    # Exchange flow
    print("  BIRJA OQIMI (Order Book):")
    print("  " + "-" * 40)
    flow = tracker.get_exchange_flows()
    if flow:
        print("  BUY hajm: " + str(flow["bid_volume"]) + " BTC")
        print("  SELL hajm: " + str(flow["ask_volume"]) + " BTC")
        print("  Ratio: " + str(flow["ratio"]) + "x")
        print("  Katta BUY orderlar: " + str(flow["large_bids"]))
        print("  Katta SELL orderlar: " + str(flow["large_asks"]))
        print("  Signal: " + flow["signal"])
    else:
        print("  Ma'lumot olinmadi")
    print("  " + "-" * 40)

    # Katta tranzaksiyalar
    print("")
    print("  KATTA BTC TRANZAKSIYALAR (10+ BTC):")
    print("  " + "-" * 40)
    large_txs = tracker.get_btc_large_transactions()
    if large_txs:
        for tx in large_txs[:5]:
            print("  " + tx["hash"] + "... | " + str(tx["btc_amount"]) + " BTC | " + tx["time"])
    else:
        print("  Hozircha katta tranzaksiya yo'q")
    print("  " + "-" * 40)

    # Umumiy signal
    print("")
    signal, msg, details = tracker.get_whale_signal()
    print("  UMUMIY WHALE SIGNAL: " + signal)
    print("  " + msg)
    print("")
    print("=" * 60)


if __name__ == "__main__":
    print_whale_report()
