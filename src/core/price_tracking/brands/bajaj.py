from src.core.price_tracking.utils import _model_name_from_markdown, _model_name_from_url, _extract_year_from_text, parse_price_from_markdown

# Constantes usadas en price_tracking.py - build_rows
PRICE_TYPE = "oferta"
CURRENCY = "MXN"


def get_model_name(url: str, markdown: str) -> str:
    return _model_name_from_markdown(markdown) or _model_name_from_url(url)


def get_year(url: str, markdown: str) -> int | None:
    return _extract_year_from_text(markdown) or _extract_year_from_text(url) or 2026


def get_price(markdown: str) -> str:
    return parse_price_from_markdown(markdown, prefer_offer_keyword=True)
