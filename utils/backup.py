"""
Módulo para crear backups automáticos de los datos de la aplicación
Los backups se guardan en una carpeta específica con fecha y hora
"""
import os
import shutil
import sys
from datetime import datetime, timedelta


def obtener_ruta_backup():
    """
    Obtiene la ruta base donde se guardan los backups
    
    Returns:
        str: Ruta completa de la carpeta de backups
    """
    # Usar una carpeta fija en el escritorio o en Documentos
    # Opción 1: En Documentos (más discreto)
    documentos = os.path.join(os.path.expanduser('~'), 'Documents')
    ruta_backup = os.path.join(documentos, 'Papucho Foodtruck Backups')
    
    # Crear la carpeta si no existe
    os.makedirs(ruta_backup, exist_ok=True)
    return ruta_backup


def crear_backup():
    """
    Crea un backup completo de todos los datos de AppData
    El backup se guarda en una carpeta con fecha y hora
    
    Returns:
        str: Ruta del backup creado, o None si falló
    """
    try:
        # Obtener ruta de AppData
        from utils.rutas import obtener_ruta_appdata
        ruta_appdata = obtener_ruta_appdata()
        
        if not os.path.exists(ruta_appdata):
            # Si no existe AppData, no hay nada que respaldar
            return None
        
        # Crear nombre de carpeta con fecha y hora
        fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_backup = f"backup_{fecha_hora}"
        
        # Ruta completa del backup
        ruta_backup_base = obtener_ruta_backup()
        ruta_backup_completo = os.path.join(ruta_backup_base, nombre_backup)
        
        # Copiar toda la carpeta AppData al backup,
        # PERO sin incluir:
        #   - La carpeta de tickets (para no acumular archivos de impresión)
        #   - El archivo .app_lock (está bloqueado por el proceso actual)
        #
        # Estructura típica en AppData:
        #   imagenes/
        #   tickets/        <-- ESTA CARPETA NO SE RESPALDA
        #   .app_lock       <-- ESTE ARCHIVO NO SE RESPALDA (está bloqueado)
        #   config
        #   ingredientes
        #   orden_actual
        #   productos
        #
        # Función personalizada para ignorar tickets y .app_lock
        def ignore_func(dirname, filenames):
            ignored = []
            # Ignorar la carpeta tickets
            if 'tickets' in filenames:
                ignored.append('tickets')
            # Ignorar el archivo .app_lock
            if '.app_lock' in filenames:
                ignored.append('.app_lock')
            return ignored
        
        shutil.copytree(
            ruta_appdata,
            ruta_backup_completo,
            ignore=ignore_func
        )
        
        return ruta_backup_completo
    except Exception as e:
        print(f"Error al crear backup: {e}")
        return None


def limpiar_backups_antiguos(dias_a_mantener=30, max_backups=50):
    """
    Limpia backups antiguos, manteniendo solo los más recientes
    
    Args:
        dias_a_mantener: Número de días de backups a mantener (por defecto 30)
        max_backups: Número máximo de backups a mantener (por defecto 50)
    
    Returns:
        int: Número de backups eliminados
    """
    try:
        ruta_backup_base = obtener_ruta_backup()
        
        if not os.path.exists(ruta_backup_base):
            return 0
        
        # Obtener todos los backups
        backups = []
        for item in os.listdir(ruta_backup_base):
            ruta_item = os.path.join(ruta_backup_base, item)
            if os.path.isdir(ruta_item) and item.startswith('backup_'):
                try:
                    # Extraer fecha del nombre
                    fecha_str = item.replace('backup_', '')
                    fecha = datetime.strptime(fecha_str, "%Y-%m-%d_%H-%M-%S")
                    backups.append((fecha, ruta_item))
                except ValueError:
                    # Si no se puede parsear la fecha, ignorar
                    continue
        
        # Ordenar por fecha (más recientes primero)
        backups.sort(key=lambda x: x[0], reverse=True)
        
        eliminados = 0
        # Calcular fecha límite usando timedelta (más seguro que replace)
        fecha_limite = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=dias_a_mantener)
        
        # Eliminar backups antiguos
        # Usar enumerate para obtener el índice directamente
        for idx, (fecha, ruta_backup) in enumerate(backups):
            eliminar = False
            
            # Eliminar si es más antiguo que el límite de días
            if fecha < fecha_limite:
                eliminar = True
            
            # Eliminar si excede el máximo de backups (índice >= max_backups significa que es el backup 51, 52, etc.)
            if idx >= max_backups:
                eliminar = True
            
            if eliminar:
                try:
                    shutil.rmtree(ruta_backup)
                    eliminados += 1
                except Exception:
                    pass  # Ignorar errores al eliminar
        
        return eliminados
    except Exception as e:
        print(f"Error al limpiar backups antiguos: {e}")
        return 0


def crear_backup_automatico():
    """
    Crea un backup automático y limpia los antiguos
    Esta función se llama al cerrar la aplicación
    
    Returns:
        tuple: (ruta_backup, backups_eliminados) o (None, 0) si falló
    """
    ruta_backup = crear_backup()
    backups_eliminados = 0
    
    if ruta_backup:
        # Limpiar backups antiguos después de crear uno nuevo
        backups_eliminados = limpiar_backups_antiguos()
    
    return (ruta_backup, backups_eliminados)
