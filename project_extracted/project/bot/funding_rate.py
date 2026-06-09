import sys
import os
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FundingRateBot:
    """Funding Rate Arbitraj - futures funding rate dan bepul foyda olish

    Qanday ishlaydi:
    - Futures bozorda har 8 soatda "funding" to'lanadi
    - Agar funding rate MUSBAT (+0.05%):
        LONG lar SHORT larga pul to'laydi
        -> Biz SHORT ochamiz = funding olamiz!
    - Agar funding rate MANFIY (-0.03%):
        SHORT lar LONG larga pul to'laydi
        -> Biz LONG ochamiz = funding olamiz!

    Kuniga 3 marta (har 8 soat) = yiliga 100%+ foyda mumkin!
    """

    def __init__(self):
        self.active_positions = {}
        self.total_funding_earned = 0
        self.funding_count = 0

    def get_funding_rates(self, exchange):
        """Barcha coinlar uchun funding rate olish"""
        try:
            # CCXT orqali futures funding rate olish
            markets = exchange.load_markets()
            funding_rates = {}

            # Binance futures ticker orqali
            url = "https://fapi.binance.com/fapi/v1/premiumIndex"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                for item in data:
                    symbol = item.get("symbol", "")
                    rate = float(item.get("lastFundingRate", 0))
                    next_time = int(item.get("nextFundingTime", 0))
                    if symbol.endswith("USDT"):
                        # CCXT formatga o'tkazish
                        formatted = symbol[:-4] + "/USDT"
                        funding_rates[formatted] = {
                            "rate": rate,
                            "rate_pct": round(rate * 100, 4),
                            "next_funding_time": next_time,
                            "annual_pct": round(rate * 100 * 3 * 365, 2)
                        }

            return funding_rates

        except Exception as e:
            print("  Funding rate xato: " + str(e))
            return {}

    def find_opportunities(self, funding_rates, min_rate=0.01):
        """Foydali funding rate imkoniyatlarni topish

        min_rate = 0.01% (har 8 soatda) = kuniga 0.03% = yiliga ~11%
        Yuqori ratelar = ko'proq foyda
        """
        opportunities = []

        for symbol, data in funding_rates.items():
            rate_pct = data["rate_pct"]
            annual = data["annual_pct"]

            # Musbat rate: SHORT ochib funding olish
            if rate_pct >= min_rate:
                opportunities.append({
                    "symbol": symbol,
                    "action": "SHORT",
                    "rate_pct": rate_pct,
                    "annual_pct": annual,
                    "reason": "Funding musbat: LONG lar to'laydi -> SHORT ochib olamiz"
                })

            # Manfiy rate: LONG ochib funding olish
            elif rate_pct <= -min_rate:
                opportunities.append({
                    "symbol": symbol,
                    "action": "LONG",
                    "rate_pct": abs(rate_pct),
                    "annual_pct": abs(annual),
                    "reason": "Funding manfiy: SHORT lar to'laydi -> LONG ochib olamiz"
                })

        # Eng yuqori rate bo'yicha tartiblash
        opportunities.sort(key=lambda x: x["rate_pct"], reverse=True)
        return opportunities

    def get_top_funding(self, exchange, top_n=10):
        """Eng yuqori funding rate li coinlarni topish"""
        rates = self.get_funding_rates(exchange)
        if not rates:
            return []

        opportunities = self.find_opportunities(rates)
        return opportunities[:top_n]

    def calculate_potential_profit(self, balance, rate_pct, leverage=1):
        """Potensial foyda hisoblash"""
        # Har 8 soatda
        per_8h = balance * (rate_pct / 100) * leverage
        # Kuniga (3 marta)
        daily = per_8h * 3
        # Oyiga
        monthly = daily * 30
        # Yiliga
        yearly = daily * 365

        return {
            "per_8h": round(per_8h, 2),
            "daily": round(daily, 2),
            "monthly": round(monthly, 2),
            "yearly": round(yearly, 2)
        }

    def record_funding(self, amount):
        """Funding to'lovini qayd qilish"""
        self.total_funding_earned = self.total_funding_earned + amount
        self.funding_count = self.funding_count + 1

    def get_stats(self):
        """Statistika"""
        return {
            "total_earned": round(self.total_funding_earned, 4),
            "count": self.funding_count,
            "active_positions": len(self.active_positions)
        }


def print_funding_report(exchange):
    """Funding rate hisobot chiqarish"""
    bot = FundingRateBot()
    opportunities = bot.get_top_funding(exchange, top_n=15)

    if not opportunities:
        print("  Funding rate ma'lumot olinmadi")
        return

    print("")
    print("=" * 60)
    print("  FUNDING RATE IMKONIYATLAR")
    print("  Vaqt: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 60)
    print("")
    print("  #   Symbol          Action  Rate     Annual")
    print("  " + "-" * 55)

    for i, opp in enumerate(opportunities):
        num = str(i + 1)
        if len(num) < 2:
            num = " " + num
        sym = opp["symbol"]
        if len(sym) < 14:
            sym = sym + " " * (14 - len(sym))
        print("  " + num + ". " + sym + " " + opp["action"] + "    " + str(opp["rate_pct"]) + "%    " + str(opp["annual_pct"]) + "%/yil")

    print("  " + "-" * 55)

    # Foyda hisoblash ($1000 balans bilan)
    if opportunities:
        top = opportunities[0]
        profit = bot.calculate_potential_profit(1000, top["rate_pct"])
        print("")
        print("  TOP signal: " + top["symbol"] + " " + top["action"])
        print("  $1000 bilan foyda:")
        print("    Har 8 soat: $" + str(profit["per_8h"]))
        print("    Kuniga: $" + str(profit["daily"]))
        print("    Oyiga: $" + str(profit["monthly"]))
        print("    Yiliga: $" + str(profit["yearly"]))
    print("")
    print("=" * 60)


if __name__ == "__main__":
    import ccxt
    exchange = ccxt.binance({"enableRateLimit": True})
    print_funding_report(exchange)
