"""
Script auxiliar para detectar y configurar la impresora por nombre
Lista todas las impresoras disponibles en Windows y permite seleccionar una
"""
import sys
import json
import os

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def obtener_ruta_config():
    """Obtiene la ruta del archivo de configuración"""
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'config.json'
    )

def listar_impresoras():
    """Lista todas las impresoras disponibles en Windows"""
    print("Buscando impresoras en Windows...\n")
    
    if sys.platform != 'win32':
        print("[ERROR] Este script solo funciona en Windows")
        return []
    
    try:
        import win32print
        impresoras = []
        impresoras_raw = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        for impresora in impresoras_raw:
            impresoras.append(impresora[2])  # El nombre está en el índice 2
        return impresoras
    except ImportError:
        print("[ERROR] pywin32 no esta instalado")
        print("Ejecuta: pip install pywin32")
        return []
    except Exception as e:
        print(f"[ERROR] Error al listar impresoras: {e}")
        return []

def detectar_impresoras():
    """Detecta todas las impresoras disponibles y configura la primera encontrada"""
    print("="*60)
    print("DETECCION DE IMPRESORAS (Win32Raw)")
    print("="*60)
    print()
    
    impresoras = listar_impresoras()
    
    if not impresoras:
        print("[ERROR] No se encontraron impresoras en el sistema")
        print("\nSugerencias:")
        print("1. Verifica que la impresora este conectada y encendida")
        print("2. Verifica que los drivers esten instalados")
        print("3. Abre Configuracion > Dispositivos > Impresoras y escaners")
        print("   y verifica que la impresora aparezca alli")
        return
    
    print(f"Se encontraron {len(impresoras)} impresora(s):\n")
    for i, nombre in enumerate(impresoras, 1):
        print(f"{i}. {nombre}")
    
    # Cargar configuración actual
    ruta_config = obtener_ruta_config()
    nombre_actual = None
    try:
        with open(ruta_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
            nombre_actual = config.get('impresora', {}).get('nombre_impresora')
    except:
        pass
    
    if nombre_actual:
        print(f"\nImpresora actualmente configurada: {nombre_actual}")
        if nombre_actual in impresoras:
            print("[OK] La impresora configurada esta disponible")
        else:
            print("[ADVERTENCIA] La impresora configurada no esta disponible")
    
    # Buscar impresoras que contengan "XP" o "Xprinter" o "80"
    impresoras_recomendadas = []
    for nombre in impresoras:
        nombre_lower = nombre.lower()
        if 'xp' in nombre_lower or 'xprinter' in nombre_lower or '80' in nombre_lower or 'ticket' in nombre_lower:
            impresoras_recomendadas.append(nombre)
    
    if impresoras_recomendadas:
        print(f"\nImpresoras recomendadas (contienen XP/Xprinter/80/Ticket):")
        for nombre in impresoras_recomendadas:
            print(f"  - {nombre}")
        impresora_seleccionada = impresoras_recomendadas[0]
    else:
        # Si no hay recomendadas, usar la primera
        impresora_seleccionada = impresoras[0]
    
    print(f"\n" + "="*60)
    print(f"Guardando automaticamente: {impresora_seleccionada}")
    print("="*60)
    
    # Guardar configuración
    config = {
        "impresora": {
            "ancho_ticket": 80,
            "modelo": "Xprinter EX-E200M",
            "nombre_impresora": impresora_seleccionada
        },
        "tickets": {
            "incluir_fecha_hora": True,
            "lineas_corte": 3
        }
    }
    
    os.makedirs(os.path.dirname(ruta_config), exist_ok=True)
    with open(ruta_config, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Configuracion guardada en: {ruta_config}")
    print(f"  Impresora: {impresora_seleccionada}")
    print("\n[OK] La impresora esta configurada y lista para usar!")
    print("\nPara probar, ejecuta: python utils/probar_impresora.py")

if __name__ == "__main__":
    try:
        detectar_impresoras()
    except KeyboardInterrupt:
        print("\n\nDeteccion cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
