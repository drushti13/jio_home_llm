import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time
import json

# ----------------- CONFIG -----------------

DOMAIN = "www.jio.com"

# Manually chosen starting URLs (you can add/remove here)
START_URLS = [
    "https://www.jio.com/jiohome",
    "https://www.jio.com/jiohome/apps",
    "https://www.jio.com/jiohome/devices",
    "https://www.jio.com/apps/jiogames",
    "https://www.jio.com/apps/jiocinema",
    "https://www.jio.com/apps/jiotv",
    "https://www.jio.com/apps/jiocloud",
    "https://www.jio.com/apps/jiosaavn",
    "https://www.jio.com/apps/myjio",
    "https://www.jio.com/mobile/",
    "https://www.jio.com/5g/",
    "https://www.jio.com/international-services/",
   
]


# Paths we *allow* the crawler to stay in
ALLOWED_PREFIXES = [
    "/jiohome",
    "/apps/jiogames",
    "/mobile",
    "/5g",
    "/international-services",
     "/apps",
]

# Paths we *never* want to crawl
DISALLOWED_SUBSTRINGS = [
    "/selfcare/",
    "/faq/",
    "/survey/",
    "/shop/cart",
    "/shop/checkout",
    "/shop/search",
    "/en-in/search",
    "/login",
    "/signin",
    "/account",
    "/myaccount",
    "/paybill",
    "/help/",
    "/apps/jiocall",   # explicitly disallowed in robots.txt
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (student-project; https://www.jio.com/)"
}

MAX_PAGES = 120    # safety cap
DELAY = 1.0       # seconds between requests
OUTPUT_FILE = "jio_scraped_bs4.jsonl"

# ------------------------------------------


def normalize_url(url: str) -> str:
    """
    Normalize URL so we don't get duplicates like:
    https://www.jio.com/jiohome  and  https://www.jio.com/jiohome/
    Also trims accidental spaces.
    """
    url = url.strip()
    parsed = urlparse(url)
    # remove fragment (#...)
    parsed = parsed._replace(fragment="")
    # rebuild URL and strip trailing slash
    normalized = parsed.geturl().rstrip("/")
    return normalized


def is_allowed_url(url: str) -> bool:
    """
    Decide whether a URL should be scraped:
    - must be on www.jio.com
    - must not contain disallowed substrings
    - path must start with one of ALLOWED_PREFIXES
    """
    parsed = urlparse(url)
    if parsed.netloc != DOMAIN:
        return False

    path = parsed.path or "/"

    # Block any clearly disallowed path parts
    for bad in DISALLOWED_SUBSTRINGS:
        if bad in path:
            return False

    # Allow only inside our selected sections
    if any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return True

    return False


def clean_page(html: str, url: str):
    """
    Remove scripts/styles, return (title, text, soup)
    """
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else url
    text = " ".join(soup.get_text(separator=" ").split())

    return title, text, soup


def crawl():
    visited = set()
    queue = deque()

    # Seed initial queue with normalized START_URLS
    for u in START_URLS:
        nu = normalize_url(u)
        queue.append(nu)

    pages = []

    while queue and len(pages) < MAX_PAGES:
        url = queue.popleft()
        url = normalize_url(url)

        if url in visited:
            continue
        visited.add(url)

        if not is_allowed_url(url):
            # print("Skipping:", url)
            continue

        print(f"Scraping: {url}")
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            res.raise_for_status()
        except Exception as e:
            print(f"Error fetching {url} -> {e}")
            continue

        title, text, soup = clean_page(res.text, url)

        pages.append({
            "url": url,
            "title": title,
            "text": text,
        })

        # Discover more links from this page
        for a in soup.find_all("a", href=True):
            link = urljoin(url, a["href"])
            link = normalize_url(link)

            if link not in visited and is_allowed_url(link):
                queue.append(link)

        time.sleep(DELAY)

    return pages


if __name__ == "__main__":
    data = crawl()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for p in data:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"\nDone. Saved {len(data)} pages to {OUTPUT_FILE}")
