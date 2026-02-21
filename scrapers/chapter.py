"""
scrapers/chapter.py
Fetches all image URLs for a single chapter from supported manga sources.
Currently supports Mangapill.
"""

import re
import httpx
from bs4 import BeautifulSoup
from constants import BASE_URL, HEADERS, DEFAULT_REQUEST_TIMEOUT
from rich.console import Console

console = Console()

# -------------------------------------------------------
# 🔍 Validate Chapter URL
# -------------------------------------------------------

def validate_chapter_url(url: str) -> bool:
    """
    Checks if a URL looks like a valid Mangapill chapter page.
    Example: https://mangapill.com/chapter/one-piece-chapter-1001
    """
    return bool(re.match(r"^https?://(www\.)?mangapill\.com/chapter/[\w\-]+", url))


# -------------------------------------------------------
# 📸 Extract Chapter Images
# -------------------------------------------------------

def scrape_chapter_images(url: str):
    """
    Scrapes all page image URLs for a given chapter.
    Returns a list of URLs (usually .jpg or .png)
    """
    if not validate_chapter_url(url):
        raise ValueError(f"Invalid chapter URL: {url}")

    console.log(f"🌐 Fetching chapter: {url}")
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=DEFAULT_REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        console.log(f"[red]Failed to fetch chapter page:[/red] {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Try to find all images used in the reader
    image_tags = soup.select("img[src*='/manga/']") or soup.find_all("img")

    images = []
    for img in image_tags:
        src = img.get("data-src") or img.get("src")
        if not src:
            continue
        if not src.startswith("http"):
            src = BASE_URL + src
        if src not in images:
            images.append(src)

    console.log(f"🖼️ Found {len(images)} pages for chapter {url.split('/')[-1]}")
    return images


# -------------------------------------------------------
# 🧩 Example usage
# -------------------------------------------------------

if __name__ == "__main__":
    test_url = "https://mangapill.com/chapter/one-piece-chapter-1001"
    imgs = scrape_chapter_images(test_url)
    print(f"Found {len(imgs)} images:")
    for i, img in enumerate(imgs[:5], 1):
        print(f"{i}. {img}")
