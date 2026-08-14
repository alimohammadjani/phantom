import requests
from bs4 import BeautifulSoup
import re

class GameScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'fa,en-US;q=0.7,en;q=0.3',
        }

    def search_downloadha(self, query, category="ALL", page_num=1):
        results = []
        cleaned_query = query.strip().replace(' ', '+')

        if page_num == 1:
            search_url = f"https://www.downloadha.com/?s={cleaned_query}"
        else:
            search_url = f"https://www.downloadha.com/page/{page_num}/?s={cleaned_query}"

        has_next_page = False

        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return {'results': [], 'has_next': False, 'status': 'NOT_FOUND'}

            soup = BeautifulSoup(response.text, 'html.parser')
            posts = soup.select('article.post-box, article.post, div.post, div.post-box, div.content-box')

            if not posts:
                titles = soup.select('h2.title a, h2.entry-title a, h3.title a, h2 a')
                for a_tag in titles:
                    href = a_tag.get('href', '')
                    title = a_tag.text.strip()
                    img_tag = a_tag.find_parent().find_next('img') if a_tag.find_parent() else None
                    img_src = img_tag.get('src', '') if img_tag else ''

                    if href and title and ('downloadha.com' in href or href.startswith('/')):
                        item = self._format_post_data(title, href, img_src)
                        if self._match_category(title, category):
                            if not any(r['link'] == href for r in results):
                                results.append(item)
            else:
                for post in posts:
                    title_tag = post.select_one('h2 a, h3 a, h1 a, a.title')
                    img_tag = post.select_one('img')
                    img_src = ''
                    if img_tag:
                        # دریافت لینک تصویر حتی اگر Lazy-Load باشد
                        img_src = img_tag.get('data-src') or img_tag.get('src') or ''

                    if title_tag:
                        title = title_tag.text.strip()
                        post_link = title_tag.get('href', '')
                        if post_link and self._match_category(title, category):
                            item = self._format_post_data(title, post_link, img_src)
                            if not any(r['link'] == post_link for r in results):
                                results.append(item)

            next_link = soup.select_one('a.next, a.next-page, .pagination .next')
            if next_link or len(results) > 0: 
                has_next_page = True if next_link else False

        except Exception as e:
            print(f"[Scraper Error Page {page_num}]: {e}")
            return {'results': [], 'has_next': False, 'status': 'ERROR'}

        status = 'OK' if results else 'EMPTY'
        return {'results': results, 'has_next': has_next_page, 'status': status}

    def _match_category(self, title, category):
        if category == "ALL":
            return True
        title_upper = title.upper()
        if category == "PC":
            console_keywords = ['PS4', 'PS5', 'XBOX', 'NINTENDO', 'SWITCH', 'PS3', 'X360']
            return not any(kw in title_upper for kw in console_keywords)
        elif category == "CONSOLE":
            console_keywords = ['PS4', 'PS5', 'XBOX', 'NINTENDO', 'SWITCH', 'PS3', 'X360', 'کنسول']
            return any(kw in title_upper for kw in console_keywords)
        return True

    def _format_post_data(self, title, link, img_src=""):
        version_info = "نسخه اصلی / نامشخص"
        title_upper = title.upper()
        if 'FITGIRL' in title_upper: version_info = "FitGirl Repack"
        elif 'DODI' in title_upper: version_info = "DODI Repack"
        elif 'EMPRESS' in title_upper: version_info = "EMPRESS"
        elif 'RUNE' in title_upper: version_info = "RUNE"
        elif 'TENOKE' in title_upper: version_info = "TENOKE"
        elif 'PS5' in title_upper or 'PS4' in title_upper: version_info = "کنسول پلی‌استیشن"
        elif 'XBOX' in title_upper: version_info = "کنسول ایکس‌باکس"

        return {'site': 'دانلودها', 'title': title, 'link': link, 'quality': version_info, 'image': img_src}

    def fetch_post_download_links(self, post_url):
        download_data = {'links': [], 'password': 'www.downloadha.com'}
        try:
            response = requests.get(post_url, headers=self.headers, timeout=12)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                download_sections = soup.select('.files-list, .download-box, .entry-content, .box-download, .dl-box')
                search_area = download_sections[0] if download_sections else soup

                a_tags = search_area.find_all('a', href=True)
                for a in a_tags:
                    href = a['href'].strip()
                    text = a.text.strip() or "لینک دانلود"
                    if re.search(r'\.(rar|zip|iso|exe|7z|bin|pkg)(\?.*)?$', href, re.IGNORECASE):
                        if not any(link['url'] == href for link in download_data['links']):
                            download_data['links'].append({'text': text, 'url': href})
        except Exception as e:
            print(f"[Details Error]: {e}")
        return download_data