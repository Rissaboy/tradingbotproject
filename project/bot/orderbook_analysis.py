"""
ORDER BOOK ANALYSIS MODULE
Orderlar tahlili - Support/Resistance va katta orderlarni topish
Sardor uchun maxsus!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from datetime import datetime


class OrderBookAnalyzer:
    """Order Book tahlili - Support/Resistance"""
    
    def __init__(self, exchange=None, depth_limit=20, imbalance_threshold=2.0):
        self.exchange = exchange
        self.depth_limit = depth_limit
        self.imbalance_threshold = imbalance_threshold
    
    def analyze_orderbook(self, symbol, exchange=None):
        """Order Book tahlili"""
        # Use provided exchange or default one
        exch = exchange or self.exchange
        
        if not exch:
            return {
                "signal": None,
                "strength": 0,
                "reason": "Exchange object yo'q"
            }
        
        try:
            # Order book olish (20 ta eng yaqin order)
            orderbook = exch.fetch_order_book(symbol, limit=self.depth_limit)
            
            bids = orderbook["bids"]  # Buy orders
            asks = orderbook["asks"]  # Sell orders
            
            if not bids or not asks:
                return {
                    "signal": None,
                    "strength": 0,
                    "reason": "Order book ma'lumoti yo'q"
                }
            
            # Total volumes
            total_bid_volume = sum([bid[1] for bid in bids])  # Buy hajm
            total_ask_volume = sum([ask[1] for ask in asks])  # Sell hajm
            
            # Bid/Ask ratio
            ba_ratio = total_bid_volume / total_ask_volume if total_ask_volume > 0 else 1
            
            # Current price
            current_price = (bids[0][0] + asks[0][0]) / 2
            
            # Spread
            spread = ((asks[0][0] - bids[0][0]) / current_price) * 100
            
            # Katta orderlarni topish (whale walls)
            avg_bid_size = total_bid_volume / len(bids)
            avg_ask_size = total_ask_volume / len(asks)
            
            whale_bids = [bid for bid in bids if bid[1] > avg_bid_size * 3]  # 3x kattaroq
            whale_asks = [ask for ask in asks if ask[1] > avg_ask_size * 3]
            
            # SIGNAL 1: Bid Dominance (Ko'proq buy order = bullish)
            if ba_ratio >= self.imbalance_threshold:
                return {
                    "signal": "LONG",
                    "strength": min(ba_ratio / self.imbalance_threshold, 3.0),
                    "reason": f"Buy orders {ba_ratio:.1f}x ko'p (kuchli support)",
                    "ba_ratio": ba_ratio,
                    "spread": spread,
                    "whale_bids": len(whale_bids),
                    "whale_asks": len(whale_asks),
                    "support_level": bids[0][0] if bids else None
                }
            
            # SIGNAL 2: Ask Dominance (Ko'proq sell order = bearish)
            elif ba_ratio <= 1 / self.imbalance_threshold:
                return {
                    "signal": "SHORT",
                    "strength": min(self.imbalance_threshold / ba_ratio, 3.0),
                    "reason": f"Sell orders {1/ba_ratio:.1f}x ko'p (kuchli resistance)",
                    "ba_ratio": ba_ratio,
                    "spread": spread,
                    "whale_bids": len(whale_bids),
                    "whale_asks": len(whale_asks),
                    "resistance_level": asks[0][0] if asks else None
                }
            
            # SIGNAL 3: Whale Buy Wall (Katta buy order = support)
            elif len(whale_bids) >= 3 and len(whale_asks) == 0:
                return {
                    "signal": "LONG",
                    "strength": 2.0,
                    "reason": f"Whale buy wall ({len(whale_bids)} ta katta order)",
                    "ba_ratio": ba_ratio,
                    "spread": spread,
                    "whale_bids": len(whale_bids),
                    "whale_asks": len(whale_asks)
                }
            
            # SIGNAL 4: Whale Sell Wall (Katta sell order = resistance)
            elif len(whale_asks) >= 3 and len(whale_bids) == 0:
                return {
                    "signal": "SHORT",
                    "strength": 2.0,
                    "reason": f"Whale sell wall ({len(whale_asks)} ta katta order)",
                    "ba_ratio": ba_ratio,
                    "spread": spread,
                    "whale_bids": len(whale_bids),
                    "whale_asks": len(whale_asks)
                }
            
            # SIGNAL 5: Wide Spread = Low Liquidity (xavfli)
            elif spread > 0.5:  # 0.5% dan katta spread
                return {
                    "signal": None,
                    "strength": 0,
                    "reason": f"Keng spread ({spread:.2f}%) - past likvidlik",
                    "ba_ratio": ba_ratio,
                    "spread": spread,
                    "warning": "LOW_LIQUIDITY"
                }
            
            else:
                return {
                    "signal": None,
                    "strength": 0,
                    "reason": "Balanced order book",
                    "ba_ratio": ba_ratio,
                    "spread": spread,
                    "whale_bids": len(whale_bids),
                    "whale_asks": len(whale_asks)
                }
        
        except Exception as e:
            return {
                "signal": None,
                "strength": 0,
                "reason": f"Order book xato: {str(e)}"
            }
    
    def find_support_resistance(self, exchange, symbol):
        """Support va Resistance darajalarini topish"""
        try:
            orderbook = exchange.fetch_order_book(symbol, limit=50)
            
            bids = orderbook["bids"]
            asks = orderbook["asks"]
            
            if not bids or not asks:
                return None, None
            
            # Eng katta buy order (support)
            largest_bid = max(bids, key=lambda x: x[1])
            support_price = largest_bid[0]
            support_volume = largest_bid[1]
            
            # Eng katta sell order (resistance)
            largest_ask = max(asks, key=lambda x: x[1])
            resistance_price = largest_ask[0]
            resistance_volume = largest_ask[1]
            
            return {
                "support": support_price,
                "support_volume": support_volume,
                "resistance": resistance_price,
                "resistance_volume": resistance_volume,
                "spread": ((resistance_price - support_price) / support_price) * 100
            }, None
        
        except Exception as e:
            return None, str(e)
    
    def get_orderbook_report(self, symbol, analysis):
        """Telegram uchun order book hisoboti"""
        report = f"<b>📗 ORDER BOOK: {symbol.replace('/USDT', '')}</b>\n\n"
        
        if analysis["signal"]:
            emoji = "🟢" if analysis["signal"] == "LONG" else "🔴"
            report += f"{emoji} <b>Signal: {analysis['signal']}</b>\n"
            report += f"Kuch: {analysis['strength']:.1f}/3.0\n\n"
        
        report += f"Buy/Sell ratio: {analysis['ba_ratio']:.2f}\n"
        report += f"Spread: {analysis['spread']:.3f}%\n"
        report += f"Whale buy walls: {analysis.get('whale_bids', 0)}\n"
        report += f"Whale sell walls: {analysis.get('whale_asks', 0)}\n"
        report += f"Sabab: {analysis['reason']}\n"
        
        if analysis.get("warning"):
            report += f"\n⚠️ Ogohlantirish: Past likvidlik"
        
        return report
