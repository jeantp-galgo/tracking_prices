"""
Punto de entrada del pipeline de tracking de precios.

Uso:
    python -m pipeline.run_pipeline                     # Todas las marcas, ambos steps
    python -m pipeline.run_pipeline --brands Bajaj      # Solo Bajaj
    python -m pipeline.run_pipeline --skip-step1        # Usar JSONs existentes (ahorra créditos Firecrawl)
"""
import sys
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from src.config.brand_configs import BRANDS
from src.core.pipeline.step1_fetch_urls import main as step1
from src.core.pipeline.step2_track_prices import main as step2

log = logging.getLogger(__name__)


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
    brands = args.brands

    if not args.skip_step1:
        log.info("=== STEP 1: Extracción de URLs ===")
        step1(brands)
    else:
        log.info("=== STEP 1: Omitido (--skip-step1) ===")

    log.info("=== STEP 2: Tracking de precios ===")
    step2(brands)

    log.info("=== Pipeline completado ===")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    main()
