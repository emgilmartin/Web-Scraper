import requests
import feedparser
import time
import sched
import re
import json
import colorama

USER_AGENT = "Elizabeth Gilmartin (egilmartin@trlm.com) - Python EDGAR Scraper v1.0"
HEADERS = {
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov",
        "Connection": "keep-alive"
    }

FEED_URL = ("https://www.sec.gov/cgi-bin/browse-edgar"
            "?action=getcurrent&CIK=&type=&company=&dateb=&owner=include"
            "&start=0&count=100&output=atom")

seen = set()
scheduler = sched.scheduler(time.time, time.sleep)
item_pattern = re.compile(r"Item\s+(\d+\.\d+)")

def load_ticker_mapping(path="company_tickers_exchange.json"):
    with open(path, "r", encoding="utf-8") as f:
        j = json.load(f)
    mapping = {}
    data = j.get("data", [])
    for row in data:
        cik_str = str(int(row[0]))   # removes leading zeros
        ticker = row[2]
        mapping[cik_str] = ticker
    return mapping

ticker_map = load_ticker_mapping()

def normalize_ticker(ticker):
    # remove letters trailing -
    if isinstance(ticker, str):
        ticker = ticker.split("-", 1)[0]
    # Only strip trailing W if it's exactly the 5th character in a 5-letter ticker
    if isinstance(ticker, str) and len(ticker) == 5 and ticker.endswith("W"):
        return ticker[:-1]
    return ticker

def safe_get(url, retries=3, delay=5):
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=(5,20))
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 403 and attempt < retries:
                print(f"{time.strftime('%H:%M:%S')} | 403 for {url}, retry {attempt}/{retries}")
                time.sleep(delay)
                delay *= 2
                continue
            print(f"{time.strftime('%H:%M:%S')} | HTTPError {resp.status_code} for {url} | {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"{time.strftime('%H:%M:%S')} | RequestException for {url} | {e}")
            return None
    return None


def scrape_edgar():
    resp = safe_get(FEED_URL)
    if resp:
        feed = feedparser.parse(resp.content)
        for entry in feed.entries:
            title = getattr(entry, 'title', '')
            link = getattr(entry, 'link', '')
            if  any(k in title for k in ("8-K", "6-K"))  and link not in seen:
                seen.add(link)

                # Extract items from title
                parts = title.split('Item')
                items_title = [part.strip().split()[0].strip(',:;.') for part in parts[1:]]
                items_str_title = ", ".join(items_title) if items_title else "N/A"

                # Extract items using regex on summary or HTML snippet
                summary_html = getattr(entry, 'summary', '')
                items_found = item_pattern.findall(summary_html)
                items_str = ", ".join(items_found) if items_found else items_str_title

                now = time.strftime("%H:%M:%S", time.localtime())

                cik_match = re.search(r'\((0*)(\d+)\)', title)
                if cik_match:
                    cik = cik_match.group(2)  # stripped zeros
                    ticker = ticker_map.get(cik)
                    ticker = normalize_ticker(ticker)
                    if not ticker:
                        continue  # skip if ticker not found

                print(f"{now} |  {ticker} |  {title} | {items_str} | {link}")


    # Reschedule the next run
    scheduler.enter(0.1, 1, scrape_edgar)

def main():
    scheduler.enter(0, 1, scrape_edgar)
    try:
        scheduler.run()
    except KeyboardInterrupt:
        print("Stopped by user.")

if __name__ == '__main__':
    main()
