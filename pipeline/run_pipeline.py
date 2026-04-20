"""
Punto de entrada del pipeline de tracking de precios.

Uso:
    python -m pipeline.run_pipeline                     # Todas las marcas, ambos steps
    python -m pipeline.run_pipeline --brands Bajaj      # Solo Bajaj
    python -m pipeline.run_pipeline --skip-step1        # Usar JSONs existentes (ahorra créditos Firecrawl)
"""
import sys
import os
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from src.config.brand_configs import (
    BRANDS,
    GSHEETS_OUTPUT_SHEET,
    GSHEETS_COSTS_WORKSHEET,
    LOG_PATH,
)
from src.config.settings import APP_ENV
from src.core.pipeline.preflight import PreflightError, run_preflight_checks
from src.core.pipeline.step1_fetch_urls import main as step1
from src.core.pipeline.step2_track_prices import main as step2
from src.notifications.email_notifier import send_price_diff_email
from src.sources.sheets.reader import GoogleSheetReader
from src.utils.scraping_cost_log import append_cost_log, build_cost_entry

log = logging.getLogger(__name__)


def _mask_secret(value: str) -> str:
    """Oculta secretos en logs dejando visibles solo ultimos 4 caracteres."""
    if not value:
        return "(vacia)"
    return f"...{value[-4:]}"


def _consolidate_cost_entries(
    brands: list[str],
    run_timestamp: str,
    mapping_entries: list[dict],
    scrapping_entries: list[dict],
) -> list[dict]:
    """Consolida costos por marca en una sola fila por corrida."""
    by_brand = {
        brand: {
            "urls_url_mapping": 0,
            "credits_url_mapping": 0,
            "urls_url_scrapping": 0,
            "credits_url_scrapping": 0,
        }
        for brand in brands
    }

    for entry in mapping_entries:
        brand = entry.get("brand")
        if not brand:
            continue
        if brand not in by_brand:
            by_brand[brand] = {
                "urls_url_mapping": 0,
                "credits_url_mapping": 0,
                "urls_url_scrapping": 0,
                "credits_url_scrapping": 0,
            }
        by_brand[brand]["urls_url_mapping"] = int(entry.get("urls_url_mapping", 0))
        by_brand[brand]["credits_url_mapping"] = int(entry.get("credits_url_mapping", 0))

    for entry in scrapping_entries:
        brand = entry.get("brand")
        if not brand:
            continue
        if brand not in by_brand:
            by_brand[brand] = {
                "urls_url_mapping": 0,
                "credits_url_mapping": 0,
                "urls_url_scrapping": 0,
                "credits_url_scrapping": 0,
            }
        by_brand[brand]["urls_url_scrapping"] = int(entry.get("urls_url_scrapping", 0))
        by_brand[brand]["credits_url_scrapping"] = int(entry.get("credits_url_scrapping", 0))

    rows: list[dict] = []
    for brand, costs in by_brand.items():
        rows.append(
            build_cost_entry(
                brand=brand,
                urls_url_mapping=costs["urls_url_mapping"],
                credits_url_mapping=costs["credits_url_mapping"],
                urls_url_scrapping=costs["urls_url_scrapping"],
                credits_url_scrapping=costs["credits_url_scrapping"],
                run_timestamp=run_timestamp,
            )
        )
    return rows


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline de tracking de precios")
    parser.add_argument(
        "--brands",
        nargs="+",
        choices=list(BRANDS.keys()),
        default=None,
        help="Marcas a procesar (default: todas)",
    )
    parser.add_argument(
        "--skip-step1",
        action="store_true",
        help="Omitir la extracción de URLs y usar los JSONs existentes",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    brands = args.brands or list(BRANDS.keys())
    run_timestamp = datetime.now(timezone.utc).isoformat()
    step1_entries: list[dict] = []

    log.info("=== APP_ENV=%s ===", APP_ENV.upper())
    log.info("Output sheet : %s", GSHEETS_OUTPUT_SHEET)
    log.info("Log path     : %s", LOG_PATH)
    log.info("Firecrawl key: %s", _mask_secret(os.getenv("FIRECRAWL_API_KEY", "")))

    # Validacion previa: env vars y acceso a Google Sheets.
    # Si algo falla, abortamos antes de gastar creditos de Firecrawl.
    log.info("=== PREFLIGHT: Validando entorno y acceso a Google Sheets ===")
    try:
        run_preflight_checks(brands)
    except PreflightError as exc:
        log.error("%s", exc)
        sys.exit(1)

    if not args.skip_step1:
        log.info("=== STEP 1: Extracción de URLs ===")
        step1_entries = step1(brands)
    else:
        log.info("=== STEP 1: Omitido (--skip-step1) ===")

    log.info("=== STEP 2: Tracking de precios ===")
    diffs_by_brand, step2_entries = step2(brands)

    cost_entries = _consolidate_cost_entries(
        brands=brands,
        run_timestamp=run_timestamp,
        mapping_entries=step1_entries,
        scrapping_entries=step2_entries,
    )
    if cost_entries:
        gsheets = GoogleSheetReader()
        df_costs = append_cost_log(
            entries=cost_entries,
            gsheets=gsheets,
            sheet_name=GSHEETS_OUTPUT_SHEET,
            worksheet=GSHEETS_COSTS_WORKSHEET,
        )
        total_credits = int(df_costs["credits_total"].sum()) if not df_costs.empty else 0
        log.info(f"=== Costos Firecrawl: {len(df_costs)} filas, {total_credits} créditos estimados ===")

    if diffs_by_brand:
        log.info("=== Notificacion: diferencias detectadas ===")
        send_price_diff_email(diffs_by_brand)
    else:
        log.info("=== Notificacion: sin diferencias detectadas ===")

    log.info("=== Pipeline completado ===")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    main()
