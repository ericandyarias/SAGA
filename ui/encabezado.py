"""
Módulo para el encabezado de la aplicación
Muestra el título "PAPUCHO FOODTRUCK"
"""
import tkinter as tk
from tkinter import ttk


class Encabezado(ttk.Frame):
    """Frame del encabezado con el título del foodtruck"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.configurar_encabezado()
    
    def configurar_encabezado(self):
        """Configura el diseño del encabezado"""
        # Configurar estilo del frame
        self.config(relief='raised', borderwidth=2)
        
        # Título principal
        titulo = ttk.Label(
            self,
            text="PAPUCHO FOODTRUCK",
            font=('Arial', 20, 'bold'),
            foreground='#2c3e50'
        )
        titulo.pack(pady=10)
        
        # Línea separadora
        separador = ttk.Separator(self, orient='horizontal')
        separador.pack(fill='x', padx=10, pady=3)
