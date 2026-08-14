import requests
from bs4 import BeautifulSoup
import re

class GameScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'fa,en-US;q=0.7,en;q=0.3',
        }
        # حافظه دائمی برای لینک‌های دیده شده
        self.global_seen_links = set()
        # حافظه Cache برای ذخیره کامل نتایج هر صفحه (کلید: app_page_num)
        self.page_cache = {}
        self.last_query = ""
        self.last_category = ""

    def fetch_page_items(self, query, site_page_num):
        """دریافت خام پست‌های یک صفحه مشخص از دانلودها"""
        cleaned_query = query.strip().replace(' ', '+')
        if site_page_num == 1:
            search_url = f"https://www.downloadha.com/?s={cleaned_query}"
        else:
            search_url = f"https://www.downloadha.com/page/{site_page_num}/?s={cleaned_query}"

        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return [], False

            soup = BeautifulSoup(response.text, 'html.parser')
            posts = soup.select('article.post-box, article.post, div.post, div.post-box, div.content-box, article')
            
            raw_items = []
            for post in posts:
                title_tag = post.select_one('h2 a, h3 a, h1 a, a.title, .post-title a')
                img_tag = post.select_one('img')
                img_src = img_tag.get('data-src') or img_tag.get('src') or '' if img_tag else ''

                cat_tags = post.select('.post-category, .category, .cat-links, .meta-cat, a[rel="category tag"]')
                cat_text = " ".join([c.text.strip() for c in cat_tags])

                if title_tag:
                    title = title_tag.text.strip()
                    post_link = title_tag.get('href', '')
                    if post_link:
                        raw_items.append({
                            'title': title,
                            'link': post_link,
                            'image': img_src,
                            'cat_text': cat_text
                        })

            next_link = soup.select_one('a.next, a.next-page, .pagination .next')
            has_next_site_page = True if next_link else False

            return raw_items, has_next_site_page

        except Exception as e:
            print(f"[Fetch Page Error]: {e}")
            return [], False

    def search_downloadha_paginated(self, query, category="ALL", app_page_num=1, target_count=10):
        # اگر عبارت جدید یا دسته‌بندی جدید انتخاب شد، کل Cache و حافظه تکراری‌ها Reset می‌شود
        if query != self.last_query or category != self.last_category:
            self.global_seen_links.clear()
            self.page_cache.clear()
            self.last_query = query
            self.last_category = category

        # اگر این صفحه قبلاً لود شده، مستقیماً از Cache بازگردانده می‌شود بدون درخواست وب
        if app_page_num in self.page_cache:
            return self.page_cache[app_page_num]

        accumulated_results = []
        current_site_page = (app_page_num - 1) * 2 + 1 
        has_more_site_pages = True

        while len(accumulated_results) < target_count and has_more_site_pages and current_site_page <= 60:
            raw_items, has_more_site_pages = self.fetch_page_items(query, current_site_page)
            
            if not raw_items:
                break

            for item in raw_items:
                if item['link'] in self.global_seen_links:
                    continue

                if self._match_category(item['title'], item['cat_text'], item['link'], category):
                    formatted_item = self._format_post_data(item['title'], item['link'], item['image'], item['cat_text'])
                    accumulated_results.append(formatted_item)
                    self.global_seen_links.add(item['link'])

                if len(accumulated_results) >= target_count:
                    break

            current_site_page += 1

        response_data = {
            'results': accumulated_results,
            'has_next': has_more_site_pages or len(accumulated_results) == target_count,
            'status': 'OK' if accumulated_results else 'EMPTY'
        }

        # ذخیره نتیجه جدید در Cache
        if accumulated_results:
            self.page_cache[app_page_num] = response_data

        return response_data

    def _match_category(self, title, cat_text, link, category):
        if category == "ALL":
            return True

        full_text = (title + " " + cat_text + " " + link).lower()

        software_keywords = [
            'software', 'نرم افزار', 'نرم‌افزار', 'برنامه', 'دانلود نرم', 
            'آموزش', 'مالتی مدیا', 'ویرایشگر', 'سیستم عامل', 'آنتی ویروس',
            'پخش کننده', 'مبدل', 'مدیریت دانلود', 'ابزار', 'طراحی', 'کدک',
            'powerdirector', 'photoshop', 'office', 'windows', 'driver'
        ]
        
        is_software = any(kw in full_text for kw in software_keywords)

        ps_keywords = ['ps4', 'ps5', 'ps3', 'playstation', 'پلی استیشن', 'پلی‌استیشن']
        xbox_keywords = ['xbox', 'x360', 'xbox one', 'series x', 'ایکس باکس', 'ایکس‌باکس']
        nintendo_keywords = ['nintendo', 'switch', 'نینتندو', 'سویچ', 'سوئیچ']

        is_ps = any(kw in full_text for kw in ps_keywords)
        is_xbox = any(kw in full_text for kw in xbox_keywords)
        is_nintendo = any(kw in full_text for kw in nintendo_keywords)
        is_console = is_ps or is_xbox or is_nintendo or ('کنسول' in full_text)

        if category == "CONSOLE_PS": return is_ps
        elif category == "CONSOLE_XBOX": return is_xbox
        elif category == "CONSOLE_NINTENDO": return is_nintendo
        elif category == "CONSOLE_ALL": return is_console

        if category == "PC_ALL":
            return not is_console
        elif category == "PC_GAME":
            return (not is_console) and (not is_software)
        elif category == "PC_SOFTWARE":
            return is_software or ('software' in link.lower() or 'نرم-افزار' in link.lower())

        return False

    def _format_post_data(self, title, link, img_src="", cat_text=""):
        version_info = "نسخه اصلی / کاربردی"
        text_upper = (title + " " + cat_text).upper()

        if 'FITGIRL' in text_upper: version_info = "FitGirl Repack"
        elif 'DODI' in text_upper: version_info = "DODI Repack"
        elif 'EMPRESS' in text_upper: version_info = "EMPRESS"
        elif 'RUNE' in text_upper: version_info = "RUNE"
        elif 'TENOKE' in text_upper: version_info = "TENOKE"
        elif any(k in text_upper for k in ['PS5', 'PS4', 'PLAYSTATION']): version_info = "کنسول پلی‌استیشن"
        elif any(k in text_upper for k in ['XBOX', 'X360']): version_info = "کنسول ایکس‌باکس"
        elif any(k in text_upper for k in ['NINTENDO', 'SWITCH']): version_info = "کنسول نینتندو"
        elif any(k in text_upper for k in ['SOFTWARE', 'نرم افزار', 'برنامه']): version_info = "نرم‌افزار / کاربردی"

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