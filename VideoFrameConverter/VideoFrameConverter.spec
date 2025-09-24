# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['VideoFrameConverter.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\software\\python\\python3.12.10\\Lib\\site-packages\\cv2\\opencv_videoio_ffmpeg4120_64.dll', 'cv2/')],
    hiddenimports=['tkinterdnd2'],
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
    name='VideoFrameConverter',
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
    icon=['icon.ico'],
)
