# Data Model: タイムライン強化・連続再生選択・動画情報・ショートカット一覧

**Branch**: `005-timeline-seq-info-help` | **Date**: 2026-03-16

---

## 変更エンティティ

### LoopBookmark（既存 + 変更）

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
    enabled: bool = True   # ← 新規追加（連続再生対象フラグ）
```

**バリデーション規則（変更なし）**:
- `point_a_ms < point_b_ms` 必須
- `repeat_count >= 1` 必須
- `enabled` は True/False のみ

**JSONスキーマ（追加フィールド）**:
```json
{
  "id": "uuid",
  "name": "区間名",
  "point_a_ms": 1000,
  "point_b_ms": 5000,
  "repeat_count": 3,
  "order": 0,
  "enabled": true
}
```

**後方互換性**: `from_dict` で `enabled` キーが存在しない場合は `True` にフォールバック。

**`to_dict` 変更**:
```python
def to_dict(self) -> dict:
    return {
        "id": self.id,
        "name": self.name,
        "point_a_ms": self.point_a_ms,
        "point_b_ms": self.point_b_ms,
        "repeat_count": self.repeat_count,
        "order": self.order,
        "enabled": self.enabled,   # ← 追加
    }
```

**`from_dict` 変更**:
```python
@classmethod
def from_dict(cls, d: dict) -> "LoopBookmark":
    return cls(
        point_a_ms=d["point_a_ms"],
        point_b_ms=d["point_b_ms"],
        name=d.get("name", ""),
        repeat_count=d.get("repeat_count", 1),
        order=d.get("order", 0),
        id=d["id"],
        enabled=d.get("enabled", True),  # ← 追加（後方互換）
    )
```

---

## 新規エンティティ

### BookmarkSlider（新規ウィジェット）

`looplayer/widgets/bookmark_slider.py`

```
BookmarkSlider (QSlider をサブクラス化)
│
├── _bookmarks: list[tuple[int, int]]   # [(a_ms, b_ms), ...]
├── _bookmark_ids: list[str]             # 各バーと対応するブックマークID
├── _duration_ms: int                    # 動画の長さ（ms）
├── _colors: list[QColor]                # 色パレット（半透明）
│
├── set_bookmarks(bookmarks, duration_ms) → None   # 描画データを更新
├── _groove_rect() → QRect                          # グルーブ領域の取得
├── _ms_to_x(ms, groove) → int                      # ms → X 座標変換
├── paintEvent(event) → None                        # 半透明バーを重ね描き
└── mousePressEvent(event) → None                   # クリックしたブックマークを特定して emit
```

**シグナル**:
```python
bookmark_bar_clicked = pyqtSignal(str)   # クリックされたブックマークのID
```

**色パレット**（アルファ = 120）:
```
インデックス0: #FFA500 (オレンジ)
インデックス1: #00C8FF (シアン)
インデックス2: #C800FF (パープル)
インデックス3: #00FF64 (グリーン)
（以降はインデックス % 4 で循環）
```

**最小幅**: `max(x2 - x1, 4)` px

---

## 読み取り専用エンティティ（メモリのみ・永続化なし）

### VideoInfo（ダイアログ表示用）

`player.py` 内のローカル構造 (dataclass or dict) として保持。

```python
@dataclass
class VideoInfo:
    file_name: str          # os.path.basename(path)
    file_size_bytes: int    # os.path.getsize(path)
    duration_ms: int        # media_player.get_length()
    width: int              # VideoTrack.width
    height: int             # VideoTrack.height
    fps: float              # frame_rate_num / frame_rate_den
    video_codec: str        # libvlc_media_get_codec_description(TrackType.video, codec)
    audio_codec: str        # libvlc_media_get_codec_description(TrackType.audio, codec)
```

取得失敗した項目は `""` または `0` で表現し、ダイアログでは「不明」と表示。

---

## ストレージ変更

### `~/.looplayer/bookmarks.json`

既存スキーマに `"enabled": true/false` フィールドを追加。

```json
{
  "/path/to/video.mp4": [
    {
      "id": "550e8400-...",
      "name": "区間1",
      "point_a_ms": 1000,
      "point_b_ms": 5000,
      "repeat_count": 3,
      "order": 0,
      "enabled": true
    },
    {
      "id": "6ba7b810-...",
      "name": "区間2",
      "point_a_ms": 10000,
      "point_b_ms": 15000,
      "repeat_count": 1,
      "order": 1,
      "enabled": false
    }
  ]
}
```

### `BookmarkStore` 追加メソッド

```python
def update_enabled(self, video_path: str, bookmark_id: str, enabled: bool) -> None:
    """ブックマークの enabled フラグを更新して永続化する。"""
```

---

## 変更なしエンティティ

- `SequentialPlayState`: ブックマークリストを受け取るだけなので変更なし。フィルタリングは呼び出し元（`BookmarkPanel`）で行う。
- `RecentFiles`: 変更なし
- `BookmarkStore` のその他メソッド: 変更なし
