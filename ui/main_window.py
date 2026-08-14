from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QScrollArea, QLabel, QFrame, 
                             QComboBox, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt
import webbrowser
from core.worker import SearchWorker, FetchLinksWorker

class ResultCard(QFrame):
    def __init__(self, site_name, title, post_url, version):
        super().__init__()
        self.post_url = post_url
        self.setObjectName("ResultCard")
        self.main_layout = QVBoxLayout(self)

        site_label = QLabel(f"🌐 منبع: {site_name}  |  🎮 پلتفرم / نسخه: {version}")
        site_label.setStyleSheet("color: #00ADB5; font-size: 11px; font-weight: bold;")
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 14px;")
        title_label.setWordWrap(True)

        self.btn_fetch = QPushButton("📂 مشاهده و دریافت لینک‌های دانلود")
        self.btn_fetch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fetch.clicked.connect(self.load_download_links)

        self.links_container = QWidget()
        self.links_layout = QVBoxLayout(self.links_container)
        self.links_container.hide()

        self.main_layout.addWidget(site_label)
        self.main_layout.addWidget(title_label)
        self.main_layout.addWidget(self.btn_fetch)
        self.main_layout.addWidget(self.links_container)

    def load_download_links(self):
        if not self.links_container.isHidden():
            self.links_container.hide()
            self.btn_fetch.setText("📂 مشاهده و دریافت لینک‌های دانلود")
            return

        self.btn_fetch.setEnabled(False)
        self.btn_fetch.setText("در حال استخراج لینک‌ها...")

        self.fetch_worker = FetchLinksWorker(self.post_url)
        self.fetch_worker.links_found.connect(self.display_links)
        self.fetch_worker.start()

    def display_links(self, data):
        self.btn_fetch.setEnabled(True)
        self.btn_fetch.setText("بستن لینک‌ها 🔼")

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
            pass_lbl = QLabel(f"🔑 رمز فایل‌ها: {data.get('password', 'www.downloadha.com')}")
            pass_lbl.setStyleSheet("color: #FFD369; font-weight: bold; margin-top: 5px;")
            self.links_layout.addWidget(pass_lbl)

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
        self.resize(850, 680)

        self.current_page = 1
        self.has_next = False

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # نوار بالای سرچ
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("نام بازی را وارد کنید...")
        self.search_input.returnPressed.connect(lambda: self.start_search(page=1))

        self.category_combo = QComboBox()
        self.category_combo.addItem("همه پلتفرم‌ها", "ALL")
        self.category_combo.addItem("بازی PC", "PC")
        self.category_combo.addItem("بازی کنسول", "CONSOLE")

        self.search_btn = QPushButton("جستجو")
        self.search_btn.clicked.connect(lambda: self.start_search(page=1))

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.category_combo)
        search_layout.addWidget(self.search_btn)
        self.main_layout.addLayout(search_layout)

        # اسکرول اریا نتایج
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.results_layout = QVBoxLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll)

        # -------------------------------------------------------------
        # کانتینر نوار پایین (Pagination) - در ابتدا مخفی است
        # -------------------------------------------------------------
        self.pagination_container = QWidget()
        self.pagination_layout = QHBoxLayout(self.pagination_container)
        self.pagination_layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn_prev = QPushButton("◀ صفحه قبل")
        self.btn_prev.clicked.connect(self.go_prev_page)

        self.btn_page_picker = QPushButton("...")
        self.btn_page_picker.setStyleSheet("font-weight: bold; font-size: 16px; padding: 5px 15px;")
        self.btn_page_picker.clicked.connect(self.open_page_dialog)

        self.btn_next = QPushButton("صفحه بعد ▶")
        self.btn_next.clicked.connect(self.go_next_page)

        self.page_label = QLabel("صفحه: 1")
        self.page_label.setStyleSheet("color: #00ADB5; font-weight: bold; margin-left: 10px;")

        self.pagination_layout.addStretch()
        self.pagination_layout.addWidget(self.btn_prev)
        self.pagination_layout.addWidget(self.btn_page_picker)
        self.pagination_layout.addWidget(self.btn_next)
        self.pagination_layout.addWidget(self.page_label)
        self.pagination_layout.addStretch()

        self.main_layout.addWidget(self.pagination_container)

        # مخفی‌سازی اولیه نوار صفحه‌بندی تا قبل از سرچ
        self.pagination_container.hide()

    def start_search(self, page=1):
        game_name = self.search_input.text().strip()
        if not game_name:
            return

        self.current_page = page
        self.page_label.setText(f"صفحه: {self.current_page}")

        # پاک کردن نتایج قبلی
        for i in reversed(range(self.results_layout.count())): 
            widget = self.results_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.search_btn.setEnabled(False)
        self.search_btn.setText("در حال جستجو...")

        selected_category = self.category_combo.currentData()
        self.worker = SearchWorker(game_name, category=selected_category, page_num=self.current_page)
        self.worker.results_found.connect(self.display_results)
        self.worker.finished.connect(self.search_finished)
        self.worker.start()

    def display_results(self, data):
        results = data.get('results', [])
        status = data.get('status', 'OK')
        self.has_next = data.get('has_next', False)

        if status == 'NOT_FOUND' or status == 'EMPTY':
            if self.current_page > 1:
                QMessageBox.warning(self, "خطا", f"صفحه شماره {self.current_page} وجود ندارد یا خالی است!")
                self.start_search(page=self.current_page - 1)
                return
            else:
                self.pagination_container.hide() # عدم نمایش پجینیشن اگر نتیجه‌ای نبود
                no_res = QLabel("هیچ نتایجی پیدا نشد.")
                no_res.setStyleSheet("color: white;")
                self.results_layout.addWidget(no_res)
                return

        # افزودن کارت‌های نتیجه
        for item in results:
            card = ResultCard(
                site_name=item['site'],
                title=item['title'],
                post_url=item['link'],
                version=item['quality']
            )
            self.results_layout.addWidget(card)

        # حالا که نتایج دریافت شد، نوار صفحه‌بندی نمایش داده می‌شود
        self.pagination_container.show()

        # تنظیم وضعیت دکمه‌ها
        enable_prev = self.current_page > 1
        enable_next = self.has_next and len(results) > 0
        self.update_pagination_buttons(enable_prev=enable_prev, enable_next=enable_next)

    def update_pagination_buttons(self, enable_prev, enable_next):
        self.btn_prev.setEnabled(enable_prev)
        self.btn_prev.setStyleSheet(f"opacity: {1.0 if enable_prev else 0.3};")

        self.btn_next.setEnabled(enable_next)
        self.btn_next.setStyleSheet(f"opacity: {1.0 if enable_next else 0.3};")

    def go_prev_page(self):
        if self.current_page > 1:
            self.start_search(page=self.current_page - 1)

    def go_next_page(self):
        if self.has_next:
            self.start_search(page=self.current_page + 1)

    def open_page_dialog(self):
        page, ok = QInputDialog.getInt(
            self, 
            "انتقال به صفحه", 
            "شماره صفحه مورد نظر را وارد کنید:", 
            value=self.current_page, 
            min=1, 
            max=100
        )
        if ok and page != self.current_page:
            self.start_search(page=page)

    def search_finished(self):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("جستجو")