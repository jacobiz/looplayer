# Widget Signal Contracts: AB Loop Player Improvements

## BookmarkRow（拡張シグナル）

`looplayer/widgets/bookmark_row.py`

### 既存シグナル（変更なし）
```python
deleted = pyqtSignal(str)               # bookmark_id
selected = pyqtSignal(str)             # bookmark_id
repeat_changed = pyqtSignal(str, int)  # bookmark_id, repeat_count
enabled_changed = pyqtSignal(str, bool) # bookmark_id, enabled
export_requested = pyqtSignal(int, int, str)  # a_ms, b_ms, label
```

### 新規シグナル
```python
frame_adjusted = pyqtSignal(str, str, int)
# bookmark_id, point ("a" | "b"), new_ms
# 微調整後の新しい ms 値を VideoPlayer へ通知

pause_ms_changed = pyqtSignal(str, int)
# bookmark_id, new_pause_ms
# ポーズ間隔スピンボックスの変更を VideoPlayer へ通知

play_count_reset = pyqtSignal(str)
# bookmark_id
# 右クリックメニュー「再生回数をリセット」を VideoPlayer へ通知

tags_changed = pyqtSignal(str, list)
# bookmark_id, new_tags
# タグ編集完了を BookmarkPanel へ通知（フィルタ再構築のため）
```

---

## BookmarkPanel（拡張シグナル）

`looplayer/widgets/bookmark_panel.py`

### 既存シグナル（変更なし）
```python
bookmark_selected = pyqtSignal(str)    # bookmark_id
seq_play_started = pyqtSignal(object)  # SequentialPlayState
seq_play_stopped = pyqtSignal()
bookmark_bar_clicked = pyqtSignal(str) # bookmark_id
```

### 新規シグナル
```python
tag_filter_changed = pyqtSignal(list)
# selected_tags: list[str]
# 空リストのとき全件表示（フィルタなし）
# VideoPlayer は不要（BookmarkPanel 内で完結）
```

---

## PlaylistPanel（新規ウィジェット）

`looplayer/widgets/playlist_panel.py`

```python
class PlaylistPanel(QWidget):
    file_requested = pyqtSignal(str)  # 絶対ファイルパス
    # QListWidget のクリックで emit → VideoPlayer._open_path() を呼ぶ

    def set_playlist(self, playlist: Playlist | None) -> None:
        """プレイリストをセット。None のときウィジェット自体を非表示にする。"""

    def update_current(self, path: str) -> None:
        """現在再生中のファイルをハイライト。VideoPlayer からファイル変更時に呼ぶ。"""
```

---

## VideoPlayer の新規/変更スロット

`looplayer/player.py`

```python
# US1
def set_point_a(self) -> None: ...          # I キー / 既存ボタン共用
def set_point_b(self) -> None: ...          # O キー / 既存ボタン共用

# US2
def _on_frame_adjusted(self, bm_id: str, point: str, new_ms: int) -> None:
    """BookmarkRow.frame_adjusted を受け取り store を更新"""

# US3
def _save_bookmark(self) -> None: ...       # QInputDialog.getText を追加

# US4
def _on_pause_ms_changed(self, bm_id: str, new_ms: int) -> None:
    """BookmarkRow.pause_ms_changed を受け取り store を更新"""
# _pause_timer: QTimer | None  (新規インスタンス変数)
# _resume_after_pause() -> None

# US5
def _on_seq_mode_toggled(self, one_round: bool) -> None:
    """BookmarkPanel の 1周/無限 トグルを受け取り app_settings を更新"""

# US6
def _on_play_count_reset(self, bm_id: str) -> None:
    """BookmarkRow.play_count_reset を受け取り store を更新"""

# US7
def open_folder(self) -> None: ...          # QFileDialog.getExistingDirectory

# US8
def _playlist_next(self) -> None:           # Alt+→
def _playlist_prev(self) -> None:           # Alt+←

# US9 - BookmarkPanel 内で完結のため VideoPlayer への変更なし

# US10
def _export_clip(self) -> None: ...         # encode_mode を ClipExportJob に渡す変更
def _export_clip_from_bookmark(...) -> None # 同上
```

---

## _on_timer() の拡張仕様

`looplayer/player.py:847`

```
B点到達時の処理フロー（pause_ms > 0 の場合）:

1. pause_ms > 0 かつ _pause_timer が None のとき:
   a. media_player.pause()
   b. _pause_timer = QTimer.singleShot(pause_ms, self._resume_after_pause)
   c. return（以降の処理をスキップ）

2. _resume_after_pause():
   a. media_player.set_time(a_ms)
   b. media_player.play()
   c. _pause_timer = None

3. Space キーでポーズキャンセル（toggle_play() を拡張）:
   if _pause_timer is not None:
       _pause_timer.stop()  ← QTimer.singleShot は stop 不可のため QTimer インスタンスを保持する
       _pause_timer = None
       → _resume_after_pause() を直接呼ぶ
```

**注意**: `QTimer.singleShot` は `QTimer` インスタンスを返さないため、`self._pause_timer = QTimer(self)` を `singleShot` の代わりに使い、`timeout.connect` + `start(pause_ms)` で同等の動作を実現する。

