import requests
from bs4 import BeautifulSoup
import re

class GameScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'fa,en-US;q=0.7,en;q=0.3',
        }

    def search_downloadha(self, query, category="ALL"):
        """
        category options:
        - 'ALL': همه دسته‌ها
        - 'PC': فقط بازی‌های کامپیوتر
        - 'CONSOLE': بازی‌های کنسول (PS4/PS5/Xbox/Switch)
        """
        results = []
        search_url = f"https://www.downloadha.com/?s={query.strip().replace(' ', '+')}"

        try:
            response = requests.get(search_url, headers=self.headers, timeout=12)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                posts = soup.select('article.post-box, article.post, div.post, div.post-box, div.content-box')
                
                if not posts:
                    titles = soup.select('h2.title a, h2.entry-title a, h3.title a, h2 a')
                    for a_tag in titles:
                        href = a_tag.get('href', '')
                        title = a_tag.text.strip()
                        if href and title and ('downloadha.com' in href or href.startswith('/')):
                            item = self._format_post_data(title, href)
                            if self._match_category(title, category):
                                results.append(item)
                    return results

                for post in posts:
                    title_tag = post.select_one('h2 a, h3 a, h1 a, a.title')
                    if title_tag:
                        title = title_tag.text.strip()
                        post_link = title_tag.get('href', '')
                        if post_link:
                            item = self._format_post_data(title, post_link)
                            # فیلتر کردن بر اساس دسته انتخاب شده
                            if self._match_category(title, category):
                                results.append(item)

        except Exception as e:
            print(f"[Search Error]: {e}")

        return results

    def _match_category(self, title, category):
        """بررسی تطابق عنوان پست با دسته‌بندی انتخابی"""
        if category == "ALL":
            return True
        
        title_upper = title.upper()
        
        if category == "PC":
            # اگر کنسولی نبود، احتمالاً PC است یا کلمات مربوط به PC را دارد
            console_keywords = ['PS4', 'PS5', 'XBOX', 'NINTENDO', 'SWITCH', 'PS3', 'X360']
            return not any(kw in title_upper for kw in console_keywords)
        
        elif category == "CONSOLE":
            console_keywords = ['PS4', 'PS5', 'XBOX', 'NINTENDO', 'SWITCH', 'PS3', 'X360', 'کنسول']
            return any(kw in title_upper for kw in console_keywords)

        return True

    def _format_post_data(self, title, link):
        version_info = "نسخه اصلی / نامشخص"
        title_upper = title.upper()
        
        if 'FITGIRL' in title_upper:
            version_info = "FitGirl Repack"
        elif 'DODI' in title_upper:
            version_info = "DODI Repack"
        elif 'EMPRESS' in title_upper:
            version_info = "EMPRESS"
        elif 'RUNE' in title_upper:
            version_info = "RUNE"
        elif 'TENOKE' in title_upper:
            version_info = "TENOKE"
        elif 'PS5' in title_upper or 'PS4' in title_upper:
            version_info = "کنسول پلی‌استیشن"
        elif 'XBOX' in title_upper:
            version_info = "کنسول ایکس‌باکس"

        return {
            'site': 'دانلودها',
            'title': title,
            'link': link,
            'quality': version_info
        }

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