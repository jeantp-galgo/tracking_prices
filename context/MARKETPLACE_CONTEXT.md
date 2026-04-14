Marketplace Galgo — Documentación técnica
1. Estados de disponibilidad de modelos
Un modelo en el marketplace puede estar en uno de tres estados desde la perspectiva del usuario en la PDP:
Disponible — Sin mensajes adicionales. El usuario ve el modelo normalmente y puede iniciar el flujo de cotización sin restricciones.
Sin stock (no stock) — El modelo sigue visible y cotizable, pero la PDP muestra un banner indicando bajo stock y posible extensión en tiempos de entrega. El usuario puede avanzar, pero con la expectativa de que no hay unidades inmediatas.
Descontinuado — El modelo aparece en la PDP pero está bloqueado funcionalmente: se muestra un mensaje de no disponibilidad y el CTA de cotización está deshabilitado. No hay forma de que el usuario avance con ese modelo.
2. Estructura de publicaciones y variantes
Cada publicación en el marketplace corresponde a un modelo base (ej: Bajaj Pulsar N250). Dentro de la PDP de ese modelo, el usuario puede seleccionar entre los años disponibles mediante selectores visuales.
La granularidad mínima es la combinación año × color, y cada combinación tiene un SKU único. Es decir, el SKU no está determinado por el año ni por el color de forma aislada, sino por la intersección de ambos.
Comportamiento por defecto al cargar la PDP:

Se selecciona automáticamente el año más reciente disponible.
Dentro de ese año, se asigna un color por defecto.
La URL inicial llega limpia, sin parámetros.

Comportamiento al interactuar:

Cambiar de año → se asigna un color por defecto para ese año → el SKU cambia → la URL se actualiza con parámetros.
Cambiar de color dentro del mismo año → el SKU cambia → la URL se actualiza.

En resumen: publicación = modelo base, variante = año × color, cada variante = un SKU único.
3. Gestión de modelos y años (Retool)
La administración del catálogo se realiza desde Retool, que funciona como el backoffice de inventario. Desde ahí se puede:

Crear modelos nuevos (publicaciones base).
Agregar nuevos años a modelos existentes.
Modificar precios de variantes existentes.

Los cambios se reflejan en la publicación del marketplace una vez guardados en Retool. Es decir, si se crea un año nuevo para un modelo, este aparece disponible en la PDP como una opción seleccionable.
4. Título SEO de la publicación
El título de pestaña (title tag) de cada PDP sigue la estructura: Marca + Modelo + Último año disponible | Galgo + País. Ejemplo: Bajaj Pulsar N 250 2026 | Galgo México.
El año que aparece en el título corresponde siempre al año más reciente disponible en la publicación. Dado que los años disponibles pueden cambiar (por ejemplo, al agregar un año nuevo desde Retool), existe un proceso interno de validación y ajuste del título SEO.
Estado actual del proceso: la actualización del título es manual. No existe una alerta automática que detecte cuándo una publicación tiene un año nuevo disponible que no coincide con el título. Sin embargo, el flujo para ejecutar el ajuste ya está construido. La detección automática es una mejora pendiente.
Nota: cuando no se ha definido un título SEO personalizado, el marketplace usa un título por defecto cuya estructura exacta no está documentada internamente al momento.