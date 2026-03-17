# Contract: Qt シグナル設計

## UpdateChecker（QThread サブクラス）

バックグラウンドでバージョン確認を行うスレッド。

```python
class UpdateChecker(QThread):
    update_available = pyqtSignal(str, str)  # (latest_version, download_url)
    up_to_date       = pyqtSignal()
    check_failed     = pyqtSignal(str)       # error_message
```

### シグナル仕様

| シグナル | 引数 | 発行条件 |
|---------|------|---------|
| `update_available(latest_version, download_url)` | `str, str` | 新バージョンが存在する場合 |
| `up_to_date()` | なし | 最新バージョン使用中の場合 |
| `check_failed(error_message)` | `str` | ネットワークエラー・タイムアウト・パースエラー |

### `update_available` 引数詳細

- `latest_version`: `"v"` プレフィックスなしのバージョン文字列（例: `"1.2.0"`）
- `download_url`: プラットフォーム対応インストーラーの直接 URL（アセットが存在しない場合は空文字列 `""`）

---

## DownloadThread（QThread サブクラス）

インストーラーをバックグラウンドでダウンロードするスレッド。

```python
class DownloadThread(QThread):
    progress = pyqtSignal(int)   # 0-100 (パーセント)
    finished = pyqtSignal(str)   # 保存先パス (絶対パス)
    failed   = pyqtSignal(str)   # エラーメッセージ
```

### シグナル仕様

| シグナル | 引数 | 発行条件 |
|---------|------|---------|
| `progress(percent)` | `int` (0–100) | ダウンロード進行中、都度発行 |
| `finished(path)` | `str` | ダウンロード完了時（保存先絶対パス） |
| `failed(error_message)` | `str` | ネットワークエラー・書き込みエラー |

### キャンセル

`QThread.requestInterruption()` でキャンセルを要求し、ダウンロード側は `self.isInterruptionRequested()` を `reporthook` 内でチェックして中断する。

---

## VideoPlayer 側の接続パターン

### 起動時チェック（サイレント失敗）

```python
checker = UpdateChecker(current_version, parent=self)
checker.update_available.connect(self._on_update_available)
checker.up_to_date.connect(checker.deleteLater)
checker.check_failed.connect(checker.deleteLater)  # サイレント無視
checker.finished.connect(checker.deleteLater)
checker.start()
```

### 手動確認（エラーを表示）

```python
checker = UpdateChecker(current_version, parent=self)
checker.update_available.connect(self._on_update_available)
checker.up_to_date.connect(self._on_up_to_date)
checker.check_failed.connect(self._on_check_failed)  # エラーダイアログ表示
checker.finished.connect(checker.deleteLater)
checker.start()
```
