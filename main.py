"""
AI TRADER — MASTER LAUNCHER
Runs all bots together or individually.

Usage:
  python main.py                    # interactive menu
  python main.py trading            # stock trading bot only
  python main.py crypto             # crypto scanner only
  python main.py auto               # auto accept bot only
  python main.py lawyer             # lawyer bot (interactive)
  python main.py all                # all bots simultaneously
"""

import sys
import os
import threading
import time

def check_env():
    required = ["ANTHROPIC_KEY"]
    trading  = ["ALPACA_KEY", "ALPACA_SECRET"]
    missing_required = [k for k in required if not os.environ.get(k)]
    missing_trading  = [k for k in trading  if not os.environ.get(k)]
    if missing_required:
        print(f"FATAL: Missing required env vars: {', '.join(missing_required)}")
        sys.exit(1)
    if missing_trading:
        print(f"WARNING: Trading features disabled — missing: {', '.join(missing_trading)}")
        return False
    return True

def run_trading_bot():
    print("[THREAD] Stock Trading Bot starting...")
    from trading_bot import scan_and_trade, monitor_stops, daily_learning
    import schedule, time
    scan_and_trade()
    schedule.every(15).minutes.do(scan_and_trade)
    schedule.every(5).minutes.do(monitor_stops)
    schedule.every().day.at("18:00").do(daily_learning)
    while True:
        schedule.run_pending()
        time.sleep(30)

def run_crypto_scanner():
    print("[THREAD] Crypto Scanner starting...")
    from crypto_scanner import run_crypto_scan, altseason_check
    import schedule, time
    run_crypto_scan("full")
    schedule.every(30).minutes.do(run_crypto_scan, scan_type="quick")
    schedule.every(4).hours.do(run_crypto_scan, scan_type="full")
    schedule.every().day.at("07:00").do(altseason_check)
    while True:
        schedule.run_pending()
        time.sleep(60)

def run_auto_bot():
    print("[THREAD] Auto Accept Bot starting...")
    from auto_accept_bot import AutoAcceptBot
    bot = AutoAcceptBot()
    bot.run()

def run_lawyer():
    from lawyer_bot import interactive_mode
    interactive_mode()

def print_menu():
    print("\n" + "=" * 55)
    print("   AI TRADER SUITE — SELECT MODE")
    print("=" * 55)
    print("  [1] Stock Trading Bot")
    print("  [2] Crypto Scanner")
    print("  [3] Auto Accept Bot")
    print("  [4] Lawyer Bot")
    print("  [5] Run ALL (trading + crypto + auto)")
    print("  [6] Exit")
    print("=" * 55)

if __name__ == "__main__":
    trading_ok = check_env()

    arg = sys.argv[1].lower() if len(sys.argv) > 1 else None

    if arg == "trading":
        run_trading_bot()

    elif arg == "crypto":
        run_crypto_scanner()

    elif arg == "auto":
        run_auto_bot()

    elif arg == "lawyer":
        run_lawyer()

    elif arg == "all":
        print("Starting ALL bots...")
        threads = []
        if trading_ok:
            threads.append(threading.Thread(target=run_trading_bot,  daemon=True, name="TradingBot"))
            threads.append(threading.Thread(target=run_crypto_scanner, daemon=True, name="CryptoScanner"))
            threads.append(threading.Thread(target=run_auto_bot,     daemon=True, name="AutoBot"))
        for t in threads:
            t.start()
            time.sleep(2)
        print(f"\n{len(threads)} bots running. Press Ctrl+C to stop all.\n")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nShutting down all bots...")

    else:
        # Interactive menu
        while True:
            print_menu()
            choice = input("Enter choice: ").strip()
            if choice == "1":
                run_trading_bot()
            elif choice == "2":
                run_crypto_scanner()
            elif choice == "3":
                run_auto_bot()
            elif choice == "4":
                run_lawyer()
            elif choice == "5":
                threads = []
                if trading_ok:
                    threads.append(threading.Thread(target=run_trading_bot,    daemon=True, name="TradingBot"))
                    threads.append(threading.Thread(target=run_crypto_scanner, daemon=True, name="CryptoScanner"))
                    threads.append(threading.Thread(target=run_auto_bot,       daemon=True, name="AutoBot"))
                for t in threads:
                    t.start()
                    time.sleep(2)
                print(f"{len(threads)} bots running. Press Ctrl+C to stop.")
                try:
                    while True:
                        time.sleep(60)
                except KeyboardInterrupt:
                    print("\nStopping...")
            elif choice == "6":
                print("Goodbye.")
                break
            else:
                print("Invalid choice.")
