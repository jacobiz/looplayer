# Research: プレイヤー UX 改善

**Date**: 2026-03-15
**Branch**: `004-player-ux`

---

## 1. ドラッグ＆ドロップ（PyQt6）

**Decision**: `QMainWindow.setAcceptDrops(True)` + `dragEnterEvent` + `dropEvent` の3点セット。`QDropEvent.mimeData().urls()[0].toLocalFile()` でパス取得。

**Rationale**: PyQt6 標準 API。`hasUrls()` でファイルドロップかどうかを判定し、`isLocalFile()` でローカルファイルのみを許可する。複数ファイルは `urls()[0]` のみ処理。

**実装パターン**:
```python
def dragEnterEvent(self, event):
    if event.mimeData().hasUrls():
        event.acceptProposedAction()
    else:
        event.ignore()

def dropEvent(self, event):
    urls = event.mimeData().urls()
    if urls and urls[0].isLocalFile():
        self._open_path(urls[0].toLocalFile())
```

**注意点**:
- `acceptProposedAction()` を呼ばないと `dropEvent` が発火しない
- `open_file()` を `_open_path(path: str)` に切り出してダイアログ経由とドロップ経由を共通化する
- Windows では `os.path.normpath()` でパス区切りを正規化する

---

## 2. フルスクリーン中カーソル自動非表示（PyQt6）

**Decision**: `setCursor(Qt.CursorShape.BlankCursor)` + `QTimer(3秒)` + `mouseMoveEvent` での `unsetCursor()` リセット。

**Rationale**: `setCursor/unsetCursor` はウィジェット単位でスタック不要。`QApplication.setOverrideCursor()` は管理が複雑なため不採用。

**実装パターン**:
```python
self._cursor_hide_timer = QTimer(self)
self._cursor_hide_timer.setSingleShot(True)
self._cursor_hide_timer.setInterval(3000)
self._cursor_hide_timer.timeout.connect(self._hide_cursor)

def _hide_cursor(self):
    if self.isFullScreen():
        self.setCursor(Qt.CursorShape.BlankCursor)

def _show_cursor(self):
    self.unsetCursor()

def mouseMoveEvent(self, event):
    if self.isFullScreen():
        self._show_cursor()
        self._cursor_hide_timer.start()   # リセット
        if event.pos().y() < 15:
            self.menuBar().show()
            self._menu_hide_timer.start(2000)
    super().mouseMoveEvent(event)
```

**注意点**:
- `toggle_fullscreen()` 内でタイマー起動、`_exit_fullscreen()` 内で `stop()` + `_show_cursor()` を呼ぶ
- `setMouseTracking(True)` は `QMainWindow`・`centralWidget()`・`video_frame` の3層に必要（既存コードで実施済み）
- フルスクリーン解除時に `unsetCursor()` を忘れるとカーソルが非表示のまま通常モードになる

---

## 3. ウィンドウを動画サイズにリサイズ（VLC 非同期問題）

**Decision**: VLC `MediaPlayerVideoChanged` イベント → `pyqtSignal` → 50ms ポーリングタイマーの二段構え。

**Rationale**: `video_get_size()` は VLC の内部デコーダーがフレームを処理するまで `(0, 0)` を返す。`MediaParsedChanged` はメタデータ解析完了であり映像サイズ確定を保証しない。`pyqtSignal` 経由で UI スレッドに渡し、ポーリングで確定を待つパターンが既存コードの `_error_occurred` シグナルと同一構造で安全。

**実装パターン**:
```python
_video_changed = pyqtSignal()   # VLC スレッド → UI スレッド

# __init__ 内
em = self.media_player.event_manager()
em.event_attach(vlc.EventType.MediaPlayerVideoChanged, self._on_vlc_video_changed)
self._video_changed.connect(self._start_size_poll)

self._size_poll_timer = QTimer(self)
self._size_poll_timer.setInterval(50)
self._size_poll_timer.timeout.connect(self._poll_video_size)
self._size_poll_count = 0

def _on_vlc_video_changed(self, _event):
    self._video_changed.emit()

def _start_size_poll(self):
    self._size_poll_count = 0
    self._size_poll_timer.start()

def _poll_video_size(self):
    self._size_poll_count += 1
    if self._size_poll_count > 40:    # 2秒でタイムアウト
        self._size_poll_timer.stop()
        return
    w, h = self.media_player.video_get_size(0)
    if w > 0 and h > 0:
        self._size_poll_timer.stop()
        self._resize_to_video(w, h)
```

**注意点**:
- VLC コールバック内で直接 `resize()` を呼ぶとスレッド違反でクラッシュ（必ず `pyqtSignal` 経由）
- `_resize_to_video` の先頭で `if self.isFullScreen(): return`（フルスクリーン中は `resize()` 無効）
- `video_get_size(0)` の引数はトラックインデックス（省略可能だが明示する）
- `open_file()` 内の `play()` 呼び出し後に `_start_size_poll()` を保険として直接呼ぶ

---

## 4. 最近開いたファイルの永続化

**Decision**: `~/.looplayer/recent_files.json` に JSON 保存。`QSettings` は不採用。

**Rationale**: 既存の `BookmarkStore` と同じ `tmp → replace()` アトミック書き込みパターンを再利用できる。ファイルが直接確認・バックアップできる。`QSettings` はプラットフォームごとに保存先が異なりコンテナ環境での扱いが複雑。

**スキーマ**:
```json
{"files": ["/path/to/video.mp4", "/path/to/other.mkv"]}
```

**メニュー再構築パターン**:
```python
def _rebuild_recent_menu(self) -> None:
    self._recent_menu.clear()
    for path in self._recent.files:
        action = QAction(Path(path).name, self)   # ファイル名のみ
        action.setToolTip(path)                   # フルパスはツールチップ
        action.setData(path)
        action.triggered.connect(lambda checked, p=path: self._open_recent(p))
        self._recent_menu.addAction(action)
```

**注意点**:
- ラムダのキャプチャは `p=path` の形でデフォルト引数に束縛する（Python の late-binding 問題回避）
- ファイル存在チェックは起動時ではなく「開こうとしたとき」に行う（マウント遅延フリーズ防止）
- `_rebuild_recent_menu()` は `open_file()` と `_open_recent()` の末尾で必ず呼ぶ

---

## 5. ブックマーク削除の時限 Undo

**Decision**: `QTimer.singleShot(5000)` + `_pending_delete` dict の1段階 Undo。`QUndoStack` は不採用。

**Rationale**: 「5秒で消える1段階 Undo」に `QUndoStack` は過剰。シンプルなタイマー + dict で十分。`Ctrl+Z` は `QAction` + `ApplicationShortcut` で受け取る。

**`BookmarkPanel` への変更点**:
- `_pending_delete: dict | None` フィールド追加
- `_undo_timer: QTimer` フィールド追加
- `_on_delete()` を「即時削除 → 保留パターン」に変更
- `_commit_delete()` でタイマー満了時に確定
- `_undo_delete()` で `Ctrl+Z` 時に再挿入

**注意点**:
- 連続削除時は前の保留を `_commit_delete()` で強制確定してから新タイマー起動
- `load_video()` 内でも `_commit_delete()` を呼んで動画切り替え時に保留をクリア
- `_store.add()` 後に `update_order()` で元のインデックスを復元する

---

## 6. ブックマーク エクスポート／インポート

**Decision**: 新規 `looplayer/bookmark_io.py` に `export_bookmarks()` / `import_bookmarks()` を実装。

**エクスポートスキーマ**:
```json
{
  "version": 1,
  "exported_at": "2026-03-15T12:00:00+00:00",
  "bookmarks": [
    {"name": "名前", "point_a_ms": 1000, "point_b_ms": 5000, "repeat_count": 1, "order": 0}
  ]
}
```
- `id` はエクスポートに含めない（インポート先で新規 UUID を発行）
- `version` フィールドで将来のスキーマ変更に対応

**重複チェック**: `(point_a_ms, point_b_ms)` ペアの set を使用。インポートファイル内の重複も `add()` 成功後に set へ追加して防止。

**注意点**:
- `int(entry["point_a_ms"])` で型を明示的にキャスト（JSON の `float` 混入対策）
- `store.add()` が `ValueError` を出すケース（A>=B、B>動画長）はスキップ扱い
- エクスポート先に既存ファイルがある場合は上書き確認ダイアログを `QFileDialog.getSaveFileName` が自動表示する
