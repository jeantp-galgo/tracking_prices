import re


def clean_model_name(model: str, brand_name: str | None = None) -> str:
    """Limpia el nombre de modelo scrapeado con reglas base multi-marca.

    Si detecta la marca en el texto, conserva solo lo que sigue a la marca.
    Luego elimina conectores y colores para estabilizar el merge.
    """
    model = str(model or "").strip()
    if not model:
        return ""

    # 1. Conservar solo la parte posterior a la marca (si existe en el texto)
    if brand_name:
        escaped_brand = re.escape(brand_name.strip())
        match = re.search(rf"{escaped_brand}\s*(.*)", model, re.IGNORECASE)
        if match:
            model = match.group(1).strip()

    # 2. Eliminar palabras de marketing comunes al inicio
    model = re.sub(r"^(nuevo|nueva|descuento)\s+", "", model, flags=re.IGNORECASE)

    # 3. Eliminar la palabra 'con' (ej. "con GPS", "con negro")
    model = re.sub(r"\bcon\b", "", model, flags=re.IGNORECASE)

    # 4. Eliminar colores comunes al final o en cualquier posición
    colores = [
        "blanca", "blanco", "negro", "negra", "azul", "rojo", "roja", "verde", "gris",
        "amarillo", "amarilla", "naranja", "dorado", "dorada", "plateado", "plateada",
        "cafe", "café", "morado", "morada", "rosado", "rosada", "beige", "vino", "plata",
        "perla", "caramelo", "grafito", "anaranjado", "fucsia", "lila", "mate", "carbono",
        "camuflaje", "camuflado", "turquesa",
    ]
    pattern_colores = r"(?:\b(?:" + "|".join(colores) + r")\b\.?,?\s*)"
    model = re.sub(pattern_colores + r"*$", "", model, flags=re.IGNORECASE)
    model = re.sub(pattern_colores, "", model, flags=re.IGNORECASE)

    # 5. Normalizar espacios múltiples
    model = re.sub(r"\s+", " ", model)
    return model.strip()
