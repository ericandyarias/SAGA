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
        self.configurar_navegador()
    
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
            text="💾 Hacer Backup",
            width=20,
            command=self.on_backup_click
        )
        self.btn_backup.pack(pady=10, padx=10)
        
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
        # La vista principal ya muestra los pedidos
        # Este método puede ser extendido para navegación futura
        pass
    
    def on_administracion_click(self):
        """Callback cuando se hace clic en Administración"""
        if self.callback_administracion:
            self.callback_administracion()
    
    def on_backup_click(self):
        """Callback cuando se hace clic en Hacer Backup"""
        if self.callback_backup:
            self.callback_backup()