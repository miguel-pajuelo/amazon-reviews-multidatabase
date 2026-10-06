import json, os
import pymysql
from pymongo import MongoClient
from datetime import datetime
import configuracion as config
from pathlib import Path

# Alumnos: Jorge Ois de Pascual y Miguel Pajuelo Gomez

BASE_DIR = Path(__file__).resolve().parent



def parse_date(date_str):
    """Convierte '07 9, 2012' a objeto datetime para MySQL """
    return datetime.strptime(date_str, '%m %d, %Y')

def connect_db():
    # Conexión MySQL

    config_sin_db = config.MYSQL_CONFIG.copy()
    config_sin_db.pop("database")

    db_mysql = pymysql.connect(**config_sin_db) # Doble asterisco que Pablo me conto
    cursor = db_mysql.cursor()
    
    # Conexión MongoDB
    client_mongo = MongoClient(config.MONGO_CONFIG['uri'])
    db_mongo = client_mongo[config.MONGO_CONFIG['db_name']]
    coll_mongo = db_mongo[config.MONGO_CONFIG['collection_name']]
    
    return db_mysql, cursor, coll_mongo

def setup_structure(cursor):
    """Crea las tablas en MySQL si no existen"""
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.MYSQL_CONFIG['database']}")
        cursor.execute(f"USE {config.MYSQL_CONFIG['database']}")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Usuarios (
                    reviewerID          VARCHAR(50) PRIMARY KEY,
                    reviewerName        VARCHAR(50)
                )
            """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Categorias (
                    id_categoria        INT AUTO_INCREMENT PRIMARY KEY,
                    nombre_categoria    VARCHAR(50) UNIQUE
                )
            """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Articulos (
                    asin                VARCHAR(20) PRIMARY KEY,
                    id_categoria        INT,
                    FOREIGN KEY (id_categoria) REFERENCES Categorias(id_categoria) 
                )
            """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Reviews_Metadatos(
                    id_reviews          INT AUTO_INCREMENT PRIMARY KEY,
                    reviewerID          VARCHAR(50),
                    asin                VARCHAR(20),
                    overall             REAL,
                    unixReviewTime      INT,
                    reviewTime          DATE,
                    helpful_votes       INT,
                    helpful_total       INT,
                    FOREIGN KEY (reviewerID) REFERENCES Usuarios(reviewerID),
                    FOREIGN KEY (asin) REFERENCES Articulos(asin)
                )           
            """)
        print("Tablas MySQL cargadas correctamente")
    except Exception as e:
        conn.rollback()
        print(f"Exception: {e}")

def load_files(db_mysql, cursor, coll_mongo):
    for category, path in config.DATA_FILES.items():
        print(f"Procesando {category}...")
        file_path = BASE_DIR / path

        # 1. Asegurar que la categoría existe en MySQL y obtener su ID
        cursor.execute("INSERT IGNORE INTO Categorias (nombre_categoria) VALUES (%s)", (category,))
        db_mysql.commit()
        cursor.execute("SELECT id_categoria FROM Categorias WHERE nombre_categoria = %s", (category,))
        id_cat = cursor.fetchone()[0]

        mongo_buffer = []

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)

                fecha_sql = parse_date(data["reviewTime"]).strftime("%Y-%m-%d")

                # Usuario
                cursor.execute("INSERT IGNORE INTO Usuarios (reviewerID, reviewerName) VALUES (%s, %s)", 
                               (data['reviewerID'], data.get('reviewerName', 'Unknown')))

                # Artículo
                cursor.execute("INSERT IGNORE INTO Articulos (asin, id_categoria) VALUES (%s, %s)", 
                               (data['asin'], id_cat))

                # Metadatos 
                sql_meta = """INSERT INTO Reviews_Metadatos 
                              (reviewerID, asin, overall, unixReviewTime, reviewTime, helpful_votes, helpful_total) 
                              VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql_meta, (
                    data['reviewerID'], data['asin'], data['overall'], 
                    data['unixReviewTime'], fecha_sql, data['helpful'][0], data['helpful'][1]
                ))

                # Mongo DB
                mongo_buffer.append({
                    "reviewerID": data['reviewerID'],
                    "asin": data['asin'],
                    "reviewText": data.get('reviewText', ''),
                    "summary": data.get('summary', '')
                })

                # Insertar en bloques de 500 
                if len(mongo_buffer) >= 500:
                    coll_mongo.insert_many(mongo_buffer)
                    mongo_buffer = []
                    db_mysql.commit()
                
            if mongo_buffer:
                coll_mongo.insert_many(mongo_buffer)
            db_mysql.commit()
        print("Carga finalizada con exito")

if __name__ == "__main__":
    try:
        conn, cursor, mongo_coll = connect_db()
        setup_structure(cursor)
        load_files(conn, cursor, mongo_coll)
        cursor.close()
        conn.close()
    except Exception as e:
        conn.rollback()
        print(f"Error : {e}")
        os._exit(0)
