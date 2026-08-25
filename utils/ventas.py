"""
Historial de pedidos confirmados y resúmenes de control interno (no fiscal).
"""
import json
import os
import uuid
from datetime import datetime, timedelta, date


def obtener_ruta_ventas():
    from utils.rutas import obtener_ruta_json
    return obtener_ruta_json('ventas.json')


def _guardar_json_atomico(ruta, datos):
    carpeta = os.path.dirname(ruta)
    os.makedirs(carpeta, exist_ok=True)
    ruta_temporal = ruta + ".tmp"
    try:
        with open(ruta_temporal, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(ruta_temporal, ruta)
    except Exception:
        try:
            if os.path.exists(ruta_temporal):
                os.remove(ruta_temporal)
        except Exception:
            pass
        raise


def cargar_ventas():
    """Carga el historial. Si el archivo no existe o está dañado, no lo pisa."""
    ruta = obtener_ruta_ventas()
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("pedidos"), list):
            return data
        if isinstance(data, list):
            return {"pedidos": data}
        return {"pedidos": []}
    except FileNotFoundError:
        return {"pedidos": []}
    except Exception as e:
        print(f"Error al cargar ventas: {e}")
        return {"pedidos": []}


def _serializar_items(items):
    from utils.productos import calcular_precio_con_ingredientes

    resultado = []
    for item in items or []:
        producto = item.get("producto") or {}
        cantidad = item.get("cantidad", 1)
        modificaciones = item.get("modificaciones_ingredientes", {})
        try:
            precio_unitario = calcular_precio_con_ingredientes(producto, modificaciones)
        except Exception:
            precio_unitario = float(producto.get("precio", 0) or 0)
        resultado.append({
            "nombre": producto.get("nombre", ""),
            "cantidad": cantidad,
            "precio_unitario": round(float(precio_unitario), 2),
            "subtotal": round(float(precio_unitario) * cantidad, 2),
        })
    return resultado


def registrar_pedido(pedido_info, cuenta_en_resumen=True):
    """
    Guarda un pedido confirmado. No debe interrumpir la caja si falla.
    """
    ahora = datetime.now()
    registro = {
        "id": str(uuid.uuid4()),
        "fecha_hora": ahora.isoformat(timespec="seconds"),
        "numero": pedido_info.get("numero"),
        "nombre_cliente": pedido_info.get("nombre_cliente") or "",
        "tipo": pedido_info.get("tipo") or "",
        "forma_pago": pedido_info.get("forma_pago") or "",
        "total": round(float(pedido_info.get("total") or 0), 2),
        "cuenta_en_resumen": bool(cuenta_en_resumen),
        "items": _serializar_items(pedido_info.get("items")),
    }
    data = cargar_ventas()
    data.setdefault("pedidos", [])
    data["pedidos"].append(registro)
    _guardar_json_atomico(obtener_ruta_ventas(), data)
    return registro


def marcar_cuenta_en_resumen(pedido_id, cuenta):
    data = cargar_ventas()
    encontrado = False
    for pedido in data.get("pedidos", []):
        if pedido.get("id") == pedido_id:
            pedido["cuenta_en_resumen"] = bool(cuenta)
            encontrado = True
            break
    if not encontrado:
        return False
    _guardar_json_atomico(obtener_ruta_ventas(), data)
    return True


FORMAS_PAGO = (
    "Desconocido",
    "Efectivo",
    "Tarjeta",
    "Transferencia/Qr",
)


def eliminar_pedido(pedido_id):
    """Borra el pedido del historial. No toca el numerador de la caja."""
    data = cargar_ventas()
    original = data.get("pedidos", [])
    filtrados = [p for p in original if p.get("id") != pedido_id]
    if len(filtrados) == len(original):
        return False
    data["pedidos"] = filtrados
    _guardar_json_atomico(obtener_ruta_ventas(), data)
    return True


def modificar_forma_pago(pedido_id, forma_pago):
    forma = (forma_pago or "").strip() or "Desconocido"
    data = cargar_ventas()
    encontrado = False
    for pedido in data.get("pedidos", []):
        if pedido.get("id") == pedido_id:
            pedido["forma_pago"] = forma
            encontrado = True
            break
    if not encontrado:
        return False
    _guardar_json_atomico(obtener_ruta_ventas(), data)
    return True


def obtener_pedido_por_id(pedido_id):
    for pedido in cargar_ventas().get("pedidos", []):
        if pedido.get("id") == pedido_id:
            return pedido
    return None


def _parsear_fecha(pedido):
    texto = pedido.get("fecha_hora") or ""
    try:
        return datetime.fromisoformat(texto)
    except (ValueError, TypeError):
        return None


def rango_periodo(periodo, ahora=None, desde=None, hasta=None):
    """periodo: 'hoy' | 'semana' | 'mes' | 'personalizado'"""
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
    inicio, fin = rango_periodo(periodo, desde=desde, hasta=hasta)
    pedidos = []
    for pedido in cargar_ventas().get("pedidos", []):
        fecha = _parsear_fecha(pedido)
        if fecha is None:
            continue
        if inicio <= fecha < fin:
            pedidos.append(pedido)
    pedidos.sort(key=lambda p: p.get("fecha_hora") or "", reverse=True)
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
        [c("PAPUCHO FOODTRUCK — Resumen de ventas", 1)],
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
