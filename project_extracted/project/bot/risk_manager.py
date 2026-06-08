from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MAX_DAILY_LOSS_PCT, MAX_CONSECUTIVE_LOSSES

class RiskManager:
    def __init__(self, initial_balance):
        self.initial_balance = initial_balance
        self.daily_start_balance = initial_balance
        self.daily_loss = 0.0
        self.consecutive_losses = 0
        self.cooldown_until = None
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.day_start = datetime.now().date()

    def new_day_check(self, current_balance):
        today = datetime.now().date()
        if today != self.day_start:
            self.day_start = today
            self.daily_start_balance = current_balance
            self.daily_loss = 0.0
            self.consecutive_losses = 0
            self.cooldown_until = None
            return True
        return False

    def can_trade(self):
        if self.cooldown_until and datetime.now() < self.cooldown_until:
            return False, "Cooldown"
        daily_loss_pct = (self.daily_loss / self.daily_start_balance) * 100 if self.daily_start_balance > 0 else 0
        if daily_loss_pct >= MAX_DAILY_LOSS_PCT:
            return False, "Kunlik limit"
        if self.consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
            self.cooldown_until = datetime.now() + timedelta(minutes=60)
            return False, "3 ketma-ket zarar"
        return True, "OK"

    def record_trade(self, profit_loss):
        self.total_trades += 1
        if profit_loss >= 0:
            self.winning_trades += 1
            self.consecutive_losses = 0
        else:
            self.losing_trades += 1
            self.consecutive_losses += 1
            self.daily_loss += abs(profit_loss)

    def get_win_rate(self):
        if self.total_trades == 0:
            return 0
        return (self.winning_trades / self.total_trades) * 100

    def get_stats(self):
        return {
            "total": self.total_trades,
            "wins": self.winning_trades,
            "losses": self.losing_trades,
            "win_rate": self.get_win_rate(),
            "consecutive_losses": self.consecutive_losses,
            "daily_loss": self.daily_loss
        }
