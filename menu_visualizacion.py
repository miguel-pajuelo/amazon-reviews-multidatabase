import pymysql, re
from pymongo import MongoClient
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
import configuracion as config


# Alumnos: Jorge Ois de Pascual y Miguel Pajuelo Gomez

def conectar_bbdd():
    # Conexión a MySQL
    conn_sql = pymysql.connect(**config.MYSQL_CONFIG)

    # Conexión a MongoDB
    client_mongo = MongoClient(config.MONGO_CONFIG["uri"])
    db_mongo = client_mongo[config.MONGO_CONFIG["db_name"]]
    coll_mongo = db_mongo[config.MONGO_CONFIG["collection_name"]]
    return conn_sql, coll_mongo

def menu():
    conn_sql, coll_mongo = conectar_bbdd()
    
    while True:
        print("\n--- MENÚ DE VISUALIZACIÓN ---")
        print("1. Evolución de reviews por años")
        print("2. Popularidad de artículos")
        print("3. Histograma por nota (overall)")
        print("4. Evolución temporal acumulada")
        print("5. Histograma de reviews por usuario")
        print("6. Nube de palabras (Summary)")
        print("7. Gráfico extra (Histograma de reviews por usuario)")
        print("8. Funcionalidad apartado 6.3: recomendar 10 artículos no consumidos")
        print("9. Salir")
        
        opcion = input("Seleccione una opción: ")
        
        if opcion == "1":
            grafico_reviews_por_anio(conn_sql)
        elif opcion == "2":
            grafico_popularidad(conn_sql)
        elif opcion == "3":
            grafico_histograma_notas(conn_sql)
        elif opcion == "4":
            grafico_evolucion_temporal(conn_sql)
        elif opcion == "5":
            grafico_histograma_reviews_por_usuario(conn_sql)
        elif opcion == "6":
            grafico_wordcloud(conn_sql, coll_mongo)
        elif opcion == "7":
            grafico_libre_boxplot(conn_sql)
        elif opcion == "8":
            recomendacion_articulos_no_consumidos(conn_sql)
        elif opcion == "9":
            print("Saliendo...")
            break
        else:
            print("Opción no válida.")

    conn_sql.close()

def grafico_reviews_por_anio(conn_sql):
    """Opción 1: Histograma de reviews por año"""
    cursor = conn_sql.cursor()
    print("\nCategorías disponibles: 'Toys_and_Games', 'Video_Games', 'Digital_Music', 'Music_Instruments' o 'todo'")
    cat = input("Seleccione categoría (o 'todo'): ")

    query = """
        SELECT YEAR(reviewTime) as anio, COUNT(*) as total 
        FROM Reviews_Metadatos 
    """
    
    if cat.lower() != "todo":
        query += """
            JOIN Articulos ON Reviews_Metadatos.asin = Articulos.asin
            JOIN Categorias ON Articulos.id_categoria = Categorias.id_categoria
            WHERE Categorias.nombre_categoria = %s
        """
        query += " GROUP BY anio ORDER BY anio"
        cursor.execute(query, (cat,))
    else:
        query += " GROUP BY anio ORDER BY anio"
        cursor.execute(query)

    resultados = cursor.fetchall()
    
    if not resultados:
        print("No se encontraron datos para esa selección.")
        return

    anios = [r[0] for r in resultados]
    totales = [r[1] for r in resultados]

    plt.figure(figsize=(10, 6))
    plt.bar(anios, totales, color="skyblue", edgecolor="black")
    plt.title(f"Reviews por año - {cat.capitalize()}")
    plt.xlabel("Años")
    plt.ylabel("Número de reviews")
    plt.xticks(anios)
    plt.show()

def grafico_popularidad(conn_sql):
    """Opción 2: Curva de artículos ordenados por número de reviews"""
    cursor = conn_sql.cursor()
    # Consulta para contar reviews por artículo (ASIN) [cite: 90, 91]
    query = """
        SELECT asin, COUNT(*) as num_reviews 
        FROM Reviews_Metadatos 
        GROUP BY asin 
        ORDER BY num_reviews DESC
    """
    cursor.execute(query)
    resultados = cursor.fetchall()
    
    counts = [r[1] for r in resultados]
    
    plt.figure(figsize=(10, 6))
    plt.plot(counts)
    plt.title("Evolución de popularidad de los productos")
    plt.xlabel("Artículos (Indexados por ranking)")
    plt.ylabel("Número de reviews")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.show()

def grafico_histograma_notas(conn_sql):
    """Opción 3: Histograma por nota (1-5)"""
    cursor = conn_sql.cursor()
    query = "SELECT overall, COUNT(*) FROM Reviews_Metadatos GROUP BY overall ORDER BY overall"
    cursor.execute(query)
    resultados = cursor.fetchall()

    notas = [int(r[0]) for r in resultados]
    totales = [r[1] for r in resultados]

    plt.figure(figsize=(8, 5))
    sns.barplot(x=notas, y=totales)
    plt.title("Reviews por nota de todos los productos")
    plt.xlabel("Nota")
    plt.ylabel("Número de reviews")
    plt.show()

def grafico_evolucion_temporal(conn_sql):
    """Opción 4: Evolución acumulada usando timestamp (unixReviewTime)"""
    cursor = conn_sql.cursor()
    # Obtenemos los timestamps ordenados
    query = "SELECT unixReviewTime FROM Reviews_Metadatos ORDER BY unixReviewTime"
    cursor.execute(query)
    resultados = cursor.fetchall()
    
    timestamps = [r[0] for r in resultados]
    # Creamos el acumulado (1, 2, 3... N)
    acumulado = list(range(1, len(timestamps) + 1))

    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, acumulado)
    plt.title("Evolución de las reviews a lo largo del tiempo")
    plt.xlabel("Tiempo (Unix Timestamp)")
    plt.ylabel("Número de reviews acumuladas")
    plt.show()

def grafico_histograma_reviews_por_usuario(conn_sql):
    """Opción 5: Histograma de número de reviews por usuario"""
    cursor = conn_sql.cursor()

    # 1. Contar cuántas reviews ha hecho cada usuario
    query = """
        SELECT reviewerID, COUNT(*) AS num_reviews
        FROM Reviews_Metadatos
        GROUP BY reviewerID
    """
    cursor.execute(query)
    resultados = cursor.fetchall()

    if not resultados:
        print("No hay datos para mostrar.")
        return

    # 2. Extraer solo el número de reviews por usuario
    reviews_por_usuario = [r[1] for r in resultados]

    # 3. Dibujar histograma
    plt.figure(figsize=(10, 6))
    plt.hist(reviews_por_usuario, bins=30, edgecolor="black")
    plt.title("Histograma de reviews por usuario")
    plt.xlabel("Número de reviews")
    plt.ylabel("Número de usuarios")
    plt.show()

def grafico_wordcloud(conn_sql, coll_mongo):
    """Opción 5: Nube de palabras basada en el summary"""
    cursor = conn_sql.cursor()

    print("\nCategorías disponibles:")
    print("Digital_Music, Musical_Instruments, Toys_and_Games, Video_Games")
    cat = input("Seleccione categoría para la nube de palabras: ").strip()

    query = """
        SELECT a.asin
        FROM Articulos a
        JOIN Categorias c ON a.id_categoria = c.id_categoria
        WHERE c.nombre_categoria = %s
    """
    cursor.execute(query, (cat,))
    asins = [r[0] for r in cursor.fetchall()]

    if not asins:
        print("Categoría no encontrada o sin artículos.")
        return

    print("Extrayendo textos de MongoDB...")
    busqueda = coll_mongo.find(
        {"asin": {"$in": asins}},
        {"summary": 1, "_id": 0}
    )

    textos = []
    for doc in busqueda:
        summary = doc.get("summary", "")
        if summary:
            textos.append(str(summary))

    if not textos:
        print("No hay summaries para esa categoría.")
        return

    texto_completo = " ".join(textos).lower()
    texto_completo = re.sub(r"[^a-zA-Z\s]", " ", texto_completo)
    texto_completo = re.sub(r"\s+", " ", texto_completo).strip()

    if not texto_completo:
        print("No hay suficiente texto limpio para generar la nube.")
        return

    stopwords_extra = {
        "the", "and", "this", "that", "with", "have", "from", "they",
        "were", "been", "would", "there", "their", "about", "really",
        "very", "more", "some", "than", "when", "what", "your",
        "good", "great", "nice", "love", "like", "product", "one",
        "use", "used", "get", "got"
    }

    stopwords = STOPWORDS.union(stopwords_extra)

    # Generación de nube
    wc = WordCloud(
        width=1000,
        height=500,
        background_color="white",
        stopwords=stopwords,
        min_word_length=4,
        collocations=False
    ).generate(texto_completo)

    plt.figure(figsize=(14, 7))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.title(f"Nube de palabras: {cat}")
    plt.show()

def grafico_libre_boxplot(conn_sql):
    """Opción 6: Distribución de notas por categoría (Boxplot)"""
    import pandas as pd
    query = """
        SELECT c.nombre_categoria, r.overall 
        FROM Reviews_Metadatos r
        JOIN Articulos a ON r.asin = a.asin
        JOIN Categorias c ON a.id_categoria = c.id_categoria
    """
    # Hemos usado pandas solo para facilitar el dibujo del boxplot
    df = pd.read_sql(query, conn_sql)
    
    plt.figure(figsize=(10, 6))
    sns.boxplot(x="nombre_categoria", y="overall", data=df)
    plt.title("Distribución de calificaciones por categoría")
    plt.show()


def recomendacion_articulos_no_consumidos(conn_sql):
    """Opción 8: Funcionalidad del apartado 6.3"""
    cursor = conn_sql.cursor()

    print("\n--- APARTADO 6.3: RECOMENDACIÓN DE ARTÍCULOS NO CONSUMIDOS ---")
    reviewer_id = input("Introduzca el identificador original del usuario (reviewerID): ").strip()

    print("\nCategorías disponibles:")
    print("Digital_Music, Musical_Instruments, Toys_and_Games, Video_Games")
    categoria = input("Introduzca el tipo de artículo: ").strip()

    # Comprobar si el usuario existe
    query_usuario = """
        SELECT reviewerID
        FROM Usuarios
        WHERE reviewerID = %s
    """
    cursor.execute(query_usuario, (reviewer_id,))
    usuario = cursor.fetchone()

    if not usuario:
        print("El usuario indicado no existe.")
        return

    query_categoria = """
        SELECT id_categoria
        FROM Categorias
        WHERE nombre_categoria = %s
    """
    cursor.execute(query_categoria, (categoria,))
    categoria_existe = cursor.fetchone()

    if not categoria_existe:
        print("La categoría indicada no existe.")
        return

    # Obtenemos los 10 artículos más populares de esa categoría que el usuario no ha consumido
    query = """
        SELECT a.asin, COUNT(r.asin) AS num_reviews
        FROM Articulos a
        JOIN Categorias c ON a.id_categoria = c.id_categoria
        JOIN Reviews_Metadatos r ON a.asin = r.asin
        WHERE c.nombre_categoria = %s
          AND a.asin NOT IN (
              SELECT asin
              FROM Reviews_Metadatos
              WHERE reviewerID = %s
          )
        GROUP BY a.asin
        ORDER BY num_reviews DESC, a.asin ASC
        LIMIT 10
    """
    cursor.execute(query, (categoria, reviewer_id))
    resultados = cursor.fetchall()

    if not resultados:
        print("No se han encontrado artículos para recomendar con esos datos.")
        return

    print(f"\nTop 10 artículos más populares no consumidos por el usuario {reviewer_id}:")
    print(f"Categoría: {categoria}")
    for i, fila in enumerate(resultados, start=1):
        print(f"{i}. ASIN: {fila[0]} | Número de reviews: {fila[1]}")

if __name__ == "__main__":
    menu()