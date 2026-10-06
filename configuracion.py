"""Configuración portable. Exportar variables de entorno; no se carga .env."""
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("BBDD_DATA_DIR", str(BASE_DIR / "datos"))).expanduser().resolve()
MYSQL_CONFIG = {
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "database": os.environ.get("MYSQL_DATABASE", "amazon_reviews"),
}
MONGO_CONFIG = {
    "uri": os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/"),
    "db_name": os.environ.get("MONGO_DATABASE", "amazon_reviews"),
    "collection_name": os.environ.get("MONGO_COLLECTION", "reviews"),
}
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")
DATA_NAMES = {'Digital_Music': 'Digital_Music_5.json', 'Musical_Instruments': 'Musical_Instruments_5.json', 'Toys_and_Games': 'Toys_and_Games_5.json', 'Video_Games': 'Video_Games_5.json'}
EXTRA_DATA_NAMES = {'Instant_Video': 'Amazon_Instant_Video_5.json', 'Phones_and_Accessories': 'Cell_Phones_and_Accessories_5.json', 'Clothing_Shoes_and_Jewelry': 'Clothing_Shoes_and_Jewelry_5.json', 'Grocery_and_Food': 'Grocery_and_Gourmet_Food_5.json', 'Office_Products': 'Office_Products_5.json', 'Pet_Supplies': 'Pet_Supplies_5.json', 'Sports_and_Outdoors': 'Sports_and_Outdoors_5.json'}
DATA_FILES = {k: str(DATA_DIR / name) for k, name in DATA_NAMES.items()}
EXTRA_DATA_FILES = {k: str(DATA_DIR / name) for k, name in EXTRA_DATA_NAMES.items()}
