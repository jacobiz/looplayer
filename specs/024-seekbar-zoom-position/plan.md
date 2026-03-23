# Implementation Plan: シークバーズーム時の現在位置インジケーター表示

**Branch**: `024-seekbar-zoom-position` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/024-seekbar-zoom-position/spec.md`

## Summary

ズームモード有効時に `QSlider` のハンドル（現在位置マーカー）がズーム範囲（zoom_start〜zoom_end）に対して正確な相対位置に表示されない問題を修正する。`BookmarkSlider` に `set_position_ms()` メソッドを追加し、`player.py` の `_on_timer()` から呼び出すことで最小変更で対応する。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: N/A（データファイル変更なし）
**Testing**: pytest + pytest-qt
**Target Platform**: デスクトップアプリ（Linux/Windows/macOS）
**Project Type**: desktop-app
**Performance Goals**: 次の描画フレーム内（≤ 1 frame delay）での位置更新
**Constraints**: QSlider の既存インターフェース（setValue / minimum / maximum）を壊さない
**Scale/Scope**: 既存 BookmarkSlider + player.py への最小変更

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 評価 | 備考 |
|------|------|------|
| I. テストファースト | ✅ PASS | `set_position_ms` のユニットテストを先に書く |
| II. シンプルさ重視 | ✅ PASS | 1メソッド追加 + 1行変更のみ、最小変更 |
| III. 過度な抽象化の禁止 | ✅ PASS | 1箇所で使うヘルパーは作らない、直接メソッドを BookmarkSlider に追加 |
| IV. 日本語コミュニケーション | ✅ PASS | コメント・コミットは日本語 |

**Gate result**: PASS — Phase 1 設計に進める

## Project Structure

### Documentation (this feature)

```text
specs/024-seekbar-zoom-position/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks で生成)
```

### Source Code (変更対象ファイル)

```text
looplayer/
├── widgets/
│   └── bookmark_slider.py   # set_position_ms() メソッド追加
└── player.py                # _on_timer() の setValue → set_position_ms 呼び出しに変更

tests/
└── unit/
    └── test_bookmark_slider_zoom.py  # TestSetPositionMs クラスを追加
```

**Structure Decision**: 既存の単一プロジェクト構造を維持。新規ファイルは作成しない。

## Complexity Tracking

*Constitution Check に違反なし — この表は空*

## Phase 0: Research Findings

詳細は [research.md](research.md) を参照。

### 根本原因

`player.py._on_timer()` が `seek_slider.setValue(int(pos * 1000))` を使って QSlider value を全体の 0.0〜1.0 範囲で設定している。QSlider はこの value を元にハンドル位置を描画するため、ズーム範囲を考慮しない。

### 解決策の決定

`BookmarkSlider.set_position_ms(current_ms: int)` メソッドを追加:

```python
def set_position_ms(self, current_ms: int) -> None:
    if self._zoom_enabled and self._zoom_end_ms > self._zoom_start_ms:
        zoom_range = self._zoom_end_ms - self._zoom_start_ms
        value = int((current_ms - self._zoom_start_ms) / zoom_range * 1000)
    elif self._duration_ms > 0:
        value = int(current_ms / self._duration_ms * 1000)
    else:
        value = 0
    self.setValue(value)  # Qt が [0, 1000] にクリップ → 範囲外は端固定（FR-004）
```

### FR-004（範囲外→端固定）の達成方法

Qt の `QAbstractSlider.setValue()` は value を `[minimum, maximum]` にクリップする（Qt ドキュメント保証）。`minimum=0, maximum=1000` のため:
- `current_ms < zoom_start_ms` → 負値 → Qt が 0 にクリップ → ハンドルが左端
- `current_ms > zoom_end_ms` → 1000超 → Qt が 1000 にクリップ → ハンドルが右端

### `sliderMoved` への影響なし

カスタム `mousePressEvent` がすべてのトラック操作を `seek_requested` シグナル（`_x_to_ms()` でズーム対応済み）で処理するため、`sliderMoved` / `_on_seek` の変更は不要。

## Phase 1: Design Artifacts

詳細は [data-model.md](data-model.md)、[quickstart.md](quickstart.md) を参照。

### 実装設計

#### Step 1: テスト追加（赤テスト）— `test_bookmark_slider_zoom.py`

```python
class TestSetPositionMs:
    def test_zoom_active_position_in_range(self, slider):
        """ズームモード中、範囲内の位置が正しい value にマップされる。"""
        slider.set_zoom(20000, 40000)
        slider.set_position_ms(30000)  # 中間 → value = 500
        assert slider.value() == 500

    def test_zoom_active_position_at_start(self, slider):
        """ズームモード中、zoom_start_ms → value = 0（左端）。"""
        slider.set_zoom(20000, 40000)
        slider.set_position_ms(20000)
        assert slider.value() == 0

    def test_zoom_active_position_at_end(self, slider):
        """ズームモード中、zoom_end_ms → value = 1000（右端）。"""
        slider.set_zoom(20000, 40000)
        slider.set_position_ms(40000)
        assert slider.value() == 1000

    def test_zoom_active_position_before_range(self, slider):
        """ズームモード中、範囲より前 → value が Qt により 0 にクリップ（左端）。"""
        slider.set_zoom(20000, 40000)
        slider.set_position_ms(10000)
        assert slider.value() == 0

    def test_zoom_active_position_after_range(self, slider):
        """ズームモード中、範囲より後 → value が Qt により 1000 にクリップ（右端）。"""
        slider.set_zoom(20000, 40000)
        slider.set_position_ms(50000)
        assert slider.value() == 1000

    def test_no_zoom_normal_mapping(self, slider):
        """ズームなし時は duration_ms に基づく通常マッピング。"""
        slider.set_position_ms(50000)  # duration = 100000 → value = 500
        assert slider.value() == 500

    def test_no_zoom_zero_duration(self, slider):
        """duration_ms = 0 の場合は value = 0。"""
        slider._duration_ms = 0
        slider.set_position_ms(0)
        assert slider.value() == 0
```

#### Step 2: メソッド実装 — `bookmark_slider.py`

`BookmarkSlider` クラスに `set_position_ms()` メソッドを `set_bookmarks()` の後に追加する。

#### Step 3: 呼び出し元変更 — `player.py`

`_on_timer()` の L.1124 を変更:
```python
# 変更前
self.seek_slider.setValue(int(pos * 1000))
# 変更後
self.seek_slider.set_position_ms(int(pos * length_ms))
```

`length_ms` は L.1120 で取得済みのため変数の追加は不要。

### 影響チェック

| 既存機能 | 影響 |
|---------|------|
| 通常再生中のハンドル位置 | 変化なし（ズーム無効時は同等の値をセット） |
| トラッククリック・ドラッグシーク | 変化なし（`seek_requested` は `_x_to_ms` 経由）|
| AB 点プレビュー描画 | 変化なし |
| ブックマークバー描画 | 変化なし |
| `_on_seek` / `sliderMoved` | 変化なし（ほぼ発火されないため） |
