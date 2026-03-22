# Research: ボタンアイコン追加

**Branch**: `023-button-icons` | **Date**: 2026-03-22

---

## Decision 1: QStyle.StandardPixmap ボタン別アイコン対応表

### Decision
以下のマッピングを採用する。すべてのアイコンが本環境（Linux/PyQt6.10.2）で `isNull() == False` であることを実行確認済み。

| ボタン属性名 | QStyle.StandardPixmap | 論拠 |
|------------|----------------------|------|
| `open_btn` | `SP_DirOpenIcon` | フォルダを開く操作を直感的に示す |
| `play_btn`（play 時） | `SP_MediaPlay` | 国際標準の ▶ アイコン |
| `play_btn`（pause 時） | `SP_MediaPause` | 国際標準の ‖ アイコン |
| `stop_btn` | `SP_MediaStop` | 国際標準の ■ アイコン |
| `set_a_btn` | `SP_MediaSeekBackward` | ループ開始点（左方向）を示唆 |
| `set_b_btn` | `SP_MediaSeekForward` | ループ終了点（右方向）を示唆 |
| `ab_toggle_btn` | `SP_BrowserReload` | ループ/繰り返し動作を示唆 |
| `ab_reset_btn` | `SP_DialogResetButton` | リセット操作を示唆 |
| `save_bookmark_btn` | `SP_FileDialogStart` | 保存操作を示唆 |
| `_zoom_btn` | `SP_FileDialogContentsView` | 表示変更操作を示唆 |

### Rationale
- QStyle.StandardPixmap は OS/テーマ追従かつ自動 HiDPI 対応（追加ファイル不要）
- media 系ボタン (play/pause/stop/open) は完全一致するアイコンが存在する
- A点・B点・ABループ・保存・ズームは近似アイコンを採用し、テキストラベルとの組み合わせで意味を補完

### Alternatives considered
- バンドル SVG/PNG ファイル → 追加アセット不要の QStyle 優先（Assumptions と整合）
- Unicode 文字をテキストとして使用（▶ ‖ 等）→ setIcon() が使えず、フォールバックと区別しにくいため不採用

---

## Decision 2: play_btn の状態連動実装パターン

### Decision
`_update_play_btn_appearance(playing: bool)` メソッドを `VideoPlayer` に追加し、7箇所の `play_btn.setText()` 呼び出しをすべてこのメソッドに統一する。

```python
def _update_play_btn_appearance(self, playing: bool) -> None:
    """FR-001: 再生状態に応じて play_btn のアイコンとテキストを更新する。"""
    if playing:
        self._apply_btn_icon(self.play_btn, QStyle.StandardPixmap.SP_MediaPause)
        self.play_btn.setText(t("btn.pause"))
    else:
        self._apply_btn_icon(self.play_btn, QStyle.StandardPixmap.SP_MediaPlay)
        self.play_btn.setText(t("btn.play"))
```

置換対象の行番号（player.py）:
- 717行: `setText(t("btn.pause"))` → `_update_play_btn_appearance(True)`
- 1067行: `setText(t("btn.play"))` → `_update_play_btn_appearance(False)`
- 1070行: `setText(t("btn.pause"))` → `_update_play_btn_appearance(True)`
- 1074行: `setText(t("btn.play"))` → `_update_play_btn_appearance(False)`
- 1903行: `setText(t("btn.pause"))` → `_update_play_btn_appearance(True)`
- 1919行: `setText(t("btn.pause"))` → `_update_play_btn_appearance(True)`
- 1962行: `setText(t("btn.pause"))` → `_update_play_btn_appearance(True)`

### Rationale
散在する setText() 呼び出しを一元化することで、アイコン更新の漏れを防ぎ、将来の変更箇所を最小化できる。

### Alternatives considered
- 各呼び出し箇所に `setIcon()` を直接追記 → 漏れリスクが高く、7箇所すべての修正が必要になりメンテナンス性が低い
- QTimer でポーリングして状態を監視 → 過剰設計（Constitution II 違反）

---

## Decision 3: FR-009 フォールバック実装パターン

### Decision
`_apply_btn_icon(btn, sp)` メソッドを VideoPlayer に追加し、全ボタンのアイコン設定を一元化する。

```python
def _apply_btn_icon(self, btn: QPushButton, sp: QStyle.StandardPixmap) -> None:
    """QStyle 標準アイコンを設定する。isNull() なら何もしない（FR-009: テキストフォールバック）。"""
    icon = self.style().standardIcon(sp)
    if not icon.isNull():
        btn.setIcon(icon)
```

### Rationale
- `isNull()` チェックを各呼び出しに書くと重複が多い（9+ 箇所）
- 9+ 箇所で使用するため Constitution III のヘルパー禁止には該当しない
- テストで `style().standardIcon()` をモックすれば SC-003 のフォールバックを検証可能

### Alternatives considered
- 各ボタンの `setIcon()` に直接 `if not icon.isNull():` を記述 → 9箇所の重複が発生
- try/except で例外捕捉 → isNull() で十分かつ明確

---

## Decision 4: メディア未ロード時の play_btn 状態

### Decision
- `_build_ui()` 内で `self.play_btn.setEnabled(False)` を追加（初期状態: disabled）
- `_open_path()` 内で `self.play_btn.setEnabled(True)` を追加（メディアロード後: enabled）
- アイコンは SP_MediaPlay（再生アイコン）を初期表示

### Rationale
FR-001 の明示的要件: 「メディア未ロード時は再生アイコンを表示しボタンを無効（disabled/グレーアウト）状態とすること」

現在の実装では `play_btn.setEnabled(False)` の呼び出しが存在しないため、追加が必要。

### Alternatives considered
- setEnabled(False) を追加しない（アイコンのみ設定）→ FR-001 違反
- メディアロード完了イベントで enable → VLC イベントコールバックが必要で複雑（_open_path で即時 enable で十分）

---

## Decision 5: 不足ツールチップの追加方針

### Decision
以下4ボタンに `setToolTip()` を追加。既存 i18n キー（ボタンラベルと同一）を再利用（FR-010）。

| ボタン | 追加するコード |
|--------|--------------|
| `open_btn` | `self.open_btn.setToolTip(t("btn.open"))` |
| `stop_btn` | `self.stop_btn.setToolTip(t("btn.stop"))` |
| `ab_reset_btn` | `self.ab_reset_btn.setToolTip(t("btn.ab_reset"))` |
| `save_bookmark_btn` | `self.save_bookmark_btn.setToolTip(t("btn.save_bookmark"))` |

### Rationale
FR-010「ツールチップテキストは既存の i18n キーを再利用し、新規キーは追加しない」に準拠。既存ツールチップ（play, set_a, set_b, ab_loop, zoom_mode）は変更不要。

---

## Decision 6: QStyle インポート追加

### Decision
`player.py` の QtWidgets インポート行に `QStyle` を追加する。

```python
# 変更前
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QMessageBox, QSplitter,
)
# 変更後（QStyle を追加）
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QMessageBox, QSplitter,
    QStyle,
)
```

### Rationale
`QStyle.StandardPixmap` を参照するために必要。`QIcon` は既にインポート済み。
