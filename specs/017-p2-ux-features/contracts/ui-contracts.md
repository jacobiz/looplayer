# UI Contracts: P2 UX 機能群

**Branch**: `017-p2-ux-features` | **Date**: 2026-03-18

---

## C-01: AppSettings.onboarding_shown

**場所**: `looplayer/app_settings.py`

```python
@property
def onboarding_shown(self) -> bool:
    """オンボーディング完了/スキップ済みフラグ。未設定は False。"""
    ...

@onboarding_shown.setter
def onboarding_shown(self, value: bool) -> None:
    """True にセットして保存する。False にセットして再表示を可能にする。"""
    ...
```

**事前条件**: なし
**事後条件**: `save()` が呼ばれ `~/.looplayer/settings.json` に `"onboarding_shown": true/false` が書き込まれる

---

## C-02: PreferencesDialog

**場所**: `looplayer/widgets/preferences_dialog.py`

```python
class PreferencesDialog(QDialog):
    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        """
        settings の現在値を各ウィジェットに反映してダイアログを構築する。
        """
        ...

    def accept(self) -> None:
        """
        各ウィジェットの値を settings に書き込んでダイアログを閉じる。
        書き込み後に super().accept() を呼ぶ。
        """
        ...
```

**シグナル**: なし（OK/Cancel は標準 QDialog シグナルを使用）
**事前条件**: `settings` は有効な `AppSettings` インスタンス
**事後条件 (accept)**: `settings.end_of_playback_action`, `sequential_play_mode`, `export_encode_mode`, `check_update_on_startup` が更新されている
**事後条件 (reject)**: `settings` の値は変更されていない

---

## C-03: OnboardingOverlay

**場所**: `looplayer/widgets/onboarding_overlay.py`

```python
class OnboardingOverlay(QWidget):
    def __init__(self, settings: AppSettings, parent: QWidget) -> None:
        """
        parent ウィジェットの中央に配置する非モーダルオーバーレイ。
        parent は VideoPlayer であること。
        """
        ...
```

**シグナル**: なし（クローズは `close()` で内部的に処理）
**表示制御**: `VideoPlayer.__init__` の末尾で `settings.onboarding_shown` が `False` のときのみ生成・表示
**サイズ追従**: `VideoPlayer.resizeEvent` で `setGeometry()` を再計算
**事前条件**: `parent` が表示状態であること
**事後条件 (完了/スキップ)**: `settings.onboarding_shown = True` を保存してウィジェットが閉じる（FR-305: 両ケースでフラグ保存）
**事後条件 (途中終了)**: `settings.onboarding_shown` は変更されない

---

## C-04: BookmarkSlider ズーム拡張

**場所**: `looplayer/widgets/bookmark_slider.py`

```python
def set_zoom(self, start_ms: int, end_ms: int) -> None:
    """
    ズームモードを有効にし、表示範囲を [start_ms, end_ms] に設定する。
    set_zoom 後は update() を呼んで再描画する。
    事前条件: start_ms < end_ms
    """
    ...

def clear_zoom(self) -> None:
    """
    ズームモードを無効にする。
    clear_zoom 後は update() を呼んで再描画する。
    """
    ...

@property
def zoom_enabled(self) -> bool:
    """ズームモードが有効かどうかを返す。"""
    ...
```

**シグナル**: 既存シグナル（`seek_requested`, `ab_point_drag_finished`）の意味はズームモード中も変わらない。ただし emit される ms 値はズーム座標変換後の値（全動画内の絶対時刻）である。
**事前条件 (`set_zoom`)**: `start_ms < end_ms`。違反時は `ValueError` を raise
**事後条件 (`set_zoom`)**: `zoom_enabled == True`、`_zoom_start_ms == start_ms`、`_zoom_end_ms == end_ms`
**事後条件 (`clear_zoom`)**: `zoom_enabled == False`

---

## C-05: VideoPlayer フルスクリーンオーバーレイ（内部インターフェース）

**場所**: `looplayer/player.py` — `VideoPlayer`

新規追加メソッド（プライベート）:

```python
def _enter_fullscreen_overlay_mode(self) -> None:
    """
    controls_panel をレイアウトから取り外しオーバーレイとして絶対配置する。
    フルスクリーン遷移時（changeEvent で isFullScreen() == True の場合）に呼ぶ。
    """
    ...

def _exit_fullscreen_overlay_mode(self) -> None:
    """
    controls_panel をレイアウトに戻す。
    フルスクリーン解除時（changeEvent で isFullScreen() == False の場合）に呼ぶ。
    """
    ...
```

**_overlay_hide_timer の仕様**:
- `singleShot=True`, `interval=3000` ms
- `timeout` シグナルを `controls_panel.hide()` に接続
- `mouseMoveEvent` での画面下端10%検出時に `start(3000)` でリセット
- `controls_panel` 上の `mouseMoveEvent`（EventFilter 経由）でも `start(3000)` でリセット

**カーソル非表示との連動**:
- `controls_panel` が表示中: `unsetCursor()` でカーソルを常時表示
- `_hide_cursor()` は `controls_panel.isVisible() == False` のときのみ実行
