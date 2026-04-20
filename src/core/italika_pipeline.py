import pandas as pd

GALGO_FEE = 1000

_FINAL_COLUMNS = [
    "captured_at", "previous_scrape_at",
    "code", "brand", "model", "model_name", "year", "year_scraped", "status",
    "price_scraped", "price_scraped_with_galgo_fee", "price_base", "discount_amount",
    "price_net", "price_diff", "price_diff_without_galgo_fee",
    "price_type", "currency", "change_status", "visibility",
    "year_match_type",
    "url_scraped", "marketplace_url",
]


def build_price_comparison(
    df_scraped: pd.DataFrame,
    df_inventory: pd.DataFrame,
    country: str,
    galgo_fee: float = GALGO_FEE,
) -> pd.DataFrame:
    """Construye el DataFrame final de comparación de precios para una marca.

    Une el resultado del scraping con el inventario, aplica el fee de Galgo
    y calcula la diferencia de precio.

    Args:
        df_scraped: DataFrame con columnas model_mapped y los campos del scrape.
        df_inventory: DataFrame del inventario filtrado por marca, con columna model_lower.
        country: Código de país (ej. 'MX'), usado para construir la URL de marketplace.
        galgo_fee: Fee aplicado sobre el precio scrapeado para comparar contra inventario.

    Returns:
        DataFrame con columnas definidas en _FINAL_COLUMNS.
    """
    df_inv = df_inventory.copy()
    df = df_scraped.copy()
    df_inv["model_lower"] = df_inv["model"].str.lower()
    df_inv["year"] = pd.to_numeric(df_inv["year"], errors="coerce")
    df["year_scraped"] = pd.to_numeric(df.get("year_scraped"), errors="coerce")

    df_exact = pd.merge(
        df_inv,
        df,
        left_on=["model_lower", "year"],
        right_on=["model_mapped", "year_scraped"],
        how="inner",
    )
    df_exact["year_match_type"] = "exact"

    df_inv_match_check = pd.merge(
        df_inv,
        df[["model_mapped", "year_scraped"]],
        left_on=["model_lower", "year"],
        right_on=["model_mapped", "year_scraped"],
        how="left",
        indicator=True,
    )
    df_unmatched = df_inv_match_check[df_inv_match_check["_merge"] == "left_only"][
        df_inv.columns
    ].copy()

    df_scraped_latest = (
        df.sort_values(
            ["model_mapped", "year_scraped"],
            ascending=[True, False],
            na_position="last",
        )
        .drop_duplicates(subset=["model_mapped"], keep="first")
        .copy()
    )

    df_fallback = pd.merge(
        df_unmatched,
        df_scraped_latest,
        left_on=["model_lower"],
        right_on=["model_mapped"],
        how="left",
    )
    df_fallback["year_match_type"] = "fallback_year"

    df_merged = pd.concat([df_exact, df_fallback], ignore_index=True, sort=False)

    df_merged.rename(
        columns={"price": "price_scraped", "url": "url_scraped"},
        inplace=True,
    )

    df_merged["marketplace_url"] = df_merged["code"].apply(
        lambda code: f"https://www.galgo.com/{country.lower()}/motos/{code}"
    )

    price_scraped_numeric = (
        df_merged["price_scraped"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )
    df_merged["price_scraped_with_galgo_fee"] = (
        price_scraped_numeric + galgo_fee
    )

    df_merged["price_diff"] = (
        df_merged["price_scraped_with_galgo_fee"] - df_merged["price_net"]
    )

    df_merged["price_diff_without_galgo_fee"] = (
        price_scraped_numeric - df_merged["price_net"]
    )

    existing_cols = [c for c in _FINAL_COLUMNS if c in df_merged.columns]
    return df_merged[existing_cols].copy()
