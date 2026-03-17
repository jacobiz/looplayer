# -*- mode: python ; coding: utf-8 -*-
# LoopPlayer PyInstaller ビルド設定（macOS）
# VLC dylib とプラグインを同梱し、macOS .app バンドルを生成する
# 前提: brew install --cask vlc で VLC.app がインストール済み

from pathlib import Path

# /Applications/VLC.app がインストール済みの場合のパス
VLC_DIR = Path("/Applications/VLC.app/Contents/MacOS")

a = Analysis(
    ['../main.py'],
    pathex=['..'],
    binaries=[
        (str(VLC_DIR / 'lib' / 'libvlc.dylib'), '.'),
        (str(VLC_DIR / 'lib' / 'libvlccore.dylib'), '.'),
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
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='LoopPlayer.app',
    icon=None,
    bundle_identifier='com.looplayer.app',
    argv_emulation=True,
)
