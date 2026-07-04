"""
SENTIMENT ANALYSIS MODULE
Ijtimoiy media va yangiliklar bo'yicha kayfiyat tahlili
Sardor uchun maxsus!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime, timedelta
import time


class SentimentAnalyzer:
    """Sentiment tahlili - Twitter, Reddit, News"""
    
    def __init__(self, sources=None):
        """
        sources: Qaysi manbalardan sentiment olish
        """
        self.sources = sources or ["alternative.me", "coinmarketcap"]
        self.fear_greed_cache = None
        self.cache_time = None
        self.cache_duration = 3600  # 1 soat
    
    def get_fear_greed_index(self):
        """
        Fear & Greed Index (0-100)
        0-25 = Extreme Fear (BULLISH signal - juda arzon)
        25-45 = Fear (BULLISH signal - arzon)
        45-55 = Neutral
        55-75 = Greed (BEARISH signal - qimmat)
        75-100 = Extreme Greed (BEARISH signal - juda qimmat)
        """
        
        # Cache tekshirish
        if self.fear_greed_cache and self.cache_time:
            if (datetime.now() - self.cache_time).seconds < self.cache_duration:
                return self.fear_greed_cache
        
        try:
            # Alternative.me API (bepul, key kerak emas)
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                value = int(data["data"][0]["value"])
                classification = data["data"][0]["value_classification"]
                
                # Cache saqlash
                result = {
                    "value": value,
                    "classification": classification,
                    "timestamp": data["data"][0]["timestamp"]
                }
                
                self.fear_greed_cache = result
                self.cache_time = datetime.now()
                
                return result
            
            else:
                return None
        
        except Exception as e:
            print(f"⚠️ Fear & Greed Index xato: {str(e)}")
            return None
    
    def analyze_sentiment(self):
        """Umumiy sentiment tahlili"""
        
        # Fear & Greed Index
        fg = self.get_fear_greed_index()
        
        if not fg:
            return {
                "signal": None,
                "strength": 0,
                "reason": "Sentiment ma'lumoti yo'q"
            }
        
        value = fg["value"]
        classification = fg["classification"]
        
        # SIGNAL 1: Extreme Fear (0-25) = BULLISH
        # "Be greedy when others are fearful"
        if value <= 25:
            return {
                "signal": "LONG",
                "strength": 3.0,  # Juda kuchli signal
                "reason": f"Extreme Fear ({value}/100) - sotib olish vaqti!",
                "fear_greed_value": value,
                "classification": classification,
                "contrarian_signal": True  # Teskari signal
            }
        
        # SIGNAL 2: Fear (25-45) = Bullish
        elif 25 < value <= 45:
            return {
                "signal": "LONG",
                "strength": 2.0,
                "reason": f"Fear ({value}/100) - yaxshi kirish nuqtasi",
                "fear_greed_value": value,
                "classification": classification,
                "contrarian_signal": True
            }
        
        # SIGNAL 3: Neutral (45-55) = No signal
        elif 45 < value <= 55:
            return {
                "signal": None,
                "strength": 0,
                "reason": f"Neutral ({value}/100) - noaniq holat",
                "fear_greed_value": value,
                "classification": classification
            }
        
        # SIGNAL 4: Greed (55-75) = Bearish
        elif 55 < value <= 75:
            return {
                "signal": "SHORT",
                "strength": 2.0,
                "reason": f"Greed ({value}/100) - ehtiyot bo'ling",
                "fear_greed_value": value,
                "classification": classification,
                "contrarian_signal": True
            }
        
        # SIGNAL 5: Extreme Greed (75-100) = BEARISH
        # "Be fearful when others are greedy"
        else:  # value > 75
            return {
                "signal": "SHORT",
                "strength": 3.0,
                "reason": f"Extreme Greed ({value}/100) - sotish vaqti!",
                "fear_greed_value": value,
                "classification": classification,
                "contrarian_signal": True
            }
    
    def get_social_sentiment(self, symbol):
        """
        Ijtimoiy media sentiment (Twitter, Reddit, etc.)
        
        ⚠️ Bu funktsiya hozircha DEMO versiyasi!
        Real ishlatish uchun:
        - Twitter API key
        - Reddit API key
        - LunarCrush API key
        kerak bo'ladi
        """
        
        # Demo: Random sentiment (real API uchun joyni tayyorlash)
        # Real versiyada Twitter, Reddit, Telegram kanallarini tahlil qilish kerak
        
        return {
            "twitter_sentiment": 0,  # -1 to +1
            "reddit_sentiment": 0,
            "telegram_sentiment": 0,
            "overall_sentiment": 0,
            "status": "DEMO - Real API ulanmagan"
        }
    
    def get_news_sentiment(self, symbol):
        """
        Yangiliklar bo'yicha sentiment
        
        ⚠️ Bu funktsiya hozircha DEMO versiyasi!
        Real ishlatish uchun:
        - CryptoPanic API
        - NewsAPI
        - CoinDesk RSS
        kerak bo'ladi
        """
        
        return {
            "positive_news": 0,
            "negative_news": 0,
            "neutral_news": 0,
            "overall_sentiment": 0,
            "status": "DEMO - Real API ulanmagan"
        }
    
    def get_combined_sentiment(self, symbol=None):
        """Barcha manbalardan sentiment birlashtirish"""
        
        # 1. Fear & Greed Index (bozor umumiy kayfiyati)
        market_sentiment = self.analyze_sentiment()
        
        # 2. Ijtimoiy media (coin-specific)
        social_sentiment = self.get_social_sentiment(symbol) if symbol else None
        
        # 3. Yangiliklar (coin-specific)
        news_sentiment = self.get_news_sentiment(symbol) if symbol else None
        
        # Combined signal
        # Hozircha faqat Fear & Greed ishlatamiz
        # Keyinchalik social va news qo'shamiz
        
        return {
            "market_sentiment": market_sentiment,
            "social_sentiment": social_sentiment,
            "news_sentiment": news_sentiment,
            "primary_signal": market_sentiment["signal"],
            "primary_strength": market_sentiment["strength"],
            "primary_reason": market_sentiment["reason"]
        }
    
    def check_sentiment_confirmation(self, signal_type):
        """Asosiy signal uchun sentiment tasdiqlash"""
        
        sentiment = self.analyze_sentiment()
        
        # Agar asosiy signal LONG va sentiment ham LONG = KUCHLI ✅
        if signal_type == "LONG" and sentiment["signal"] == "LONG":
            return True, sentiment["strength"], sentiment["reason"]
        
        # Agar asosiy signal SHORT va sentiment ham SHORT = KUCHLI ✅
        elif signal_type == "SHORT" and sentiment["signal"] == "SHORT":
            return True, sentiment["strength"], sentiment["reason"]
        
        # Agar sentiment teskari = ZAIF ❌
        elif signal_type == "LONG" and sentiment["signal"] == "SHORT":
            return False, 0, f"Sentiment teskari: {sentiment['reason']}"
        
        elif signal_type == "SHORT" and sentiment["signal"] == "LONG":
            return False, 0, f"Sentiment teskari: {sentiment['reason']}"
        
        # Sentiment neutral = O'rtacha ⚠️
        else:
            return True, 0.5, "Sentiment neutral"
    
    def get_sentiment_report(self):
        """Telegram uchun sentiment hisoboti"""
        
        sentiment = self.analyze_sentiment()
        
        if not sentiment or sentiment["signal"] is None:
            return "📊 <b>SENTIMENT ANALYSIS</b>\n\nMa'lumot yo'q ❌"
        
        value = sentiment["fear_greed_value"]
        classification = sentiment["classification"]
        
        # Emoji
        if value <= 25:
            emoji = "😱"  # Extreme Fear
        elif value <= 45:
            emoji = "😰"  # Fear
        elif value <= 55:
            emoji = "😐"  # Neutral
        elif value <= 75:
            emoji = "😁"  # Greed
        else:
            emoji = "🤑"  # Extreme Greed
        
        # Signal emoji
        signal_emoji = "🟢" if sentiment["signal"] == "LONG" else "🔴"
        
        report = f"<b>📊 MARKET SENTIMENT</b>\n\n"
        report += f"{emoji} <b>Fear & Greed Index: {value}/100</b>\n"
        report += f"Holat: {classification}\n\n"
        
        report += f"{signal_emoji} <b>Signal: {sentiment['signal']}</b>\n"
        report += f"Kuch: {sentiment['strength']:.1f}/3.0\n"
        report += f"Sabab: {sentiment['reason']}\n\n"
        
        # Contrarian strategy
        if sentiment.get("contrarian_signal"):
            report += "💡 <b>Contrarian Strategy</b>\n"
            report += "Bozor kayfiyatiga qarshi savdo qiling!\n"
        
        # Tavsiya
        report += "\n<b>📌 TAVSIYA:</b>\n"
        if value <= 25:
            report += "✅ Sotib olish uchun AJOYIB vaqt!\n"
            report += "Bozor qo'rquvda, narxlar pastda."
        elif value <= 45:
            report += "✅ Sotib olish uchun yaxshi vaqt.\n"
            report += "Hali ham xavotirda, lekin yaxshilanmoqda."
        elif value <= 55:
            report += "⚠️ Noaniq holat. Kutib turing."
        elif value <= 75:
            report += "⚠️ Bozor ochko'z. Ehtiyot bo'ling.\n"
            report += "Yangi pozitsiya ochmang."
        else:
            report += "❌ Bozor juda ochko'z!\n"
            report += "Foyda oling va kuting."
        
        return report


# ============================================
# TEST (Agar to'g'ridan-to'g'ri ishga tushirsangiz)
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("SENTIMENT ANALYZER TEST")
    print("=" * 60)
    
    # Analyzer yaratish
    analyzer = SentimentAnalyzer()
    
    # Fear & Greed Index
    print("\n📊 FEAR & GREED INDEX\n")
    
    fg = analyzer.get_fear_greed_index()
    
    if fg:
        print(f"Qiymat: {fg['value']}/100")
        print(f"Holat: {fg['classification']}")
    else:
        print("Ma'lumot yo'q")
    
    # Sentiment tahlili
    print("\n" + "=" * 60)
    print("SENTIMENT ANALYSIS")
    print("=" * 60)
    
    sentiment = analyzer.analyze_sentiment()
    
    print(f"\nSignal: {sentiment['signal']}")
    print(f"Kuch: {sentiment['strength']}/3.0")
    print(f"Sabab: {sentiment['reason']}")
    
    # Telegram hisoboti
    print("\n" + "=" * 60)
    print("TELEGRAM HISOBOTI")
    print("=" * 60)
    
    print("\n" + analyzer.get_sentiment_report())
