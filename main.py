import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def load_stylesheet(app):
    try:
        with open("assets/style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Style file not found, running with default theme.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # اعمال استایل QSS
    load_stylesheet(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())