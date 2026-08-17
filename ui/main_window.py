from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QScrollArea, QLabel, QFrame, 
                             QInputDialog, QMessageBox, QToolButton, QMenu, QApplication,
                             QGroupBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QAction
import webbrowser
from core.worker import SearchWorker, FetchLinksWorker, ImageDownloader, shared_scraper


class HoverToolButton(QToolButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

    def enterEvent(self, event):
        self.showMenu()
        super().enterEvent(event)


class ResultCard(QFrame):
    def __init__(self, site_name, title, post_url, version, image_url=""):
        super().__init__()
        self.post_url = post_url
        self.image_url = image_url
        self.download_links = []
        self.setObjectName("ResultCard")
        self.setStyleSheet("""
            #ResultCard {
                background-color: #2D3748;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 10px;
            }
        """)

        self.main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()

        self.img_label = QLabel()
        self.img_label.setFixedSize(100, 100)
        self.img_label.setStyleSheet("background-color: #1A202C; border-radius: 6px; color: #718096;")
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setText("📷 بدون عکس")
        self.img_label.setScaledContents(True)

        info_layout = QVBoxLayout()

        site_label = QLabel(f"🌐 منبع: {site_name}  |  🎮 دسته‌بندی / کیفیت: {version}")
        site_label.setStyleSheet("color: #00ADB5; font-size: 11px; font-weight: bold;")
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px;")
        title_label.setWordWrap(True)

        self.btn_fetch = QPushButton("📂 مشاهده و تفکیک نسخه‌ها و پارت‌های دانلود")
        self.btn_fetch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fetch.clicked.connect(self.load_download_links)

        info_layout.addWidget(site_label)
        info_layout.addWidget(title_label)
        info_layout.addWidget(self.btn_fetch)

        top_layout.addWidget(self.img_label)
        top_layout.addLayout(info_layout)

        self.main_layout.addLayout(top_layout)

        self.links_container = QWidget()
        self.links_layout = QVBoxLayout(self.links_container)
        self.links_container.hide()
        self.main_layout.addWidget(self.links_container)

        if self.image_url:
            self.img_worker = ImageDownloader(self.image_url)
            self.img_worker.image_loaded.connect(self.set_image)
            self.img_worker.start()

    def set_image(self, pixmap):
        if not pixmap.isNull():
            scaled = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.img_label.setPixmap(scaled)

    def load_download_links(self):
        if not self.links_container.isHidden():
            self.links_container.hide()
            self.btn_fetch.setText("📂 مشاهده و تفکیک نسخه‌ها و پارت‌های دانلود")
            return

        self.btn_fetch.setEnabled(False)
        self.btn_fetch.setText("⏳ در حال استخراج و دسته‌بندی نسخه‌ها...")

        self.fetch_worker = FetchLinksWorker(self.post_url)
        self.fetch_worker.links_found.connect(self.display_links)
        self.fetch_worker.start()

    def copy_single_link(self, url, btn):
        clipboard = QApplication.clipboard()
        clipboard.setText(url)
        old_text = btn.text()
        btn.setText("✅ کپی شد!")
        btn.setStyleSheet("background-color: #00ADB5; color: white; padding: 5px 10px; border-radius: 4px; font-size: 11px;")
        QTimer.singleShot(1500, lambda: self.reset_copy_btn(btn, old_text))

    def reset_copy_btn(self, btn, text):
        btn.setText(text)
        btn.setStyleSheet("background-color: #393E46; color: #EEEEEE; padding: 5px 10px; border-radius: 4px; font-size: 11px;")

    def copy_group_links(self, links_list, group_name):
        if not links_list:
            return
        all_urls = "\n".join([l['url'] for l in links_list])
        clipboard = QApplication.clipboard()
        clipboard.setText(all_urls)
        QMessageBox.information(self, "کپی موفق", f"✅ تمامی لینک‌های «{group_name}» کپی شدند.")

    def group_links_by_version(self, links):
        """دسته‌بندی هوشمند پارت‌ها بر اساس نسخه (مثلاً FitGirl, DODI, Setup, Update)"""
        groups = {}
        for link in links:
            text = link.get('text', '')
            # شناسایی نسخه بر اساس الگوهای متداول
            version_key = "نسخه اصلی / عمومی"
            if "fitgirl" in text.lower():
                version_key = "نسخه فشرده FitGirl"
            elif "dodi" in text.lower():
                version_key = "نسخه فشرده DODI"
            elif "rune" in text.lower():
                version_key = "نسخه کامل RUNE"
            elif "elamigos" in text.lower():
                version_key = "نسخه ElAmigos"
            elif "update" in text.lower() or "آپدیت" in text:
                version_key = "آپدیت‌ها و پچ‌ها"
            elif "dlc" in text.lower():
                version_key = "بسته‌های الحاقی (DLC)"

            if version_key not in groups:
                groups[version_key] = []
            groups[version_key].append(link)
        return groups

    def display_links(self, data):
        self.btn_fetch.setEnabled(True)
        self.btn_fetch.setText("بستن بخش لینک‌ها 🔼")

        for i in reversed(range(self.links_layout.count())):
            widget = self.links_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.download_links = data.get('links', [])
        if not self.download_links:
            no_link_lbl = QLabel("هیچ لینک دانلودی برای این پست یافت نشد.")
            no_link_lbl.setStyleSheet("color: #FF5722;")
            self.links_layout.addWidget(no_link_lbl)
        else:
            # نوار سراسری اطلاعات رمز و دکمه کپی همه
            top_bar = QHBoxLayout()
            pass_lbl = QLabel(f"🔑 رمز فایل‌ها: {data.get('password', 'www.downloadha.com')}")
            pass_lbl.setStyleSheet("color: #FFD369; font-weight: bold; font-size: 12px;")
            
            btn_copy_everything = QPushButton("📋 کپی کل لینک‌های همه نسخه‌ها")
            btn_copy_everything.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_copy_everything.setStyleSheet("background-color: #00ADB5; color: white; font-size: 11px; padding: 5px 12px; border-radius: 4px; font-weight: bold;")
            btn_copy_everything.clicked.connect(lambda: self.copy_group_links(self.download_links, "کل پست"))

            top_bar.addWidget(pass_lbl)
            top_bar.addStretch()
            top_bar.addWidget(btn_copy_everything)
            self.links_layout.addLayout(top_bar)

            # تفکیک نسخه‌ها به صورت باکس‌های مجزا
            grouped = self.group_links_by_version(self.download_links)

            for group_name, group_links in grouped.items():
                group_box = QGroupBox(f"📦 {group_name} ({len(group_links)} پارت)")
                group_box.setStyleSheet("""
                    QGroupBox {
                        color: #00ADB5;
                        font-weight: bold;
                        font-size: 12px;
                        border: 1px solid #393E46;
                        border-radius: 6px;
                        margin-top: 10px;
                        padding-top: 15px;
                        background-color: #222831;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px;
                    }
                """)
                g_layout = QVBoxLayout(group_box)

                # دکمه کپی مخصوص این نسخه
                btn_copy_this_group = QPushButton(f"📋 کپی همه پارت‌های {group_name}")
                btn_copy_this_group.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_copy_this_group.setStyleSheet("background-color: #393E46; color: #EEEEEE; font-size: 11px; padding: 4px 8px; border-radius: 4px; margin-bottom: 6px;")
                btn_copy_this_group.clicked.connect(lambda checked, gl=group_links, gn=group_name: self.copy_group_links(gl, gn))
                g_layout.addWidget(btn_copy_this_group)

                # لیست پارت‌ها
                for link_item in group_links:
                    row_widget = QWidget()
                    row_layout = QHBoxLayout(row_widget)
                    row_layout.setContentsMargins(0, 2, 0, 2)

                    url = link_item['url']
                    text = link_item['text']

                    btn_open = QPushButton(f"📥 {text}")
                    btn_open.setStyleSheet("""
                        QPushButton {
                            background-color: #1A202C; 
                            color: #EEEEEE; 
                            text-align: left; 
                            padding: 5px 8px; 
                            border: 1px solid #2D3748;
                            border-radius: 4px;
                            font-size: 11px;
                        }
                        QPushButton:hover { background-color: #2D3748; }
                    """)
                    btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_open.clicked.connect(lambda checked, u=url: webbrowser.open(u))

                    btn_copy = QPushButton("📋 کپی")
                    btn_copy.setStyleSheet("background-color: #2D3748; color: #EEEEEE; padding: 5px 10px; border-radius: 4px; font-size: 11px;")
                    btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_copy.clicked.connect(lambda checked, u=url, b=btn_copy: self.copy_single_link(u, b))

                    row_layout.addWidget(btn_open, stretch=4)
                    row_layout.addWidget(btn_copy, stretch=1)
                    g_layout.addWidget(row_widget)

                self.links_layout.addWidget(group_box)

        self.links_container.show()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Searcher Pro")
        self.resize(900, 700)

        self.current_page = 1
        self.last_valid_page = 1
        self.requested_page = 1
        self.has_next = False
        self.selected_category = "ALL"

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # نوار بالای سرچ
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("نام بازی یا برنامه را وارد کنید...")
        self.search_input.returnPressed.connect(lambda: self.start_search(page=1))

        # دکمه کنسول
        self.btn_console = HoverToolButton()
        self.btn_console.setText("🎮 کنسول ▾")
        self.btn_console.setCursor(Qt.CursorShape.PointingHandCursor)

        console_menu = QMenu(self.btn_console)
        act_ps = QAction("🔵 پلی‌استیشن (PS4 / PS5)", self)
        act_ps.triggered.connect(lambda: self.change_category("CONSOLE_PS", "🔵 کنسول (PS) ▾"))

        act_xbox = QAction("🟢 ایکس‌باکس (XBOX)", self)
        act_xbox.triggered.connect(lambda: self.change_category("CONSOLE_XBOX", "🟢 کنسول (XBOX) ▾"))

        act_nintendo = QAction("🔴 نینتندو (Switch)", self)
        act_nintendo.triggered.connect(lambda: self.change_category("CONSOLE_NINTENDO", "🔴 کنسول (Nintendo) ▾"))

        console_menu.addAction(act_ps)
        console_menu.addAction(act_xbox)
        console_menu.addAction(act_nintendo)
        self.btn_console.setMenu(console_menu)

        # دکمه PC
        self.btn_pc = HoverToolButton()
        self.btn_pc.setText("💻 کامپیوتر (PC) ▾")
        self.btn_pc.setCursor(Qt.CursorShape.PointingHandCursor)

        pc_menu = QMenu(self.btn_pc)
        act_pair = QAction("👥 جفت (بازی و برنامه)", self)
        act_pair.triggered.connect(lambda: self.change_category("PC_ALL", "👥 PC (جفت) ▾"))

        act_game = QAction("🎮 بازی PC", self)
        act_game.triggered.connect(lambda: self.change_category("PC_GAME", "🎮 PC (بازی) ▾"))

        act_app = QAction("🖥️ برنامه PC", self)
        act_app.triggered.connect(lambda: self.change_category("PC_SOFTWARE", "🖥️ PC (برنامه) ▾"))

        pc_menu.addAction(act_pair)
        pc_menu.addAction(act_game)
        pc_menu.addAction(act_app)
        self.btn_pc.setMenu(pc_menu)

        # دکمه جستجو
        self.search_btn = QPushButton("جستجو")
        self.search_btn.clicked.connect(lambda: self.start_search(page=1))

        self.update_filter_buttons_style()

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_console)
        search_layout.addWidget(self.btn_pc)
        search_layout.addWidget(self.search_btn)
        self.main_layout.addLayout(search_layout)

        # بخش نتایج
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.results_layout = QVBoxLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll)

        # نوار صفحه‌بندی
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
        self.pagination_container.hide()

    def change_category(self, cat_code, btn_label):
        self.selected_category = cat_code
        if cat_code.startswith("CONSOLE_"):
            self.btn_console.setText(btn_label)
            self.btn_pc.setText("💻 کامپیوتر (PC) ▾")
        elif cat_code.startswith("PC_"):
            self.btn_pc.setText(btn_label)
            self.btn_console.setText("🎮 کنسول ▾")

        self.update_filter_buttons_style()
        self.start_search(page=1)

    def update_filter_buttons_style(self):
        active_style = "background-color: #00ADB5; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;"
        default_style = "background-color: #393E46; color: #EEEEEE; padding: 6px 12px; border-radius: 4px;"

        if self.selected_category.startswith("CONSOLE_"):
            self.btn_console.setStyleSheet(active_style + " QToolButton::menu-indicator { image: none; }")
            self.btn_pc.setStyleSheet(default_style + " QToolButton::menu-indicator { image: none; }")
        elif self.selected_category.startswith("PC_"):
            self.btn_console.setStyleSheet(default_style + " QToolButton::menu-indicator { image: none; }")
            self.btn_pc.setStyleSheet(active_style + " QToolButton::menu-indicator { image: none; }")
        else:
            self.btn_console.setStyleSheet(default_style + " QToolButton::menu-indicator { image: none; }")
            self.btn_pc.setStyleSheet(default_style + " QToolButton::menu-indicator { image: none; }")

    def start_search(self, page=1):
        game_name = self.search_input.text().strip()
        if not game_name:
            return

        self.requested_page = page
        self.page_label.setText(f"صفحه: {page}")

        is_cached = (
            game_name == shared_scraper.last_query and 
            self.selected_category == shared_scraper.last_category and 
            page in shared_scraper.page_cache
        )

        if not is_cached:
            self.search_btn.setEnabled(False)
            self.search_btn.setText("در حال جستجو...")

        self.worker = SearchWorker(game_name, category=self.selected_category, page_num=page)
        self.worker.results_found.connect(self.display_results)
        self.worker.finished.connect(self.search_finished)
        self.worker.start()

    def display_results(self, data):
        results = data.get('results', [])
        status = data.get('status', 'OK')
        self.has_next = data.get('has_next', False)

        if status == 'NOT_FOUND' or status == 'EMPTY' or len(results) == 0:
            if self.requested_page != self.last_valid_page and self.last_valid_page >= 1:
                QMessageBox.warning(
                    self, 
                    "اطلاع", 
                    f"نتیجه‌ای در صفحه {self.requested_page} یافت نشد.\nبازگشت به آخرین صفحه معتبر (صفحه {self.last_valid_page})..."
                )
                self.start_search(page=self.last_valid_page)
                return
            elif self.requested_page > 1:
                QMessageBox.warning(self, "اطلاع", f"نتیجه دیگری در صفحه {self.requested_page} یافت نشد.")
                self.start_search(page=1)
                return
            else:
                self.pagination_container.hide()
                for i in reversed(range(self.results_layout.count())): 
                    widget = self.results_layout.itemAt(i).widget()
                    if widget:
                        widget.deleteLater()
                no_res = QLabel("هیچ نتایجی مطابق فیلتر یافت نشد.")
                no_res.setStyleSheet("color: white; font-size: 13px;")
                self.results_layout.addWidget(no_res)
                return

        self.current_page = self.requested_page
        self.last_valid_page = self.current_page
        self.page_label.setText(f"صفحه: {self.current_page}")

        for i in reversed(range(self.results_layout.count())): 
            widget = self.results_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for item in results:
            card = ResultCard(
                site_name=item['site'],
                title=item['title'],
                post_url=item['link'],
                version=item['quality'],
                image_url=item.get('image', '')
            )
            self.results_layout.addWidget(card)

        self.pagination_container.show()

        enable_prev = self.current_page > 1
        enable_next = self.has_next and len(results) >= 10
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