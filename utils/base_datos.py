"""
Propósito: SQLite local de SAGA (data/saga.db).
Crea tablas, importa el catálogo de fábrica y las ventas viejas en JSON.
La UI no habla SQL: pasa por productos, ingredientes, ventas y orden.
usuario y comprobante quedan listos para fiscal/ARCA.
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime


VERSION_ESQUEMA = 1
NOMBRE_DB = "saga.db"


def obtener_ruta_db():
    from utils.rutas import obtener_ruta_data
    carpeta = obtener_ruta_data()
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, NOMBRE_DB)


def _conectar(ruta=None):
    conn = sqlite3.connect(ruta or obtener_ruta_db(), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def conexion(ruta=None):
    conn = _conectar(ruta)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def checkpoint():
    try:
        conn = _conectar()
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def _tabla_existe(conn, nombre):
    fila = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (nombre,),
    ).fetchone()
    return fila is not None


def _crear_tablas(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS categoria (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL UNIQUE,
            es_especial INTEGER NOT NULL DEFAULT 0,
            orden INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS ingrediente (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL UNIQUE,
            precio_extra REAL NOT NULL DEFAULT 0,
            precio_resta REAL NOT NULL DEFAULT 0,
            imagen TEXT
        );

        CREATE TABLE IF NOT EXISTS ingrediente_categoria (
            ingrediente_id INTEGER NOT NULL REFERENCES ingrediente(id) ON DELETE CASCADE,
            nombre TEXT NOT NULL,
            PRIMARY KEY (ingrediente_id, nombre)
        );

        CREATE TABLE IF NOT EXISTS producto (
            id INTEGER PRIMARY KEY,
            categoria_id INTEGER NOT NULL REFERENCES categoria(id) ON DELETE CASCADE,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            descripcion TEXT,
            imagen TEXT,
            activo INTEGER NOT NULL DEFAULT 1,
            orden INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS producto_ingrediente (
            producto_id INTEGER NOT NULL REFERENCES producto(id) ON DELETE CASCADE,
            ingrediente_id INTEGER NOT NULL REFERENCES ingrediente(id) ON DELETE CASCADE,
            cantidad_base INTEGER NOT NULL DEFAULT 1,
            orden INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (producto_id, ingrediente_id)
        );

        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL DEFAULT '',
            documento TEXT,
            cuit TEXT,
            condicion_iva TEXT,
            domicilio TEXT,
            telefono TEXT,
            email TEXT,
            notas TEXT,
            creado_en TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS comprobante (
            id INTEGER PRIMARY KEY,
            tipo TEXT,
            punto_venta INTEGER,
            numero INTEGER,
            cae TEXT,
            cae_vencimiento TEXT,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            creado_en TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pedido (
            id TEXT PRIMARY KEY,
            fecha_hora TEXT NOT NULL,
            numero INTEGER NOT NULL,
            nombre_cliente TEXT NOT NULL DEFAULT '',
            usuario_id INTEGER REFERENCES usuario(id),
            comprobante_id INTEGER REFERENCES comprobante(id),
            tipo TEXT NOT NULL DEFAULT '',
            domicilio TEXT,
            hora_estimada TEXT,
            hora_retiro TEXT,
            forma_pago TEXT NOT NULL DEFAULT '',
            estado_pago TEXT,
            total REAL NOT NULL DEFAULT 0,
            cuenta_en_resumen INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS pedido_item (
            id INTEGER PRIMARY KEY,
            pedido_id TEXT NOT NULL REFERENCES pedido(id) ON DELETE CASCADE,
            producto_id INTEGER REFERENCES producto(id) ON DELETE SET NULL,
            nombre TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_base REAL NOT NULL DEFAULT 0,
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            orden INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS pedido_item_modificacion (
            id INTEGER PRIMARY KEY,
            pedido_item_id INTEGER NOT NULL REFERENCES pedido_item(id) ON DELETE CASCADE,
            ingrediente_id INTEGER REFERENCES ingrediente(id) ON DELETE SET NULL,
            nombre TEXT NOT NULL,
            cantidad_base INTEGER NOT NULL DEFAULT 0,
            cantidad_final INTEGER NOT NULL DEFAULT 0,
            precio_ajuste_unitario REAL NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS numerador (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            siguiente INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_pedido_fecha ON pedido(fecha_hora);
        CREATE INDEX IF NOT EXISTS idx_pedido_numero ON pedido(numero);
        CREATE INDEX IF NOT EXISTS idx_item_pedido ON pedido_item(pedido_id);
        CREATE INDEX IF NOT EXISTS idx_producto_categoria ON producto(categoria_id);
        """
    )


def meta_get(conn, clave, por_defecto=None):
    fila = conn.execute("SELECT valor FROM meta WHERE clave=?", (clave,)).fetchone()
    if not fila:
        return por_defecto
    return fila["valor"]


def meta_set(conn, clave, valor):
    conn.execute(
        "INSERT INTO meta(clave, valor) VALUES(?, ?) ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
        (clave, str(valor)),
    )


CATEGORIA_PERSONALIZADOS = "Personalizados"


def asegurar_personalizados(conn):
    fila = conn.execute(
        "SELECT id FROM categoria WHERE lower(nombre)=lower(?)",
        (CATEGORIA_PERSONALIZADOS,),
    ).fetchone()
    max_orden = conn.execute("SELECT COALESCE(MAX(orden), 0) FROM categoria").fetchone()[0]
    if fila:
        conn.execute(
            "UPDATE categoria SET es_especial=1, nombre=?, orden=? WHERE id=?",
            (CATEGORIA_PERSONALIZADOS, max_orden + 1, fila["id"]),
        )
        return
    conn.execute(
        "INSERT INTO categoria(nombre, es_especial, orden) VALUES(?, 1, ?)",
        (CATEGORIA_PERSONALIZADOS, max_orden + 1),
    )


def asegurar_numerador(conn, valor=None):
    fila = conn.execute("SELECT siguiente FROM numerador WHERE id=1").fetchone()
    if fila:
        return
    if valor is None:
        valor = _leer_orden_txt() or 1
    conn.execute("INSERT INTO numerador(id, siguiente) VALUES(1, ?)", (int(valor),))


def _leer_json(ruta):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"No se pudo leer {ruta}: {e}")
        return None


def _leer_orden_txt():
    from utils.rutas import obtener_ruta_data
    ruta = os.path.join(obtener_ruta_data(), "orden_actual.txt")
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith("#"):
                    return int(linea)
        return None
    except (FileNotFoundError, ValueError):
        return None


def _importar_catalogo(conn):
    from utils.rutas import obtener_ruta_archivo_inicial

    data_prod = _leer_json(obtener_ruta_archivo_inicial("productos.json"))
    data_ing = _leer_json(obtener_ruta_archivo_inicial("ingredientes.json"))
    if not isinstance(data_prod, dict):
        data_prod = {"categorias": []}
    if not isinstance(data_ing, dict):
        data_ing = {"ingredientes": []}

    for ing in data_ing.get("ingredientes") or []:
        imagen = ing.get("imagen") or None
        conn.execute(
            """
            INSERT INTO ingrediente(id, nombre, precio_extra, precio_resta, imagen)
            VALUES(?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                int(ing.get("id") or 0) or None,
                ing.get("nombre") or "",
                float(ing.get("precio_extra") or 0),
                float(ing.get("precio_resta") or 0),
                imagen,
            ),
        )
        ing_id = ing.get("id")
        if not ing_id:
            fila = conn.execute(
                "SELECT id FROM ingrediente WHERE nombre=?",
                (ing.get("nombre") or "",),
            ).fetchone()
            ing_id = fila["id"] if fila else None
        if not ing_id:
            continue
        for nombre_cat in ing.get("categorias") or []:
            nombre_cat = (nombre_cat or "").strip()
            if not nombre_cat:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO ingrediente_categoria(ingrediente_id, nombre) VALUES(?, ?)",
                (ing_id, nombre_cat),
            )

    for orden_cat, categoria in enumerate(data_prod.get("categorias") or []):
        nombre = (categoria.get("nombre") or "").strip()
        if not nombre:
            continue
        especial = 1 if nombre.strip().lower() == CATEGORIA_PERSONALIZADOS.lower() else 0
        conn.execute(
            "INSERT OR IGNORE INTO categoria(nombre, es_especial, orden) VALUES(?, ?, ?)",
            (nombre, especial, orden_cat),
        )
        cat_id = conn.execute(
            "SELECT id FROM categoria WHERE nombre=?",
            (nombre,),
        ).fetchone()["id"]

        for orden_prod, producto in enumerate(categoria.get("productos") or []):
            pid = producto.get("id")
            conn.execute(
                """
                INSERT INTO producto(id, categoria_id, nombre, precio, descripcion, imagen, orden)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(pid) if pid is not None else None,
                    cat_id,
                    producto.get("nombre") or "",
                    float(producto.get("precio") or 0),
                    producto.get("descripcion") or "",
                    producto.get("imagen") or None,
                    orden_prod,
                ),
            )
            if pid is None:
                pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            for orden_ing, receta in enumerate(producto.get("ingredientes") or []):
                nombre_ing = (receta.get("nombre") or "").strip()
                if not nombre_ing:
                    continue
                fila_ing = conn.execute(
                    "SELECT id FROM ingrediente WHERE nombre=?",
                    (nombre_ing,),
                ).fetchone()
                if not fila_ing:
                    continue
                conn.execute(
                    """
                    INSERT OR IGNORE INTO producto_ingrediente(
                        producto_id, ingrediente_id, cantidad_base, orden
                    ) VALUES(?, ?, ?, ?)
                    """,
                    (
                        int(pid),
                        fila_ing["id"],
                        int(receta.get("cantidad_base") if receta.get("cantidad_base") is not None else 1),
                        orden_ing,
                    ),
                )


def _importar_ventas(conn):
    from utils.rutas import obtener_ruta_json

    data = _leer_json(obtener_ruta_json("ventas.json"))
    if not data:
        return
    pedidos = data.get("pedidos") if isinstance(data, dict) else data
    if not isinstance(pedidos, list):
        return

    for pedido in pedidos:
        pid = pedido.get("id")
        if not pid:
            continue
        conn.execute(
            """
            INSERT OR IGNORE INTO pedido(
                id, fecha_hora, numero, nombre_cliente, tipo, forma_pago,
                total, cuenta_en_resumen
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(pid),
                pedido.get("fecha_hora") or "",
                int(pedido.get("numero") or 0),
                pedido.get("nombre_cliente") or "",
                pedido.get("tipo") or "",
                pedido.get("forma_pago") or "",
                float(pedido.get("total") or 0),
                1 if pedido.get("cuenta_en_resumen", True) else 0,
            ),
        )
        for orden, item in enumerate(pedido.get("items") or []):
            nombre = item.get("nombre") or ""
            fila_prod = conn.execute(
                "SELECT id, precio FROM producto WHERE nombre=? LIMIT 1",
                (nombre,),
            ).fetchone()
            producto_id = fila_prod["id"] if fila_prod else None
            precio_base = float(fila_prod["precio"]) if fila_prod else float(item.get("precio_unitario") or 0)
            conn.execute(
                """
                INSERT INTO pedido_item(
                    pedido_id, producto_id, nombre, cantidad,
                    precio_base, precio_unitario, subtotal, orden
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(pid),
                    producto_id,
                    nombre,
                    int(item.get("cantidad") or 1),
                    precio_base,
                    float(item.get("precio_unitario") or 0),
                    float(item.get("subtotal") or 0),
                    orden,
                ),
            )


def _migrar_json_si_corresponde(conn):
    if meta_get(conn, "migracion_json") == "1":
        return
    try:
        _importar_catalogo(conn)
        _importar_ventas(conn)
        orden = _leer_orden_txt()
        if orden is not None:
            conn.execute("DELETE FROM numerador WHERE id=1")
            conn.execute("INSERT INTO numerador(id, siguiente) VALUES(1, ?)", (int(orden),))
    except Exception as e:
        print(f"Error al migrar JSON a SQLite: {e}")
        raise
    meta_set(conn, "migracion_json", "1")
    meta_set(conn, "migracion_json_fecha", datetime.now().isoformat(timespec="seconds"))


def inicializar_base_datos():
    """Crea el esquema, importa JSON una sola vez y deja Personalizados/numerador."""
    with conexion() as conn:
        _crear_tablas(conn)
        version = meta_get(conn, "esquema_version")
        if version is None:
            meta_set(conn, "esquema_version", VERSION_ESQUEMA)
        _migrar_json_si_corresponde(conn)
        asegurar_personalizados(conn)
        asegurar_numerador(conn)
    return obtener_ruta_db()
