# Research: Bookmark Side Panel Toggle

**Branch**: `021-bookmark-sidepanel`
**Date**: 2026-03-21

---

## Decision 1: レイアウト変更方式 — QSplitter

**Decision**: `video_frame` の代わりに水平 `QSplitter` を中央 `QVBoxLayout` の上段（stretch=1）に配置し、左ペイン = `video_frame`、右ペイン = `_panel_tabs` とする。

**Rationale**:
- PyQt6 標準ウィジェット。新規クラス不要（Constitution III PASS）。
- ドラッグリサイズが組み込み済みで追加実装ゼロ。
- `_panel_tabs.hide()` で右ペインを非表示にするだけで video_frame が幅全体に伸びる。

**Alternatives considered**:
- `QDockWidget`: 浮動ウィンドウにもなるが、固定サイドパネルのみ必要なので過剰。
- `QHBoxLayout` + 手動リサイズ: ドラッグ実装が必要で複雑化。

---

## Decision 2: `_panel_tabs` の移動元・移動先

**Decision**: `controls_panel` 内の `controls_layout` から `_panel_tabs` を取り出し、QSplitter の右ペイン（インデックス 1）に追加する。

**Rationale**:
- `_panel_tabs` は現在 `controls_layout.addWidget(_panel_tabs)` で下部に配置されている（`player.py` 296行目）。これを削除して QSplitter に渡す最小変更で実現できる。
- `controls_panel`（シークバー・ボタン群）は QSplitter の下段に残し、常時表示を維持（FR-009）。

**Concrete layout after change**:
```
QMainWindow
└── centralWidget (QWidget)
    └── QVBoxLayout (margin=8, spacing=6)
        ├── QSplitter (Horizontal, stretch=1)      ← NEW
        │   ├── video_frame (左ペイン)
        │   └── _panel_tabs (右ペイン, 最小幅240px)
        └── controls_panel (シークバー・ボタン群)
```

---

## Decision 3: パネル幅の永続化方式

**Decision**: AppSettings に `bookmark_panel_visible: bool` と `bookmark_panel_width: int` を追加。パネル非表示直前・アプリ終了時（`closeEvent`）に幅を保存する。

**Rationale**:
- 既存の AppSettings パターン（`_data.get("key", default)` + アトミック保存）をそのまま踏襲（Constitution II PASS）。
- `splitter.splitterMoved` シグナルではなく `closeEvent` で保存することで、ドラッグ中の大量 I/O を避ける。加えて、パネルを非表示にした時点でも幅を保存することで「再表示したら元の幅に戻る」体験を確保。

**Default values**:
- `bookmark_panel_visible`: `False`（spec の Assumptions に準拠。既存動作踏襲）
- `bookmark_panel_width`: `280`（px）。起動時にウィンドウ幅が不明なため絶対値で保持。最小値クランプ（240px）は表示時に適用する。

---

## Decision 4: フルスクリーン時のパネル制御

**Decision**: `_enter_fullscreen_overlay_mode()` でパネルを非表示にし、直前の表示状態をインスタンス変数 `_panel_tabs_was_visible` に保存。`_exit_fullscreen_overlay_mode()` で状態を復元する。

**Rationale**:
- `_enter/exit_fullscreen_overlay_mode()` はすでに `controls_panel` の着脱を行っており、同じパターンでパネル制御を追加できる（Constitution II）。
- QSplitter を完全に取り外す必要はない。右ペインの `_panel_tabs` を hide/show するだけで video_frame が全幅を占有する。

---

## Decision 5: ウィンドウリサイズ時の動画サイズ調整との整合

**Decision**: `_resize_to_video(w, h)` でウィンドウ目標幅を計算する際、パネルが表示中なら `panel_width` を加算する。

**Rationale**:
- 現在 `_resize_to_video()` はウィンドウ全体をビデオ解像度に合わせる。QSplitter 導入後は、ウィンドウ幅 = 動画幅 + パネル幅 となるため、パネルが表示中の場合のみ加算が必要。
- 計算式: `target_w = min(video_w + (panel_w if panel_visible else 0), avail_w)`

---

## Decision 6: トグルメニュー項目の配置

**Decision**: `_setup_view_menu()` 内の `mirror_action` の直後に `_bookmark_panel_action`（チェック可能な QAction、ショートカット `B`）を追加する。

**Rationale**:
- 既存の `menu.view` に追加するのが最も自然（表示系操作の集約）。
- チェックマーク（`setCheckable(True)`）で現在の表示状態を視覚的に示す（FR-003）。
- `B` キーは既存ショートカット（`I`, `O`, `Space`, `F`, `M`, 矢印, `[`, `]`, `Ctrl+S`, `Ctrl+E`, `Ctrl+B`, `Delete`）と非衝突。

---

## Decision 7: QSplitter の初期サイズ設定

**Decision**: 起動時に `splitter.setSizes([max(0, window_w - panel_w), panel_w])` で初期幅を設定する。ただし `window_w` が確定するのはウィジェット表示後のため、`showEvent` または `QTimer.singleShot(0, ...)` で遅延実行する。

**Rationale**:
- `_setup_ui()` 時点ではウィンドウ幅が未確定のため `splitter.setSizes()` を直接呼べない。
- `QTimer.singleShot(0, _apply_initial_panel_width)` パターンは既存コードでも使用されている（`_open_path()` の再生位置復元など）。

