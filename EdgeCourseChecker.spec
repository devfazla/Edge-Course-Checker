# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Edge Course Checker (single-file, windowed).
# Build with:  pyinstaller EdgeCourseChecker.spec
# Compatible with PyInstaller 6.x.

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],          # bundle logo.png / icon.ico next to the code
    hiddenimports=[
        'PIL', 'PIL.Image', 'PIL.ImageTk',  # PIL is imported lazily inside functions
        'requests',
    ],
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
    name='EdgeCourseChecker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # windowed app: no black terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
