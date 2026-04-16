# Frecuencia de Actualizacion — tracking_prices_changes

## Frecuencia configurada

El pipeline se ejecuta automaticamente **todos los dias a las 10:00 AM hora Colombia (UTC-5)**.

| Parametro | Valor |
|---|---|
| Frecuencia | Diaria |
| Hora | 10:00 AM (Colombia, UTC-5) |
| Expresion cron | `0 15 * * *` (UTC) |
| Plataforma | GitHub Actions |
| Archivo de workflow | `.github/workflows/weekly_tracking.yml` |

---

## Disparadores

| Tipo | Descripcion |
|---|---|
| `schedule` | Cron diario automatico a las 15:00 UTC |
| `workflow_dispatch` | Ejecucion manual desde GitHub Actions con parametros opcionales |

### Parametros disponibles en ejecucion manual

| Parametro | Descripcion | Default |
|---|---|---|
| `brands` | Marcas a procesar. Ej: `"Bajaj Italika"`. Vacio = todas | Todas |
| `skip_step1` | Omitir extraccion de URLs y usar los JSONs locales. Ahorra creditos de Firecrawl | `false` |

---

## Lo que ocurre en cada ejecucion

1. Checkout del repositorio (rama `main`)
2. Instalacion de dependencias desde `requirements.txt` (Python 3.11, con cache de pip)
3. Decodificacion y escritura del archivo de credenciales de Google Sheets desde el secret `GOOGLE_SHEETS_KEY_BASE64`
4. Ejecucion del pipeline: `python -m pipeline.run_pipeline` (Step 1 + Step 2 para todas las marcas)
5. Commit automatico de los cambios en `src/data/json/brand_urls/` y `data/logs/price_diff_log.csv` al branch `main` con el mensaje `chore: actualizar URLs y log de precios [skip ci]`
6. Envio de email de notificacion segun el resultado (actualmente al correo de jtrujillo@galgo.com)

---

## Secrets requeridos en GitHub

| Secret | Uso |
|---|---|
| `FIRECRAWL_API_KEY` | API key de Firecrawl para scraping y change tracking |
| `GOOGLE_SHEETS_KEY_BASE64` | Credenciales de cuenta de servicio de Google Sheets en base64 |
| `GMAIL_USERNAME` | Cuenta Gmail desde/hacia la que se envian notificaciones |
| `GMAIL_APP_PASSWORD` | Contrasena de aplicacion de Gmail (no la contrasena de la cuenta) |

---

## Notificaciones por email

Al finalizar cada ejecucion se envia un email a `GMAIL_USERNAME`:

| Resultado | Asunto del email |
|---|---|
| Exitoso | `Price Tracking completado — {run_id}` |
| Fallido | `Price Tracking fallo — {run_id}` |

El cuerpo incluye: fecha de ejecucion, nombre del workflow, rama y enlace directo a los logs de GitHub Actions.

---

## Historial de cambios de frecuencia

| Fecha | Cambio |
|---|---|
| 2026-04-16 | Se cambia de semanal (martes 10:00 AM CO) a diario (todos los dias 10:00 AM CO) |
