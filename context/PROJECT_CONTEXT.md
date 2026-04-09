# tracking_prices_changes — Contexto del Proyecto

## Que es

Sistema de seguimiento de precios de catalogos de marcas de motos y scooters. Scrapea los sitios web oficiales de cada marca usando Firecrawl Change Tracking (modo git-diff), cruza los precios obtenidos contra el inventario interno del marketplace (Google Sheets) y exporta un archivo CSV con la comparacion de precios por modelo.

Esta disenado para soportar multiples marcas. Actualmente opera con Italika y Bajaj. Cada marca tiene su propio modulo de parseo y su archivo de mapeo de nombres para resolver discrepancias entre los nombres del sitio web y los del inventario interno.

## Estado (2026-04-08)

### Completado
- Scraping de precios con Firecrawl Change Tracking para Italika y Bajaj
- Modulo de descubrimiento y filtrado de URLs por marca
- Pipeline de comparacion de precios contra inventario
- Limpieza y mapeo de nombres de modelo (JSON por marca/pais)
- Exportacion de resultado a CSV

### En progreso
-

### Por hacer
-

## Que hace

1. Descubre y filtra las URLs del catalogo del sitio web oficial de la marca
2. Guarda y compara las URLs para detectar modelos nuevos o eliminados
3. Scrapea cada URL usando Firecrawl (batch_scrape con changeTracking en modo git-diff)
4. Extrae nombre del modelo, precio, tipo de precio, moneda, estado de cambio y timestamp previo
5. Limpia y mapea los nombres de modelo para cruzarlos con el inventario
6. Lee el inventario interno desde Google Sheets
7. Hace merge entre scraping e inventario por modelo y anio
8. Calcula la diferencia de precio aplicando el fee de Galgo configurado por marca
9. Exporta el resultado a CSV

## Flujo general

```text
[Proceso 1 — brand_urls.ipynb]
Sitio web de la marca → Firecrawl map → Filtro por marca → JSON brand_urls/{marca}.json

[Proceso 2 — tracking_prices.ipynb]
JSON brand_urls/{marca}.json → Firecrawl batch_scrape (changeTracking) → df_scraped
                                                                              ↓
Google Sheets [MKP] Precios → df_inventory (filtrado por marca) → Merge (modelo + anio)
                                                                              ↓
                                                          build_price_comparison → CSV
```

## Arquitectura

```
tracking_prices_changes/
├── notebooks/
│   ├── brand_urls.ipynb           # Proceso 1: descubrimiento y guardado de URLs
│   └── tracking_prices.ipynb      # Proceso 2: scraping y comparacion de precios
├── src/
│   ├── config/
│   │   ├── settings.py            # Rutas base y COUNTRY
│   │   └── brand_configs.py       # BRAND_FEES: fee de Galgo por marca
│   ├── core/
│   │   ├── scraper/
│   │   │   └── app.py             # ScrapingUtils: descubre URLs con Firecrawl map
│   │   ├── urls_tracking/
│   │   │   └── urls_tracking.py   # Filtros de URLs por marca y compare_urls
│   │   ├── price_tracking/
│   │   │   ├── price_tracking.py  # run_price_tracking: batch_scrape + changeTracking
│   │   │   ├── utils.py           # Parseo de precios, nombres de modelo y anio
│   │   │   └── brands/
│   │   │       ├── italika.py     # Parseo especifico para Italika
│   │   │       └── bajaj.py       # Parseo especifico para Bajaj
│   │   └── italika_pipeline.py    # build_price_comparison: merge + fee + price_diff
│   ├── data/
│   │   └── json/
│   │       ├── brand_urls/        # URLs guardadas por marca (italika.json, bajaj.json)
│   │       └── replace_name/MX/  # Mapeo de nombres por marca ({marca}_mapeo_nombres.json)
│   ├── sources/
│   │   └── sheets/
│   │       ├── client.py          # Autenticacion con Google Sheets
│   │       └── reader.py          # Lectura y escritura de hojas
│   └── utils/
│       ├── clean_model_name.py    # Limpia nombres: elimina marca, colores, conectores
│       └── replace_model_name.py  # Carga y aplica el mapeo JSON de nombres de modelo
├── context/
├── env_example
└── .gitignore
```

| Archivo | Funcion |
|---|---|
| `src/core/price_tracking/price_tracking.py` | Ejecuta el scraping y construye las filas de resultado por URL |
| `src/core/italika_pipeline.py` | Merge scraping-inventario, aplica fee de Galgo, calcula price_diff |
| `src/core/urls_tracking/urls_tracking.py` | Filtros de URLs por marca y deteccion de URLs nuevas |
| `src/data/json/replace_name/MX/` | JSONs de mapeo de nombres para resolver discrepancias entre scraping e inventario |

## Output

Archivo CSV guardado en el directorio de trabajo del notebook (`notebooks/`) con el nombre `{DDMMYYYY}-{brand_slug}_precios.csv`.

Columnas del CSV:

| Columna | Descripcion |
|---|---|
| `captured_at` | Timestamp UTC de la captura actual |
| `previous_scrape_at` | Timestamp del scrape anterior (segun Firecrawl) |
| `code` | Codigo del producto en el inventario interno |
| `brand` | Marca |
| `model` | Nombre del modelo en el inventario |
| `model_name` | Nombre del modelo scrapeado |
| `year` | Anio en el inventario |
| `year_scraped` | Anio extraido del scraping |
| `status` | Estado en el marketplace (available / no_stock) |
| `price_scraped` | Precio publicado en el sitio de la marca |
| `price_scraped_with_galgo_fee` | Precio scrapeado + fee de Galgo de la marca |
| `price_base` | Precio base en el inventario |
| `discount_amount` | Descuento en el inventario |
| `price_net` | Precio neto del inventario (price_base - discount_amount) |
| `price_diff` | Diferencia: price_scraped_with_galgo_fee - price_net |
| `price_type` | Tipo de precio scrapeado (contado / oferta / etc.) |
| `currency` | Moneda (MXN) |
| `change_status` | Estado de cambio segun Firecrawl (same / new / changed / removed) |
| `visibility` | Visibilidad de la pagina segun Firecrawl |
| `url_scraped` | URL del producto en el sitio de la marca |
| `marketplace_url` | URL del producto en galgo.com |

## Stack tecnico

| Tecnologia | Uso |
|---|---|
| Python 3.x | Lenguaje principal |
| Jupyter Notebooks | Punto de entrada para ejecucion |
| Firecrawl | Scraping y change tracking de sitios web |
| pandas | Transformacion de datos y merge |
| gspread / gspread-dataframe | Lectura y escritura en Google Sheets |
| python-dotenv | Carga de variables de entorno desde `.env` |

## Requisitos

```env
FIRECRAWL_API_KEY=<api key de Firecrawl>
```

Credenciales de Google Sheets: archivo `src/config/key-google-sheets.json` (cuenta de servicio). No se versiona.
