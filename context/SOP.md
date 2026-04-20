# SOP — tracking_prices_changes

## Proposito

Ejecutar el pipeline de comparacion de precios entre los sitios web oficiales de las marcas (Italika, Bajaj) y el inventario interno del marketplace. El resultado se escribe en Google Sheets con la diferencia de precio por modelo y se envia un email con los cambios detectados.

## Arquitectura

```text
tracking_prices_changes/
├── pipeline/
│   └── run_pipeline.py              # Punto de entrada del pipeline automatizado
├── notebooks/
│   ├── brand_urls.ipynb             # Auxiliar: descubrimiento y revision de URLs
│   └── tracking_prices.ipynb        # Auxiliar: scraping y comparacion ad hoc
├── src/
│   ├── config/
│   │   ├── settings.py              # APP_ENV, rutas base, constantes de billing Firecrawl
│   │   └── brand_configs.py         # BRANDS, fees de Galgo, nombres de hojas GSheets
│   ├── core/
│   │   ├── pipeline/
│   │   │   ├── preflight.py         # Validacion de entorno antes de ejecutar
│   │   │   ├── step1_fetch_urls.py  # Step 1: descubrimiento de URLs via Firecrawl map
│   │   │   └── step2_track_prices.py # Step 2: scraping de precios y merge con inventario
│   │   ├── scraper/
│   │   │   └── app.py               # ScrapingUtils: descubre URLs con Firecrawl map
│   │   ├── urls_tracking/
│   │   │   └── urls_tracking.py     # Filtros de URLs por marca y deteccion de cambios
│   │   ├── price_tracking/
│   │   │   ├── price_tracking.py    # run_price_tracking: batch_scrape + changeTracking
│   │   │   ├── utils.py             # Parseo de precios, nombres de modelo y anio
│   │   │   └── brands/
│   │   │       ├── italika.py       # Parseo especifico para Italika
│   │   │       └── bajaj.py         # Parseo especifico para Bajaj
│   │   └── italika_pipeline.py      # build_price_comparison: merge + fee + price_diff
│   ├── notifications/
│   │   └── email_notifier.py        # Notificacion por email via Resend API
│   ├── data/
│   │   └── json/
│   │       ├── brand_urls/          # URLs guardadas por marca (italika.json, bajaj.json)
│   │       └── replace_name/MX/    # Mapeo de nombres por marca ({marca}_mapeo_nombres.json)
│   ├── sources/
│   │   └── sheets/
│   │       ├── client.py            # Autenticacion con Google Sheets
│   │       └── reader.py            # Lectura y escritura de hojas
│   └── utils/
│       ├── clean_model_name.py      # Limpia nombres: elimina marca, colores, conectores
│       ├── replace_model_name.py    # Carga y aplica el mapeo JSON de nombres de modelo
│       ├── price_diff_log.py        # Registra filas con price_diff != 0 en log historico CSV
│       └── scraping_cost_log.py     # Registra creditos Firecrawl usados en hoja GSheets
├── context/
├── env_example
└── .gitignore
```

| Archivo clave | Funcion |
|---|---|
| `pipeline/run_pipeline.py` | Orquesta el pipeline completo: preflight, step1, step2, costos, email |
| `src/core/pipeline/preflight.py` | Valida entorno y acceso a Google Sheets antes de gastar creditos |
| `src/core/price_tracking/price_tracking.py` | Ejecuta el scraping y construye las filas de resultado por URL |
| `src/core/italika_pipeline.py` | Merge scraping-inventario, aplica fee de Galgo, calcula price_diff |
| `src/notifications/email_notifier.py` | Envia email con diferencias de precio via Resend API |
| `src/utils/scraping_cost_log.py` | Escribe costos de Firecrawl en la hoja `scraping_costs` de GSheets |

## Stack tecnico

| Tecnologia | Uso |
|---|---|
| Python 3.x | Lenguaje principal |
| Firecrawl | Scraping y change tracking de sitios web |
| pandas | Transformacion de datos y merge |
| gspread / gspread-dataframe | Lectura y escritura en Google Sheets |
| resend | Envio de emails de diferencias de precio |
| python-dotenv | Carga de variables de entorno desde `.env` |
| GitHub Actions | Ejecucion automatizada diaria |

---

## Configuracion inicial

### Variables de entorno

```bash
cp env_example .env
```

Editar `.env` y completar:

```env
APP_ENV=master                           # "master" para produccion, "development" para pruebas
FIRECRAWL_API_KEY=<api key de Firecrawl>
FIRECRAWL_API_KEY_DEV=<api key dev>      # Solo necesario si APP_ENV=development
RESEND_API_KEY=<api key de Resend>
NOTIFICATION_EMAIL_TO=<email destino de alertas de precio>
NOTIFICATION_EMAIL_FROM=<email remitente> # Opcional; default: onboarding@resend.dev
```

Colocar el archivo de credenciales de Google Sheets en:

```
src/config/key-google-sheets.json
```

### Instalacion

```bash
python -m venv venv
venv\Scripts\activate         # Windows
source venv/bin/activate      # Linux / macOS

pip install -r requirements.txt
```

---

## Ejecucion del pipeline

El punto de entrada principal es `pipeline/run_pipeline.py`. Ejecuta las 5 fases en orden: preflight, step1 (URLs), step2 (scraping + merge), registro de costos en GSheets y email de diferencias.

### Comandos

```bash
# Todas las marcas, con descubrimiento de URLs (step1 + step2)
python -m pipeline.run_pipeline

# Solo marcas especificas
python -m pipeline.run_pipeline --brands Bajaj
python -m pipeline.run_pipeline --brands "Bajaj Italika"

# Omitir step1 (usar URLs existentes en JSON, ahorra creditos de Firecrawl)
python -m pipeline.run_pipeline --skip-step1
```

### Validacion previa (preflight)

Para verificar el entorno sin ejecutar el pipeline:

```bash
python -m src.core.pipeline.preflight
python -m src.core.pipeline.preflight --brands Bajaj
```

El preflight valida: variables de entorno requeridas, existencia de `key-google-sheets.json`, y acceso real a todas las hojas esperadas en Google Sheets. Si algo falla, reporta todos los errores juntos antes de abortar.

---

## Proceso auxiliar: Descubrimiento manual de URLs

**Notebook**: `notebooks/brand_urls.ipynb`

Util para inspeccionar que URLs se detectan para una marca o para depurar el filtro de URLs antes de correr el pipeline.

1. Configurar la marca objetivo:

```python
BRAND = "Bajaj"  # Opciones actuales: "Bajaj", "Italika"
```

2. Ejecutar el notebook completo. El sistema extrae todas las URLs del sitio, aplica el filtro de la marca y las compara con las guardadas en `src/data/json/brand_urls/{brand}.json`.

---

## Proceso auxiliar: Scraping ad hoc

**Notebook**: `notebooks/tracking_prices.ipynb`

Util para ejecutar o inspeccionar el scraping de una marca de forma interactiva, sin correr el pipeline completo.

---

## Ejecucion automatizada (GitHub Actions)

El pipeline corre automaticamente todos los dias a las 10:00 AM hora Colombia via GitHub Actions.

**Archivo de workflow**: `.github/workflows/daily_tracking.yml`

Para disparar manualmente desde GitHub:

1. Ir a **Actions → Daily Price Tracking → Run workflow**
2. Opcional: especificar marcas en el campo `brands` (ej. `Bajaj Italika`)
3. Opcional: activar `skip_step1` para omitir la extraccion de URLs y ahorrar creditos de Firecrawl

### Notificaciones del workflow

Hay dos sistemas de email independientes:

| Sistema | Canal | Cuando se envia |
|---|---|---|
| Estado del pipeline | Gmail (action-send-mail) | Siempre al terminar: exito o fallo del workflow |
| Diferencias de precio | Resend (email_notifier.py) | Solo si hay modelos con `price_diff != 0` |

Ver detalle completo de frecuencia, secrets y notificaciones en `context/UPDATE_SCHEDULE.md`.

---

## Notas

| Situacion | Comportamiento | Solucion |
|---|---|---|
| Modelo scrapeado sin match en inventario | No aparece en el output (el merge es inventory-first) | Verificar si el modelo existe en el inventario o agregar al mapeo de nombres |
| Modelo en inventario sin URL scrapeada para su anio | Aparece con `year_match_type = "fallback_year"` y columnas de scraping en NaN si tampoco hay anio alternativo | Verificar si la URL del modelo existe y esta incluida en `urls_to_scrape` |
| Nombre de modelo no hace match | El merge no cruza por discrepancia de nombres | Agregar el mapeo en `src/data/json/replace_name/MX/{brand}_mapeo_nombres.json` |
| `change_status` vacio en primera ejecucion | Firecrawl no tiene scrape previo para comparar | Normal; en la segunda ejecucion ya devuelve `same` o `changed` |
| `year_match_type = "fallback_year"` con precio en NaN | El modelo existe en el inventario pero no tiene ninguna URL scrapeada con match de nombre | Revisar mapeo de nombres o agregar la URL a `brand_urls/{marca}.json` |
| Agregar una nueva marca | No existe modulo de parseo ni filtro de URLs | Crear `src/core/price_tracking/brands/{marca}.py`, agregar filtro en `urls_tracking.py`, fee en `brand_configs.py` y hoja en el Google Sheets de output |
| Preflight falla con error de credenciales | `key-google-sheets.json` no encontrado o variables de entorno vacias | Verificar que el archivo existe en `src/config/` y que `.env` tiene todas las variables requeridas |
| Email de diferencias no se envia | No habia modelos con `price_diff != 0` en la corrida | Comportamiento normal; revisar el output en GSheets para confirmar |
