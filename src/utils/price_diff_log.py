import pandas as pd
from pathlib import Path
from datetime import date

_LOG_COLUMNS = [
    "run_date",
    "captured_at",
    "brand",
    "code",
    "model",
    "year",
    "price_scraped",
    "price_scraped_with_galgo_fee",
    "price_net",
    "price_diff",
]


def append_price_diff_log(df_final: pd.DataFrame, log_path: str | Path) -> int:
    """Agrega al log histórico CSV las filas con diferencia de precio real.

    Solo procesa filas que hicieron match con inventario (code no nulo)
    y tienen price_diff distinto de cero.

    Args:
        df_final: DataFrame resultado de build_price_comparison.
        log_path: Ruta al CSV acumulativo. Se crea si no existe.

    Returns:
        Número de filas agregadas en esta ejecución.
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    df_diffs = df_final[
        df_final["code"].notna()
        & df_final["price_diff"].notna()
        & (df_final["price_diff"] != 0)
    ].copy()

    if df_diffs.empty:
        return 0

    df_diffs["run_date"] = date.today().isoformat()

    existing_cols = [c for c in _LOG_COLUMNS if c in df_diffs.columns]
    df_to_log = df_diffs[existing_cols]

    write_header = not log_path.exists()
    df_to_log.to_csv(log_path, mode="a", index=False, header=write_header)

    return len(df_to_log)
