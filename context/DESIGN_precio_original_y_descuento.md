# Diseño: Captura de precio original y cálculo de descuento

**Fecha:** 2026-04-15  
**Estado:** Pendiente de implementación  
**Relacionado con:** TODO → "Agregar en el output precio tachado y no tachado"

---

## Contexto del problema

Actualmente el sistema captura un único precio por producto. En Bajaj, la página muestra
dos precios con etiquetas diferenciadas en el markdown:

```
$69,999.00 Precio              ← precio original (sin descuento)
$66,499.00Precio de oferta     ← precio final (precio con descuento)
```

El código hoy solo extrae el `Precio de oferta` gracias a `prefer_offer_keyword=True` en
`bajaj.py`. El precio original se ignora.

En Itálika **no hay descuento explícito**, solo un precio de contado. No aplica este cambio.

---

## Objetivo

1. Capturar el **precio original** (el que no tiene descuento) en una columna separada.
2. Calcular el **descuento absoluto** (`price_original - price_final`) cuando ambos existan.
3. No romper el comportamiento actual para Itálika ni para marcas futuras sin descuento.

---

## Cambios por archivo

### 1. `src/core/price_tracking/utils.py`

Agregar función nueva `parse_prices_pair`:

```python
def parse_prices_pair(markdown: str) -> dict:
    """
    Devuelve precio original y precio de oferta desde el markdown de Bajaj.
    
    Formato esperado en markdown:
        $69,999.00 Precio
        $66,499.00Precio de oferta
    
    Returns:
        {
            "price_original": "69,999.00",  # vacío si no existe
            "price_final":    "66,499.00",  # vacío si no existe
            "discount":       "3,500.00",   # vacío si alguno falta
        }
    """
    # Captura "$X Precio" que NO sea "Precio de oferta"
    # Negative lookahead (?!\s*de\s*oferta) evita falsos positivos
    original_match = re.search(
        r"\$([\d,]+(?:\.\d{2})?)\s*Precio(?!\s*de\s*oferta)",
        markdown,
        re.IGNORECASE,
    )
    price_original = original_match.group(1) if original_match else ""

    # Reutiliza la lógica existente de oferta
    price_final = _extract_offer_price(markdown)

    # Calcular descuento solo si ambos existen
    discount = ""
    if price_original and price_final:
        try:
            orig = float(price_original.replace(",", ""))
            final = float(price_final.replace(",", ""))
            diff = orig - final
            if diff > 0:
                discount = f"{diff:,.2f}"
        except ValueError:
            pass

    return {
        "price_original": price_original,
        "price_final": price_final,
        "discount": discount,
    }
```

---

### 2. `src/core/price_tracking/brands/bajaj.py`

- Reemplazar `get_price()` por `get_prices()` que devuelve el dict completo.
- Mantener `get_price()` como alias por compatibilidad si hace falta.

```python
from src.core.price_tracking.utils import (
    _model_name_from_markdown,
    _model_name_from_url,
    _extract_year_from_text,
    parse_prices_pair,
)

PRICE_TYPE = "oferta"
CURRENCY = "MXN"


def get_model_name(url: str, markdown: str) -> str:
    return _model_name_from_markdown(markdown) or _model_name_from_url(url)


def get_year(url: str, markdown: str) -> int | None:
    return _extract_year_from_text(markdown) or _extract_year_from_text(url) or 2026


def get_prices(markdown: str) -> dict:
    """Devuelve price_original, price_final y discount."""
    return parse_prices_pair(markdown)


def get_price(markdown: str) -> str:
    """Alias de compatibilidad — devuelve solo price_final."""
    return get_prices(markdown)["price_final"]
```

---

### 3. `src/core/price_tracking/price_tracking.py`

En `_build_row`, detectar si el brand handler tiene `get_prices()` y agregar las columnas nuevas:

```python
def _build_row(url: str, brand_name: str, page_data: Any, captured_at: str) -> dict[str, Any]:
    brand = _BRAND_HANDLERS[brand_name.strip().lower()]
    ct = getattr(page_data, "changeTracking", None) or getattr(page_data, "change_tracking", None)
    markdown = getattr(page_data, "markdown", "") or ""

    # Soporte para marcas con precio doble (original + oferta)
    if hasattr(brand, "get_prices"):
        prices = brand.get_prices(markdown)
        price = prices["price_final"]
        price_original = prices["price_original"]
        discount = prices["discount"]
    else:
        price = brand.get_price(markdown)
        price_original = ""
        discount = ""

    return {
        "brand_name":        brand_name,
        "model_name":        brand.get_model_name(url, markdown),
        "year_scraped":      brand.get_year(url, markdown),
        "url":               url,
        "price":             price,           # precio final (oferta o único)
        "price_original":    price_original,  # precio antes del descuento (vacío si no aplica)
        "discount":          discount,         # diferencia absoluta (vacío si no aplica)
        "price_type":        brand.PRICE_TYPE,
        "currency":          brand.CURRENCY,
        "captured_at":       captured_at,
        "change_status":     _get_ct_field(ct, "changeStatus", "change_status") or "",
        "previous_scrape_at":_get_ct_field(ct, "previousScrapeAt", "previous_scrape_at") or "",
        "visibility":        _get_ct_field(ct, "visibility") or "",
    }
```

---

## Comportamiento esperado por marca

| Marca    | `price` | `price_original` | `discount` |
|----------|---------|-----------------|------------|
| Bajaj (con oferta) | `66,499.00` | `69,999.00` | `3,500.00` |
| Bajaj (sin oferta) | `69,999.00` | `` | `` |
| Itálika  | `X,XXX.XX` | `` | `` |

---

## Riesgos

- **Bajaj sin oferta activa**: `price_original` quedará vacío. El campo `price` seguirá
  capturando el precio único correctamente a través de `_find_all_prices_in_markdown`.
  Hay que validar que en ese caso el negative lookahead no corte el único precio disponible.
- **Cambio de estructura HTML en Bajaj**: si la tienda deja de usar "Precio de oferta"
  como etiqueta, el extractor falla silenciosamente (devuelve vacío). Se detectaría en
  el log de cambios de Firecrawl.
- **Columnas nuevas en Google Sheets**: hay que agregar las columnas `price_original` y
  `discount` al sheet de Bajaj. No afecta a Itálika.

---

## Criterios de aceptación

- [ ] Bajaj con oferta → 3 campos poblados: `price`, `price_original`, `discount`
- [ ] Bajaj sin oferta → solo `price` poblado, los otros dos vacíos
- [ ] Itálika → sin cambios, `price_original` y `discount` vacíos
- [ ] El notebook principal `tracking_prices.ipynb` muestra las columnas nuevas en el output
- [ ] El log histórico `price_diff_log.csv` no se rompe con columnas nuevas
