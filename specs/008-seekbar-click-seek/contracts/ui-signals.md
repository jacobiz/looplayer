# UI Signal Contracts: BookmarkSlider

**Feature**: `008-seekbar-click-seek`
**File**: `looplayer/widgets/bookmark_slider.py`
**Date**: 2026-03-16

---

## シグナル一覧

### `seek_requested` *(新規)*

```python
seek_requested = pyqtSignal(int)
```

| 項目 | 内容 |
|------|------|
| 型 | `int` |
| 単位 | ミリ秒（ms） |
| 範囲 | `[0, duration_ms]`（`BookmarkSlider._duration_ms` の現在値でクリップ済み） |
| emit 条件 | トラック上の左クリック（ブックマーク区間バー以外） / ドラッグ中の mouseMoveEvent |
| emit しない条件 | `_duration_ms <= 0` の場合、ブックマーク区間バー上のクリックの場合 |

**受信側（VideoPlayer）**:

```python
self.seek_slider.seek_requested.connect(self._on_seek_ms)

def _on_seek_ms(self, ms: int) -> None:
    if self.media_player.get_length() > 0:
        self.media_player.set_time(ms)
```

---

### `bookmark_bar_clicked` *(既存・変更なし)*

```python
bookmark_bar_clicked = pyqtSignal(str)
```

| 項目 | 内容 |
|------|------|
| 型 | `str` |
| 内容 | クリックされたブックマークの ID |
| emit 条件 | 左クリックがブックマーク区間バー上に命中した場合 |
| 優先度 | `seek_requested` より優先（ブックマークバー上では seek_requested は emit しない） |

---

## `BookmarkSlider` 状態遷移

```
待機中
  └─ 左クリック（ブックマークバー上）   → bookmark_bar_clicked emit → 待機中に戻る
  └─ 左クリック（トラック上・duration>0）→ seek_requested emit、_dragging=True → ドラッグ中
  └─ 左クリック（duration=0）          → 何もしない → 待機中に戻る

ドラッグ中
  └─ mouseMoveEvent（左ボタン押下中）   → seek_requested emit → ドラッグ中を維持
  └─ mouseReleaseEvent（左ボタン）      → _dragging=False → 待機中に戻る
```

---

## VideoPlayer 側の `_on_timer` 変更

ドラッグ中にスライダー位置が上書きされないよう、既存の保護条件を拡張する：

```python
# 変更前
if length_ms > 0 and not self.seek_slider.isSliderDown():

# 変更後
if length_ms > 0 and not self.seek_slider.isSliderDown() and not self.seek_slider._dragging:
```
