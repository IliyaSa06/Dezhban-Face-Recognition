# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Dezhban-face-biometric.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\The Arion\\AppData\\Roaming\\Python\\Python310\\site-packages\\face_recognition_models', 'face_recognition_models'), ('C:\\Users\\The Arion\\AppData\\Roaming\\Python\\Python310\\site-packages\\mysql\\connector\\locales', 'mysql/connector/locales')],
    hiddenimports=['mysql.connector.plugins.mysql_native_password', 'mysql.connector.locales.eng.client_error', 'mysql.connector.locales.eng'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Dezhban-face-biometric',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
