# Research: 自動更新機能 (010-auto-update)

## 1. バージョン取得・比較

**Decision**: GitHub Releases REST API (`/releases/latest`) + 手動セマンティックバージョン比較  
**Rationale**: 追加ライブラリ不要。`packaging` は pip 経由で利用可能だが、`"1.2.3".split(".")` でタプル整数比較をすれば同等の結果を最小コードで得られる。  
**Alternatives considered**: `packaging.version.Version` （依存追加になる）, `semver` ライブラリ（同上）

### GitHub API

```
GET https://api.github.com/repos/jacobiz/looplayer/releases/latest
Headers: {"User-Agent": "LoopPlayer/{VERSION}"}
Response key fields:
  tag_name: "v1.2.0"     ← "v" prefix 付き
  assets[].name          ← ファイル名でフィルタ
  assets[].browser_download_url
```

**バージョン比較ロジック**:
```python
def _is_newer(current: str, latest: str) -> bool:
    return tuple(int(x) for x in latest.split(".")) > \
           tuple(int(x) for x in current.split("."))
```

## 2. バックグラウンド版チェック（起動ブロックなし）

**Decision**: `QThread` サブクラス `UpdateChecker` でバージョン確認を非同期実行  
**Rationale**: PyQt6 の推奨パターン。`threading.Thread` + `pyqtSignal` でも可だが、`QThread` の方が Qt のライフサイクル管理に統合されやすい。  
**Alternatives considered**: `threading.Thread`（Qt オブジェクトとのスレッド安全性が煩雑）

### シグナル設計

```python
class UpdateChecker(QThread):
    update_available = pyqtSignal(str, str)  # (latest_version, download_url)
    up_to_date       = pyqtSignal()
    check_failed     = pyqtSignal(str)       # error_message (手動確認時のみ使用)
```

## 3. インストーラーダウンロード

**Decision**: `urllib.request.urlretrieve` + `reporthook` コールバックで進捗取得  
**Rationale**: 標準ライブラリのみ。`requests` ライブラリ不要でダウンロード進捗も取得可能。  
**Alternatives considered**: `requests` ライブラリ（依存追加）

### ダウンロード先

```python
import tempfile, pathlib
dest = pathlib.Path(tempfile.gettempdir()) / filename
```

### プラットフォーム別アセット名

| OS | `sys.platform` | アセット名パターン | 起動コマンド |
|----|---------------|-------------------|------------|
| Windows | `"win32"` | `LoopPlayer-Setup-{ver}.exe` | `subprocess.Popen([path])` |
| macOS | `"darwin"` | `LoopPlayer-{ver}.dmg` | `subprocess.Popen(["open", path])` |

## 4. ダウンロード進捗ダイアログ

**Decision**: `QDialog` + `QProgressBar` + `QThread` (`DownloadThread`)  
**Rationale**: UI スレッドに戻してプログレスバーを更新する必要があるため、シグナル経由で安全に実現する。  
**モーダル**: `dialog.exec()` でブロッキング表示（仕様 FR-004 どおり）。

### DownloadThread シグナル設計

```python
class DownloadThread(QThread):
    progress = pyqtSignal(int)   # 0-100
    finished = pyqtSignal(str)   # 保存先パス
    failed   = pyqtSignal(str)   # エラーメッセージ
```

## 5. AppSettings 拡張

**Decision**: `AppSettings` クラスに `check_update_on_startup: bool` プロパティを追加  
**Rationale**: 既存の `~/.looplayer/settings.json` / アトミック保存パターンをそのまま流用できる。新規ファイル不要。  
**既存フィールド**: `end_of_playback_action`

追加キー: `"check_update_on_startup"` (デフォルト: `True`)

## 6. i18n キー追加

既存 `looplayer/i18n.py` の `_STRINGS` 辞書に以下を追加:

| キー | ja | en |
|------|----|----|
| `menu.help.check_update` | 更新を確認... | Check for Updates... |
| `menu.help.auto_check` | 起動時に更新を確認する | Check for Updates on Startup |
| `msg.update_available.title` | 更新があります | Update Available |
| `msg.update_available.body` | バージョン {ver} が利用可能です（現在: {current_ver}）。今すぐダウンロードしますか？ | Version {ver} is available (current: {current_ver}). Download now? |
| `msg.update_latest.title` | 最新バージョンです | Up to Date |
| `msg.update_latest.body` | 最新バージョン {ver} を使用中です。 | You are using the latest version ({ver}). |
| `msg.update_check_failed.title` | 更新確認エラー | Update Check Failed |
| `msg.update_check_failed.body` | 更新確認に失敗しました。インターネット接続を確認してください。 | Failed to check for updates. Please check your internet connection. |
| `msg.update_download_failed.title` | ダウンロードエラー | Download Failed |
| `dialog.download.title` | 更新をダウンロード中... | Downloading Update... |
| `btn.download_now` | 今すぐダウンロード | Download Now |
| `btn.later` | あとで | Later |
| `btn.retry` | 再試行 | Retry |
| `status.update_checking` | 更新を確認中... | Checking for updates... |

## 7. 変更ファイル一覧

| ファイル | 種別 | 変更内容 |
|---------|------|---------|
| `looplayer/updater.py` | 新規 | UpdateChecker, DownloadThread, DownloadDialog |
| `looplayer/app_settings.py` | 変更 | `check_update_on_startup` プロパティ追加 |
| `looplayer/i18n.py` | 変更 | 13 キー追加 |
| `looplayer/player.py` | 変更 | ヘルプメニュー 2 項目追加、起動時チェック呼び出し |
| `tests/unit/test_updater.py` | 新規 | UpdateChecker ・バージョン比較ユニットテスト |
| `tests/integration/test_auto_update.py` | 新規 | メニュー項目・AppSettings 統合テスト |

## 8. タイムアウト・エラー処理

- バージョン確認 HTTP タイムアウト: 5 秒（`urllib.request.urlopen(url, timeout=5)`）
- ダウンロードタイムアウト: 設定しない（大容量ファイルのため）、ユーザーキャンセルで中断
- HTTP 4xx/5xx: 例外として扱い `check_failed` シグナルを発行
- JSON パースエラー: 同上
