# Data Model: AB Loop Player Improvements

## 既存エンティティの拡張

### LoopBookmark（拡張）

`looplayer/bookmark_store.py`

```python
@dataclass
class LoopBookmark:
    point_a_ms: int
    point_b_ms: int
    name: str = ""
    repeat_count: int = 1
    order: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enabled: bool = True
    notes: str = ""
    # --- 新規フィールド ---
    pause_ms: int = 0          # B点到達後のポーズ間隔（ms）。UI は秒換算で表示
    play_count: int = 0        # ループ再生回数（B点到達ごとにインクリメント）
    tags: list[str] = field(default_factory=list)  # タグリスト（OR フィルタ用）
```

**後方互換方針**:
- `to_dict()`: 新フィールドをそのまま追加
- `from_dict()`: `.get("pause_ms", 0)` / `.get("play_count", 0)` / `.get("tags", [])` でデフォルト値を使う

**バリデーション** (BookmarkStore.add/update):
- `pause_ms`: 0 以上 10000 以下（UI スピンボックスの範囲と一致）
- `play_count`: 0 以上（負値は拒否）
- `tags`: 各タグの前後空白をトリム、空文字列を除去

---

### SequentialPlayState（拡張）

`looplayer/sequential.py`

```python
@dataclass
class SequentialPlayState:
    bookmarks: list[LoopBookmark]
    current_index: int = 0
    remaining_repeats: int = 0
    active: bool = True
    one_round_mode: bool = False   # 新規: True のとき1周で停止

    def on_b_reached(self) -> int | None:
        """
        次の A 点 ms を返す。1周停止モードで全ブックマーク完走時は None を返す。
        """
        ...
```

**状態遷移**:
- `one_round_mode=False`（デフォルト）: 従来通り無限ループ
- `one_round_mode=True`: 最後のブックマークの最終リピートが完了したとき `None` を返す
- `None` を受け取った player.py 側が `_stop_seq_play()` を呼ぶ

---

### ClipExportJob（拡張）

`looplayer/clip_export.py`

```python
@dataclass
class ClipExportJob:
    source_path: Path
    start_ms: int
    end_ms: int
    output_path: Path
    encode_mode: str = "copy"   # 新規: "copy" | "transcode"
```

**encode_mode の値**:
- `"copy"`: `-c copy`（既存動作、デフォルト）
- `"transcode"`: `-c:v libx264 -c:a aac -crf 23`

---

## 新規エンティティ

### PlaylistPanel（新規ウィジェット）

`looplayer/widgets/playlist_panel.py`

- 状態: `Playlist | None`（None のときパネルは非表示）
- シグナル: `file_requested = pyqtSignal(str)`（ファイルパスを VideoPlayer に渡す）
- 表示: `QListWidget` でファイル名一覧 + 現在ファイルのハイライト

---

## AppSettings 新規フィールド

`looplayer/app_settings.py`

| プロパティ名 | 型 | デフォルト | JSON キー |
|---|---|---|---|
| `sequential_play_mode` | `str` | `"infinite"` | `"sequential_play_mode"` |
| `export_encode_mode` | `str` | `"copy"` | `"export_encode_mode"` |

**有効値**:
- `sequential_play_mode`: `"infinite"` | `"one_round"`
- `export_encode_mode`: `"copy"` | `"transcode"`

---

## 永続化ファイルへの影響

| ファイル | 変更内容 |
|---------|---------|
| `~/.looplayer/bookmarks.json` | `pause_ms`, `play_count`, `tags` フィールドが追加される（後方互換） |
| `~/.looplayer/settings.json` | `sequential_play_mode`, `export_encode_mode` キーが追加される |

