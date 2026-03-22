"""
Módulo para gestión de productos en el archivo JSON
Maneja operaciones CRUD y asegura que las categorías fijas existan
"""
import json
import os


# Categorías fijas del sistema
CATEGORIAS_FIJAS = [
    "Hamburguesas",
    "Lomitos",
    "Milanesas",
    "Panchos",
    "Fritas",
    "Empanadas",
    "Bebidas"
]


def obtener_ruta_json():
    """Obtiene la ruta del archivo JSON de productos"""
    from utils.rutas import obtener_ruta_json as obtener_ruta_json_helper
    return obtener_ruta_json_helper('productos.json')


def cargar_productos():
    """Carga los productos desde el archivo JSON"""
    ruta = obtener_ruta_json()
    
    # La migración desde instalación antigua se hace en obtener_ruta_json()
    # Aquí solo cargamos el archivo (ya está en AppData o se migró automáticamente)
    
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Asegurar que todas las categorías fijas existan
            asegurar_categorias_fijas(data)
            guardar_productos(data)
            return data
    except FileNotFoundError:
        # Crear estructura inicial con categorías fijas
        data = {"categorias": []}
        asegurar_categorias_fijas(data)
        guardar_productos(data)
        return data
    except json.JSONDecodeError:
        print("Error: El archivo productos.json no es válido. Se creará uno nuevo.")
        data = {"categorias": []}
        asegurar_categorias_fijas(data)
        guardar_productos(data)
        return data


def guardar_productos(data):
    """Guarda los productos en el archivo JSON"""
    ruta = obtener_ruta_json()
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    # Escribir con flush explícito para asegurar que se guarde
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())  # Forzar escritura al disco


def asegurar_categorias_fijas(data):
    """Asegura que todas las categorías fijas existan en los datos"""
    categorias_existentes = {cat["nombre"] for cat in data.get("categorias", [])}
    
    for categoria_nombre in CATEGORIAS_FIJAS:
        if categoria_nombre not in categorias_existentes:
            data.setdefault("categorias", []).append({
                "nombre": categoria_nombre,
                "productos": []
            })


def obtener_siguiente_id():
    """Obtiene el siguiente ID disponible para un nuevo producto"""
    data = cargar_productos()
    max_id = 0
    
    for categoria in data.get("categorias", []):
        for producto in categoria.get("productos", []):
            if producto.get("id", 0) > max_id:
                max_id = producto.get("id", 0)
    
    return max_id + 1


def obtener_todos_los_productos():
    """Obtiene todos los productos de todas las categorías"""
    data = cargar_productos()
    productos = []
    
    for categoria in data.get("categorias", []):
        for producto in categoria.get("productos", []):
            productos.append({
                **producto,
                "categoria": categoria["nombre"]
            })
    
    return productos


def buscar_producto_por_id(producto_id):
    """Busca un producto por su ID y retorna el producto con su categoría"""
    data = cargar_productos()
    
    for categoria in data.get("categorias", []):
        for producto in categoria.get("productos", []):
            if producto.get("id") == producto_id:
                return {
                    "producto": producto,
                    "categoria": categoria["nombre"]
                }
    
    return None


def agregar_producto(categoria_nombre, nombre, precio, descripcion, imagen=None):
    """Agrega un nuevo producto a una categoría"""
    data = cargar_productos()
    
    # Buscar la categoría
    categoria = None
    for cat in data.get("categorias", []):
        if cat["nombre"] == categoria_nombre:
            categoria = cat
            break
    
    if not categoria:
        # Si no existe, crearla (aunque debería existir por ser fija)
        categoria = {"nombre": categoria_nombre, "productos": []}
        data.setdefault("categorias", []).append(categoria)
    
    # Crear nuevo producto
    nuevo_producto = {
        "id": obtener_siguiente_id(),
        "nombre": nombre,
        "precio": float(precio),
        "descripcion": descripcion
    }
    
    # Agregar imagen si se proporciona
    if imagen:
        nuevo_producto["imagen"] = imagen
    
    categoria.setdefault("productos", []).append(nuevo_producto)
    guardar_productos(data)
    return nuevo_producto


def modificar_producto(producto_id, categoria_nombre, nombre, precio, descripcion, imagen=None):
    """Modifica un producto existente"""
    data = cargar_productos()
    
    # Buscar y eliminar el producto de su categoría actual
    producto_encontrado = None
    categoria_original = None
    
    for categoria in data.get("categorias", []):
        for idx, producto in enumerate(categoria.get("productos", [])):
            if producto.get("id") == producto_id:
                producto_encontrado = categoria["productos"].pop(idx)
                categoria_original = categoria["nombre"]
                break
        if producto_encontrado:
            break
    
    if not producto_encontrado:
        return False
    
    # Actualizar datos del producto
    producto_encontrado["nombre"] = nombre
    producto_encontrado["precio"] = float(precio)
    producto_encontrado["descripcion"] = descripcion
    
    # Actualizar imagen si se proporciona (None significa no cambiar, "" significa eliminar)
    if imagen is not None:
        if imagen:
            producto_encontrado["imagen"] = imagen
        else:
            producto_encontrado.pop("imagen", None)
    
    # Si cambió de categoría, agregarlo a la nueva
    if categoria_original != categoria_nombre:
        # Buscar la nueva categoría
        nueva_categoria = None
        for cat in data.get("categorias", []):
            if cat["nombre"] == categoria_nombre:
                nueva_categoria = cat
                break
        
        if nueva_categoria:
            nueva_categoria.setdefault("productos", []).append(producto_encontrado)
        else:
            # Si no existe, crearla
            nueva_categoria = {"nombre": categoria_nombre, "productos": [producto_encontrado]}
            data.setdefault("categorias", []).append(nueva_categoria)
    else:
        # Si no cambió de categoría, volver a agregarlo
        categoria_original_obj = None
        for cat in data.get("categorias", []):
            if cat["nombre"] == categoria_original:
                categoria_original_obj = cat
                break
        if categoria_original_obj:
            categoria_original_obj.setdefault("productos", []).append(producto_encontrado)
    
    guardar_productos(data)
    return True


def eliminar_producto(producto_id):
    """Elimina un producto por su ID"""
    data = cargar_productos()
    
    for categoria in data.get("categorias", []):
        for idx, producto in enumerate(categoria.get("productos", [])):
            if producto.get("id") == producto_id:
                categoria["productos"].pop(idx)
                guardar_productos(data)
                return True
    
    return False


def obtener_ingredientes_producto(producto_id):
    """Obtiene los ingredientes de un producto. Retorna lista vacía si no tiene ingredientes"""
    resultado = buscar_producto_por_id(producto_id)
    if resultado:
        producto = resultado['producto']
        # Compatibilidad hacia atrás: si no tiene ingredientes, retornar lista vacía
        return producto.get("ingredientes", [])
    return []


def agregar_ingrediente_a_producto(producto_id, ingrediente_data):
    """
    Agrega un ingrediente a un producto
    ingrediente_data debe tener: nombre, cantidad_base
    NOTA: Los precios (precio_extra, precio_resta) se obtienen dinámicamente desde ingredientes.json
    """
    data = cargar_productos()
    
    for categoria in data.get("categorias", []):
        for producto in categoria.get("productos", []):
            if producto.get("id") == producto_id:
                if "ingredientes" not in producto:
                    producto["ingredientes"] = []
                
                # Solo guardar nombre y cantidad_base (sistema de referencias)
                ingrediente_referencia = {
                    "nombre": ingrediente_data.get("nombre", ""),
                    "cantidad_base": ingrediente_data.get("cantidad_base", 1)
                }
                
                producto["ingredientes"].append(ingrediente_referencia)
                guardar_productos(data)
                return True
    
    return False


def modificar_ingrediente_producto(producto_id, indice_ingrediente, ingrediente_data):
    """Modifica un ingrediente específico de un producto"""
    data = cargar_productos()
    
    for categoria in data.get("categorias", []):
        for producto in categoria.get("productos", []):
            if producto.get("id") == producto_id:
                ingredientes = producto.get("ingredientes", [])
                if 0 <= indice_ingrediente < len(ingredientes):
                    # Solo guardar nombre y cantidad_base (sistema de referencias)
                    ingrediente_referencia = {
                        "nombre": ingrediente_data.get("nombre", ""),
                        "cantidad_base": ingrediente_data.get("cantidad_base", 1)
                    }
                    ingredientes[indice_ingrediente] = ingrediente_referencia
                    guardar_productos(data)
                    return True
    
    return False


def eliminar_ingrediente_producto(producto_id, indice_ingrediente):
    """Elimina un ingrediente específico de un producto"""
    data = cargar_productos()
    
    for categoria in data.get("categorias", []):
        for producto in categoria.get("productos", []):
            if producto.get("id") == producto_id:
                ingredientes = producto.get("ingredientes", [])
                if 0 <= indice_ingrediente < len(ingredientes):
                    ingredientes.pop(indice_ingrediente)
                    guardar_productos(data)
                    return True
    
    return False


def calcular_precio_con_ingredientes(producto, modificaciones_ingredientes=None):
    """
    Calcula el precio final de un producto considerando modificaciones de ingredientes
    Los precios de los ingredientes se obtienen dinámicamente desde ingredientes.json
    
    Args:
        producto: Diccionario del producto con precio base y opcionalmente ingredientes
        modificaciones_ingredientes: Dict con {nombre_ingrediente: cantidad_modificada}
                                    donde cantidad_modificada puede ser positiva (extra) o negativa (quitar)
    
    Returns:
        float: Precio final calculado
    """
    precio_base = producto.get("precio", 0.0)
    ingredientes = producto.get("ingredientes", [])
    
    # Si no hay modificaciones, retornar precio base
    if not modificaciones_ingredientes:
        return precio_base
    
    ajuste_total = 0.0
    
    # Importar aquí para evitar importación circular
    from utils.ingredientes import buscar_ingrediente_por_nombre
    
    # Crear diccionario de ingredientes del producto por nombre
    ingredientes_producto_dict = {ing.get("nombre", ""): ing for ing in ingredientes}
    
    # Procesar ingredientes del producto
    for ingrediente in ingredientes:
        nombre = ingrediente.get("nombre", "")
        cantidad_base = ingrediente.get("cantidad_base", 1)
        
        # Buscar el ingrediente actualizado desde ingredientes.json para obtener precios
        ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre)
        if not ingrediente_actualizado:
            # Si el ingrediente no existe, usar valores por defecto (0.0)
            precio_extra = 0.0
            precio_resta = 0.0
        else:
            precio_extra = ingrediente_actualizado.get("precio_extra", 0.0)
            precio_resta = ingrediente_actualizado.get("precio_resta", 0.0)
        
        # Obtener cantidad modificada (usar cantidad_base si no se modificó)
        cantidad_modificada = modificaciones_ingredientes.get(nombre, cantidad_base)
        
        if cantidad_modificada > cantidad_base:
            # Se agregaron extras
            extras = cantidad_modificada - cantidad_base
            ajuste_total += extras * precio_extra
        elif cantidad_modificada < cantidad_base:
            # Se quitaron unidades
            quitados = cantidad_base - cantidad_modificada
            ajuste_total -= quitados * precio_resta
        # Si cantidad_modificada == cantidad_base, no hay ajuste (ya está incluido en el precio base)
    
    # Procesar ingredientes adicionales que no están en el producto
    for nombre, cantidad_adicional in modificaciones_ingredientes.items():
        if nombre not in ingredientes_producto_dict and cantidad_adicional > 0:
            # Este es un ingrediente adicional que no está en el producto
            ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre)
            if ingrediente_actualizado:
                precio_extra = ingrediente_actualizado.get("precio_extra", 0.0)
                # Los ingredientes adicionales se cobran como extras
                ajuste_total += cantidad_adicional * precio_extra
    
    return precio_base + ajuste_total