"""
Seguimiento de precios con Firecrawl Change Tracking (modo git-diff).
Extrae precio actual desde markdown con regex y metadata de cambio desde changeTracking.
No usa modo JSON — sin costo adicional por página.
"""

import os
import re
from datetime import datetime, timezone
from typing import Any


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Acceso seguro a atributo o clave dict."""
    if obj is None:
        return default
    if hasattr(obj, key):
        return getattr(obj, key, default)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def _build_formats(tag: str | None = None) -> list:
    """Construye el array de formats para batch_scrape con changeTracking en modo git-diff."""
    ct: dict[str, Any] = {"type": "changeTracking", "modes": ["git-diff"]}
    if tag:
        ct["tag"] = tag
    return ["markdown", ct]


def _model_name_from_url(url: str) -> str:
    """Deriva model_name desde el slug de la URL, removiendo IDs numéricos finales."""
    url = url.rstrip("/")
    if "/p" in url:
        url = url.split("/p")[0]
    segment = url.split("/")[-1] if "/" in url else url
    # Quitar sufijos numéricos largos (ej. -34006713 o -34006713-1300703478)
    segment = re.sub(r"(-\d{6,})+$", "", segment)
    return segment.replace("-", " ").strip() or url


def _find_all_prices_in_markdown(markdown: str) -> list[tuple[str, int]]:
    """Devuelve todos los precios encontrados en el markdown y su posición. [(precio, start), ...]."""
    if not markdown or not isinstance(markdown, str):
        return []
    patterns = [
        r"\$\s*([\d,]+(?:\.\d{2})?)",
        r"([\d]{1,3}(?:,[\d]{3})*(?:\.[\d]{2})?)\s*MXN",
        r"([\d]{1,3}(?:\.[\d]{3})*(?:,[\d]{2})?)\s*MXN",
        r"precio[:\s]+[\$]?\s*([\d,\.]+)",
    ]
    out: list[tuple[str, int]] = []
    for pat in patterns:
        for m in re.finditer(pat, markdown, re.IGNORECASE):
            out.append((m.group(1).strip(), m.start()))
    return sorted(out, key=lambda x: x[1])


def parse_price_from_markdown(markdown: str, prefer_second: bool = True) -> str:
    """
    Extrae precio del markdown. Si prefer_second y hay al menos 2 matches, devuelve el segundo.
    En Italika el primer precio suele ser "Pago de contado" y el segundo el precio oferta vigente.
    """
    all_matches = _find_all_prices_in_markdown(markdown)
    if not all_matches:
        return ""
    if prefer_second and len(all_matches) >= 2:
        return all_matches[1][0]
    return all_matches[0][0]


def _build_row(
    url: str,
    brand_name: str,
    page_data: Any,
    captured_at: str,
) -> dict[str, Any]:
    """Construye una fila con las 10 columnas alineadas al PRD."""
    ct = _get(page_data, "changeTracking") or _get(page_data, "change_tracking")
    markdown = _get(page_data, "markdown") or ""

    return {
        "brand_name": brand_name,
        "model_name": _model_name_from_url(url),
        "url": url,
        "price": parse_price_from_markdown(markdown),
        "price_type": "contado",
        "currency": "MXN",
        "captured_at": captured_at,
        "change_status": _get(ct, "changeStatus") or _get(ct, "change_status") or "",
        "previous_scrape_at": _get(ct, "previousScrapeAt") or _get(ct, "previous_scrape_at") or "",
        "visibility": _get(ct, "visibility") or "",
    }


def run_price_tracking(
    urls: list[str],
    brand_name: str,
    tag: str | None = None,
) -> list[dict[str, Any]]:
    """
    Ejecuta seguimiento de precios para una lista de URLs usando Firecrawl Change Tracking.

    Args:
        urls: Lista de URLs de producto a monitorear.
        brand_name: Nombre de la marca (ej. 'italika'). Se usa como prefijo del tag por defecto.
        tag: Tag opcional para changeTracking. Permite mantener historiales separados
             por frecuencia de ejecución (ej. 'italika-daily'). Si no se provee,
             se genera como '{brand_name}-prices'.

    Returns:
        Lista de dicts con 10 columnas: brand_name, model_name, url, price, price_type,
        currency, captured_at, change_status, previous_scrape_at, visibility.
    """
    if not urls:
        return []

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY no está configurada en las variables de entorno")

    from firecrawl import Firecrawl

    firecrawl = Firecrawl(api_key=api_key)
    effective_tag = tag or f"{brand_name}-prices"
    formats = _build_formats(effective_tag)

    # captured_at es el mismo para todos los registros de una misma ejecución
    captured_at = datetime.now(timezone.utc).isoformat()

    try:
        # onlyMainContent debe ser consistente entre ejecuciones para comparaciones confiables
        result = firecrawl.batch_scrape(
            urls,
            formats=formats,
            only_main_content=True,
            poll_interval=2,
            wait_timeout=300,
        )
    except Exception as e:
        raise RuntimeError(f"Error en batch_scrape: {e}") from e

    data = _get(result, "data")
    if data is None and isinstance(result, list):
        data = result
    if not data:
        return []
    if isinstance(data, dict):
        data = [data]

    # Emparejar respuestas por URL normalizada para tolerar reordenamientos en el batch
    def _normalize_url(u: str) -> str:
        return (u or "").rstrip("/").split("?")[0]

    url_to_item: dict[str, Any] = {}
    for item in data:
        meta = _get(item, "metadata")
        resp_url = _get(meta, "sourceURL") or _get(meta, "url") or ""
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
