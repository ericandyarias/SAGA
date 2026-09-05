"""
Módulo para obtener rutas correctas de archivos
Funciona tanto en desarrollo como en ejecutable empaquetado
Usa AppData del usuario para archivos modificables cuando está instalado
"""
import os
import sys


def obtener_ruta_base():
    """
    Obtiene la ruta base de la aplicación.
    Funciona tanto en desarrollo como cuando está empaquetado con PyInstaller.
    
    Returns:
        str: Ruta base de la aplicación
    """
    # Si estamos ejecutando desde un ejecutable empaquetado (PyInstaller)
    if getattr(sys, 'frozen', False):
        # sys.executable apunta al .exe
        # La carpeta base es el directorio donde está el .exe
        return os.path.dirname(sys.executable)
    else:
        # En desarrollo, la carpeta base es el directorio raíz del proyecto
        # (dos niveles arriba desde utils/)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def obtener_ruta_appdata():
    """
    Obtiene la ruta de AppData del usuario para archivos modificables.
    Solo se usa cuando la aplicación está instalada (empaquetada).
    
    Returns:
        str: Ruta completa de AppData\\SAGA
    """
    appdata = os.getenv('APPDATA')
    if not appdata:
        # Fallback si APPDATA no está definido
        appdata = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming')
    
    ruta_appdata = os.path.join(appdata, 'SAGA')
    # Crear la carpeta si no existe
    os.makedirs(ruta_appdata, exist_ok=True)
    return ruta_appdata


def obtener_ruta_data():
    """
    Obtiene la ruta de la carpeta data.
    En desarrollo usa la carpeta del proyecto.
    Cuando está instalado, usa AppData para archivos modificables.
    
    Returns:
        str: Ruta completa de la carpeta data
    """
    # Si está empaquetado, usar AppData para archivos modificables
    if getattr(sys, 'frozen', False):
        return obtener_ruta_appdata()
    else:
        # En desarrollo, usar la carpeta del proyecto
        return os.path.join(obtener_ruta_base(), 'data')


CARPETA_CONFIG_INICIAL = "config_inicial_bdd"
ARCHIVOS_CONFIG_INICIAL = ("productos.json", "ingredientes.json", "config.json")


def obtener_ruta_config_inicial():
    """
    Carpeta con el catálogo y la config de fábrica.
    En desarrollo: data/config_inicial_bdd.
    Instalado: data/config_inicial_bdd junto al .exe (solo lectura).
    """
    return os.path.join(obtener_ruta_data_instalacion(), CARPETA_CONFIG_INICIAL)


def obtener_ruta_archivo_inicial(nombre_archivo):
    """
    Busca un JSON de arranque: primero la carpeta de fábrica, después
    ubicaciones viejas (data/ suelto) por si hay una instalación anterior.
    """
    candidatos = [
        os.path.join(obtener_ruta_config_inicial(), nombre_archivo),
        os.path.join(obtener_ruta_data(), CARPETA_CONFIG_INICIAL, nombre_archivo),
        os.path.join(obtener_ruta_data(), nombre_archivo),
        os.path.join(obtener_ruta_data_instalacion(), nombre_archivo),
    ]
    for ruta in candidatos:
        if os.path.exists(ruta):
            return ruta
    return candidatos[0]


def asegurar_config_de_trabajo():
    """
    En el .exe, copia la config de fábrica a AppData la primera vez.
    En desarrollo se usa directo data/config_inicial_bdd/config.json.
    """
    import shutil

    if not getattr(sys, "frozen", False):
        return os.path.join(obtener_ruta_config_inicial(), "config.json")

    destino = os.path.join(obtener_ruta_data(), "config.json")
    if os.path.exists(destino):
        return destino
    origen = obtener_ruta_archivo_inicial("config.json")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if os.path.exists(origen) and os.path.normcase(origen) != os.path.normcase(destino):
        try:
            shutil.copy2(origen, destino)
        except Exception:
            pass
    return destino


def obtener_ruta_data_instalacion():
    """
    Obtiene la ruta de la carpeta data en la instalación.
    DEPRECADO: Ya no se usa, todo está en AppData.
    Se mantiene solo para compatibilidad y migración de datos antiguos.
    
    Returns:
        str: Ruta completa de la carpeta data en la instalación
    """
    return os.path.join(obtener_ruta_base(), 'data')


def obtener_ruta_json(nombre_archivo):
    """
    JSON de trabajo (config, ventas) o de fábrica (productos, ingredientes).
    """
    if nombre_archivo in ("productos.json", "ingredientes.json"):
        return obtener_ruta_archivo_inicial(nombre_archivo)
    if nombre_archivo == "config.json":
        return asegurar_config_de_trabajo()

    ruta_data = obtener_ruta_data()
    ruta_json = os.path.join(ruta_data, nombre_archivo)

    if getattr(sys, "frozen", False):
        ruta_instalacion = obtener_ruta_data_instalacion()
        ruta_json_instalacion = os.path.join(ruta_instalacion, nombre_archivo)
        if not os.path.exists(ruta_json) and os.path.exists(ruta_json_instalacion):
            import shutil
            try:
                os.makedirs(os.path.dirname(ruta_json), exist_ok=True)
                shutil.copy2(ruta_json_instalacion, ruta_json)
            except Exception:
                pass

    return ruta_json


def migrar_datos_desde_instalacion():
    """
    Migra todos los datos desde la instalación antigua (Program Files) a AppData
    Solo se ejecuta una vez si detecta datos en Program Files que no están en AppData
    """
    if not getattr(sys, 'frozen', False):
        # Solo en modo instalado
        return
    
    try:
        ruta_appdata = obtener_ruta_appdata()
        ruta_instalacion = obtener_ruta_data_instalacion()
        
        # Si no existe la carpeta de instalación o está vacía, no hay nada que migrar
        if not os.path.exists(ruta_instalacion):
            return
        
        import shutil
        
        archivos_json = ["ventas.json", "saga.db"]
        for archivo in archivos_json:
            ruta_instalacion_archivo = os.path.join(ruta_instalacion, archivo)
            ruta_appdata_archivo = os.path.join(ruta_appdata, archivo)
            if os.path.exists(ruta_instalacion_archivo) and not os.path.exists(ruta_appdata_archivo):
                try:
                    os.makedirs(os.path.dirname(ruta_appdata_archivo), exist_ok=True)
                    shutil.copy2(ruta_instalacion_archivo, ruta_appdata_archivo)
                except Exception:
                    pass

        # Config de fábrica (catálogo + config.json)
        origen_inicial = os.path.join(ruta_instalacion, CARPETA_CONFIG_INICIAL)
        destino_inicial = os.path.join(ruta_appdata, CARPETA_CONFIG_INICIAL)
        if os.path.isdir(origen_inicial) and not os.path.exists(destino_inicial):
            try:
                shutil.copytree(origen_inicial, destino_inicial)
            except Exception:
                pass

        for archivo in ARCHIVOS_CONFIG_INICIAL:
            viejo = os.path.join(ruta_instalacion, archivo)
            if os.path.exists(viejo):
                try:
                    os.makedirs(destino_inicial, exist_ok=True)
                    destino_archivo = os.path.join(destino_inicial, archivo)
                    if not os.path.exists(destino_archivo):
                        shutil.copy2(viejo, destino_archivo)
                except Exception:
                    pass
        
        # Migrar carpeta de imágenes completa
        ruta_imagenes_instalacion = os.path.join(ruta_instalacion, 'imagenes')
        ruta_imagenes_appdata = os.path.join(ruta_appdata, 'imagenes')
        
        if os.path.exists(ruta_imagenes_instalacion) and not os.path.exists(ruta_imagenes_appdata):
            try:
                shutil.copytree(ruta_imagenes_instalacion, ruta_imagenes_appdata)
            except Exception:
                pass
        
        # Migrar carpeta de tickets (si existe)
        ruta_tickets_instalacion = os.path.join(ruta_instalacion, 'tickets')
        ruta_tickets_appdata = os.path.join(ruta_appdata, 'tickets')
        
        if os.path.exists(ruta_tickets_instalacion):
            try:
                if not os.path.exists(ruta_tickets_appdata):
                    shutil.copytree(ruta_tickets_instalacion, ruta_tickets_appdata)
                else:
                    # Si ya existe, copiar archivos individuales
                    for archivo in os.listdir(ruta_tickets_instalacion):
                        ruta_origen = os.path.join(ruta_tickets_instalacion, archivo)
                        ruta_destino = os.path.join(ruta_tickets_appdata, archivo)
                        if os.path.isfile(ruta_origen) and not os.path.exists(ruta_destino):
                            shutil.copy2(ruta_origen, ruta_destino)
            except Exception:
                pass
        
        # Migrar orden_actual.txt
        ruta_orden_instalacion = os.path.join(ruta_instalacion, 'orden_actual.txt')
        ruta_orden_appdata = os.path.join(ruta_appdata, 'orden_actual.txt')
        
        if os.path.exists(ruta_orden_instalacion) and not os.path.exists(ruta_orden_appdata):
            try:
                os.makedirs(os.path.dirname(ruta_orden_appdata), exist_ok=True)
                shutil.copy2(ruta_orden_instalacion, ruta_orden_appdata)
            except Exception:
                pass
    except Exception as e:
        # No bloquear el inicio si falla la migración
        print(f"Error al migrar datos desde instalación: {e}")
