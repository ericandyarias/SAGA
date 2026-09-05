"""
Gestión de productos y categorías (SQLite).
La forma de los diccionarios se mantiene para la UI.
"""
from utils.base_datos import (
    CATEGORIA_PERSONALIZADOS,
    checkpoint,
    conexion,
    inicializar_base_datos,
)


NOMBRES_CATEGORIA_RESERVADOS = {"todas", CATEGORIA_PERSONALIZADOS.lower()}


def es_categoria_especial(nombre):
    """Personalizados es una categoría de sistema, no se administra."""
    return (nombre or "").strip().lower() == CATEGORIA_PERSONALIZADOS.lower()


def normalizar_nombre_categoria(nombre):
    return (nombre or "").strip()


def obtener_ruta_json():
    from utils.rutas import obtener_ruta_json as obtener_ruta_json_helper
    return obtener_ruta_json_helper("productos.json")


def _ingredientes_producto(conn, producto_id):
    filas = conn.execute(
        """
        SELECT i.nombre, pi.cantidad_base
        FROM producto_ingrediente pi
        JOIN ingrediente i ON i.id = pi.ingrediente_id
        WHERE pi.producto_id=?
        ORDER BY pi.orden, pi.ingrediente_id
        """,
        (producto_id,),
    ).fetchall()
    return [{"nombre": f["nombre"], "cantidad_base": f["cantidad_base"]} for f in filas]


def _dict_producto(conn, fila):
    producto = {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "precio": fila["precio"],
        "descripcion": fila["descripcion"] or "",
        "ingredientes": _ingredientes_producto(conn, fila["id"]),
    }
    if fila["imagen"]:
        producto["imagen"] = fila["imagen"]
    return producto


def cargar_productos():
    """Catálogo en el formato que espera la UI: {categorias: [{nombre, productos}]}."""
    inicializar_base_datos()
    with conexion() as conn:
        categorias = []
        for cat in conn.execute(
            "SELECT id, nombre FROM categoria ORDER BY orden, id"
        ).fetchall():
            productos = []
            for prod in conn.execute(
                """
                SELECT id, nombre, precio, descripcion, imagen
                FROM producto
                WHERE categoria_id=? AND activo=1
                ORDER BY orden, id
                """,
                (cat["id"],),
            ).fetchall():
                productos.append(_dict_producto(conn, prod))
            categorias.append({"nombre": cat["nombre"], "productos": productos})
        return {"categorias": categorias}


def guardar_productos(data=None):
    """Los cambios ya se persisten en cada operación. Acá se cierra el WAL."""
    checkpoint()


def asegurar_categoria_personalizados(data):
    inicializar_base_datos()
    with conexion() as conn:
        from utils.base_datos import asegurar_personalizados
        asegurar_personalizados(conn)
    return False


def _id_categoria(conn, nombre):
    fila = conn.execute(
        "SELECT id FROM categoria WHERE nombre=?",
        (nombre,),
    ).fetchone()
    return fila["id"] if fila else None


def _nombre_categoria_existe(nombre, excluir=None, data=None):
    objetivo = normalizar_nombre_categoria(nombre).casefold()
    excluir_norm = normalizar_nombre_categoria(excluir).casefold() if excluir else None
    with conexion() as conn:
        for fila in conn.execute("SELECT nombre FROM categoria").fetchall():
            actual = normalizar_nombre_categoria(fila["nombre"]).casefold()
            if excluir_norm and actual == excluir_norm:
                continue
            if actual == objetivo:
                return True
    return False


def _validar_nombre_categoria(nombre, excluir=None, data=None):
    nombre = normalizar_nombre_categoria(nombre)
    if not nombre:
        raise ValueError("Debe ingresar un nombre de categoría")
    if nombre.casefold() in NOMBRES_CATEGORIA_RESERVADOS:
        raise ValueError(f"El nombre '{nombre}' está reservado")
    if _nombre_categoria_existe(nombre, excluir=excluir, data=data):
        raise ValueError("Ya existe una categoría con ese nombre")
    return nombre


def obtener_nombres_categorias(incluir_especiales=False, data=None):
    inicializar_base_datos()
    with conexion() as conn:
        filas = conn.execute(
            "SELECT nombre, es_especial FROM categoria ORDER BY orden, id"
        ).fetchall()
    nombres = []
    for fila in filas:
        if not incluir_especiales and fila["es_especial"]:
            continue
        if fila["nombre"]:
            nombres.append(fila["nombre"])
    return nombres


def listar_categorias():
    inicializar_base_datos()
    with conexion() as conn:
        filas = conn.execute(
            """
            SELECT c.nombre, COUNT(p.id) AS cantidad
            FROM categoria c
            LEFT JOIN producto p ON p.categoria_id = c.id
            WHERE c.es_especial=0
            GROUP BY c.id
            ORDER BY c.orden, c.id
            """
        ).fetchall()
    return [{"nombre": f["nombre"], "cantidad_productos": f["cantidad"]} for f in filas]


def agregar_categoria(nombre):
    nombre = _validar_nombre_categoria(nombre)
    with conexion() as conn:
        especial = conn.execute(
            "SELECT id, orden FROM categoria WHERE es_especial=1 ORDER BY orden DESC LIMIT 1"
        ).fetchone()
        if especial:
            orden = especial["orden"]
            conn.execute(
                "UPDATE categoria SET orden=orden+1 WHERE id=?",
                (especial["id"],),
            )
        else:
            orden = conn.execute(
                "SELECT COALESCE(MAX(orden), -1)+1 FROM categoria"
            ).fetchone()[0]
        conn.execute(
            "INSERT INTO categoria(nombre, es_especial, orden) VALUES(?, 0, ?)",
            (nombre, orden),
        )
    return {"nombre": nombre, "productos": []}


def renombrar_categoria(nombre_anterior, nombre_nuevo):
    nombre_anterior = normalizar_nombre_categoria(nombre_anterior)
    if not nombre_anterior or es_categoria_especial(nombre_anterior):
        raise ValueError("No se puede modificar esa categoría")

    nombre_nuevo = _validar_nombre_categoria(nombre_nuevo, excluir=nombre_anterior)
    if nombre_nuevo == nombre_anterior:
        return True

    with conexion() as conn:
        fila = conn.execute(
            "SELECT id FROM categoria WHERE nombre=?",
            (nombre_anterior,),
        ).fetchone()
        if not fila:
            raise ValueError("No se encontró la categoría")
        conn.execute(
            "UPDATE categoria SET nombre=? WHERE id=?",
            (nombre_nuevo, fila["id"]),
        )
        conn.execute(
            "UPDATE ingrediente_categoria SET nombre=? WHERE nombre=?",
            (nombre_nuevo, nombre_anterior),
        )
    return True


def eliminar_categoria(nombre):
    nombre = normalizar_nombre_categoria(nombre)
    if not nombre or es_categoria_especial(nombre):
        raise ValueError("No se puede eliminar esa categoría")

    with conexion() as conn:
        fila = conn.execute(
            "SELECT id FROM categoria WHERE nombre=?",
            (nombre,),
        ).fetchone()
        if not fila:
            raise ValueError("No se encontró la categoría")

        from utils.imagenes import eliminar_imagen
        for prod in conn.execute(
            "SELECT imagen FROM producto WHERE categoria_id=?",
            (fila["id"],),
        ).fetchall():
            if prod["imagen"]:
                try:
                    eliminar_imagen(prod["imagen"])
                except Exception:
                    pass

        conn.execute("DELETE FROM categoria WHERE id=?", (fila["id"],))
        conn.execute(
            "DELETE FROM ingrediente_categoria WHERE nombre=?",
            (nombre,),
        )
    return True


def obtener_siguiente_id():
    with conexion() as conn:
        max_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM producto").fetchone()[0]
    return max_id + 1


def obtener_todos_los_productos():
    inicializar_base_datos()
    with conexion() as conn:
        filas = conn.execute(
            """
            SELECT p.id, p.nombre, p.precio, p.descripcion, p.imagen, c.nombre AS categoria
            FROM producto p
            JOIN categoria c ON c.id = p.categoria_id
            WHERE p.activo=1
            ORDER BY c.orden, p.orden, p.id
            """
        ).fetchall()
        resultado = []
        for fila in filas:
            item = _dict_producto(conn, fila)
            item["categoria"] = fila["categoria"]
            resultado.append(item)
        return resultado


def buscar_producto_por_id(producto_id):
    inicializar_base_datos()
    with conexion() as conn:
        fila = conn.execute(
            """
            SELECT p.id, p.nombre, p.precio, p.descripcion, p.imagen, c.nombre AS categoria
            FROM producto p
            JOIN categoria c ON c.id = p.categoria_id
            WHERE p.id=?
            """,
            (producto_id,),
        ).fetchone()
        if not fila:
            return None
        return {
            "producto": _dict_producto(conn, fila),
            "categoria": fila["categoria"],
        }


def agregar_producto(categoria_nombre, nombre, precio, descripcion, imagen=None):
    with conexion() as conn:
        cat_id = _id_categoria(conn, categoria_nombre)
        if not cat_id or es_categoria_especial(categoria_nombre):
            raise ValueError("La categoría no existe")
        nuevo_id = conn.execute("SELECT COALESCE(MAX(id), 0)+1 FROM producto").fetchone()[0]
        orden = conn.execute(
            "SELECT COALESCE(MAX(orden), -1)+1 FROM producto WHERE categoria_id=?",
            (cat_id,),
        ).fetchone()[0]
        conn.execute(
            """
            INSERT INTO producto(id, categoria_id, nombre, precio, descripcion, imagen, orden)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (nuevo_id, cat_id, nombre, float(precio), descripcion, imagen or None, orden),
        )
    nuevo = {
        "id": nuevo_id,
        "nombre": nombre,
        "precio": float(precio),
        "descripcion": descripcion,
    }
    if imagen:
        nuevo["imagen"] = imagen
    return nuevo


def modificar_producto(producto_id, categoria_nombre, nombre, precio, descripcion, imagen=None):
    with conexion() as conn:
        fila = conn.execute(
            "SELECT id, categoria_id, imagen FROM producto WHERE id=?",
            (producto_id,),
        ).fetchone()
        if not fila:
            return False
        cat_id = _id_categoria(conn, categoria_nombre)
        if not cat_id or es_categoria_especial(categoria_nombre):
            return False
        imagen_final = fila["imagen"]
        if imagen is not None:
            imagen_final = imagen or None
        conn.execute(
            """
            UPDATE producto
            SET categoria_id=?, nombre=?, precio=?, descripcion=?, imagen=?
            WHERE id=?
            """,
            (cat_id, nombre, float(precio), descripcion, imagen_final, producto_id),
        )
    return True


def eliminar_producto(producto_id):
    with conexion() as conn:
        fila = conn.execute("SELECT id FROM producto WHERE id=?", (producto_id,)).fetchone()
        if not fila:
            return False
        conn.execute("DELETE FROM producto WHERE id=?", (producto_id,))
    return True


def obtener_ingredientes_producto(producto_id):
    resultado = buscar_producto_por_id(producto_id)
    if resultado:
        return resultado["producto"].get("ingredientes", [])
    return []


def agregar_ingrediente_a_producto(producto_id, ingrediente_data):
    nombre = ingrediente_data.get("nombre", "")
    cantidad_base = ingrediente_data.get("cantidad_base", 1)
    with conexion() as conn:
        prod = conn.execute("SELECT id FROM producto WHERE id=?", (producto_id,)).fetchone()
        if not prod:
            return False
        ing = conn.execute("SELECT id FROM ingrediente WHERE nombre=?", (nombre,)).fetchone()
        if not ing:
            return False
        orden = conn.execute(
            "SELECT COALESCE(MAX(orden), -1)+1 FROM producto_ingrediente WHERE producto_id=?",
            (producto_id,),
        ).fetchone()[0]
        conn.execute(
            """
            INSERT INTO producto_ingrediente(producto_id, ingrediente_id, cantidad_base, orden)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(producto_id, ingrediente_id) DO UPDATE SET cantidad_base=excluded.cantidad_base
            """,
            (producto_id, ing["id"], cantidad_base, orden),
        )
    return True


def modificar_ingrediente_producto(producto_id, indice_ingrediente, ingrediente_data):
    nombre = ingrediente_data.get("nombre", "")
    cantidad_base = ingrediente_data.get("cantidad_base", 1)
    with conexion() as conn:
        filas = conn.execute(
            """
            SELECT ingrediente_id FROM producto_ingrediente
            WHERE producto_id=? ORDER BY orden, ingrediente_id
            """,
            (producto_id,),
        ).fetchall()
        if not (0 <= indice_ingrediente < len(filas)):
            return False
        viejo_id = filas[indice_ingrediente]["ingrediente_id"]
        nuevo = conn.execute("SELECT id FROM ingrediente WHERE nombre=?", (nombre,)).fetchone()
        if not nuevo:
            return False
        conn.execute(
            """
            UPDATE producto_ingrediente
            SET ingrediente_id=?, cantidad_base=?
            WHERE producto_id=? AND ingrediente_id=?
            """,
            (nuevo["id"], cantidad_base, producto_id, viejo_id),
        )
    return True


def eliminar_ingrediente_producto(producto_id, indice_ingrediente):
    with conexion() as conn:
        filas = conn.execute(
            """
            SELECT ingrediente_id FROM producto_ingrediente
            WHERE producto_id=? ORDER BY orden, ingrediente_id
            """,
            (producto_id,),
        ).fetchall()
        if not (0 <= indice_ingrediente < len(filas)):
            return False
        conn.execute(
            "DELETE FROM producto_ingrediente WHERE producto_id=? AND ingrediente_id=?",
            (producto_id, filas[indice_ingrediente]["ingrediente_id"]),
        )
    return True


def calcular_precio_con_ingredientes(producto, modificaciones_ingredientes=None):
    precio_base = producto.get("precio", 0.0)
    ingredientes = producto.get("ingredientes", [])

    if not modificaciones_ingredientes:
        return precio_base

    ajuste_total = 0.0
    from utils.ingredientes import buscar_ingrediente_por_nombre

    ingredientes_producto_dict = {ing.get("nombre", ""): ing for ing in ingredientes}

    for ingrediente in ingredientes:
        nombre = ingrediente.get("nombre", "")
        cantidad_base = ingrediente.get("cantidad_base", 1)
        ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre)
        if not ingrediente_actualizado:
            precio_extra = 0.0
            precio_resta = 0.0
        else:
            precio_extra = ingrediente_actualizado.get("precio_extra", 0.0)
            precio_resta = ingrediente_actualizado.get("precio_resta", 0.0)

        cantidad_modificada = modificaciones_ingredientes.get(nombre, cantidad_base)

        if cantidad_modificada > cantidad_base:
            extras = cantidad_modificada - cantidad_base
            ajuste_total += extras * precio_extra
        elif cantidad_modificada < cantidad_base:
            quitados = cantidad_base - cantidad_modificada
            ajuste_total -= quitados * precio_resta

    for nombre, cantidad_adicional in modificaciones_ingredientes.items():
        if nombre not in ingredientes_producto_dict and cantidad_adicional > 0:
            ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre)
            if ingrediente_actualizado:
                precio_extra = ingrediente_actualizado.get("precio_extra", 0.0)
                ajuste_total += cantidad_adicional * precio_extra

    return precio_base + ajuste_total
