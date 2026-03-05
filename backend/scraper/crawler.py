import os
from firecrawl import Firecrawl


class Crawler():
    """
    scrapes from the shopify stores
    """
    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise RuntimeError("FIRECRAWL API KEY not set")

        self.firecrawl = Firecrawl(api_key)

    def crawl_website(self, store_url: str) -> list[str]:
        response = self.firecrawl.map(url = store_url, search = 'products', limit = 1000)
        if not response or not hasattr(response, "links"):
            return []
        return list(set(response.links))
    







