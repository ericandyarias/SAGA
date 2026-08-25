"""
Módulo para generar tickets de pedidos usando python-escpos con Win32Raw
Genera tickets en formato ESC/POS para impresoras térmicas (80mm)
Impresión directa sin previsualización, ocupando todo el ancho del papel
Usa Win32Raw para imprimir por nombre de impresora en Windows
"""
import os
import sys
import json
from datetime import datetime

try:
    from escpos.printer import Win32Raw
    from escpos.exceptions import Error
    ESCPOS_AVAILABLE = True
except ImportError:
    ESCPOS_AVAILABLE = False
    print("Advertencia: python-escpos no está instalado. Ejecuta: pip install python-escpos")


def obtener_ruta_tickets():
    """Obtiene la ruta del directorio de tickets"""
    from utils.rutas import obtener_ruta_data
    return os.path.join(obtener_ruta_data(), 'tickets')


def obtener_ruta_config():
    """Obtiene la ruta del archivo de configuración"""
    from utils.rutas import obtener_ruta_json
    return obtener_ruta_json('config.json')


def _config_por_defecto():
    return {
        "impresora": {
            "ancho_ticket": 80,
            "modelo": "Térmica 80mm",
            "nombre_impresora": ""
        },
        "tickets": {
            "incluir_fecha_hora": True,
            "lineas_corte": 3,
            "enlace_qr": ""
        }
    }


def cargar_configuracion():
    """Carga la configuración desde el archivo JSON sin pisarlo si está dañado."""
    ruta_config = obtener_ruta_config()
    try:
        with open(ruta_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        if not isinstance(config, dict):
            return _config_por_defecto()
        config.setdefault("impresora", {})
        config.setdefault("tickets", {"incluir_fecha_hora": True, "lineas_corte": 3, "enlace_qr": ""})
        if not isinstance(config.get("impresora"), dict):
            config["impresora"] = _config_por_defecto()["impresora"]
        if not isinstance(config.get("tickets"), dict):
            config["tickets"] = _config_por_defecto()["tickets"]
        config["tickets"].setdefault("incluir_fecha_hora", True)
        config["tickets"].setdefault("lineas_corte", 3)
        config["tickets"].setdefault("enlace_qr", "")
        return config
    except FileNotFoundError:
        config_default = _config_por_defecto()
        try:
            _guardar_json_atomico(ruta_config, config_default)
        except Exception:
            pass
        return config_default
    except Exception as e:
        print(f"Error al cargar configuración: {e}")
        return _config_por_defecto()


def _guardar_json_atomico(ruta, datos):
    """Escribe el JSON en un temporal y lo reemplaza, para no corromper el archivo."""
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


def guardar_configuracion_impresora(nombre_impresora):
    """
    Guarda la impresora de tickets (térmica 80 mm) sin perder el resto de la config.
    """
    nombre = (nombre_impresora or "").strip()
    if not nombre:
        raise ValueError("Seleccione una impresora")

    config = cargar_configuracion()
    if not isinstance(config, dict):
        config = _config_por_defecto()
    config.setdefault("impresora", {})
    if not isinstance(config.get("impresora"), dict):
        config["impresora"] = {}
    config.setdefault("tickets", {"incluir_fecha_hora": True, "lineas_corte": 3, "enlace_qr": ""})
    if not isinstance(config.get("tickets"), dict):
        config["tickets"] = {"incluir_fecha_hora": True, "lineas_corte": 3, "enlace_qr": ""}
    config["impresora"]["nombre_impresora"] = nombre
    config["impresora"]["ancho_ticket"] = 80
    config["impresora"]["modelo"] = "Térmica 80mm"

    _guardar_json_atomico(obtener_ruta_config(), config)
    return config


def normalizar_enlace_qr(enlace):
    """Limpia el enlace. Vacío si no hay nada usable."""
    texto = (enlace or "").strip()
    if not texto:
        return ""
    if "://" not in texto:
        texto = "https://" + texto
    return texto


def guardar_enlace_qr(enlace):
    """Guarda el enlace del QR del ticket de cliente (puede quedar vacío para no imprimirlo)."""
    texto = normalizar_enlace_qr(enlace)
    config = cargar_configuracion()
    if not isinstance(config, dict):
        config = _config_por_defecto()
    config.setdefault("tickets", {"incluir_fecha_hora": True, "lineas_corte": 3, "enlace_qr": ""})
    if not isinstance(config.get("tickets"), dict):
        config["tickets"] = {"incluir_fecha_hora": True, "lineas_corte": 3, "enlace_qr": ""}
    config["tickets"]["enlace_qr"] = texto
    _guardar_json_atomico(obtener_ruta_config(), config)
    return config


def obtener_enlace_qr(config=None):
    if config is None:
        config = cargar_configuracion()
    tickets = config.get("tickets") if isinstance(config, dict) else {}
    if not isinstance(tickets, dict):
        return ""
    return normalizar_enlace_qr(tickets.get("enlace_qr", ""))


def imprimir_qr_ticket_cliente(printer, enlace):
    """
    Imprime un QR al final del ticket de cliente.
    Primero intenta el comando nativo de la impresora; si falla, lo manda como imagen.
    Si ambos fallan, el resto del ticket igual se imprime.
    """
    enlace = normalizar_enlace_qr(enlace)
    if not enlace or printer is None:
        return

    try:
        printer.set(align='center', font='a', width=1, height=1, bold=False)
        printer.text("Seguinos en Instagram\n")
    except Exception:
        pass

    try:
        printer.qr(enlace, size=6, native=True, center=True)
        return
    except TypeError:
        try:
            printer.qr(enlace, size=6, native=True)
            return
        except Exception as e:
            print(f"QR nativo no disponible, se intenta como imagen: {e}")
    except Exception as e:
        print(f"QR nativo no disponible, se intenta como imagen: {e}")

    try:
        printer.qr(enlace, size=6, native=False, center=True)
        return
    except TypeError:
        try:
            printer.qr(enlace, size=6, native=False)
            return
        except Exception as e:
            print(f"No se pudo imprimir el QR como imagen: {e}")
    except Exception as e:
        print(f"No se pudo imprimir el QR como imagen: {e}")


def listar_impresoras_windows():
    """
    Lista todas las impresoras disponibles en Windows
    Retorna lista de nombres de impresoras
    """
    if sys.platform != 'win32':
        return []
    
    try:
        import win32print
        impresoras = []
        impresoras_raw = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        for impresora in impresoras_raw:
            impresoras.append(impresora[2])  # El nombre está en el índice 2
        return impresoras
    except ImportError:
        print("Advertencia: pywin32 no está instalado. Ejecuta: pip install pywin32")
        return []
    except Exception as e:
        print(f"Error al listar impresoras: {e}")
        return []


def verificar_impresora_existe(nombre_impresora):
    """
    Verifica si una impresora existe en Windows
    Retorna True si existe, False en caso contrario
    """
    if sys.platform != 'win32':
        return False
    
    try:
        import win32print
        impresoras = listar_impresoras_windows()
        return nombre_impresora in impresoras
    except Exception as e:
        print(f"Error al verificar impresora: {e}")
        return False


def obtener_impresora():
    """
    Obtiene la conexión a la impresora usando Win32Raw
    Retorna objeto printer o None si hay error
    """
    if not ESCPOS_AVAILABLE:
        print("Error: python-escpos no está disponible")
        return None
    
    if sys.platform != 'win32':
        print("Error: Win32Raw solo está disponible en Windows")
        return None
    
    config = cargar_configuracion()
    nombre_impresora = config.get('impresora', {}).get('nombre_impresora', '')
    
    if not nombre_impresora:
        print("Error: No se ha configurado el nombre de la impresora")
        print("Configure la impresora en Administración > Configuración")
        return None
    
    # Verificar que la impresora existe
    if not verificar_impresora_existe(nombre_impresora):
        print(f"Error: La impresora '{nombre_impresora}' no se encuentra en el sistema")
        print("\nImpresoras disponibles:")
        impresoras = listar_impresoras_windows()
        if impresoras:
            for imp in impresoras:
                print(f"  - {imp}")
        else:
            print("  (No se pudieron listar las impresoras)")
        print("Elija la impresora en Administración > Configuración")
        return None
    
    try:
        printer = Win32Raw(nombre_impresora)
        return printer
    except Error as e:
        print(f"Error al conectar con la impresora '{nombre_impresora}': {e}")
        return None
    except Exception as e:
        print(f"Error inesperado al conectar con la impresora: {e}")
        return None


def formatear_texto_centrado(texto, ancho=48):
    """
    Formatea texto centrado para impresora térmica
    ancho: ancho en caracteres (48 para impresora de 80mm)
    """
    texto = str(texto)
    if len(texto) >= ancho:
        return texto[:ancho]
    
    espacios_izq = (ancho - len(texto)) // 2
    espacios_der = ancho - len(texto) - espacios_izq
    return ' ' * espacios_izq + texto + ' ' * espacios_der


def formatear_linea_producto(nombre, cantidad, precio_total, ancho=48):
    """
    Formatea una línea de producto: cantidad + nombre a la izquierda, precio total a la derecha
    Formato: cantidad Nombre                    $precio_total
    ancho: ancho total en caracteres
    
    Nota: precio_total ya debe incluir la multiplicación por cantidad
    """
    cantidad_nombre = f"{cantidad} {nombre}"
    precio_str = f"${precio_total:,.0f}"
    
    # Calcular espacios para alinear precio exactamente al final (ancho - len(precio_str))
    # Esto asegura que todos los precios terminen en la misma columna
    espacios_necesarios = ancho - len(cantidad_nombre) - len(precio_str)
    
    if espacios_necesarios < 1:
        # Si no cabe, truncar nombre
        max_nombre = ancho - len(precio_str) - len(str(cantidad)) - 2  # 2 para espacios
        nombre_truncado = nombre[:max_nombre] + "..."
        cantidad_nombre = f"{cantidad} {nombre_truncado}"
        espacios_necesarios = ancho - len(cantidad_nombre) - len(precio_str)
    
    return cantidad_nombre + ' ' * espacios_necesarios + precio_str


def tiene_modificaciones_reales(producto, modificaciones):
    """
    Verifica si un producto tiene modificaciones reales de ingredientes
    (es decir, si alguna cantidad difiere de la cantidad base o si hay ingredientes adicionales)
    
    Args:
        producto: Diccionario del producto con ingredientes
        modificaciones: Dict con {nombre_ingrediente: cantidad_actual}
    
    Returns:
        bool: True si hay modificaciones reales, False en caso contrario
    """
    if not modificaciones:
        return False
    
    ingredientes = producto.get('ingredientes', [])
    ingredientes_producto_dict = {ing.get('nombre', '') for ing in ingredientes}
    
    # Verificar modificaciones en ingredientes del producto
    for ingrediente in ingredientes:
        nombre = ingrediente.get('nombre', '')
        cantidad_base = ingrediente.get('cantidad_base', 1)
        cantidad_actual = modificaciones.get(nombre, cantidad_base)
        
        if cantidad_actual != cantidad_base:
            return True
    
    # Verificar ingredientes adicionales que no están en el producto
    for nombre_ing, cantidad_actual in modificaciones.items():
        if nombre_ing not in ingredientes_producto_dict and cantidad_actual > 0:
            return True
    
    return False


def formatear_linea_ingrediente(nombre_ing, cantidad_mod, es_extra, precio_unitario, cantidad_items, ancho=48):
    """
    Formatea una línea de ingrediente modificado
    Formato para extra simple:   Extra Nombre                    +$Precio
    Formato para extra múltiple: cantidad Extra Nombre           +$total
    Formato para sin:            Sin Nombre                       -$Precio
    
    Args:
        nombre_ing: Nombre del ingrediente
        cantidad_mod: Cantidad modificada (extras o quitados)
        es_extra: True si es extra, False si es quitado
        precio_unitario: Precio unitario del ajuste (por extra o por quitar)
        cantidad_items: Cantidad de items del producto (para calcular total)
        ancho: Ancho total en caracteres
    
    Returns:
        str: Línea formateada con precio alineado exactamente a la derecha (misma posición que precios base)
    """
    # Calcular precio total
    if es_extra:
        precio_total = precio_unitario * cantidad_mod * cantidad_items
        signo = "+"
    else:
        precio_total = precio_unitario * cantidad_mod * cantidad_items
        signo = "-"
    
    # Formato especial para extras múltiples
    if es_extra and cantidad_mod > 1:
        # Formato simple en una línea: "cantidad Extra Nombre +$total"
        parte_izq = f"  {cantidad_mod} Extra {nombre_ing}"
        precio_str = f"{signo}${precio_total:,.0f}"
    else:
        # Formato simple: "Extra Nombre" o "Sin Nombre"
        prefijo = "  Extra " if es_extra else "  Sin "
        parte_izq = prefijo + nombre_ing
        precio_str = f"{signo}${abs(precio_total):,.0f}"
    
    # Calcular espacios para alinear precio exactamente al final (ancho - len(precio_str))
    # Esto asegura que todos los precios terminen en la misma columna que los precios base
    espacios_necesarios = ancho - len(parte_izq) - len(precio_str)
    
    if espacios_necesarios < 1:
        # Si no cabe, truncar parte izquierda
        max_ancho_parte_izq = ancho - len(precio_str) - 1
        if len(parte_izq) > max_ancho_parte_izq:
            parte_izq = parte_izq[:max_ancho_parte_izq - 3] + "..."
        espacios_necesarios = ancho - len(parte_izq) - len(precio_str)
    
    return parte_izq + ' ' * espacios_necesarios + precio_str


def formatear_linea_subtotal(precio_unitario, cantidad, subtotal, ancho=48):
    """
    Formatea la línea de subtotal para productos editados
    Formato: $ precio_unitario   x cantidad     =     $ subtotal
    El precio unitario se alinea a la derecha
    
    Args:
        precio_unitario: Precio unitario del producto (con modificaciones)
        cantidad: Cantidad del producto
        subtotal: Total del producto (precio_unitario * cantidad)
        ancho: Ancho total en caracteres
    
    Returns:
        str: Línea formateada
    """
    precio_str = f"${precio_unitario:,.0f}"
    cantidad_str = f"x {cantidad}"
    subtotal_str = f"=     ${subtotal:,.0f}"
    
    # Calcular espacios para alinear precio a la derecha
    # Estructura: espacios_izq + precio_str + espacios1 + cantidad_str + espacios2 + subtotal_str
    # El precio debe quedar alineado a la derecha, luego espacios, luego cantidad, luego espacios, luego subtotal
    
    # Calcular el ancho necesario para precio + espacios + cantidad
    ancho_precio_cantidad = len(precio_str) + 3 + len(cantidad_str)  # 3 espacios entre precio y cantidad
    
    # Calcular espacios para alinear el precio a la derecha
    # Queremos que el precio esté cerca del centro-izquierda, pero alineado
    espacios_izq = max(0, ancho - len(precio_str) - 3 - len(cantidad_str) - len(subtotal_str) - 5)
    espacios1 = 3  # Espacios fijos entre precio y cantidad
    espacios2 = 5  # Espacios fijos entre cantidad y "="
    
    return ' ' * espacios_izq + precio_str + ' ' * espacios1 + cantidad_str + ' ' * espacios2 + subtotal_str


def imprimir_ticket_escpos(pedido_info, tipo_ticket):
    """
    Imprime un ticket directamente usando ESC/POS con Win32Raw
    
    Args:
        pedido_info: Diccionario con la información del pedido
        tipo_ticket: 'COCINA' o 'CLIENTE'
    
    Returns:
        bool: True si la impresión fue exitosa, False en caso contrario
    """
    if not ESCPOS_AVAILABLE:
        print("Error: python-escpos no está disponible")
        return False
    
    if sys.platform != 'win32':
        print("Error: Win32Raw solo está disponible en Windows")
        return False
    
    printer = None
    try:
        printer = obtener_impresora()
        if not printer:
            return False
        
        config = cargar_configuracion()
        ancho_caracteres = 48  # Ancho estándar para impresora de 80mm
        
        # Inicializar impresora
        printer.set(align='center', font='a', width=2, height=2, bold=True)
        printer.text("PAPUCHO FOODTRUCK\n")
        
        # Separador grueso
        printer.set(align='center')
        printer.text("=" * ancho_caracteres + "\n")
        
        # Marca del ticket (COCINA o CLIENTE) - sin fecha
        printer.set(align='center', font='a', width=1, height=1, bold=True)
        printer.text(f"=== {tipo_ticket} ===\n")
        
        # Número de orden y fecha en la misma línea
        if config.get('tickets', {}).get('incluir_fecha_hora', True):
            fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
            texto_izq = f"Orden #{pedido_info['numero']:04d}"
            texto_der = fecha_hora
            espacios = " " * (ancho_caracteres - len(texto_izq) - len(texto_der))
            printer.set(align='left', font='a', width=1, height=1, bold=False)
            printer.text(texto_izq + espacios + texto_der + "\n")
        else:
            printer.set(align='center', font='a', width=1, height=1, bold=False)
            printer.text(f"Orden #{pedido_info['numero']:04d}\n")
        
        # Separador
        printer.set(align='center')
        printer.text("=" * ancho_caracteres + "\n")
        
        # Cliente
        printer.set(align='left', font='a', width=1, height=1, bold=False)
        printer.text(f"Cliente: {pedido_info['nombre_cliente']}\n")
        
        # Tipo de pedido y información adicional
        tipo_pedido = pedido_info.get('tipo', 'Servicio en mesa')
        
        # Domicilio si es pedido a domicilio
        if tipo_pedido == "Domicilio":
            if pedido_info.get('domicilio'):
                domicilio = pedido_info['domicilio']
                # Si el domicilio es muy largo, dividirlo en líneas
                if len(domicilio) > ancho_caracteres - 12:
                    palabras = domicilio.split()
                    linea = "Domicilio: "
                    for palabra in palabras:
                        if len(linea) + len(palabra) + 1 > ancho_caracteres:
                            printer.text(linea + "\n")
                            linea = "  " + palabra
                        else:
                            linea += " " + palabra if linea != "Domicilio: " else palabra
                    printer.text(linea + "\n")
                else:
                    printer.text(f"Domicilio: {domicilio}\n")
            
            # Hora estimada si existe
            if pedido_info.get('hora_estimada'):
                printer.text(f"Hora estimada: {pedido_info['hora_estimada']}\n")
        elif tipo_pedido == "Retira en puesto":
            # Mostrar tipo de pedido
            printer.text(f"{tipo_pedido}\n")
            # Hora estimada si existe
            if pedido_info.get('hora_retiro'):
                printer.text(f"Hora estimada: {pedido_info['hora_retiro']}\n")
        else:
            # Servicio en mesa u otros tipos
            printer.text(f"{tipo_pedido}\n")
        
        # PEDIDO
        printer.set(align='left', bold=True)
        printer.text("PEDIDO:\n")
        printer.set(bold=False)
        
        # Items del pedido
        for item in pedido_info['items']:
            producto = item['producto']
            nombre = producto['nombre']
            cantidad = item['cantidad']
            modificaciones = item.get('modificaciones_ingredientes', {})
            
            # Calcular precio unitario y subtotal considerando ingredientes
            from utils.productos import calcular_precio_con_ingredientes
            precio_unitario = calcular_precio_con_ingredientes(producto, modificaciones)
            subtotal = precio_unitario * cantidad
            
            # Verificar si tiene modificaciones reales
            tiene_modificaciones = tiene_modificaciones_reales(producto, modificaciones)
            
            # Precio base del producto (sin modificaciones)
            precio_base = producto.get('precio', 0.0)
            
            if tiene_modificaciones:
                # Formato especial para productos editados
                # Mostrar: cantidad + nombre + precio total (precio_base * cantidad)
                precio_total = precio_base * cantidad
                linea_producto = formatear_linea_producto(nombre, cantidad, precio_total, ancho_caracteres)
                printer.text(linea_producto + "\n")
                
                # Mostrar modificaciones de ingredientes
                ingredientes = producto.get('ingredientes', [])
                # Importar función para buscar ingrediente por nombre
                from utils.ingredientes import buscar_ingrediente_por_nombre
                
                if ingredientes and modificaciones:
                    for ingrediente in ingredientes:
                        nombre_ing = ingrediente.get('nombre', '')
                        cantidad_base = ingrediente.get('cantidad_base', 1)
                        cantidad_actual = modificaciones.get(nombre_ing, cantidad_base)
                        
                        # Buscar el ingrediente actualizado desde ingredientes.json para obtener precios
                        ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre_ing)
                        if ingrediente_actualizado:
                            precio_extra = ingrediente_actualizado.get('precio_extra', 0.0)
                            precio_resta = ingrediente_actualizado.get('precio_resta', 0.0)
                        else:
                            # Si el ingrediente no existe, usar 0.0
                            precio_extra = 0.0
                            precio_resta = 0.0
                        
                        if cantidad_actual > cantidad_base:
                            # Extras agregados
                            extras = cantidad_actual - cantidad_base
                            texto_ing = formatear_linea_ingrediente(
                                nombre_ing, extras, True, precio_extra, cantidad, ancho_caracteres
                            )
                            printer.text(texto_ing + "\n")
                        elif cantidad_actual < cantidad_base:
                            # Ingredientes quitados
                            quitados = cantidad_base - cantidad_actual
                            texto_ing = formatear_linea_ingrediente(
                                nombre_ing, quitados, False, precio_resta, cantidad, ancho_caracteres
                            )
                            printer.text(texto_ing + "\n")
                
                # Procesar ingredientes adicionales que no están en el producto (siempre, incluso si no hay ingredientes principales)
                if modificaciones:
                    ingredientes_producto_dict = {ing.get('nombre', '') for ing in ingredientes}
                    for nombre_ing, cantidad_actual in modificaciones.items():
                        if nombre_ing not in ingredientes_producto_dict and cantidad_actual > 0:
                            # Este es un ingrediente adicional que no está en el producto
                            ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre_ing)
                            if ingrediente_actualizado:
                                precio_extra = ingrediente_actualizado.get('precio_extra', 0.0)
                            else:
                                precio_extra = 0.0
                            
                            # Mostrar siempre los ingredientes adicionales si tienen cantidad > 0, independientemente del precio
                            texto_ing = formatear_linea_ingrediente(
                                nombre_ing, cantidad_actual, True, precio_extra, cantidad, ancho_caracteres
                            )
                            printer.text(texto_ing + "\n")
            else:
                # Formato normal para productos sin editar: cantidad + nombre + precio total (precio_base * cantidad)
                precio_total = precio_base * cantidad
                linea = formatear_linea_producto(nombre, cantidad, precio_total, ancho_caracteres)
                printer.text(linea + "\n")
        
        # Separador
        printer.text("-" * ancho_caracteres + "\n")
        
        # Total a pagar
        total = pedido_info['total']
        printer.set(align='left', bold=True)
        printer.text("TOTAL A PAGAR:")
        printer.set(align='right', bold=True)
        printer.text(f"${total:,.0f}\n")
        
        # Separador
        printer.set(align='center')
        printer.text("-" * ancho_caracteres + "\n")
        
        # Forma de pago
        printer.set(align='left', bold=False)
        forma_pago = pedido_info['forma_pago']
        
        # Formato especial para "Desconocido"
        if forma_pago == "Desconocido":
            if tipo_ticket == 'COCINA':
                # En ticket de COCINA mostrar opciones para tachar
                printer.text("Metodo de pago:\n")
                printer.text("\n")
                # Centrar las opciones de pago
                printer.set(align='center', bold=False)
                printer.text("Efectivo      Transferencia/Qr      Tarjeta\n")
                printer.text("\n")
            # En ticket de CLIENTE no mostrar nada
        else:
            printer.text(f"Metodo de pago: {forma_pago}\n")
            printer.text("\n")
            printer.text("\n")
        
        # Estado de pago (solo en ticket de cocina)
        if tipo_ticket == 'COCINA' and pedido_info.get('estado_pago'):
            estado_pago = pedido_info['estado_pago']
            # Centrar el estado de pago
            texto_estado = "Pagado                      Pendiente de pago"
            printer.set(align='center', bold=False)
            printer.text(f"{texto_estado}\n")
        
        # Separador final
        printer.set(align='center')
        printer.text("=" * ancho_caracteres + "\n")
        
        # QR del Instagram u otro enlace (solo ticket de cliente)
        if tipo_ticket == 'CLIENTE':
            imprimir_qr_ticket_cliente(printer, obtener_enlace_qr(config))
            printer.text("\n")
            espacios_corte = 1
        else:
            espacios_corte = 2

        for _ in range(espacios_corte):
            printer.text("\n")

        try:
            printer.cut(mode="PART", feed=False)
        except TypeError:
            printer.cut()
        
        # Cerrar conexión
        printer.close()
        
        return True
        
    except Error as e:
        print(f"Error ESC/POS al imprimir ticket: {e}")
        if printer:
            try:
                printer.close()
            except:
                pass
        return False
    except Exception as e:
        print(f"Error inesperado al imprimir ticket: {e}")
        if printer:
            try:
                printer.close()
            except:
                pass
        return False


def guardar_ticket_texto(pedido_info, tipo_ticket):
    """
    Guarda el ticket en un archivo de texto plano (opcional, para respaldo)
    
    Args:
        pedido_info: Diccionario con la información del pedido
        tipo_ticket: 'COCINA' o 'CLIENTE'
    
    Returns:
        str: Ruta del archivo guardado
    """
    # Asegurar que el directorio existe
    directorio_tickets = obtener_ruta_tickets()
    os.makedirs(directorio_tickets, exist_ok=True)
    
    # Generar nombre del archivo
    numero_orden = pedido_info['numero']
    nombre_archivo = f"ticket_{tipo_ticket.lower()}_{numero_orden:04d}.txt"
    ruta_archivo = os.path.join(directorio_tickets, nombre_archivo)
    
    # Generar contenido del ticket en texto plano
    config = cargar_configuracion()
    ancho_caracteres = 48
    
    contenido = []
    contenido.append("=" * ancho_caracteres)
    contenido.append(formatear_texto_centrado("PAPUCHO FOODTRUCK", ancho_caracteres))
    contenido.append("=" * ancho_caracteres)
    
    # Marca del ticket (COCINA o CLIENTE) - sin fecha
    contenido.append(formatear_texto_centrado(f"=== {tipo_ticket} ===", ancho_caracteres))
    
    # Número de orden y fecha en la misma línea
    if config.get('tickets', {}).get('incluir_fecha_hora', True):
        fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
        texto_izq = f"Orden #{pedido_info['numero']:04d}"
        texto_der = fecha_hora
        espacios = " " * (ancho_caracteres - len(texto_izq) - len(texto_der))
        contenido.append(texto_izq + espacios + texto_der)
    else:
        contenido.append(formatear_texto_centrado(f"Orden #{pedido_info['numero']:04d}", ancho_caracteres))
    
    contenido.append("=" * ancho_caracteres)
    contenido.append(f"Cliente: {pedido_info['nombre_cliente']}")
    
    # Tipo de pedido
    tipo_pedido = pedido_info.get('tipo', 'Servicio en mesa')
    
    # Domicilio si es pedido a domicilio
    if tipo_pedido == "Domicilio":
        if pedido_info.get('domicilio'):
            contenido.append(f"Domicilio: {pedido_info['domicilio']}")
        # Hora estimada si existe
        if pedido_info.get('hora_estimada'):
            contenido.append(f"Hora estimada: {pedido_info['hora_estimada']}")
    elif tipo_pedido == "Retira en puesto":
        # Mostrar tipo de pedido
        contenido.append(f"{tipo_pedido}")
        # Hora estimada si existe
        if pedido_info.get('hora_retiro'):
            contenido.append(f"Hora estimada: {pedido_info['hora_retiro']}")
    else:
        # Servicio en mesa u otros tipos
        contenido.append(f"{tipo_pedido}")
    
    contenido.append("PEDIDO:")
    
    for item in pedido_info['items']:
        producto = item['producto']
        nombre = producto['nombre']
        cantidad = item['cantidad']
        modificaciones = item.get('modificaciones_ingredientes', {})
        
        # Calcular precio unitario y subtotal considerando ingredientes
        from utils.productos import calcular_precio_con_ingredientes
        precio_unitario = calcular_precio_con_ingredientes(producto, modificaciones)
        subtotal = precio_unitario * cantidad
        
        # Precio base del producto (sin modificaciones)
        precio_base = producto.get('precio', 0.0)
        
        # Verificar si tiene modificaciones reales
        tiene_modificaciones = tiene_modificaciones_reales(producto, modificaciones)
        
        if tiene_modificaciones:
            # Formato especial para productos editados
            # Mostrar: cantidad + nombre + precio total (precio_base * cantidad)
            precio_total = precio_base * cantidad
            linea_producto = formatear_linea_producto(nombre, cantidad, precio_total, ancho_caracteres)
            contenido.append(linea_producto)
            
            # Mostrar modificaciones de ingredientes
            ingredientes = producto.get('ingredientes', [])
            # Importar función para buscar ingrediente por nombre
            from utils.ingredientes import buscar_ingrediente_por_nombre
            
            if ingredientes and modificaciones:
                for ingrediente in ingredientes:
                    nombre_ing = ingrediente.get('nombre', '')
                    cantidad_base = ingrediente.get('cantidad_base', 1)
                    cantidad_actual = modificaciones.get(nombre_ing, cantidad_base)
                    
                    # Buscar el ingrediente actualizado desde ingredientes.json para obtener precios
                    ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre_ing)
                    if ingrediente_actualizado:
                        precio_extra = ingrediente_actualizado.get('precio_extra', 0.0)
                        precio_resta = ingrediente_actualizado.get('precio_resta', 0.0)
                    else:
                        # Si el ingrediente no existe, usar 0.0
                        precio_extra = 0.0
                        precio_resta = 0.0
                    
                    if cantidad_actual > cantidad_base:
                        # Extras agregados
                        extras = cantidad_actual - cantidad_base
                        texto_ing = formatear_linea_ingrediente(
                            nombre_ing, extras, True, precio_extra, cantidad, ancho_caracteres
                        )
                        contenido.append(texto_ing)
                    elif cantidad_actual < cantidad_base:
                        # Ingredientes quitados
                        quitados = cantidad_base - cantidad_actual
                        texto_ing = formatear_linea_ingrediente(
                            nombre_ing, quitados, False, precio_resta, cantidad, ancho_caracteres
                        )
                        contenido.append(texto_ing)
            
            # Procesar ingredientes adicionales que no están en el producto (siempre, incluso si no hay ingredientes principales)
            if modificaciones:
                ingredientes_producto_dict = {ing.get('nombre', '') for ing in ingredientes}
                for nombre_ing, cantidad_actual in modificaciones.items():
                    if nombre_ing not in ingredientes_producto_dict and cantidad_actual > 0:
                        # Este es un ingrediente adicional que no está en el producto
                        ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre_ing)
                        if ingrediente_actualizado:
                            precio_extra = ingrediente_actualizado.get('precio_extra', 0.0)
                        else:
                            precio_extra = 0.0
                        
                        # Mostrar siempre los ingredientes adicionales si tienen cantidad > 0, independientemente del precio
                        texto_ing = formatear_linea_ingrediente(
                            nombre_ing, cantidad_actual, True, precio_extra, cantidad, ancho_caracteres
                        )
                        contenido.append(texto_ing)
        else:
            # Formato normal para productos sin editar: cantidad + nombre + precio total (precio_base * cantidad)
            precio_total = precio_base * cantidad
            linea = formatear_linea_producto(nombre, cantidad, precio_total, ancho_caracteres)
            contenido.append(linea)
    
    contenido.append("-" * ancho_caracteres)
    total = pedido_info['total']
    linea_total = "TOTAL A PAGAR:" + " " * (ancho_caracteres - len("TOTAL A PAGAR:") - len(f"${total:,.0f}")) + f"${total:,.0f}"
    contenido.append(linea_total)
    contenido.append("-" * ancho_caracteres)
    
    # Forma de pago
    forma_pago = pedido_info['forma_pago']
    
    # Formato especial para "Desconocido"
    if forma_pago == "Desconocido":
        if tipo_ticket == 'COCINA':
            # En ticket de COCINA mostrar opciones para tachar
            contenido.append("Metodo de pago:")
            contenido.append("")
            # Centrar las opciones de pago
            contenido.append(formatear_texto_centrado("Efectivo      Transferencia/Qr      Tarjeta", ancho_caracteres))
            contenido.append("")
        # En ticket de CLIENTE no mostrar nada (no agregar líneas)
    else:
        contenido.append(f"Metodo de pago: {forma_pago}")
        contenido.append("")
        contenido.append("")
    
    # Estado de pago (solo en ticket de cocina)
    if tipo_ticket == 'COCINA' and pedido_info.get('estado_pago'):
        estado_pago = pedido_info['estado_pago']
        # Centrar el estado de pago
        texto_estado = "Pagado                      Pendiente de pago"
        contenido.append(formatear_texto_centrado(texto_estado, ancho_caracteres))
    
    # Separador final
    contenido.append("=" * ancho_caracteres)
    
    if tipo_ticket == 'CLIENTE':
        enlace = obtener_enlace_qr()
        if enlace:
            contenido.append("")
            contenido.append(formatear_texto_centrado("Seguinos en Instagram", ancho_caracteres))
            contenido.append(formatear_texto_centrado(enlace, ancho_caracteres))
        contenido.append("")
        contenido.append("")
        contenido.append("")
    
    # Guardar en archivo
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        f.write('\n'.join(contenido))
    
    return ruta_archivo


def generar_tickets_pedido(pedido_info, imprimir_automatico=True, guardar_respaldo=True):
    """
    Genera ambos tickets (COCINA y CLIENTE) para un pedido e imprime directamente
    
    Args:
        pedido_info: Diccionario con la información del pedido
        imprimir_automatico: Si es True, imprime automáticamente los tickets
        guardar_respaldo: Si es True, guarda archivos .txt de respaldo
    
    Returns:
        dict: Diccionario con las rutas de los archivos generados (si aplica) y estado de impresión
    """
    resultado = {
        'cocina': None,
        'cliente': None,
        'impresion_cocina': False,
        'impresion_cliente': False
    }
    
    # Guardar respaldo en archivos de texto si está habilitado
    if guardar_respaldo:
        try:
            resultado['cocina'] = guardar_ticket_texto(pedido_info, 'COCINA')
            resultado['cliente'] = guardar_ticket_texto(pedido_info, 'CLIENTE')
        except Exception as e:
            print(f"Error al guardar tickets de respaldo: {e}")
    
    # Imprimir automáticamente si está habilitado
    if imprimir_automatico:
        resultado['impresion_cocina'] = imprimir_ticket_escpos(pedido_info, 'COCINA')
        # Pequeña pausa entre impresiones
        import time
        time.sleep(0.5)
        resultado['impresion_cliente'] = imprimir_ticket_escpos(pedido_info, 'CLIENTE')
    
    return resultado


def imprimir_ticket_prueba(nombre_impresora=None):
    """
    Imprime un ticket de prueba simple.
    Si se pasa nombre_impresora, usa esa; si no, la configurada.
    """
    if not ESCPOS_AVAILABLE:
        print("Error: python-escpos no está disponible")
        return False
    
    if sys.platform != 'win32':
        print("Error: Win32Raw solo está disponible en Windows")
        return False
    
    printer = None
    try:
        if nombre_impresora:
            if not verificar_impresora_existe(nombre_impresora):
                print(f"Error: La impresora '{nombre_impresora}' no se encuentra en el sistema")
                return False
            printer = Win32Raw(nombre_impresora)
            nombre_mostrar = nombre_impresora
        else:
            printer = obtener_impresora()
            if not printer:
                return False
            config = cargar_configuracion()
            nombre_mostrar = config.get('impresora', {}).get('nombre_impresora', '')
        
        printer.set(align='center', font='a', width=1, height=1, bold=True)
        printer.text("TICKET DE PRUEBA\n")
        printer.text("PAPUCHO FOODTRUCK\n")
        printer.set(align='center', bold=False)
        printer.text("Impresora termica 80mm\n")
        if nombre_mostrar:
            printer.text(f"{nombre_mostrar}\n")
        printer.text("\n\n")
        printer.cut()
        
        printer.close()
        print("Ticket de prueba impreso exitosamente")
        return True
        
    except Error as e:
        print(f"Error ESC/POS al imprimir ticket de prueba: {e}")
        if printer:
            try:
                printer.close()
            except:
                pass
        return False
    except Exception as e:
        print(f"Error inesperado al imprimir ticket de prueba: {e}")
        if printer:
            try:
                printer.close()
            except:
                pass
        return False
