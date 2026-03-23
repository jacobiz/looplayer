# Data Model: シークバーズーム時の現在位置インジケーター表示

**Feature**: 024-seekbar-zoom-position
**Date**: 2026-03-23

## 変更なし（データモデル）

本機能はデータファイル（bookmarks.json, settings.json 等）への変更を伴わない。

## BookmarkSlider 内部状態の変化

既存フィールドは変更なし。以下のフィールドとメソッドを追加する。

### 追加フィールド

なし（`_zoom_start_ms`, `_zoom_end_ms`, `_zoom_enabled`, `_duration_ms` の既存フィールドを利用）

### 追加メソッド

| メソッド | シグネチャ | 説明 |
|---------|-----------|------|
| `set_position_ms` | `(current_ms: int) -> None` | 現在位置 ms をズームモードに応じた QSlider value に変換してセットする |

### `set_position_ms` の変換ロジック

```
if zoom_enabled and zoom_range > 0:
    value = (current_ms - zoom_start_ms) / zoom_range * 1000
    # Qt が [0, 1000] にクリップ → 範囲外は端に固定（FR-004）
else:
    value = current_ms / duration_ms * 1000  # 通常モード（既存動作と同等）
setValue(int(value))
```

### player.py の変更

| 変更箇所 | 変更前 | 変更後 |
|---------|--------|--------|
| `_on_timer()` L.1124 | `seek_slider.setValue(int(pos * 1000))` | `seek_slider.set_position_ms(int(pos * length_ms))` |
