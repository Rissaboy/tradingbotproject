import subprocess
import time
import os
import sys
from datetime import datetime

# Bu fayl botni avtomatik qayta ishga tushiradi
# Agar bot qulab tushsa (xato, internet uzilishi) - 30 soniyadan keyin qayta yoqadi

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(ROOT_DIR, "bot", "main.py")
RESTART_DELAY = 30          # Qulagandan keyin necha soniya kutish
MAX_RESTARTS_PER_HOUR = 20  # Soatiga max qayta yoqish (cheksiz loop oldini olish)

restart_times = []


def can_restart():
    """Soatiga juda ko'p qayta yoqilmaganini tekshirish"""
    global restart_times
    now = time.time()
    # Oxirgi 1 soatdagi restartlar
    restart_times = [t for t in restart_times if now - t < 3600]
    if len(restart_times) >= MAX_RESTARTS_PER_HOUR:
        return False
    return True


def run_with_autorestart():
    print("=" * 60)
    print("  SARDOR BOT - AUTO RESTART WRAPPER")
    print("  Bot qulasa avtomatik qayta ishga tushadi")
    print("  Restart kechikishi: " + str(RESTART_DELAY) + " soniya")
    print("=" * 60)
    print("")

    restart_count = 0

    while True:
        try:
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print("")
            print(">>> [" + start_time + "] Bot ishga tushmoqda... (restart #" + str(restart_count) + ")")
            print("")

            # Botni ishga tushirish
            result = subprocess.run([sys.executable, MAIN_SCRIPT])

            # Agar bot normal to'xtagan bo'lsa (Ctrl+C = exit code 0 yoki 2)
            if result.returncode == 0:
                print("")
                print(">>> Bot normal to'xtatildi. Wrapper ham to'xtaydi.")
                break

            print("")
            print(">>> Bot qulab tushdi! (exit code: " + str(result.returncode) + ")")

        except KeyboardInterrupt:
            print("")
            print(">>> Ctrl+C bosildi. Bot va wrapper to'xtatildi.")
            break

        except Exception as e:
            print(">>> Wrapper xato: " + str(e))

        # Qayta yoqish tekshiruvi
        if not can_restart():
            print(">>> Juda ko'p qayta yoqildi (soatiga " + str(MAX_RESTARTS_PER_HOUR) + "). To'xtatildi.")
            print(">>> Muammoni tekshiring: data/logs/ papkasidagi log fayllar")
            break

        restart_times.append(time.time())
        restart_count = restart_count + 1

        print(">>> " + str(RESTART_DELAY) + " soniyadan keyin qayta yoqiladi...")
        try:
            time.sleep(RESTART_DELAY)
        except KeyboardInterrupt:
            print(">>> Kutish bekor qilindi. To'xtatildi.")
            break


if __name__ == "__main__":
    run_with_autorestart()
