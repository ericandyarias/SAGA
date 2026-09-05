"""
Historial de pedidos confirmados (SQLite). Control interno, no fiscal.
"""
from datetime import datetime, timedelta, date

from utils.base_datos import conexion, inicializar_base_datos


FORMAS_PAGO = (
    "Desconocido",
    "Efectivo",
    "Tarjeta",
    "Transferencia/Qr",
)


def obtener_ruta_ventas():
    from utils.rutas import obtener_ruta_json
    return obtener_ruta_json("ventas.json")


def _pedido_completo(conn, fila):
    pedido = {
        "id": fila["id"],
        "fecha_hora": fila["fecha_hora"],
        "numero": fila["numero"],
        "nombre_cliente": fila["nombre_cliente"] or "",
        "tipo": fila["tipo"] or "",
        "forma_pago": fila["forma_pago"] or "",
        "total": fila["total"],
        "cuenta_en_resumen": bool(fila["cuenta_en_resumen"]),
        "domicilio": fila["domicilio"] or "",
        "hora_estimada": fila["hora_estimada"] or "",
        "hora_retiro": fila["hora_retiro"] or "",
        "estado_pago": fila["estado_pago"] or "",
        "usuario_id": fila["usuario_id"],
        "comprobante_id": fila["comprobante_id"],
        "items": [],
    }
    items = conn.execute(
        """
        SELECT id, producto_id, nombre, cantidad, precio_base, precio_unitario, subtotal
        FROM pedido_item WHERE pedido_id=? ORDER BY orden, id
        """,
        (fila["id"],),
    ).fetchall()
    for item in items:
        mods = conn.execute(
            """
            SELECT nombre, cantidad_base, cantidad_final, precio_ajuste_unitario
            FROM pedido_item_modificacion WHERE pedido_item_id=? ORDER BY id
            """,
            (item["id"],),
        ).fetchall()
        pedido["items"].append({
            "nombre": item["nombre"],
            "cantidad": item["cantidad"],
            "precio_unitario": item["precio_unitario"],
            "subtotal": item["subtotal"],
            "precio_base": item["precio_base"],
            "producto_id": item["producto_id"],
            "modificaciones": [
                {
                    "nombre": m["nombre"],
                    "cantidad_base": m["cantidad_base"],
                    "cantidad_final": m["cantidad_final"],
                    "precio_ajuste_unitario": m["precio_ajuste_unitario"],
                }
                for m in mods
            ],
        })
    return pedido


def cargar_ventas():
    inicializar_base_datos()
    with conexion() as conn:
        filas = conn.execute(
            "SELECT * FROM pedido ORDER BY fecha_hora"
        ).fetchall()
        return {"pedidos": [_pedido_completo(conn, f) for f in filas]}


def _id_ingrediente(conn, nombre):
    if not nombre:
        return None
    fila = conn.execute("SELECT id FROM ingrediente WHERE nombre=?", (nombre,)).fetchone()
    return fila["id"] if fila else None


def registrar_pedido(pedido_info, cuenta_en_resumen=True):
    """
    Guarda un pedido confirmado. No debe interrumpir la caja si falla.
    """
    import uuid
    from utils.productos import calcular_precio_con_ingredientes

    inicializar_base_datos()
    ahora = datetime.now()
    pedido_id = str(uuid.uuid4())
    registro = {
        "id": pedido_id,
        "fecha_hora": ahora.isoformat(timespec="seconds"),
        "numero": pedido_info.get("numero"),
        "nombre_cliente": pedido_info.get("nombre_cliente") or "",
        "tipo": pedido_info.get("tipo") or "",
        "forma_pago": pedido_info.get("forma_pago") or "",
        "total": round(float(pedido_info.get("total") or 0), 2),
        "cuenta_en_resumen": bool(cuenta_en_resumen),
        "items": [],
    }

    with conexion() as conn:
        conn.execute(
            """
            INSERT INTO pedido(
                id, fecha_hora, numero, nombre_cliente, tipo, domicilio,
                hora_estimada, hora_retiro, forma_pago, estado_pago,
                total, cuenta_en_resumen
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pedido_id,
                registro["fecha_hora"],
                registro["numero"],
                registro["nombre_cliente"],
                registro["tipo"],
                pedido_info.get("domicilio") or None,
                pedido_info.get("hora_estimada") or None,
                pedido_info.get("hora_retiro") or None,
                registro["forma_pago"],
                pedido_info.get("estado_pago") or None,
                registro["total"],
                1 if cuenta_en_resumen else 0,
            ),
        )

        for orden, item in enumerate(pedido_info.get("items") or []):
            producto = item.get("producto") or {}
            cantidad = item.get("cantidad", 1)
            modificaciones = item.get("modificaciones_ingredientes") or {}
            try:
                precio_unitario = calcular_precio_con_ingredientes(producto, modificaciones)
            except Exception:
                precio_unitario = float(producto.get("precio", 0) or 0)
            precio_base = float(producto.get("precio", 0) or 0)
            subtotal = round(float(precio_unitario) * cantidad, 2)
            producto_id = producto.get("id")
            conn.execute(
                """
                INSERT INTO pedido_item(
                    pedido_id, producto_id, nombre, cantidad,
                    precio_base, precio_unitario, subtotal, orden
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pedido_id,
                    producto_id,
                    producto.get("nombre") or "",
                    cantidad,
                    round(precio_base, 2),
                    round(float(precio_unitario), 2),
                    subtotal,
                    orden,
                ),
            )
            item_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            receta = {ing.get("nombre", ""): ing for ing in producto.get("ingredientes") or []}
            nombres = set(receta) | set(modificaciones)
            for nombre in nombres:
                base = int((receta.get(nombre) or {}).get("cantidad_base") or 0)
                final = int(modificaciones.get(nombre, base))
                if final == base and nombre in receta:
                    continue
                ing_id = _id_ingrediente(conn, nombre)
                precio_ajuste = 0.0
                if ing_id:
                    ing = conn.execute(
                        "SELECT precio_extra, precio_resta FROM ingrediente WHERE id=?",
                        (ing_id,),
                    ).fetchone()
                    if final > base:
                        precio_ajuste = float(ing["precio_extra"] or 0)
                    elif final < base:
                        precio_ajuste = float(ing["precio_resta"] or 0)
                    else:
                        precio_ajuste = float(ing["precio_extra"] or 0)
                conn.execute(
                    """
                    INSERT INTO pedido_item_modificacion(
                        pedido_item_id, ingrediente_id, nombre,
                        cantidad_base, cantidad_final, precio_ajuste_unitario
                    ) VALUES(?, ?, ?, ?, ?, ?)
                    """,
                    (item_id, ing_id, nombre, base, final, precio_ajuste),
                )
            registro["items"].append({
                "nombre": producto.get("nombre") or "",
                "cantidad": cantidad,
                "precio_unitario": round(float(precio_unitario), 2),
                "subtotal": subtotal,
            })
    return registro


def marcar_cuenta_en_resumen(pedido_id, cuenta):
    with conexion() as conn:
        cur = conn.execute(
            "UPDATE pedido SET cuenta_en_resumen=? WHERE id=?",
            (1 if cuenta else 0, pedido_id),
        )
        return cur.rowcount > 0


def eliminar_pedido(pedido_id):
    with conexion() as conn:
        cur = conn.execute("DELETE FROM pedido WHERE id=?", (pedido_id,))
        return cur.rowcount > 0


def modificar_forma_pago(pedido_id, forma_pago):
    forma = (forma_pago or "").strip() or "Desconocido"
    with conexion() as conn:
        cur = conn.execute(
            "UPDATE pedido SET forma_pago=? WHERE id=?",
            (forma, pedido_id),
        )
        return cur.rowcount > 0


def obtener_pedido_por_id(pedido_id):
    inicializar_base_datos()
    with conexion() as conn:
        fila = conn.execute("SELECT * FROM pedido WHERE id=?", (pedido_id,)).fetchone()
        if not fila:
            return None
        return _pedido_completo(conn, fila)


def _parsear_fecha(pedido):
    texto = pedido.get("fecha_hora") or ""
    try:
        return datetime.fromisoformat(texto)
    except (ValueError, TypeError):
        return None


def rango_periodo(periodo, ahora=None, desde=None, hasta=None):
    ahora = ahora or datetime.now()
    inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    if periodo == "personalizado" and desde and hasta:
        d1, d2 = desde, hasta
        if isinstance(d1, date) and not isinstance(d1, datetime):
            d1 = datetime(d1.year, d1.month, d1.day)
        if isinstance(d2, date) and not isinstance(d2, datetime):
            d2 = datetime(d2.year, d2.month, d2.day)
        if d2 < d1:
            d1, d2 = d2, d1
        return d1.replace(hour=0, minute=0, second=0, microsecond=0), d2.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
    if periodo == "semana":
        inicio = inicio_dia - timedelta(days=inicio_dia.weekday())
        fin = inicio + timedelta(days=7)
    elif periodo == "mes":
        inicio = inicio_dia.replace(day=1)
        if inicio.month == 12:
            fin = inicio.replace(year=inicio.year + 1, month=1)
        else:
            fin = inicio.replace(month=inicio.month + 1)
    else:
        inicio = inicio_dia
        fin = inicio_dia + timedelta(days=1)
    return inicio, fin


def pedidos_en_periodo(periodo="hoy", desde=None, hasta=None):
    inicializar_base_datos()
    inicio, fin = rango_periodo(periodo, desde=desde, hasta=hasta)
    inicio_txt = inicio.isoformat(timespec="seconds")
    fin_txt = fin.isoformat(timespec="seconds")
    with conexion() as conn:
        filas = conn.execute(
            """
            SELECT * FROM pedido
            WHERE fecha_hora >= ? AND fecha_hora < ?
            ORDER BY fecha_hora DESC
            """,
            (inicio_txt, fin_txt),
        ).fetchall()
        pedidos = [_pedido_completo(conn, f) for f in filas]
    return pedidos, inicio, fin


def calcular_resumen(pedidos):
    que_cuentan = [p for p in pedidos if p.get("cuenta_en_resumen", True)]
    pruebas = [p for p in pedidos if not p.get("cuenta_en_resumen", True)]
    por_pago = {}
    for pedido in que_cuentan:
        clave = pedido.get("forma_pago") or "Sin dato"
        por_pago[clave] = por_pago.get(clave, 0) + float(pedido.get("total") or 0)
    return {
        "cantidad_cuentan": len(que_cuentan),
        "total_cuentan": round(sum(float(p.get("total") or 0) for p in que_cuentan), 2),
        "cantidad_prueba": len(pruebas),
        "total_prueba": round(sum(float(p.get("total") or 0) for p in pruebas), 2),
        "por_pago": {k: round(v, 2) for k, v in por_pago.items()},
    }


def exportar_excel(ruta_archivo, periodo="hoy", desde=None, hasta=None):
    from utils.excel_xlsx import guardar_xlsx

    pedidos, inicio, fin = pedidos_en_periodo(periodo, desde=desde, hasta=hasta)
    resumen = calcular_resumen(pedidos)
    nombres_periodo = {
        "hoy": "Hoy",
        "semana": "Esta semana",
        "mes": "Este mes",
        "personalizado": "Personalizado",
    }
    etiqueta = nombres_periodo.get(periodo, periodo)
    hasta_txt = (fin - timedelta(seconds=1)).strftime("%d/%m/%Y")
    desde_txt = inicio.strftime("%d/%m/%Y")

    def c(valor, estilo=0, numero=False):
        return {"v": valor, "s": estilo, "n": numero}

    filas = [
        [c("SAGA — Resumen de ventas", 1)],
        [c("Control interno · no es un documento fiscal", 2)],
        [c("Periodo", 3), c(etiqueta, 5), c("Desde", 3), c(desde_txt, 5), c("Hasta", 3), c(hasta_txt, 5)],
        [],
        [c("Pedidos confirmados", 3), c(int(resumen["cantidad_cuentan"]), 9, True),
         c("Total que cuenta", 3), c(resumen["total_cuentan"], 7, True)],
        [c("Pedidos no confirmados", 3), c(int(resumen["cantidad_prueba"]), 9, True),
         c("Monto prueba", 3), c(resumen["total_prueba"], 7, True)],
        [],
        [c("Desglose por forma de pago de Pedidos Confirmados", 2)],
    ]
    if resumen["por_pago"]:
        for forma, monto in resumen["por_pago"].items():
            filas.append([c(forma, 5), c(monto, 7, True)])
    else:
        filas.append([c("Sin ventas que cuenten en este periodo", 5)])

    filas.append([])
    filas.append([
        c("Pedido", 4), c("Estado del pedido", 4), c("Fecha", 4), c("Hora", 4),
        c("Cliente", 4), c("Tipo", 4), c("Forma de pago", 4), c("Total", 4),
    ])

    for i, pedido in enumerate(sorted(pedidos, key=lambda p: p.get("fecha_hora") or "")):
        fecha = _parsear_fecha(pedido)
        estilo_fila = 6 if i % 2 else 5
        estilo_monto = 8 if i % 2 else 7
        total = float(pedido.get("total") or 0)
        filas.append([
            c(f"{int(pedido.get('numero') or 0):04d}", estilo_fila),
            c("Confirmado" if pedido.get("cuenta_en_resumen", True) else "No confirmado", estilo_fila),
            c(fecha.strftime("%d/%m/%Y") if fecha else "", estilo_fila),
            c(fecha.strftime("%H:%M") if fecha else "", estilo_fila),
            c(pedido.get("nombre_cliente") or "", estilo_fila),
            c(pedido.get("tipo") or "", estilo_fila),
            c(pedido.get("forma_pago") or "", estilo_fila),
            c(total, estilo_monto, True),
        ])

    anchos = [26, 22, 24, 18, 20, 22, 20, 16]
    combinadas = ["A1:H1", "A2:H2", "A8:H8"]
    guardar_xlsx(ruta_archivo, filas, anchos=anchos, combinadas=combinadas)
    return ruta_archivo
