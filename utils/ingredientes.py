"""
Módulo para gestión de ingredientes en el archivo JSON
Maneja operaciones CRUD de ingredientes y su asignación a categorías
"""
import json
import os


def obtener_ruta_json():
    """Obtiene la ruta del archivo JSON de ingredientes"""
    from utils.rutas import obtener_ruta_json as obtener_ruta_json_helper
    return obtener_ruta_json_helper('ingredientes.json')


def cargar_ingredientes():
    """Carga los ingredientes desde el archivo JSON"""
    ruta = obtener_ruta_json()
    
    # La migración desde instalación antigua se hace en obtener_ruta_json()
    # Aquí solo cargamos el archivo (ya está en AppData o se migró automáticamente)
    
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        # Crear estructura inicial
        data = {"ingredientes": []}
        guardar_ingredientes(data)
        return data
    except json.JSONDecodeError:
        print("Error: El archivo ingredientes.json no es válido. Se creará uno nuevo.")
        data = {"ingredientes": []}
        guardar_ingredientes(data)
        return data


def guardar_ingredientes(data):
    """Guarda los ingredientes en el archivo JSON"""
    ruta = obtener_ruta_json()
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    # Escribir con flush explícito para asegurar que se guarde
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())  # Forzar escritura al disco


def obtener_siguiente_id():
    """Obtiene el siguiente ID disponible para un nuevo ingrediente"""
    data = cargar_ingredientes()
    max_id = 0
    
    for ingrediente in data.get("ingredientes", []):
        if ingrediente.get("id", 0) > max_id:
            max_id = ingrediente.get("id", 0)
    
    return max_id + 1


def obtener_todos_los_ingredientes():
    """Obtiene todos los ingredientes"""
    data = cargar_ingredientes()
    return data.get("ingredientes", [])


def buscar_ingrediente_por_id(ingrediente_id):
    """Busca un ingrediente por su ID"""
    data = cargar_ingredientes()
    
    for ingrediente in data.get("ingredientes", []):
        if ingrediente.get("id") == ingrediente_id:
            return ingrediente
    
    return None


def buscar_ingrediente_por_nombre(nombre):
    """Busca un ingrediente por su nombre"""
    data = cargar_ingredientes()
    
    for ingrediente in data.get("ingredientes", []):
        if ingrediente.get("nombre") == nombre:
            return ingrediente
    
    return None


def agregar_ingrediente(nombre, categorias, precio_extra, precio_resta, imagen=None):
    """Agrega un nuevo ingrediente"""
    data = cargar_ingredientes()
    
    nuevo_ingrediente = {
        "id": obtener_siguiente_id(),
        "nombre": nombre,
        "categorias": categorias if isinstance(categorias, list) else [categorias],
        "precio_extra": float(precio_extra),
        "precio_resta": float(precio_resta)
    }
    
    # Agregar imagen si se proporciona
    if imagen:
        nuevo_ingrediente["imagen"] = imagen
    
    data.setdefault("ingredientes", []).append(nuevo_ingrediente)
    guardar_ingredientes(data)
    return nuevo_ingrediente


def modificar_ingrediente(ingrediente_id, nombre, categorias, precio_extra, precio_resta, imagen=None):
    """Modifica un ingrediente existente y actualiza el nombre en todos los productos que lo usan"""
    data = cargar_ingredientes()
    
    # Buscar el ingrediente para obtener el nombre anterior
    ingrediente_anterior = None
    nombre_anterior = None
    for ingrediente in data.get("ingredientes", []):
        if ingrediente.get("id") == ingrediente_id:
            ingrediente_anterior = ingrediente
            nombre_anterior = ingrediente.get("nombre", "")
            ingrediente["nombre"] = nombre
            ingrediente["categorias"] = categorias if isinstance(categorias, list) else [categorias]
            ingrediente["precio_extra"] = float(precio_extra)
            ingrediente["precio_resta"] = float(precio_resta)
            
            # Actualizar imagen si se proporciona (None significa no cambiar, "" significa eliminar)
            if imagen is not None:
                if imagen:
                    ingrediente["imagen"] = imagen
                else:
                    ingrediente.pop("imagen", None)
            
            guardar_ingredientes(data)
            break
    
    if not ingrediente_anterior:
        return False
    
    # Si el nombre cambió, actualizar el nombre en todos los productos que lo usan
    if nombre_anterior and nombre_anterior != nombre:
        from utils.productos import cargar_productos, guardar_productos
        productos_data = cargar_productos()
        productos_modificados = False
        
        for categoria in productos_data.get("categorias", []):
            for producto in categoria.get("productos", []):
                ingredientes = producto.get("ingredientes", [])
                if ingredientes:
                    for ing in ingredientes:
                        if ing.get("nombre") == nombre_anterior:
                            ing["nombre"] = nombre
                            productos_modificados = True
        
        if productos_modificados:
            guardar_productos(productos_data)
    
    return True


def eliminar_ingrediente(ingrediente_id):
    """Elimina un ingrediente por su ID y también lo elimina de todos los productos que lo usan"""
    data = cargar_ingredientes()
    
    # Buscar el ingrediente para obtener su nombre
    ingrediente_a_eliminar = None
    for idx, ingrediente in enumerate(data.get("ingredientes", [])):
        if ingrediente.get("id") == ingrediente_id:
            ingrediente_a_eliminar = ingrediente
            data["ingredientes"].pop(idx)
            guardar_ingredientes(data)
            break
    
    if not ingrediente_a_eliminar:
        return False
    
    # Eliminar el ingrediente de todos los productos que lo usan
    nombre_ingrediente = ingrediente_a_eliminar.get("nombre")
    if nombre_ingrediente:
        from utils.productos import cargar_productos, guardar_productos
        productos_data = cargar_productos()
        productos_modificados = False
        
        for categoria in productos_data.get("categorias", []):
            for producto in categoria.get("productos", []):
                ingredientes = producto.get("ingredientes", [])
                if ingredientes:
                    # Filtrar ingredientes que coincidan con el nombre
                    ingredientes_originales = len(ingredientes)
                    producto["ingredientes"] = [
                        ing for ing in ingredientes 
                        if ing.get("nombre") != nombre_ingrediente
                    ]
                    if len(producto["ingredientes"]) < ingredientes_originales:
                        productos_modificados = True
        
        if productos_modificados:
            guardar_productos(productos_data)
    
    return True


def obtener_ingredientes_por_categoria(categoria_nombre):
    """Obtiene todos los ingredientes disponibles para una categoría"""
    data = cargar_ingredientes()
    ingredientes = []
    
    for ingrediente in data.get("ingredientes", []):
        categorias = ingrediente.get("categorias", [])
        if categoria_nombre in categorias:
            ingredientes.append(ingrediente)
    
    return ingredientes
