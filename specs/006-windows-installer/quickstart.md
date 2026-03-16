# Quickstart: Windows インストーラのビルドと配布

**Branch**: `006-windows-installer` | **Date**: 2026-03-16

## 実装の全体像

```
looplayer/version.py          # バージョン定数（新規）
installer/looplayer.spec      # PyInstaller 設定（新規）
installer/looplayer.iss       # Inno Setup スクリプト（新規）
installer/build.ps1           # ローカルビルド用スクリプト（新規）
.github/workflows/release.yml # GitHub Actions リリースワークフロー（新規）
```

---

## ステップ 1: バージョン管理ファイルの追加

`looplayer/version.py` を新規作成:

```python
VERSION = "1.0.0"
APP_NAME = "LoopPlayer"
PUBLISHER = "LoopPlayer Project"
```

`looplayer/player.py` のウィンドウタイトルでこれを参照するよう更新。

---

## ステップ 2: VLC プラグインパス修正

`looplayer/player.py` の先頭（imports の後）に追加:

```python
import sys
import os

# バンドルされた exe 実行時に VLC プラグインパスを設定
if getattr(sys, 'frozen', False):
    _vlc_plugins = os.path.join(sys._MEIPASS, 'plugins')
    if os.path.exists(_vlc_plugins):
        os.environ['VLC_PLUGIN_PATH'] = _vlc_plugins
```

---

## ステップ 3: PyInstaller .spec ファイル

`installer/looplayer.spec` を作成:

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

VLC_DIR = Path("C:/Program Files/VideoLAN/VLC")

a = Analysis(
    ['../main.py'],
    pathex=[],
    binaries=[
        (str(VLC_DIR / 'libvlc.dll'), '.'),
        (str(VLC_DIR / 'libvlccore.dll'), '.'),
    ],
    datas=[
        (str(VLC_DIR / 'plugins'), 'plugins'),
    ],
    hiddenimports=['vlc'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='LoopPlayer',
    icon=None,
    console=False,
    onefile=True,
)
```

---

## ステップ 4: Inno Setup スクリプト

`installer/looplayer.iss` を作成（主要部分）:

```ini
[Setup]
AppName=LoopPlayer
AppVersion={#AppVersion}
AppPublisher=LoopPlayer Project
DefaultDirName={localappdata}\LoopPlayer
DefaultGroupName=LoopPlayer
OutputBaseFilename=LoopPlayer-Setup-{#AppVersion}
OutputDir=../dist
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
UninstallDisplayName=LoopPlayer
CreateUninstallRegKey=yes

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "../dist/LoopPlayer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\LoopPlayer"; Filename: "{app}\LoopPlayer.exe"
Name: "{commondesktop}\LoopPlayer"; Filename: "{app}\LoopPlayer.exe"

[Run]
Filename: "{app}\LoopPlayer.exe"; Description: "LoopPlayer を起動する"; \
  Flags: nowait postinstall skipifsilent
```

---

## ステップ 5: GitHub Actions リリースワークフロー

`.github/workflows/release.yml` を新規作成:

```yaml
name: リリース

on:
  push:
    tags:
      - 'v*'

jobs:
  build-and-release:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: VLC・依存パッケージのインストール
        run: |
          choco install vlc --yes --no-progress
          choco install innosetup --yes --no-progress
          pip install -r requirements.txt pyinstaller

      - name: PyInstaller でビルド
        run: |
          $version = "${{ github.ref_name }}".TrimStart('v')
          pyinstaller installer/looplayer.spec

      - name: Inno Setup でインストーラ作成
        run: |
          $version = "${{ github.ref_name }}".TrimStart('v')
          iscc /DAppVersion=$version installer/looplayer.iss

      - name: SHA256 チェックサム生成
        run: |
          $version = "${{ github.ref_name }}".TrimStart('v')
          $hash = (Get-FileHash "dist\LoopPlayer-Setup-$version.exe" -Algorithm SHA256).Hash
          "SHA256: $hash  LoopPlayer-Setup-$version.exe" | Out-File dist\SHA256SUMS.txt

      - name: GitHub Release に公開
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          $version = "${{ github.ref_name }}".TrimStart('v')
          gh release create ${{ github.ref_name }} `
            "dist\LoopPlayer-Setup-$version.exe#LoopPlayer インストーラ (Windows)" `
            "dist\SHA256SUMS.txt#SHA256 チェックサム" `
            --title "LoopPlayer ${{ github.ref_name }}" `
            --generate-release-notes
```

---

## ローカルビルド手順

Windows 環境でのビルド（開発・動作確認用）:

```powershell
# 前提: VLC と Inno Setup がインストール済み
# choco install vlc innosetup

pip install pyinstaller
pyinstaller installer/looplayer.spec
$version = "1.0.0"
iscc /DAppVersion=$version installer/looplayer.iss

# 出力: dist/LoopPlayer-Setup-1.0.0.exe
```

---

## リリース手順

```bash
# バージョンを更新
# looplayer/version.py の VERSION = "x.y.z" を編集

git add looplayer/version.py
git commit -m "chore: バージョンを x.y.z に更新"
git tag vx.y.z
git push origin vx.y.z
# → GitHub Actions が自動でインストーラをビルドして Releases に公開
```

---

## テスト方針

本フィーチャーは CI 環境（Linux）ではなく Windows 実機でのテストが必要。

| テスト項目 | 方法 |
|-----------|------|
| インストーラ動作 | Python 未インストールの Windows 環境で実行 |
| 多言語 UI | 日本語 Windows + 英語 Windows の両方で確認 |
| アンインストール | 「アプリと機能」から実行してファイル消去を確認 |
| ユーザーデータ保持 | アンインストール後 `~/.looplayer/` が残ることを確認 |
| 上書きアップデート | 旧バージョン → 新バージョンのインストーラを順に実行 |
| ロールバック（FR-011） | インストール完了後に `%LOCALAPPDATA%\LoopPlayer` にファイルが存在することを確認。次に別 PC の仮想環境でインストール中にプロセスを強制終了し、`%LOCALAPPDATA%\LoopPlayer` にファイルが残っていないこと（Inno Setup の標準トランザクション機能による自動ロールバック）を確認 |
| ファイルサイズ（SC-002） | `dist/LoopPlayer-Setup-x.x.x.exe` のファイルサイズが 200MB 以下であることを確認（`build.ps1` 実行時に自動表示） |
