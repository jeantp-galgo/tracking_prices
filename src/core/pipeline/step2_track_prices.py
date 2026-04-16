"""
Step 2: Scraping de precios y comparación contra inventario.
Equivalente a tracking_prices.ipynb.

Uso:
    python -m pipeline.run_pipeline
    python -m pipeline.run_pipeline --brands Bajaj
"""
import json
import logging
from pathlib import Path

import pandas as pd

from src.config.settings import COUNTRY
from src.config.brand_configs import BRANDS, GSHEETS_INVENTORY, GSHEETS_OUTPUT_SHEET, LOG_PATH
from src.core.price_tracking.price_tracking import run_price_tracking
from src.utils.clean_model_name import clean_model_name
from src.utils.replace_model_name import map_model_name, load_mapping_file
from src.core.italika_pipeline import build_price_comparison
from src.sources.sheets.reader import GoogleSheetReader
from src.utils.price_diff_log import append_price_diff_log

log = logging.getLogger(__name__)


def load_urls(brand_name: str) -> list[str]:
    """Carga URLs desde el JSON local de la marca, deduplicando."""
    json_path = Path("src/data/json/brand_urls") / f"{brand_name.lower()}.json"
    with open(json_path, "r", encoding="utf-8") as f:
        urls = json.load(f)["urls"]
    seen: set[str] = set()
    return [u for u in urls if not (u in seen or seen.add(u))]  # type: ignore[func-returns-value]


def load_inventory(gsheets: GoogleSheetReader, brand_name: str) -> pd.DataFrame:
    """Lee el inventario desde Google Sheets y filtra por marca y status activo."""
    df = gsheets.read_sheet(GSHEETS_INVENTORY)
    df = df[df["brand"] == brand_name]
    df = df[df["status"].isin(["available", "no_stock"])]
    return df.reset_index(drop=True)


def prepare_scraped_df(df: pd.DataFrame, brand_name: str) -> pd.DataFrame:
    """Limpia nombres y aplica mapeo de modelos al DataFrame scrapeado."""
    df = df.copy()
    df["year_scraped"] = pd.to_numeric(df.get("year_scraped"), errors="coerce").astype("Int64")
    df["model_name_clean"] = df["model_name"].apply(
        lambda m: clean_model_name(m, brand_name=brand_name)
    )
    mapeo = load_mapping_file(COUNTRY, brand_name)
    df["model_mapped"] = df["model_name_clean"].apply(lambda x: map_model_name(x, mapeo))
    df["model_mapped"] = df["model_mapped"].str.lower()
    return df


def track_prices_for_brand(brand_name: str, gsheets: GoogleSheetReader) -> pd.DataFrame:
    """Ejecuta el pipeline completo de tracking para una marca."""
    config = BRANDS[brand_name]

    urls = load_urls(brand_name)
    if not urls:
        raise ValueError(f"[{brand_name}] No hay URLs disponibles en el JSON local.")
    log.info(f"[{brand_name}] {len(urls)} URLs cargadas")

    df_inventory = load_inventory(gsheets, brand_name)
    log.info(f"[{brand_name}] {len(df_inventory)} filas de inventario cargadas")

    log.info(f"[{brand_name}] Ejecutando batch scrape...")
    rows = run_price_tracking(urls=urls, brand_name=brand_name)
    df_scraped = prepare_scraped_df(pd.DataFrame(rows), brand_name)
    log.info(f"[{brand_name}] {len(df_scraped)} URLs scrapeadas")

    df_final = build_price_comparison(
        df_scraped,
        df_inventory,
        COUNTRY,
        galgo_fee=config["galgo_fee"],
    )

    gsheets.update_sheet(
        {
            "sheet_name": GSHEETS_OUTPUT_SHEET,
            "worksheet": brand_name,
            "df": df_final.sort_values(by="model_name"),
        },
        clear_data=True,
    )
    log.info(f"[{brand_name}] {len(df_final)} filas escritas en Google Sheets")

    rows_logged = append_price_diff_log(df_final, LOG_PATH)
    if rows_logged:
        log.info(f"[{brand_name}] {rows_logged} diferencias de precio registradas en log")

    return df_final


def main(brands: list[str] | None = None) -> None:
    gsheets = GoogleSheetReader()
    brands = brands or list(BRANDS.keys())
    for brand in brands:
        track_prices_for_brand(brand, gsheets)
