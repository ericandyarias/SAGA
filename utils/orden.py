"""
Módulo para manejar el número de orden persistente
"""
import os


def obtener_ruta_orden():
    """Obtiene la ruta del archivo de orden"""
    from utils.rutas import obtener_ruta_data
    return os.path.join(obtener_ruta_data(), 'orden_actual.txt')


def leer_numero_orden():
    """Lee el número de orden actual desde el archivo"""
    ruta = obtener_ruta_orden()
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read().strip()
            if contenido:
                return int(contenido)
            else:
                return 1
    except FileNotFoundError:
        # Si no existe el archivo, crearlo con el valor inicial
        guardar_numero_orden(1)
        return 1
    except ValueError:
        # Si el contenido no es un número válido, resetear a 1
        guardar_numero_orden(1)
        return 1


def guardar_numero_orden(numero):
    """Guarda el número de orden en el archivo"""
    ruta = obtener_ruta_orden()
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(str(numero))


def incrementar_orden():
    """Incrementa el número de orden y lo guarda"""
    numero_actual = leer_numero_orden()
    nuevo_numero = numero_actual + 1
    guardar_numero_orden(nuevo_numero)
    return nuevo_numero
