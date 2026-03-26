import pandas as pd

GALGO_FEE = 1000

_FINAL_COLUMNS = [
    "captured_at", "previous_scrape_at",
    "code", "brand", "model", "model_name", "year", "year_scraped", "status",
    "price_scraped", "price_scraped_with_galgo_fee", "price_base", "discount_amount",
    "price_net", "price_diff",
    "price_type", "currency", "change_status", "visibility",
    "url_scraped", "marketplace_url",
]


def build_price_comparison(
    df_scraped: pd.DataFrame,
    df_inventory: pd.DataFrame,
    country: str,
) -> pd.DataFrame:
    """Construye el DataFrame final de comparación de precios para Italika.

    Une el resultado del scraping con el inventario, aplica el fee de Galgo
    (+1000 MXN, exclusivo de Italika) y calcula la diferencia de precio.

    Args:
        df_scraped: DataFrame con columnas model_mapped y los campos del scrape.
        df_inventory: DataFrame del inventario filtrado por marca, con columna model_lower.
        country: Código de país (ej. 'MX'), usado para construir la URL de marketplace.

    Returns:
        DataFrame con columnas definidas en _FINAL_COLUMNS.
    """
    df = df_scraped.copy()
    df_inv = df_inventory.copy()
    df_inv["model_lower"] = df_inv["model"].str.lower()

    df_merged = pd.merge(
        df,
        df_inv,
        left_on="model_mapped",
        right_on="model_lower",
        how="left",
        indicator=True,
    )

    df_merged.rename(
        columns={"price": "price_scraped", "url": "url_scraped"},
        inplace=True,
    )

    df_merged["marketplace_url"] = df_merged["code"].apply(
        lambda code: f"https://www.galgo.com/{country.lower()}/motos/{code}"
    )

    df_merged["price_scraped_with_galgo_fee"] = (
        df_merged["price_scraped"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .astype(int)
        + GALGO_FEE
    )

    df_merged["price_diff"] = (
        df_merged["price_scraped_with_galgo_fee"] - df_merged["price_net"]
    )

    existing_cols = [c for c in _FINAL_COLUMNS if c in df_merged.columns]
    return df_merged[existing_cols].copy()
