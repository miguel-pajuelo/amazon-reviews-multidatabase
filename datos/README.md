# Datos de Amazon

Los once archivos JSON originales se conservan en el archivo local de la asignatura. Se excluyen del repositorio por tamaño y se cargan desde esta carpeta o desde `BBDD_DATA_DIR`.

Usar la versión histórica **Amazon review data, 5-core, 2014** de [Julian McAuley / UCSD](https://cseweb.ucsd.edu/~jmcauley/datasets/amazon/links.html), cuyo esquema incluye `reviewerID`, `asin`, `helpful`, `reviewTime`, `unixReviewTime`, `overall`, `reviewText` y `summary`. Descargar el gzip de cada categoría y descomprimirlo como JSON de una reseña por línea. La versión Amazon 2023 tiene otro esquema y no es un sustituto directo.

| Grupo | Categoría en el código | Archivo esperado |
|---|---|---|
| Principal | Digital_Music | `Digital_Music_5.json` |
| Principal | Musical_Instruments | `Musical_Instruments_5.json` |
| Principal | Toys_and_Games | `Toys_and_Games_5.json` |
| Principal | Video_Games | `Video_Games_5.json` |
| Adicional | Instant_Video | `Amazon_Instant_Video_5.json` |
| Adicional | Phones_and_Accessories | `Cell_Phones_and_Accessories_5.json` |
| Adicional | Clothing_Shoes_and_Jewelry | `Clothing_Shoes_and_Jewelry_5.json` |
| Adicional | Grocery_and_Food | `Grocery_and_Gourmet_Food_5.json` |
| Adicional | Office_Products | `Office_Products_5.json` |
| Adicional | Pet_Supplies | `Pet_Supplies_5.json` |
| Adicional | Sports_and_Outdoors | `Sports_and_Outdoors_5.json` |

Para reutilizar la copia local, indicar como `BBDD_DATA_DIR` la ruta absoluta de `BBDD/trabajo/datos`. No es necesario copiar de nuevo los datasets al repositorio. Las bases MySQL y MongoDB deben estar vacías al realizar la primera carga; el cargador original inserta nuevamente las reseñas si se repite.
