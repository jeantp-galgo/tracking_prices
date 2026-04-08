import re
from urllib.parse import urlparse


def _model_name_from_url(url: str) -> str:
    """Deriva model_name desde el slug de la URL, removiendo IDs numéricos finales."""
    parsed = urlparse((url or "").strip())
    path = parsed.path.rstrip("/")
    if path.endswith("/p"):
        path = path[:-2]
    segment = path.split("/")[-1] if "/" in path else path
    segment = re.sub(r"(-\d{6,})+$", "", segment)
    return segment.replace("-", " ").strip() or (url or "").strip()


def _model_name_from_markdown(markdown: str) -> str:
    """Extrae nombre de modelo desde encabezados H1/H2 del markdown."""
    if not markdown or not isinstance(markdown, str):
        return ""

    candidates = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        title = re.sub(r"^#{1,6}\s*", "", stripped).strip()
        if not title:
            continue
        lowered = title.lower()
        if lowered in {"top of page", "bottom of page", "whatsapp"}:
            continue
        if "precio" in lowered and "$" in title:
            continue
        candidates.append(title)

    for candidate in candidates:
        if re.search(r"[a-zA-Z].*\d|\d.*[a-zA-Z]", candidate) and len(candidate) <= 80:
            return candidate
    return candidates[0] if candidates else ""


def _extract_year_from_text(text: str) -> int | None:
    """Extrae año de modelo de un texto. Prioriza frases 'Modelo 20XX', si no toma el primero disponible."""
    if not text or not isinstance(text, str):
        return None

    for pattern in [r"modelo(?:\s+de)?\s*(20\d{2})", r"model\s*year\s*(20\d{2})"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            year = int(match.group(1))
            if 2020 <= year <= 2035:
                return year

    for raw in re.findall(r"\b(20\d{2})\b", text):
        year = int(raw)
        if 2020 <= year <= 2035:
            return year

    return None


def _find_all_prices_in_markdown(markdown: str) -> list[tuple[str, int]]:
    """Devuelve todos los precios encontrados en el markdown y su posición."""
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


def _extract_offer_price(markdown: str) -> str:
    """Prioriza el precio asociado a texto de oferta en el markdown."""
    if not markdown or not isinstance(markdown, str):
        return ""
    patterns = [
        r"\$\s*([\d,]+(?:\.\d{2})?)\s*precio\s*de\s*oferta",
        r"precio\s*de\s*oferta\s*\$?\s*([\d,]+(?:\.\d{2})?)",
    ]
    for pat in patterns:
        match = re.search(pat, markdown, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def parse_price_from_markdown(markdown: str, prefer_second: bool = True, prefer_offer_keyword: bool = False) -> str:
    """Extrae precio del markdown."""
    if prefer_offer_keyword:
        offer_price = _extract_offer_price(markdown)
        if offer_price:
            return offer_price

    all_matches = _find_all_prices_in_markdown(markdown)
    if not all_matches:
        return ""
    if prefer_second and len(all_matches) >= 2:
        return all_matches[1][0]
    return all_matches[0][0]
