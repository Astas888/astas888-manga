"""
Scrapers package for Astas888 Manga.
Contains site-specific and general scraping utilities.
"""

from .manga import scrape_manga, validate_manga_url
# from .chapter import scrape_chapter  # Uncomment if you add chapter scraping

__all__ = [
    "scrape_manga",
    "validate_manga_url",
    # "scrape_chapter",
]
