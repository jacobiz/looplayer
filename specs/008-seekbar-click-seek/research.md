# Research: シークバークリックシーク

**Feature**: `008-seekbar-click-seek`
**Date**: 2026-03-16

---

## 1. PyQt6 QSlider のクリック挙動

**Decision**: `mousePressEvent` を完全にオーバーライドし、スーパークラスを呼ばずに直接 ms を計算して `seek_requested` を emit する（ブックマークバー以外のクリック時）

**Rationale**:
- PyQt6/Qt6 の `QSlider.mousePressEvent` のデフォルト動作はスタイル依存（Windows: SnappingSlider でクリック位置に即スナップ、macOS: PageStep ジャンプ）。プラットフォームをまたいで一貫した「クリック位置へ即ジャンプ」を実現するには `super()` を呼ばずに独自処理する必要がある。
- 既存の `mousePressEvent` はすでにオーバーライド済みであり（bookmark_bar_clicked の検出）、ブックマークバー以外のケースで `super()` を呼んでいる。この `super()` 呼び出しを独自シークロジックに置き換える。

**Alternatives considered**:
- `super()` を呼んだ後に `sliderMoved` シグナルを活用する → プラットフォーム差異を解消できないため却下
- `QSlider.setPageStep(0)` でページジャンプを抑制する → スタイルシート等の副作用リスクがあるため却下

---

## 2. ドラッグ中のリアルタイムシーク

**Decision**: `_dragging: bool` フラグを `BookmarkSlider` インスタンス変数として持ち、`mouseMoveEvent` で `seek_requested` を emit する。`isSliderDown()` は使わない。

**Rationale**:
- `isSliderDown()` は Qt 内部のつまみドラッグ状態を返す。今回はつまみ以外のトラッククリックからのドラッグなので `isSliderDown()` は `False` のまま — 使えない。
- 独自 `_dragging` フラグで「トラッククリック開始→移動→リリース」のライフサイクルを管理する方が明確。
- `mouseMoveEvent` で emit するが、VLC の `set_time()` は頻繁呼び出しに対応している（内部的に前回と同じ位置への設定は無視される）。

**Alternatives considered**:
- タイマー（`QTimer`）でポーリングしてシーク → 遅延が生じるため却下
- `setValue()` で QSlider の値を更新して既存 `sliderMoved` を活用する → `sliderMoved` は ratio (0-1000) ベース。ms ベースの新シグナルとの二重管理になるため却下

---

## 3. シグナル設計（ms vs ratio）

**Decision**: `seek_requested = pyqtSignal(int)` — 値の単位はミリ秒（int）

**Rationale**:
- 仕様 FR-002 が「グルーブ幅の比率に動画長を乗じた ms」を明示
- `VideoPlayer._on_seek_ms(ms)` で `set_time(ms)` を呼ぶと意図が明確
- 既存の `sliderMoved → _on_seek(value)` は ratio ベース (value/1000.0) だが、新シグナルは独立系として設計し、混乱を避ける

**Alternatives considered**:
- `pyqtSignal(float)` で ratio を emit → 既存 `_on_seek` と統一できるが、単位が不明瞭になる

---

## 4. `_on_timer` との競合（スライダー位置の更新）

**Decision**: `mouseMoveEvent` によるドラッグ中は `isSliderDown()` が `False` のままなので、`_on_timer` がスライダーの `setValue()` を呼んで位置を上書きしてしまう。これを防ぐために `_dragging` フラグを `isSliderDown()` の代替として `_on_timer` でチェックする。

**Rationale**:
- 既存コード: `if length_ms > 0 and not self.seek_slider.isSliderDown(): self.seek_slider.setValue(...)` — ドラッグ中は `isSliderDown()` で保護している
- 今回の独自ドラッグでは `isSliderDown()` が効かないため、`seek_slider._dragging` を追加チェックする（`or self.seek_slider._dragging`）

**Alternatives considered**:
- `seek_slider.setSliderDown(True)` を手動で呼ぶ → Qt 内部状態を手動管理するのは副作用リスクが高い
- `_dragging` の代わりに `seek_slider` にパブリックプロパティ `is_seeking` を追加する → 同等だが命名が変わるだけ。`_dragging` で十分

---

## 5. 既存テストへの影響

**Decision**: 既存の `test_bookmark_slider.py`（US4/005 ブランチで作成済み）に新テストを追加する。

**Rationale**:
- 既存ファイルはすでに `BookmarkSlider` のユニットテストを含む
- `tests/unit/test_bookmark_slider.py` に `TestClickSeek` クラスと `TestDragSeek` クラスを追加
- `bookmark_bar_clicked` の挙動が変わらないことを検証する `TestBookmarkBarClickRegressions` クラスも追加

---

## NEEDS CLARIFICATION 解決済み

すべての技術的不確実性は本 research.md で解消された。plan.md の Technical Context に未解決項目なし。
