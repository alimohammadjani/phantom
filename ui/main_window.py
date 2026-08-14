from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QScrollArea, QLabel, QFrame, QMessageBox)
from PyQt6.QtCore import Qt
import webbrowser
from core.worker import SearchWorker, FetchLinksWorker

class ResultCard(QFrame):
    def __init__(self, site_name, title, post_url, version):
        super().__init__()
        self.post_url = post_url
        self.setObjectName("ResultCard")
        
        self.main_layout = QVBoxLayout(self)

        # اطلاعات سربرگ
        site_label = QLabel(f"🌐 منبع: {site_name}  |  🎮 نسخه: {version}")
        site_label.setStyleSheet("color: #00ADB5; font-size: 11px; font-weight: bold;")
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 14px;")
        title_label.setWordWrap(True)

        # دکمه نمایش لینک‌های دانلود
        self.btn_fetch = QPushButton("📂 مشاهده و دریافت لینک‌های دانلود")
        self.btn_fetch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fetch.clicked.connect(self.load_download_links)

        # کانتینر برای لینک‌های دانلود (در ابتدا مخفی است)
        self.links_container = QWidget()
        self.links_layout = QVBoxLayout(self.links_container)
        self.links_container.hide()

        self.main_layout.addWidget(site_label)
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(self.btn_fetch)
        self.main_layout.addWidget(self.links_container)

    def load_download_links(self):
        # اگر قبلا باز شده بود، با کلیک مجدد مخفی کن
        if not self.links_container.isHidden():
            self.links_container.hide()
            self.btn_fetch.setText("📂 مشاهده و دریافت لینک‌های دانلود")
            return

        self.btn_fetch.setEnabled(False)
        self.btn_fetch.setText("در حال استخراج لینک‌ها...")

        # اجرای ترد برای گرفتن لینک‌ها
        self.fetch_worker = FetchLinksWorker(self.post_url)
        self.fetch_worker.links_found.connect(self.display_links)
        self.fetch_worker.start()

    def display_links(self, data):
        self.btn_fetch.setEnabled(True)
        self.btn_fetch.setText("بستن لینک‌ها 🔼")

        # پاک کردن لینک‌های قبلی در صورت وجود
        for i in reversed(range(self.links_layout.count())):
            widget = self.links_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        links = data.get('links', [])
        if not links:
            no_link_lbl = QLabel("هیچ لینک مستقیم دانلودی یافت نشد.")
            no_link_lbl.setStyleSheet("color: #FF5722;")
            self.links_layout.addWidget(no_link_lbl)
        else:
            # نمایش رمز فایل‌ها
            pass_lbl = QLabel(f"🔑 رمز فایل‌ها: {data.get('password', 'www.downloadha.com')}")
            pass_lbl.setStyleSheet("color: #FFD369; font-weight: bold; margin-top: 5px;")
            self.links_layout.addWidget(pass_lbl)

            # ایجاد دکمه برای هر لینک دانلود
            for link_item in links:
                btn_link = QPushButton(f"📥 {link_item['text']}")
                btn_link.setStyleSheet("""
                    QPushButton {
                        background-color: #222831; 
                        color: #EEEEEE; 
                        text-align: left; 
                        padding: 6px; 
                        border: 1px solid #393E46;
                    }
                    QPushButton:hover { background-color: #393E46; }
                """)
                btn_link.setCursor(Qt.CursorShape.PointingHandCursor)
                url = link_item['url']
                btn_link.clicked.connect(lambda checked, u=url: webbrowser.open(u))
                self.links_layout.addWidget(btn_link)

        self.links_container.show()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Searcher Pro")
        self.resize(850, 650)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # نوار جستجو
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("نام بازی را وارد کنید (مثلا: Resident Evil)...")
        self.search_input.returnPressed.connect(self.start_search)
        
        self.search_btn = QPushButton("جستجو")
        self.search_btn.clicked.connect(self.start_search)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        self.main_layout.addLayout(search_layout)

        # اسکرول اریا نتایج
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.results_layout = QVBoxLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content)
        
        self.main_layout.addWidget(self.scroll)

    def start_search(self):
        game_name = self.search_input.text().strip()
        if not game_name:
            return

        for i in reversed(range(self.results_layout.count())): 
            widget = self.results_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.search_btn.setEnabled(False)
        self.search_btn.setText("در حال جستجو...")

        self.worker = SearchWorker(game_name)
        self.worker.results_found.connect(self.display_results)
        self.worker.finished.connect(self.search_finished)
        self.worker.start()

    def display_results(self, results):
        if not results:
            no_res = QLabel("هیچ نتایجی پیدا نشد.")
            no_res.setStyleSheet("color: white;")
            self.results_layout.addWidget(no_res)
            return

        for item in results:
            card = ResultCard(
                site_name=item['site'],
                title=item['title'],
                post_url=item['link'],
                version=item['quality']
            )
            self.results_layout.addWidget(card)

    def search_finished(self):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("جستجو")