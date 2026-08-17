import sys
import argparse

def run_desktop_gui():
    """راه‌اندازی نسخه دسکتاپ PyQt6"""
    print("🚀 در حال اجرای رابط کاربری دسکتاپ (PyQt6)...")
    from PyQt6.QtWidgets import QApplication
    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

def run_bale_bot():
    """راه‌اندازی ربات پیام‌رسان بله (Bale.ai Bot)"""
    print("🤖 در حال راه‌اندازی و اتصال ربات بله...")
    from bot.bale_bot import start_bale_bot
    start_bale_bot()

def main():
    parser = argparse.ArgumentParser(description="Game Searcher Pro - Launcher")
    parser.add_argument(
        "--mode", 
        choices=["gui", "bot"], 
        help="انتخاب حالت اجرا: gui (رابط دسکتاپ) یا bot (ربات بله)"
    )
    args = parser.parse_args()

    # اگر از طریق آرگومان خط فرمان مشخص شده باشد:
    if args.mode == "gui":
        run_desktop_gui()
    elif args.mode == "bot":
        run_bale_bot()
    else:
        # منوی تعاملی در ترمینال در صورت اجرا بدون آرگومان
        print("=" * 55)
        print("🎮 به سامانه جامع Game Searcher Pro خوش آمدید 🎮")
        print("=" * 55)
        print("لطفاً مشخص کنید کدام نسخه را می‌خواهید اجرا کنید:")
        print("  [1] 🖥️  نسخه دسکتاپ گرافیکی (PyQt6 GUI - MainWindow)")
        print("  [2] 🤖  نسخه ربات پیام‌رسان بله (Bale.ai Bot)")
        print("  [3] ❌  خروج")
        print("=" * 55)

        try:
            choice = input("👉 لطفاً گزینه مورد نظر را وارد کنید (1/2): ").strip()
            if choice == "1":
                run_desktop_gui()
            elif choice == "2":
                run_bale_bot()
            elif choice == "3":
                print("👋 خداحافظ!")
                sys.exit(0)
            else:
                print("⚠️ گزینه نامعتبر است! به صورت پیش‌فرض نسخه دسکتاپ اجرا می‌شود.")
                run_desktop_gui()
        except KeyboardInterrupt:
            print("\n👋 خروج از برنامه.")
            sys.exit(0)

if __name__ == "__main__":
    main()
