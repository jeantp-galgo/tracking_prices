from src.core.price_tracking.utils import _model_name_from_url, parse_price_from_markdown

PRICE_TYPE = "contado"
CURRENCY = "MXN"


def get_model_name(url: str, markdown: str) -> str:
    return _model_name_from_url(url)


def get_year(url: str, markdown: str) -> int | None:
    return 2026  # Italika no muestra año en página


def get_price(markdown: str) -> str:
    return parse_price_from_markdown(markdown, prefer_second=True)
