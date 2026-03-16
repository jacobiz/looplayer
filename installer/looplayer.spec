# -*- mode: python ; coding: utf-8 -*-
# LoopPlayer PyInstaller ビルド設定
# VLC DLL とプラグインを同梱し、Windows スタンドアロン exe を生成する

from pathlib import Path

# Chocolatey でインストールされた VLC のデフォルトパス
VLC_DIR = Path("C:/Program Files/VideoLAN/VLC")

a = Analysis(
    ['../main.py'],
    pathex=['..'],
    binaries=[
        (str(VLC_DIR / 'libvlc.dll'), '.'),
        (str(VLC_DIR / 'libvlccore.dll'), '.'),
    ],
    datas=[
        (str(VLC_DIR / 'plugins'), 'plugins'),
    ],
    hiddenimports=['vlc'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LoopPlayer',
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
    onefile=True,
)
