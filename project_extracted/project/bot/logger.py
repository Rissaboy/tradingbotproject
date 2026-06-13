import logging
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def setup_logger():
    """Bot uchun logging tizimini sozlash"""
    log_dir = os.path.join(ROOT_DIR, "data", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Har kun uchun alohida log fayl
    log_filename = "bot_" + datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger("sardor_bot")
    logger.setLevel(logging.INFO)

    # Eski handlerlarni tozalash (qayta sozlashda dublikat bo'lmasin)
    if logger.handlers:
        logger.handlers.clear()

    # Faylga yozish
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Global logger
_logger = None


def get_logger():
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger


def log_info(message):
    """Oddiy ma'lumot yozish"""
    try:
        get_logger().info(message)
    except:
        pass


def log_trade(action, symbol, details):
    """Savdo harakatini yozish"""
    try:
        msg = "TRADE | " + action + " | " + symbol + " | " + str(details)
        get_logger().info(msg)
    except:
        pass


def log_error(message):
    """Xatoni yozish"""
    try:
        get_logger().error("ERROR | " + str(message))
    except:
        pass


def log_signal(symbol, signal_type, strategy, ai_conf, decision):
    """Signal qarorini yozish"""
    try:
        msg = "SIGNAL | " + symbol + " | " + signal_type + " | " + strategy + " | AI:" + str(round(ai_conf * 100, 1)) + "% | " + decision
        get_logger().info(msg)
    except:
        pass
