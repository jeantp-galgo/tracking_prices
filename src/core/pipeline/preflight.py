"""
Preflight checks: valida entorno y acceso a recursos externos antes de scrapear.

Objetivo: fallar rápido y barato, ANTES de gastar creditos de Firecrawl o
sobreescribir datos en Google Sheets con hojas renombradas/ausentes.

Uso como modulo (en Python):
    from src.core.pipeline.preflight import run_preflight_checks
    run_preflight_checks(brands=["Bajaj", "Italika"])

Uso como script (en GitHub Actions):
    python -m src.core.pipeline.preflight
    python -m src.core.pipeline.preflight --brands Bajaj
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.config.brand_configs import (
    BRANDS,
    GSHEETS_COSTS_WORKSHEET,
    GSHEETS_INVENTORY,
    GSHEETS_OUTPUT_SHEET,
)
from src.config.settings import GOOGLE_SHEET_CREDENTIALS

log = logging.getLogger(__name__)

REQUIRED_ENV_VARS: tuple[str, ...] = (
    "FIRECRAWL_API_KEY",
    "RESEND_API_KEY",
    "NOTIFICATION_EMAIL_TO",
)


class PreflightError(RuntimeError):
    """Agrupa todos los errores de preflight en un solo mensaje."""


def _check_env_vars() -> list[str]:
    """Valida que las variables requeridas esten definidas y no vacias."""
    errors: list[str] = []
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var)
        if not value or not value.strip():
            errors.append(f"[env] Variable faltante o vacia: {var}")
    return errors


def _check_gsheets_credentials() -> list[str]:
    """Verifica que el JSON de credenciales exista en disco."""
    errors: list[str] = []
    cred_path = Path(GOOGLE_SHEET_CREDENTIALS)
    if not cred_path.is_file():
        errors.append(
            f"[gsheets] No se encontro el archivo de credenciales en {cred_path}"
        )
    return errors


def _check_gsheets_access(brands: list[str]) -> list[str]:
    """
    Abre el cliente de gspread y valida que existan todas las hojas/worksheets
    que el pipeline va a leer y escribir.
    """
    errors: list[str] = []

    try:
        # Import diferido: si faltan credenciales, el check anterior ya lo reporta.
        from src.sources.sheets.reader import GoogleSheetReader

        reader = GoogleSheetReader()
        client = reader.client
    except Exception as exc:
        return [f"[gsheets] No se pudo autenticar con Google Sheets: {exc}"]

    # Hoja de inventario (lectura)
    try:
        sheet = client.open(GSHEETS_INVENTORY["sheet_name"])
        sheet.worksheet(GSHEETS_INVENTORY["worksheet"])
    except Exception as exc:
        errors.append(
            f"[gsheets] No se pudo abrir inventario "
            f"'{GSHEETS_INVENTORY['sheet_name']}' / "
            f"worksheet '{GSHEETS_INVENTORY['worksheet']}': {exc}"
        )

    # Hoja de output (escritura): debe existir el archivo, un worksheet por marca
    # y el worksheet de costos.
    try:
        output_sheet = client.open(GSHEETS_OUTPUT_SHEET)
    except Exception as exc:
        errors.append(
            f"[gsheets] No se pudo abrir archivo de output "
            f"'{GSHEETS_OUTPUT_SHEET}': {exc}"
        )
        return errors

    expected_worksheets = list(brands) + [GSHEETS_COSTS_WORKSHEET]
    try:
        existing = {ws.title for ws in output_sheet.worksheets()}
    except Exception as exc:
        errors.append(
            f"[gsheets] No se pudieron listar worksheets de "
            f"'{GSHEETS_OUTPUT_SHEET}': {exc}"
        )
        return errors

    for ws_name in expected_worksheets:
        if ws_name not in existing:
            errors.append(
                f"[gsheets] Falta worksheet '{ws_name}' en "
                f"'{GSHEETS_OUTPUT_SHEET}'. Disponibles: {sorted(existing)}"
            )

    return errors


def run_preflight_checks(brands: list[str] | None = None) -> None:
    """
    Ejecuta todas las validaciones y levanta PreflightError si alguna falla.
    Acumula errores para reportarlos todos juntos (no solo el primero).
    """
    brands = brands or list(BRANDS.keys())

    errors: list[str] = []
    errors.extend(_check_env_vars())
    cred_errors = _check_gsheets_credentials()
    errors.extend(cred_errors)

    # Si no hay credenciales, no tiene sentido intentar abrir hojas.
    if not cred_errors:
        errors.extend(_check_gsheets_access(brands))

    if errors:
        detail = "\n  - " + "\n  - ".join(errors)
        raise PreflightError(
            f"Preflight fallo con {len(errors)} error(es):{detail}"
        )

    log.info("Preflight OK: env vars, credenciales y hojas verificadas (%s).", brands)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preflight del pipeline de tracking")
    parser.add_argument(
        "--brands",
        nargs="+",
        choices=list(BRANDS.keys()),
        default=None,
        help="Marcas a validar (default: todas)",
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    args = _parse_args()
    try:
        run_preflight_checks(args.brands)
    except PreflightError as exc:
        log.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
