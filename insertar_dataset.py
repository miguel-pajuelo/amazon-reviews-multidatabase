import json
import configuracion as config
from load_data import connect_db, parse_date # Reutilizamos tus funciones

# Alumnos: Jorge Ois de Pascual y Miguel Pajuelo Gomez

def insertar_nuevo_dataset(nombre_categoria):
    db_mysql, cursor, coll_mongo = connect_db()
    # connect_db abre MySQL sin base para permitir la creación inicial.
    # La importación adicional utiliza la base ya creada por load_data.py.
    cursor.execute(f"USE {config.MYSQL_CONFIG['database']}")
    
    path = config.EXTRA_DATA_FILES[nombre_categoria]
    print(f"Insertando nuevos datos desde: {path}...")

    # Asegurar que la nueva categoría existe en MySQL
    cursor.execute("INSERT IGNORE INTO Categorias (nombre_categoria) VALUES (%s)", (nombre_categoria,))
    db_mysql.commit()
    cursor.execute("SELECT id_categoria FROM Categorias WHERE nombre_categoria = %s", (nombre_categoria,))
    id_cat = cursor.fetchone()[0]

    mongo_buffer = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            fecha_sql = parse_date(data["reviewTime"]).strftime("%Y-%m-%d")

            # MySQL - Usuarios y Artículos 
            cursor.execute("INSERT IGNORE INTO Usuarios (reviewerID, reviewerName) VALUES (%s, %s)", 
                           (data['reviewerID'], data.get('reviewerName', 'Unknown')))

            cursor.execute("INSERT IGNORE INTO Articulos (asin, id_categoria) VALUES (%s, %s)", 
                           (data['asin'], id_cat))

            # MySQL - Metadatos
            sql_meta = """INSERT INTO Reviews_Metadatos 
                          (reviewerID, asin, overall, unixReviewTime, reviewTime, helpful_votes, helpful_total) 
                          VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql_meta, (
                data['reviewerID'], data['asin'], data['overall'], 
                data['unixReviewTime'], fecha_sql, data['helpful'][0], data['helpful'][1]
            ))

            # MongoDB - Buffer para textos
            mongo_buffer.append({
                "reviewerID": data['reviewerID'],
                "asin": data['asin'],
                "reviewText": data.get('reviewText', ''),
                "summary": data.get('summary', '')
            })

            if len(mongo_buffer) >= 500:
                coll_mongo.insert_many(mongo_buffer)
                mongo_buffer = []
                db_mysql.commit()
        
        if mongo_buffer:
            coll_mongo.insert_many(mongo_buffer)
        db_mysql.commit()

    print(f"Dataset {nombre_categoria} insertado con éxito")
    cursor.close()
    db_mysql.close()

def validar_entrada():
    print("---------------------------")
    print("¿Qué dataset desea incluir?")
    
    opciones = list(config.EXTRA_DATA_FILES.keys())
    
    for i, key in enumerate(opciones):
        print(f"{i+1}: {key}")

    seleccion = input("Seleccione el número o el nombre del dataset o salir: ").strip()

    # Validar si es un número (índice)
    if seleccion.isdigit():
        indice = int(seleccion) - 1
        if 0 <= indice < len(opciones):
            return opciones[indice]
    
    # Validar si es el nombre exacto (key)
    if seleccion in config.EXTRA_DATA_FILES:
        return seleccion
    
    if seleccion == ("Salir" or "salir"):
        print("Saliendo sin instertar ningun dataset.")
        return None

    # Si no es ninguno, manejar el error
    print("Error: Selección no válida. Intente de nuevo.")
    return validar_entrada()

if __name__ == "__main__":
    entrada = validar_entrada()
    if entrada:
        insertar_nuevo_dataset(entrada)
