"""
Módulo para asegurar que solo se ejecute una instancia de la aplicación
Usa un mutex de Windows para prevenir múltiples instancias
Si hay otra instancia, trae su ventana al frente en lugar de abrir una nueva
"""
import sys
import os

# Variable global para mantener el mutex durante toda la ejecución
_mutex_handle = None

# Variable global para mantener el archivo de bloqueo abierto
_lock_file_handle = None

# Título de la ventana principal (debe coincidir con el título en main.py)
TITULO_VENTANA = "PAPUCHO FOODTRUCK - Sistema de Caja"


def verificar_instancia_unica():
    """
    Verifica si ya hay una instancia de la aplicación ejecutándose
    Usa un mutex de Windows para prevenir múltiples instancias
    
    El mutex es un mecanismo de sincronización de Windows que permite
    que solo un proceso tenga acceso a un recurso compartido a la vez.
    Si el mutex ya existe, significa que otra instancia está ejecutándose.
    
    Returns:
        bool: True si es la primera instancia, False si ya hay una ejecutándose
    """
    global _mutex_handle
    
    # PRIMERO: Intentar método de archivo (más rápido y confiable)
    # Esto previene el problema de race condition al inicio
    resultado_archivo = verificar_instancia_unica_archivo()
    if not resultado_archivo:
        # Ya hay una instancia según el método de archivo
        return False
    
    # SEGUNDO: Si el método de archivo pasó, verificar con mutex de Windows
    try:
        # Intentar importar win32event (solo disponible en Windows)
        import win32event
        import win32api
        import winerror
        
        # Crear un mutex con un nombre único para la aplicación
        # Usar "Global\" para que funcione entre sesiones de usuario
        mutex_nombre = "Global\\PapuchoFoodtruck_SingleInstance_Mutex_v3"
        
        # Intentar crear el mutex (True = el proceso actual es el dueño inicial)
        _mutex_handle = win32event.CreateMutex(None, True, mutex_nombre)
        
        # IMPORTANTE: GetLastError debe llamarse inmediatamente después de CreateMutex
        # para obtener el código de error correcto
        ultimo_error = win32api.GetLastError()
        
        if ultimo_error == winerror.ERROR_ALREADY_EXISTS:
            # Ya existe una instancia ejecutándose
            # El mutex fue creado por otro proceso
            # Cerrar el handle que acabamos de crear (no es nuestro mutex)
            if _mutex_handle:
                try:
                    win32api.CloseHandle(_mutex_handle)
                    _mutex_handle = None
                except:
                    pass
            return False
        else:
            # Es la primera instancia
            # El mutex fue creado exitosamente por este proceso
            # Mantener el mutex abierto durante toda la ejecución
            # NO cerrar el mutex hasta que la aplicación termine
            return True
            
    except ImportError:
        # Si no está disponible win32event, confiar en el método de archivo
        # que ya verificamos arriba
        return resultado_archivo
    except Exception as e:
        # Si hay algún error con el mutex, confiar en el método de archivo
        print(f"Error al verificar instancia única (mutex): {e}")
        return resultado_archivo


def verificar_instancia_unica_archivo():
    """
    Método alternativo usando archivo de bloqueo (fallback)
    Se usa si win32event no está disponible
    Usa un archivo bloqueado para prevenir acceso simultáneo
    
    Returns:
        bool: True si es la primera instancia, False si ya hay una ejecutándose
    """
    global _lock_file_handle
    
    try:
        from utils.rutas import obtener_ruta_appdata
        
        # Ruta del archivo de bloqueo
        ruta_lock = os.path.join(obtener_ruta_appdata(), '.app_lock')
        
        # Limpiar archivo de lock huérfano (si el proceso anterior murió)
        if os.path.exists(ruta_lock):
            try:
                # Intentar leer el PID del archivo
                with open(ruta_lock, 'r') as f:
                    pid_str = f.read().strip()
                    if pid_str:
                        pid_anterior = int(pid_str)
                        # Verificar si el proceso todavía está ejecutándose
                        if not verificar_proceso_activo(pid_anterior):
                            # El proceso murió, eliminar el archivo de lock
                            try:
                                os.remove(ruta_lock)
                            except:
                                pass
            except (ValueError, IOError, OSError):
                # Si no se puede leer o el PID es inválido, eliminar el archivo
                try:
                    os.remove(ruta_lock)
                except:
                    pass
        
        # Intentar crear/abrir el archivo en modo exclusivo
        try:
            # En Windows, usar msvcrt para bloqueo exclusivo
            if sys.platform == 'win32':
                import msvcrt
                # Intentar abrir el archivo en modo exclusivo
                try:
                    # Abrir en modo 'w+' para lectura y escritura
                    lock_file = open(ruta_lock, 'w+')
                    # Intentar bloquear el archivo (LK_NBLCK = bloqueo no bloqueante)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    
                    # Escribir el PID actual
                    lock_file.seek(0)
                    lock_file.write(str(os.getpid()))
                    lock_file.truncate()
                    lock_file.flush()
                    
                    # Guardar referencia global para mantener el archivo abierto
                    _lock_file_handle = lock_file
                    
                    # NO cerrar el archivo - mantenerlo abierto durante toda la ejecución
                    # Se cerrará cuando la aplicación termine
                    return True
                except (IOError, OSError, PermissionError):
                    # El archivo está bloqueado por otro proceso - hay otra instancia
                    try:
                        if 'lock_file' in locals():
                            lock_file.close()
                    except:
                        pass
                    return False
            else:
                # Para otros sistemas, usar método simple
                return verificar_instancia_unica_simple()
            
        except Exception as e:
            # Si falla, usar método simple
            print(f"Error al crear archivo de bloqueo: {e}")
            return verificar_instancia_unica_simple()
            
    except Exception as e:
        # Si hay error, usar método más simple
        print(f"Error al verificar instancia única (archivo): {e}")
        return verificar_instancia_unica_simple()


def verificar_instancia_unica_simple():
    """
    Método simple: verificar si hay otro proceso con el mismo nombre ejecutándose
    
    Returns:
        bool: True si es la primera instancia, False si ya hay una ejecutándose
    """
    try:
        import subprocess
        
        # Obtener el nombre del ejecutable actual
        if getattr(sys, 'frozen', False):
            nombre_proceso = os.path.basename(sys.executable)
        else:
            nombre_proceso = 'python.exe'
        
        # Contar cuántas instancias del proceso están ejecutándose
        if sys.platform == 'win32':
            resultado = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {nombre_proceso}'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Contar cuántas veces aparece el nombre del proceso en la salida
            # (excluyendo la línea de encabezado)
            lineas = resultado.stdout.split('\n')
            count = 0
            for linea in lineas:
                if nombre_proceso.lower() in linea.lower() and 'PID' not in linea:
                    count += 1
            
            # Si hay más de una instancia (contando la actual), hay otra ejecutándose
            return count <= 1
        else:
            # Para otros sistemas operativos
            return True
    except Exception:
        # Si falla, permitir ejecutar
        return True


def verificar_proceso_activo(pid):
    """
    Verifica si un proceso con el PID dado está activo
    
    Args:
        pid: ID del proceso a verificar
    
    Returns:
        bool: True si el proceso está activo, False en caso contrario
    """
    try:
        import psutil
        return psutil.pid_exists(pid)
    except ImportError:
        # Si psutil no está disponible, usar método alternativo en Windows
        try:
            import subprocess
            # En Windows, usar tasklist para verificar el proceso
            resultado = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            # Si el PID aparece en la salida, el proceso está activo
            return str(pid) in resultado.stdout
        except Exception:
            # Si falla, asumir que el proceso no está activo
            return False


def traer_ventana_al_frente(titulo_ventana):
    """
    Busca una ventana por su título y la trae al frente
    
    Args:
        titulo_ventana: Título de la ventana a buscar
    
    Returns:
        bool: True si se encontró y activó la ventana, False en caso contrario
    """
    try:
        import win32gui
        import win32con
        
        def enum_windows_callback(hwnd, windows):
            """Callback para enumerar ventanas"""
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if titulo_ventana in window_title or window_title == titulo_ventana:
                    windows.append((hwnd, window_title))
            return True
        
        # Enumerar todas las ventanas visibles
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        # Buscar la ventana con el título exacto o que contenga el título
        for hwnd, window_title in windows:
            if titulo_ventana in window_title:
                try:
                    # Restaurar la ventana si está minimizada
                    if win32gui.IsIconic(hwnd):
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    
                    # Traer la ventana al frente
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.BringWindowToTop(hwnd)
                    win32gui.SetActiveWindow(hwnd)
                    
                    # Flash la ventana para indicar que se activó
                    try:
                        win32gui.FlashWindow(hwnd, True)
                    except:
                        pass
                    
                    return True
                except Exception as e:
                    print(f"Error al traer ventana al frente: {e}")
                    continue
        
        return False
        
    except ImportError:
        # win32gui no está disponible
        return False
    except Exception as e:
        print(f"Error al buscar ventana: {e}")
        return False


def activar_instancia_existente():
    """
    Intenta activar la instancia existente de la aplicación
    Trae su ventana al frente
    Espera un poco para asegurar que la ventana esté completamente creada
    
    Returns:
        bool: True si se activó la ventana existente, False en caso contrario
    """
    import time
    
    # Intentar varias veces con pequeños delays
    # La ventana puede tardar un momento en aparecer
    # Esperar un poco más la primera vez para dar tiempo a que la ventana se cree
    time.sleep(0.5)
    
    for intento in range(10):  # Más intentos
        if traer_ventana_al_frente(TITULO_VENTANA):
            return True
        time.sleep(0.3)  # Esperar 300ms entre intentos
    
    return False


def limpiar_archivo_lock():
    """
    Limpia el archivo de bloqueo y cierra el mutex al cerrar la aplicación
    """
    global _mutex_handle, _lock_file_handle
    
    # Cerrar el mutex si está abierto
    if _mutex_handle:
        try:
            import win32api
            win32api.CloseHandle(_mutex_handle)
            _mutex_handle = None
        except:
            pass
    
    # Cerrar el archivo de bloqueo si está abierto
    if _lock_file_handle:
        try:
            _lock_file_handle.close()
            _lock_file_handle = None
        except:
            pass
    
    # Limpiar archivo de bloqueo (método alternativo)
    try:
        from utils.rutas import obtener_ruta_appdata
        ruta_lock = os.path.join(obtener_ruta_appdata(), '.app_lock')
        if os.path.exists(ruta_lock):
            try:
                # Intentar eliminar el archivo
                os.remove(ruta_lock)
            except (PermissionError, OSError):
                # Si está bloqueado, intentar desbloquearlo primero
                try:
                    if sys.platform == 'win32':
                        import msvcrt
                        # Abrir y desbloquear
                        with open(ruta_lock, 'r+') as f:
                            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                        os.remove(ruta_lock)
                except:
                    pass
    except Exception:
        pass
