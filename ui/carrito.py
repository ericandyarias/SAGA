"""
Módulo para el carrito de compras (barra derecha)
Muestra items seleccionados, cantidad, total y botón de confirmación
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import sys
from PIL import Image, ImageTk

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.orden import leer_numero_orden, incrementar_orden
from utils.tickets import generar_tickets_pedido
from utils.productos import calcular_precio_con_ingredientes
from utils.tickets import tiene_modificaciones_reales
from utils.ingredientes import buscar_ingrediente_por_nombre
from utils.imagenes import obtener_ruta_completa_imagen, cargar_imagen_tkinter
from utils.scroll_rueda import habilitar_scroll_rueda, actualizar_region_scroll


class Carrito(ttk.Frame):
    """Frame lateral derecho para el carrito de compras"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.items = []  # Lista de items en el carrito
        self.numero_orden = leer_numero_orden()  # Cargar número de orden
        self.configurar_carrito()
    
    def configurar_carrito(self):
        """Configura el diseño del carrito"""
        # Configurar estilo del frame y grid
        self.config(relief='sunken', borderwidth=2, width=300)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Frame para el encabezado del carrito
        frame_encabezado = ttk.Frame(self)
        frame_encabezado.grid(row=0, column=0, sticky='ew', padx=10, pady=10)
        frame_encabezado.columnconfigure(1, weight=1)
        
        # Título del carrito (izquierda)
        titulo = ttk.Label(
            frame_encabezado,
            text="🛒 Carrito",
            font=('Arial', 14, 'bold')
        )
        titulo.grid(row=0, column=0, sticky='w')
        
        # Número de pedido (derecha)
        self.label_numero_pedido = ttk.Label(
            frame_encabezado,
            text=f"Pedido #{self.numero_orden:04d}",
            font=('Arial', 11, 'bold'),
            foreground='#3498db'
        )
        self.label_numero_pedido.grid(row=0, column=1, sticky='e', padx=10)
        
        # Frame para la lista de items
        frame_lista = ttk.Frame(self)
        frame_lista.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        frame_lista.columnconfigure(0, weight=1)
        frame_lista.rowconfigure(0, weight=1)
        self.frame_lista = frame_lista
        
        # Canvas con scrollbar para items
        canvas = tk.Canvas(frame_lista)
        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=canvas.yview)
        self.frame_items = ttk.Frame(canvas)
        
        self.frame_items.bind(
            "<Configure>",
            lambda e: actualizar_region_scroll(canvas)
        )
        
        # Crear ventana del canvas y configurar para que se expanda
        canvas_window = canvas.create_window((0, 0), window=self.frame_items, anchor="nw")
        
        # Función para ajustar el ancho del frame cuando el canvas cambie de tamaño
        def ajustar_ancho_frame(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
            actualizar_region_scroll(canvas)
        
        canvas.bind('<Configure>', ajustar_ancho_frame)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Guardar referencia al canvas para poder accederlo desde otros métodos
        self.canvas_carrito = canvas
        habilitar_scroll_rueda(frame_lista, canvas)
        
        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Frame para el total
        frame_total = ttk.Frame(self)
        frame_total.grid(row=2, column=0, sticky='ew', padx=10, pady=10)
        frame_total.columnconfigure(0, weight=1)
        
        ttk.Separator(frame_total, orient='horizontal').grid(row=0, column=0, sticky='ew', pady=5)
        
        self.label_total = ttk.Label(
            frame_total,
            text="Total: $0.00",
            font=('Arial', 14, 'bold'),
            foreground='#2c3e50'
        )
        self.label_total.grid(row=1, column=0, pady=5)
        
        # Frame para botones
        frame_botones = ttk.Frame(self)
        frame_botones.grid(row=3, column=0, sticky='ew', padx=10, pady=10)
        frame_botones.columnconfigure(0, weight=1)
        frame_botones.columnconfigure(1, weight=1)
        
        # Botón Borrar Carrito (usando tk.Button para mejor control de hover)
        self.btn_borrar = tk.Button(
            frame_botones,
            text="🗑️ Borrar Todo - (F1)",
            command=self.on_borrar_carrito,
            font=('Arial', 12),
            relief='flat',
            cursor='hand2',
            borderwidth=0,
            compound='left',
            anchor='center'
        )
        self.btn_borrar.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        # Botón Confirmar (usando tk.Button para mejor control de hover)
        self.btn_confirmar = tk.Button(
            frame_botones,
            text="✅ Confirmar Pedido - (F2)",
            command=self.on_confirmar,
            font=('Arial', 12),
            relief='flat',
            cursor='hand2',
            borderwidth=0
        )
        self.btn_confirmar.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Configurar estilos iniciales de los botones
        self.actualizar_estilo_boton_confirmar()
        self.actualizar_estilo_boton_borrar()
        self._registrar_atajos()
        
        # Mostrar mensaje inicial
        self.mostrar_mensaje_vacio()
    
    def _hay_ventana_secundaria(self):
        """True si hay un diálogo o ventana encima (admin, confirmación, etc.)."""
        root = self.winfo_toplevel()
        for w in root.winfo_children():
            try:
                if isinstance(w, tk.Toplevel) and w.winfo_exists() and w.winfo_viewable():
                    return True
            except tk.TclError:
                continue
        return False
    
    def _atajo_borrar(self, event=None):
        if self._hay_ventana_secundaria():
            return
        self.on_borrar_carrito()
        return 'break'
    
    def _atajo_confirmar(self, event=None):
        if self._hay_ventana_secundaria():
            return
        self.on_confirmar()
        return 'break'
    
    def _registrar_atajos(self):
        """F1 borra el pedido y F2 abre confirmar, aunque el foco esté en el buscador."""
        self.bind_all('<F1>', self._atajo_borrar)
        self.bind_all('<F2>', self._atajo_confirmar)
    
    def mostrar_mensaje_vacio(self):
        """Muestra un mensaje cuando el carrito está vacío"""
        for widget in self.frame_items.winfo_children():
            widget.destroy()
        
        mensaje = ttk.Label(
            self.frame_items,
            text="El carrito está vacío\nSelecciona productos para comenzar",
            font=('Arial', 10),
            foreground='gray',
            justify='center'
        )
        mensaje.pack(pady=50)
        
        # Actualizar estilos de los botones cuando está vacío
        self.actualizar_estilo_boton_confirmar()
        self.actualizar_estilo_boton_borrar()
        self.update_idletasks()
        actualizar_region_scroll(self.canvas_carrito)
    
    def agregar_item(self, producto, cantidad=1):
        """Agrega un item al carrito (siempre agrega un nuevo item base)"""
        # Recargar el producto desde el JSON para obtener la versión más actualizada con ingredientes
        from utils.productos import buscar_producto_por_id
        resultado = buscar_producto_por_id(producto['id'])
        if resultado:
            # Usar el producto actualizado del JSON
            producto_actualizado = resultado['producto'].copy()
            producto_actualizado['categoria'] = resultado.get('categoria', '')
        else:
            # Si no se encuentra, usar el producto original pero asegurar que tenga categoría
            producto_actualizado = producto.copy()
            if 'categoria' not in producto_actualizado:
                producto_actualizado['categoria'] = ''
        
        # Siempre agregar un nuevo item base (sin modificaciones)
        # Inicializar modificaciones_ingredientes: dict con {nombre_ingrediente: cantidad_actual}
        modificaciones_ingredientes = {}
        ingredientes = producto_actualizado.get("ingredientes", [])
        for ingrediente in ingredientes:
            nombre = ingrediente.get("nombre", "")
            cantidad_base = ingrediente.get("cantidad_base", 1)
            modificaciones_ingredientes[nombre] = cantidad_base
        
        self.items.append({
            'producto': producto_actualizado,
            'cantidad': cantidad,
            'modificaciones_ingredientes': modificaciones_ingredientes
        })
        self.actualizar_vista()
    
    def eliminar_item(self, item_idx):
        """Elimina un item del carrito por su índice"""
        if 0 <= item_idx < len(self.items):
            self.items.pop(item_idx)
            self.actualizar_vista()
    
    def actualizar_cantidad(self, item_idx, nueva_cantidad):
        """Actualiza la cantidad de un item por su índice"""
        if 0 <= item_idx < len(self.items):
            if nueva_cantidad <= 0:
                self.eliminar_item(item_idx)
            else:
                self.items[item_idx]['cantidad'] = nueva_cantidad
            self.actualizar_vista()
    
    def calcular_total(self):
        """Calcula el total del carrito considerando modificaciones de ingredientes"""
        total = 0
        for item in self.items:
            producto = item['producto']
            cantidad = item['cantidad']
            modificaciones = item.get('modificaciones_ingredientes', {})
            
            # Calcular precio unitario con ingredientes
            precio_unitario = calcular_precio_con_ingredientes(producto, modificaciones)
            total += precio_unitario * cantidad
        return total
    
    def actualizar_estilo_boton_confirmar(self):
        """Actualiza el estilo del botón de confirmar según el estado del carrito"""
        if not self.items or len(self.items) == 0:
            # Carrito vacío: gris con letras blancas
            self.btn_confirmar.config(
                bg='#95a5a6',
                fg='white',
                activebackground='#7f8c8d',
                activeforeground='white'
            )
        else:
            # Carrito con contenido: verde con letras blancas
            self.btn_confirmar.config(
                bg='#27ae60',
                fg='white',
                activebackground='#2ecc71',  # Verde clarito para hover
                activeforeground='white'
            )
        
        # Configurar eventos de hover
        self.configurar_hover_confirmar()
    
    def configurar_hover_confirmar(self):
        """Configura los efectos hover para el botón de confirmar"""
        def on_enter(event):
            if self.items and len(self.items) > 0:
                # Verde clarito cuando hay contenido
                self.btn_confirmar.config(bg='#2ecc71')
            else:
                # Gris más claro cuando está vacío
                self.btn_confirmar.config(bg='#bdc3c7')
        
        def on_leave(event):
            # Restaurar color original
            if self.items and len(self.items) > 0:
                self.btn_confirmar.config(bg='#27ae60')
            else:
                self.btn_confirmar.config(bg='#95a5a6')
        
        self.btn_confirmar.bind('<Enter>', on_enter)
        self.btn_confirmar.bind('<Leave>', on_leave)
    
    def actualizar_estilo_boton_borrar(self):
        """Actualiza el estilo del botón de borrar según el estado del carrito"""
        if not self.items or len(self.items) == 0:
            # Carrito vacío: gris con letras blancas
            self.btn_borrar.config(
                bg='#95a5a6',
                fg='white',
                activebackground='#7f8c8d',
                activeforeground='white'
            )
        else:
            # Carrito con contenido: rojo con letras blancas
            self.btn_borrar.config(
                bg='#e74c3c',
                fg='white',
                activebackground='#ec7063',  # Rojo clarito para hover
                activeforeground='white'
            )
        
        # Configurar eventos de hover
        self.configurar_hover_borrar()
    
    def configurar_hover_borrar(self):
        """Configura los efectos hover para el botón de borrar"""
        def on_enter(event):
            if self.items and len(self.items) > 0:
                # Rojo clarito cuando hay contenido
                self.btn_borrar.config(bg='#ec7063')
            else:
                # Gris más claro cuando está vacío
                self.btn_borrar.config(bg='#bdc3c7')
        
        def on_leave(event):
            # Restaurar color original
            if self.items and len(self.items) > 0:
                self.btn_borrar.config(bg='#e74c3c')
            else:
                self.btn_borrar.config(bg='#95a5a6')
        
        self.btn_borrar.bind('<Enter>', on_enter)
        self.btn_borrar.bind('<Leave>', on_leave)
    
    def actualizar_vista(self):
        """Actualiza la vista del carrito"""
        # Limpiar items actuales
        for widget in self.frame_items.winfo_children():
            widget.destroy()
        
        if not self.items:
            self.mostrar_mensaje_vacio()
            self.label_total.config(text="Total: $0.00")
            self.btn_confirmar.config(state='normal')
            self.actualizar_estilo_boton_confirmar()
            self.actualizar_estilo_boton_borrar()
            return
        
        # Configurar grid del frame de items para que ocupen todo el ancho
        self.frame_items.columnconfigure(0, weight=1)
        
        # Mostrar cada item
        for idx, item in enumerate(self.items):
            frame_item = ttk.Frame(self.frame_items, relief='raised', borderwidth=1)
            frame_item.grid(row=idx, column=0, sticky='ew', padx=5, pady=5)
            frame_item.columnconfigure(0, weight=1)
            
            # Información del producto
            info_frame = ttk.Frame(frame_item)
            info_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
            info_frame.columnconfigure(0, weight=1)
            
            ttk.Label(
                info_frame,
                text=item['producto']['nombre'],
                font=('Arial', 10, 'bold')
            ).grid(row=0, column=0, sticky='w')
            
            # Calcular precio unitario y subtotal considerando ingredientes
            modificaciones = item.get('modificaciones_ingredientes', {})
            precio_unitario = calcular_precio_con_ingredientes(item['producto'], modificaciones)
            subtotal = precio_unitario * item['cantidad']
            
            # Mostrar precio base y ajustes si hay modificaciones
            precio_base = item['producto']['precio']
            fila_precio = 1
            
            # Verificar si hay modificaciones reales (cambios en ingredientes, independientemente del precio)
            tiene_modificaciones = tiene_modificaciones_reales(item['producto'], modificaciones)
            
            # También verificar si hay ingredientes adicionales que no están en el producto
            ingredientes = item['producto'].get('ingredientes', [])
            ingredientes_producto_dict = {ing.get('nombre', '') for ing in ingredientes}
            tiene_ingredientes_adicionales = any(
                nombre_ing not in ingredientes_producto_dict and cantidad_actual > 0
                for nombre_ing, cantidad_actual in modificaciones.items()
            )
            
            if tiene_modificaciones or tiene_ingredientes_adicionales:
                # Mostrar precio según si cambió o no
                if precio_unitario != precio_base:
                    ttk.Label(
                        info_frame,
                        text=f"Base: ${precio_base:.2f} → ${precio_unitario:.2f} x {item['cantidad']} = ${subtotal:.2f}",
                        font=('Arial', 9),
                        foreground='#e67e22'
                    ).grid(row=fila_precio, column=0, sticky='w')
                else:
                    # Precio no cambió pero hay modificaciones (impacto neto = 0)
                    ttk.Label(
                        info_frame,
                        text=f"${precio_unitario:.2f} x {item['cantidad']} = ${subtotal:.2f} (modificado)",
                        font=('Arial', 9),
                        foreground='#e67e22'
                    ).grid(row=fila_precio, column=0, sticky='w')
                
                # Mostrar detalle de ingredientes modificados (extras y quitados)
                fila_detalle = fila_precio + 1
                
                # Importar función para buscar ingrediente por nombre
                from utils.ingredientes import buscar_ingrediente_por_nombre
                
                # Crear diccionario de ingredientes del producto por nombre
                ingredientes_producto_dict = {ing.get('nombre', ''): ing for ing in ingredientes}
                
                # Procesar ingredientes del producto
                for ingrediente in ingredientes:
                    nombre_ing = ingrediente.get('nombre', '')
                    cantidad_base = ingrediente.get('cantidad_base', 1)
                    cantidad_actual = modificaciones.get(nombre_ing, cantidad_base)
                    
                    # Buscar el ingrediente actualizado desde ingredientes.json para obtener precios
                    ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre_ing)
                    if ingrediente_actualizado:
                        precio_extra = ingrediente_actualizado.get('precio_extra', 0.0)
                        precio_resta = ingrediente_actualizado.get('precio_resta', 0.0)
                    else:
                        # Si el ingrediente no existe, usar 0.0
                        precio_extra = 0.0
                        precio_resta = 0.0
                    
                    if cantidad_actual > cantidad_base:
                        # Extras agregados
                        extras = cantidad_actual - cantidad_base
                        precio_total_extra = precio_extra * extras * item['cantidad']
                        if extras > 1:
                            texto_detalle = f"  {extras} Extra {nombre_ing} +${precio_total_extra:.2f}"
                        else:
                            texto_detalle = f"  Extra {nombre_ing} +${precio_total_extra:.2f}"
                        
                        ttk.Label(
                            info_frame,
                            text=texto_detalle,
                            font=('Arial', 8),
                            foreground='#e67e22'
                        ).grid(row=fila_detalle, column=0, sticky='w')
                        fila_detalle += 1
                    elif cantidad_actual < cantidad_base:
                        # Ingredientes quitados
                        quitados = cantidad_base - cantidad_actual
                        precio_total_resta = precio_resta * quitados * item['cantidad']
                        if quitados > 1:
                            texto_detalle = f"  {quitados} Sin {nombre_ing} -${precio_total_resta:.2f}"
                        else:
                            texto_detalle = f"  Sin {nombre_ing} -${precio_total_resta:.2f}"
                        
                        ttk.Label(
                            info_frame,
                            text=texto_detalle,
                            font=('Arial', 8),
                            foreground='#e67e22'
                        ).grid(row=fila_detalle, column=0, sticky='w')
                        fila_detalle += 1
                
                # Procesar ingredientes adicionales que no están en el producto
                for nombre_ing, cantidad_actual in modificaciones.items():
                    if nombre_ing not in ingredientes_producto_dict and cantidad_actual > 0:
                        # Este es un ingrediente adicional que no está en el producto
                        ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre_ing)
                        if ingrediente_actualizado:
                            precio_extra = ingrediente_actualizado.get('precio_extra', 0.0)
                        else:
                            precio_extra = 0.0
                        
                        # Mostrar siempre los ingredientes adicionales si tienen cantidad > 0, independientemente del precio
                        precio_total_extra = precio_extra * cantidad_actual * item['cantidad']
                        if cantidad_actual > 1:
                            if precio_extra > 0:
                                texto_detalle = f"  {cantidad_actual} Extra {nombre_ing} +${precio_total_extra:.2f}"
                            else:
                                texto_detalle = f"  {cantidad_actual} Extra {nombre_ing}"
                        else:
                            if precio_extra > 0:
                                texto_detalle = f"  Extra {nombre_ing} +${precio_total_extra:.2f}"
                            else:
                                texto_detalle = f"  Extra {nombre_ing}"
                        
                        ttk.Label(
                            info_frame,
                            text=texto_detalle,
                            font=('Arial', 8),
                            foreground='#e67e22'
                        ).grid(row=fila_detalle, column=0, sticky='w')
                        fila_detalle += 1
            else:
                ttk.Label(
                    info_frame,
                    text=f"${precio_unitario:.2f} x {item['cantidad']} = ${subtotal:.2f}",
                    font=('Arial', 11),
                    foreground='gray'
                ).grid(row=fila_precio, column=0, sticky='w')
            
            # Controles de cantidad
            controles_frame = ttk.Frame(frame_item)
            controles_frame.grid(row=0, column=1, padx=5, pady=5, sticky='e')
            
            # Usar el índice del item para los callbacks
            item_index = idx
            
            # Botón editar ingredientes (a la izquierda del botón menos)
            # SOLO mostrar el botón si el producto tiene ingredientes definidos
            ingredientes = item['producto'].get('ingredientes', [])
            
            # Obtener categoría del producto si no está en el item (para uso futuro)
            categoria = item['producto'].get('categoria', '')
            if not categoria:
                # Buscar la categoría del producto
                from utils.productos import buscar_producto_por_id
                resultado = buscar_producto_por_id(item['producto']['id'])
                if resultado:
                    categoria = resultado.get('categoria', '')
                    item['producto']['categoria'] = categoria
            
            # SOLO mostrar botón si tiene ingredientes (sin lógica hardcodeada)
            columna_actual = 0
            if ingredientes and len(ingredientes) > 0:
                btn_editar = ttk.Button(
                    controles_frame,
                    text="✏️",
                    width=3,
                    command=lambda idx=item_index: self.editar_ingredientes(idx)
                )
                btn_editar.grid(row=0, column=columna_actual, padx=2)
                columna_actual += 1
            
            # Botón menos - leer cantidad actual desde self.items al ejecutar
            btn_menos = ttk.Button(
                controles_frame,
                text="-",
                width=3,
                command=lambda idx=item_index: self.actualizar_cantidad(idx, self.items[idx]['cantidad'] - 1)
            )
            btn_menos.grid(row=0, column=columna_actual, padx=2)
            columna_actual += 1
            
            ttk.Label(
                controles_frame,
                text=str(item['cantidad']),
                width=3
            ).grid(row=0, column=columna_actual, padx=2)
            columna_actual += 1
            
            # Botón más - leer cantidad actual desde self.items al ejecutar
            btn_mas = ttk.Button(
                controles_frame,
                text="+",
                width=3,
                command=lambda idx=item_index: self.actualizar_cantidad(idx, self.items[idx]['cantidad'] + 1)
            )
            btn_mas.grid(row=0, column=columna_actual, padx=2)
            columna_actual += 1
            
            # Botón eliminar
            btn_eliminar = ttk.Button(
                controles_frame,
                text="🗑️",
                width=3,
                command=lambda idx=item_index: self.eliminar_item(idx)
            )
            btn_eliminar.grid(row=0, column=columna_actual, padx=2)
        
        # Actualizar total
        total = self.calcular_total()
        self.label_total.config(text=f"Total: ${total:.2f}")
        self.btn_confirmar.config(state='normal')
        
        # Actualizar estilos de los botones cuando hay contenido
        self.actualizar_estilo_boton_confirmar()
        self.actualizar_estilo_boton_borrar()
        self.update_idletasks()
        actualizar_region_scroll(self.canvas_carrito)
    
    def editar_ingredientes(self, item_idx):
        """Abre una ventana para editar los ingredientes de un item específico"""
        # Obtener el item por su índice
        if not (0 <= item_idx < len(self.items)):
            return
        
        # Guardar el índice en una variable local para usar en el closure
        item_index = item_idx
        item = self.items[item_index]
        
        # Recargar el producto desde el JSON para obtener ingredientes actualizados
        from utils.productos import buscar_producto_por_id
        resultado = buscar_producto_por_id(item['producto']['id'])
        if resultado:
            # Actualizar el producto en el item con la versión más reciente
            producto_actualizado = resultado['producto']
            self.items[item_index]['producto'] = producto_actualizado
            item = self.items[item_index]  # Actualizar referencia local
            # Si hay nuevos ingredientes, inicializar sus modificaciones
            modificaciones = item.get('modificaciones_ingredientes', {})
            ingredientes_actuales = producto_actualizado.get('ingredientes', [])
            for ingrediente in ingredientes_actuales:
                nombre = ingrediente.get('nombre', '')
                if nombre not in modificaciones:
                    # Inicializar con cantidad_base si es un ingrediente nuevo
                    modificaciones[nombre] = ingrediente.get('cantidad_base', 1)
            self.items[item_index]['modificaciones_ingredientes'] = modificaciones
            item = self.items[item_index]  # Actualizar referencia local
        
        producto = item['producto']
        ingredientes = producto.get('ingredientes', [])
        
        if not ingredientes or len(ingredientes) == 0:
            mensaje = "Este producto no tiene ingredientes configurables.\n\n"
            mensaje += "Para agregar ingredientes a este producto:\n"
            mensaje += "1. Ve al panel de Administración\n"
            mensaje += "2. Selecciona el producto en la pestaña 'Productos'\n"
            mensaje += "3. Asigna ingredientes al producto desde el formulario"
            messagebox.showinfo("Sin Ingredientes", mensaje)
            return
        
        # Crear ventana modal (diseño más simple)
        ventana = tk.Toplevel(self)
        ventana.title(f"Editar Ingredientes - {producto['nombre']}")
        ventana.geometry("850x650")
        ventana.resizable(True, True)
        ventana.transient(self.winfo_toplevel())
        ventana.grab_set()

        # Centrar ventana un poco más a la izquierda
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() // 2) - (ventana.winfo_width() // 2) - 150
        y = (ventana.winfo_screenheight() // 2) - (ventana.winfo_height() // 2)
        ventana.geometry(f"+{x}+{y}")

        # Frame principal
        frame_principal = ttk.Frame(ventana, padding=20)
        frame_principal.pack(fill='both', expand=True)
        frame_principal.columnconfigure(0, weight=1)
        frame_principal.rowconfigure(3, weight=1)  # Área de ingredientes con scroll

        # Título
        ttk.Label(
            frame_principal,
            text="Editar Ingredientes",
            font=('Arial', 14, 'bold')
        ).grid(row=0, column=0, pady=(0, 5))

        ttk.Label(
            frame_principal,
            text=producto['nombre'],
            font=('Arial', 12),
            foreground='gray'
        ).grid(row=1, column=0, pady=(0, 10))

        # Frame para ingredientes con scroll
        frame_scroll = ttk.Frame(frame_principal)
        frame_scroll.grid(row=3, column=0, sticky='nsew', pady=10)
        frame_scroll.columnconfigure(0, weight=1)
        frame_scroll.rowconfigure(0, weight=1)

        canvas_frame = tk.Canvas(frame_scroll)
        scrollbar = ttk.Scrollbar(frame_scroll, orient="vertical", command=canvas_frame.yview)
        frame_ingredientes = ttk.Frame(canvas_frame)

        frame_ingredientes.bind(
            "<Configure>",
            lambda e: canvas_frame.configure(scrollregion=canvas_frame.bbox("all"))
        )

        canvas_window = canvas_frame.create_window((0, 0), window=frame_ingredientes, anchor="nw")

        def ajustar_ancho_frame(event):
            canvas_width = event.width
            canvas_frame.itemconfig(canvas_window, width=canvas_width)

        canvas_frame.bind('<Configure>', ajustar_ancho_frame)
        canvas_frame.configure(yscrollcommand=scrollbar.set)

        canvas_frame.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        # Variables para almacenar las cantidades actuales
        variables_cantidad = {}
        modificaciones_actuales = item.get('modificaciones_ingredientes', {}).copy()
        # Lista para guardar referencias a los traces y poder eliminarlos
        traces_activos = []

        # Frame para precio total (debajo de los ingredientes)
        frame_precio_total = ttk.Frame(frame_principal)
        frame_precio_total.grid(row=4, column=0, sticky='ew', pady=10)

        ttk.Separator(frame_precio_total, orient='horizontal').pack(fill='x', pady=5)

        label_precio_base = ttk.Label(
            frame_precio_total,
            text=f"Precio base: ${producto['precio']:.2f}",
            font=('Arial', 10)
        )
        label_precio_base.pack()

        label_precio_final = ttk.Label(
            frame_precio_total,
            text="",
            font=('Arial', 12, 'bold'),
            foreground='#27ae60'
        )
        label_precio_final.pack()

        # Función para calcular precio total
        def actualizar_precio_total():
            precio_base = producto.get('precio', 0.0)
            ajuste_total = 0.0

            # Crear diccionario de ingredientes del producto por nombre para búsqueda rápida
            ingredientes_producto_dict = {ing.get('nombre', ''): ing for ing in ingredientes}

            for nombre_ing, var in variables_cantidad.items():
                if isinstance(nombre_ing, str):
                    # Buscar si este ingrediente está en el producto
                    ingrediente_producto = ingredientes_producto_dict.get(nombre_ing)
                    
                    if ingrediente_producto:
                        cantidad_base = ingrediente_producto.get('cantidad_base', 1)
                    else:
                        # Si no está en el producto, cantidad_base = 0
                        cantidad_base = 0
                    
                    # Obtener precios desde ingredientes.json
                    ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre_ing)
                    if ingrediente_actualizado:
                        precio_extra = ingrediente_actualizado.get('precio_extra', 0.0)
                        precio_resta = ingrediente_actualizado.get('precio_resta', 0.0)
                    else:
                        precio_extra = 0.0
                        precio_resta = 0.0
                    
                    cantidad_actual = var.get()

                    if cantidad_actual > cantidad_base:
                        extras = cantidad_actual - cantidad_base
                        ajuste_total += extras * precio_extra
                    elif cantidad_actual < cantidad_base:
                        quitados = cantidad_base - cantidad_actual
                        ajuste_total -= quitados * precio_resta

            precio_final = precio_base + ajuste_total
            ajuste = precio_final - precio_base

            if ajuste != 0:
                signo = "+" if ajuste > 0 else ""
                label_precio_final.config(
                    text=f"Precio final: ${precio_final:.2f} ({signo}${ajuste:.2f})"
                )
            else:
                label_precio_final.config(text=f"Precio final: ${precio_final:.2f}")

        # Detectar si hay ingredientes adicionales (que no están en el producto)
        # Si los hay, activar automáticamente "mostrar todos los ingredientes"
        ingredientes_producto_nombres = {ing.get('nombre', '') for ing in ingredientes}
        tiene_ingredientes_adicionales = False
        
        for nombre_ing, cantidad in modificaciones_actuales.items():
            if nombre_ing not in ingredientes_producto_nombres and cantidad > 0:
                tiene_ingredientes_adicionales = True
                break
        
        # Variable para controlar si se muestran todos los ingredientes o solo los del producto
        # Si hay ingredientes adicionales, activar automáticamente
        mostrar_todos_ingredientes = tk.BooleanVar(value=tiene_ingredientes_adicionales)
        
        # Frame para el botón de mostrar todos los ingredientes
        frame_boton_todos = ttk.Frame(frame_principal)
        frame_boton_todos.grid(row=2, column=0, sticky='ew', pady=(0, 5), padx=5)
        
        btn_mostrar_todos = ttk.Button(
            frame_boton_todos,
            text="📋 Mostrar Todos los Ingredientes",
            command=lambda: toggle_mostrar_todos()
        )
        btn_mostrar_todos.pack(side='left')
        
        # Función para actualizar el texto del botón según el estado
        def actualizar_texto_boton():
            if mostrar_todos_ingredientes.get():
                btn_mostrar_todos.config(text="🔒 Mostrar Solo del Producto")
            else:
                btn_mostrar_todos.config(text="📋 Mostrar Todos los Ingredientes")
        
        # Función para alternar entre mostrar todos o solo del producto
        def toggle_mostrar_todos():
            mostrar_todos_ingredientes.set(not mostrar_todos_ingredientes.get())
            actualizar_texto_boton()
            renderizar_ingredientes()
        
        # Actualizar el texto del botón inicialmente
        actualizar_texto_boton()
        
        # Función para renderizar los ingredientes
        def renderizar_ingredientes():
            # Limpiar traces activos antes de destruir widgets
            for var_ref, trace_id in traces_activos:
                try:
                    # Intentar eliminar el trace
                    var_ref.trace_remove('write', trace_id)
                except:
                    pass
            traces_activos.clear()
            
            # Limpiar frame de ingredientes
            for widget in frame_ingredientes.winfo_children():
                widget.destroy()
            
            # Limpiar variables de cantidad anteriores (excepto las que ya existen)
            # Mantener las variables existentes para preservar los valores
            
            # Determinar qué ingredientes mostrar
            ingredientes_a_mostrar = []
            if mostrar_todos_ingredientes.get():
                # Obtener todos los ingredientes de la base de datos
                from utils.ingredientes import obtener_todos_los_ingredientes
                todos_ingredientes_db = obtener_todos_los_ingredientes()
                
                # Crear un diccionario de ingredientes del producto por nombre para búsqueda rápida
                ingredientes_producto_dict = {ing.get('nombre', ''): ing for ing in ingredientes}
                
                # Combinar: primero los del producto, luego los demás
                nombres_ya_agregados = set()
                for ing_producto in ingredientes:
                    ingredientes_a_mostrar.append(ing_producto)
                    nombres_ya_agregados.add(ing_producto.get('nombre', ''))
                
                # Agregar los que no están en el producto (con cantidad_base = 0)
                for ing_db in todos_ingredientes_db:
                    nombre_ing = ing_db.get('nombre', '')
                    if nombre_ing not in nombres_ya_agregados:
                        # Crear un ingrediente con cantidad_base = 0 para los que no están en el producto
                        ing_adicional = {
                            'nombre': nombre_ing,
                            'cantidad_base': 0
                        }
                        ingredientes_a_mostrar.append(ing_adicional)
            else:
                # Mostrar solo los ingredientes del producto
                ingredientes_a_mostrar = ingredientes
            
            # Layout de dos columnas para los ingredientes
            frame_ingredientes.columnconfigure(0, weight=1)
            frame_ingredientes.columnconfigure(1, weight=1)
            
            # Mostrar cada ingrediente
            if not ingredientes_a_mostrar:
                ttk.Label(
                    frame_ingredientes,
                    text="No hay ingredientes disponibles.",
                    font=('Arial', 10),
                    foreground='gray'
                ).grid(row=0, column=0, padx=20, pady=20)
                return
            
            # Crear un mapeo de nombres a índices para preservar variables existentes
            # Usar un identificador único basado en el nombre del ingrediente
            variables_cantidad_por_nombre = {}
            for nombre_ing, var in variables_cantidad.items():
                if isinstance(nombre_ing, str):
                    variables_cantidad_por_nombre[nombre_ing] = var
            
            for idx, ingrediente in enumerate(ingredientes_a_mostrar):
                nombre = ingrediente.get('nombre', '')
                cantidad_base = ingrediente.get('cantidad_base', 0 if mostrar_todos_ingredientes.get() and nombre not in [ing.get('nombre', '') for ing in ingredientes] else ingrediente.get('cantidad_base', 1))
                
                # Obtener precios desde ingredientes.json (no desde el producto)
                ingrediente_actualizado = buscar_ingrediente_por_nombre(nombre)
                if ingrediente_actualizado:
                    precio_extra = ingrediente_actualizado.get('precio_extra', 0.0)
                    precio_resta = ingrediente_actualizado.get('precio_resta', 0.0)
                else:
                    precio_extra = 0.0
                    precio_resta = 0.0

                # Obtener cantidad actual (o base si no hay modificación)
                cantidad_actual = modificaciones_actuales.get(nombre, cantidad_base)
                
                # Si ya existe una variable para este ingrediente, usarla; si no, crear una nueva
                if nombre in variables_cantidad_por_nombre:
                    var_cantidad = variables_cantidad_por_nombre[nombre]
                    var_cantidad.set(cantidad_actual)  # Actualizar el valor
                else:
                    var_cantidad = tk.IntVar(value=cantidad_actual)
                    variables_cantidad_por_nombre[nombre] = var_cantidad
                
                # Guardar usando el nombre como clave para preservar entre renderizados
                variables_cantidad[nombre] = var_cantidad

                # Posición en dos columnas
                fila = idx // 2
                columna = idx % 2

                # Frame para cada ingrediente (diseño simple)
                frame_ing = ttk.LabelFrame(frame_ingredientes, text=nombre, padding=10)
                frame_ing.grid(row=fila, column=columna, sticky='nsew', padx=5, pady=5)
                frame_ing.columnconfigure(2, weight=1)

                # Frame para la imagen del ingrediente (lado izquierdo)
                frame_imagen = ttk.Frame(frame_ing)
                frame_imagen.grid(row=0, column=0, rowspan=3, padx=(0, 10), sticky='ns')
                
                # Cargar imagen del ingrediente
                imagen_ingrediente = None
                if ingrediente_actualizado:
                    ruta_imagen_relativa = ingrediente_actualizado.get('imagen')
                    if ruta_imagen_relativa:
                        ruta_imagen_completa = obtener_ruta_completa_imagen(ruta_imagen_relativa)
                        if ruta_imagen_completa:
                            imagen_ingrediente = cargar_imagen_tkinter(ruta_imagen_completa, 70, 70)
                
                # Si no hay imagen, crear una imagen transparente como placeholder
                if not imagen_ingrediente:
                    # Crear imagen transparente de 70x70 píxeles
                    imagen_transparente = Image.new('RGBA', (70, 70), (255, 255, 255, 0))
                    imagen_ingrediente = ImageTk.PhotoImage(imagen_transparente)
                
                # Label para mostrar la imagen (siempre con imagen, incluso si es transparente)
                label_imagen = ttk.Label(
                    frame_imagen,
                    image=imagen_ingrediente,
                    text="",
                    compound='center',
                    anchor='center'
                )
                label_imagen.pack(expand=True)
                # Mantener referencia a la imagen para evitar que se elimine por el garbage collector
                label_imagen.image = imagen_ingrediente

                # Label cantidad
                ttk.Label(frame_ing, text="Cantidad:").grid(row=0, column=1, padx=5, sticky='w')

                # Frame para controles de cantidad
                frame_controles = ttk.Frame(frame_ing)
                frame_controles.grid(row=0, column=2, sticky='w', padx=5)

                # Botón menos
                btn_menos = ttk.Button(
                    frame_controles,
                    text="-",
                    width=3,
                    command=lambda v=var_cantidad: v.set(max(0, v.get() - 1))
                )
                btn_menos.pack(side='left', padx=2)

                # Label cantidad actual
                label_cantidad = ttk.Label(frame_controles, textvariable=var_cantidad, width=5)
                label_cantidad.pack(side='left', padx=5)

                # Botón más
                btn_mas = ttk.Button(
                    frame_controles,
                    text="+",
                    width=3,
                    command=lambda v=var_cantidad: v.set(v.get() + 1)
                )
                btn_mas.pack(side='left', padx=2)

                # Información de precios
                info_text = f"Base: {cantidad_base}"
                if precio_extra > 0:
                    info_text += f" | Extra: +${precio_extra:.2f}"
                if precio_resta > 0:
                    info_text += f" | Quitar: -${precio_resta:.2f}"

                label_info = ttk.Label(
                    frame_ing,
                    text=info_text,
                    font=('Arial', 8),
                    foreground='black',
                    wraplength=250
                )
                label_info.grid(row=1, column=1, columnspan=2, sticky='ew', padx=5, pady=2)

                # Label impacto en precio
                label_impacto = ttk.Label(frame_ing, text="", font=('Arial', 9, 'bold'))
                label_impacto.grid(row=2, column=1, columnspan=2, sticky='w', padx=5, pady=2)

                # Callback para actualizar impacto y precio total
                def on_cambio_cantidad(*_args,
                                       var_ref=var_cantidad,
                                       label_ref=label_impacto,
                                       base=cantidad_base,
                                       p_extra=precio_extra,
                                       p_resta=precio_resta):
                    try:
                        cantidad = var_ref.get()
                        if cantidad > base:
                            impacto = (cantidad - base) * p_extra
                            label_ref.config(text=f"Impacto: +${impacto:.2f}", foreground='#e67e22')
                        elif cantidad < base:
                            impacto = (base - cantidad) * p_resta
                            label_ref.config(text=f"Impacto: -${impacto:.2f}", foreground='#e67e22')
                        else:
                            label_ref.config(text="", foreground='gray')
                        actualizar_precio_total()
                    except tk.TclError:
                        # El widget fue destruido, ignorar el error
                        pass

                # Vincular cambios de cantidad
                trace_id = var_cantidad.trace_add('write', on_cambio_cantidad)
                traces_activos.append((var_cantidad, trace_id))
                # Inicializar impacto para el estado actual
                try:
                    on_cambio_cantidad()
                except:
                    pass
            
            # Asegurar que el frame_ingredientes tenga el ancho correcto
            frame_ingredientes.update_idletasks()
            canvas_frame.update_idletasks()
            
            # Actualizar precio total después de renderizar
            actualizar_precio_total()
        
        # Renderizar ingredientes inicialmente (solo los del producto)
        renderizar_ingredientes()

        # Frame para botones (simple)
        frame_botones = ttk.Frame(frame_principal)
        frame_botones.grid(row=5, column=0, pady=15)
        # No usar weight para que los botones no se expandan

        # Botón Cancelar
        btn_cancelar = tk.Button(
            frame_botones,
            text="❌ Cancelar",
            command=ventana.destroy,
            width=15,
            bg='#95a5a6',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            activebackground='#7f8c8d',
            activeforeground='white'
        )
        btn_cancelar.pack(side='left', padx=5)
        
        # Botón Guardar/Aceptar
        def guardar_modificaciones():
            # Verificar que el índice sigue siendo válido
            if not (0 <= item_index < len(self.items)):
                ventana.destroy()
                return
            
            # Convertir modificaciones a formato por nombre
            # Crear diccionario de ingredientes del producto por nombre
            ingredientes_producto_dict = {ing.get('nombre', ''): ing for ing in ingredientes}
            modificaciones_por_nombre = {}
            
            for nombre_ing, var in variables_cantidad.items():
                if isinstance(nombre_ing, str):
                    cantidad_actual = var.get()
                    
                    # Solo guardar ingredientes que tienen cantidad diferente a su base
                    # o que están en el producto
                    ingrediente_producto = ingredientes_producto_dict.get(nombre_ing)
                    
                    if ingrediente_producto:
                        cantidad_base = ingrediente_producto.get('cantidad_base', 1)
                        # Guardar siempre los ingredientes del producto
                        modificaciones_por_nombre[nombre_ing] = cantidad_actual
                    else:
                        # Para ingredientes que no están en el producto, solo guardar si cantidad > 0
                        if cantidad_actual > 0:
                            modificaciones_por_nombre[nombre_ing] = cantidad_actual
            
            # Actualizar el item usando el índice para asegurar que es el correcto
            self.items[item_index]['modificaciones_ingredientes'] = modificaciones_por_nombre
            self.actualizar_vista()
            ventana.destroy()
        
        btn_guardar = tk.Button(
            frame_botones,
            text="✅ Aceptar",
            command=guardar_modificaciones,
            width=15,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            activebackground='#2ecc71',
            activeforeground='white'
        )
        btn_guardar.pack(side='left', padx=5)
        
        # Centrar ventana un poco más a la izquierda
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() // 2) - (ventana.winfo_width() // 2) - 150
        y = (ventana.winfo_screenheight() // 2) - (ventana.winfo_height() // 2)
        ventana.geometry(f"+{x}+{y}")
    
    def on_confirmar(self):
        """Callback cuando se confirma el pedido"""
        if not self.items:
            return
        
        # Abrir ventana de confirmación
        self.mostrar_ventana_confirmacion()
    
    def mostrar_ventana_confirmacion(self):
        """Muestra una ventana secundaria para confirmar el pedido"""
        ventana = tk.Toplevel(self)
        ventana.title("Confirmar Pedido")
        ventana.geometry("450x620")
        ventana.resizable(False, False)
        
        # Centrar la ventana
        ventana.transient(self.winfo_toplevel())
        ventana.grab_set()
        
        # Frame principal
        frame_principal = ttk.Frame(ventana, padding=15)
        frame_principal.pack(fill='both', expand=True)
        
        # Título
        ttk.Label(
            frame_principal,
            text="Confirmar Pedido",
            font=('Arial', 16, 'bold')
        ).pack(pady=(0, 5))
        
        # Número de orden
        ttk.Label(
            frame_principal,
            text=f"Orden #{self.numero_orden:04d}",
            font=('Arial', 12, 'bold'),
            foreground='#3498db'
        ).pack(pady=(0, 15))
        
        # Frame para contener cliente y pago lado a lado
        frame_columnas = ttk.Frame(frame_principal)
        frame_columnas.pack(fill='both', expand=True, pady=5)
        frame_columnas.columnconfigure(0, weight=1)
        frame_columnas.columnconfigure(1, weight=1)
        
        # Frame para información del cliente (columna izquierda) - se ajusta dinámicamente
        frame_cliente = ttk.LabelFrame(frame_columnas, text="Datos del Cliente", padding=10)
        frame_cliente.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        
        # Frame para forma de pago (columna derecha) - se ajusta dinámicamente
        frame_pago = ttk.LabelFrame(frame_columnas, text="Método de Pago - (F6)", padding=10)
        frame_pago.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        
        # Campo nombre del cliente
        ttk.Label(frame_cliente, text="Nombre del Cliente:", font=('Arial', 9)).pack(anchor='w', pady=(0, 5))
        entry_nombre = ttk.Entry(frame_cliente, width=30, font=('Arial', 10))
        entry_nombre.pack(fill='x', pady=(0, 15))
        entry_nombre.focus()
        
        # Variable para tipo de pedido (mutuamente excluyentes)
        self.var_tipo_pedido = tk.StringVar(value="Servicio en mesa")
        
        # Frame para opciones de tipo de pedido
        frame_tipo_pedido = ttk.Frame(frame_cliente)
        frame_tipo_pedido.pack(fill='x', pady=(0, 5))
        
        ttk.Label(frame_tipo_pedido, text="Tipo de Pedido - (F5):", font=('Arial', 9)).pack(anchor='w', pady=(0, 5))
        
        # Opciones de tipo de pedido (radiobuttons)
        opciones_tipo = [
            ("Servicio en mesa", "Servicio en mesa"),
            ("Domicilio", "Domicilio"),
            ("Retira en puesto", "Retira en puesto")
        ]
        
        for texto, valor in opciones_tipo:
            ttk.Radiobutton(
                frame_tipo_pedido,
                text=texto,
                variable=self.var_tipo_pedido,
                value=valor,
                command=lambda: self.toggle_tipo_pedido_inputs()
            ).pack(anchor='w', pady=2)
        
        # Frame para input de domicilio (inicialmente oculto)
        frame_domicilio = ttk.Frame(frame_cliente)
        ttk.Label(frame_domicilio, text="Dirección:", font=('Arial', 9)).pack(anchor='w', pady=(5, 5))
        entry_domicilio = ttk.Entry(frame_domicilio, width=30, font=('Arial', 10))
        entry_domicilio.pack(fill='x', pady=(0, 5))
        
        # Campo de hora estimada para domicilio (dos inputs separados)
        frame_hora_estimada = ttk.Frame(frame_domicilio)
        ttk.Label(frame_domicilio, text="Hora estimada (opcional):", font=('Arial', 9)).pack(anchor='w', pady=(5, 5))
        
        entry_hora_estimada_h = ttk.Entry(frame_hora_estimada, width=5, font=('Arial', 10), justify='center')
        entry_hora_estimada_h.pack(side='left')
        ttk.Label(frame_hora_estimada, text=":", font=('Arial', 12, 'bold')).pack(side='left', padx=2)
        entry_hora_estimada_m = ttk.Entry(frame_hora_estimada, width=5, font=('Arial', 10), justify='center')
        entry_hora_estimada_m.pack(side='left')
        
        # Placeholders
        entry_hora_estimada_h.insert(0, "HH")
        entry_hora_estimada_h.config(foreground='gray')
        entry_hora_estimada_m.insert(0, "MM")
        entry_hora_estimada_m.config(foreground='gray')
        
        def on_focus_in_hora_estimada_h(event):
            if entry_hora_estimada_h.get() == "HH":
                entry_hora_estimada_h.delete(0, tk.END)
                entry_hora_estimada_h.config(foreground='black')
        
        def on_focus_out_hora_estimada_h(event):
            valor = entry_hora_estimada_h.get().strip()
            if not valor or valor == "":
                entry_hora_estimada_h.delete(0, tk.END)
                entry_hora_estimada_h.insert(0, "HH")
                entry_hora_estimada_h.config(foreground='gray')
        
        def on_focus_in_hora_estimada_m(event):
            if entry_hora_estimada_m.get() == "MM":
                entry_hora_estimada_m.delete(0, tk.END)
                entry_hora_estimada_m.config(foreground='black')
        
        def on_focus_out_hora_estimada_m(event):
            valor = entry_hora_estimada_m.get().strip()
            if not valor or valor == "":
                entry_hora_estimada_m.delete(0, tk.END)
                entry_hora_estimada_m.insert(0, "MM")
                entry_hora_estimada_m.config(foreground='gray')
        
        # Validar mientras se escribe (solo números)
        def on_keypress_hora_h(event):
            if event.keysym.startswith('F'):
                return
            if event.char.isdigit() or event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Tab', 'Return'):
                return True
            return 'break'
        
        def on_keypress_hora_m(event):
            if event.keysym.startswith('F'):
                return
            if event.char.isdigit() or event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Tab', 'Return'):
                return True
            return 'break'
        
        entry_hora_estimada_h.bind('<KeyPress>', on_keypress_hora_h)
        entry_hora_estimada_h.bind('<FocusIn>', on_focus_in_hora_estimada_h)
        entry_hora_estimada_h.bind('<FocusOut>', on_focus_out_hora_estimada_h)
        
        entry_hora_estimada_m.bind('<KeyPress>', on_keypress_hora_m)
        entry_hora_estimada_m.bind('<FocusIn>', on_focus_in_hora_estimada_m)
        entry_hora_estimada_m.bind('<FocusOut>', on_focus_out_hora_estimada_m)
        
        frame_hora_estimada.pack(anchor='w', pady=(0, 5))
        
        frame_domicilio.pack_forget()
        
        # Frame para input de hora de retiro (inicialmente oculto)
        frame_hora_retiro = ttk.Frame(frame_cliente)
        ttk.Label(frame_hora_retiro, text="Hora estimada (opcional):", font=('Arial', 9)).pack(anchor='w', pady=(5, 5))
        
        frame_hora_retiro_inputs = ttk.Frame(frame_hora_retiro)
        entry_hora_retiro_h = ttk.Entry(frame_hora_retiro_inputs, width=5, font=('Arial', 10), justify='center')
        entry_hora_retiro_h.pack(side='left')
        ttk.Label(frame_hora_retiro_inputs, text=":", font=('Arial', 12, 'bold')).pack(side='left', padx=2)
        entry_hora_retiro_m = ttk.Entry(frame_hora_retiro_inputs, width=5, font=('Arial', 10), justify='center')
        entry_hora_retiro_m.pack(side='left')
        
        # Placeholders
        entry_hora_retiro_h.insert(0, "HH")
        entry_hora_retiro_h.config(foreground='gray')
        entry_hora_retiro_m.insert(0, "MM")
        entry_hora_retiro_m.config(foreground='gray')
        
        def on_focus_in_hora_retiro_h(event):
            if entry_hora_retiro_h.get() == "HH":
                entry_hora_retiro_h.delete(0, tk.END)
                entry_hora_retiro_h.config(foreground='black')
        
        def on_focus_out_hora_retiro_h(event):
            valor = entry_hora_retiro_h.get().strip()
            if not valor or valor == "":
                entry_hora_retiro_h.delete(0, tk.END)
                entry_hora_retiro_h.insert(0, "HH")
                entry_hora_retiro_h.config(foreground='gray')
        
        def on_focus_in_hora_retiro_m(event):
            if entry_hora_retiro_m.get() == "MM":
                entry_hora_retiro_m.delete(0, tk.END)
                entry_hora_retiro_m.config(foreground='black')
        
        def on_focus_out_hora_retiro_m(event):
            valor = entry_hora_retiro_m.get().strip()
            if not valor or valor == "":
                entry_hora_retiro_m.delete(0, tk.END)
                entry_hora_retiro_m.insert(0, "MM")
                entry_hora_retiro_m.config(foreground='gray')
        
        # Validar mientras se escribe (solo números)
        def on_keypress_hora_retiro_h(event):
            if event.keysym.startswith('F'):
                return
            if event.char.isdigit() or event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Tab', 'Return'):
                return True
            return 'break'
        
        def on_keypress_hora_retiro_m(event):
            if event.keysym.startswith('F'):
                return
            if event.char.isdigit() or event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Tab', 'Return'):
                return True
            return 'break'
        
        entry_hora_retiro_h.bind('<KeyPress>', on_keypress_hora_retiro_h)
        entry_hora_retiro_h.bind('<FocusIn>', on_focus_in_hora_retiro_h)
        entry_hora_retiro_h.bind('<FocusOut>', on_focus_out_hora_retiro_h)
        
        entry_hora_retiro_m.bind('<KeyPress>', on_keypress_hora_retiro_m)
        entry_hora_retiro_m.bind('<FocusIn>', on_focus_in_hora_retiro_m)
        entry_hora_retiro_m.bind('<FocusOut>', on_focus_out_hora_retiro_m)
        
        frame_hora_retiro_inputs.pack(anchor='w')
        frame_hora_retiro.pack_forget()
        
        # Guardar referencias para acceso desde callbacks
        self.entry_domicilio = entry_domicilio
        self.entry_hora_retiro_h = entry_hora_retiro_h
        self.entry_hora_retiro_m = entry_hora_retiro_m
        self.entry_hora_estimada_h = entry_hora_estimada_h
        self.entry_hora_estimada_m = entry_hora_estimada_m
        self.frame_domicilio = frame_domicilio
        self.frame_hora_retiro = frame_hora_retiro
        
        # Frame para forma de pago (columna derecha) - ya está creado en frame_columnas
        # Variable para forma de pago
        self.var_forma_pago = tk.StringVar(value="Desconocido")
        
        # Opciones de pago
        opciones_pago = [
            ("Desconocido", "Desconocido"),
            ("Efectivo", "Efectivo"),
            ("Tarjeta", "Tarjeta"),
            ("Transferencia/Qr", "Transferencia/Qr")
        ]
        
        for texto, valor in opciones_pago:
            ttk.Radiobutton(
                frame_pago,
                text=texto,
                variable=self.var_forma_pago,
                value=valor
            ).pack(anchor='w', pady=3)
        
        # Frame para el total
        frame_total = ttk.Frame(frame_principal)
        frame_total.pack(pady=(12, 8))
        
        # Calcular y mostrar el total
        total = self.calcular_total()
        ttk.Label(
            frame_total,
            text=f"Total: ${total:.2f}",
            font=('Arial', 14, 'bold'),
            foreground='#2c3e50'
        ).pack()

        self.var_pedido_prueba = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame_principal,
            text="Pedido de prueba - (F9)",
            variable=self.var_pedido_prueba
        ).pack(pady=(0, 8))
        
        # Frame para botones
        frame_botones = ttk.Frame(frame_principal)
        frame_botones.pack(pady=10)
        
        # Botón Cancelar (usando tk.Button para mejor control de hover) - PRIMERO
        btn_cancelar = tk.Button(
            frame_botones,
            text="Cancelar - (F1)",
            command=ventana.destroy,
            width=18,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10),
            relief='flat',
            cursor='hand2',
            activebackground='#ec7063',
            activeforeground='white'
        )
        btn_cancelar.pack(side='left', padx=5)
        
        # Configurar hover para botón Cancelar (rojo clarito)
        def on_enter_cancelar(event):
            btn_cancelar.config(bg='#ec7063')
        def on_leave_cancelar(event):
            btn_cancelar.config(bg='#e74c3c')
        btn_cancelar.bind('<Enter>', on_enter_cancelar)
        btn_cancelar.bind('<Leave>', on_leave_cancelar)
        
        # Botón Aceptar (usando tk.Button para mejor control de hover) - SEGUNDO
        def aceptar_pedido():
            self.procesar_confirmacion(
                ventana,
                entry_nombre.get(),
                entry_domicilio.get(),
                entry_hora_retiro_h.get(),
                entry_hora_retiro_m.get(),
                entry_hora_estimada_h.get(),
                entry_hora_estimada_m.get()
            )

        btn_aceptar = tk.Button(
            frame_botones,
            text="Aceptar - (F2)",
            command=aceptar_pedido,
            width=18,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10),
            relief='flat',
            cursor='hand2',
            activebackground='#2ecc71',
            activeforeground='white'
        )
        btn_aceptar.pack(side='left', padx=5)
        
        # Configurar hover para botón Aceptar
        def on_enter_aceptar(event):
            btn_aceptar.config(bg='#2ecc71')
        def on_leave_aceptar(event):
            btn_aceptar.config(bg='#27ae60')
        btn_aceptar.bind('<Enter>', on_enter_aceptar)
        btn_aceptar.bind('<Leave>', on_leave_aceptar)

        valores_tipo = [valor for _, valor in opciones_tipo]
        valores_pago = [valor for _, valor in opciones_pago]

        def ciclo_tipo(event=None):
            actual = self.var_tipo_pedido.get()
            i = valores_tipo.index(actual) if actual in valores_tipo else -1
            self.var_tipo_pedido.set(valores_tipo[(i + 1) % len(valores_tipo)])
            self.toggle_tipo_pedido_inputs()
            return 'break'

        def ciclo_pago(event=None):
            actual = self.var_forma_pago.get()
            i = valores_pago.index(actual) if actual in valores_pago else -1
            self.var_forma_pago.set(valores_pago[(i + 1) % len(valores_pago)])
            return 'break'

        def toggle_prueba(event=None):
            self.var_pedido_prueba.set(not self.var_pedido_prueba.get())
            return 'break'

        def on_f1_cancelar(event=None):
            ventana.destroy()
            return 'break'

        def on_f2_aceptar(event=None):
            aceptar_pedido()
            return 'break'

        ventana.bind_all('<F1>', on_f1_cancelar)
        ventana.bind_all('<F2>', on_f2_aceptar)
        ventana.bind_all('<F5>', ciclo_tipo)
        ventana.bind_all('<F6>', ciclo_pago)
        ventana.bind_all('<F9>', toggle_prueba)

        def al_cerrar_confirmacion(event):
            if event.widget is not ventana:
                return
            for tecla in ('<F1>', '<F2>', '<F5>', '<F6>', '<F9>'):
                ventana.unbind_all(tecla)
            self._registrar_atajos()

        ventana.bind('<Destroy>', al_cerrar_confirmacion)
        
        # Inicializar el estado de los inputs según el tipo de pedido por defecto
        self.toggle_tipo_pedido_inputs()
        
        # Centrar la ventana en la pantalla
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() // 2) - (ventana.winfo_width() // 2)
        y = (ventana.winfo_screenheight() // 2) - (ventana.winfo_height() // 2)
        ventana.geometry(f"+{x}+{y}")
    
    def toggle_tipo_pedido_inputs(self):
        """Muestra u oculta los inputs según el tipo de pedido seleccionado"""
        tipo_pedido = self.var_tipo_pedido.get()
        
        # Ocultar todos los frames primero
        self.frame_domicilio.pack_forget()
        self.frame_hora_retiro.pack_forget()
        
        # Mostrar el frame correspondiente según el tipo de pedido
        if tipo_pedido == "Domicilio":
            self.frame_domicilio.pack(fill='x', pady=(5, 0))
        elif tipo_pedido == "Retira en puesto":
            self.frame_hora_retiro.pack(fill='x', pady=(5, 0))
        # "Servicio en mesa" no necesita inputs adicionales
    
    def procesar_confirmacion(self, ventana, nombre_cliente, domicilio, hora_retiro_h, hora_retiro_m, hora_estimada_h, hora_estimada_m):
        """Procesa la confirmación del pedido"""
        # Obtener tipo de pedido seleccionado
        tipo_pedido = self.var_tipo_pedido.get()
        
        # Validar campos según el tipo de pedido
        if tipo_pedido == "Domicilio":
            if not domicilio or not domicilio.strip():
                messagebox.showwarning(
                    "Campo Requerido",
                    "Por favor, ingrese la dirección de entrega."
                )
                return
            domicilio_final = domicilio.strip()
            # La hora estimada no es obligatoria, pero si está ingresada y no es el placeholder, la validamos
            if hora_estimada_h and hora_estimada_h.strip() and hora_estimada_h.strip() != "HH" and \
               hora_estimada_m and hora_estimada_m.strip() and hora_estimada_m.strip() != "MM":
                # Validar horas (00-23)
                try:
                    hora_val = int(hora_estimada_h.strip())
                    if hora_val < 0 or hora_val > 23:
                        messagebox.showwarning(
                            "Hora Inválida",
                            "Las horas deben estar entre 00 y 23."
                        )
                        return
                except ValueError:
                    messagebox.showwarning(
                        "Hora Inválida",
                        "Por favor, ingrese un valor numérico válido para las horas."
                    )
                    return
                
                # Validar minutos (00-59)
                try:
                    minuto_val = int(hora_estimada_m.strip())
                    if minuto_val < 0 or minuto_val > 59:
                        messagebox.showwarning(
                            "Minutos Inválidos",
                            "Los minutos deben estar entre 00 y 59."
                        )
                        return
                except ValueError:
                    messagebox.showwarning(
                        "Minutos Inválidos",
                        "Por favor, ingrese un valor numérico válido para los minutos."
                    )
                    return
                
                hora_estimada_final = f"{hora_estimada_h.strip()}:{hora_estimada_m.strip()}"
            else:
                hora_estimada_final = None
            hora_retiro_final = None
        elif tipo_pedido == "Retira en puesto":
            # La hora no es obligatoria, pero si está ingresada y no es el placeholder, la validamos
            if hora_retiro_h and hora_retiro_h.strip() and hora_retiro_h.strip() != "HH" and \
               hora_retiro_m and hora_retiro_m.strip() and hora_retiro_m.strip() != "MM":
                # Validar horas (00-23)
                try:
                    hora_val = int(hora_retiro_h.strip())
                    if hora_val < 0 or hora_val > 23:
                        messagebox.showwarning(
                            "Hora Inválida",
                            "Las horas deben estar entre 00 y 23."
                        )
                        return
                except ValueError:
                    messagebox.showwarning(
                        "Hora Inválida",
                        "Por favor, ingrese un valor numérico válido para las horas."
                    )
                    return
                
                # Validar minutos (00-59)
                try:
                    minuto_val = int(hora_retiro_m.strip())
                    if minuto_val < 0 or minuto_val > 59:
                        messagebox.showwarning(
                            "Minutos Inválidos",
                            "Los minutos deben estar entre 00 y 59."
                        )
                        return
                except ValueError:
                    messagebox.showwarning(
                        "Minutos Inválidos",
                        "Por favor, ingrese un valor numérico válido para los minutos."
                    )
                    return
                
                hora_retiro_final = f"{hora_retiro_h.strip()}:{hora_retiro_m.strip()}"
            else:
                hora_retiro_final = None
            domicilio_final = None
            hora_estimada_final = None
        else:  # "Servicio en mesa"
            domicilio_final = None
            hora_retiro_final = None
            hora_estimada_final = None
        
        # Obtener forma de pago
        forma_pago = self.var_forma_pago.get()
        
        # Estado de pago por defecto (siempre pendiente)
        estado_pago = "Pendiente de pago"
        
        # Guardar información completa del pedido (para tickets)
        total = self.calcular_total()
        pedido_info = {
            'numero': self.numero_orden,
            # El nombre del cliente ahora es opcional; si viene vacío se guarda como cadena vacía
            'nombre_cliente': nombre_cliente.strip() if nombre_cliente else "",
            'tipo': tipo_pedido,
            'domicilio': domicilio_final,
            'hora_retiro': hora_retiro_final,
            'hora_estimada': hora_estimada_final,
            'forma_pago': forma_pago,
            'estado_pago': estado_pago,
            'items': self.items.copy(),
            'total': total
        }
        cuenta_en_resumen = True
        try:
            cuenta_en_resumen = not bool(self.var_pedido_prueba.get())
        except Exception:
            cuenta_en_resumen = True
        
        # Cerrar ventana de confirmación
        ventana.destroy()
        
        # Generar tickets (COCINA y CLIENTE) e imprimir automáticamente
        # Los tickets se imprimen directamente usando Win32Raw sin previsualización
        try:
            resultado = generar_tickets_pedido(pedido_info, imprimir_automatico=True, guardar_respaldo=True)
            
            # Construir mensaje sobre tickets generados
            if resultado.get('cocina') and resultado.get('cliente'):
                mensaje_tickets = f"\n\nTickets generados:\n• {os.path.basename(resultado['cocina'])}\n• {os.path.basename(resultado['cliente'])}"
            else:
                mensaje_tickets = "\n\nTickets generados"
            
            # Informar sobre el estado de la impresión
            if resultado.get('impresion_cocina') and resultado.get('impresion_cliente'):
                mensaje_tickets += "\n\n✅ Tickets enviados a la impresora"
            elif resultado.get('impresion_cocina') or resultado.get('impresion_cliente'):
                mensaje_tickets += "\n\n⚠ Algunos tickets no se pudieron imprimir"
            else:
                mensaje_tickets += "\n\n⚠ No se pudo imprimir (verifique la impresora)"
        except Exception as e:
            mensaje_tickets = f"\n\n⚠ Error al generar/imprimir tickets: {str(e)}"

        try:
            from utils.ventas import registrar_pedido
            registrar_pedido(pedido_info, cuenta_en_resumen=cuenta_en_resumen)
        except Exception:
            mensaje_tickets += "\n\n⚠ No se pudo guardar en el resumen de ventas"
        
        # Mostrar messagebox
        messagebox.showinfo(
            "Pedido Confirmado",
            f"Pedido #{self.numero_orden:04d} confirmado.\n"
            f"Cliente: {nombre_cliente.strip()}\n"
            f"Total: ${total:.2f}"
            f"{mensaje_tickets}"
        )
        
        # Limpiar el carrito
        self.items = []
        self.actualizar_vista()
        
        # Generar nuevo número de pedido
        self.numero_orden = incrementar_orden()
        self.label_numero_pedido.config(text=f"Pedido #{self.numero_orden:04d}")
        
        # Actualizar estilos de los botones después de limpiar
        self.actualizar_estilo_boton_confirmar()
        self.actualizar_estilo_boton_borrar()
    
    def on_borrar_carrito(self):
        """Callback cuando se quiere borrar todo el carrito"""
        if not self.items:
            return
        
        # Mostrar ventana de confirmación
        self.mostrar_ventana_confirmacion_borrar()
    
    def mostrar_ventana_confirmacion_borrar(self):
        """Muestra una ventana de confirmación para borrar el carrito"""
        ventana = tk.Toplevel(self)
        ventana.title("Confirmar Borrado")
        ventana.geometry("450x200")
        ventana.resizable(False, False)
        
        # Centrar la ventana
        ventana.transient(self.winfo_toplevel())
        ventana.grab_set()
        
        # Frame principal
        frame_principal = ttk.Frame(ventana, padding=30)
        frame_principal.pack(fill='both', expand=True)
        
        # Mensaje de confirmación
        ttk.Label(
            frame_principal,
            text="¿Está seguro de borrar todo el carrito?",
            font=('Arial', 13, 'bold'),
            justify='center'
        ).pack(pady=(10, 5))
        
        ttk.Label(
            frame_principal,
            text="Esta acción no se puede deshacer.",
            font=('Arial', 10),
            foreground='gray',
            justify='center'
        ).pack(pady=(0, 20))
        
        # Frame para botones (centrados y con mejor espaciado)
        frame_botones = ttk.Frame(frame_principal)
        frame_botones.pack(pady=10)
        
        # Botón Cancelar (izquierda)
        btn_cancelar = tk.Button(
            frame_botones,
            text="Cancelar - (F1)",
            command=ventana.destroy,
            width=20,
            bg='#95a5a6',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            activebackground='#7f8c8d',
            activeforeground='white'
        )
        btn_cancelar.pack(side='left', padx=10)
        
        # Configurar hover para botón Cancelar
        def on_enter_cancelar_borrar(event):
            btn_cancelar.config(bg='#bdc3c7')
        def on_leave_cancelar_borrar(event):
            btn_cancelar.config(bg='#95a5a6')
        btn_cancelar.bind('<Enter>', on_enter_cancelar_borrar)
        btn_cancelar.bind('<Leave>', on_leave_cancelar_borrar)
        
        # Botón Confirmar (derecha)
        btn_confirmar = tk.Button(
            frame_botones,
            text="Sí, Borrar - (F2)",
            command=lambda: self.borrar_carrito_completo(ventana),
            width=20,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            activebackground='#ec7063',
            activeforeground='white'
        )
        btn_confirmar.pack(side='left', padx=10)
        
        # Configurar hover para botón Confirmar borrado (rojo clarito)
        def on_enter_confirmar_borrar(event):
            btn_confirmar.config(bg='#ec7063')
        def on_leave_confirmar_borrar(event):
            btn_confirmar.config(bg='#e74c3c')
        btn_confirmar.bind('<Enter>', on_enter_confirmar_borrar)
        btn_confirmar.bind('<Leave>', on_leave_confirmar_borrar)

        def on_f1_cancelar(event=None):
            ventana.destroy()
            return 'break'

        def on_f2_borrar(event=None):
            self.borrar_carrito_completo(ventana)
            return 'break'

        ventana.bind_all('<F1>', on_f1_cancelar)
        ventana.bind_all('<F2>', on_f2_borrar)

        def al_cerrar_dialogo(event):
            if event.widget is not ventana:
                return
            ventana.unbind_all('<F1>')
            ventana.unbind_all('<F2>')
            self._registrar_atajos()

        ventana.bind('<Destroy>', al_cerrar_dialogo)
        
        # Centrar la ventana en la pantalla
        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() // 2) - (ventana.winfo_width() // 2)
        y = (ventana.winfo_screenheight() // 2) - (ventana.winfo_height() // 2)
        ventana.geometry(f"+{x}+{y}")
    
    def borrar_carrito_completo(self, ventana):
        """Borra todo el contenido del carrito"""
        # Limpiar items
        self.items = []
        
        # Actualizar vista
        self.actualizar_vista()
        
        # Cerrar ventana de confirmación
        ventana.destroy()
        
        # Mostrar mensaje de confirmación
        messagebox.showinfo(
            "Carrito Borrado",
            "El carrito ha sido borrado correctamente."
        )
