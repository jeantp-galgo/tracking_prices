import os
from firecrawl import Firecrawl
from src.core.scraper.utils import get_urls_from_firecrawl_map

class ScrapingUtils:
    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        self.firecrawl = Firecrawl(api_key=self.api_key)

    def get_all_urls_from_website(self, url: str):
        """ Trae todas las URLs de un sitio web """
        url_list = self.firecrawl.map(url=url)
        return get_urls_from_firecrawl_map(url_list)

    def scrape_url(self, url: str, **kwargs):
        """ Scrapea una URL """
        return self.firecrawl.scrape(url=url, **kwargs)