"""
Funciones auxiliares para gestionar ingredientes en productos
"""
import tkinter as tk
from tkinter import messagebox
from utils.ingredientes import obtener_todos_los_ingredientes, buscar_ingrediente_por_nombre
from utils.productos import agregar_ingrediente_a_producto, eliminar_ingrediente_producto


def cargar_ingredientes_por_categoria(combo, categoria):
    """Carga ingredientes disponibles para una categoría en un combobox"""
    if not categoria:
        combo['values'] = []
        return
    
    todos_ingredientes = obtener_todos_los_ingredientes()
    ingredientes_disponibles = []
    
    for ingrediente in todos_ingredientes:
        categorias = ingrediente.get("categorias", [])
        if categoria in categorias:
            ingredientes_disponibles.append(ingrediente['nombre'])
    
    combo['values'] = ingredientes_disponibles


# La función obtener_ingrediente_por_nombre ahora está en utils.ingredientes como buscar_ingrediente_por_nombre
# Mantener esta función por compatibilidad con código existente
def obtener_ingrediente_por_nombre(nombre):
    """Obtiene un ingrediente por su nombre (wrapper para buscar_ingrediente_por_nombre)"""
    return buscar_ingrediente_por_nombre(nombre)


def agregar_ingrediente_a_producto_ui(producto_id, nombre_ingrediente, cantidad_base, combo, tree, entry_cantidad):
    """Agrega un ingrediente a un producto desde la UI"""
    if not nombre_ingrediente:
        messagebox.showwarning("Advertencia", "Debe seleccionar un ingrediente")
        return
    
    try:
        cantidad_base_int = int(cantidad_base)
        if cantidad_base_int < 0:
            messagebox.showerror("Error", "La cantidad base debe ser mayor o igual a 0")
            return
    except ValueError:
        messagebox.showerror("Error", "La cantidad base debe ser un número válido")
        return
    
    ingrediente = obtener_ingrediente_por_nombre(nombre_ingrediente)
    if not ingrediente:
        messagebox.showerror("Error", "Ingrediente no encontrado")
        return
    
    # Crear estructura de ingrediente para el producto (solo nombre y cantidad_base)
    ingrediente_data = {
        "nombre": ingrediente['nombre'],
        "cantidad_base": cantidad_base_int
    }
    
    # Agregar al producto
    if agregar_ingrediente_a_producto(producto_id, ingrediente_data):
        # Actualizar treeview (mostrar precios desde ingrediente actualizado)
        tree.insert(
            '',
            'end',
            values=(
                ingrediente['nombre'],
                cantidad_base_int,
                f"${ingrediente['precio_extra']:.2f}",
                f"${ingrediente['precio_resta']:.2f}"
            )
        )
        # Limpiar selección
        combo.set('')
        entry_cantidad.delete(0, 'end')
        entry_cantidad.insert(0, "1")
        messagebox.showinfo("Éxito", "Ingrediente agregado al producto")
    else:
        messagebox.showerror("Error", "No se pudo agregar el ingrediente al producto")


def eliminar_ingrediente_de_producto_ui(producto_id, tree):
    """Elimina un ingrediente seleccionado de un producto"""
    seleccion = tree.selection()
    if not seleccion:
        messagebox.showwarning("Advertencia", "Debe seleccionar un ingrediente para eliminar")
        return
    
    item = tree.item(seleccion[0])
    indice = tree.index(seleccion[0])
    
    if eliminar_ingrediente_producto(producto_id, indice):
        tree.delete(seleccion[0])
        messagebox.showinfo("Éxito", "Ingrediente eliminado del producto")
    else:
        messagebox.showerror("Error", "No se pudo eliminar el ingrediente del producto")
