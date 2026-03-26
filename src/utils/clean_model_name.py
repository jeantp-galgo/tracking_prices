import re


def clean_model_name(model: str) -> str:
    """Limpia el nombre de modelo scrapeado de Italika.

    Elimina el prefijo de tipo de moto y la marca, quita colores y
    palabras conectoras ('con'), y normaliza espacios.
    """
    # 1. Conservar solo la parte después de 'Italika'
    match = re.search(r"Italika\s*(.*)", model, re.IGNORECASE)
    if match:
        model = match.group(1).strip()

    # 2. Eliminar la palabra 'con' (ej. "con GPS", "con negro")
    model = re.sub(r"\bcon\b", "", model, flags=re.IGNORECASE)

    # 3. Eliminar colores comunes al final o en cualquier posición
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

    # 4. Normalizar espacios múltiples
    model = re.sub(r"\s+", " ", model)
    return model.strip()
