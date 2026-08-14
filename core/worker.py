from PyQt6.QtCore import QThread, pyqtSignal
from core.scraper import GameScraper

class SearchWorker(QThread):
    results_found = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, game_name):
        super().__init__()
        self.game_name = game_name
        self.scraper = GameScraper()

    def run(self):
        results = self.scraper.search_downloadha(self.game_name)
        self.results_found.emit(results)
        self.finished.emit()

class FetchLinksWorker(QThread):
    """ترد اختصاصی برای گرفتن لینک‌های دانلود داخل یک پست"""
    links_found = pyqtSignal(dict)

    def __init__(self, post_url):
        super().__init__()
        self.post_url = post_url
        self.scraper = GameScraper()

    def run(self):
        data = self.scraper.fetch_post_download_links(self.post_url)
        self.links_found.emit(data)