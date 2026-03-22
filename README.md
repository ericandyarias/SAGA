# PAPUCHO FOODTRUCK - Sistema de Caja

Sistema de punto de venta (POS) para foodtruck desarrollado con Python y Tkinter (ttk).

## 📁 Estructura del Proyecto

```
caja_foodtruck/
├── main.py                 # Aplicación principal
├── ui/                     # Módulos de interfaz
│   ├── __init__.py
│   ├── encabezado.py       # Header con título
│   ├── navegador.py        # Barra lateral izquierda
│   ├── seleccion.py        # Selección de productos (centro)
│   └── carrito.py          # Items seleccionados + confirmación
└── data/
    └── productos.json      # Datos de productos y categorías
```

## 🚀 Uso

Para ejecutar la aplicación:

```bash
python main.py
```

## 🎨 Componentes

### Encabezado
- Muestra el título "PAPUCHO FOODTRUCK"
- Ubicado en la parte superior de la ventana

### Navegador
- Barra lateral izquierda
- Botones: "Pedidos" y "Administración"
- Navegación principal de la aplicación

### Selección
- Área central para selección de productos
- Buscador de productos
- Botones de categorías
- Lista de productos con botones para agregar

### Carrito
- Barra lateral derecha
- Lista de items seleccionados
- Control de cantidades
- Cálculo de total
- Botones: "Confirmar Pedido" e "Imprimir"

## 📝 Datos

Los productos se cargan desde `data/productos.json` con la siguiente estructura:

```json
{
  "categorias": [
    {
      "nombre": "Categoría",
      "productos": [
        {
          "id": 1,
          "nombre": "Producto",
          "precio": 10.00,
          "descripcion": "Descripción"
        }
      ]
    }
  ]
}
```

## 🔧 Requisitos

- Python 3.7+
- Tkinter (incluido en Python estándar)

## 📌 Estado del Proyecto

- ✅ Estructura inicial completa
- ✅ UI básica funcional
- ⏳ Lógica de negocio (en desarrollo)
- ⏳ Integración con impresora (pendiente)
- ⏳ Módulo de administración (pendiente)
