from typing import List, Optional


def filter_product_urls(
    urls: List[str],
    exclude_terms: Optional[List[str]] = None,
    suffix: str = "/p",
) -> List[str]:
    """Filtra una lista de URLs para quedarse solo con páginas de producto.

    Args:
        urls: Lista de URLs obtenida del map del sitio.
        exclude_terms: Términos que, si aparecen en la URL (case-insensitive),
            la descartan. Por ejemplo: ['morbidelli'].
        suffix: Sufijo que debe tener la URL para considerarse producto.
            Por defecto '/p' (convención de VTEX).

    Returns:
        Lista de URLs que pasan todos los filtros.
    """
    exclude_terms = [t.lower() for t in (exclude_terms or [])]

    result = []
    for url in urls:
        url_lower = url.lower()
        if any(term in url_lower for term in exclude_terms):
            continue
        if not url.endswith(suffix):
            continue
        result.append(url)

    return result
