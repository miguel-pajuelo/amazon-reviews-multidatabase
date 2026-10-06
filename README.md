# Análisis de reseñas de Amazon con MySQL, MongoDB y Neo4j

Proyecto académico de **Miguel Pajuelo Gómez y Jorge Ois de Pascual** para Bases de Datos, ICAI, Universidad Pontificia Comillas.

Infraestructura de almacenamiento y análisis de reseñas de Amazon: MySQL conserva las entidades y metadatos estructurados, MongoDB los textos, y Neo4j los grafos de similitudes y consumo. Python coordina la carga, las consultas, la visualización y una recomendación sencilla de artículos no consumidos.

## Arquitectura y módulos

```text
JSON de reseñas ── load_data.py ──┬── MySQL: usuarios, categorías, artículos y valoraciones
                                └── MongoDB: textos y resúmenes
MySQL ── neo4JProyecto.py ── Neo4j: similitudes, artículos y relaciones de consumo
MySQL + MongoDB ── menu_visualizacion.py ── gráficos, nubes y recomendaciones
```

| Módulo | Responsabilidad |
|---|---|
| `configuracion.py` | Conexiones por variables de entorno y rutas de datos. |
| `load_data.py` | Creación de tablas e inserción de las cuatro categorías principales. |
| `insertar_dataset.py` | Incorporación de siete categorías adicionales. |
| `menu_visualizacion.py` | Distribuciones temporales, popularidad, valoraciones, nubes de palabras y recomendación. |
| `neo4JProyecto.py` | Similitud de Pearson, relaciones usuario-artículo-categoría y visualización de grafos. |

Consultar la [memoria de entrega](documentacion/memoria.pdf), el [póster](documentacion/poster.pdf) y la [procedencia de la selección](PROCEDENCIA.md).

## Preparación

Requiere Python y servicios accesibles de MySQL, MongoDB y Neo4j. Crear un entorno nuevo; los entornos del ordenador original no se distribuyen:

```sh
python -m venv .venv
# Activar .venv antes de instalar: ver instrucciones inmediatamente debajo.
python -m pip install -r requirements.txt
```

Activar `.venv` antes de instalar y ejecutar: `.venv\Scripts\Activate.ps1` en PowerShell o `. .venv/bin/activate` en un shell POSIX. Configurar las variables de `.env.example` en el shell; el archivo no se carga automáticamente. Por ejemplo, en PowerShell:

```powershell
$env:MYSQL_USER = "TU_USUARIO_MYSQL"
$env:MYSQL_PASSWORD = "TU_CONTRASENA_LOCAL"
$env:NEO4J_PASSWORD = "TU_CONTRASENA_NEO4J_LOCAL"
```

La base MySQL usada por defecto es `amazon_reviews`; el usuario necesita permisos para crearla y cargar sus tablas. MongoDB utiliza la base `amazon_reviews` y la colección `reviews`. Neo4j utiliza la base configurada en `NEO4J_DATABASE`; en una instalación Community normalmente es `neo4j`.

Preparar los once datasets siguiendo [datos/README.md](datos/README.md). El código utiliza el formato histórico de reseñas 5-core, no el esquema Amazon 2023. Para aprovechar los archivos conservados localmente, definir `BBDD_DATA_DIR` con la ruta absoluta a la carpeta de datos existente. No se incluyen los grandes JSON en Git.

## Ejecución

Desde esta carpeta, y en bases destinadas a este proyecto:

```sh
python load_data.py
python menu_visualizacion.py
python insertar_dataset.py
```

La carga inicial debe realizarse una sola vez en bases vacías. El cargador original no deduplica las reseñas al repetir una importación.

Los escenarios de Neo4j ejecutan `limpiar_neo4j`, que borra todos los nodos y relaciones de la base seleccionada antes de construir cada grafo. Ejecutarlos en una instancia/base dedicada al ejercicio:

```sh
python neo4JProyecto.py
```

Las imágenes generadas se guardan en `imagenes/`, que se excluye de Git.

## Alcance y estado

La recomendación implementada usa popularidad y artículos no consumidos. La memoria también propone filtrado colaborativo, factorización matricial y evaluación como ampliaciones; no se presentan como modelos entrenados por este código.

Las copias permiten configurar otra máquina sin conservar las contraseñas originales. Se mantienen los algoritmos y las consultas de los módulos seleccionados. La preparación no ha cargado ni consultado servicios reales; [VALIDACION.md](VALIDACION.md) distingue las comprobaciones locales del trabajo pendiente para una ejecución completa. El manejo de errores del cargador conserva limitaciones del original, incluido el uso de `conn` en algunas rutas de excepción antes de que exista una conexión.
