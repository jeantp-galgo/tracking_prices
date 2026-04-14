# SOP — tracking_prices_changes

## Proposito

Consultar y comparar los precios publicados en el sitio web oficial de una marca de motos contra el inventario interno del marketplace. El resultado se escribe en Google Sheets (una hoja por marca) con la diferencia de precio por modelo, el tipo de match del merge y el estado de cambio detectado por Firecrawl.

## Configuracion inicial

### Variables de entorno

```bash
cp env_example .env
```

Editar `.env` y completar:

```env
FIRECRAWL_API_KEY=<api key de Firecrawl>
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

## Proceso 1: Descubrimiento de URLs

**Notebook**: `notebooks/brand_urls.ipynb`

Ejecutar cuando se sospeche que el catalogo de la marca tiene URLs nuevas, o como paso previo si las URLs no se han actualizado recientemente.

1. Configurar la marca objetivo:

```python
BRAND = "Bajaj"  # Opciones actuales: "Bajaj", "Italika"
```

2. Ejecutar el notebook completo.
3. El sistema extrae todas las URLs del sitio, aplica el filtro de la marca y las compara con las guardadas en `src/data/json/brand_urls/{brand}.json`.
4. Si hay URLs nuevas, las agrega al JSON y las imprime en pantalla.

---

## Proceso 2: Scraping y comparacion de precios

**Notebook**: `notebooks/tracking_prices.ipynb`

1. Configurar la marca objetivo:

```python
BRAND_NAME = "Bajaj"  # Opciones actuales: "Bajaj", "Italika"
```

2. Las celdas iniciales cargan las URLs del sitio via `scraper.get_all_urls_from_website()`. Para una prueba puntual, sobreescribir `urls_to_scrape` con una lista manual antes de continuar.

3. Ejecutar hasta la seccion **5. Ejecutar price tracking**. Firecrawl procesara las URLs en batch y retornara markdown y datos de changeTracking por pagina.

4. La seccion **6** limpia y mapea los nombres de modelo. Si un modelo no tiene mapeo definido, se usa el nombre limpio tal como viene del scraping.

5. La seccion **7** hace el merge con el inventario leido desde Google Sheets (hoja `[MKP] Precios`, worksheet `price_data_mx`), filtrado por la marca seleccionada.

6. La seccion **8** construye el DataFrame final con `build_price_comparison()`, que aplica el fee de Galgo de la marca (definido en `src/config/brand_configs.py`) y calcula `price_diff`. El merge es en dos etapas:
   - **Exacto**: cruza por `modelo + anio`. Columna `year_match_type = "exact"`.
   - **Fallback**: para filas del inventario sin match por anio, cruza solo por modelo usando el anio scrapeado mas reciente disponible. Columna `year_match_type = "fallback_year"`.

7. La seccion **10** escribe el resultado en Google Sheets:
   - Archivo: `[Scraping - MX] Comparativa de precios`
   - Hoja: nombre de la marca seleccionada (ej. `Italika`, `Bajaj`)
   - Cada ejecucion reemplaza todos los datos previos de la hoja.

8. La seccion **11** registra en `data/logs/price_diff_log.csv` los modelos donde `price_diff != 0`. El archivo se crea automaticamente si no existe y se acumula con cada ejecucion.

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
