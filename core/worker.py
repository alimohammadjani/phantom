import requests
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from core.scraper import GameScraper

shared_scraper = GameScraper()

class SearchWorker(QThread):
    results_found = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, game_name, category="ALL", page_num=1):
        super().__init__()
        self.game_name = game_name
        self.category = category
        self.page_num = page_num
        self.scraper = shared_scraper

    def run(self):
        data = self.scraper.search_downloadha_paginated(
            query=self.game_name, 
            category=self.category, 
            app_page_num=self.page_num,
            target_count=10
        )
        self.results_found.emit(data)
        self.finished.emit()

class FetchLinksWorker(QThread):
    links_found = pyqtSignal(dict)

    def __init__(self, post_url):
        super().__init__()
        self.post_url = post_url
        self.scraper = shared_scraper

    def run(self):
        data = self.scraper.fetch_post_download_links(self.post_url)
        self.links_found.emit(data)

class ImageDownloader(QThread):
    image_loaded = pyqtSignal(QPixmap)

    def __init__(self, image_url):
        super().__init__()
        self.image_url = image_url

    def run(self):
        if not self.image_url:
            return
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(self.image_url, headers=headers, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.image_loaded.emit(pixmap)
        except Exception as e:
            print(f"[Image Load Error]: {e}")