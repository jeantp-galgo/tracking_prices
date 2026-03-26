# PRD: Tracking de cambios de precios — Italika

## 1. Resumen del producto

### 1.1 Titulo y version del documento

- PRD: tracking_prices_changes — Monitoreo automatizado de precios Italika
- Version: 1.0
- Fecha: 2026-03-26

### 1.2 Vision general del producto

Este proyecto automatiza el monitoreo de precios del catalogo de modelos publicados en el sitio web oficial de Italika (https://www.italika.mx). El sistema realiza scraping periodico para extraer el nombre, URL y precio(s) de cada modelo disponible, registrando cada captura con su timestamp correspondiente.

El proposito central es construir un historial de precios consultable que permita detectar variaciones a lo largo del tiempo: subidas, bajas, aparicion de nuevos modelos y eliminacion de modelos existentes. Los resultados se almacenan en una base de datos estructurada y se exportan a formatos de facil consumo como Google Sheets y CSV/JSON.

El sistema esta disenado para ejecutarse de forma desatendida, con minima intervencion manual una vez configurado, y para escalar a nuevas fuentes de datos si el negocio lo requiere en el futuro.

---

## 2. Problema que resuelve

### 2.1 Objetivos de negocio

- Contar con un registro historico y auditado de precios publicados por Italika para cada modelo de su catalogo.
- Detectar de forma automatica y oportuna cualquier cambio de precio (alza, baja o eliminacion de modelo) sin depender de revision manual del sitio web.
- Facilitar la toma de decisiones comerciales o de compra basadas en tendencias de precio observadas a lo largo del tiempo.
- Reducir el tiempo y esfuerzo operativo dedicado a la vigilancia manual de precios.

### 2.2 Objetivos del usuario

- Recibir alertas o reportes cuando se detecte un cambio de precio relevante.
- Consultar el historial de precios de cualquier modelo en un formato accesible (hoja de calculo o exportacion).
- Ejecutar el scraper de forma programada sin necesidad de intervencion tecnica recurrente.
- Acceder a los datos en bruto para realizar analisis ad hoc en notebooks de Jupyter.

### 2.3 Fuera de alcance (non-goals)

- No se contempla el scraping de sitios web distintos a Italika en esta version inicial.
- No se incluye una interfaz grafica de usuario (dashboard web) propia; la visualizacion se delega a Google Sheets y notebooks.
- No se realizara ninguna accion automatica derivada de los cambios de precio (por ejemplo, generar ordenes de compra o notificaciones push a dispositivos moviles).
- No se extraeran imagenes, videos, especificaciones tecnicas ni otro contenido de las paginas de producto mas alla de los campos definidos.
- No se contempla la comparacion de precios contra competidores distintos a Italika.

---

## 3. Usuarios objetivo

### 3.1 Tipos de usuario

- **Usuario analista**: consume los datos exportados (CSV, JSON, Google Sheets) para analisis de precios y generacion de reportes.
- **Usuario operativo / tecnico**: configura, ejecuta y monitorea el scraper; gestiona el entorno, las credenciales y la programacion de tareas.

### 3.2 Detalle de personas

- **Analista de precios**: profesional no necesariamente tecnico que necesita acceder a reportes actualizados de precios sin interactuar con el codigo fuente. Su canal principal es Google Sheets o un archivo CSV exportado.
- **Desarrollador / operador del sistema**: profesional tecnico responsable de mantener el scraper en funcionamiento, ajustar la frecuencia de ejecucion, gestionar las dependencias y resolver errores de scraping.

### 3.3 Acceso por rol

- **Operador tecnico**: acceso completo al repositorio, entorno virtual, base de datos y configuracion de variables de entorno.
- **Analista de precios**: acceso de solo lectura a Google Sheets compartida y a archivos de exportacion CSV/JSON.

---

## 4. Requerimientos funcionales

Los requerimientos se presentan con su identificador unico, descripcion y prioridad.

**RF-001 — Descubrimiento de URLs del catalogo** (Prioridad: Alta)

- El sistema debe recorrer el sitio web de Italika y recopilar todas las URLs de paginas de modelo disponibles en el catalogo.
- Debe detectar nuevas URLs que no existian en ejecuciones anteriores.
- Debe marcar como "eliminadas" las URLs que ya no esten presentes en el sitio.

**RF-002 — Extraccion de datos de precio por modelo** (Prioridad: Alta)

- Por cada URL de modelo, el sistema debe extraer los siguientes campos: `model_name`, `url`, `price`, `price_type`, `currency`, `captured_at`.
- Si una pagina de modelo expone multiples precios (contado, MSI, financiado, etc.), cada precio se debe registrar como una fila independiente vinculada al mismo modelo y timestamp.
- El sistema debe manejar tanto contenido HTML estatico como contenido renderizado dinamicamente via JavaScript.

**RF-003 — Almacenamiento del historial de precios** (Prioridad: Alta)

- Cada ejecucion del scraper debe persistir los registros extraidos en la base de datos principal con su timestamp de captura.
- Los registros historicos no deben ser sobreescritos; cada captura debe acumularse para permitir analisis temporal.

**RF-004 — Deteccion de cambios de precio** (Prioridad: Alta)

- El sistema debe comparar el precio de cada modelo en la ejecucion actual contra el ultimo precio registrado y clasificar el cambio como:
  - Subida de precio
  - Bajada de precio
  - Sin cambio
  - Modelo nuevo (primera aparicion)
  - Modelo eliminado (ausente en la captura actual)

**RF-005 — Generacion de reporte de cambios** (Prioridad: Alta)

- Al finalizar cada ejecucion, el sistema debe producir un reporte que liste unicamente los modelos con variacion detectada, indicando el precio anterior, el precio nuevo, el tipo de cambio y el timestamp.

**RF-006 — Exportacion a Google Sheets** (Prioridad: Media)

- El sistema debe poder exportar el historial de precios y el reporte de cambios a una hoja de calculo de Google Sheets definida por configuracion.
- La exportacion debe sobreescribir o actualizar las hojas correspondientes en cada ejecucion.

**RF-007 — Exportacion a CSV / JSON** (Prioridad: Media)

- El sistema debe generar archivos CSV y/o JSON con los datos capturados en cada ejecucion como salida intermedia para analisis en notebooks.
- Los archivos deben nombrarse incluyendo el timestamp de la ejecucion para facilitar su identificacion.

**RF-008 — Ejecucion programada** (Prioridad: Media)

- El scraper debe poder ejecutarse de forma programada (diaria o semanal) mediante un mecanismo de scheduling (cron, tarea programada del sistema operativo o equivalente).
- Debe ser posible ejecutarlo tambien de forma manual en cualquier momento.

**RF-009 — Registro de logs de ejecucion** (Prioridad: Media)

- Cada ejecucion debe generar un log que incluya: fecha y hora de inicio y fin, numero de modelos procesados, numero de cambios detectados y cualquier error o advertencia ocurrida.

**RF-010 — Manejo de errores de scraping** (Prioridad: Alta)

- Si una URL individual falla durante la extraccion, el sistema debe registrar el error en el log, omitir ese modelo en la ejecucion actual y continuar con el resto del catalogo.
- Si el sitio web completo no esta disponible, la ejecucion debe abortarse con un error claro en el log.

---

## 5. Requerimientos no funcionales

**RNF-001 — Resiliencia ante cambios del sitio web**

- El sistema debe ser capaz de continuar la ejecucion parcial ante errores en URLs individuales sin interrumpir el procesamiento del resto del catalogo.

**RNF-002 — Configurabilidad**

- Todos los parametros operativos (URL base, frecuencia, credenciales de base de datos, ID de Google Sheet, rutas de exportacion) deben estar definidos en variables de entorno via archivo `.env`, sin valores hardcodeados en el codigo fuente.

**RNF-003 — Reproducibilidad del entorno**

- El entorno de ejecucion debe ser reproducible mediante `venv` y un archivo `requirements.txt` actualizado.

**RNF-004 — Eficiencia de scraping**

- El sistema debe respetar tiempos de espera entre solicitudes para evitar sobrecargar el servidor de Italika y reducir el riesgo de bloqueo (rate limiting).

**RNF-005 — Trazabilidad**

- Cada registro almacenado debe incluir el timestamp exacto de captura para garantizar la integridad del historial.

**RNF-006 — Mantenibilidad**

- El codigo debe estar estructurado en modulos con responsabilidades claras (descubrimiento, extraccion, almacenamiento, deteccion de cambios, exportacion) para facilitar modificaciones futuras.

**RNF-007 — Seguridad de credenciales**

- Las credenciales de acceso (API keys de Firecrawl, credenciales de Google Sheets, etc.) no deben estar en el repositorio; deben gestionarse exclusivamente via variables de entorno o archivos de secretos excluidos del control de versiones.

---

## 6. Casos de uso principales

### CU-001 — Ejecucion programada del scraper

**Actor**: Sistema (tarea programada) / Operador tecnico
**Flujo normal**:
1. El scheduler invoca el script principal del scraper.
2. El sistema descubre todas las URLs del catalogo de Italika.
3. Por cada URL, extrae los campos definidos (modelo, precio(s), timestamp).
4. Compara los precios extraidos contra el ultimo registro en la base de datos.
5. Persiste todos los registros nuevos en la base de datos.
6. Genera el reporte de cambios detectados.
7. Exporta los datos a Google Sheets y/o CSV/JSON segun configuracion.
8. Registra el log de ejecucion.

**Flujo alternativo — URL con error**:
- En el paso 3, si una URL devuelve error, se registra en el log y se continua con la siguiente.

**Flujo alternativo — Sitio no disponible**:
- En el paso 2, si el sitio web no responde, la ejecucion se aborta y se registra el error.

### CU-002 — Consulta del historial de precios

**Actor**: Analista de precios
**Flujo normal**:
1. El analista accede a la Google Sheet compartida o al archivo CSV exportado.
2. Filtra por modelo o rango de fechas segun su necesidad.
3. Visualiza la evolucion de precios a lo largo del tiempo.

### CU-003 — Ejecucion manual del scraper

**Actor**: Operador tecnico
**Flujo normal**:
1. El operador activa el script manualmente desde la linea de comandos.
2. El sistema ejecuta el flujo completo descrito en CU-001.
3. El operador verifica el log de ejecucion para confirmar el resultado.

### CU-004 — Analisis ad hoc en notebook

**Actor**: Analista de precios / Operador tecnico
**Flujo normal**:
1. El usuario abre un notebook de Jupyter en el directorio del proyecto.
2. Carga el archivo CSV/JSON generado por la ultima ejecucion.
3. Realiza analisis exploratorio, graficas de tendencias u otras operaciones.

---

## 7. Consideraciones tecnicas

### 7.1 Puntos de integracion

- **Firecrawl API**: para extraccion rapida de contenido HTML/Markdown de paginas estaticas o con contenido expuesto en el HTML inicial. Requiere API key gestionada via variable de entorno.
- **Playwright**: para renderizado de paginas con contenido cargado dinamicamente via JavaScript. Se activara si Firecrawl no logra exponer los precios en el HTML inicial.
- **Google Sheets API**: para la exportacion de datos a hojas de calculo compartidas. Requiere credenciales OAuth2 o de cuenta de servicio gestionadas fuera del repositorio.
- **Base de datos local**: SQLite como opcion preferida para la version inicial por simplicidad; PostgreSQL como alternativa si se requiere acceso concurrente o despliegue en servidor.

### 7.2 Estrategia de scraping

- Evaluar primero si Firecrawl es suficiente para exponer los precios del sitio de Italika.
- Si los precios se cargan via JavaScript asincrono, incorporar Playwright para el scraping detallado de paginas individuales.
- Una estrategia combinada (Firecrawl para descubrimiento de URLs + Playwright para extraccion de precios) es la opcion mas robusta ante contenido mixto.

### 7.3 Almacenamiento y privacidad

- Los datos almacenados son exclusivamente precios y metadatos publicos del sitio web de Italika; no se manejan datos personales.
- Las credenciales de servicios externos (Firecrawl, Google Sheets) deben estar en `.env` y en `.gitignore`.
- Se recomienda realizar backups periodicos del archivo de base de datos SQLite si se usa como almacenamiento principal.

### 7.4 Escalabilidad y rendimiento

- Para la version inicial, el volumen de modelos en el catalogo de Italika es manejable con ejecucion secuencial; si el catalogo crece significativamente, se puede introducir procesamiento paralelo con limites de concurrencia.
- Se deben implementar delays entre solicitudes HTTP para respetar el rate limiting del servidor.
- El diseno de la base de datos debe incluir indices en los campos `model_name`, `url` y `captured_at` para optimizar las consultas historicas.

### 7.5 Desafios potenciales

- El sitio web de Italika puede cambiar su estructura HTML o sistema de carga de precios, rompiendo los selectores del scraper; se recomienda implementar validaciones que alerten cuando un campo esperado no se encuentra.
- El sitio puede implementar mecanismos anti-bot (CAPTCHAs, bloqueo por IP); se debe evaluar el uso de proxies rotatorios o delays adaptativos si esto ocurre.
- La precision en la normalizacion del campo `price` (eliminar comas, simbolos de moneda, espacios) es critica para la deteccion correcta de cambios.

---

## 8. Fuera de alcance

Los siguientes elementos quedan explicitamente excluidos de esta version del proyecto:

- Scraping de sitios web distintos a `italika.mx`.
- Comparacion de precios contra competidores o distribuidores terceros.
- Interfaz grafica web propia para visualizacion de datos.
- Notificaciones automaticas a dispositivos moviles (push, SMS, WhatsApp).
- Extraccion de especificaciones tecnicas, imagenes u otro contenido que no sea precio y metadatos de modelo.
- Gestion de inventario o disponibilidad de stock.
- Integracion con sistemas ERP o de compras.

---

## 9. Metricas de exito

### 9.1 Metricas centradas en el usuario

- El analista puede consultar el historial de precios de cualquier modelo sin asistencia tecnica.
- El reporte de cambios es legible y no requiere interpretacion adicional.
- La latencia entre la publicacion de un cambio de precio en el sitio de Italika y su deteccion en el sistema no supera un ciclo de ejecucion programada.

### 9.2 Metricas de negocio

- Cobertura del catalogo: al menos el 95% de los modelos listados en el sitio de Italika son capturados correctamente en cada ejecucion.
- Precision en la deteccion de cambios: 0 falsos positivos en la clasificacion de cambios de precio (es decir, no se reportan cambios cuando el precio no ha variado).
- Disponibilidad del historial: los datos de al menos los ultimos 90 dias estan disponibles para consulta.

### 9.3 Metricas tecnicas

- Tasa de error de scraping por ejecucion: menos del 5% de URLs del catalogo fallan en una ejecucion tipica.
- Tiempo de ejecucion completo: una ejecucion del scraper para el catalogo completo debe completarse en menos de 30 minutos.
- Uptime del scheduler: el scraper se ejecuta en al menos el 95% de las ventanas programadas sin intervencion manual.

---

## 10. Hitos y secuenciacion

### 10.1 Estimacion del proyecto

- Tamano: Pequeno-Mediano
- Estimacion total: 4-6 semanas para version funcional completa

### 10.2 Equipo y composicion

- Equipo reducido: 1 desarrollador Python con conocimientos de scraping y 1 analista de datos para validacion de outputs.

### 10.3 Fases sugeridas

**Fase 1 — Prototipo de scraping** (1-2 semanas)

- Validar si Firecrawl es suficiente o si se requiere Playwright para exponer los precios de Italika.
- Implementar el modulo de descubrimiento de URLs del catalogo.
- Implementar el modulo de extraccion de datos por modelo con los 6 campos definidos.
- Validar la normalizacion y calidad de los datos extraidos.

**Fase 2 — Almacenamiento e historial** (1 semana)

- Diseno e implementacion del esquema de base de datos (SQLite inicial).
- Implementacion de la logica de insercion de registros con timestamp.
- Implementacion del modulo de deteccion de cambios (subida, baja, nuevo, eliminado).

**Fase 3 — Reportes y exportacion** (1 semana)

- Generacion del reporte de cambios por ejecucion.
- Exportacion a CSV/JSON.
- Integracion con Google Sheets API para exportacion automatica.

**Fase 4 — Scheduling, logs y hardening** (1 semana)

- Configuracion del mecanismo de ejecucion programada.
- Implementacion del sistema de logging.
- Manejo robusto de errores por URL y por ejecucion.
- Documentacion del entorno y del proceso de despliegue.

**Fase 5 — Validacion y ajustes** (1 semana)

- Ejecuciones de prueba en condiciones reales.
- Validacion de la cobertura del catalogo y precision de la deteccion de cambios.
- Ajustes finos de selectores, delays y configuracion.

---

## 11. Historias de usuario

### 11.1 Descubrimiento del catalogo de modelos

- **ID**: RF-001
- **Descripcion**: Como operador tecnico, quiero que el sistema recorra automaticamente el sitio de Italika y recopile todas las URLs de modelos disponibles, para no tener que mantener una lista manual de paginas a monitorear.
- **Criterios de aceptacion**:
  - El sistema genera una lista de URLs de modelos del catalogo actual de Italika.
  - Las URLs nuevas respecto a la ejecucion anterior son identificadas como "modelos nuevos".
  - Las URLs ausentes respecto a la ejecucion anterior son marcadas como "modelos eliminados".
  - Si ninguna URL es encontrada (posible cambio estructural del sitio), el sistema registra una advertencia critica en el log.

### 11.2 Extraccion de precios por modelo

- **ID**: RF-002
- **Descripcion**: Como operador tecnico, quiero que el sistema extraiga el nombre, URL, precio(s), tipo de precio, moneda y timestamp de cada modelo del catalogo, para construir el historial de precios.
- **Criterios de aceptacion**:
  - Para cada modelo, se extraen al menos los campos: `model_name`, `url`, `price`, `price_type`, `currency`, `captured_at`.
  - Si un modelo tiene multiples tipos de precio, cada uno se registra como una fila separada.
  - El campo `price` es normalizado a un valor numerico sin simbolos de moneda ni separadores de miles.
  - Si un campo esperado no se encuentra en la pagina, el registro se marca con valor nulo y se registra una advertencia en el log.

### 11.3 Almacenamiento del historial

- **ID**: RF-003
- **Descripcion**: Como analista de precios, quiero que cada captura quede almacenada de forma permanente con su timestamp, para poder consultar la evolucion de precios a lo largo del tiempo.
- **Criterios de aceptacion**:
  - Cada ejecucion inserta registros nuevos en la base de datos sin sobreescribir los historicos.
  - Cada registro incluye el campo `captured_at` con precision de segundo.
  - Es posible consultar todos los precios registrados para un modelo especifico ordenados cronologicamente.
  - La base de datos persiste entre ejecuciones del scraper.

### 11.4 Deteccion de cambios de precio

- **ID**: RF-004
- **Descripcion**: Como analista de precios, quiero que el sistema compare automaticamente el precio actual de cada modelo contra el ultimo registrado y clasifique el cambio, para detectar variaciones sin revision manual.
- **Criterios de aceptacion**:
  - El sistema clasifica correctamente cada modelo en una de las siguientes categorias: sin cambio, subida de precio, bajada de precio, modelo nuevo, modelo eliminado.
  - La comparacion se realiza por `url` y `price_type` para garantizar que se comparan precios del mismo tipo.
  - Los modelos clasificados como "sin cambio" no aparecen en el reporte de cambios.
  - La clasificacion no genera falsos positivos cuando el precio no ha variado.

### 11.5 Generacion del reporte de cambios

- **ID**: RF-005
- **Descripcion**: Como analista de precios, quiero recibir un reporte al finalizar cada ejecucion que liste los modelos con cambios detectados, para tomar decisiones de forma oportuna.
- **Criterios de aceptacion**:
  - El reporte incluye: nombre del modelo, URL, precio anterior, precio nuevo, tipo de cambio y timestamp de la captura.
  - El reporte es generado al finalizar cada ejecucion, incluso si no hay cambios (en ese caso indica "sin cambios detectados").
  - El reporte es exportado como archivo y/o enviado a Google Sheets segun configuracion.

### 11.6 Exportacion a Google Sheets

- **ID**: RF-006
- **Descripcion**: Como analista de precios, quiero que los datos del historial y el reporte de cambios se actualicen automaticamente en Google Sheets, para consultarlos sin acceder al sistema tecnico.
- **Criterios de aceptacion**:
  - El sistema actualiza o crea las hojas designadas en Google Sheets al finalizar cada ejecucion.
  - La exportacion funciona con credenciales configuradas via variable de entorno.
  - Si la exportacion falla, el sistema registra el error en el log pero no interrumpe el guardado en la base de datos local.

### 11.7 Exportacion a CSV y JSON

- **ID**: RF-007
- **Descripcion**: Como analista de precios, quiero que los datos de cada ejecucion sean exportados en formato CSV y/o JSON, para poder cargarlos en notebooks de Jupyter y realizar analisis propios.
- **Criterios de aceptacion**:
  - El sistema genera al menos un archivo CSV con los registros de la ejecucion actual.
  - El nombre del archivo incluye el timestamp de la ejecucion.
  - Los archivos son guardados en el directorio configurado via variable de entorno.

### 11.8 Ejecucion programada sin intervencion manual

- **ID**: RF-008
- **Descripcion**: Como operador tecnico, quiero que el scraper se ejecute automaticamente segun una frecuencia configurada (diaria o semanal), para no tener que iniciarlo manualmente en cada ciclo.
- **Criterios de aceptacion**:
  - El sistema puede ser invocado por un scheduler externo (cron o equivalente) sin parametros adicionales.
  - La frecuencia de ejecucion es configurable sin modificar el codigo fuente.
  - La ejecucion programada produce los mismos resultados que la ejecucion manual.

### 11.9 Registro de logs de ejecucion

- **ID**: RF-009
- **Descripcion**: Como operador tecnico, quiero que cada ejecucion genere un log con el resultado, errores y estadisticas, para poder diagnosticar problemas y verificar que el sistema funciona correctamente.
- **Criterios de aceptacion**:
  - El log incluye: timestamp de inicio y fin, numero de modelos procesados, numero de cambios detectados, lista de URLs con error y descripcion del error.
  - Los logs se guardan en archivos con rotacion o en la base de datos, segun configuracion.
  - El nivel de detalle del log es configurable (INFO, WARNING, ERROR).

### 11.10 Manejo de errores por URL individual

- **ID**: RF-010
- **Descripcion**: Como operador tecnico, quiero que el sistema continue procesando el resto del catalogo aunque una URL individual falle, para que un error puntual no invalide toda la ejecucion.
- **Criterios de aceptacion**:
  - Si una URL retorna error HTTP o no expone los campos esperados, el error se registra en el log y se continua con la siguiente URL.
  - Si mas del 50% de las URLs fallan en una misma ejecucion, el sistema registra una alerta critica.
  - Los modelos con error en una ejecucion no se marcan como "eliminados"; se mantiene su ultimo precio registrado.

### 11.11 Configuracion segura de credenciales

- **ID**: RNF-007
- **Descripcion**: Como operador tecnico, quiero que todas las credenciales y parametros sensibles se gestionen via variables de entorno, para no exponer secretos en el repositorio de codigo.
- **Criterios de aceptacion**:
  - Ningun valor de credencial (API keys, passwords, tokens) aparece en el codigo fuente ni en archivos versionados.
  - El archivo `.env` esta incluido en `.gitignore`.
  - El proyecto incluye un archivo `.env.example` con las variables requeridas pero sin valores reales.
  - El sistema falla con un mensaje de error claro si una variable de entorno requerida no esta definida al iniciar la ejecucion.
