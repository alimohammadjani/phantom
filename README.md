# Game Searcher Pro

A lightweight Python desktop application built with PyQt6 for searching, filtering, and extracting download links from DownloadHa for games and software.

It scrapes post details in real-time, displays item metadata and thumbnail covers, and exposes direct download links with archive passwords—all in a single clean UI.

---

## Features

- **Fast Multi-Threaded Scraping**: Network requests run on background threads (`QThread`), keeping the UI smooth and non-blocking.
- **Smart Category Filtering**:
  - **Console**: PlayStation (PS4/PS5), Xbox, Nintendo Switch.
  - **PC**: Games, Software, or both.
- **Direct Link Extractor**: Parses post pages and lists direct downloadable archive links (`.rar`, `.zip`, `.iso`, etc.) along with extraction passwords.
- **Image Caching & Async Loading**: Loads post cover art asynchronously without lagging the application.
- **Pagination & In-Memory Cache**: Built-in caching for search queries and pages to avoid redundant requests.

---

## Tech Stack

- **GUI**: PyQt6
- **Web Scraping**: BeautifulSoup4, Requests
- **Language**: Python 3.9+

---


## Installation & Setup

### 1. Clone the repository
git clone https://github.com/your-username/game-searcher-pro.git
cd game-searcher-pro

### 2. Set up a Virtual Environment (Recommended)

Linux / macOS:
python3 -m venv venv
source venv/bin/activate

Windows:
python -m venv venv
venv\Scripts\activate

### 3. Install Dependencies
pip install -r requirements.txt

---

## How to Run

Execute the entry file:

python main.py

1. Enter the title of the game or program in the search bar.
2. Select a category filter (Console / PC) if needed.
3. Click Search or press Enter.
4. Click "📂 مشاهده و دریافت لینک‌های دانلود" on any card to view available direct links and archive passwords.
