"""
MULTI-EXCHANGE ARBITRAGE MODULE
Bir necha birjalar orasida narx farqini topish va foyda olish
Sardor uchun maxsus!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ccxt
import time
from datetime import datetime


class ArbitrageAnalyzer:
    """Arbitraj tahlili - bir necha birjalar orasida narx farqi"""
    
    def __init__(self, min_profit_pct=0.5, exchanges_config=None):
        """
        min_profit_pct: Minimum foyda foizi (komissiyadan keyin)
        exchanges_config: Qaysi birjalarni tekshirish
        """
        self.min_profit_pct = min_profit_pct
        
        # Birjalarni ulash (testnet rejimida)
        self.exchanges = {}
        
        # Default exchanges
        if exchanges_config is None:
            exchanges_config = {
                "binance": {"testnet": True},
                "bybit": {"testnet": True},
                "gateio": {"testnet": False},  # gateio testnet yo'q
            }
        
        # Har bir birjani ulash
        for exchange_name, config in exchanges_config.items():
            try:
                exchange_class = getattr(ccxt, exchange_name)
                
                # Testnet sozlamalari
                if config.get("testnet"):
                    if exchange_name == "binance":
                        exchange = exchange_class({
                            "apiKey": os.getenv(f"{exchange_name.upper()}_TESTNET_API_KEY", ""),
                            "secret": os.getenv(f"{exchange_name.upper()}_TESTNET_SECRET_KEY", ""),
                            "options": {"defaultType": "future"},
                        })
                        exchange.set_sandbox_mode(True)
                    
                    elif exchange_name == "bybit":
                        exchange = exchange_class({
                            "apiKey": os.getenv(f"{exchange_name.upper()}_TESTNET_API_KEY", ""),
                            "secret": os.getenv(f"{exchange_name.upper()}_TESTNET_SECRET_KEY", ""),
                            "options": {"defaultType": "linear"},  # USDT perpetual
                        })
                        exchange.set_sandbox_mode(True)
                    
                    else:
                        exchange = exchange_class()
                
                else:
                    exchange = exchange_class()
                
                self.exchanges[exchange_name] = exchange
                
            except Exception as e:
                print(f"⚠️ {exchange_name} ulanmadi: {str(e)}")
    
    def get_price_on_exchanges(self, symbol):
        """Bir coin uchun barcha birjalardagi narxlarni olish"""
        prices = {}
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                ticker = exchange.fetch_ticker(symbol)
                prices[exchange_name] = {
                    "bid": ticker["bid"],  # Eng yuqori buy narxi
                    "ask": ticker["ask"],  # Eng past sell narxi
                    "last": ticker["last"],  # Oxirgi savdo narxi
                    "volume": ticker["quoteVolume"],  # 24h hajm
                    "timestamp": ticker["timestamp"]
                }
            except Exception as e:
                # Bu birjada coin yo'q yoki xato
                continue
        
        return prices
    
    def find_arbitrage_opportunity(self, symbol):
        """Arbitraj imkoniyatini topish"""
        prices = self.get_price_on_exchanges(symbol)
        
        if len(prices) < 2:
            return {
                "opportunity": False,
                "reason": "Kam birjalarda mavjud"
            }
        
        # Eng past ask (sotib olish narxi) va eng yuqori bid (sotish narxi)
        buy_opportunities = []  # (exchange, ask_price)
        sell_opportunities = []  # (exchange, bid_price)
        
        for exchange_name, data in prices.items():
            buy_opportunities.append((exchange_name, data["ask"]))
            sell_opportunities.append((exchange_name, data["bid"]))
        
        # Eng arzon sotib olish
        best_buy_exchange, best_buy_price = min(buy_opportunities, key=lambda x: x[1])
        
        # Eng qimmat sotish
        best_sell_exchange, best_sell_price = max(sell_opportunities, key=lambda x: x[1])
        
        # Foyda hisoblash
        # 1. Birinchi birjadan sotib olish (ask narxida)
        # 2. Ikkinchi birjaga o'tkazish
        # 3. Ikkinchi birjada sotish (bid narxida)
        
        # Komissiya (0.1% har bir savdo + 0.0005 BTC/ETH transfer)
        trading_fee_pct = 0.1 * 2  # Ikkala birjada ham
        transfer_fee_pct = 0.05  # O'tkazish komissiyasi (~0.05%)
        total_fee_pct = trading_fee_pct + transfer_fee_pct
        
        # Foyda foizi
        profit_pct = ((best_sell_price - best_buy_price) / best_buy_price) * 100
        net_profit_pct = profit_pct - total_fee_pct
        
        # Agar foyda minimum dan katta bo'lsa
        if net_profit_pct >= self.min_profit_pct and best_buy_exchange != best_sell_exchange:
            return {
                "opportunity": True,
                "symbol": symbol,
                "buy_exchange": best_buy_exchange,
                "buy_price": best_buy_price,
                "sell_exchange": best_sell_exchange,
                "sell_price": best_sell_price,
                "gross_profit_pct": profit_pct,
                "net_profit_pct": net_profit_pct,
                "reason": f"{best_buy_exchange} da sotib olib, {best_sell_exchange} da sotish",
                "action": "ARBITRAGE",
                "all_prices": prices
            }
        
        else:
            return {
                "opportunity": False,
                "reason": f"Foyda kam ({net_profit_pct:.2f}% < {self.min_profit_pct}%)",
                "net_profit_pct": net_profit_pct,
                "buy_exchange": best_buy_exchange,
                "sell_exchange": best_sell_exchange
            }
    
    def scan_arbitrage_opportunities(self, symbols):
        """Bir necha coin uchun arbitraj imkoniyatlarini skanerlash"""
        opportunities = []
        
        for symbol in symbols:
            try:
                result = self.find_arbitrage_opportunity(symbol)
                
                if result["opportunity"]:
                    opportunities.append(result)
                    print(f"✅ ARBITRAGE: {symbol} - {result['net_profit_pct']:.2f}% foyda")
                    print(f"   {result['buy_exchange']}: ${result['buy_price']:.4f}")
                    print(f"   {result['sell_exchange']}: ${result['sell_price']:.4f}")
                
                # Rate limit uchun kutish
                time.sleep(0.5)
            
            except Exception as e:
                print(f"⚠️ {symbol}: {str(e)}")
                continue
        
        return opportunities
    
    def get_arbitrage_report(self, opportunities):
        """Telegram uchun arbitraj hisoboti"""
        if not opportunities:
            return "📊 <b>ARBITRAGE SCANNER</b>\n\nHozir imkoniyat yo'q ❌"
        
        report = f"📊 <b>ARBITRAGE OPPORTUNITIES</b>\n"
        report += f"Topildi: {len(opportunities)} ta\n\n"
        
        for opp in opportunities:
            symbol_short = opp["symbol"].replace("/USDT", "")
            report += f"<b>{symbol_short}</b>\n"
            report += f"Foyda: <b>{opp['net_profit_pct']:.2f}%</b> 💰\n"
            report += f"📉 Sotib ol: {opp['buy_exchange']} (${opp['buy_price']:.4f})\n"
            report += f"📈 Sot: {opp['sell_exchange']} (${opp['sell_price']:.4f})\n\n"
        
        return report
    
    def execute_arbitrage_trade(self, opportunity, amount_usd):
        """
        ARBITRAJ SAVDONI BAJARISH (EHTIYOTKORLIK BILAN!)
        
        Bu funktsiya faqat real pulda ishlatish uchun!
        Testnetda sinab ko'ring birinchi!
        
        1. Birinchi birjada sotib olish
        2. Ikkinchi birjaga o'tkazish
        3. Ikkinchi birjada sotish
        """
        
        # ⚠️ BU FUNKTSIYA HOZIRCHA ISHLAMAYDI!
        # Manual ravishda qilishingiz kerak:
        # 1. Birinchi birjada sotib oling
        # 2. Wallet ga o'tkazing
        # 3. Ikkinchi birjaga depozit qiling
        # 4. Ikkinchi birjada soting
        
        return {
            "success": False,
            "message": "Manual ravishda bajaring (avtomatik emas)"
        }


# ============================================
# TEST (Agar to'g'ridan-to'g'ri ishga tushirsangiz)
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("ARBITRAGE SCANNER TEST")
    print("=" * 60)
    
    # Analyzer yaratish
    analyzer = ArbitrageAnalyzer(
        min_profit_pct=0.5,  # 0.5% dan katta foyda
        exchanges_config={
            "binance": {"testnet": True},
            "bybit": {"testnet": True},
        }
    )
    
    # Test coinlar
    test_symbols = [
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT",
        "XRP/USDT",
        "DOGE/USDT",
    ]
    
    print(f"\n{len(analyzer.exchanges)} ta birja ulandi:")
    for name in analyzer.exchanges.keys():
        print(f"  ✅ {name}")
    
    print(f"\n{len(test_symbols)} ta coin tekshirilmoqda...\n")
    
    opportunities = analyzer.scan_arbitrage_opportunities(test_symbols)
    
    print("\n" + "=" * 60)
    print(f"NATIJA: {len(opportunities)} ta arbitraj imkoniyati topildi")
    print("=" * 60)
    
    if opportunities:
        print("\nTelegram hisoboti:")
        print(analyzer.get_arbitrage_report(opportunities))
