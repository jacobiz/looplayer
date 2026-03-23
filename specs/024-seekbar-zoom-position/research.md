# Research: シークバーズーム時の現在位置インジケーター表示

**Feature**: 024-seekbar-zoom-position
**Date**: 2026-03-23

## 問題の根本原因

### Decision: QSlider.setValue の値をズーム範囲に再マップする

**Rationale**:
`_on_timer()` は `seek_slider.setValue(int(pos * 1000))` で QSlider の value を全体の 0〜1.0 に対応した 0〜1000 でセットしている。QSlider はこの value を使ってハンドルを描画するため、ズームモードが有効でも全体の時間軸に基づいた位置にハンドルが表示される。

**修正方針**:
`BookmarkSlider` に `set_position_ms(current_ms: int)` メソッドを追加する。
- ズームモード有効時: `value = (current_ms - zoom_start) / (zoom_end - zoom_start) * 1000`
- ズームモード無効時: `value = current_ms / duration_ms * 1000`
- Qt が value を `[minimum, maximum]` = `[0, 1000]` にクリップするため、FR-004（範囲外→端固定）は自動的に達成される

**Alternatives considered**:

| 案 | 内容 | 却下理由 |
|----|------|---------|
| paintEvent オーバーライドでカスタムハンドル描画 | QSlider のネイティブハンドルを隠して独自描画 | プラットフォームスタイルとの互換性が複雑、YAGNI |
| QSlider の minimum/maximum をズーム範囲 ms に変更 | range を zoom_start〜zoom_end ms に更新 | `sliderMoved` の value 解釈が変わり `_on_seek` の修正が必要 |
| player.py 側で変換を実装 | `_on_timer` にズーム変換ロジックを追加 | ロジックが BookmarkSlider の外に漏れる、凝集度が低い |

**選択案**: `BookmarkSlider.set_position_ms()` メソッド追加（最小変更・高凝集）

---

## 影響範囲の調査

### `sliderMoved` シグナルの利用状況

`seek_slider.sliderMoved.connect(self._on_seek)` は接続されているが:
- `mousePressEvent` のカスタム実装がトラッククリック・ドラッグを `seek_requested` シグナルで処理
- `super().mousePressEvent(event)` は AB マーカー・ブックマーク・トラック以外の場合のみ呼ばれる
- 結果として `sliderMoved` はほぼ発火されない（ハンドルを直接ドラッグした場合のみ）

→ `sliderMoved` / `_on_seek` の変更は不要

### ズームモード切り替え時の即時更新（FR-005）

`_toggle_zoom_mode()` → `_apply_zoom_range()` / `clear_zoom()` 後、次の `_on_timer` ティック（200ms 間隔）で自動更新される。
200ms の遅延は SC-002「次の描画フレーム内」の要件を満たすため追加の即時更新は不要。

### テスト対象ファイル

- `tests/unit/test_bookmark_slider_zoom.py` — 既存ファイルに `set_position_ms` テストを追加
- `looplayer/widgets/bookmark_slider.py` — `set_position_ms` メソッドを追加
- `looplayer/player.py` — `_on_timer` の `setValue` → `set_position_ms` 呼び出しに変更
