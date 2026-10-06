# Comprobaciones de preparación

Fecha: 6 de octubre de 2026. Python 3.12.14 para las comprobaciones locales.

- Sintaxis de los cinco módulos Python comprobada.
- Configuración importada con cuatro rutas de categorías principales y siete adicionales, resueltas como rutas absolutas desde la carpeta de datos.
- El módulo de Neo4j importa la configuración central sin iniciar una conexión; se comprueba la normalización de categorías.
- La importación adicional selecciona MySQL con `USE` antes de insertar. La secuencia se comprueba con conectores simulados y una reseña sintética, incluyendo el texto que se enviaría a MongoDB.

No se han iniciado ni conectado MySQL, MongoDB o Neo4j; no se han cargado datasets reales ni repetido gráficos. La prueba con conectores simulados no valida el comportamiento transaccional, permisos ni compatibilidad de los servicios. Seguir el README para una ejecución completa en bases destinadas al ejercicio. El cargador original conserva sus límites de repetición de cargas y manejo de excepciones.
