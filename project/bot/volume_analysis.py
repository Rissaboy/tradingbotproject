"""
VOLUME ANALYSIS MODULE
Hajm tahlili - Katta investorlar (kitlar) harakatini topish
Sardor uchun maxsus!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime


class VolumeAnalyzer:
    """Hajm tahlili - kitlarni topish"""
    
    def __init__(self, lookback_periods=20, spike_multiplier=3.0):
        self.lookback_periods = lookback_periods
        self.spike_multiplier = spike_multiplier
    
    def analyze_volume(self, df, symbol=None):
        """Hajm tahlili va signal berish"""
        if len(df) < self.lookback_periods + 1:
            return {
                "volume_signal": None,
                "volume_strength": 0,
                "reason": "Ma'lumot yetarli emas"
            }
        
        current_volume = df.iloc[-1]["volume"]
        avg_volume = df["volume"].tail(self.lookback_periods).mean()
        
        # Volume spike (o'rtachadan katta hajm)
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Volume-Price relationship
        current_close = df.iloc[-1]["close"]
        prev_close = df.iloc[-2]["close"]
        price_change = ((current_close - prev_close) / prev_close) * 100
        
        # Volume trend (hajm o'smoqdami?)
        recent_volumes = df["volume"].tail(5).values
        volume_trend = "RISING" if recent_volumes[-1] > np.mean(recent_volumes[:-1]) * 1.2 else "FALLING"
        
        # SIGNAL 1: Volume Spike + Price Up = BULLISH (Kitlar olmoqda)
        if volume_ratio >= self.spike_multiplier and price_change > 0.5:
            return {
                "volume_signal": "LONG",
                "volume_strength": min(volume_ratio / self.spike_multiplier, 3.0),  # 1.0 - 3.0
                "reason": f"Volume spike {volume_ratio:.1f}x (kitlar olmoqda)",
                "volume_ratio": volume_ratio,
                "price_change": price_change
            }
        
        # SIGNAL 2: Volume Spike + Price Down = BEARISH (Kitlar sotmoqda)
        elif volume_ratio >= self.spike_multiplier and price_change < -0.5:
            return {
                "volume_signal": "SHORT",
                "volume_strength": min(volume_ratio / self.spike_multiplier, 3.0),
                "reason": f"Volume spike {volume_ratio:.1f}x (kitlar sotmoqda)",
                "volume_ratio": volume_ratio,
                "price_change": price_change
            }
        
        # SIGNAL 3: Accumulation (Narx o'smayapti lekin hajm katta - kitlar yig'moqda)
        elif volume_ratio >= self.spike_multiplier * 0.7 and -0.3 < price_change < 0.3 and volume_trend == "RISING":
            return {
                "volume_signal": "LONG",
                "volume_strength": 1.5,
                "reason": f"Accumulation (kitlar jim yig'moqda)",
                "volume_ratio": volume_ratio,
                "price_change": price_change
            }
        
        # SIGNAL 4: Distribution (Narx tushmoqda, hajm katta - kitlar sotmoqda)
        elif volume_ratio >= 2.0 and price_change < -1.0:
            return {
                "volume_signal": "SHORT",
                "volume_strength": 2.0,
                "reason": f"Distribution (kitlar sotib chiqmoqda)",
                "volume_ratio": volume_ratio,
                "price_change": price_change
            }
        
        # SIGNAL 5: Volume-Price Divergence
        # Narx yuqoriga, lekin hajm past = zaif trend
        elif price_change > 1.0 and volume_ratio < 0.7:
            return {
                "volume_signal": None,  # Signal yo'q (zaif)
                "volume_strength": 0,
                "reason": f"Zaif trend (hajm past)",
                "volume_ratio": volume_ratio,
                "price_change": price_change,
                "warning": "WEAK_TREND"
            }
        
        else:
            return {
                "volume_signal": None,
                "volume_strength": 0,
                "reason": "Normal hajm",
                "volume_ratio": volume_ratio,
                "price_change": price_change
            }
    
    def check_volume_confirmation(self, signal_type, df):
        """Asosiy signal uchun volume tasdiqlash"""
        volume_analysis = self.analyze_volume(df)
        
        # Agar asosiy signal LONG va volume ham LONG = KUCHLI ✅
        if signal_type == "LONG" and volume_analysis["volume_signal"] == "LONG":
            return True, volume_analysis["volume_strength"], volume_analysis["reason"]
        
        # Agar asosiy signal SHORT va volume ham SHORT = KUCHLI ✅
        elif signal_type == "SHORT" and volume_analysis["volume_signal"] == "SHORT":
            return True, volume_analysis["volume_strength"], volume_analysis["reason"]
        
        # Agar volume teskari signal = ZAIF ❌
        elif signal_type == "LONG" and volume_analysis["volume_signal"] == "SHORT":
            return False, 0, "Volume teskari signal (kitlar sotmoqda)"
        
        elif signal_type == "SHORT" and volume_analysis["volume_signal"] == "LONG":
            return False, 0, "Volume teskari signal (kitlar olmoqda)"
        
        # Volume neutral = O'rtacha ⚠️
        else:
            return True, 0.5, "Volume neutral"
    
    def get_volume_report(self, symbol, df):
        """Telegram uchun hajm hisoboti"""
        analysis = self.analyze_volume(df)
        
        report = f"<b>📊 VOLUME ANALYSIS: {symbol.replace('/USDT', '')}</b>\n\n"
        
        if analysis["volume_signal"]:
            emoji = "🟢" if analysis["volume_signal"] == "LONG" else "🔴"
            report += f"{emoji} <b>Signal: {analysis['volume_signal']}</b>\n"
            report += f"Kuch: {analysis['volume_strength']:.1f}/3.0\n\n"
        
        report += f"Hajm: {analysis['volume_ratio']:.1f}x o'rtachadan\n"
        report += f"Narx o'zgarishi: {analysis['price_change']:.2f}%\n"
        report += f"Sabab: {analysis['reason']}\n"
        
        if analysis.get("warning"):
            report += f"\n⚠️ Ogohlantirish: Zaif trend"
        
        return report
