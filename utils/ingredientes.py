"""
Gestión de ingredientes (SQLite).
"""
from utils.base_datos import checkpoint, conexion, inicializar_base_datos


def obtener_ruta_json():
    from utils.rutas import obtener_ruta_json as obtener_ruta_json_helper
    return obtener_ruta_json_helper("ingredientes.json")


def _categorias_de(conn, ingrediente_id):
    filas = conn.execute(
        "SELECT nombre FROM ingrediente_categoria WHERE ingrediente_id=? ORDER BY nombre",
        (ingrediente_id,),
    ).fetchall()
    return [f["nombre"] for f in filas]


def _dict_ingrediente(conn, fila):
    item = {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "categorias": _categorias_de(conn, fila["id"]),
        "precio_extra": fila["precio_extra"],
        "precio_resta": fila["precio_resta"],
    }
    if fila["imagen"]:
        item["imagen"] = fila["imagen"]
    return item


def cargar_ingredientes():
    inicializar_base_datos()
    with conexion() as conn:
        filas = conn.execute(
            "SELECT id, nombre, precio_extra, precio_resta, imagen FROM ingrediente ORDER BY id"
        ).fetchall()
        return {"ingredientes": [_dict_ingrediente(conn, f) for f in filas]}


def guardar_ingredientes(data=None):
    checkpoint()


def obtener_siguiente_id():
    with conexion() as conn:
        max_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM ingrediente").fetchone()[0]
    return max_id + 1


def obtener_todos_los_ingredientes():
    return cargar_ingredientes().get("ingredientes", [])


def buscar_ingrediente_por_id(ingrediente_id):
    inicializar_base_datos()
    with conexion() as conn:
        fila = conn.execute(
            "SELECT id, nombre, precio_extra, precio_resta, imagen FROM ingrediente WHERE id=?",
            (ingrediente_id,),
        ).fetchone()
        if not fila:
            return None
        return _dict_ingrediente(conn, fila)


def buscar_ingrediente_por_nombre(nombre):
    inicializar_base_datos()
    with conexion() as conn:
        fila = conn.execute(
            "SELECT id, nombre, precio_extra, precio_resta, imagen FROM ingrediente WHERE nombre=?",
            (nombre,),
        ).fetchone()
        if not fila:
            return None
        return _dict_ingrediente(conn, fila)


def _set_categorias(conn, ingrediente_id, categorias):
    conn.execute(
        "DELETE FROM ingrediente_categoria WHERE ingrediente_id=?",
        (ingrediente_id,),
    )
    lista = categorias if isinstance(categorias, list) else [categorias]
    for nombre in lista:
        nombre = (nombre or "").strip()
        if not nombre:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO ingrediente_categoria(ingrediente_id, nombre) VALUES(?, ?)",
            (ingrediente_id, nombre),
        )


def agregar_ingrediente(nombre, categorias, precio_extra, precio_resta, imagen=None):
    with conexion() as conn:
        nuevo_id = conn.execute("SELECT COALESCE(MAX(id), 0)+1 FROM ingrediente").fetchone()[0]
        conn.execute(
            """
            INSERT INTO ingrediente(id, nombre, precio_extra, precio_resta, imagen)
            VALUES(?, ?, ?, ?, ?)
            """,
            (nuevo_id, nombre, float(precio_extra), float(precio_resta), imagen or None),
        )
        _set_categorias(conn, nuevo_id, categorias)
    nuevo = {
        "id": nuevo_id,
        "nombre": nombre,
        "categorias": categorias if isinstance(categorias, list) else [categorias],
        "precio_extra": float(precio_extra),
        "precio_resta": float(precio_resta),
    }
    if imagen:
        nuevo["imagen"] = imagen
    return nuevo


def modificar_ingrediente(ingrediente_id, nombre, categorias, precio_extra, precio_resta, imagen=None):
    with conexion() as conn:
        fila = conn.execute(
            "SELECT id, imagen FROM ingrediente WHERE id=?",
            (ingrediente_id,),
        ).fetchone()
        if not fila:
            return False
        imagen_final = fila["imagen"]
        if imagen is not None:
            imagen_final = imagen or None
        conn.execute(
            """
            UPDATE ingrediente
            SET nombre=?, precio_extra=?, precio_resta=?, imagen=?
            WHERE id=?
            """,
            (nombre, float(precio_extra), float(precio_resta), imagen_final, ingrediente_id),
        )
        _set_categorias(conn, ingrediente_id, categorias)
    return True


def eliminar_ingrediente(ingrediente_id):
    with conexion() as conn:
        fila = conn.execute("SELECT id FROM ingrediente WHERE id=?", (ingrediente_id,)).fetchone()
        if not fila:
            return False
        conn.execute("DELETE FROM ingrediente WHERE id=?", (ingrediente_id,))
    return True


def renombrar_categoria_en_ingredientes(nombre_anterior, nombre_nuevo):
    with conexion() as conn:
        conn.execute(
            "UPDATE ingrediente_categoria SET nombre=? WHERE nombre=?",
            (nombre_nuevo, nombre_anterior),
        )
    return True


def quitar_categoria_de_ingredientes(nombre_categoria):
    with conexion() as conn:
        conn.execute(
            "DELETE FROM ingrediente_categoria WHERE nombre=?",
            (nombre_categoria,),
        )
    return True


def obtener_ingredientes_por_categoria(categoria_nombre):
    inicializar_base_datos()
    with conexion() as conn:
        filas = conn.execute(
            """
            SELECT DISTINCT i.id, i.nombre, i.precio_extra, i.precio_resta, i.imagen
            FROM ingrediente i
            JOIN ingrediente_categoria ic ON ic.ingrediente_id = i.id
            WHERE ic.nombre=?
            ORDER BY i.nombre
            """,
            (categoria_nombre,),
        ).fetchall()
        return [_dict_ingrediente(conn, f) for f in filas]
