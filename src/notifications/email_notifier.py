import logging
import os
from datetime import date

import pandas as pd
import resend
from src.config.settings import APP_ENV

log = logging.getLogger(__name__)

_EMAIL_COLUMNS = [
    "model",
    "year",
    "price_scraped",
    "price_scraped_with_galgo_fee",
    "price_net",
    "price_diff",
    "url_scraped",
    "marketplace_url",
]


def _build_brand_table(df_brand: pd.DataFrame) -> str:
    """Construye la tabla HTML por marca con columnas relevantes."""
    cols = [col for col in _EMAIL_COLUMNS if col in df_brand.columns]
    if not cols:
        return "<p>Sin columnas compatibles para renderizar.</p>"

    table_df = df_brand[cols].copy()
    for col in ("price_scraped", "price_scraped_with_galgo_fee", "price_net", "price_diff"):
        if col in table_df.columns:
            table_df[col] = (
                table_df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .pipe(pd.to_numeric, errors="coerce")
                .round(2)
            )

    for col in ("url_scraped", "marketplace_url"):
        if col in table_df.columns:
            # Renderiza enlaces clickeables para facilitar revisión desde email.
            table_df[col] = table_df[col].apply(
                lambda url: f'<a href="{url}" target="_blank">{url}</a>'
                if isinstance(url, str) and url.strip()
                else ""
            )

    return table_df.to_html(index=False, border=0, justify="left", escape=False)


def _build_email_html(diffs_by_brand: dict[str, pd.DataFrame]) -> tuple[str, int]:
    """Arma HTML consolidado y retorna total de diferencias."""
    sections: list[str] = []
    total_diffs = 0

    for brand, df_brand in sorted(diffs_by_brand.items()):
        if df_brand.empty:
            continue
        total_diffs += len(df_brand)
        sections.append(
            (
                f"<h3>{brand}</h3>"
                f"<p>Diferencias detectadas: <strong>{len(df_brand)}</strong></p>"
                f"{_build_brand_table(df_brand)}"
            )
        )

    if total_diffs == 0:
        return "", 0

    summary = "".join(
        f"<li>{brand}: {len(df)}</li>"
        for brand, df in sorted(diffs_by_brand.items())
        if not df.empty
    )
    html = (
        "<h2>Price Tracking - Diferencias detectadas</h2>"
        f"<p>Fecha de corrida: {date.today().isoformat()}</p>"
        f"<p>Total de diferencias: <strong>{total_diffs}</strong></p>"
        f"<ul>{summary}</ul>"
        + "".join(sections)
    )
    return html, total_diffs


def _parse_recipients(raw: str) -> list[str]:
    """Parsea uno o varios correos separados por coma desde una variable de entorno."""
    return [addr.strip() for addr in raw.split(",") if addr.strip()]


def send_price_diff_email(diffs_by_brand: dict[str, pd.DataFrame]) -> None:
    """Envía un correo consolidado con diferencias de precio."""
    api_key = os.getenv("RESEND_API_KEY")
    to_raw = os.getenv("NOTIFICATION_EMAIL_TO", "")
    from_email = os.getenv("NOTIFICATION_EMAIL_FROM", "onboarding@resend.dev")

    if not api_key:
        log.warning("No se envio email de diferencias: falta RESEND_API_KEY.")
        return

    to_list = _parse_recipients(to_raw)
    if not to_list:
        log.warning("No se envio email de diferencias: falta NOTIFICATION_EMAIL_TO.")
        return

    html, total_diffs = _build_email_html(diffs_by_brand)
    if total_diffs == 0:
        log.info("No hay diferencias para notificar por email.")
        return

    resend.api_key = api_key
    prefix = "[DEV] " if APP_ENV == "development" else ""
    subject = f"{prefix}[Price Tracking] {total_diffs} diferencias detectadas - {date.today().isoformat()}"

    try:
        resend.Emails.send(
            {
                "from": from_email,
                "to": to_list,
                "subject": subject,
                "html": html,
            }
        )
        log.info("Email de diferencias enviado a %s con %s registros.", to_list, total_diffs)
    except Exception as exc:  # pragma: no cover
        log.warning("Fallo al enviar email con Resend: %s", exc)
