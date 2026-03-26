# src/config/settings.py
import pathlib

# Raíz del proyecto: sube 3 niveles desde este archivo
# settings.py → config/ → src/ → proyecto/
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent

# Desde PROJECT_ROOT construyes lo que necesites
SRC_DIR = PROJECT_ROOT / "src"

COUNTRY = "MX"