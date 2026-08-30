# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

root = Path(SPECPATH)

if sys.platform == "win32":
    icon_file = str(root / "assets" / "icon.ico")
elif sys.platform == "darwin":
    icon_file = str(root / "assets" / "icon.icns")
else:
    icon_file = str(root / "assets" / "icon.png")

a = Analysis(
    ["main.py"],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "gui" / "theme.qss"), "gui"),
        (str(root / "assets" / "icon.png"), "assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ZombieSlayer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=(sys.platform == "darwin"),
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="ZombieSlayer.app",
        icon=icon_file,
        bundle_identifier="com.blucorbel.zombieslayer",
        info_plist={
            "NSHighResolutionCapable": "True",
            "CFBundleShortVersionString": "1.0.0",
        },
    )
