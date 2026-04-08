# src/config/settings.py
from pathlib import Path

# Directorio de la aplicación
CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]

# Google Sheets
GOOGLE_SHEET_CREDENTIALS = f"{SRC_DIR}/config/key-google-sheets.json"

COUNTRY = "MX"