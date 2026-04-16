import re
import pandas as pd
from rapidfuzz import fuzz
from src.utils.replace_model_name import load_mapping_file


class ModelMatcher:
    """
    Busca el modelo de inventario que corresponde a un nombre scrapeado.

    Aplica dos niveles en orden:
      Tier 1 — token_sort_ratio: resuelve diferencias de espacios, signos y orden de palabras.
      Tier 2 — JSON fallback: cubre diferencias semánticas mapeadas manualmente.

    Uso:
        matcher = ModelMatcher(df_inventory, country="MX", brand="bajaj")
        result = matcher.find("Avenger Cruise 220")
    """

    def __init__(self, df_inventory: pd.DataFrame, country: str, brand: str, threshold: int = 88, model_col: str = "model", code_col: str = "code"):
        """
        Args:
            df_inventory: DataFrame con al menos las columnas model y code.
            country: Código de país para localizar el JSON de mapeo (ej. "MX").
            brand: Nombre de la marca para localizar el JSON de mapeo (ej. "bajaj").
            threshold: Score mínimo de similitud para aceptar un match en Tier 1 (0-100).
            model_col: Nombre de la columna de modelo en df_inventory.
            code_col: Nombre de la columna de código en df_inventory.
        """
        self.df = df_inventory[[code_col, model_col]].drop_duplicates().copy()
        self.threshold = threshold
        self.model_col = model_col
        self.code_col = code_col
        self.mapping = load_mapping_file(country, brand)

    @staticmethod
    def normalize(text: str) -> str:
        """
        Convierte a minúsculas y elimina signos especiales.
        Conserva letras, números y espacios para que token_sort_ratio pueda ordenar tokens.
        Ej: "Pulsar N 250 FI+ABS UG" → "pulsar n 250 fi abs ug"
        """
        return re.sub(r'[^a-z0-9 ]', '', text.lower().strip())

    def find(self, input_model: str) -> dict:
        """
        Aplica Tier 1 y, si falla, Tier 2.

        Returns:
            dict con claves:
              - tier (1, 2 o None si no hubo match)
              - score (int o None)
              - input (nombre original ingresado)
              - matched_model (nombre en inventario o None)
              - code (código en inventario o None)
              - warning (str o None)
        """
        result = self._tier1_fuzzy(input_model)
        if result:
            return result

        result = self._tier2_json(input_model)
        if result:
            return result

        return {
            "tier": None,
            "score": None,
            "input": input_model,
            "matched_model": None,
            "code": None,
            "warning": "Sin match — agregar al JSON de mapeo manual",
        }

    def _tier1_fuzzy(self, input_model: str) -> dict | None:
        """
        Tier 1: token_sort_ratio sobre nombres normalizados.
        Ordena los tokens antes de comparar → resuelve diferencias de orden de palabras.
        """
        best_match = None
        best_score = -1
        input_norm = self.normalize(input_model)

        for _, row in self.df.iterrows():
            score = fuzz.token_sort_ratio(input_norm, self.normalize(str(row[self.model_col])))
            if score >= self.threshold and score > best_score:
                best_score = score
                best_match = {
                    "tier": 1,
                    "score": score,
                    "input": input_model,
                    "matched_model": row[self.model_col],
                    "code": row[self.code_col],
                    "warning": None,
                }

        return best_match

    def _tier2_json(self, input_model: str) -> dict | None:
        """
        Tier 2: lookup exacto en el JSON de mapeo manual.
        Cubre diferencias semánticas que el fuzzy no puede inferir.
        """
        mapped_name = self.mapping.get(input_model)

        if not mapped_name:
            return None

        inventory_row = self.df[self.df[self.model_col] == mapped_name]

        code = inventory_row.iloc[0][self.code_col] if not inventory_row.empty else None
        warning = "Nombre mapeado no encontrado en inventario" if inventory_row.empty else None

        return {
            "tier": 2,
            "score": None,
            "input": input_model,
            "matched_model": mapped_name,
            "code": code,
            "warning": warning,
        }

    def find_many(self, models: list[str]) -> pd.DataFrame:
        """
        Aplica find() a una lista de modelos y devuelve un DataFrame con los resultados.

        Útil para procesar todos los modelos scrapeados de una vez.
        """
        results = [self.find(m) for m in models]
        return pd.DataFrame(results)
