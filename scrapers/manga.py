"""
scrapers/manga.py
Scrapes manga metadata and chapter listings from supported sources (e.g. Mangapill).
"""

import re
import httpx
from bs4 import BeautifulSoup
from constants import BASE_URL, HEADERS, DEFAULT_REQUEST_TIMEOUT
from rich.console import Console

console = Console()

# -------------------------------------------------------
# 🧩 URL Validation
# -------------------------------------------------------

def validate_manga_url(url: str) -> bool:
    """
    Ensure the provided URL matches known manga patterns.
    Example: https://mangapill.com/manga/one-piece
    """
    return bool(re.match(r"^https?://(www\.)?mangapill\.com/manga/[\w\-]+", url))


# -------------------------------------------------------
# 🧠 Manga Scraper
# -------------------------------------------------------

def scrape_manga(url: str):
    """
    Scrapes manga info and chapter list from Mangapill.
    Returns a dict with:
    {
      "title": str,
      "author": str | None,
      "description": str | None,
      "chapters": [{"title":..., "url":...}, ...]
    }
    """
    if not validate_manga_url(url):
        raise ValueError(f"Invalid Mangapill URL: {url}")

    console.log(f"🌐 Fetching manga page: {url}")
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=DEFAULT_REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        console.log(f"[red]Failed to fetch manga page:[/red] {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract manga title
    title_tag = soup.find("h1", class_="text-2xl") or soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Unknown Title"

    # Author
    author_tag = soup.find(string=re.compile("Author"))
    author = author_tag.find_next("a").text.strip() if author_tag else None

    # Description
    desc_tag = soup.find("div", class_="manga-description") or soup.find("p")
    description = desc_tag.text.strip() if desc_tag else None

    # Chapter list
    chapters = []
    for a in soup.select("a[href*='/chapter/']"):
        href = a.get("href")
        ch_title = a.text.strip()
        if not href:
            continue
        ch_url = href if href.startswith("http") else BASE_URL + href
        chapters.append({
            "title": ch_title or href.split("/")[-1],
            "url": ch_url,
        })

    chapters = list({c["url"]: c for c in chapters}.values())  # dedupe
    chapters.sort(key=lambda x: x["url"])  # ensure order

    console.log(f"✅ Found {len(chapters)} chapters for {title}")

    return {
        "title": title,
        "author": author,
        "description": description,
        "chapters": chapters,
    }
