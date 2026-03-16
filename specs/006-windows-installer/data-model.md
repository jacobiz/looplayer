# Data Model: Windows スタンドアロンアプリ インストーラ

**Branch**: `006-windows-installer` | **Date**: 2026-03-16

## 概要

本フィーチャーのデータモデルは「ビルド成果物」と「インストール状態」の 2 軸で構成される。アプリ本体のデータモデル（LoopBookmark 等）に変更はない。

---

## エンティティ

### 1. インストーラ成果物 (Installer Artifact)

GitHub Releases に添付される配布物。

| 属性 | 説明 | 例 |
|------|------|----|
| `filename` | ファイル名（命名規則: `LoopPlayer-Setup-{version}.exe`） | `LoopPlayer-Setup-1.0.0.exe` |
| `version` | セマンティックバージョン (MAJOR.MINOR.PATCH) | `1.0.0` |
| `target_arch` | ターゲットアーキテクチャ | `win-x64`（固定） |
| `size_bytes` | ファイルサイズ（SC-002: 200MB 以下） | ≤ 209,715,200 bytes |
| `sha256` | SHA256 チェックサム（配布時に添付） | 64文字の16進数文字列 |
| `release_tag` | GitHub Release のタグ | `v1.0.0` |

---

### 2. バージョン情報 (Version Info)

アプリのバージョンを一元管理するファイル。インストーラビルド時・アプリ起動時に参照される。

| 属性 | 説明 | 例 |
|------|------|----|
| `version` | セマンティックバージョン文字列 | `"1.0.0"` |
| `app_name` | アプリ表示名 | `"LoopPlayer"` |
| `publisher` | 発行者名（インストーラに表示） | `"LoopPlayer Project"` |

**ファイル**: `looplayer/version.py`

```python
VERSION = "1.0.0"
APP_NAME = "LoopPlayer"
PUBLISHER = "LoopPlayer Project"
```

---

### 3. インストール状態 (Install State)

Windows レジストリに記録される。Inno Setup が自動管理する。

| レジストリキー | 値 | 説明 |
|--------------|-----|------|
| `DisplayName` | `LoopPlayer` | 「アプリと機能」での表示名 |
| `DisplayVersion` | `1.0.0` | バージョン表示 |
| `Publisher` | `LoopPlayer Project` | 発行者 |
| `InstallLocation` | `%LOCALAPPDATA%\LoopPlayer` | インストール先 |
| `UninstallString` | `{uninstall.exe}` | アンインストール実行パス |
| `EstimatedSize` | （KB 単位） | 推定サイズ |

レジストリパス: `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\LoopPlayer`
（ユーザースコープ。管理者権限不要）

---

### 4. ユーザーデータ (User Data) ※インストーラ管理外

インストーラはこれらのファイルを一切操作しない（保持対象）。

| ファイル | 説明 |
|----------|------|
| `~/.looplayer/bookmarks.json` | ブックマーク（動画パスをキーに保存） |
| `~/.looplayer/recent_files.json` | 最近開いたファイルの履歴 |

---

## ビルド成果物の関係図

```
バージョンタグ (git tag v1.0.0)
        │
        ▼
GitHub Actions (windows-latest)
        │
        ├── PyInstaller
        │       └── dist/VideoPlayer.exe（ポータブル版）
        │
        └── Inno Setup
                └── dist/LoopPlayer-Setup-1.0.0.exe（インストーラ）
                        │
                        ▼
               GitHub Releases
               ├── LoopPlayer-Setup-1.0.0.exe
               └── SHA256SUMS.txt
```

---

## バージョン管理規則

- 形式: `MAJOR.MINOR.PATCH`（セマンティックバージョニング）
- 管理場所: `looplayer/version.py` の `VERSION` 定数
- インストーラ・exe・レジストリ・リリースタグはすべてこの値を参照する
- git タグ形式: `v{VERSION}`（例: `v1.0.0`）
