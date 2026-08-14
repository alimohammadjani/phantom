import requests
from bs4 import BeautifulSoup
import re

class GameScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'fa,en-US;q=0.7,en;q=0.3',
        }

    def search_downloadha(self, query):
        """مرحله ۱: جستجوی عمومی و استخراج تمام کارت‌ها/پست‌ها"""
        results = []
        search_url = f"https://www.downloadha.com/?s={query.strip().replace(' ', '+')}"

        try:
            response = requests.get(search_url, headers=self.headers, timeout=12)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # روش‌های مختلف پیدا کردن پست‌ها در ساختار جدید یا قدیمی دانلودها
                posts = soup.select('article.post-box, article.post, div.post, div.post-box, div.content-box')
                
                # اگر با روش بالا پیدا نشد، از طریق پیدا کردن تمام تیترهای لینک‌دار عمل کن
                if not posts:
                    titles = soup.select('h2.title a, h2.entry-title a, h3.title a, h2 a')
                    for a_tag in titles:
                        href = a_tag.get('href', '')
                        title = a_tag.text.strip()
                        if href and title and ('downloadha.com' in href or href.startswith('/')):
                            results.append(self._format_post_data(title, href))
                    return results

                for post in posts:
                    title_tag = post.select_one('h2 a, h3 a, h1 a, a.title')
                    if title_tag:
                        title = title_tag.text.strip()
                        post_link = title_tag.get('href', '')
                        if post_link:
                            results.append(self._format_post_data(title, post_link))

        except Exception as e:
            print(f"[Search Error]: {e}")

        return results

    def _format_post_data(self, title, link):
        """تشخیص نسخه از روی تیتر برای نمایش اولیه"""
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
        elif 'ELAMIGOS' in title_upper:
            version_info = "ElAmigos"

        return {
            'site': 'دانلودها',
            'title': title,
            'link': link,
            'quality': version_info
        }

    def fetch_post_download_links(self, post_url):
        """مرحله ۲: استخراج لینک‌ها از تمام فرم‌ها و باکس‌های داخل پست"""
        download_data = {
            'links': [],
            'password': 'www.downloadha.com'
        }

        try:
            response = requests.get(post_url, headers=self.headers, timeout=12)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # ۱. پیدا کردن تمام بخش‌ها، فرم‌ها و باکس‌های دانلود (files-list, download-box و...)
                download_sections = soup.select('.files-list, .download-box, .entry-content, .box-download, .dl-box')
                
                search_area = soup
                if download_sections:
                    # اگر باکس پیدا شد، جستجو رو محدود به اون کن
                    search_area = download_sections[0]

                # ۲. پیدا کردن تمام لینک‌های مستقیم فایل (rar, zip, iso, exe, 7z و...)
                a_tags = search_area.find_all('a', href=True)
                
                for a in a_tags:
                    href = a['href'].strip()
                    text = a.text.strip() or "لینک دانلود"
                    
                    # فیلتر کردن لینک‌های مستقیم دانلود
                    if re.search(r'\.(rar|zip|iso|exe|7z|bin|mkv)(\?.*)?$', href, re.IGNORECASE):
                        # جلوگیری از لینک‌های تکراری
                        if not any(link['url'] == href for link in download_data['links']):
                            download_data['links'].append({
                                'text': text,
                                'url': href
                            })

        except Exception as e:
            print(f"[Details Error]: {e}")

        return download_data