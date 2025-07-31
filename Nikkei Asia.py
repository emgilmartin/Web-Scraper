import requests
from bs4 import BeautifulSoup
import feedparser
import time
import webbrowser
from datetime import datetime

HEADERS = {'User-Agent': 'Mozilla/5.0'}
NIKKEI_FEED = 'https://asia.nikkei.com/rss/feed/nar'
STAT_FEED = 'https://www.statnews.com/feed/'
JPANDA_URL = 'https://fuzzypandaresearch.com'
seen = set()

def safe_get(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp
    except requests.exceptions.HTTPError as e:
        print(f"{time.strftime('%H:%M:%S')} | HTTPError for {url} | {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"{time.strftime('%H:%M:%S')} | ConnectionError for {url} | {e}")
    except requests.exceptions.Timeout as e:
        print(f"{time.strftime('%H:%M:%S')} | Timeout for {url} | {e}")
    except requests.exceptions.RequestException as e:
        print(f"{time.strftime('%H:%M:%S')} | RequestException for {url} | {e}")
    return None

def fetch_rss(feed_url, n=5):
    resp = safe_get(feed_url)
    if not resp:
        return []
    return feedparser.parse(resp.content).entries[:n]

def fetch_fuzzypanda_posts():
    resp = safe_get(JPANDA_URL)
    if not resp:
        return []
    soup = BeautifulSoup(resp.content, 'html.parser')
    return [
        {'title': a.get_text(strip=True), 'link': a['href']}
        for a in soup.select('h2.entry-title a')
    ]

def log_item(source, title, link):
    now = time.strftime("%H:%M:%S", time.localtime())
    print(f"{now} | {source} | {title} | {link}")
    try:
        webbrowser.open(link, new=1)
    except Exception as e:
        print(f"{time.strftime('%H:%M:%S')} | Browser open error for {link} | {e}")

def run_scraper():
    while True:
        for entry in fetch_rss(NIKKEI_FEED, 5):
            link = getattr(entry, 'link', None)
            title = getattr(entry, 'title', None)
            if link and title and link not in seen:
                seen.add(link)
                log_item('NikkeiRSS', title, link)

        for entry in fetch_rss(STAT_FEED, 5):
            link = getattr(entry, 'link', None)
            title = getattr(entry, 'title', None)
            if link and title and link not in seen:
                seen.add(link)
                log_item('STAT News', title, link)

        for post in fetch_fuzzypanda_posts():
            link, title = post.get('link'), post.get('title')
            if link and title and link not in seen:
                seen.add(link)
                log_item('Fuzzy Panda Research', title, link)

        time.sleep(10)

if __name__ == '__main__':
    run_scraper()
