import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    GRID_TRADING_ENABLED, GRID_LEVELS, GRID_SPACING_PCT,
    GRID_ORDER_SIZE_PCT, GRID_TAKE_PROFIT_PCT
)


class GridBot:
    """Grid Trading - flat bozorda avtomatik foyda"""

    def __init__(self, symbol, current_price, balance):
        self.symbol = symbol
        self.center_price = current_price
        self.balance = balance
        self.grid_orders = []
        self.filled_orders = []
        self.total_profit = 0
        self.trades_count = 0
        self.create_grid(current_price)

    def create_grid(self, center_price):
        """Grid darajalarini yaratish"""
        self.grid_orders = []
        self.center_price = center_price

        for i in range(1, GRID_LEVELS + 1):
            buy_price = center_price * (1 - (GRID_SPACING_PCT * i / 100))
            self.grid_orders.append({
                "type": "BUY",
                "price": round(buy_price, 6),
                "level": -i,
                "filled": False,
                "fill_price": 0
            })

            sell_price = center_price * (1 + (GRID_SPACING_PCT * i / 100))
            self.grid_orders.append({
                "type": "SELL",
                "price": round(sell_price, 6),
                "level": i,
                "filled": False,
                "fill_price": 0
            })

    def check_grid(self, current_price):
        """Narx grid darajasini kesib o'tganmi tekshirish"""
        signals = []

        for order in self.grid_orders:
            if order["filled"]:
                continue

            if order["type"] == "BUY" and current_price <= order["price"]:
                order["filled"] = True
                order["fill_price"] = current_price
                self.filled_orders.append({
                    "type": "BUY",
                    "price": current_price,
                    "level": order["level"],
                    "time": datetime.now().strftime("%H:%M:%S")
                })
                signals.append({
                    "action": "GRID_BUY",
                    "price": current_price,
                    "level": order["level"],
                    "tp_price": current_price * (1 + GRID_TAKE_PROFIT_PCT / 100)
                })

            elif order["type"] == "SELL" and current_price >= order["price"]:
                order["filled"] = True
                order["fill_price"] = current_price
                self.filled_orders.append({
                    "type": "SELL",
                    "price": current_price,
                    "level": order["level"],
                    "time": datetime.now().strftime("%H:%M:%S")
                })
                signals.append({
                    "action": "GRID_SELL",
                    "price": current_price,
                    "level": order["level"],
                    "tp_price": current_price * (1 - GRID_TAKE_PROFIT_PCT / 100)
                })

        profit_signals = self.check_take_profits(current_price)
        signals = signals + profit_signals

        return signals

    def check_take_profits(self, current_price):
        """Grid orderlar uchun foyda olish"""
        signals = []
        new_filled = []

        for order in self.filled_orders:
            if order["type"] == "BUY":
                buy_price = order["price"]
                profit_pct = ((current_price - buy_price) / buy_price) * 100

                if profit_pct >= GRID_TAKE_PROFIT_PCT:
                    profit = (current_price - buy_price) * (self.balance * GRID_ORDER_SIZE_PCT / 100) / buy_price
                    self.total_profit = self.total_profit + profit
                    self.trades_count = self.trades_count + 1
                    signals.append({
                        "action": "GRID_TP",
                        "buy_price": buy_price,
                        "sell_price": current_price,
                        "profit_pct": round(profit_pct, 2),
                        "profit_usd": round(profit, 2)
                    })
                else:
                    new_filled.append(order)
            else:
                sell_price = order["price"]
                profit_pct = ((sell_price - current_price) / sell_price) * 100

                if profit_pct >= GRID_TAKE_PROFIT_PCT:
                    profit = (sell_price - current_price) * (self.balance * GRID_ORDER_SIZE_PCT / 100) / sell_price
                    self.total_profit = self.total_profit + profit
                    self.trades_count = self.trades_count + 1
                    signals.append({
                        "action": "GRID_TP",
                        "buy_price": current_price,
                        "sell_price": sell_price,
                        "profit_pct": round(profit_pct, 2),
                        "profit_usd": round(profit, 2)
                    })
                else:
                    new_filled.append(order)

        self.filled_orders = new_filled
        return signals

    def should_reset_grid(self, current_price):
        """Grid ni qayta yaratish kerakmi?"""
        distance = abs(current_price - self.center_price) / self.center_price * 100
        max_distance = GRID_SPACING_PCT * GRID_LEVELS * 1.5
        if distance > max_distance:
            return True
        return False

    def reset_grid(self, current_price):
        """Gridni yangi narx atrofida qayta yaratish"""
        self.filled_orders = []
        self.create_grid(current_price)

    def get_stats(self):
        """Grid statistikasi"""
        active_buys = len([o for o in self.grid_orders if o["type"] == "BUY" and not o["filled"]])
        active_sells = len([o for o in self.grid_orders if o["type"] == "SELL" and not o["filled"]])
        filled_count = len(self.filled_orders)
        return {
            "symbol": self.symbol,
            "center": self.center_price,
            "active_buys": active_buys,
            "active_sells": active_sells,
            "filled": filled_count,
            "total_profit": round(self.total_profit, 2),
            "trades": self.trades_count
        }
