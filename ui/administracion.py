"""
Módulo para la ventana de administración de productos
Permite Alta, Baja y Modificación de productos
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import os
import sys

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.productos import (
    cargar_productos, CATEGORIAS_FIJAS,
    agregar_producto, modificar_producto, eliminar_producto,
    obtener_todos_los_productos
)
from utils.ingredientes import (
    cargar_ingredientes,
    agregar_ingrediente, modificar_ingrediente, eliminar_ingrediente,
    obtener_todos_los_ingredientes, buscar_ingrediente_por_id
)
from ui.administracion_ingredientes_producto import (
    cargar_ingredientes_por_categoria,
    agregar_ingrediente_a_producto_ui,
    eliminar_ingrediente_de_producto_ui
)
from utils.imagenes import (
    guardar_imagen_producto, guardar_imagen_ingrediente,
    cargar_imagen_tkinter, eliminar_imagen
)


class VentanaAdministracion:
    """Ventana de administración de productos"""
    
    def __init__(self, parent, callback_actualizar=None):
        """
        Inicializa la ventana de administración
        
        Args:
            parent: Ventana padre
            callback_actualizar: Función a llamar cuando se actualicen los productos
        """
        self.parent = parent
        self.callback_actualizar = callback_actualizar
        self.producto_seleccionado = None
        
        self.crear_ventana()
        self.cargar_lista_productos()
    
    def crear_ventana(self):
        """Crea y configura la ventana de administración"""
        self.ventana = tk.Toplevel(self.parent)
        self.ventana.title("Administración")
        self.ventana.geometry("1400x700")
        self.ventana.resizable(True, True)
        
        # Centrar la ventana
        self.ventana.transient(self.parent)
        self.ventana.grab_set()
        
        # Frame principal
        frame_principal = ttk.Frame(self.ventana, padding=10)
        frame_principal.pack(fill='both', expand=True)
        
        # Título
        titulo = ttk.Label(
            frame_principal,
            text="⚙️ Administración",
            font=('Arial', 16, 'bold')
        )
        titulo.pack(pady=10)
        
        # Notebook (pestañas)
        self.notebook = ttk.Notebook(frame_principal)
        self.notebook.pack(fill='both', expand=True)
        
        # Pestaña de Productos
        frame_productos = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame_productos, text="📦 Productos")
        self.crear_pestaña_productos(frame_productos)
        
        # Pestaña de Ingredientes
        frame_ingredientes = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame_ingredientes, text="🥗 Ingredientes")
        self.crear_pestaña_ingredientes(frame_ingredientes)
        
        # Centrar la ventana horizontalmente y posicionarla arriba
        self.ventana.update_idletasks()
        x = (self.ventana.winfo_screenwidth() // 2) - (self.ventana.winfo_width() // 2)
        y = 50  # Posición fija cerca de la parte superior
        self.ventana.geometry(f"+{x}+{y}")
    
    def crear_pestaña_productos(self, parent):
        """Crea la pestaña de productos"""
        # Configurar grid
        parent.columnconfigure(0, weight=1)  # Lista (más pequeña)
        parent.columnconfigure(1, weight=10)  # Formulario mucho más ancho
        parent.rowconfigure(0, weight=1)
        
        # Frame izquierdo: Lista de productos
        self.crear_frame_lista(parent)
        
        # Frame derecho: Formulario
        self.crear_frame_formulario(parent)
    
    def crear_frame_lista(self, parent):
        """Crea el frame con la lista de productos"""
        frame_lista = ttk.LabelFrame(parent, text="Lista de Productos", padding=10)
        frame_lista.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        frame_lista.columnconfigure(0, weight=1)
        frame_lista.rowconfigure(1, weight=1)
        
        # Frame para filtros
        frame_filtros = ttk.Frame(frame_lista)
        frame_filtros.grid(row=0, column=0, sticky='ew', pady=5)
        frame_filtros.columnconfigure(1, weight=1)
        frame_filtros.columnconfigure(3, weight=1)
        
        ttk.Label(frame_filtros, text="Categoría:").grid(row=0, column=0, padx=5)
        
        self.var_filtro_categoria = tk.StringVar(value="Todas")
        combo_filtro = ttk.Combobox(
            frame_filtros,
            textvariable=self.var_filtro_categoria,
            values=["Todas"] + CATEGORIAS_FIJAS,
            state='readonly',
            width=15
        )
        combo_filtro.grid(row=0, column=1, padx=5, sticky='w')
        combo_filtro.bind('<<ComboboxSelected>>', lambda e: self.cargar_lista_productos())
        
        # Buscador
        ttk.Label(frame_filtros, text="🔍 Buscar:").grid(row=0, column=2, padx=(10, 5))
        self.var_buscador = tk.StringVar()
        entry_buscador = ttk.Entry(
            frame_filtros,
            textvariable=self.var_buscador,
            width=20
        )
        entry_buscador.grid(row=0, column=3, padx=5, sticky='ew')
        # Filtrar mientras se escribe
        self.var_buscador.trace_add('write', lambda *args: self.cargar_lista_productos())
        
        # Treeview para lista de productos
        frame_tree = ttk.Frame(frame_lista)
        frame_tree.grid(row=1, column=0, sticky='nsew')
        frame_tree.columnconfigure(0, weight=1)
        frame_tree.rowconfigure(0, weight=1)
        
        # Frame interno para el treeview con scroll
        frame_interno = ttk.Frame(frame_tree)
        frame_interno.grid(row=0, column=0, sticky='nsew')
        frame_interno.columnconfigure(0, weight=1)
        frame_interno.rowconfigure(0, weight=1)
        
        # Scrollbar vertical
        scrollbar_vertical = ttk.Scrollbar(frame_interno, orient='vertical')
        scrollbar_vertical.grid(row=0, column=1, sticky='ns')
        
        # Scrollbar horizontal
        scrollbar_horizontal = ttk.Scrollbar(frame_interno, orient='horizontal')
        scrollbar_horizontal.grid(row=1, column=0, sticky='ew')
        
        # Treeview (sin columna Categoría visible)
        self.tree = ttk.Treeview(
            frame_interno,
            columns=('ID', 'Categoría', 'Nombre', 'Precio', 'Descripción'),
            show='headings',
            yscrollcommand=scrollbar_vertical.set,
            xscrollcommand=scrollbar_horizontal.set,
            selectmode='browse'
        )
        scrollbar_vertical.config(command=self.tree.yview)
        scrollbar_horizontal.config(command=self.tree.xview)
        
        # Configurar columnas
        self.tree.heading('ID', text='ID')
        self.tree.heading('Categoría', text='Categoría')
        self.tree.heading('Nombre', text='Nombre')
        self.tree.heading('Precio', text='Precio')
        self.tree.heading('Descripción', text='Descripción')
        
        self.tree.column('ID', width=0, stretch=False)  # Ocultar columna ID
        self.tree.column('Categoría', width=0, stretch=False)  # Ocultar columna Categoría
        self.tree.column('Nombre', width=200, minwidth=150, stretch=False)  # Ancho fijo
        self.tree.column('Precio', width=120, minwidth=80, stretch=False)  # Ancho fijo
        # Configurar Descripción con ancho MUY grande para forzar scroll horizontal siempre
        self.tree.column('Descripción', width=350, minwidth=200, stretch=False)  # Ancho muy grande para forzar scroll
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        self.tree.bind('<<TreeviewSelect>>', self.on_seleccionar_producto)
        
        # Botones de acción
        frame_botones_lista = ttk.Frame(frame_lista)
        frame_botones_lista.grid(row=2, column=0, pady=10)
        
        btn_nuevo = ttk.Button(
            frame_botones_lista,
            text="➕ Nuevo Producto",
            command=self.nuevo_producto,
            width=20
        )
        btn_nuevo.pack(side='left', padx=5)
    
    def crear_frame_formulario(self, parent):
        """Crea el frame con el formulario de producto"""
        frame_formulario = ttk.LabelFrame(parent, text="Datos del Producto", padding=10)
        frame_formulario.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        frame_formulario.columnconfigure(0, weight=1)
        frame_formulario.rowconfigure(0, weight=1)
        
        # Canvas con scrollbar para el formulario
        canvas_formulario = tk.Canvas(frame_formulario)
        scrollbar_formulario = ttk.Scrollbar(frame_formulario, orient="vertical", command=canvas_formulario.yview)
        frame_contenido = ttk.Frame(canvas_formulario)
        
        frame_contenido.bind(
            "<Configure>",
            lambda e: canvas_formulario.configure(scrollregion=canvas_formulario.bbox("all"))
        )
        
        # Crear ventana del canvas
        canvas_window = canvas_formulario.create_window((0, 0), window=frame_contenido, anchor="nw")
        
        # Función para ajustar el ancho del frame cuando el canvas cambie de tamaño
        def ajustar_ancho_frame_form(event):
            canvas_width = event.width
            canvas_formulario.itemconfig(canvas_window, width=canvas_width)
        
        canvas_formulario.bind('<Configure>', ajustar_ancho_frame_form)
        canvas_formulario.configure(yscrollcommand=scrollbar_formulario.set)
        
        # Configurar scroll con rueda del mouse
        def on_mousewheel_form(event):
            # Verificar que el canvas todavía existe antes de usarlo
            try:
                if canvas_formulario.winfo_exists():
                    canvas_formulario.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                # El widget fue destruido, ignorar el error
                pass
        
        # Vincular solo al canvas y al frame contenido (no globalmente)
        canvas_formulario.bind("<MouseWheel>", on_mousewheel_form)
        frame_contenido.bind("<MouseWheel>", on_mousewheel_form)
        
        canvas_formulario.grid(row=0, column=0, sticky='nsew')
        scrollbar_formulario.grid(row=0, column=1, sticky='ns')
        
        # Guardar referencia al canvas para acceso desde otros métodos
        self.canvas_formulario = canvas_formulario
        
        # Ahora el contenido va en frame_contenido en lugar de frame_formulario
        frame_contenido.columnconfigure(1, weight=1)
        
        # Categoría
        ttk.Label(frame_contenido, text="Categoría:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.var_categoria = tk.StringVar()
        combo_categoria = ttk.Combobox(
            frame_contenido,
            textvariable=self.var_categoria,
            values=CATEGORIAS_FIJAS,
            state='readonly',
            width=20
        )
        combo_categoria.grid(row=0, column=1, sticky='ew', pady=5, padx=5)
        
        # Nombre
        ttk.Label(frame_contenido, text="Nombre:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.entry_nombre = ttk.Entry(frame_contenido, width=30)
        self.entry_nombre.grid(row=1, column=1, sticky='ew', pady=5, padx=5)
        
        # Precio
        ttk.Label(frame_contenido, text="Precio:").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        self.entry_precio = ttk.Entry(frame_contenido, width=30)
        self.entry_precio.grid(row=2, column=1, sticky='ew', pady=5, padx=5)
        
        # Descripción
        ttk.Label(frame_contenido, text="Descripción:").grid(row=3, column=0, sticky='nw', pady=5, padx=5)
        self.text_descripcion = tk.Text(frame_contenido, width=30, height=2, wrap='word')
        self.text_descripcion.grid(row=3, column=1, sticky='ew', pady=5, padx=5)
        
        # Sección de Imagen
        frame_imagen = ttk.LabelFrame(frame_contenido, text="Imagen del Producto", padding=10)
        frame_imagen.grid(row=4, column=0, columnspan=2, sticky='ew', pady=10, padx=5)
        frame_imagen.columnconfigure(0, weight=1)
        
        # Frame para preview y botón
        frame_imagen_controles = ttk.Frame(frame_imagen)
        frame_imagen_controles.grid(row=0, column=0, sticky='ew')
        frame_imagen_controles.columnconfigure(0, weight=1)
        
        # Preview de imagen (pequeño, 100x100)
        self.label_preview_imagen = ttk.Label(
            frame_imagen_controles,
            text="Sin imagen",
            background='lightgray',
            width=15
        )
        self.label_preview_imagen.grid(row=0, column=0, padx=5, pady=5)
        self.imagen_preview_producto = None  # Mantener referencia para evitar garbage collection
        
        # Botón cargar imagen
        btn_cargar_imagen = ttk.Button(
            frame_imagen_controles,
            text="📷 Cargar Imagen",
            command=self.cargar_imagen_producto,
            width=20
        )
        btn_cargar_imagen.grid(row=0, column=1, padx=5, pady=5)
        
        # Variable para ruta de imagen temporal
        self.ruta_imagen_producto_temp = None
        
        # Frame para botones
        frame_botones = ttk.Frame(frame_contenido)
        frame_botones.grid(row=5, column=0, columnspan=2, pady=20)
        
        # Botón Guardar
        self.btn_guardar = ttk.Button(
            frame_botones,
            text="💾 Guardar",
            command=self.guardar_producto,
            width=15
        )
        self.btn_guardar.pack(side='left', padx=5)
        
        # Botón Modificar
        self.btn_modificar = ttk.Button(
            frame_botones,
            text="✏️ Modificar",
            command=self.modificar_producto_actual,
            width=15,
            state='disabled'
        )
        self.btn_modificar.pack(side='left', padx=5)
        
        # Botón Eliminar
        self.btn_eliminar = ttk.Button(
            frame_botones,
            text="❌ Eliminar",
            command=self.eliminar_producto_actual,
            width=15,
            state='disabled'
        )
        self.btn_eliminar.pack(side='left', padx=5)
        
        # Botón Limpiar
        btn_limpiar = ttk.Button(
            frame_botones,
            text="🔄 Limpiar",
            command=self.limpiar_formulario,
            width=15
        )
        btn_limpiar.pack(side='left', padx=5)
        
        # Sección de Ingredientes del Producto
        frame_ingredientes_producto = ttk.LabelFrame(frame_contenido, text="Ingredientes del Producto", padding=10)
        frame_ingredientes_producto.grid(row=6, column=0, columnspan=2, sticky='ew', pady=10, padx=5)
        frame_ingredientes_producto.columnconfigure(0, weight=1)
        
        # Frame para agregar ingrediente
        frame_agregar_ing = ttk.Frame(frame_ingredientes_producto)
        frame_agregar_ing.grid(row=0, column=0, sticky='ew', pady=5)
        frame_agregar_ing.columnconfigure(1, weight=1)
        
        ttk.Label(frame_agregar_ing, text="Ingrediente:").grid(row=0, column=0, padx=5, sticky='w')
        self.combo_ingrediente = ttk.Combobox(frame_agregar_ing, state='readonly', width=20)
        self.combo_ingrediente.grid(row=0, column=1, padx=5, sticky='ew')
        
        ttk.Label(frame_agregar_ing, text="Cantidad Base:").grid(row=0, column=2, padx=5, sticky='w')
        self.entry_cantidad_ing = ttk.Entry(frame_agregar_ing, width=10)
        self.entry_cantidad_ing.grid(row=0, column=3, padx=5)
        self.entry_cantidad_ing.insert(0, "1")
        
        btn_agregar_ing = ttk.Button(
            frame_agregar_ing,
            text="➕ Agregar",
            command=self.agregar_ingrediente_producto,
            width=12
        )
        btn_agregar_ing.grid(row=0, column=4, padx=5)
        
        # Treeview para ingredientes del producto
        frame_tree_ing = ttk.Frame(frame_ingredientes_producto)
        frame_tree_ing.grid(row=1, column=0, sticky='nsew', pady=5)
        frame_tree_ing.columnconfigure(0, weight=1)
        frame_tree_ing.rowconfigure(0, weight=1)
        
        scrollbar_ing = ttk.Scrollbar(frame_tree_ing)
        scrollbar_ing.grid(row=0, column=1, sticky='ns')
        
        self.tree_ingredientes_producto = ttk.Treeview(
            frame_tree_ing,
            columns=('Nombre', 'Cantidad', 'Precio Extra', 'Precio Resta'),
            show='headings',
            yscrollcommand=scrollbar_ing.set,
            height=5
        )
        scrollbar_ing.config(command=self.tree_ingredientes_producto.yview)
        
        self.tree_ingredientes_producto.heading('Nombre', text='Nombre')
        self.tree_ingredientes_producto.heading('Cantidad', text='Cantidad Base')
        self.tree_ingredientes_producto.heading('Precio Extra', text='Precio Extra')
        self.tree_ingredientes_producto.heading('Precio Resta', text='Precio Resta')
        
        self.tree_ingredientes_producto.column('Nombre', width=150)
        self.tree_ingredientes_producto.column('Cantidad', width=100)
        self.tree_ingredientes_producto.column('Precio Extra', width=100)
        self.tree_ingredientes_producto.column('Precio Resta', width=100)
        
        self.tree_ingredientes_producto.grid(row=0, column=0, sticky='nsew')
        
        # Botón eliminar ingrediente
        btn_eliminar_ing = ttk.Button(
            frame_ingredientes_producto,
            text="❌ Eliminar Ingrediente",
            command=self.eliminar_ingrediente_producto,
            width=30
        )
        btn_eliminar_ing.grid(row=2, column=0, pady=5)
        
        # Actualizar combo cuando cambia la categoría
        combo_categoria.bind('<<ComboboxSelected>>', self.on_categoria_changed)
    
    def cargar_lista_productos(self):
        """Carga la lista de productos en el treeview"""
        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Obtener productos
        productos = obtener_todos_los_productos()
        
        # Filtrar por categoría si es necesario
        filtro_categoria = self.var_filtro_categoria.get()
        if filtro_categoria != "Todas":
            productos = [p for p in productos if p["categoria"] == filtro_categoria]
        
        # Filtrar por texto de búsqueda si existe
        texto_busqueda = self.var_buscador.get().strip().lower()
        if texto_busqueda:
            productos = [
                p for p in productos
                if texto_busqueda in p['nombre'].lower()
                or texto_busqueda in p.get('descripcion', '').lower()
            ]
        
        # Agregar productos al treeview
        for producto in productos:
            self.tree.insert(
                '',
                'end',
                values=(
                    producto['id'],
                    producto['categoria'],
                    producto['nombre'],
                    f"${producto['precio']:,.2f}",
                    producto.get('descripcion', '')
                )
            )
    
    def on_seleccionar_producto(self, event):
        """Callback cuando se selecciona un producto en la lista"""
        seleccion = self.tree.selection()
        if not seleccion:
            return
        
        item = self.tree.item(seleccion[0])
        producto_id = int(item['values'][0])
        
        # Buscar el producto completo
        from utils.productos import buscar_producto_por_id
        resultado = buscar_producto_por_id(producto_id)
        
        if resultado:
            self.producto_seleccionado = resultado['producto']
            
            # Llenar formulario
            self.var_categoria.set(resultado['categoria'])
            self.entry_nombre.delete(0, 'end')
            self.entry_nombre.insert(0, self.producto_seleccionado['nombre'])
            self.entry_precio.delete(0, 'end')
            self.entry_precio.insert(0, str(self.producto_seleccionado['precio']))
            self.text_descripcion.delete('1.0', 'end')
            self.text_descripcion.insert('1.0', self.producto_seleccionado.get('descripcion', ''))
            
            # Cargar imagen del producto si existe
            self.mostrar_imagen_producto(self.producto_seleccionado.get('imagen'))
            self.ruta_imagen_producto_temp = None
            
            # Habilitar botones de modificar y eliminar
            self.btn_modificar.config(state='normal')
            self.btn_eliminar.config(state='normal')
            self.btn_guardar.config(state='disabled')
            
            # Cargar ingredientes del producto
            self.cargar_ingredientes_producto()
            # Cargar ingredientes disponibles según la categoría
            self.on_categoria_changed()
    
    def nuevo_producto(self):
        """Prepara el formulario para un nuevo producto"""
        self.limpiar_formulario()
        self.producto_seleccionado = None
        self.btn_guardar.config(state='normal')
        self.btn_modificar.config(state='disabled')
        self.btn_eliminar.config(state='disabled')
    
    def limpiar_formulario(self):
        """Limpia el formulario"""
        self.var_categoria.set('')
        self.entry_nombre.delete(0, 'end')
        self.entry_precio.delete(0, 'end')
        self.text_descripcion.delete('1.0', 'end')
        self.producto_seleccionado = None
        self.tree.selection_remove(self.tree.selection())
        # Limpiar imagen
        self.mostrar_imagen_producto(None)
        self.ruta_imagen_producto_temp = None
        # Limpiar el treeview de ingredientes del producto
        if hasattr(self, 'tree_ingredientes_producto'):
            for item in self.tree_ingredientes_producto.get_children():
                self.tree_ingredientes_producto.delete(item)
    
    def validar_formulario(self):
        """Valida que el formulario esté completo"""
        if not self.var_categoria.get():
            messagebox.showerror("Error", "Debe seleccionar una categoría")
            return False
        
        if not self.entry_nombre.get().strip():
            messagebox.showerror("Error", "Debe ingresar un nombre")
            return False
        
        try:
            precio = float(self.entry_precio.get())
            if precio <= 0:
                messagebox.showerror("Error", "El precio debe ser mayor a 0")
                return False
        except ValueError:
            messagebox.showerror("Error", "El precio debe ser un número válido")
            return False
        
        return True
    
    def guardar_producto(self):
        """Guarda un nuevo producto"""
        if not self.validar_formulario():
            return
        
        categoria = self.var_categoria.get()
        nombre = self.entry_nombre.get().strip()
        precio = float(self.entry_precio.get())
        descripcion = self.text_descripcion.get('1.0', 'end').strip()
        
        try:
            nuevo_producto = agregar_producto(categoria, nombre, precio, descripcion)
            producto_id = nuevo_producto['id']
            
            # Guardar imagen si se cargó una
            if self.ruta_imagen_producto_temp:
                try:
                    ruta_imagen = guardar_imagen_producto(self.ruta_imagen_producto_temp, producto_id)
                    # Actualizar producto con imagen
                    from utils.productos import modificar_producto
                    modificar_producto(producto_id, categoria, nombre, precio, descripcion, ruta_imagen)
                except Exception as e:
                    messagebox.showwarning("Advertencia", f"Producto guardado pero error al guardar imagen: {str(e)}")
            
            messagebox.showinfo("Éxito", "Producto agregado correctamente")
            self.cargar_lista_productos()
            self.limpiar_formulario()
            
            # Notificar actualización
            if self.callback_actualizar:
                self.callback_actualizar()
        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar producto: {str(e)}")
    
    def modificar_producto_actual(self):
        """Modifica el producto seleccionado"""
        if not self.producto_seleccionado:
            messagebox.showerror("Error", "Debe seleccionar un producto")
            return
        
        if not self.validar_formulario():
            return
        
        producto_id = self.producto_seleccionado['id']
        categoria = self.var_categoria.get()
        nombre = self.entry_nombre.get().strip()
        precio = float(self.entry_precio.get())
        descripcion = self.text_descripcion.get('1.0', 'end').strip()
        
        # Obtener imagen actual o nueva
        ruta_imagen = self.producto_seleccionado.get('imagen')
        
        # Si se cargó una nueva imagen, guardarla
        if self.ruta_imagen_producto_temp:
            try:
                # Eliminar imagen anterior si existe
                if ruta_imagen:
                    eliminar_imagen(ruta_imagen)
                # Guardar nueva imagen
                ruta_imagen = guardar_imagen_producto(self.ruta_imagen_producto_temp, producto_id)
            except Exception as e:
                messagebox.showwarning("Advertencia", f"Error al guardar imagen: {str(e)}")
        
        try:
            if modificar_producto(producto_id, categoria, nombre, precio, descripcion, ruta_imagen):
                messagebox.showinfo("Éxito", "Producto modificado correctamente")
                self.cargar_lista_productos()
                
                # Preparar formulario para crear un nuevo producto
                self.nuevo_producto()
                
                # Notificar actualización
                if self.callback_actualizar:
                    self.callback_actualizar()
            else:
                messagebox.showerror("Error", "No se pudo modificar el producto")
        except Exception as e:
            messagebox.showerror("Error", f"Error al modificar producto: {str(e)}")
    
    def eliminar_producto_actual(self):
        """Elimina el producto seleccionado"""
        if not self.producto_seleccionado:
            messagebox.showerror("Error", "Debe seleccionar un producto")
            return
        
        # Confirmar eliminación
        respuesta = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar el producto '{self.producto_seleccionado['nombre']}'?"
        )
        
        if not respuesta:
            return
        
        try:
            if eliminar_producto(self.producto_seleccionado['id']):
                messagebox.showinfo("Éxito", "Producto eliminado correctamente")
                self.cargar_lista_productos()
                self.limpiar_formulario()
                
                # Notificar actualización
                if self.callback_actualizar:
                    self.callback_actualizar()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el producto")
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar producto: {str(e)}")
    
    def crear_pestaña_ingredientes(self, parent):
        """Crea la pestaña de administración de ingredientes"""
        # Configurar grid
        parent.columnconfigure(0, weight=3)  # Lista más ancha
        parent.columnconfigure(1, weight=2)  # Formulario más estrecho
        parent.rowconfigure(0, weight=1)
        
        # Frame izquierdo: Lista de ingredientes
        frame_lista = ttk.LabelFrame(parent, text="Lista de Ingredientes", padding=10)
        frame_lista.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        frame_lista.columnconfigure(0, weight=1)
        frame_lista.rowconfigure(1, weight=1)
        
        # Treeview para lista de ingredientes
        frame_tree = ttk.Frame(frame_lista)
        frame_tree.grid(row=1, column=0, sticky='nsew')
        frame_tree.columnconfigure(0, weight=1)
        frame_tree.rowconfigure(0, weight=1)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tree)
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Treeview
        self.tree_ingredientes = ttk.Treeview(
            frame_tree,
            columns=('ID', 'Nombre', 'Categorías', 'Precio Extra', 'Precio Resta'),
            show='headings',
            yscrollcommand=scrollbar.set,
            selectmode='browse'
        )
        scrollbar.config(command=self.tree_ingredientes.yview)
        
        # Configurar columnas
        self.tree_ingredientes.heading('ID', text='ID')
        self.tree_ingredientes.heading('Nombre', text='Nombre')
        self.tree_ingredientes.heading('Categorías', text='Categorías')
        self.tree_ingredientes.heading('Precio Extra', text='Precio Extra')
        self.tree_ingredientes.heading('Precio Resta', text='Precio Resta')
        
        self.tree_ingredientes.column('ID', width=0, stretch=False)  # Ocultar
        self.tree_ingredientes.column('Nombre', width=200)
        self.tree_ingredientes.column('Categorías', width=250)
        self.tree_ingredientes.column('Precio Extra', width=120)
        self.tree_ingredientes.column('Precio Resta', width=120)
        
        self.tree_ingredientes.grid(row=0, column=0, sticky='nsew')
        self.tree_ingredientes.bind('<<TreeviewSelect>>', self.on_seleccionar_ingrediente)
        
        # Botones de acción
        frame_botones_lista = ttk.Frame(frame_lista)
        frame_botones_lista.grid(row=2, column=0, pady=10)
        
        btn_nuevo_ing = ttk.Button(
            frame_botones_lista,
            text="➕ Nuevo Ingrediente",
            command=self.nuevo_ingrediente,
            width=20
        )
        btn_nuevo_ing.pack(side='left', padx=5)
        
        # Frame derecho: Formulario de ingrediente
        frame_formulario_ing = ttk.LabelFrame(parent, text="Datos del Ingrediente", padding=10)
        frame_formulario_ing.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        frame_formulario_ing.columnconfigure(0, weight=1)
        frame_formulario_ing.rowconfigure(0, weight=1)
        
        # Canvas con scrollbar para el formulario de ingredientes
        canvas_formulario_ing = tk.Canvas(frame_formulario_ing)
        scrollbar_formulario_ing = ttk.Scrollbar(frame_formulario_ing, orient="vertical", command=canvas_formulario_ing.yview)
        frame_contenido_ing = ttk.Frame(canvas_formulario_ing)
        
        frame_contenido_ing.bind(
            "<Configure>",
            lambda e: canvas_formulario_ing.configure(scrollregion=canvas_formulario_ing.bbox("all"))
        )
        
        # Crear ventana del canvas
        canvas_window_ing = canvas_formulario_ing.create_window((0, 0), window=frame_contenido_ing, anchor="nw")
        
        # Función para ajustar el ancho del frame cuando el canvas cambie de tamaño
        def ajustar_ancho_frame_form_ing(event):
            canvas_width = event.width
            canvas_formulario_ing.itemconfig(canvas_window_ing, width=canvas_width)
        
        canvas_formulario_ing.bind('<Configure>', ajustar_ancho_frame_form_ing)
        canvas_formulario_ing.configure(yscrollcommand=scrollbar_formulario_ing.set)
        
        # Configurar scroll con rueda del mouse
        def on_mousewheel_form_ing(event):
            # Verificar que el canvas todavía existe antes de usarlo
            try:
                if canvas_formulario_ing.winfo_exists():
                    canvas_formulario_ing.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                # El widget fue destruido, ignorar el error
                pass
        
        # Vincular solo al canvas y al frame contenido (no globalmente)
        canvas_formulario_ing.bind("<MouseWheel>", on_mousewheel_form_ing)
        frame_contenido_ing.bind("<MouseWheel>", on_mousewheel_form_ing)
        
        canvas_formulario_ing.grid(row=0, column=0, sticky='nsew')
        scrollbar_formulario_ing.grid(row=0, column=1, sticky='ns')
        
        # Guardar referencia al canvas para acceso desde otros métodos
        self.canvas_formulario_ing = canvas_formulario_ing
        
        # Ahora el contenido va en frame_contenido_ing en lugar de frame_formulario_ing
        frame_contenido_ing.columnconfigure(1, weight=1)
        
        # Nombre
        ttk.Label(frame_contenido_ing, text="Nombre:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.entry_nombre_ing = ttk.Entry(frame_contenido_ing, width=30)
        self.entry_nombre_ing.grid(row=0, column=1, sticky='ew', pady=5, padx=5)
        
        # Categorías (checkboxes)
        ttk.Label(frame_contenido_ing, text="Categorías:").grid(row=1, column=0, sticky='nw', pady=5, padx=5)
        frame_categorias_ing = ttk.Frame(frame_contenido_ing)
        frame_categorias_ing.grid(row=1, column=1, sticky='ew', pady=5, padx=5)
        
        self.vars_categorias_ing = {}
        for idx, categoria in enumerate(CATEGORIAS_FIJAS):
            var = tk.BooleanVar()
            self.vars_categorias_ing[categoria] = var
            checkbox = ttk.Checkbutton(
                frame_categorias_ing,
                text=categoria,
                variable=var
            )
            checkbox.grid(row=idx // 2, column=idx % 2, sticky='w', padx=5, pady=2)
        
        # Precio Extra
        ttk.Label(frame_contenido_ing, text="Precio Extra:").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        self.entry_precio_extra = ttk.Entry(frame_contenido_ing, width=30)
        self.entry_precio_extra.grid(row=2, column=1, sticky='ew', pady=5, padx=5)
        
        # Precio Resta
        ttk.Label(frame_contenido_ing, text="Precio Resta:").grid(row=3, column=0, sticky='w', pady=5, padx=5)
        self.entry_precio_resta = ttk.Entry(frame_contenido_ing, width=30)
        self.entry_precio_resta.grid(row=3, column=1, sticky='ew', pady=5, padx=5)
        
        # Sección de Imagen
        frame_imagen_ing = ttk.LabelFrame(frame_contenido_ing, text="Imagen del Ingrediente", padding=10)
        frame_imagen_ing.grid(row=4, column=0, columnspan=2, sticky='ew', pady=10, padx=5)
        frame_imagen_ing.columnconfigure(0, weight=1)
        
        # Frame para preview y botón
        frame_imagen_controles_ing = ttk.Frame(frame_imagen_ing)
        frame_imagen_controles_ing.grid(row=0, column=0, sticky='ew')
        frame_imagen_controles_ing.columnconfigure(0, weight=1)
        
        # Preview de imagen (pequeño, 100x100)
        self.label_preview_imagen_ing = ttk.Label(
            frame_imagen_controles_ing,
            text="Sin imagen",
            background='lightgray',
            width=15
        )
        self.label_preview_imagen_ing.grid(row=0, column=0, padx=5, pady=5)
        self.imagen_preview_ingrediente = None  # Mantener referencia para evitar garbage collection
        
        # Botón cargar imagen
        btn_cargar_imagen_ing = ttk.Button(
            frame_imagen_controles_ing,
            text="📷 Cargar Imagen",
            command=self.cargar_imagen_ingrediente,
            width=20
        )
        btn_cargar_imagen_ing.grid(row=0, column=1, padx=5, pady=5)
        
        # Variable para ruta de imagen temporal
        self.ruta_imagen_ingrediente_temp = None
        
        # Frame para botones
        frame_botones_ing = ttk.Frame(frame_contenido_ing)
        frame_botones_ing.grid(row=5, column=0, columnspan=2, pady=20)
        
        # Botón Guardar
        self.btn_guardar_ing = ttk.Button(
            frame_botones_ing,
            text="💾 Guardar",
            command=self.guardar_ingrediente,
            width=15
        )
        self.btn_guardar_ing.pack(side='left', padx=5)
        
        # Botón Modificar
        self.btn_modificar_ing = ttk.Button(
            frame_botones_ing,
            text="✏️ Modificar",
            command=self.modificar_ingrediente_actual,
            width=15,
            state='disabled'
        )
        self.btn_modificar_ing.pack(side='left', padx=5)
        
        # Botón Eliminar
        self.btn_eliminar_ing = ttk.Button(
            frame_botones_ing,
            text="❌ Eliminar",
            command=self.eliminar_ingrediente_actual,
            width=15,
            state='disabled'
        )
        self.btn_eliminar_ing.pack(side='left', padx=5)
        
        # Botón Limpiar
        btn_limpiar_ing = ttk.Button(
            frame_botones_ing,
            text="🔄 Limpiar",
            command=self.limpiar_formulario_ingrediente,
            width=15
        )
        btn_limpiar_ing.pack(side='left', padx=5)
        
        # Cargar lista inicial
        self.cargar_lista_ingredientes()
        self.ingrediente_seleccionado = None
    
    def cargar_lista_ingredientes(self):
        """Carga la lista de ingredientes en el treeview"""
        # Limpiar treeview
        for item in self.tree_ingredientes.get_children():
            self.tree_ingredientes.delete(item)
        
        # Obtener ingredientes
        ingredientes = obtener_todos_los_ingredientes()
        
        # Agregar ingredientes al treeview
        for ingrediente in ingredientes:
            categorias_str = ", ".join(ingrediente.get("categorias", []))
            self.tree_ingredientes.insert(
                '',
                'end',
                values=(
                    ingrediente['id'],
                    ingrediente['nombre'],
                    categorias_str,
                    f"${ingrediente['precio_extra']:.2f}",
                    f"${ingrediente['precio_resta']:.2f}"
                )
            )
    
    def on_seleccionar_ingrediente(self, event):
        """Callback cuando se selecciona un ingrediente en la lista"""
        seleccion = self.tree_ingredientes.selection()
        if not seleccion:
            return
        
        item = self.tree_ingredientes.item(seleccion[0])
        ingrediente_id = int(item['values'][0])
        
        # Buscar el ingrediente completo
        ingrediente = buscar_ingrediente_por_id(ingrediente_id)
        
        if ingrediente:
            self.ingrediente_seleccionado = ingrediente
            
            # Llenar formulario
            self.entry_nombre_ing.delete(0, 'end')
            self.entry_nombre_ing.insert(0, ingrediente['nombre'])
            
            # Limpiar checkboxes
            for var in self.vars_categorias_ing.values():
                var.set(False)
            
            # Marcar categorías del ingrediente
            categorias = ingrediente.get("categorias", [])
            for categoria in categorias:
                if categoria in self.vars_categorias_ing:
                    self.vars_categorias_ing[categoria].set(True)
            
            self.entry_precio_extra.delete(0, 'end')
            self.entry_precio_extra.insert(0, str(ingrediente['precio_extra']))
            
            self.entry_precio_resta.delete(0, 'end')
            self.entry_precio_resta.insert(0, str(ingrediente['precio_resta']))
            
            # Cargar imagen del ingrediente si existe
            self.mostrar_imagen_ingrediente(ingrediente.get('imagen'))
            self.ruta_imagen_ingrediente_temp = None
            
            # Habilitar botones de modificar y eliminar
            self.btn_modificar_ing.config(state='normal')
            self.btn_eliminar_ing.config(state='normal')
            self.btn_guardar_ing.config(state='disabled')
    
    def nuevo_ingrediente(self):
        """Prepara el formulario para un nuevo ingrediente"""
        self.limpiar_formulario_ingrediente()
        self.ingrediente_seleccionado = None
        self.btn_guardar_ing.config(state='normal')
        self.btn_modificar_ing.config(state='disabled')
        self.btn_eliminar_ing.config(state='disabled')
    
    def limpiar_formulario_ingrediente(self):
        """Limpia el formulario de ingrediente"""
        self.entry_nombre_ing.delete(0, 'end')
        for var in self.vars_categorias_ing.values():
            var.set(False)
        self.entry_precio_extra.delete(0, 'end')
        self.entry_precio_resta.delete(0, 'end')
        self.ingrediente_seleccionado = None
        self.tree_ingredientes.selection_remove(self.tree_ingredientes.selection())
        # Limpiar imagen
        self.mostrar_imagen_ingrediente(None)
        self.ruta_imagen_ingrediente_temp = None
    
    def validar_formulario_ingrediente(self):
        """Valida que el formulario de ingrediente esté completo"""
        if not self.entry_nombre_ing.get().strip():
            messagebox.showerror("Error", "Debe ingresar un nombre")
            return False
        
        # Verificar que al menos una categoría esté seleccionada
        categorias_seleccionadas = [cat for cat, var in self.vars_categorias_ing.items() if var.get()]
        if not categorias_seleccionadas:
            messagebox.showerror("Error", "Debe seleccionar al menos una categoría")
            return False
        
        try:
            precio_extra = float(self.entry_precio_extra.get())
            if precio_extra < 0:
                messagebox.showerror("Error", "El precio extra debe ser mayor o igual a 0")
                return False
        except ValueError:
            messagebox.showerror("Error", "El precio extra debe ser un número válido")
            return False
        
        try:
            precio_resta = float(self.entry_precio_resta.get())
            if precio_resta < 0:
                messagebox.showerror("Error", "El precio de resta debe ser mayor o igual a 0")
                return False
        except ValueError:
            messagebox.showerror("Error", "El precio de resta debe ser un número válido")
            return False
        
        return True
    
    def guardar_ingrediente(self):
        """Guarda un nuevo ingrediente"""
        if not self.validar_formulario_ingrediente():
            return
        
        nombre = self.entry_nombre_ing.get().strip()
        categorias = [cat for cat, var in self.vars_categorias_ing.items() if var.get()]
        precio_extra = float(self.entry_precio_extra.get())
        precio_resta = float(self.entry_precio_resta.get())
        
        try:
            nuevo_ingrediente = agregar_ingrediente(nombre, categorias, precio_extra, precio_resta)
            ingrediente_id = nuevo_ingrediente['id']
            
            # Guardar imagen si se cargó una
            if self.ruta_imagen_ingrediente_temp:
                try:
                    ruta_imagen = guardar_imagen_ingrediente(self.ruta_imagen_ingrediente_temp, ingrediente_id)
                    # Actualizar ingrediente con imagen
                    from utils.ingredientes import modificar_ingrediente
                    modificar_ingrediente(ingrediente_id, nombre, categorias, precio_extra, precio_resta, ruta_imagen)
                except Exception as e:
                    messagebox.showwarning("Advertencia", f"Ingrediente guardado pero error al guardar imagen: {str(e)}")
            
            messagebox.showinfo("Éxito", "Ingrediente agregado correctamente")
            self.cargar_lista_ingredientes()
            self.limpiar_formulario_ingrediente()
        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar ingrediente: {str(e)}")
    
    def modificar_ingrediente_actual(self):
        """Modifica el ingrediente seleccionado"""
        if not self.ingrediente_seleccionado:
            messagebox.showerror("Error", "Debe seleccionar un ingrediente")
            return
        
        if not self.validar_formulario_ingrediente():
            return
        
        ingrediente_id = self.ingrediente_seleccionado['id']
        nombre = self.entry_nombre_ing.get().strip()
        categorias = [cat for cat, var in self.vars_categorias_ing.items() if var.get()]
        precio_extra = float(self.entry_precio_extra.get())
        precio_resta = float(self.entry_precio_resta.get())
        
        # Obtener imagen actual o nueva
        ruta_imagen = self.ingrediente_seleccionado.get('imagen')
        
        # Si se cargó una nueva imagen, guardarla
        if self.ruta_imagen_ingrediente_temp:
            try:
                # Eliminar imagen anterior si existe
                if ruta_imagen:
                    eliminar_imagen(ruta_imagen)
                # Guardar nueva imagen
                ruta_imagen = guardar_imagen_ingrediente(self.ruta_imagen_ingrediente_temp, ingrediente_id)
            except Exception as e:
                messagebox.showwarning("Advertencia", f"Error al guardar imagen: {str(e)}")
        
        try:
            if modificar_ingrediente(ingrediente_id, nombre, categorias, precio_extra, precio_resta, ruta_imagen):
                messagebox.showinfo("Éxito", "Ingrediente modificado correctamente")
                self.cargar_lista_ingredientes()
                self.nuevo_ingrediente()
                # Si hay un producto seleccionado, recargar sus ingredientes para mostrar cambios
                if self.producto_seleccionado:
                    from utils.productos import buscar_producto_por_id
                    resultado = buscar_producto_por_id(self.producto_seleccionado['id'])
                    if resultado:
                        self.producto_seleccionado = resultado['producto']
                        self.cargar_ingredientes_producto()
            else:
                messagebox.showerror("Error", "No se pudo modificar el ingrediente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al modificar ingrediente: {str(e)}")
    
    def eliminar_ingrediente_actual(self):
        """Elimina el ingrediente seleccionado"""
        if not self.ingrediente_seleccionado:
            messagebox.showerror("Error", "Debe seleccionar un ingrediente")
            return
        
        # Confirmar eliminación
        respuesta = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar el ingrediente '{self.ingrediente_seleccionado['nombre']}'?"
        )
        
        if not respuesta:
            return
        
        try:
            if eliminar_ingrediente(self.ingrediente_seleccionado['id']):
                messagebox.showinfo("Éxito", "Ingrediente eliminado correctamente")
                self.cargar_lista_ingredientes()
                self.limpiar_formulario_ingrediente()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el ingrediente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar ingrediente: {str(e)}")
    
    # Métodos para gestionar ingredientes de productos
    def on_categoria_changed(self, event=None):
        """Actualiza el combo de ingredientes cuando cambia la categoría del producto"""
        categoria = self.var_categoria.get()
        if categoria:
            cargar_ingredientes_por_categoria(self.combo_ingrediente, categoria)
        else:
            self.combo_ingrediente['values'] = []
    
    def cargar_ingredientes_producto(self):
        """Carga los ingredientes del producto seleccionado en el treeview"""
        # Limpiar treeview
        for item in self.tree_ingredientes_producto.get_children():
            self.tree_ingredientes_producto.delete(item)
        
        if not self.producto_seleccionado:
            return
        
        # Importar función para buscar ingrediente por nombre
        from utils.ingredientes import buscar_ingrediente_por_nombre
        
        ingredientes = self.producto_seleccionado.get('ingredientes', [])
        for ingrediente in ingredientes:
            nombre_ing = ingrediente.get('nombre', '')
            cantidad_base_ing = ingrediente.get('cantidad_base', 1)
            
            # Buscar el ingrediente actualizado desde ingredientes.json para obtener precios
            ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre_ing)
            if ingrediente_actualizado:
                precio_extra_ing = ingrediente_actualizado.get('precio_extra', 0.0)
                precio_resta_ing = ingrediente_actualizado.get('precio_resta', 0.0)
            else:
                # Si el ingrediente no existe, mostrar 0.0
                precio_extra_ing = 0.0
                precio_resta_ing = 0.0
            
            self.tree_ingredientes_producto.insert(
                '',
                'end',
                values=(
                    nombre_ing,
                    cantidad_base_ing,
                    f"${precio_extra_ing:.2f}",
                    f"${precio_resta_ing:.2f}"
                )
            )
    
    def agregar_ingrediente_producto(self):
        """Agrega un ingrediente al producto seleccionado"""
        if not self.producto_seleccionado:
            messagebox.showwarning("Advertencia", "Debe seleccionar un producto primero")
            return
        
        producto_id = self.producto_seleccionado['id']
        nombre_ingrediente = self.combo_ingrediente.get()
        cantidad_base = self.entry_cantidad_ing.get()
        
        agregar_ingrediente_a_producto_ui(
            producto_id,
            nombre_ingrediente,
            cantidad_base,
            self.combo_ingrediente,
            self.tree_ingredientes_producto,
            self.entry_cantidad_ing
        )
        
        # Recargar el producto para actualizar los ingredientes
        from utils.productos import buscar_producto_por_id
        resultado = buscar_producto_por_id(producto_id)
        if resultado:
            self.producto_seleccionado = resultado['producto']
            self.cargar_ingredientes_producto()
    
    def eliminar_ingrediente_producto(self):
        """Elimina un ingrediente del producto seleccionado"""
        if not self.producto_seleccionado:
            messagebox.showwarning("Advertencia", "Debe seleccionar un producto primero")
            return
        
        producto_id = self.producto_seleccionado['id']
        eliminar_ingrediente_de_producto_ui(producto_id, self.tree_ingredientes_producto)
        
        # Recargar el producto para actualizar los ingredientes
        from utils.productos import buscar_producto_por_id
        resultado = buscar_producto_por_id(producto_id)
        if resultado:
            self.producto_seleccionado = resultado['producto']
            self.cargar_ingredientes_producto()
    
    def cargar_imagen_producto(self):
        """Abre diálogo para cargar imagen de producto"""
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen del producto",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if ruta:
            try:
                # Validar formato
                from utils.imagenes import validar_formato_imagen
                if not validar_formato_imagen(ruta):
                    messagebox.showerror("Error", "Formato de imagen no permitido")
                    return
                
                # Guardar ruta temporal
                self.ruta_imagen_producto_temp = ruta
                
                # Mostrar preview
                self.mostrar_imagen_producto(ruta, es_ruta_completa=True)
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar imagen: {str(e)}")
    
    def mostrar_imagen_producto(self, ruta_imagen, es_ruta_completa=False):
        """Muestra preview de imagen del producto"""
        if not ruta_imagen:
            self.label_preview_imagen.config(image='', text="Sin imagen")
            self.imagen_preview_producto = None
            return
        
        try:
            # Cargar imagen redimensionada (100x100 para preview)
            if es_ruta_completa:
                imagen_tk = cargar_imagen_tkinter(ruta_imagen, 100, 100)
            else:
                imagen_tk = cargar_imagen_tkinter(ruta_imagen, 100, 100)
            
            if imagen_tk:
                self.label_preview_imagen.config(image=imagen_tk, text='')
                self.imagen_preview_producto = imagen_tk  # Mantener referencia
                # Actualizar scrollregion después de cargar imagen
                if hasattr(self, 'canvas_formulario'):
                    self.canvas_formulario.update_idletasks()
                    self.canvas_formulario.configure(scrollregion=self.canvas_formulario.bbox("all"))
            else:
                self.label_preview_imagen.config(image='', text="Error al cargar")
                self.imagen_preview_producto = None
        except Exception:
            self.label_preview_imagen.config(image='', text="Error al cargar")
            self.imagen_preview_producto = None
    
    def cargar_imagen_ingrediente(self):
        """Abre diálogo para cargar imagen de ingrediente"""
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen del ingrediente",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if ruta:
            try:
                # Validar formato
                from utils.imagenes import validar_formato_imagen
                if not validar_formato_imagen(ruta):
                    messagebox.showerror("Error", "Formato de imagen no permitido")
                    return
                
                # Guardar ruta temporal
                self.ruta_imagen_ingrediente_temp = ruta
                
                # Mostrar preview
                self.mostrar_imagen_ingrediente(ruta, es_ruta_completa=True)
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar imagen: {str(e)}")
    
    def mostrar_imagen_ingrediente(self, ruta_imagen, es_ruta_completa=False):
        """Muestra preview de imagen del ingrediente"""
        if not ruta_imagen:
            self.label_preview_imagen_ing.config(image='', text="Sin imagen")
            self.imagen_preview_ingrediente = None
            return
        
        try:
            # Cargar imagen redimensionada (100x100 para preview)
            if es_ruta_completa:
                imagen_tk = cargar_imagen_tkinter(ruta_imagen, 100, 100)
            else:
                imagen_tk = cargar_imagen_tkinter(ruta_imagen, 100, 100)
            
            if imagen_tk:
                self.label_preview_imagen_ing.config(image=imagen_tk, text='')
                self.imagen_preview_ingrediente = imagen_tk  # Mantener referencia
                # Actualizar scrollregion después de cargar imagen
                if hasattr(self, 'canvas_formulario_ing'):
                    self.canvas_formulario_ing.update_idletasks()
                    self.canvas_formulario_ing.configure(scrollregion=self.canvas_formulario_ing.bbox("all"))
            else:
                self.label_preview_imagen_ing.config(image='', text="Error al cargar")
                self.imagen_preview_ingrediente = None
        except Exception:
            self.label_preview_imagen_ing.config(image='', text="Error al cargar")
            self.imagen_preview_ingrediente = None