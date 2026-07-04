"""
PAIR TRADING STRATEGIYASI
Teskari korrelyatsiya bilan savdo qilish
Sardor uchun maxsus!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    PAIR_TRADING_ENABLED, PAIR_MIN_CORRELATION, PAIR_TRIGGER_MOVE_PCT,
    PAIR_STOP_LOSS_PCT, PAIR_TAKE_PROFIT_PCT, PAIR_MAX_POSITIONS,
    PAIR_LOOKBACK_HOURS
)
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class PairTradingEngine:
    """Pair Trading strategiyasi"""
    
    def __init__(self, exchange):
        self.exchange = exchange
        self.correlation_cache = {}  # {('BTC/USDT', 'ETH/USDT'): -0.75}
        self.last_correlation_update = None
        self.active_pairs = []
        
    def update_correlations(self, symbols):
        """Barcha coinlar orasida korrelyatsiyani yangilash"""
        print("  >>> Pair Trading: Korrelyatsiya yangilanmoqda...")
        
        # Har 1 soatda yangilash
        now = datetime.now()
        if self.last_correlation_update and (now - self.last_correlation_update).seconds < 3600:
            return
        
        try:
            # Har bir coin uchun narxlarni olish
            price_data = {}
            for symbol in symbols:
                try:
                    ohlcv = self.exchange.fetch_ohlcv(symbol, "1h", limit=PAIR_LOOKBACK_HOURS)
                    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
                    price_data[symbol] = df["close"].values
                except:
                    continue
            
            # Korrelyatsiya hisoblash
            self.correlation_cache = {}
            symbols_list = list(price_data.keys())
            
            for i in range(len(symbols_list)):
                for j in range(i + 1, len(symbols_list)):
                    coin1 = symbols_list[i]
                    coin2 = symbols_list[j]
                    
                    # Pearson correlation
                    corr = np.corrcoef(price_data[coin1], price_data[coin2])[0, 1]
                    
                    # Faqat teskari korrelyatsiyani saqlash
                    if corr < PAIR_MIN_CORRELATION:
                        self.correlation_cache[(coin1, coin2)] = corr
            
            self.last_correlation_update = now
            print(f"  >>> Pair Trading: {len(self.correlation_cache)} ta teskari juftlik topildi")
            
            # Eng kuchli 5 ta
            sorted_pairs = sorted(self.correlation_cache.items(), key=lambda x: x[1])
            for pair, corr in sorted_pairs[:5]:
                coin1 = pair[0].replace("/USDT", "")
                coin2 = pair[1].replace("/USDT", "")
                print(f"      {coin1} ↔️ {coin2}: {corr:.2f}")
        
        except Exception as e:
            print(f"  >>> Pair Trading xato: {e}")
    
    def check_pair_signals(self, current_prices, open_positions):
        """Pair Trading signallarini tekshirish"""
        if not PAIR_TRADING_ENABLED:
            return []
        
        if len(self.active_pairs) >= PAIR_MAX_POSITIONS:
            return []  # Maksimal pair limitga yetgan
        
        signals = []
        
        # Har bir teskari juftlikni tekshirish
        for (coin1, coin2), correlation in self.correlation_cache.items():
            # Agar ikkala coin ham ochiq bo'lsa, skip
            if coin1 in open_positions or coin2 in open_positions:
                continue
            
            # Hozirgi narxlar
            price1 = current_prices.get(coin1)
            price2 = current_prices.get(coin2)
            
            if not price1 or not price2:
                continue
            
            try:
                # Oxirgi 10 soat o'rtacha narx
                ohlcv1 = self.exchange.fetch_ohlcv(coin1, "1h", limit=10)
                ohlcv2 = self.exchange.fetch_ohlcv(coin2, "1h", limit=10)
                
                avg_price1 = np.mean([x[4] for x in ohlcv1])  # close narxlar
                avg_price2 = np.mean([x[4] for x in ohlcv2])
                
                # O'zgarish %
                change1 = ((price1 - avg_price1) / avg_price1) * 100
                change2 = ((price2 - avg_price2) / avg_price2) * 100
                
                # SIGNAL 1: Coin1 ko'tarildi → Coin2 SHORT
                if change1 >= PAIR_TRIGGER_MOVE_PCT and change2 < PAIR_TRIGGER_MOVE_PCT:
                    signals.append({
                        "symbol": coin2,
                        "type": "SHORT",
                        "reason": f"Pair: {coin1.replace('/USDT', '')} +{change1:.1f}% (corr: {correlation:.2f})",
                        "strategy": "PairTrading",
                        "pair_coin": coin1,
                        "correlation": correlation
                    })
                
                # SIGNAL 2: Coin2 ko'tarildi → Coin1 SHORT
                elif change2 >= PAIR_TRIGGER_MOVE_PCT and change1 < PAIR_TRIGGER_MOVE_PCT:
                    signals.append({
                        "symbol": coin1,
                        "type": "SHORT",
                        "reason": f"Pair: {coin2.replace('/USDT', '')} +{change2:.1f}% (corr: {correlation:.2f})",
                        "strategy": "PairTrading",
                        "pair_coin": coin2,
                        "correlation": correlation
                    })
                
                # SIGNAL 3: Coin1 tushdi → Coin2 LONG
                elif change1 <= -PAIR_TRIGGER_MOVE_PCT and change2 > -PAIR_TRIGGER_MOVE_PCT:
                    signals.append({
                        "symbol": coin2,
                        "type": "LONG",
                        "reason": f"Pair: {coin1.replace('/USDT', '')} {change1:.1f}% (corr: {correlation:.2f})",
                        "strategy": "PairTrading",
                        "pair_coin": coin1,
                        "correlation": correlation
                    })
                
                # SIGNAL 4: Coin2 tushdi → Coin1 LONG
                elif change2 <= -PAIR_TRIGGER_MOVE_PCT and change1 > -PAIR_TRIGGER_MOVE_PCT:
                    signals.append({
                        "symbol": coin1,
                        "type": "LONG",
                        "reason": f"Pair: {coin2.replace('/USDT', '')} {change2:.1f}% (corr: {correlation:.2f})",
                        "strategy": "PairTrading",
                        "pair_coin": coin2,
                        "correlation": correlation
                    })
            
            except Exception as e:
                continue
        
        return signals
    
    def get_correlation_report(self):
        """Telegram uchun korrelyatsiya hisoboti"""
        if not self.correlation_cache:
            return "Hali korrelyatsiya ma'lumotlari yo'q. Biroz kuting..."
        
        report = "<b>📊 TESKARI KORRELYATSIYA</b>\n\n"
        
        # Eng kuchli 10 ta
        sorted_pairs = sorted(self.correlation_cache.items(), key=lambda x: x[1])
        
        for i, (pair, corr) in enumerate(sorted_pairs[:10], 1):
            coin1 = pair[0].replace("/USDT", "")
            coin2 = pair[1].replace("/USDT", "")
            
            if corr < -0.70:
                emoji = "🔥"
            elif corr < -0.50:
                emoji = "✅"
            else:
                emoji = "⚠️"
            
            report += f"{i}. {emoji} <b>{coin1}</b> ↔️ <b>{coin2}</b>: {corr:.2f}\n"
        
        report += f"\n<i>Jami: {len(self.correlation_cache)} ta teskari juftlik</i>"
        return report
