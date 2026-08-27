# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import escpos

escpos_path = os.path.dirname(escpos.__file__)
escpos_datas = []
for file in os.listdir(escpos_path):
    if file.endswith('.json'):
        escpos_datas.append((os.path.join(escpos_path, file), 'escpos'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('data/imagenes', 'data/imagenes'),
        ('Icono Hamburguesa.ico', '.'),
    ] + escpos_datas,
    hiddenimports=[
        'escpos',
        'escpos.printer',
        'escpos.capabilities',
        'win32print',
        'win32gui',
        'win32event',
        'win32api',
        'win32con',
        'pythoncom',
        'qrcode',
        'qrcode.image.pil',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
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
    name='SAGA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Icono Hamburguesa.ico',
)
