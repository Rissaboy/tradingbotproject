import sys
import os
import requests
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NL = chr(10)


class FundingArbitrage:
    """Delta-Neutral Funding Rate Arbitrage - eng xavfsiz kripto strategiya!

    Spot BUY + Futures SHORT = narx ta'siri 0
    Faqat funding rate = sof foyda!
    Yillik 15-40% (bozorga qarab)
    """

    def __init__(self, exchange, telegram_func=None):
        self.exchange = exchange
        self.send_telegram = telegram_func
        self.active_positions = {}
        self.total_funding_earned = 0
        self.total_trades = 0

    def get_current_funding_rate(self, symbol="BTC/USDT"):
        try:
            binance_symbol = symbol.replace("/", "")
            url = "https://fapi.binance.com/fapi/v1/premiumIndex?symbol=" + binance_symbol
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                rate = float(data.get("lastFundingRate", 0))
                mark_price = float(data.get("markPrice", 0))
                return {
                    "symbol": symbol,
                    "rate": rate,
                    "rate_pct": round(rate * 100, 4),
                    "mark_price": mark_price,
                    "annual_pct": round(rate * 100 * 3 * 365, 2)
                }
            return None
        except:
            return None

    def get_best_opportunities(self, symbols=None, min_rate=0.01):
        if symbols is None:
            symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT", "ADA/USDT", "AVAX/USDT", "LINK/USDT", "BNB/USDT", "DOT/USDT"]
        opportunities = []
        for symbol in symbols:
            data = self.get_current_funding_rate(symbol)
            if data and abs(data["rate_pct"]) >= min_rate:
                data["action"] = "SHORT" if data["rate_pct"] > 0 else "LONG"
                data["safe_annual"] = round(abs(data["rate_pct"]) * 3 * 365 * 0.7, 2)
                opportunities.append(data)
            time.sleep(0.2)
        opportunities.sort(key=lambda x: abs(x["rate_pct"]), reverse=True)
        return opportunities

    def calculate_position(self, balance, rate_pct, allocation_pct=50):
        allocated = balance * (allocation_pct / 100)
        spot_size = allocated / 2
        futures_size = allocated / 2
        funding_per_8h = futures_size * (rate_pct / 100)
        funding_daily = funding_per_8h * 3
        funding_monthly = funding_daily * 30
        funding_yearly = funding_daily * 365
        spot_fee = spot_size * 0.001
        futures_fee = futures_size * 0.0004
        total_fees = (spot_fee + futures_fee) * 2
        net_daily = funding_daily - (total_fees / 30)
        net_monthly = funding_monthly - total_fees
        net_yearly = funding_yearly - (total_fees * 12)
        return {
            "allocated": round(allocated, 2),
            "spot_size": round(spot_size, 2),
            "futures_size": round(futures_size, 2),
            "funding_per_8h": round(funding_per_8h, 4),
            "funding_daily": round(funding_daily, 4),
            "funding_monthly": round(funding_monthly, 2),
            "funding_yearly": round(funding_yearly, 2),
            "total_fees": round(total_fees, 4),
            "net_daily": round(net_daily, 4),
            "net_monthly": round(net_monthly, 2),
            "net_yearly": round(net_yearly, 2),
            "apy_pct": round((net_yearly / allocated) * 100, 2) if allocated > 0 else 0
        }

    def should_close(self, symbol):
        funding_data = self.get_current_funding_rate(symbol)
        if not funding_data:
            return False, ""
        rate = funding_data["rate_pct"]
        if rate < -0.005:
            return True, "Funding manfiy: " + str(rate) + "%"
        if abs(rate) < 0.003:
            return True, "Funding juda past: " + str(rate) + "%"
        return False, ""

    def collect_funding(self, symbol):
        if symbol not in self.active_positions:
            return 0
        pos = self.active_positions[symbol]
        funding_data = self.get_current_funding_rate(symbol)
        if not funding_data:
            return 0
        rate = funding_data["rate_pct"]
        funding_amount = pos["futures_size"] * (rate / 100)
        pos["total_funding"] = pos["total_funding"] + funding_amount
        pos["funding_count"] = pos["funding_count"] + 1
        self.total_funding_earned = self.total_funding_earned + funding_amount
        return funding_amount

    def print_report(self):
        print("")
        print("=" * 60)
        print("  DELTA-NEUTRAL FUNDING ARBITRAGE")
        print("  Xavfsiz yillik 15-40% foyda")
        print("  Vaqt: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
        print("=" * 60)
        print("")
        print("  ENG YAXSHI IMKONIYATLAR (katta coinlar):")
        print("  " + "-" * 55)
        print("  #   Symbol        Rate      Yillik    $1000/oy")
        print("  " + "-" * 55)
        opportunities = self.get_best_opportunities()
        if not opportunities:
            print("  Ma'lumot olinmadi (VPN kerak bo'lishi mumkin)")
        else:
            for i, opp in enumerate(opportunities[:10]):
                calc = self.calculate_position(1000, opp["rate_pct"])
                sym = opp["symbol"]
                if len(sym) < 12:
                    sym = sym + " " * (12 - len(sym))
                print("  " + str(i+1) + ".  " + sym + "  " + str(opp["rate_pct"]) + "%     " + str(opp["safe_annual"]) + "%    $" + str(calc["net_monthly"]))
        print("  " + "-" * 55)
        print("")
        if opportunities:
            best = opportunities[0]
            calc = self.calculate_position(1000, best["rate_pct"])
            print("  DELTA-NEUTRAL HISOB (" + best["symbol"] + "):")
            print("  " + "-" * 55)
            print("  Kapital: $1000")
            print("  Spot BUY: $" + str(calc["spot_size"]) + " (narx oshsa foyda)")
            print("  Futures SHORT: $" + str(calc["futures_size"]) + " (narx oshsa zarar)")
            print("  JAMI narx ta'siri: $0 (delta neutral!)")
            print("")
            print("  Funding foyda:")
            print("    Har 8 soat: $" + str(calc["funding_per_8h"]))
            print("    Kuniga: $" + str(calc["net_daily"]))
            print("    Oyiga: $" + str(calc["net_monthly"]))
            print("    Yiliga: $" + str(calc["net_yearly"]))
            print("    APY: " + str(calc["apy_pct"]) + "%")
            print("")
            print("  Komissiya (ochish+yopish): $" + str(calc["total_fees"]))
            print("  " + "-" * 55)
            print("")
            print("  XAVFSIZLIK:")
            print("  - Narx ko'tarilsa: Spot +$100, Futures -$100 = $0")
            print("  - Narx tushsa: Spot -$100, Futures +$100 = $0")
            print("  - Faqat FUNDING = SOF FOYDA!")
            print("  - Risk: faqat birja xavfi (hack, bankrot)")
        print("")
        print("=" * 60)


if __name__ == "__main__":
    import ccxt
    exchange = ccxt.binance({"enableRateLimit": True})
    arb = FundingArbitrage(exchange)
    arb.print_report()
