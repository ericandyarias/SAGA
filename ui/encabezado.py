"""
Propósito: barra superior de la ventana principal.
Muestra el nombre del local (una línea), leído de la configuración.
"""
import tkinter as tk
from tkinter import ttk

from utils.tickets import obtener_nombre_sistema


class Encabezado(ttk.Frame):
    """Frame del encabezado con el título del sistema"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.label_titulo = None
        self.configurar_encabezado()
    
    def configurar_encabezado(self):
        """Configura el diseño del encabezado"""
        self.config(relief='raised', borderwidth=2)
        
        self.label_titulo = ttk.Label(
            self,
            text=obtener_nombre_sistema(),
            font=('Arial', 16, 'bold'),
            foreground='#2c3e50',
            anchor='center',
            justify='center'
        )
        self.label_titulo.pack(pady=10, fill='x', padx=10)
        self.bind('<Configure>', self._ajustar_titulo)
        
        separador = ttk.Separator(self, orient='horizontal')
        separador.pack(fill='x', padx=10, pady=3)

    def _ajustar_titulo(self, event=None):
        if not self.label_titulo:
            return
        ancho = max(self.winfo_width() - 40, 200)
        self.label_titulo.configure(wraplength=ancho)

    def actualizar_titulo(self, nombre=None):
        """Actualiza el título visible sin recargar la ventana."""
        if not self.label_titulo:
            return
        self.label_titulo.config(text=nombre or obtener_nombre_sistema())
