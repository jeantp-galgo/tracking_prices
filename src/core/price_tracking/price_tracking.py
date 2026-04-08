"""
Seguimiento de precios con Firecrawl Change Tracking (modo git-diff).
"""

import os
from datetime import datetime, timezone
from typing import Any

from firecrawl import Firecrawl
from src.core.price_tracking.brands import italika, bajaj

_BRAND_HANDLERS = {
    "italika": italika,
    "bajaj": bajaj,
}

def _build_formats(tag: str | None = None) -> list:
    """Construye el array de formats para batch_scrape con changeTracking en modo git-diff."""
    ct: dict[str, Any] = {"type": "changeTracking", "modes": ["git-diff"]}
    if tag:
        ct["tag"] = tag
    return ["markdown", ct]


def _build_row(url: str, brand_name: str, page_data: Any, captured_at: str) -> dict[str, Any]:
    """Construye una fila con las columnas del resultado."""
    brand = _BRAND_HANDLERS[brand_name.strip().lower()]
    ct = getattr(page_data, "changeTracking", None) or getattr(page_data, "change_tracking", None)
    markdown = getattr(page_data, "markdown", "") or ""

    return {
        "brand_name": brand_name,
        "model_name": brand.get_model_name(url, markdown),
        "year_scraped": brand.get_year(url, markdown),
        "url": url,
        "price": brand.get_price(markdown),
        "price_type": brand.PRICE_TYPE,
        "currency": brand.CURRENCY,
        "captured_at": captured_at,
        "change_status": getattr(ct, "changeStatus", "") or getattr(ct, "change_status", "") or "",
        "previous_scrape_at": getattr(ct, "previousScrapeAt", "") or getattr(ct, "previous_scrape_at", "") or "",
        "visibility": getattr(ct, "visibility", "") or "",
    }


def run_price_tracking(urls: list[str], brand_name: str, tag: str | None = None) -> list[dict[str, Any]]:
    """
    Ejecuta seguimiento de precios para una lista de URLs usando Firecrawl Change Tracking.

    Args:
        urls: Lista de URLs de producto a monitorear.
        brand_name: Nombre de la marca (ej. 'italika', 'bajaj').
        tag: Tag para changeTracking. Si no se provee, se genera como '{brand_name}-prices'.

    Returns:
        Lista de dicts con columnas: brand_name, model_name, year_scraped, url, price,
        price_type, currency, captured_at, change_status, previous_scrape_at, visibility.
    """
    if not urls:
        return []

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY no está configurada en las variables de entorno")

    firecrawl = Firecrawl(api_key=api_key)
    effective_tag = tag or f"{brand_name}-prices"
    formats = _build_formats(effective_tag)
    captured_at = datetime.now(timezone.utc).isoformat()

    try:
        result = firecrawl.batch_scrape(
            urls,
            formats=formats,
            only_main_content=True,
            poll_interval=2,
            wait_timeout=300,
        )
    except Exception as e:
        raise RuntimeError(f"Error en batch_scrape: {e}") from e

    data = getattr(result, "data", None)
    if data is None and isinstance(result, list):
        data = result
    if not data:
        return []

    def _normalize_url(u: str) -> str:
        return (u or "").rstrip("/").split("?")[0]

    url_to_item: dict[str, Any] = {}
    for item in data:
        meta = getattr(item, "metadata", None)
        resp_url = getattr(meta, "sourceURL", "") or getattr(meta, "url", "") or ""
        if resp_url:
            url_to_item[_normalize_url(resp_url)] = item

    rows: list[dict[str, Any]] = []
    for i, requested_url in enumerate(urls):
        item = url_to_item.get(_normalize_url(requested_url))
        if item is None and i < len(data):
            item = data[i]
        if item is None:
            continue
        rows.append(_build_row(requested_url, brand_name, item, captured_at))

    return rows
