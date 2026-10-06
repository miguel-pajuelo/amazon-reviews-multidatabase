import pymysql
from itertools import combinations
from math import sqrt
from neo4j import GraphDatabase
import networkx as nx
import matplotlib.pyplot as plt
import configuracion as config
from pathlib import Path

# Alumnos: Jorge Ois de Pascual y Miguel Pajuelo Gomez

# Configuración Neo4j
NEO4J_URI = config.NEO4J_URI
NEO4J_USER = config.NEO4J_USER
NEO4J_PASSWORD = config.NEO4J_PASSWORD
NEO4J_DATABASE = config.NEO4J_DATABASE

# Parámetros fáciles de cambiar
TOP_USUARIOS_SIMILITUD = 30
PRIMEROS_USUARIOS = 400
TOP_ARTICULOS_POPULARES = 5
MAX_REVIEWS_ARTICULO_POPULAR = 40


def conectar_bbdd():
    # Conexión a MySQL
    conn_sql = pymysql.connect(cursorclass=pymysql.cursors.DictCursor, **config.MYSQL_CONFIG)

    # Conexión a Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    return conn_sql, driver


def limpiar_neo4j(driver):
    """Elimina todos los nodos y relaciones de Neo4j"""
    with driver.session(database=NEO4J_DATABASE) as session:
        session.run("MATCH (n) DETACH DELETE n")


def normalizar_categoria(categoria):
    """Permite introducir categorías de forma flexible"""
    categorias_validas = {
        "digital_music": "Digital_Music",
        "digital music": "Digital_Music",
        "music": "Digital_Music",
        "musica": "Digital_Music",
        "música": "Digital_Music",
        "discos": "Digital_Music",
        "musical_instruments": "Musical_Instruments",
        "musical instruments": "Musical_Instruments",
        "instruments": "Musical_Instruments",
        "instrumentos": "Musical_Instruments",
        "toys_and_games": "Toys_and_Games",
        "toys and games": "Toys_and_Games",
        "toys": "Toys_and_Games",
        "juguetes": "Toys_and_Games",
        "video_games": "Video_Games",
        "video games": "Video_Games",
        "videogames": "Video_Games",
        "videojuegos": "Video_Games"
    }

    categoria = categoria.strip()
    if categoria in config.DATA_FILES:
        return categoria

    return categorias_validas.get(categoria.lower())


def pedir_categoria():
    print("\nCategorías disponibles:")
    for categoria in config.DATA_FILES.keys():
        print(f"- {categoria}")

    while True:
        categoria = input("Seleccione una categoría: ")
        categoria_normalizada = normalizar_categoria(categoria)
        if categoria_normalizada:
            return categoria_normalizada
        print("Categoría no válida.")


def pedir_entero_positivo(mensaje):
    while True:
        try:
            valor = int(input(mensaje))
            if valor > 0:
                return valor
            print("Debe introducir un entero positivo.")
        except ValueError:
            print("Entrada no válida.")


def construir_placeholders(n):
    return ", ".join(["%s"] * n)


# APARTADO 4.1 - Obtener similitudes entre usuarios y mostrar los enlaces en Neo4J

def obtener_top_usuarios(conn_sql, limite=TOP_USUARIOS_SIMILITUD):
    """Obtiene los usuarios con más reviews"""
    query = """
        SELECT u.reviewerID, u.reviewerName,
               COUNT(*) AS total_reviews,
               AVG(r.overall) AS media_reviews
        FROM Usuarios u
        JOIN Reviews_Metadatos r ON u.reviewerID = r.reviewerID
        GROUP BY u.reviewerID, u.reviewerName
        ORDER BY total_reviews DESC, u.reviewerID ASC
        LIMIT %s
    """
    cursor = conn_sql.cursor()
    cursor.execute(query, (limite,))
    resultados = cursor.fetchall()
    cursor.close()
    return resultados


def obtener_reviews_usuarios(conn_sql, reviewer_ids):
    """Obtiene asin y nota para una lista de usuarios"""
    if not reviewer_ids:
        return {}

    placeholders = construir_placeholders(len(reviewer_ids))
    query = f"""
        SELECT reviewerID, asin, overall
        FROM Reviews_Metadatos
        WHERE reviewerID IN ({placeholders})
    """

    ratings = {reviewer_id: {} for reviewer_id in reviewer_ids}

    cursor = conn_sql.cursor()
    cursor.execute(query, tuple(reviewer_ids))
    resultados = cursor.fetchall()
    cursor.close()

    for fila in resultados:
        ratings[fila["reviewerID"]][fila["asin"]] = float(fila["overall"])

    return ratings


def media_valoraciones(ratings_usuario):
    if not ratings_usuario:
        return 0.0
    return sum(ratings_usuario.values()) / len(ratings_usuario)


def calcular_pearson(ratings_u, ratings_v, media_u, media_v):
    """Calcula la correlación de Pearson entre dos usuarios"""
    articulos_comunes = set(ratings_u.keys()) & set(ratings_v.keys())

    if not articulos_comunes:
        return None, 0

    numerador = 0
    suma_u = 0
    suma_v = 0

    for asin in articulos_comunes:
        dif_u = ratings_u[asin] - media_u
        dif_v = ratings_v[asin] - media_v
        numerador += dif_u * dif_v
        suma_u += dif_u ** 2
        suma_v += dif_v ** 2

    denominador = sqrt(suma_u) * sqrt(suma_v)

    if denominador == 0:
        return 0.0, len(articulos_comunes)

    return numerador / denominador, len(articulos_comunes)


def calcular_similitudes(conn_sql, limite=TOP_USUARIOS_SIMILITUD):
    """Calcula similitudes entre los top usuarios"""
    usuarios = obtener_top_usuarios(conn_sql, limite)
    reviewer_ids = [u["reviewerID"] for u in usuarios]
    ratings = obtener_reviews_usuarios(conn_sql, reviewer_ids)

    medias = {}
    for reviewer_id in reviewer_ids:
        medias[reviewer_id] = media_valoraciones(ratings[reviewer_id])

    similitudes = []

    for user1, user2 in combinations(reviewer_ids, 2):
        pearson, comunes = calcular_pearson(
            ratings[user1], ratings[user2], medias[user1], medias[user2]
        )

        if pearson is not None:
            similitudes.append({
                "user1": user1,
                "user2": user2,
                "pearson": round(pearson, 6),
                "common_items": comunes
            })

    return usuarios, similitudes


def cargar_similitudes_neo4j(driver, usuarios, similitudes):
    """Carga usuarios y similitudes en Neo4j"""
    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(
            """
            UNWIND $usuarios AS usuario
            MERGE (u:Usuario {reviewerID: usuario.reviewerID})
            SET u.reviewerName = usuario.reviewerName,
                u.totalReviews = usuario.total_reviews,
                u.mediaReviews = round(usuario.media_reviews, 4)
            """,
            usuarios=usuarios
        )

        session.run(
            """
            UNWIND $similitudes AS similitud
            MATCH (u1:Usuario {reviewerID: similitud.user1})
            MATCH (u2:Usuario {reviewerID: similitud.user2})
            MERGE (u1)-[r:SIMILAR_A]->(u2)
            SET r.pearson = similitud.pearson,
                r.common_items = similitud.common_items
            MERGE (u2)-[r2:SIMILAR_A]->(u1)
            SET r2.pearson = similitud.pearson,
                r2.common_items = similitud.common_items
            """,
            similitudes=similitudes
        )


def usuario_con_mas_vecinos(driver):
    """Devuelve el usuario con más vecinos en Neo4j"""
    with driver.session(database=NEO4J_DATABASE) as session:
        result = session.run(
            """
            MATCH (u:Usuario)
            OPTIONAL MATCH (u)-[:SIMILAR_A]-(v:Usuario)
            WITH u, COUNT(DISTINCT v) AS vecinos
            RETURN u.reviewerID AS reviewerID,
                   u.reviewerName AS reviewerName,
                   vecinos
            ORDER BY vecinos DESC, reviewerID ASC
            LIMIT 1
            """
        )
        fila = result.single()
        if fila:
            return dict(fila)
        return None


def apartado_4_1(conn_sql, driver):
    print(f"\nCalculando similitudes para los {TOP_USUARIOS_SIMILITUD} usuarios con más reviews...")

    limpiar_neo4j(driver)

    usuarios, similitudes = calcular_similitudes(conn_sql, TOP_USUARIOS_SIMILITUD)
    cargar_similitudes_neo4j(driver, usuarios, similitudes)

    print("Carga finalizada en Neo4j.")
    print(f"- Usuarios cargados: {len(usuarios)}")
    print(f"- Relaciones de similitud creadas: {len(similitudes) * 2}")

    usuario = usuario_con_mas_vecinos(driver)
    if usuario:
        print("\nUsuario con más vecinos:")
        print(f"- reviewerID: {usuario['reviewerID']}")
        print(f"- reviewerName: {usuario['reviewerName']}")
        print(f"- vecinos: {usuario['vecinos']}")

        mostrar_grafo_neo4j(
        driver,
        titulo="Apartado 4.1 - Similitudes entre usuarios",
        nombre_imagen="apartado_4_1.png"
        )

    else:
        print("No se ha podido obtener el usuario con más vecinos.")


# APARTADO 4.2 - Obtener enlaces entre usuarios y artículos
def obtener_articulos_aleatorios(conn_sql, categoria, cantidad):
    """Selecciona artículos aleatorios de una categoría"""
    query = """
        SELECT a.asin, c.nombre_categoria
        FROM Articulos a
        JOIN Categorias c ON a.id_categoria = c.id_categoria
        WHERE c.nombre_categoria = %s
        ORDER BY RAND()
        LIMIT %s
    """
    cursor = conn_sql.cursor()
    cursor.execute(query, (categoria, cantidad))
    resultados = cursor.fetchall()
    cursor.close()
    return resultados


def obtener_reviews_articulos(conn_sql, asins):
    """Obtiene todas las reviews de una lista de artículos"""
    if not asins:
        return []

    placeholders = construir_placeholders(len(asins))
    query = f"""
        SELECT r.reviewerID, u.reviewerName, r.asin,
               r.overall, r.unixReviewTime, r.reviewTime,
               c.nombre_categoria
        FROM Reviews_Metadatos r
        JOIN Usuarios u ON r.reviewerID = u.reviewerID
        JOIN Articulos a ON r.asin = a.asin
        JOIN Categorias c ON a.id_categoria = c.id_categoria
        WHERE r.asin IN ({placeholders})
        ORDER BY r.asin, r.unixReviewTime ASC
    """
    cursor = conn_sql.cursor()
    cursor.execute(query, tuple(asins))
    resultados = cursor.fetchall()
    cursor.close()
    return resultados


def cargar_articulos_reviews_neo4j(driver, articulos, reviews):
    """Carga artículos, usuarios y reviews en Neo4j"""
    usuarios = {}
    for review in reviews:
        usuarios[review["reviewerID"]] = {
            "reviewerID": review["reviewerID"],
            "reviewerName": review["reviewerName"]
        }

    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(
            """
            UNWIND $articulos AS articulo
            MERGE (a:Articulo {asin: articulo.asin})
            SET a.categoria = articulo.nombre_categoria
            """,
            articulos=articulos
        )

        session.run(
            """
            UNWIND $usuarios AS usuario
            MERGE (u:Usuario {reviewerID: usuario.reviewerID})
            SET u.reviewerName = usuario.reviewerName
            """,
            usuarios=list(usuarios.values())
        )

        session.run(
            """
            UNWIND $reviews AS review
            MATCH (u:Usuario {reviewerID: review.reviewerID})
            MATCH (a:Articulo {asin: review.asin})
            MERGE (u)-[r:VALORO]->(a)
            SET r.rating = review.overall,
                r.unixReviewTime = review.unixReviewTime,
                r.reviewTime = review.reviewTime
            """,
            reviews=[
                {
                    "reviewerID": review["reviewerID"],
                    "asin": review["asin"],
                    "overall": float(review["overall"]),
                    "unixReviewTime": int(review["unixReviewTime"]),
                    "reviewTime": str(review["reviewTime"])
                }
                for review in reviews
            ]
        )


def apartado_4_2(conn_sql, driver):
    print("\n--- Apartado 4.2: Usuarios y artículos aleatorios ---")

    categoria = pedir_categoria()
    cantidad = pedir_entero_positivo("Número de artículos aleatorios a seleccionar: ")

    articulos = obtener_articulos_aleatorios(conn_sql, categoria, cantidad)
    if not articulos:
        print("No se han encontrado artículos para esa categoría.")
        return

    limpiar_neo4j(driver)

    asins = [articulo["asin"] for articulo in articulos]
    reviews = obtener_reviews_articulos(conn_sql, asins)
    cargar_articulos_reviews_neo4j(driver, articulos, reviews)

    print("\nCarga finalizada en Neo4j.")
    print(f"- Categoría seleccionada: {categoria}")
    print(f"- Artículos aleatorios cargados: {len(articulos)}")
    print(f"- Relaciones usuario-artículo creadas: {len(reviews)}")
    mostrar_grafo_neo4j(
        driver,
        titulo=f"Apartado 4.2 - Usuarios y artículos aleatorios ({categoria})",
        nombre_imagen="apartado_4_2.png"
    )


# APARTADO 4.3 - Obtener algunos usuarios que han visto más de un determinado tipo de artículo
def obtener_primeros_usuarios(conn_sql, limite=PRIMEROS_USUARIOS):
    """Obtiene los primeros usuarios ordenados por nombre"""
    query = """
        SELECT reviewerID, reviewerName
        FROM Usuarios
        ORDER BY reviewerName ASC, reviewerID ASC
        LIMIT %s
    """
    cursor = conn_sql.cursor()
    cursor.execute(query, (limite,))
    resultados = cursor.fetchall()
    cursor.close()
    return resultados


def obtener_tipos_por_usuario(conn_sql, reviewer_ids):
    """Obtiene cuántos artículos distintos ha puntuado cada usuario por tipo"""
    if not reviewer_ids:
        return []

    placeholders = construir_placeholders(len(reviewer_ids))
    query = f"""
        SELECT u.reviewerID, u.reviewerName, c.nombre_categoria,
               COUNT(DISTINCT r.asin) AS num_articulos
        FROM Usuarios u
        JOIN Reviews_Metadatos r ON u.reviewerID = r.reviewerID
        JOIN Articulos a ON r.asin = a.asin
        JOIN Categorias c ON a.id_categoria = c.id_categoria
        WHERE u.reviewerID IN ({placeholders})
        GROUP BY u.reviewerID, u.reviewerName, c.nombre_categoria
        ORDER BY u.reviewerName ASC, u.reviewerID ASC, c.nombre_categoria ASC
    """
    cursor = conn_sql.cursor()
    cursor.execute(query, tuple(reviewer_ids))
    resultados = cursor.fetchall()
    cursor.close()
    return resultados


def filtrar_usuarios_varios_tipos(registros):
    """Se queda solo con usuarios que han puntuado más de un tipo"""
    categorias_por_usuario = {}
    datos_usuario = {}

    for fila in registros:
        reviewer_id = fila["reviewerID"]
        if reviewer_id not in categorias_por_usuario:
            categorias_por_usuario[reviewer_id] = set()
        categorias_por_usuario[reviewer_id].add(fila["nombre_categoria"])

        datos_usuario[reviewer_id] = {
            "reviewerID": reviewer_id,
            "reviewerName": fila["reviewerName"]
        }

    usuarios_validos = []
    reviewer_validos = set()

    for reviewer_id, categorias in categorias_por_usuario.items():
        if len(categorias) > 1:
            usuarios_validos.append(datos_usuario[reviewer_id])
            reviewer_validos.add(reviewer_id)

    relaciones = [fila for fila in registros if fila["reviewerID"] in reviewer_validos]

    return usuarios_validos, relaciones


def cargar_usuarios_tipos_neo4j(driver, usuarios, relaciones):
    """Carga usuarios, tipos y relaciones en Neo4j"""
    tipos = sorted(set([fila["nombre_categoria"] for fila in relaciones]))
    tipos_payload = [{"nombre": tipo} for tipo in tipos]

    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(
            """
            UNWIND $usuarios AS usuario
            MERGE (u:Usuario {reviewerID: usuario.reviewerID})
            SET u.reviewerName = usuario.reviewerName
            """,
            usuarios=usuarios
        )

        session.run(
            """
            UNWIND $tipos AS tipo
            MERGE (t:TipoArticulo {nombre: tipo.nombre})
            """,
            tipos=tipos_payload
        )

        session.run(
            """
            UNWIND $relaciones AS relacion
            MATCH (u:Usuario {reviewerID: relacion.reviewerID})
            MATCH (t:TipoArticulo {nombre: relacion.nombre_categoria})
            MERGE (u)-[r:HA_PUNTUADO_TIPO]->(t)
            SET r.num_articulos = relacion.num_articulos
            """,
            relaciones=relaciones
        )


def apartado_4_3(conn_sql, driver):
    print("\n--- Apartado 4.3: Usuarios que han puntuado más de un tipo de artículo ---")

    limpiar_neo4j(driver)

    usuarios_iniciales = obtener_primeros_usuarios(conn_sql, PRIMEROS_USUARIOS)
    reviewer_ids = [usuario["reviewerID"] for usuario in usuarios_iniciales]
    registros = obtener_tipos_por_usuario(conn_sql, reviewer_ids)
    usuarios_validos, relaciones = filtrar_usuarios_varios_tipos(registros)

    if not usuarios_validos:
        print("No se han encontrado usuarios que hayan puntuado artículos de más de una categoría.")
        return

    cargar_usuarios_tipos_neo4j(driver, usuarios_validos, relaciones)

    print("\nCarga finalizada en Neo4j.")
    print(f"- Usuarios revisados inicialmente: {len(usuarios_iniciales)}")
    print(f"- Usuarios multicategoría cargados: {len(usuarios_validos)}")
    print(f"- Relaciones usuario-tipo creadas: {len(relaciones)}")
    mostrar_grafo_neo4j(
        driver,
        titulo="Apartado 4.3 - Usuarios que han puntuado más de un tipo",
        nombre_imagen="apartado_4_3.png"
    )


# APARTADO 4.4 - Artículos populares y artículos en común entre usuarios
def obtener_articulos_populares(conn_sql, limite=TOP_ARTICULOS_POPULARES, max_reviews=MAX_REVIEWS_ARTICULO_POPULAR):
    """Obtiene los artículos más populares con menos de max_reviews reviews"""
    query = """
        SELECT r.asin, c.nombre_categoria, COUNT(*) AS num_reviews
        FROM Reviews_Metadatos r
        JOIN Articulos a ON r.asin = a.asin
        JOIN Categorias c ON a.id_categoria = c.id_categoria
        GROUP BY r.asin, c.nombre_categoria
        HAVING COUNT(*) < %s
        ORDER BY num_reviews DESC, r.asin ASC
        LIMIT %s
    """
    cursor = conn_sql.cursor()
    cursor.execute(query, (max_reviews, limite))
    resultados = cursor.fetchall()
    cursor.close()
    return resultados


def obtener_usuarios_involucrados(reviews):
    return sorted(set([review["reviewerID"] for review in reviews]))


def obtener_articulos_comunes(conn_sql, reviewer_ids):
    """Calcula cuántos artículos en común han puntuado los usuarios"""
    if len(reviewer_ids) < 2:
        return []

    placeholders = construir_placeholders(len(reviewer_ids))
    query = f"""
        SELECT r1.reviewerID AS user1,
               r2.reviewerID AS user2,
               COUNT(DISTINCT r1.asin) AS common_items
        FROM Reviews_Metadatos r1
        JOIN Reviews_Metadatos r2
          ON r1.asin = r2.asin
         AND r1.reviewerID < r2.reviewerID
        WHERE r1.reviewerID IN ({placeholders})
          AND r2.reviewerID IN ({placeholders})
        GROUP BY r1.reviewerID, r2.reviewerID
        HAVING common_items > 0
        ORDER BY common_items DESC, user1 ASC, user2 ASC
    """

    parametros = tuple(reviewer_ids) + tuple(reviewer_ids)
    cursor = conn_sql.cursor()
    cursor.execute(query, parametros)
    resultados = cursor.fetchall()
    cursor.close()
    return resultados


def cargar_articulos_populares_neo4j(driver, articulos, reviews, comunes):
    """Carga el grafo del apartado 4.4 en Neo4j"""
    usuarios = {}
    for review in reviews:
        usuarios[review["reviewerID"]] = {
            "reviewerID": review["reviewerID"],
            "reviewerName": review["reviewerName"]
        }

    with driver.session(database=NEO4J_DATABASE) as session:
        session.run(
            """
            UNWIND $articulos AS articulo
            MERGE (a:Articulo {asin: articulo.asin})
            SET a.categoria = articulo.nombre_categoria,
                a.numReviews = articulo.num_reviews
            """,
            articulos=articulos
        )

        session.run(
            """
            UNWIND $usuarios AS usuario
            MERGE (u:Usuario {reviewerID: usuario.reviewerID})
            SET u.reviewerName = usuario.reviewerName
            """,
            usuarios=list(usuarios.values())
        )

        session.run(
            """
            UNWIND $reviews AS review
            MATCH (u:Usuario {reviewerID: review.reviewerID})
            MATCH (a:Articulo {asin: review.asin})
            MERGE (u)-[r:VALORO]->(a)
            SET r.rating = review.overall,
                r.unixReviewTime = review.unixReviewTime,
                r.reviewTime = review.reviewTime
            """,
            reviews=[
                {
                    "reviewerID": review["reviewerID"],
                    "asin": review["asin"],
                    "overall": float(review["overall"]),
                    "unixReviewTime": int(review["unixReviewTime"]),
                    "reviewTime": str(review["reviewTime"])
                }
                for review in reviews
            ]
        )

        session.run(
            """
            UNWIND $comunes AS comun
            MATCH (u1:Usuario {reviewerID: comun.user1})
            MATCH (u2:Usuario {reviewerID: comun.user2})
            MERGE (u1)-[r:ARTICULOS_EN_COMUN]->(u2)
            SET r.common_items = comun.common_items
            """,
            comunes=comunes
        )


def apartado_4_4(conn_sql, driver):
    print("\n--- Apartado 4.4: Artículos populares y artículos en común entre usuarios ---")

    limpiar_neo4j(driver)

    articulos = obtener_articulos_populares(
        conn_sql,
        TOP_ARTICULOS_POPULARES,
        MAX_REVIEWS_ARTICULO_POPULAR
    )

    if not articulos:
        print("No se han encontrado artículos que cumplan la condición pedida.")
        return

    asins = [articulo["asin"] for articulo in articulos]
    reviews = obtener_reviews_articulos(conn_sql, asins)
    reviewer_ids = obtener_usuarios_involucrados(reviews)
    comunes = obtener_articulos_comunes(conn_sql, reviewer_ids)

    cargar_articulos_populares_neo4j(driver, articulos, reviews, comunes)

    print("\nCarga finalizada en Neo4j.")
    print(f"- Artículos populares cargados: {len(articulos)}")
    print(f"- Usuarios implicados: {len(reviewer_ids)}")
    print(f"- Relaciones usuario-artículo creadas: {len(reviews)}")
    print(f"- Relaciones usuario-usuario por artículos en común: {len(comunes)}")
    mostrar_grafo_neo4j(
        driver,
        titulo="Apartado 4.4 - Artículos populares y artículos en común",
        nombre_imagen="apartado_4_4.png"
    )


# MENÚ
def menu():
    conn_sql, driver = conectar_bbdd()

    while True:
        print("\n--- MENÚ NEO4J ---")
        print("1. Similitudes entre usuarios")
        print("2. Usuarios y artículos aleatorios")
        print("3. Usuarios que han puntuado más de un tipo")
        print("4. Artículos populares y artículos en común")
        print("5. Salir")

        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            apartado_4_1(conn_sql, driver)
        elif opcion == "2":
            apartado_4_2(conn_sql, driver)
        elif opcion == "3":
            apartado_4_3(conn_sql, driver)
        elif opcion == "4":
            apartado_4_4(conn_sql, driver)
        elif opcion == "5":
            print("Saliendo...")
            break
        else:
            print("Opción no válida.")

    conn_sql.close()
    driver.close()

def obtener_etiqueta_nodo(labels, props):
    """Devuelve la etiqueta visible de un nodo"""
    if "Usuario" in labels:
        nombre = props.get("reviewerName")
        if nombre and str(nombre).strip() and str(nombre).lower() != "unknown":
            return str(nombre)
        return str(props.get("reviewerID", "Usuario"))

    if "Articulo" in labels:
        return str(props.get("asin", "Articulo"))

    if "TipoArticulo" in labels:
        return str(props.get("nombre", "TipoArticulo"))

    return "Nodo"


def obtener_color_nodo(tipo):
    """Color del nodo según su tipo"""
    if tipo == "Usuario":
        return "skyblue"
    if tipo == "Articulo":
        return "lightgreen"
    if tipo == "TipoArticulo":
        return "orange"
    return "lightgray"


def obtener_etiqueta_arista(tipo, props):
    """Devuelve la etiqueta visible de una arista"""
    if tipo == "SIMILAR_A":
        pearson = props.get("pearson", 0)
        comunes = props.get("common_items", 0)
        return f"p={round(float(pearson), 2)}\ncom={comunes}"

    if tipo == "VALORO":
        rating = props.get("rating", "")
        return f"{rating}"

    if tipo == "HA_PUNTUADO_TIPO":
        num_articulos = props.get("num_articulos", 0)
        return f"n={num_articulos}"

    if tipo == "ARTICULOS_EN_COMUN":
        comunes = props.get("common_items", 0)
        return f"com={comunes}"

    return tipo

# VISUALIZACION DE LOS GRAFOS
def mostrar_grafo_neo4j(driver, titulo="Grafo Neo4j", nombre_imagen=None):
    """Lee el grafo actual desde Neo4j y lo representa con networkx + matplotlib"""
    with driver.session(database=NEO4J_DATABASE) as session:
        nodos = session.run(
            """
            MATCH (n)
            RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props
            """
        ).data()

        relaciones = session.run(
            """
            MATCH (n)-[r]->(m)
            RETURN elementId(n) AS origen,
                   elementId(m) AS destino,
                   type(r) AS tipo,
                   properties(r) AS props
            """
        ).data()

    if not nodos:
        print("No hay nodos en Neo4j para representar.")
        return

    G = nx.DiGraph()

    # Añadir nodos
    for nodo in nodos:
        labels = nodo["labels"]
        props = nodo["props"]
        tipo = labels[0] if labels else "Nodo"

        G.add_node(
            nodo["id"],
            label=obtener_etiqueta_nodo(labels, props),
            tipo=tipo
        )

    # Añadir aristas
    for relacion in relaciones:
        G.add_edge(
            relacion["origen"],
            relacion["destino"],
            label=obtener_etiqueta_arista(relacion["tipo"], relacion["props"]),
            tipo=relacion["tipo"]
        )

    plt.figure(figsize=(14, 10))

    pos = nx.spring_layout(G, seed=42, k=1.2)

    colores = [obtener_color_nodo(data["tipo"]) for _, data in G.nodes(data=True)]
    etiquetas_nodos = {nodo: data["label"] for nodo, data in G.nodes(data=True)}

    nx.draw_networkx_nodes(G, pos, node_color=colores, node_size=1800, alpha=0.9)
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="-|>", arrowsize=15, width=1.2)
    nx.draw_networkx_labels(G, pos, labels=etiquetas_nodos, font_size=8)

    # Solo dibujar etiquetas de arista si no hay demasiadas, para que no sea ilegible
    if G.number_of_edges() <= 80:
        etiquetas_aristas = {(u, v): data["label"] for u, v, data in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=etiquetas_aristas, font_size=7)

    plt.title(titulo)
    plt.axis("off")
    plt.tight_layout()

    if nombre_imagen:
        output_dir = Path(__file__).resolve().parent / "imagenes"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / nombre_imagen
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Imagen guardada en: {output_path}")

    plt.show()


if __name__ == "__main__":
    try:
        menu()
    except pymysql.MySQLError as e:
        print(f"Error MySQL: {e}")
    except Exception as e:
        print(f"Error : {e}")
