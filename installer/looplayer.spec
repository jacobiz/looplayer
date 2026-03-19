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
        ('../assets/icon.png', 'assets'),
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
    [],
    exclude_binaries=True,
    name='looplay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='../assets/icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# onedir モード: DLL をインストール先フォルダに固定配置する
# （onefile の %TEMP% 展開 → Defender スキャン → クラッシュ を回避）
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='looplay',
)
