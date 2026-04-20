# src/config/settings.py
import os
from pathlib import Path

APP_ENV = os.getenv("APP_ENV", "master").strip().lower()
if APP_ENV not in {"master", "development"}:
    raise ValueError(
        f"APP_ENV invalido: '{APP_ENV}'. Valores permitidos: 'master', 'development'."
    )

# En development forzamos el uso de la key de Firecrawl de pruebas.
# Si falta FIRECRAWL_API_KEY_DEV, dejamos la variable vacia para que
# el preflight falle antes de consumir creditos accidentalmente.
if APP_ENV == "development":
    os.environ["FIRECRAWL_API_KEY"] = os.getenv("FIRECRAWL_API_KEY_DEV", "").strip()

# Directorio de la aplicación
CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]

# Google Sheets
GOOGLE_SHEET_CREDENTIALS = f"{SRC_DIR}/config/key-google-sheets.json"

COUNTRY = "MX"

# Firecrawl billing defaults.
# Fuente: docs/.firecrawl/firecrawl-billing.md
FIRECRAWL_MAP_CREDITS = 1
FIRECRAWL_SCRAPE_CREDITS_PER_URL = 1