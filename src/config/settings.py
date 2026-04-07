# src/config/settings.py
import pathlib
from pathlib import Path

# Raíz del proyecto: sube 3 niveles desde este archivo
# # settings.py → config/ → src/ → proyecto/
# PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent

# # Desde PROJECT_ROOT construyes lo que necesites
# SRC_DIR = PROJECT_ROOT / "src"

# Directorio de la aplicación
CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]

# Google Sheets
GOOGLE_SHEET_CREDENTIALS = f"{SRC_DIR}/config/key-google-sheets.json"

COUNTRY = "MX"