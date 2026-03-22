"""
Sistema de Caja para Foodtruck - PAPUCHO FOODTRUCK
Aplicación principal que integra todos los componentes de la UI
"""
import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# IMPORTANTE: Verificar instancia única ANTES de importar tkinter
from utils.instancia_unica import verificar_instancia_unica, limpiar_archivo_lock, activar_instancia_existente

# Verificar instancia única lo más temprano posible
if not verificar_instancia_unica():
    # Ya hay una instancia ejecutándose
    # Intentar traer la ventana existente al frente
    ventana_activada = activar_instancia_existente()
    
    # Siempre mostrar mensaje informativo
    try:
        import ctypes
        if ventana_activada:
            mensaje = "Papucho Foodtruck ya está ejecutándose.\n\nSe ha traído la ventana existente al frente."
        else:
            mensaje = "Papucho Foodtruck ya está ejecutándose.\n\nNo se pudo encontrar la ventana existente.\n\nPor favor, cierre la instancia actual antes de abrir una nueva."
        
        ctypes.windll.user32.MessageBoxW(
            0,
            mensaje,
            "Aplicación ya en ejecución",
            0x30  # MB_ICONWARNING
        )
    except Exception as e:
        print(f"Papucho Foodtruck ya está ejecutándose. Error al mostrar mensaje: {e}")
    
    # Cerrar esta instancia
    sys.exit(0)

# Ahora sí importar tkinter y el resto de módulos
import tkinter as tk
from tkinter import ttk, messagebox
import time

from ui.encabezado import Encabezado
from ui.navegador import Navegador
from ui.seleccion import Seleccion
from ui.carrito import Carrito
from ui.administracion import VentanaAdministracion
from ui.splash import SplashScreen
from utils.productos import cargar_productos, guardar_productos
from utils.ingredientes import cargar_ingredientes, guardar_ingredientes
from utils.backup import crear_backup_automatico
from utils.rutas import migrar_datos_desde_instalacion


class AplicacionCaja:
    """Clase principal de la aplicación de caja"""
    
    def __init__(self, root):
        self.root = root
        self.configurar_ventana()
        self.configurar_cierre()
        self.crear_componentes()
        self.configurar_layout()
    
    def configurar_ventana(self):
        """Configura la ventana principal"""
        self.root.title("PAPUCHO FOODTRUCK - Sistema de Caja")
        # Pantalla completa
        self.root.state('zoomed')  # Windows
        # Alternativa para Linux/Mac: self.root.attributes('-zoomed', True)
        self.root.minsize(1000, 600)
        
        # Configurar icono de la ventana
        try:
            # Intentar obtener la ruta del icono
            if getattr(sys, 'frozen', False):
                # Si está instalado, el icono está en la carpeta de instalación
                ruta_icono = os.path.join(os.path.dirname(sys.executable), 'Icono Hamburguesa.ico')
            else:
                # En desarrollo, el icono está en la raíz del proyecto
                ruta_icono = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Icono Hamburguesa.ico')
            
            if os.path.exists(ruta_icono):
                self.root.iconbitmap(ruta_icono)
        except Exception as e:
            # Si falla, continuar sin icono (no crítico)
            print(f"No se pudo cargar el icono: {e}")
        
        # Configurar estilo
        estilo = ttk.Style()
        estilo.theme_use('clam')
        
        # Configurar colores personalizados
        estilo.configure('Accent.TButton', foreground='white')
    
    def configurar_cierre(self):
        """Configura el handler para cuando se cierra la ventana"""
        def on_closing():
            """Handler que se ejecuta al cerrar la aplicación"""
            # Mostrar ventana de confirmación
            respuesta = messagebox.askyesno(
                "Confirmar cierre",
                "¿Está seguro que desea cerrar el sistema?",
                icon='question'
            )
            
            # Si el usuario confirma, proceder con el cierre
            if respuesta:
                try:
                    # Forzar guardado de todos los datos
                    self.guardar_todos_los_datos()
                    # Crear backup automático después de guardar
                    self.crear_backup_al_cerrar()
                except Exception as e:
                    # Si hay error al guardar, mostrar mensaje pero permitir cerrar
                    print(f"Error al guardar datos: {e}")
                finally:
                    # Limpiar archivo de bloqueo antes de cerrar
                    limpiar_archivo_lock()
                    # Cerrar la aplicación
                    self.root.destroy()
            # Si el usuario cancela, no hacer nada (la ventana permanece abierta)
        
        # Vincular el evento de cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
    
    def guardar_todos_los_datos(self):
        """Fuerza el guardado de todos los datos (productos e ingredientes)"""
        try:
            # Recargar y guardar productos (fuerza sincronización)
            productos_data = cargar_productos()
            guardar_productos(productos_data)
            
            # Recargar y guardar ingredientes (fuerza sincronización)
            ingredientes_data = cargar_ingredientes()
            guardar_ingredientes(ingredientes_data)
        except Exception as e:
            print(f"Error al guardar datos al cerrar: {e}")
            raise
    
    def crear_backup_al_cerrar(self):
        """Crea un backup automático de todos los datos al cerrar la aplicación (OPCIONAL)"""
        # Ya no se hace backup automático al cerrar
        # El usuario puede hacer backup manualmente desde el menú
        pass
    
    def crear_componentes(self):
        """Crea todos los componentes de la UI"""
        # Encabezado (arriba, ancho completo)
        self.encabezado = Encabezado(self.root)
        
        # Frame principal para el contenido
        self.frame_principal = ttk.Frame(self.root)
        
        # Navegador (izquierda)
        self.navegador = Navegador(self.frame_principal)
        
        # Selección de productos (centro)
        self.seleccion = Seleccion(self.frame_principal)
        
        # Carrito (derecha)
        self.carrito = Carrito(self.frame_principal)
        
        # Conectar componentes
        self.conectar_componentes()
    
    def conectar_componentes(self):
        """Conecta los componentes entre sí"""
        # Hacer que la selección pueda agregar items al carrito
        self.seleccion.callback_agregar_carrito = self.carrito.agregar_item
        
        # Conectar navegador con administración
        self.navegador.callback_administracion = self.abrir_administracion
        
        # Conectar navegador con backup
        self.navegador.callback_backup = self.hacer_backup_manual
    
    def abrir_administracion(self):
        """Abre la ventana de administración"""
        VentanaAdministracion(
            self.root,
            callback_actualizar=self.actualizar_productos
        )
    
    def actualizar_productos(self):
        """Actualiza los productos en la selección cuando se modifican en administración"""
        self.seleccion.recargar_productos()
    
    def hacer_backup_manual(self):
        """Muestra ventana de confirmación y ejecuta backup manual"""
        from utils.backup import crear_backup_automatico, obtener_ruta_backup
        
        # Mostrar ventana de confirmación
        respuesta = messagebox.askyesno(
            "Confirmar Backup",
            "¿Desea crear un backup de todos los datos?\n\n"
            "El backup se guardará en:\n"
            f"{obtener_ruta_backup()}",
            icon='question'
        )
        
        if respuesta:
            # Mostrar mensaje de progreso
            ventana_progreso = tk.Toplevel(self.root)
            ventana_progreso.title("Creando Backup")
            ventana_progreso.geometry("400x150")
            ventana_progreso.transient(self.root)
            ventana_progreso.grab_set()
            
            # Centrar ventana
            ventana_progreso.update_idletasks()
            x = (ventana_progreso.winfo_screenwidth() // 2) - (ventana_progreso.winfo_width() // 2)
            y = (ventana_progreso.winfo_screenheight() // 2) - (ventana_progreso.winfo_height() // 2)
            ventana_progreso.geometry(f"+{x}+{y}")
            
            frame_progreso = ttk.Frame(ventana_progreso, padding=20)
            frame_progreso.pack(fill='both', expand=True)
            
            label_progreso = ttk.Label(
                frame_progreso,
                text="Creando backup...\nPor favor espere.",
                font=('Arial', 10)
            )
            label_progreso.pack(pady=10)
            
            ventana_progreso.update()
            
            try:
                # Crear backup
                ruta_backup, backups_eliminados = crear_backup_automatico()
                
                # Cerrar ventana de progreso
                ventana_progreso.destroy()
                
                if ruta_backup:
                    mensaje = f"✅ Backup creado exitosamente.\n\n"
                    mensaje += f"Ubicación:\n{ruta_backup}\n\n"
                    if backups_eliminados > 0:
                        mensaje += f"Se eliminaron {backups_eliminados} backup(s) antiguo(s)."
                    else:
                        mensaje += "No se eliminaron backups antiguos."
                    
                    messagebox.showinfo("Backup Exitoso", mensaje)
                else:
                    messagebox.showerror(
                        "Error",
                        "No se pudo crear el backup.\n\n"
                        "Verifique que haya datos para respaldar."
                    )
            except Exception as e:
                ventana_progreso.destroy()
                messagebox.showerror(
                    "Error",
                    f"Error al crear backup:\n{str(e)}"
                )
    
    def configurar_layout(self):
        """Configura el layout usando grid"""
        # Encabezado en la fila 0, columnas 0-2
        self.encabezado.grid(row=0, column=0, columnspan=3, sticky='ew', padx=5, pady=5)
        
        # Frame principal en la fila 1
        self.frame_principal.grid(row=1, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)
        
        # Configurar grid del frame principal
        self.frame_principal.columnconfigure(1, weight=5)  # Selección (centro) - más espacio
        self.frame_principal.columnconfigure(0, weight=1)  # Navegador - más estrecho
        self.frame_principal.columnconfigure(2, weight=2)  # Carrito
        self.frame_principal.rowconfigure(0, weight=1)
        
        # Navegador (columna 0)
        self.navegador.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        # Selección (columna 1)
        self.seleccion.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        
        # Carrito (columna 2)
        self.carrito.grid(row=0, column=2, sticky='nsew', padx=5, pady=5)
        
        # Configurar grid de la ventana principal
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)


def main():
    """Función principal"""
    # La verificación de instancia única ya se hizo al inicio del módulo
    # Crear ventana principal pero ocultarla inmediatamente (debe existir para el splash)
    root = tk.Tk()
    root.withdraw()  # Ocultar inmediatamente, no se verá hasta que se muestre explícitamente
    
    # Crear splash screen PRIMERO (aparecerá antes que todo)
    splash = SplashScreen(root=root)
    
    # Forzar que el splash se muestre y esté al frente
    splash.splash.update()
    splash.splash.lift()
    splash.splash.attributes('-topmost', True)
    
    # Simular progreso inicial
    splash.actualizar_progreso(5, "Iniciando sistema...")
    splash.splash.update()
    time.sleep(0.3)
    
    def inicializar_aplicacion():
        """Función que inicializa la aplicación"""
        # Migrar datos antiguos desde instalación si existen (solo una vez)
        splash.actualizar_progreso(10, "Verificando datos...")
        splash.splash.update()
        try:
            migrar_datos_desde_instalacion()
        except Exception:
            pass  # No bloquear si falla la migración
        
        # Actualizar progreso
        splash.actualizar_progreso(15, "Cargando productos...")
        splash.splash.update()
        time.sleep(0.2)
        
        # Asegurar que las categorías fijas existan al iniciar
        cargar_productos()
        
        splash.actualizar_progreso(35, "Cargando ingredientes...")
        splash.splash.update()
        time.sleep(0.2)
        
        # Cargar ingredientes para verificar que todo esté bien
        cargar_ingredientes()
        
        splash.actualizar_progreso(50, "Inicializando componentes...")
        splash.splash.update()
        time.sleep(0.2)
        
        # Crear la aplicación (pero la ventana sigue oculta)
        splash.actualizar_progreso(65, "Creando interfaz...")
        splash.splash.update()
        app = AplicacionCaja(root)
        
        splash.actualizar_progreso(85, "Preparando interfaz...")
        splash.splash.update()
        time.sleep(0.2)
        
        splash.actualizar_progreso(95, "Finalizando...")
        splash.splash.update()
        time.sleep(0.2)
        
        return app
    
    # Inicializar aplicación con splash screen
    try:
        app = inicializar_aplicacion()
        splash.actualizar_progreso(100, "¡Listo!")
        splash.splash.update()
        time.sleep(0.3)
        
        # Cerrar splash después de un pequeño delay para que se vea el progreso
        def cerrar_splash_y_mostrar():
            splash.cerrar()
            # Asegurar que la ventana principal esté visible y al frente
            root.deiconify()
            root.lift()
            root.focus_set()
        
        splash.splash.after(200, cerrar_splash_y_mostrar)
    except Exception as e:
        splash.cerrar()
        if root:
            root.deiconify()
        raise
    
    # Iniciar el loop principal (ahora la ventana principal está visible)
    root.mainloop()


if __name__ == "__main__":
    main()
