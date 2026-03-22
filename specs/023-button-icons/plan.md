# Implementation Plan: ボタンアイコン追加

**Branch**: `023-button-icons` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/023-button-icons/spec.md`

## Summary

PyQt6 の `QStyle.StandardPixmap` を使い `looplayer/player.py` の9ボタンにアイコンを追加する。
`_apply_btn_icon()` と `_update_play_btn_appearance()` の2メソッドを VideoPlayer に追加。
7箇所に散在する `play_btn.setText()` 呼び出しを `_update_play_btn_appearance()` に集約。
不足している4ボタンのツールチップを既存 i18n キーで補完（新規キー追加なし）。
メディア未ロード時は `play_btn.setEnabled(False)` で disabled 初期状態を実現。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2, python-vlc 3.0.21203
**Storage**: N/A（UI 変更のみ、データファイル変更なし）
**Testing**: pytest + pytest-qt (pytestqt)
**Target Platform**: Linux / Windows / macOS (desktop-app)
**Project Type**: desktop-app
**Performance Goals**: 起動時の即座のアイコン表示（遅延ゼロ — `_build_ui()` 内で同期実行）
**Constraints**: 追加アセットファイルなし・新規 i18n キーなし・QStyle.StandardPixmap のみ使用
**Scale/Scope**: `looplayer/player.py` の9ボタン + 2メソッド追加 + 7箇所 setText 置換

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 状態 | 根拠 |
|------|------|------|
| I. テストファースト | ✅ PASS | テストファイルを実装前に作成する（tasks.md で先行タスク指定） |
| II. シンプルさ重視 | ✅ PASS | 追加するのは2メソッドのみ。既存コードの最小変更。 |
| III. 過度な抽象化の禁止 | ✅ PASS | `_apply_btn_icon` は9+ 箇所で使用のため正当化可。専用クラス不使用。 |
| IV. 日本語コミュニケーション | ✅ PASS | コメント・コミットメッセージは日本語 |

## Project Structure

### Documentation (this feature)

```text
specs/023-button-icons/
├── plan.md              # このファイル
├── research.md          # Phase 0 出力 — アイコンマッピング・実装方針
├── data-model.md        # Phase 1 出力 — ボタン状態モデル
├── quickstart.md        # Phase 1 出力 — 手動検証シナリオ
├── contracts/
│   └── button_icon_contract.md   # Phase 1 出力 — UI契約
└── tasks.md             # Phase 2 出力 (/speckit.tasks で生成)
```

### Source Code (変更対象ファイル)

```text
looplayer/
└── player.py            # 主要変更ファイル（アイコン追加、2メソッド追加、7箇所置換）

tests/
└── integration/
    ├── test_button_icons_p1.py    # US1: 主要再生ボタン（新規）
    ├── test_button_icons_p2.py    # US2: ABループボタン（新規）
    └── test_button_icons_p3.py    # US3: ブックマーク保存・ズーム（新規）
```

**Structure Decision**: 単一プロジェクト構成。テストは統合テスト（VideoPlayer インスタンスを使用）として `tests/integration/` に配置。UI 状態をテストするため pytestqt の `qtbot` を活用。

## Implementation Details

### looplayer/player.py — 変更内容

**1. インポート追加**（`_build_ui` より前、QtWidgets インポートに `QStyle` を追加）

```python
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QMessageBox, QSplitter,
    QStyle,   # 追加
)
```

**2. `_apply_btn_icon` メソッド追加**（VideoPlayer クラス内）

```python
def _apply_btn_icon(self, btn: QPushButton, sp: QStyle.StandardPixmap) -> None:
    """QStyle 標準アイコンを設定する。isNull() ならフォールバック（FR-009）。"""
    icon = self.style().standardIcon(sp)
    if not icon.isNull():
        btn.setIcon(icon)
```

**3. `_update_play_btn_appearance` メソッド追加**（VideoPlayer クラス内）

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

**4. `_build_ui` 内の変更**（ボタン作成後に追記）

```python
# --- ここから追加 ---
# play_btn: 初期状態（メディア未ロード）→ 再生アイコン + disabled（FR-001）
self.play_btn.setEnabled(False)
self._update_play_btn_appearance(playing=False)

# 静的アイコン設定
self._apply_btn_icon(self.open_btn, QStyle.StandardPixmap.SP_DirOpenIcon)
self._apply_btn_icon(self.stop_btn, QStyle.StandardPixmap.SP_MediaStop)
self._apply_btn_icon(self.set_a_btn, QStyle.StandardPixmap.SP_MediaSeekBackward)
self._apply_btn_icon(self.set_b_btn, QStyle.StandardPixmap.SP_MediaSeekForward)
self._apply_btn_icon(self.ab_toggle_btn, QStyle.StandardPixmap.SP_BrowserReload)
self._apply_btn_icon(self.ab_reset_btn, QStyle.StandardPixmap.SP_DialogResetButton)
self._apply_btn_icon(self.save_bookmark_btn, QStyle.StandardPixmap.SP_FileDialogStart)
self._apply_btn_icon(self._zoom_btn, QStyle.StandardPixmap.SP_FileDialogContentsView)

# 不足ツールチップ追加（FR-010: 既存 i18n キー再利用）
self.open_btn.setToolTip(t("btn.open"))
self.stop_btn.setToolTip(t("btn.stop"))
self.ab_reset_btn.setToolTip(t("btn.ab_reset"))
self.save_bookmark_btn.setToolTip(t("btn.save_bookmark"))
# --- ここまで追加 ---
```

**5. `_open_path` 内の変更**（メディアロード直後）

```python
# 変更前（717行目付近）:
self.media_player.play()
self.play_btn.setText(t("btn.pause"))

# 変更後:
self.media_player.play()
self.play_btn.setEnabled(True)          # メディアロード後に enable
self._update_play_btn_appearance(True)   # アイコン + テキスト更新
```

**6. 7箇所の `play_btn.setText()` 置換**（research.md Decision 2 参照）

| 行番号 | 変更前 | 変更後 |
|--------|--------|--------|
| ~717 | `setText(t("btn.pause"))` | `_update_play_btn_appearance(True)` |
| ~1067 | `setText(t("btn.play"))` | `_update_play_btn_appearance(False)` |
| ~1070 | `setText(t("btn.pause"))` | `_update_play_btn_appearance(True)` |
| ~1074 | `setText(t("btn.play"))` | `_update_play_btn_appearance(False)` |
| ~1903 | `setText(t("btn.pause"))` | `_update_play_btn_appearance(True)` |
| ~1919 | `setText(t("btn.pause"))` | `_update_play_btn_appearance(True)` |
| ~1962 | `setText(t("btn.pause"))` | `_update_play_btn_appearance(True)` |

### テストファイル構成

**`tests/integration/test_button_icons_p1.py`** — US1 テスト
**`tests/integration/test_button_icons_p2.py`** — US2 テスト
**`tests/integration/test_button_icons_p3.py`** — US3 + FR-009 + FR-010 テスト

各テストファイルの `player` fixture:
```python
@pytest.fixture
def player(qtbot: QtBot, tmp_path: Path) -> VideoPlayer:
    store = BookmarkStore(storage_path=tmp_path / "bookmarks.json")
    widget = VideoPlayer(store=store, recent_storage=tmp_path / "recent.json")
    qtbot.addWidget(widget)
    yield widget
    widget.timer.stop()
    widget._size_poll_timer.stop()
    widget.media_player.stop()
```

## Complexity Tracking

| 追加の複雑さ | 理由 | シンプルな代替案を採用しない理由 |
|-------------|------|--------------------------------|
| `_apply_btn_icon()` メソッド | 9+ 箇所の isNull() チェックを一元化 | 各呼び出しに直接記述すると9箇所の重複 |
| `_update_play_btn_appearance()` メソッド | 7箇所の setText() + setIcon() の組み合わせを一元化 | 漏れリスクが高く、将来の変更箇所が増える |
