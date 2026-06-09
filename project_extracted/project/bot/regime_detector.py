import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RegimeDetector:
    """Bozor rejimini aniqlash va strategiyani avtomatik almashtirish

    4 xil rejim:
    1. TRENDING_UP    -> Trend Following + Breakout ishlaydi
    2. TRENDING_DOWN  -> Short strategiya + Breakout ishlaydi
    3. RANGING (flat) -> Grid Trading + Mean Reversion ishlaydi
    4. VOLATILE       -> DCA + kichik pozitsiya ishlaydi
    """

    def __init__(self):
        self.current_regime = "UNKNOWN"
        self.regime_history = []

    def detect_regime(self, df):
        """Hozirgi bozor rejimini aniqlash"""
        if len(df) < 50:
            return "UNKNOWN", {}

        last = df.iloc[-1]
        close_prices = df["close"].tail(50).values

        # 1. ADX - trend kuchi
        adx = last["adx"] if "adx" in last else 20

        # 2. Volatillik (ATR)
        atr_pct = last["atr_pct"] if "atr_pct" in last else 1.5

        # 3. EMA trend yo'nalishi
        ema_diff = 0
        if "ema_short" in last and "ema_long" in last:
            ema_diff = (last["ema_short"] - last["ema_long"]) / last["close"] * 100

        # 4. Narx o'zgarishi (oxirgi 20 sham)
        price_change_20 = ((close_prices[-1] - close_prices[-20]) / close_prices[-20]) * 100

        # 5. Bollinger Band kengligi
        bb_width = last["bb_width"] if "bb_width" in last else 2.0

        # 6. Narx range (oxirgi 50 sham high - low)
        high_50 = df["high"].tail(50).max()
        low_50 = df["low"].tail(50).min()
        range_pct = ((high_50 - low_50) / low_50) * 100

        # Rejim aniqlash logikasi
        regime = "RANGING"
        confidence = 0

        # TRENDING_UP: ADX yuqori + EMA UP + narx oshmoqda
        if adx > 25 and ema_diff > 0.5 and price_change_20 > 2:
            regime = "TRENDING_UP"
            confidence = min(100, int(adx + abs(ema_diff) * 10))

        # TRENDING_DOWN: ADX yuqori + EMA DOWN + narx tushmoqda
        elif adx > 25 and ema_diff < -0.5 and price_change_20 < -2:
            regime = "TRENDING_DOWN"
            confidence = min(100, int(adx + abs(ema_diff) * 10))

        # VOLATILE: ATR juda yuqori + BB keng
        elif atr_pct > 3.0 or bb_width > 5.0:
            regime = "VOLATILE"
            confidence = min(100, int(atr_pct * 20))

        # RANGING: ADX past + narx kichik range da
        else:
            regime = "RANGING"
            confidence = min(100, int((30 - adx) * 3))

        self.current_regime = regime
        self.regime_history.append(regime)
        if len(self.regime_history) > 100:
            self.regime_history = self.regime_history[-100:]

        details = {
            "regime": regime,
            "confidence": confidence,
            "adx": round(adx, 1),
            "atr_pct": round(atr_pct, 2),
            "ema_diff": round(ema_diff, 2),
            "price_change_20": round(price_change_20, 2),
            "bb_width": round(bb_width, 2),
            "range_pct": round(range_pct, 2)
        }

        return regime, details

    def get_recommended_strategies(self, regime):
        """Rejimga qarab qaysi strategiyalar ishlatilishi kerak"""

        strategies = {
            "TRENDING_UP": {
                "use": ["Trend", "Breakout"],
                "avoid": ["MeanRev"],
                "grid": False,
                "dca": False,
                "description": "Trend kuchli UP - faqat LONG"
            },
            "TRENDING_DOWN": {
                "use": ["Trend", "Breakout"],
                "avoid": ["MeanRev"],
                "grid": False,
                "dca": True,
                "description": "Trend kuchli DOWN - faqat SHORT"
            },
            "RANGING": {
                "use": ["MeanRev", "SmartMoney"],
                "avoid": ["Trend", "Breakout"],
                "grid": True,
                "dca": False,
                "description": "Flat bozor - Grid + MeanRev"
            },
            "VOLATILE": {
                "use": ["SmartMoney"],
                "avoid": ["Trend", "Breakout", "MeanRev"],
                "grid": False,
                "dca": True,
                "description": "Xavfli - kichik pozitsiya + DCA"
            },
            "UNKNOWN": {
                "use": ["Trend", "MeanRev"],
                "avoid": [],
                "grid": False,
                "dca": False,
                "description": "Noaniq - ehtiyotkor savdo"
            }
        }

        return strategies.get(regime, strategies["UNKNOWN"])

    def should_trade(self, regime, strategy_name):
        """Bu strategiya hozirgi rejimda ishlatilishi kerakmi?"""
        recommendations = self.get_recommended_strategies(regime)

        if strategy_name in recommendations["avoid"]:
            return False, "Rejim '" + regime + "' da '" + strategy_name + "' tavsiya etilmaydi"

        if strategy_name in recommendations["use"]:
            return True, "Rejim '" + regime + "' da '" + strategy_name + "' yaxshi ishlaydi"

        return True, "OK"

    def should_use_grid(self, regime):
        """Grid bot ishlatish kerakmi?"""
        recommendations = self.get_recommended_strategies(regime)
        return recommendations["grid"]

    def should_use_dca(self, regime):
        """DCA ishlatish kerakmi?"""
        recommendations = self.get_recommended_strategies(regime)
        return recommendations["dca"]

    def get_regime_stats(self):
        """Rejim statistikasi"""
        if not self.regime_history:
            return {}

        total = len(self.regime_history)
        stats = {}
        for regime in ["TRENDING_UP", "TRENDING_DOWN", "RANGING", "VOLATILE"]:
            count = self.regime_history.count(regime)
            stats[regime] = round(count / total * 100, 1)

        return stats
