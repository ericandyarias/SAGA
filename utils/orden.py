"""
Propósito: numerador de pedidos (el número que sale en el ticket).
Se guarda en SQLite; orden_actual.txt solo sirve para migrar instalaciones viejas.
"""
from utils.base_datos import conexion, inicializar_base_datos


def obtener_ruta_orden():
    from utils.rutas import obtener_ruta_data
    import os
    return os.path.join(obtener_ruta_data(), "orden_actual.txt")


def leer_numero_orden():
    inicializar_base_datos()
    with conexion() as conn:
        fila = conn.execute("SELECT siguiente FROM numerador WHERE id=1").fetchone()
        if not fila:
            conn.execute("INSERT INTO numerador(id, siguiente) VALUES(1, 1)")
            return 1
        return int(fila["siguiente"])


def guardar_numero_orden(numero):
    inicializar_base_datos()
    with conexion() as conn:
        conn.execute(
            "INSERT INTO numerador(id, siguiente) VALUES(1, ?) ON CONFLICT(id) DO UPDATE SET siguiente=excluded.siguiente",
            (int(numero),),
        )


def incrementar_orden():
    inicializar_base_datos()
    with conexion() as conn:
        fila = conn.execute("SELECT siguiente FROM numerador WHERE id=1").fetchone()
        actual = int(fila["siguiente"]) if fila else 1
        nuevo = actual + 1
        conn.execute(
            "INSERT INTO numerador(id, siguiente) VALUES(1, ?) ON CONFLICT(id) DO UPDATE SET siguiente=excluded.siguiente",
            (nuevo,),
        )
        return nuevo
