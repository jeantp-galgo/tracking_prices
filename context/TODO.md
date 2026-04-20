## ✅ Completado

- [x] Log histórico de diferencias de precio: CSV acumulativo en data/logs/price_diff_log.csv — ✔ 2026-04-14 14:00
- [x] Notificación por correo consolidada cuando existan diferencias de precio — ✔ 2026-04-20 12:38
- [x] Registrar créditos Firecrawl consumidos por corrida en hoja scraping_costs — ✔ 2026-04-20 15:05
- [x] Validar variables de entorno antes de ejecutar, eso evita que los inputs y outputs no interfieran cuando se haya scrapeado — ✔ 2026-04-20 16:20
- [x] Simplificar log de costos Firecrawl a una fila por marca con columnas mapping/scrapping — ✔ 2026-04-20 15:29

## 🔄 En progreso

- [ ] Bajaj
- [ ] Agregar en el output precio original y precio de oferta + cálculo de descuento (ver DESIGN_precio_original_y_descuento.md)

## 📋 Por hacer

- [ ] Automatizar con una frecuencia de actualización semanal, todos los martes
- [ ] Hacerlo mas user-friendly: renombrar columnas
- [ ] Exportar SOP (para el equipo no técnico)
- [ ] Explicar en el archivo de gsheets el funcionamiento y puntos importantes (puede ser una hoja principal que explique un poco su funcionamiento)
- [ ] Agregar una columna que haga la diferencia de precios sin tener el fee de Galgo
- [ ] Ordenar output por modelo
- [ ] Validar URLs y modelos. Se puede hacer un mapeo del nombre basado en la URL
- [ ] Consolidar scraping en un solo archivo: Outputs de marcas ahora quedará en hojas individuales en un mismo archivo

## 💡 Backlog / Futuras mejoras

- [ ] Honda
- [ ] TVS
- [ ] Vento
- [ ] Suzuki
- [ ] CFLITE
- [ ] CF Moto (no solicitado pero hace parte de la familia CF)
- [ ] Scraping desde 3 fuentes
