from scrapers.manga import scrape_manga, validate_manga_url

class MangapillSource:
    name = "mangapill"
    base_url = "https://mangapill.com"

    @staticmethod
    def scrape(url: str):
        return scrape_manga(url)

    @staticmethod
    def validate(url: str):
        return validate_manga_url(url)
