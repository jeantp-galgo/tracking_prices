"""
Step 1: Extrae y actualiza las URLs de productos de cada marca.
Equivalente a brand_urls.ipynb.

Uso:
    python -m pipeline.run_pipeline
    python -m pipeline.run_pipeline --brands Bajaj
"""
import json
import logging
import argparse
from pathlib import Path

from src.core.scraper.app import ScrapingUtils
from src.core.urls_tracking.urls_tracking import bajaj_filter, italika_filter, compare_urls
from src.config.brand_configs import BRANDS

log = logging.getLogger(__name__)

_FILTERS = {
    "bajaj": bajaj_filter,
    "italika": italika_filter,
}


def fetch_urls_for_brand(brand_name: str) -> list[str]:
    """Extrae URLs actualizadas para una marca y actualiza el JSON local."""
    config = BRANDS[brand_name]
    scraper = ScrapingUtils()

    log.info(f"[{brand_name}] Mapeando URLs en {config['base_url']}")
    urls_scraped = scraper.get_all_urls_from_website(config["base_url"])

    filter_fn = _FILTERS[config["filter"]]
    new_urls = filter_fn(urls_scraped)
    log.info(f"[{brand_name}] {len(new_urls)} URLs filtradas tras scraping")

    json_path = Path("src/data/json/brand_urls") / f"{brand_name.lower()}.json"
    with open(json_path, "r", encoding="utf-8") as f:
        old_urls = json.load(f)["urls"]

    compare_urls(new_urls, old_urls, brand_name)
    return new_urls


def main(brands: list[str] | None = None) -> None:
    brands = brands or list(BRANDS.keys())
    for brand in brands:
        fetch_urls_for_brand(brand)
