"""
Script de prueba para verificar la conexión con la impresora
Ejecuta este script para diagnosticar problemas de impresión
Usa Win32Raw para imprimir por nombre de impresora en Windows
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

def probar_impresora():
    """Prueba la conexión y impresión con la impresora configurada"""
    print("="*60)
    print("PRUEBA DE IMPRESORA (Win32Raw)")
    print("="*60)
    print()
    
    if sys.platform != 'win32':
        print("[ERROR] Este script solo funciona en Windows")
        return False
    
    # Cargar configuración
    try:
        ruta_config = obtener_ruta_config()
        with open(ruta_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        nombre_impresora = config.get('impresora', {}).get('nombre_impresora', 'XP-80C')
        
        if not nombre_impresora:
            print("[ERROR] No hay nombre de impresora configurado")
            print("Configura 'nombre_impresora' en data/config.json")
            return False
        
        print(f"Configuracion encontrada:")
        print(f"  Nombre de impresora: {nombre_impresora}")
        print()
        
    except FileNotFoundError:
        print("[ERROR] Archivo de configuracion no encontrado")
        print("Se creara uno con valores por defecto")
        # El módulo tickets.py creará la configuración automáticamente
        nombre_impresora = "XP-80C"
    except Exception as e:
        print(f"[ERROR] Error al cargar configuracion: {e}")
        return False
    
    # Verificar que python-escpos esté instalado
    try:
        from escpos.printer import Win32Raw
        from escpos.exceptions import Error
    except ImportError:
        print("[ERROR] python-escpos no esta instalado")
        print("Ejecuta: pip install python-escpos")
        return False
    
    # Verificar que la impresora existe
    try:
        import win32print
        impresoras = []
        impresoras_raw = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        for impresora in impresoras_raw:
            impresoras.append(impresora[2])
        
        print("Impresoras disponibles en el sistema:")
        if impresoras:
            for imp in impresoras:
                marcador = " <-- CONFIGURADA" if imp == nombre_impresora else ""
                print(f"  - {imp}{marcador}")
        else:
            print("  (No se encontraron impresoras)")
        
        if nombre_impresora not in impresoras:
            print()
            print(f"[ERROR] La impresora '{nombre_impresora}' no se encuentra en el sistema")
            print("Actualiza 'nombre_impresora' en data/config.json con el nombre correcto")
            return False
        
        print()
        print(f"[OK] La impresora '{nombre_impresora}' esta disponible")
        
    except ImportError:
        print("[ADVERTENCIA] pywin32 no esta instalado")
        print("Ejecuta: pip install pywin32")
        print("Continuando sin verificar existencia de impresora...")
    except Exception as e:
        print(f"[ADVERTENCIA] Error al verificar impresoras: {e}")
        print("Continuando sin verificar existencia de impresora...")
    
    # Intentar conectar con la impresora
    print()
    print("Intentando conectar con la impresora...")
    printer = None
    try:
        printer = Win32Raw(nombre_impresora)
        print(f"[OK] Conexion establecida con la impresora '{nombre_impresora}'")
    except Error as e:
        print(f"[ERROR] Error ESC/POS al conectar: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error al conectar: {e}")
        return False
    
    # Intentar imprimir un ticket de prueba
    print()
    print("Imprimiendo ticket de prueba...")
    try:
        # Configurar impresora
        printer.set(align='center', font='a', width=1, height=1, bold=True)
        printer.text("TICKET DE PRUEBA\n")
        printer.text("Impresora XP-80C\n")
        printer.set(align='center')
        printer.text("=" * 48 + "\n")
        printer.set(align='left', font='a', width=1, height=1, bold=False)
        printer.text("Si ves este ticket, la impresora funciona correctamente!\n")
        printer.text("=" * 48 + "\n")
        printer.text("\n\n\n")
        printer.cut()
        
        print("[OK] Ticket de prueba enviado a la impresora")
        print("Verifica que el ticket se haya impreso correctamente")
        
    except Error as e:
        print(f"[ERROR] Error ESC/POS al imprimir: {e}")
        if printer:
            try:
                printer.close()
            except:
                pass
        return False
    except Exception as e:
        print(f"[ERROR] Error al imprimir: {e}")
        print()
        print("Detalles del error:")
        import traceback
        traceback.print_exc()
        if printer:
            try:
                printer.close()
            except:
                pass
        return False
    finally:
        try:
            printer.close()
            print("[OK] Conexion cerrada correctamente")
        except:
            pass
    
    print()
    print("="*60)
    print("[OK] PRUEBA COMPLETADA")
    print("="*60)
    return True

if __name__ == "__main__":
    try:
        exito = probar_impresora()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\nPrueba cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
