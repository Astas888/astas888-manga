"""
Downloader package for Astas888 Manga.
Handles async chapter/image downloading, retry logic, and rate limiting.
"""

from .async_manager import AsyncDownloadManager

__all__ = ["AsyncDownloadManager"]
