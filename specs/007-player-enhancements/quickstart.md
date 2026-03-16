# Quickstart: プレイヤー機能強化

**Branch**: `007-player-enhancements` | **Date**: 2026-03-16

## 実装の全体像

```text
looplayer/playback_position.py   # 新規: PlaybackPosition クラス
looplayer/app_settings.py        # 新規: AppSettings クラス
looplayer/playlist.py            # 新規: Playlist クラス
looplayer/bookmark_store.py      # 変更: LoopBookmark.notes フィールド追加
looplayer/bookmark_io.py         # 変更: notes の export/import 対応
looplayer/player.py              # 変更: 全 US の統合（最大の変更ファイル）
looplayer/widgets/bookmark_row.py   # 変更: メモボタン追加
looplayer/widgets/bookmark_panel.py # 変更: メモダイアログ連携
```

---

## US1: 精細な再生操作

### ステップ 1: 速度ショートカット `[` `]`

`player.py` の `_build_ui()` 内でショートカット追加:

```python
# 既存の速度リストを定数として定義
_PLAYBACK_RATES = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

# QShortcut で追加
QShortcut(QKeySequence("]"), self).activated.connect(self._speed_up)
QShortcut(QKeySequence("["), self).activated.connect(self._speed_down)

def _speed_up(self):
    rates = _PLAYBACK_RATES
    idx = rates.index(self._playback_rate) if self._playback_rate in rates else -1
    if idx < len(rates) - 1:
        self._set_playback_rate(rates[idx + 1])
    else:
        self.statusBar().showMessage("最大速度です", 2000)

def _speed_down(self):
    rates = _PLAYBACK_RATES
    idx = rates.index(self._playback_rate) if self._playback_rate in rates else len(rates)
    if idx > 0:
        self._set_playback_rate(rates[idx - 1])
    else:
        self.statusBar().showMessage("最小速度です", 2000)
```

### ステップ 2: 精細シーク（±1秒・±10秒）

既存の `_seek_relative(ms)` メソッドを使って追加:

```python
# _build_ui() 内
QShortcut(QKeySequence("Shift+Right"), self).activated.connect(lambda: self._seek_relative(1000))
QShortcut(QKeySequence("Shift+Left"),  self).activated.connect(lambda: self._seek_relative(-1000))
QShortcut(QKeySequence("Ctrl+Right"),  self).activated.connect(lambda: self._seek_relative(10000))
QShortcut(QKeySequence("Ctrl+Left"),   self).activated.connect(lambda: self._seek_relative(-10000))
```

### ステップ 3: フレームコマ送り（`.` と `,`）

```python
QShortcut(QKeySequence("."), self).activated.connect(self._frame_forward)
QShortcut(QKeySequence(","), self).activated.connect(self._frame_backward)

def _frame_forward(self):
    if self.media_player.is_playing():
        self.media_player.pause()
    self.media_player.next_frame()

def _frame_backward(self):
    if self.media_player.is_playing():
        self.media_player.pause()
    fps = self.media_player.get_fps()
    frame_ms = int(1000.0 / fps) if fps > 0 else 40  # フォールバック: 25fps
    t = self.media_player.get_time()
    self.media_player.set_time(max(0, t - frame_ms))
```

---

## US2: マルチトラック対応

### メニュー構成

```python
# _build_menu() 内
self._audio_track_menu = play_menu.addMenu("音声トラック(&A)")
self._subtitle_menu    = play_menu.addMenu("字幕(&S)")

# aboutToShow でリアルタイム更新
self._audio_track_menu.aboutToShow.connect(self._rebuild_audio_track_menu)
self._subtitle_menu.aboutToShow.connect(self._rebuild_subtitle_menu)
```

### トラックメニューの再構築

```python
def _rebuild_audio_track_menu(self):
    self._audio_track_menu.clear()
    descs = self.media_player.audio_get_track_description() or []
    # descs = [(id, name), ...]。トラックが 1 種類以下はグレーアウト
    group = QActionGroup(self)
    group.setExclusive(True)
    for track_id, name in descs:
        action = QAction(name.decode() if isinstance(name, bytes) else name, self)
        action.setCheckable(True)
        action.setChecked(self.media_player.audio_get_track() == track_id)
        action.triggered.connect(lambda _, tid=track_id: self.media_player.audio_set_track(tid))
        group.addAction(action)
        self._audio_track_menu.addAction(action)
    self._audio_track_menu.setEnabled(len(descs) > 1)

def _rebuild_subtitle_menu(self):
    self._subtitle_menu.clear()
    descs = self.media_player.video_get_spu_description() or []
    group = QActionGroup(self)
    group.setExclusive(True)
    # 「字幕なし」オプション（track_id = -1）
    off_action = QAction("字幕なし", self)
    off_action.setCheckable(True)
    off_action.setChecked(self.media_player.video_get_spu() == -1)
    off_action.triggered.connect(lambda: self.media_player.video_set_spu(-1))
    group.addAction(off_action)
    self._subtitle_menu.addAction(off_action)
    for track_id, name in descs:
        action = QAction(name.decode() if isinstance(name, bytes) else name, self)
        action.setCheckable(True)
        action.setChecked(self.media_player.video_get_spu() == track_id)
        action.triggered.connect(lambda _, tid=track_id: self.media_player.video_set_spu(tid))
        group.addAction(action)
        self._subtitle_menu.addAction(action)
    self._subtitle_menu.setEnabled(bool(descs))
```

---

## US3: スクリーンショット

```python
from datetime import datetime

def _take_screenshot(self):
    if not self._current_path:
        return
    desktop = Path.home() / "Desktop"
    save_dir = desktop if desktop.exists() else Path.home()
    filename = f"LoopPlayer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = save_dir / filename
    self.media_player.video_take_snapshot(0, str(path), 0, 0)
    self.statusBar().showMessage(f"保存しました: {path}", 3000)
```

メニュー追加:
```python
screenshot_action = QAction("スクリーンショット(&P)", self)
screenshot_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
screenshot_action.triggered.connect(self._take_screenshot)
self._screenshot_action = screenshot_action  # グレーアウト制御のために保持
file_menu.addAction(screenshot_action)
```

---

## US4: 再生終了時の動作

### AppSettings モジュール

`looplayer/app_settings.py`:

```python
import json
from pathlib import Path

_SETTINGS_PATH = Path.home() / ".looplayer" / "settings.json"
_VALID_ACTIONS = ("stop", "rewind", "loop")

class AppSettings:
    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        try:
            return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def save(self) -> None:
        _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _SETTINGS_PATH.with_suffix(".json.tmp")
        try:
            tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(_SETTINGS_PATH)
        except OSError:
            tmp.unlink(missing_ok=True)
            raise

    @property
    def end_of_playback_action(self) -> str:
        val = self._data.get("end_of_playback_action", "stop")
        return val if val in _VALID_ACTIONS else "stop"

    @end_of_playback_action.setter
    def end_of_playback_action(self, value: str) -> None:
        if value not in _VALID_ACTIONS:
            raise ValueError(f"Invalid action: {value}")
        self._data["end_of_playback_action"] = value
        self.save()
```

### player.py での統合

```python
# 終了イベントハンドラ
def _handle_playback_ended(self):
    # プレイリスト有効 → 次のファイルへ
    if self._playlist and self._playlist.has_next():
        self._playlist.advance()
        self._open_path(str(self._playlist.current()))
        return
    # ABループ有効 → _on_timer が制御するため何もしない
    if self._ab_loop_enabled:
        return
    action = self._app_settings.end_of_playback_action
    if action == "rewind":
        self.media_player.stop()
        self.media_player.set_time(0)
        self._update_seek_ui()
    elif action == "loop":
        self.media_player.stop()
        self.media_player.play()
    # "stop" は VLC が自動的に停止するため何もしない
```

---

## US5: 再生位置の記憶

### PlaybackPosition モジュール

`looplayer/playback_position.py`:

```python
import json
from pathlib import Path

_PATH = Path.home() / ".looplayer" / "positions.json"
_MAX_ENTRIES = 10

class PlaybackPosition:
    def __init__(self):
        self._data: dict[str, int] = self._load()

    def _load(self) -> dict:
        try:
            data = json.loads(_PATH.read_text(encoding="utf-8"))
            return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, int)}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def _save(self) -> None:
        _PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _PATH.with_suffix(".json.tmp")
        try:
            tmp.write_text(json.dumps(self._data, ensure_ascii=False), encoding="utf-8")
            tmp.replace(_PATH)
        except OSError:
            tmp.unlink(missing_ok=True)

    def save(self, filepath: str, position_ms: int, duration_ms: int) -> None:
        # 保存しない条件
        if duration_ms <= 0:
            return
        if position_ms < 5000:                              # 5 秒未満
            return
        if position_ms / duration_ms >= 0.95:              # 95% 以上
            self._data.pop(filepath, None)
            self._save()
            return
        # 上限管理: 先頭（最古）エントリを削除
        if filepath in self._data:
            del self._data[filepath]
        while len(self._data) >= _MAX_ENTRIES:
            oldest_key = next(iter(self._data))
            del self._data[oldest_key]
        self._data[filepath] = position_ms
        self._save()

    def load(self, filepath: str) -> int | None:
        if not Path(filepath).exists():
            return None
        return self._data.get(filepath)
```

---

## US6: ブックマークメモ

### LoopBookmark への notes 追加

`bookmark_store.py` の `LoopBookmark` に `notes: str = ""` を追加。`_save_all()` / `_load_all()` は `asdict()` を使っているため自動的に対応。ただし `_load_all()` のデシリアライズ箇所で `notes` がない旧データへのフォールバックを確認する:

```python
# bookmark_store.py の _load_all() 内
bm = LoopBookmark(
    point_a_ms=raw["point_a_ms"],
    point_b_ms=raw["point_b_ms"],
    name=raw.get("name", ""),
    repeat_count=raw.get("repeat_count", 1),
    order=raw.get("order", 0),
    id=raw.get("id", str(uuid.uuid4())),
    enabled=raw.get("enabled", True),
    notes=raw.get("notes", ""),   # ← 追加
)
```

### BookmarkRow へのメモボタン追加

`bookmark_row.py` の `_build()` に追加:

```python
self.memo_btn = QPushButton("✎")
self.memo_btn.setFixedSize(24, 24)
self.memo_btn.setToolTip("メモ")
self.memo_btn.clicked.connect(lambda: self.memo_clicked.emit(self.bookmark_id))
layout.addWidget(self.memo_btn)
```

シグナルに `memo_clicked = pyqtSignal(str)` を追加（bookmark_id を渡す）。

---

## US7: フォルダドロップでプレイリスト

### Playlist モジュール

`looplayer/playlist.py`:

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class Playlist:
    files: list[Path]
    index: int = 0

    def current(self) -> Path:
        return self.files[self.index]

    def has_next(self) -> bool:
        return self.index + 1 < len(self.files)

    def advance(self) -> bool:
        if self.has_next():
            self.index += 1
            return True
        return False

    def __len__(self) -> int:
        return len(self.files)
```

### dropEvent の拡張

```python
_SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"}

def dropEvent(self, event: QDropEvent):
    for url in event.mimeData().urls():
        if not url.isLocalFile():
            continue
        local = Path(url.toLocalFile())
        if local.is_dir():
            self._open_folder(local)
            return
        if local.suffix.lower() in _SUPPORTED_EXTENSIONS:
            self._playlist = None   # プレイリスト解除
            self._open_path(str(local))
            return

def _open_folder(self, folder: Path):
    files = sorted(
        p for p in folder.iterdir()
        if not p.name.startswith('.') and p.suffix.lower() in _SUPPORTED_EXTENSIONS
    )
    if not files:
        QMessageBox.warning(self, "エラー", "対応する動画ファイルが見つかりませんでした。")
        return
    if len(files) == 1:
        self._playlist = None
        self._open_path(str(files[0]))
        return
    from looplayer.playlist import Playlist
    self._playlist = Playlist(list(files))
    self._open_path(str(self._playlist.current()))
```

---

## ショートカット一覧ダイアログへの追記

`player.py` の `_show_shortcuts()` に以下のカテゴリ・行を追記:

| カテゴリ | キー | 動作 |
|---------|------|------|
| 再生操作 | `.` | 1フレーム進む（自動一時停止） |
| 再生操作 | `,` | 1フレーム戻る（自動一時停止） |
| 再生操作 | `Shift+→` | +1秒シーク |
| 再生操作 | `Shift+←` | -1秒シーク |
| 再生操作 | `Ctrl+→` | +10秒シーク |
| 再生操作 | `Ctrl+←` | -10秒シーク |
| 再生操作 | `]` | 再生速度を上げる |
| 再生操作 | `[` | 再生速度を下げる |
| ファイル操作 | `Ctrl+Shift+S` | スクリーンショット保存 |

---

## テスト方針

| テストファイル | 種別 | 対象 US |
|--------------|------|---------|
| `tests/unit/test_playback_position.py` | ユニット | US5 |
| `tests/unit/test_app_settings.py` | ユニット | US4 |
| `tests/unit/test_playlist.py` | ユニット | US7 |
| `tests/unit/test_bookmark_notes.py` | ユニット | US6 |
| `tests/integration/test_player_enhancements.py` | 統合 | US1〜US7 |

Constitution I（テストファースト）に従い、各 US の実装前に対応ユニットテストを作成してから実装する。
