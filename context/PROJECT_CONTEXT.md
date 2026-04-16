# tracking_prices_changes — Contexto del Proyecto

## Que es

Sistema de seguimiento de precios de catalogos de marcas de motos y scooters. Scrapea los sitios web oficiales de cada marca disponible usando Firecrawl Change Tracking, cruza los precios obtenidos contra el inventario interno del marketplace y exporta un archivo CSV con la comparacion de precios por modelo.

Esta diseñado para soportar multiples marcas. Actualmente opera con Italika y Bajaj. Cada marca tiene su propio modulo de parseo y su archivo de mapeo de nombres para resolver discrepancias entre los nombres del sitio web y los del inventario interno.

## Que hace

1. Descubre y filtra las URLs del catalogo del sitio web oficial de la marca
2. Guarda y compara las URLs para detectar modelos nuevos o eliminados
3. Scrapea cada URL usando Firecrawl
4. Extrae nombre del modelo, precio, tipo de precio, moneda, estado de cambio y timestamp previo
5. Limpia y mapea los nombres de modelo para cruzarlos con el inventario
6. Lee la base de inventario (se tiene una hoja específica para esto que viene desde Google Sheets)
7. Hace un cruce entre la información scrapeada e inventario por modelo y año, con fallback al año mas reciente disponible si no hay match exacto
8. Calcula la diferencia de precio teniendo en cuenta el fee de Galgo configurado por marca
9. Exporta el resultado al archivo de Comparativa de precios en la hoja correspondiente a la marca
10. Registra en un log historico CSV los modelos con diferencia de precio distinta de cero

## Como interpretar la diferencia de precios

Esta seccion es clave para leer correctamente los resultados. El cruce de precios toma como referencia **nuestros propios modelos de base de inventario de Galgo**. Eso significa que la columna `price_diff` siempre se lee desde nuestra perspectiva:

| Valor de `price_diff` | Que significa para Galgo |
|---|---|
| **Positivo** (mayor a 0) | Estamos MAS CAROS que la marca |
| **Negativo** (menor a 0) | Estamos MAS BARATOS que la marca |
| Cero | El precio es identico al de la marca |

**Como se calcula:** Se toma el precio publicado por la marca en su sitio oficial, se le suma el fee de Galgo correspondiente, y ese resultado se compara contra el precio neto de nuestro inventario.

> **Ejemplo practico:** Si `price_diff = 500`, el precio de Galgo es $500 MXN mas caro que lo que publica la marca. Si `price_diff = -300`, Galgo esta $300 MXN mas barato que la marca.

**Por que el fee de Galgo importa:** El fee representa el costo operativo que Galgo agrega sobre el precio de la marca. Incluirlo en el calculo permite hacer una comparacion justa entre lo que cobra la marca y lo que cobramos nosotros en condiciones equivalentes.

> **Nota para equipos no tecnicos:** Para saber si estamos caros o baratos, solo revisa el signo de `price_diff`. Positivo = somos mas caros. Negativo = somos mas baratos. El numero indica la diferencia en pesos (MXN).

## Flujo general

```text
[Proceso 1 — Descubrir las urls]
Sitio web de la marca → Firecrawl map (extrae todas las URLs del sitio) → Filtro de URLs → Lista con todas las URLs de la página

[Proceso 2 — Seguimiento de cambios por URLs]
Lista con todas las URLs → Screapea con Firecrawl (usando la característica de changeTracking) → tabla con la información scrapeada
                                                                              ↓
Google Sheets [MKP] Precios (referencia de precios por modelos) → tabla de base de inventario(filtrado por marca)
                                                   ↓
                               Cruce por modelo + año → year_match_type = "exact"
                               Fallback (modelo, año mas reciente) → year_match_type = "fallback_year"
                                                   ↓
                                     Procesar cambios de precios (aplica fee, calcula price_diff)
                                                   ↓
                      Google Sheets [Scraping - MX] Comparativa de precios → hoja {BRAND_NAME}
                                                   ↓
                                     data/logs/price_diff_log.csv (solo filas con price_diff != 0)
```

## Output

### Hoja de Google Sheets (resultado principal)

El resultado se escribe en el archivo de Google Sheets **`[Scraping - MX] Comparativa de precios`**, en una hoja cuyo nombre es el `BRAND_NAME` seleccionado (ej. `Italika`, `Bajaj`). Cada ejecucion reemplaza todos los datos de esa hoja.

Columnas del output:

| Columna | Descripcion |
|---|---|
| `captured_at` | Timestamp UTC de la captura actual |
| `previous_scrape_at` | Timestamp del scrape anterior (segun Firecrawl) |
| `code` | Codigo del producto en el inventario interno |
| `brand` | Marca |
| `model` | Nombre del modelo en el inventario |
| `model_name` | Nombre del modelo scrapeado |
| `year` | Año en el inventario |
| `year_scraped` | Año extraido del scraping |
| `status` | Estado en el marketplace (available / no_stock) |
| `price_scraped` | Precio publicado en el sitio de la marca |
| `price_scraped_with_galgo_fee` | Precio scrapeado + fee de Galgo según la marca |
| `price_base` | Precio base en el inventario |
| `discount_amount` | Descuento |
| `price_net` | Precio neto del inventario (price_base - discount_amount) |
| `price_diff` | Diferencia: price_scraped_with_galgo_fee - price_net |
| `price_type` | Tipo de precio scrapeado (contado / oferta / etc.) |
| `currency` | Moneda (MXN) |
| `change_status` | Estado de cambio segun Firecrawl (same / new / changed / removed) |
| `visibility` | Visibilidad de la pagina segun Firecrawl |
| `year_match_type` | Tipo de match en el merge: `exact` (modelo + año) o `fallback_year` (modelo con año mas reciente disponible) |
| `url_scraped` | URL del producto en el sitio de la marca |
| `marketplace_url` | URL del producto en galgo.com |
