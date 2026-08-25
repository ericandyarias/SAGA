"""
Módulo para la barra de navegación lateral izquierda
Contiene los botones principales: Pedidos y Administración
"""
import tkinter as tk
from tkinter import ttk


class Navegador(ttk.Frame):
    """Frame de navegación lateral con botones principales"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.callback_administracion = None
        self.callback_backup = None
        self.seccion_activa = 'pedidos'
        self.configurar_estilos_menu()
        self.configurar_navegador()
    
    def configurar_estilos_menu(self):
        """Estilos del menú: el botón activo se ve más gris."""
        estilo = ttk.Style()
        estilo.configure(
            'MenuActivo.TButton',
            background='#9aa3aa',
            foreground='#1a1a1a',
            lightcolor='#a8b0b6',
            darkcolor='#7a8288',
            bordercolor='#6d757a',
            focuscolor='#9aa3aa',
            font=('Arial', 9, 'bold')
        )
        estilo.map(
            'MenuActivo.TButton',
            background=[
                ('pressed', '#7f878c'),
                ('active', '#8b949a'),
            ],
            foreground=[
                ('pressed', '#1a1a1a'),
                ('active', '#1a1a1a'),
            ]
        )
    
    def marcar_seccion(self, seccion):
        """Resalta solo el botón activo del menú principal."""
        self.seccion_activa = seccion
        botones = {
            'pedidos': self.btn_pedidos,
            'administracion': self.btn_administracion,
            'backup': self.btn_backup,
        }
        for nombre, boton in botones.items():
            if nombre == seccion:
                boton.configure(style='MenuActivo.TButton')
            else:
                boton.configure(style='TButton')
    
    def configurar_navegador(self):
        """Configura el diseño del navegador"""
        # Configurar estilo del frame
        self.config(relief='sunken', borderwidth=2, width=200)
        
        # Título de la sección
        titulo_seccion = ttk.Label(
            self,
            text="Menú Principal",
            font=('Arial', 12, 'bold')
        )
        titulo_seccion.pack(pady=10)
        
        # Botón Pedidos
        self.btn_pedidos = ttk.Button(
            self,
            text="📋 Pedidos",
            width=20,
            command=self.on_pedidos_click
        )
        self.btn_pedidos.pack(pady=10, padx=10)
        
        # Botón Administración
        self.btn_administracion = ttk.Button(
            self,
            text="⚙️ Administración",
            width=20,
            command=self.on_administracion_click
        )
        self.btn_administracion.pack(pady=10, padx=10)
        
        # Botón Hacer Backup
        self.btn_backup = ttk.Button(
            self,
            text="💾 Backup",
            width=20,
            command=self.on_backup_click
        )
        self.btn_backup.pack(pady=10, padx=10)
        
        self.marcar_seccion('pedidos')
        
        # Espaciador
        ttk.Label(self, text="").pack(expand=True)
        
        # Información del desarrollador
        frame_desarrollador = ttk.Frame(self)
        frame_desarrollador.pack(side='bottom', fill='x', pady=10, padx=5)
        
        ttk.Label(
            frame_desarrollador,
            text="Desarrollador:",
            font=('Arial', 8),
            foreground='gray'
        ).pack()
        
        ttk.Label(
            frame_desarrollador,
            text="Eric Andy Arias Rojas",
            font=('Arial', 8, 'bold'),
            foreground='#2c3e50'
        ).pack()
        
        ttk.Label(
            frame_desarrollador,
            text="02478-601418",
            font=('Arial', 8),
            foreground='#2c3e50'
        ).pack(pady=(2, 0))
        
    
    def on_pedidos_click(self):
        """
        Callback cuando se hace clic en Pedidos
        Nota: Actualmente la vista de pedidos es la vista principal
        Este botón está disponible para futuras funcionalidades
        """
        self.marcar_seccion('pedidos')
    
    def on_administracion_click(self):
        """Callback cuando se hace clic en Administración"""
        self.marcar_seccion('administracion')
        if self.callback_administracion:
            self.callback_administracion()
    
    def on_backup_click(self):
        """Callback cuando se hace clic en Hacer Backup"""
        self.marcar_seccion('backup')
        if self.callback_backup:
            self.callback_backup()
        else:
            self.marcar_seccion('pedidos')