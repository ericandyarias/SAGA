# SAGA - Sistema Administrativo Gastronómico - Arias

Punto de venta para gastronomía (Python + Tkinter).

## Uso

```bash
python main.py
```

## Estructura (qué hace cada cosa)

```
SAGA/
├── main.py                      # Arranca la caja
├── requirements.txt             # Librerías de Python
├── saga.spec                    # Cómo PyInstaller arma el .exe
├── installer_script.iss         # Cómo Inno Setup arma el instalador
├── build_installer_completo.bat # Genera .exe + instalador
├── preparar_datos_instalador.py # Deja data/ virgen para el instalador
├── ui/                          # Pantallas
├── utils/                       # Datos, tickets, rutas
└── data/
    ├── saga.db                  # Base de trabajo (productos, ventas, orden)
    ├── ventas.json              # Solo migración de pedidos viejos
    ├── orden_actual.txt         # Solo migración del número de orden
    ├── config_inicial_bdd/      # Catálogo y config de fábrica (JSON)
    ├── imagenes/                # Fotos de productos e ingredientes
    └── tickets/                 # Copias de texto de tickets impresos
```

Cada archivo de código tiene al inicio un comentario "Propósito".

## Requisitos

- Python 3.7+
- Dependencias en `requirements.txt`
