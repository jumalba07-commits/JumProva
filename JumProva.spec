# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

block_cipher = None

# Ruta del icono
icon_path = Path("src/assets/jumprova.ico")

a = Analysis(
    ['src/main.py'],
    pathex=['.'],  # Añadir la ruta actual para que encuentre src
    binaries=[],
    datas=[
        ('src/assets', 'src/assets'),  # Mantener estructura src/assets
    ],
    hiddenimports=[
        'mutagen',
        'mutagen.id3',
        'mutagen.mp3',
        'mutagen.flac',
        'mutagen.ogg',
        'mutagen.wave',
        'mutagen.aac',
        'mutagen.mp4',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL._imaging',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'ctypes',
        'hashlib',
        'shutil',
        'tempfile',
        'threading',
        'datetime',
        're',
        'src',
        'src.gui',
        'src.core',
        'src.config',
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='JumProva',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sin terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['src/assets/jumprova.ico'] if icon_path.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JumProva',
)