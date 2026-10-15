# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'pyqtgraph',
    'serial',
    'serial.tools.list_ports',
    'scipy',
    'scipy.signal',
    'scipy.special',
    'numpy',
    'pandas',
    'neurokit2',
]

# Recolectar datos y módulos de NeuroKit2 y PyQtGraph
nk_datas, nk_binaries, nk_hiddenimports = collect_all('neurokit2')
datas += nk_datas
binaries += nk_binaries
hiddenimports += nk_hiddenimports

pg_datas, pg_binaries, pg_hiddenimports = collect_all('pyqtgraph')
datas += pg_datas
binaries += pg_binaries
hiddenimports += pg_hiddenimports

block_cipher = None

a = Analysis(
    ['app_pyqt6/main.py'],
    pathex=['app_pyqt6', '.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'IPython', 'pytest', 'sphinx'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Configuración Onedir (arranque instantáneo)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Cayetino_ESP32',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Cayetino_ESP32',
)
