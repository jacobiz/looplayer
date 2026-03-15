# Implementation Plan: プレイヤー UX 改善

**Branch**: `004-player-ux` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-player-ux/spec.md`

## Summary

6 つの UX 改善機能（D&D・最近開いたファイル・ウィンドウリサイズ・フルスクリーンカーソル非表示・ブックマーク削除Undo・エクスポート/インポート）を追加する。
既存の `player.py`・`bookmark_panel.py` を中心に拡張し、新規ファイルは `recent_files.py`・`bookmark_io.py` の 2 つに限定する。

## Technical Context

**Language/Version**: Python 3.12.13 + PyQt6 6.10.2, python-vlc 3.0.21203
**Primary Dependencies**: PyQt6（QDrag, QTimer, QCursor, QFileDialog, QAction）, python-vlc（MediaPlayerVideoChanged イベント）
**Storage**: `~/.looplayer/recent_files.json`（新規）, `~/.looplayer/bookmarks.json`（既存・変更なし）
**Testing**: pytest + pytest-qt（pytestqt）
**Target Platform**: Linux / Windows デスクトップ
**Project Type**: desktop-app
**Performance Goals**: ウィンドウリサイズ 100ms 以内（SC-003）、カーソル再表示 100ms 以内（SC-004）
**Constraints**: 最小ウィンドウサイズ 800×600; フルスクリーン中はリサイズ無効
**Scale/Scope**: 6 ユーザーストーリー、新規ファイル 2 本、既存ファイル 2 本の変更

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. テストファースト | ✅ PASS | 各 US に対応するテストファイルを先に作成してから実装する |
| II. シンプルさ重視 | ✅ PASS | QUndoStack 不採用（過剰）; QSettings 不採用（移植性問題）; シンプルな dict + QTimer で十分 |
| III. 過度な抽象化の禁止 | ✅ PASS | `recent_files.py`・`bookmark_io.py` は複数箇所から利用されるため正当化される。新規ヘルパーはこの 2 ファイルのみ |
| IV. 日本語コミュニケーション | ✅ PASS | UIラベル・コメント・エラーメッセージ（ユーザー向け）は日本語で記述 |

*Post-design re-check*: `bookmark_io.py` は `export_bookmarks()` / `import_bookmarks()` の 2 関数のみ。`RecentFiles` クラスは `player.py` から直接利用し、永続化のカプセル化は正当（Constitution II/III に準拠）。

## Project Structure

### Documentation (this feature)

```text
specs/004-player-ux/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
looplayer/
├── player.py                  # 変更: D&D, 最近開いたファイル, リサイズ, カーソル非表示
├── recent_files.py            # 新規: RecentFiles クラス（永続化）
├── bookmark_io.py             # 新規: export_bookmarks() / import_bookmarks()
└── widgets/
    └── bookmark_panel.py      # 変更: 削除Undo (_pending_delete + QTimer)

tests/
├── unit/
│   ├── test_recent_files.py        # 新規: US2 unit
│   ├── test_bookmark_io.py         # 新規: US6 unit
│   └── test_bookmark_undo.py       # 新規: US5 unit (BookmarkPanel)
└── integration/
    ├── test_drag_drop.py           # 新規: US1 integration
    ├── test_recent_files_menu.py   # 新規: US2 integration (menu)
    ├── test_window_resize.py       # 新規: US3 integration
    ├── test_cursor_hide.py         # 新規: US4 integration
    └── test_export_import.py       # 新規: US6 integration
```

**Structure Decision**: 単一プロジェクト構成。新規クラス・関数は `looplayer/` 直下に追加。`widgets/` には UI 固有のコード（BookmarkPanel のみ）。テストは既存の `tests/unit/` + `tests/integration/` 構造を踏襲。

## Architecture Design

### US1: ドラッグ＆ドロップ (`player.py`)

```python
# VideoPlayer.__init__
self.setAcceptDrops(True)

def dragEnterEvent(self, event):
    if event.mimeData().hasUrls():
        event.acceptProposedAction()
    else:
        event.ignore()

def dropEvent(self, event):
    urls = event.mimeData().urls()
    if urls and urls[0].isLocalFile():
        self._open_path(urls[0].toLocalFile())

def _open_path(self, path: str):
    # open_file() のコアロジックを切り出してダイアログ不要化
```

### US2: 最近開いたファイル (`recent_files.py` + `player.py`)

```python
# looplayer/recent_files.py
class RecentFiles:
    MAX = 10
    def __init__(self, storage_path=None): ...
    def add(self, path: str) -> None: ...   # 先頭挿入・重複排除・MAX超過削除
    def remove(self, path: str) -> None: ... # 存在しないファイル選択時
    @property
    def files(self) -> list[str]: ...        # 最新順リスト

# player.py
self._recent = RecentFiles()
self._recent_menu = QMenu("最近開いたファイル")

def _rebuild_recent_menu(self) -> None:
    self._recent_menu.clear()
    for path in self._recent.files:
        action = QAction(Path(path).name, self)
        action.setToolTip(path)
        action.setData(path)
        action.triggered.connect(lambda checked, p=path: self._open_recent(p))
        self._recent_menu.addAction(action)
```

### US3: ウィンドウリサイズ (`player.py`)

```python
_video_changed = pyqtSignal()

# __init__
em = self.media_player.event_manager()
em.event_attach(vlc.EventType.MediaPlayerVideoChanged, self._on_vlc_video_changed)
self._video_changed.connect(self._start_size_poll)
self._size_poll_timer = QTimer(self)
self._size_poll_timer.setInterval(50)
self._size_poll_timer.timeout.connect(self._poll_video_size)

def _resize_to_video(self, w, h):
    if self.isFullScreen():
        return
    # スクリーンサイズ・最小サイズクランプ処理
```

### US4: カーソル非表示 (`player.py`)

```python
self._cursor_hide_timer = QTimer(self)
self._cursor_hide_timer.setSingleShot(True)
self._cursor_hide_timer.setInterval(3000)
self._cursor_hide_timer.timeout.connect(self._hide_cursor)

def _hide_cursor(self):
    if self.isFullScreen():
        self.setCursor(Qt.CursorShape.BlankCursor)

def mouseMoveEvent(self, event):
    if self.isFullScreen():
        self.unsetCursor()
        self._cursor_hide_timer.start()
    super().mouseMoveEvent(event)
```

### US5: ブックマーク削除Undo (`bookmark_panel.py`)

```python
# BookmarkPanel
self._pending_delete: dict | None = None
self._undo_timer = QTimer(self)
self._undo_timer.setSingleShot(True)
self._undo_timer.setInterval(5000)
self._undo_timer.timeout.connect(self._commit_delete)

def _on_delete(self, bookmark_id: str):
    if self._pending_delete:
        self._commit_delete()  # 前の保留を確定
    bm = self._get_bookmark(bookmark_id)
    self._pending_delete = {"bookmark": bm, "original_index": bm.order}
    self._store.delete(self._video_path, bookmark_id)
    self._undo_timer.start()

def _undo_delete(self):
    if not self._pending_delete:
        return
    bm = self._pending_delete["bookmark"]
    idx = self._pending_delete["original_index"]
    self._undo_timer.stop()
    self._pending_delete = None
    self._store.add(self._video_path, bm)
    # update_order で元のインデックスに復元
```

### US6: エクスポート/インポート (`bookmark_io.py` + `player.py`)

```python
# looplayer/bookmark_io.py
def export_bookmarks(bookmarks: list[LoopBookmark], dest_path: str) -> None: ...
def import_bookmarks(src_path: str) -> list[dict]: ...
    # 戻り値は検証済みの dict リスト（LoopBookmark 生成は caller 側）
    # ValueError: 無効 JSON、フォーマット不正
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| `recent_files.py` 新規クラス | 永続化・MAX管理・重複排除のロジックを `player.py` に直接書くと 50行超になり player が肥大化する | `player.py` 直書きは単一責任原則違反で将来のテストが困難 |
| `bookmark_io.py` 新規モジュール | `bookmark_panel.py` や `player.py` に直接書くと UI コードと IO コードが混在する | 分離することでユニットテストが容易になる（UI なしでテスト可能） |
| VLC `pyqtSignal` + ポーリングタイマー | `video_get_size()` は VLC のデコーダー処理完了まで `(0,0)` を返すため非同期処理が必須 | VLC コールバック内で直接 `resize()` を呼ぶとスレッド違反でクラッシュ |
