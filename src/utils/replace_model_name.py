import json
import os
import re
from typing import Dict, Optional
from src.config.settings import SRC_DIR

def normalize_brand_name(marca: str) -> str:
    """Normaliza el nombre de la marca para el nombre del archivo."""
    normalized = re.sub(r"[^a-z0-9]+", "_", (marca or "").strip().lower())
    return normalized.strip("_")


def get_mapping_file_path(country: str, marca: str) -> str:
    """
    Obtiene la ruta del archivo JSON de mapeo para un país y marca.

    Args:
        country: Código del país (ej: 'MX', 'CO')
        marca: Nombre de la marca

    Returns:
        Ruta completa del archivo JSON
    """
    marca_normalizada = normalize_brand_name(marca)
    return f'{SRC_DIR}/data/json/replace_name/{country}/{marca_normalizada}_mapeo_nombres.json'


def load_mapping_file(country: str, marca: str) -> Dict[str, str]:
    """
    Carga el archivo JSON de mapeo de nombres para un país y marca.

    Si el archivo no existe, lo crea vacío.

    Args:
        country: Código del país (ej: 'MX', 'CO')
        marca: Nombre de la marca

    Returns:
        Diccionario con el mapeo de nombres
    """
    filename = get_mapping_file_path(country, marca)

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            mapeo_nombres = json.load(f)
            print(f"Archivo de mapeo cargado correctamente: {filename}")
            return mapeo_nombres
    except FileNotFoundError:
        marca_normalizada = normalize_brand_name(marca)
        print(f"ERROR: El archivo de mapeo: {marca_normalizada}_mapeo_nombres.json no se encuentra. Creando archivo vacío.")
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        return {}


def map_model_name(modelo: str, mapeo_nombres: Dict[str, str]) -> str:
    """
    Mapea un nombre de modelo usando el diccionario de mapeo.

    Si el modelo no está en el mapeo, devuelve el nombre original (sin cambio).

    Args:
        modelo: Nombre del modelo a mapear
        mapeo_nombres: Diccionario con el mapeo de nombres

    Returns:
        Nombre mapeado si existe en el diccionario, o el nombre original si no
    """
    modelo_limpio = str(modelo).strip().lower()
    # Normalizar las claves del mapeo para comparación
    mapeo_normalizado = {str(k).strip().lower(): v for k, v in mapeo_nombres.items()}
    return mapeo_normalizado.get(modelo_limpio, modelo_limpio)
