from .mangapill_source import MangapillSource

def find_source_for_url(url: str):
    if "mangapill.com" in url:
        return MangapillSource
    return None
