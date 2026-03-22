# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Obtener ruta de escpos para incluir archivos de datos
import os
import escpos
escpos_path = os.path.dirname(escpos.__file__)

# Preparar lista de archivos de datos de escpos
escpos_datas = []
for file in os.listdir(escpos_path):
    if file.endswith('.json'):
        source = os.path.join(escpos_path, file)
        dest = 'escpos'  # Se copiará a escpos/ dentro del bundle
        escpos_datas.append((source, dest))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data', 'data'),  # Incluir toda la carpeta data
        ('data/imagenes', 'data/imagenes'),  # Incluir explícitamente las imágenes
    ] + escpos_datas,  # Agregar archivos de datos de escpos
    hiddenimports=[
        'escpos',
        'escpos.printer',
        'escpos.capabilities',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PapuchoFoodtruck',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sin ventana de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Icono Hamburguesa.ico',  # Icono de la aplicación
)
