import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    DCA_ENABLED, DCA_MAX_ORDERS, DCA_STEP_PCT,
    DCA_MULTIPLIER, DCA_TAKE_PROFIT_PCT
)


class DCABot:
    """DCA (Dollar Cost Averaging) - narx tushganda qo'shimcha sotib olish
    
    Qanday ishlaydi:
    1. Birinchi BUY @ $60,000
    2. Narx -2% tushdi -> 2-chi BUY @ $58,800 (2x hajm)
    3. Narx yana -2% tushdi -> 3-chi BUY @ $57,624 (4x hajm)
    4. O'rtacha narx: $58,500
    5. Narx $59,100 ga chiqdi (+1% o'rtachadan) -> SELL hammasi -> FOYDA!
    
    Natija: oddiy botda -3% zarar bo'lardi, DCA bilan +1% foyda!
    """

    def __init__(self, symbol, entry_price, initial_size, strategy, ai_confidence):
        self.symbol = symbol
        self.orders = []
        self.total_invested = 0
        self.total_quantity = 0
        self.average_price = 0
        self.is_active = True
        self.strategy = strategy
        self.ai_confidence = ai_confidence
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Birinchi order
        self.add_order(entry_price, initial_size)

    def add_order(self, price, size):
        """Yangi DCA order qo'shish"""
        order_num = len(self.orders) + 1
        
        # Multiplier: har keyingi order kattaroq
        if order_num > 1:
            size = size * (DCA_MULTIPLIER ** (order_num - 1))

        quantity = size / price
        self.orders.append({
            "num": order_num,
            "price": price,
            "size": round(size, 2),
            "quantity": quantity,
            "time": datetime.now().strftime("%H:%M:%S")
        })

        self.total_invested = self.total_invested + size
        self.total_quantity = self.total_quantity + quantity
        self.average_price = self.total_invested / self.total_quantity

        return order_num

    def check_dca(self, current_price):
        """DCA signal tekshirish"""
        signals = []

        if not self.is_active:
            return signals

        # 1. Take Profit tekshirish (o'rtacha narxdan)
        profit_pct = ((current_price - self.average_price) / self.average_price) * 100

        if profit_pct >= DCA_TAKE_PROFIT_PCT:
            total_profit = (current_price - self.average_price) * self.total_quantity
            signals.append({
                "action": "DCA_CLOSE",
                "profit_pct": round(profit_pct, 2),
                "profit_usd": round(total_profit, 2),
                "orders_count": len(self.orders),
                "avg_price": round(self.average_price, 2),
                "close_price": current_price
            })
            self.is_active = False
            return signals

        # 2. Keyingi DCA order kerakmi?
        if len(self.orders) >= DCA_MAX_ORDERS:
            return signals

        last_order_price = self.orders[-1]["price"]
        drop_pct = ((last_order_price - current_price) / last_order_price) * 100

        if drop_pct >= DCA_STEP_PCT:
            # Yangi DCA order
            base_size = self.orders[0]["size"]
            order_num = self.add_order(current_price, base_size)
            signals.append({
                "action": "DCA_BUY",
                "order_num": order_num,
                "price": current_price,
                "avg_price": round(self.average_price, 2),
                "total_invested": round(self.total_invested, 2),
                "drop_pct": round(drop_pct, 2)
            })

        return signals

    def get_stats(self):
        """DCA statistikasi"""
        return {
            "symbol": self.symbol,
            "orders": len(self.orders),
            "max_orders": DCA_MAX_ORDERS,
            "avg_price": round(self.average_price, 2),
            "total_invested": round(self.total_invested, 2),
            "is_active": self.is_active,
            "strategy": self.strategy
        }

    def get_current_profit(self, current_price):
        """Hozirgi foyda/zarar"""
        if self.total_quantity == 0:
            return 0, 0
        profit_pct = ((current_price - self.average_price) / self.average_price) * 100
        profit_usd = (current_price - self.average_price) * self.total_quantity
        return round(profit_pct, 2), round(profit_usd, 2)
