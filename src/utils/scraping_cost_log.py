from datetime import datetime
from typing import Any

import pandas as pd

_COST_LOG_COLUMNS = [
    "run_date",
    "run_timestamp",
    "brand",
    "step_url_mapping",
    "urls_url_mapping",
    "credits_url_mapping",
    "step_url_scrapping",
    "urls_url_scrapping",
    "credits_url_scrapping",
    "credits_total",
]


def build_cost_entry(
    brand: str,
    urls_url_mapping: int,
    credits_url_mapping: int,
    urls_url_scrapping: int,
    credits_url_scrapping: int,
    run_timestamp: str,
) -> dict[str, Any]:
    """Construye una fila consolidada para el log de creditos Firecrawl."""
    urls_mapping = int(urls_url_mapping)
    mapping = int(credits_url_mapping)
    urls_scrapping = int(urls_url_scrapping)
    scrapping = int(credits_url_scrapping)
    run_date = datetime.fromisoformat(run_timestamp).date().isoformat()
    return {
        "run_date": run_date,
        "run_timestamp": run_timestamp,
        "brand": brand,
        "step_url_mapping": "url_mapping",
        "urls_url_mapping": urls_mapping,
        "credits_url_mapping": mapping,
        "step_url_scrapping": "url_scrapping",
        "urls_url_scrapping": urls_scrapping,
        "credits_url_scrapping": scrapping,
        "credits_total": mapping + scrapping,
    }


def append_cost_log(entries: list[dict[str, Any]], gsheets: Any, sheet_name: str, worksheet: str) -> pd.DataFrame:
    """
    Agrega filas de costo de scraping a una hoja de Google Sheets.

    Fuente de pricing: docs/.firecrawl/firecrawl-billing.md.
    """
    if not entries:
        return pd.DataFrame(columns=_COST_LOG_COLUMNS)

    df = pd.DataFrame(entries)
    existing_cols = [c for c in _COST_LOG_COLUMNS if c in df.columns]
    df_to_write = df[existing_cols]

    gsheets.update_sheet(
        {
            "sheet_name": sheet_name,
            "worksheet": worksheet,
            "df": df_to_write,
        },
        clear_data=False,
    )
    return df_to_write
