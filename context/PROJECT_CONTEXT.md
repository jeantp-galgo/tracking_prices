# Contexto del Proyecto: tracking_prices_changes

## Descripcion general

Este proyecto automatiza el monitoreo de precios de los modelos de la marca **Italika**. El sistema scrapea periodicamente el sitio web oficial de Italika para extraer informacion de cada modelo disponible y registrar sus precios, permitiendo detectar cambios a lo largo del tiempo y construir un historial de precios.

---

## Objetivo

Rastrear de forma sistematica los precios publicados en el sitio web de Italika por modelo, de modo que se pueda:

- Detectar cambios de precio (subidas, bajas, eliminaciones).
- Mantener un historial con fecha y hora de cada captura.
- Generar alertas o reportes cuando se detecten variaciones relevantes.

---

## Fuente de datos

| Campo | Detalle |
|---|---|
| Sitio web | [https://www.italika.mx](https://www.italika.mx) |
| Tipo de contenido | Paginas de producto individuales por modelo |
| Estructura esperada | Cada modelo tiene su propia URL con nombre, descripcion y precio(s) |
| Frecuencia de scraping | A definir segun necesidad operativa (diario / semanal) |

El sitio puede requerir renderizado de JavaScript para exponer los precios, por lo que se debe evaluar si Firecrawl por si solo es suficiente o si se necesita Playwright para contenido dinamico.

---

## Datos a extraer

Por cada modelo de Italika se deben capturar los siguientes campos:

| Campo | Descripcion | Ejemplo |
|---|---|---|
| `model_name` | Nombre del modelo tal como aparece en la pagina | `Italika FT150` |
| `url` | URL de la pagina del modelo | `https://www.italika.mx/motos/ft150` |
| `price` | Precio de lista publicado | `25,990` |
| `price_type` | Tipo de precio (contado, MSI, financiado, etc.) | `contado` |
| `currency` | Moneda del precio | `MXN` |
| `captured_at` | Timestamp de la captura | `2026-03-26T10:00:00` |

> Si la pagina muestra multiples precios para un mismo modelo (por ejemplo, precio de contado y precio a meses), se registran todos como filas separadas vinculadas al mismo modelo y timestamp.

### Nota sobre el año del modelo

Italika no publica el año del modelo en su sitio web. Por convencion, se hardcodea el valor `2026` en el campo correspondiente para todos los registros scrapeados. La base de inventario interna puede contener modelos de 2024, 2025 y 2026. La logica para resolver ambiguedades por año se definira en una etapa posterior cuando el sistema este mas maduro.

---

## Esquema de la base de inventario interna

La base de inventario interna es la fuente de referencia propia de la empresa. Sus campos son independientes de los del scraping y se documentan por separado para dejar claro el origen de cada dato.

| Campo | Descripcion | Ejemplo |
|---|---|---|
| `code` | Codigo de la publicacion | `ITA-FT150-26` |
| `brand` | Marca | `Italika` |
| `model` | Nombre del modelo | `FT150` |
| `year` | Año del modelo | `2026` |
| `price_base` | Precio base sin descuento | `27,500` |
| `discount_amount` | Monto de descuento aplicado | `1,510` |
| `price_net` | Precio neto (`price_base - discount_amount`) | `25,990` |

---

## Merge entre scraping e inventario interno

### Objetivo del merge

Despues de cada ejecucion del scraper, los precios obtenidos de Italika se cruzan con la base de inventario interna. El objetivo es habilitar comparaciones directas como:

- "El precio publicado en Italika es distinto al precio neto de nuestro inventario."
- "El modelo aparece en Italika pero no existe en nuestro inventario."
- "El modelo existe en nuestro inventario pero ya no aparece en el sitio de Italika."

### Mapeo de columnas antes del merge

Los nombres de los campos del scraping no coinciden necesariamente con los de la base de inventario interna. Antes de realizar el merge se aplica un paso de mapeo para unificar los nombres de columnas. Ejemplo de mapeo:

| Campo en scraping | Campo en inventario interno |
|---|---|
| `model_name` | `model` |
| `price` | `price_net` |
| `captured_at` | _(sin equivalente directo — se conserva como metadato)_ |

El mapeo exacto se define en el modulo de transformacion de datos (`src/data/`).

### Clave de union

El merge se realiza por modelo y año. Dado que el año se hardcodea como `2026` en el scraping, la clave efectiva de union es `(model, year)`.

### Resultado del merge

El dataset resultante combina los campos de ambas fuentes y permite calcular diferencias de precio, por ejemplo:

```
price_diff = price (scraping) - price_net (inventario)
```

Los registros sin correspondencia en alguno de los dos lados se identifican para analisis posterior (modelo nuevo, modelo descontinuado, etc.).

---

## Stack tecnologico

### Scraping

Se evaluan dos alternativas principales, que pueden usarse de forma combinada:

| Herramienta | Uso previsto | Notas |
|---|---|---|
| **Firecrawl** | Extraccion rapida de contenido HTML/Markdown estructurado | Preferido para paginas estaticas o con contenido expuesto en el HTML inicial |
| **Playwright** | Automatizacion de navegador para contenido dinamico (JavaScript) | Necesario si los precios se cargan via JS asincronico |
| Combinacion | Firecrawl para descubrimiento de URLs + Playwright para scraping detallado | Estrategia mas robusta si hay contenido mixto |

### Lenguaje y dependencias

| Componente | Tecnologia |
|---|---|
| Lenguaje principal | Python 3.x |
| Entorno virtual | `venv` (directorio `venv/` en la raiz del proyecto) |
| Configuracion de entorno | Variables de entorno via `.env` (basado en `env_example`) |
| Notebooks de analisis | Jupyter (directorio `notebooks/`) |

### Almacenamiento (a definir)

| Opcion | Descripcion |
|---|---|
| Base de datos local | SQLite o PostgreSQL via conectores en `src/sources/database/` |
| Google Sheets | Integracion disponible en `src/sources/sheets/` |
| Archivos planos | CSV / JSON como salida intermedia desde `scripts/` |

---

## Estructura del proyecto

```
tracking_prices_changes/
├── context/                    # Documentacion de contexto del proyecto
│   └── PROJECT_CONTEXT.md
├── notebooks/                  # Jupyter notebooks para exploracion y analisis
├── scripts/                    # Scripts standalone ejecutables directamente
├── src/
│   ├── config/                 # Archivos de configuracion (URLs base, parametros)
│   ├── core/                   # Logica de negocio principal
│   │   └── scraper/            # Modulo de scraping (Firecrawl / Playwright)
│   ├── data/                   # Procesamiento, limpieza y transformacion de datos
│   ├── sources/
│   │   ├── database/           # Conectores y modelos de base de datos
│   │   └── sheets/             # Integracion con Google Sheets / Excel
│   └── utils/                  # Funciones utilitarias compartidas
├── trash/                      # Archivos temporales o experimentos descartados
├── venv/                       # Entorno virtual de Python (no versionado)
├── .gitignore
└── env_example                 # Plantilla de variables de entorno requeridas
```

---

## Outputs esperados

### Registro historico de precios

Cada ejecucion del scraper debe producir un conjunto de registros que incluyan el modelo, el precio capturado y el timestamp. Esto permite:

- Comparar el precio actual con el precio anterior para detectar cambios.
- Consultar el historial completo de un modelo especifico.
- Generar reportes de variacion de precios en un rango de fechas.

### Deteccion de cambios

El sistema debe ser capaz de identificar y reportar:

- **Subida de precio**: el precio actual es mayor al ultimo registrado.
- **Bajada de precio**: el precio actual es menor al ultimo registrado.
- **Modelo nuevo**: aparece un modelo que no existia en la captura anterior.
- **Modelo eliminado**: un modelo que existia ya no aparece en el sitio.

### Formatos de salida previstos

| Formato | Uso |
|---|---|
| Base de datos | Almacenamiento principal con historial completo |
| Google Sheets | Reporte compartido para consulta no tecnica |
| CSV / JSON | Exportacion para analisis ad hoc en notebooks |

---

## Variables de entorno requeridas

A documentar en `env_example` conforme se integren los servicios. Se anticipan las siguientes:

```
# Firecrawl
FIRECRAWL_API_KEY=

# Google Sheets (si aplica)
GOOGLE_SHEETS_CREDENTIALS_PATH=
GOOGLE_SHEETS_SPREADSHEET_ID=

# Base de datos (si aplica)
DATABASE_URL=
```

---

## Estado del proyecto

- [x] Estructura de carpetas creada
- [x] Esquema de la base de inventario interna definido
- [x] Flujo de merge entre scraping e inventario documentado
- [ ] Definicion de herramienta de scraping (Firecrawl vs Playwright)
- [ ] Implementacion del scraper de modelos Italika
- [ ] Modelo de datos y esquema de almacenamiento
- [ ] Implementacion del mapeo de columnas y logica de merge
- [ ] Logica de deteccion de cambios de precio (scraping vs inventario)
- [ ] Resolucion de ambiguedad por año cuando el sistema este maduro
- [ ] Integracion con almacenamiento (base de datos / Google Sheets)
- [ ] Programacion de ejecucion periodica
