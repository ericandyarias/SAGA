"""
Propósito: dejar data/ virgen antes de armar el instalador.
Conserva el catálogo de fábrica y las imágenes; resetea config, ventas, tickets y saga.db.
Lo llama build_installer_completo.bat.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
CONFIG_INICIAL = os.path.join(DATA, "config_inicial_bdd")
sys.path.insert(0, ROOT)

from utils.tickets import NOMBRE_SISTEMA_DEFAULT


def escribir_json(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
        f.write("\n")


def vaciar_tickets():
    carpeta = os.path.join(DATA, "tickets")
    os.makedirs(carpeta, exist_ok=True)
    for nombre in os.listdir(carpeta):
        ruta = os.path.join(carpeta, nombre)
        if os.path.isfile(ruta):
            os.remove(ruta)


def main():
    os.makedirs(CONFIG_INICIAL, exist_ok=True)

    for obligatorio in ("productos.json", "ingredientes.json"):
        ruta = os.path.join(CONFIG_INICIAL, obligatorio)
        if not os.path.isfile(ruta):
            raise SystemExit(f"Falta config_inicial_bdd/{obligatorio}. No se puede armar el instalador sin el catálogo.")

    escribir_json(os.path.join(CONFIG_INICIAL, "config.json"), {
        "_proposito": "Config de fábrica: impresora 80 mm, opciones de ticket y nombre del local.",
        "impresora": {
            "ancho_ticket": 80,
            "modelo": "Térmica 80mm",
            "nombre_impresora": ""
        },
        "tickets": {
            "incluir_fecha_hora": True,
            "lineas_corte": 3,
            "enlace_qr": ""
        },
        "sistema": {
            "nombre": NOMBRE_SISTEMA_DEFAULT
        }
    })
    escribir_json(os.path.join(DATA, "ventas.json"), {
        "_proposito": "Semilla vacía de ventas JSON para el instalador (migración a SQLite).",
        "pedidos": [],
    })

    with open(os.path.join(DATA, "orden_actual.txt"), "w", encoding="utf-8") as f:
        f.write("# Propósito: número de orden de instalaciones viejas. El valor real está en saga.db.\n")
        f.write("1\n")

    for nombre_db in ("saga.db", "saga.db-wal", "saga.db-shm"):
        ruta_db = os.path.join(DATA, nombre_db)
        if os.path.isfile(ruta_db):
            os.remove(ruta_db)

    vaciar_tickets()
    os.makedirs(os.path.join(DATA, "imagenes", "productos"), exist_ok=True)
    os.makedirs(os.path.join(DATA, "imagenes", "ingredientes"), exist_ok=True)

    print("Datos vírgenes listos para el instalador.")
    print("Se conservaron productos, ingredientes, precios e imágenes.")
    print("Se resetearon config, ventas, tickets, número de orden y saga.db.")


if __name__ == "__main__":
    main()
