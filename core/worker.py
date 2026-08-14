from PyQt6.QtCore import QThread, pyqtSignal
from core.scraper import GameScraper

class SearchWorker(QThread):
    results_found = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, game_name, category="ALL", page_num=1):
        super().__init__()
        self.game_name = game_name
        self.category = category
        self.page_num = page_num
        self.scraper = GameScraper()

    def run(self):
        data = self.scraper.search_downloadha(self.game_name, self.category, self.page_num)
        self.results_found.emit(data)
        self.finished.emit()

class FetchLinksWorker(QThread):
    links_found = pyqtSignal(dict)

    def __init__(self, post_url):
        super().__init__()
        self.post_url = post_url
        self.scraper = GameScraper()

    def run(self):
        data = self.scraper.fetch_post_download_links(self.post_url)
        self.links_found.emit(data)