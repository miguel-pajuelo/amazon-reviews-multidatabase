# Amazon Reviews Analysis with MySQL, MongoDB and Neo4j

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?logo=mysql&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-4581C3?logo=neo4j&logoColor=white)

**One reviews dataset, three database models: structured metadata, review documents and user/product graphs.**

Academic project by **Miguel Pajuelo Gómez and Jorge Ois de Pascual** for *Bases de Datos*, ICAI, Universidad Pontificia Comillas. Python coordinates ingestion, cross-database queries, visual analysis and a simple popularity-based recommendation workflow.

[Usage examples](#the-project-in-use) · [Architecture](#architecture) · [Data model](#relational-data-model) · [Setup](#setup) · [Execution](#execution) · [Report](documentacion/memoria.pdf)

## The project in use

The practical goal is to turn large review files into questions a user can answer interactively: **how people rate products, how review activity changes, which products attract the most reviews and which items a user has not consumed**.

| User question | Application action | Output |
|---|---|---|
| What ratings do reviewers give? | Choose option **3** in `menu_visualizacion.py`. | Rating-frequency chart. |
| How does review activity change by year? | Choose option **1**, then a category or `todo`. | Annual review counts. |
| Which products have the most reviews? | Choose option **2**. | Products ordered by review count. |
| What could this user try next? | Choose option **8**, then a user and category. | Up to ten popular products the user has not consumed. |
| How are reviewers and products connected? | Run the scenarios in `neo4JProyecto.py`. | Similarity and consumption graphs after a database run. |

### Example: review ratings

![Actual rating distribution from the four original source datasets](.codex/visuals/usage_rating_distribution.png)

### Example: review activity over time

![Actual annual review counts for digital music, musical instruments, toys and games, and video games](.codex/visuals/usage_reviews_by_year.png)

### Example: popular products

![Six products with the highest review counts in the original source files](.codex/visuals/usage_popular_products.png)

**Where these examples come from:** all **474,344 records** in the four original primary JSON files were streamed and aggregated directly. The counts, input-file hashes and category scope are recorded in [usage_analysis.json](.codex/visuals/usage_analysis.json). These figures show the analyses supported by the application using real coursework input data. They are newly rendered source-file analyses, **not screenshots of a live MySQL/MongoDB/Neo4j session**.

The files are a historical 5-core snapshot spanning 1998–2014. They do not represent all Amazon purchases or reviews; the final year's count is bounded by the snapshot and should not be interpreted as a full-year market decline. No raw review text or individual reviewer details are published with these examples.

## What the project demonstrates

- **Data modelling:** choosing relational tables, document storage and graph relationships for different parts of the same domain.
- **ETL in Python:** reading line-delimited review JSON, normalising metadata and batching review texts into MongoDB.
- **SQL and graph analysis:** joining users and products, calculating user similarity with Pearson correlation and exploring consumption relationships.
- **Visual exploration:** review activity over time, ratings, popular products, word clouds and graph visualisations.

## Architecture

![Amazon reviews ingestion and analysis across MySQL, MongoDB and Neo4j](.codex/visuals/architecture.png)

MySQL stores structured entities and ratings; MongoDB stores review text and summaries with `reviewerID` and `asin` for application-level lookups. Neo4j graphs are built from MySQL query results. This is an academic integration, without a distributed transaction layer across the three services.

## Relational data model

The following diagram follows the tables and foreign keys created in [`load_data.py`](load_data.py). Foreign-key columns are nullable in the original schema.

![Relational tables, nullable foreign keys and separate MongoDB review documents](.codex/visuals/data_model.png)

## Repository guide

| Module | Responsibility |
|---|---|
| [configuracion.py](configuracion.py) | Database connection settings and portable dataset paths. |
| [load_data.py](load_data.py) | Schema creation and ingestion of four main review categories. |
| [insertar_dataset.py](insertar_dataset.py) | Ingestion of seven additional categories. |
| [menu_visualizacion.py](menu_visualizacion.py) | Interactive SQL/document analysis, charts and recommendations. |
| [neo4JProyecto.py](neo4JProyecto.py) | Pearson similarity, user/product/category graphs and visualisation. |
| [Dataset instructions](datos/README.md) | Expected files and the historical Amazon review format. |
| [Report](documentacion/memoria.pdf) / [Poster](documentacion/poster.pdf) | Original submission and proposed extensions. |

## Setup

You need Python and accessible **MySQL, MongoDB and Neo4j** services. The repository does not bundle or automatically start database servers.

### 1. Install Python dependencies

PowerShell, from this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On Linux/macOS, use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe` in the commands below.

### 2. Configure connections and data

Use [.env.example](.env.example) as the complete reference. Variables must be exported in the shell; the file is not read automatically. PowerShell example:

```powershell
$env:MYSQL_USER = "YOUR_MYSQL_USER"
$env:MYSQL_PASSWORD = "YOUR_LOCAL_MYSQL_PASSWORD"
$env:NEO4J_PASSWORD = "YOUR_LOCAL_NEO4J_PASSWORD"
$env:BBDD_DATA_DIR = "C:\absolute\path\to\review_datasets"
```

| Service | Default configuration |
|---|---|
| MySQL | `127.0.0.1:3306`, database `amazon_reviews`; user needs schema/data creation permissions. |
| MongoDB | `mongodb://127.0.0.1:27017/`, database `amazon_reviews`, collection `reviews`. |
| Neo4j | `bolt://127.0.0.1:7687`, database `neo4j`; use a dedicated exercise database/instance. |

Prepare the eleven dataset files described in [datos/README.md](datos/README.md). The code expects the historical **5-core Amazon reviews format**, not Amazon 2023. Large JSON files and local passwords are excluded from Git.

## Execution

With the services running, use databases dedicated to this project. Load the main categories **once into empty databases**:

```powershell
.\.venv\Scripts\python.exe load_data.py
.\.venv\Scripts\python.exe menu_visualizacion.py
```

To add the supplementary categories:

```powershell
.\.venv\Scripts\python.exe insertar_dataset.py
```

To run the interactive graph scenarios:

```powershell
.\.venv\Scripts\python.exe neo4JProyecto.py
```

**Database behaviour to know:** repeated ingestion does not deduplicate review records. Each Neo4j scenario calls `limpiar_neo4j`, deleting all nodes and relationships in the selected graph database before rebuilding it. Use a dedicated instance/database. Generated figures are written to `imagenes/`, which is excluded from Git.

## Implemented analysis and scope

| Implemented in the selected code | Discussed as future extensions in the report |
|---|---|
| SQL aggregations and document-backed word clouds. | A trained matrix-factorisation recommendation model. |
| Pearson user similarities and consumption graphs. | A complete collaborative-filtering evaluation pipeline. |
| Popularity-based suggestions excluding consumed items. | Benchmark metrics for recommendation quality. |

The architecture diagrams describe the code and schema. The new usage charts are direct source-file calculations; no database services were started to generate them. Earlier configuration and ingestion checks used a synthetic record and simulated connectors, as recorded in VALIDACION.md.

The original loader retains limitations in repeat loads and exception handling, including references to `conn` before connection creation in some error paths. See [VALIDACION.md](VALIDACION.md) for the precise checks and [PROCEDENCIA.md](PROCEDENCIA.md) for the selected versions and portability changes.
