import requests
from bs4 import BeautifulSoup
import feedparser
import time
from datetime import datetime
import webbrowser

def fetch_latest_morpheus():
    url = "https://www.morpheus-research.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Morpheus Fetch Error: {e}")
        return None, None

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the most recent report title and link
    post = soup.find("h2", class_="post-title")
    if not post:
        return None, None

    headline = post.get_text(strip=True)
    link = post.find("a")["href"] if post.find("a") else None

    return headline, link

def monitor_morpheus(interval=5):
    last_seen = None

    while True:
        headline, link = fetch_latest_morpheus()

        if headline and headline != last_seen:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"{now} | Morpheus Research | {headline} | {link}")

            if link:
                webbrowser.open(link)

            last_seen = headline

        time.sleep(interval)

if __name__ == "__main__":
    monitor_morpheus(interval=1)