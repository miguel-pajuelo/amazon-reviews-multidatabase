# Procedencia y selección de versiones

Trabajo compartido de Miguel Pajuelo Gómez y Jorge Ois de Pascual. Se conservan las cabeceras de autoría.

Los cinco módulos Python y los requisitos de trabajo y entrega coinciden por SHA-256. Se seleccionan los de trabajo como base de la copia. La memoria incluida es el PDF de la entrega descomprimida; el PDF de trabajo es una variante diferente conservada en el archivo local. El póster incluido procede de trabajo.

`configuracion.py` se adapta para leer credenciales del entorno y resolver las once rutas desde `datos/` o `BBDD_DATA_DIR`. La copia de `neo4JProyecto.py` usa esa configuración central y crea una carpeta de imágenes portable. En `insertar_dataset.py` se selecciona la base MySQL antes de importar una categoría adicional: el conector original abre la conexión sin base para permitir la creación inicial, y la importación adicional no la seleccionaba. Las consultas de análisis y las reglas de carga mantienen el comportamiento del ejercicio.

Datos: [Amazon product data, versión histórica 2014, Julian McAuley / UCSD](https://cseweb.ucsd.edu/~jmcauley/datasets/amazon/links.html). Se documentan las categorías y nombres en [datos/README.md](datos/README.md). Los datasets completos se conservan fuera de esta carpeta y no se han redistribuido como parte de la preparación.
