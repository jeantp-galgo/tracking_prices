# Amplitude Chart API Parser Notes

## Problema detectado

Al consumir `GET /api/3/chart/{chart_id}/csv`, para algunos charts la respuesta llega en `data` como **string CSV embebido**, no como objeto JSON estructurado (`series`, `seriesLabels`, `xValues`).

Adicionalmente, ese string puede incluir:

- una primera linea de titulo (por ejemplo, `Facturacion MX (ult. sugerido)`),
- filas vacias,
- columnas con tabs escapados/reales (`\\t` y `\t`),
- estructura jerarquica con celdas vacias que requieren `forward-fill`.

## Sintomas observados

- `AttributeError: 'str' object has no attribute 'get'` al asumir que `data` era dict.
- DataFrame con una sola columna (solo el titulo de la tabla).
- Valores con `\t` visibles en headers y celdas.
- Export a CSV sin las dimensiones esperadas (`model`, `year`, `color`, `price`, `brand`).

## Causa raiz

El parser trataba todos los casos como JSON estructurado o TSV simple, pero el payload real del chart era CSV quoted con una fila de titulo previa al header real.

## Correccion implementada

1. Normalizacion de payload:
   - Soporte para `data` como `dict`, JSON-string o CSV-string.
2. Parser CSV robusto:
   - Parseo con `csv.reader` para manejar quoted CSV de forma estable.
   - Deteccion del header real (primera fila con 2+ celdas no vacias).
   - Eliminacion solo de filas/columnas totalmente vacias.
   - Renombrado estable de columnas vacias/duplicadas.
3. Limpieza de texto:
   - Remocion de `\\t`/`\t` y saltos de linea en headers y valores.
4. Normalizacion jerarquica:
   - `forward-fill` en columnas categoricas para conservar contexto de dimensiones.

## Checklist rapido de validacion

- `df.shape` debe tener mas de una columna para charts con dimensiones.
- `df.columns.tolist()` debe incluir dimensiones esperadas + metrica.
- `df.head()` no debe mostrar `\t` en headers ni valores.
- `df.to_csv(..., index=False)` debe exportar todas las columnas.

