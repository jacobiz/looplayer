# Research: プレイヤーメニュー基本機能

**Date**: 2026-03-15
**Branch**: `003-player-menus`

## 1. PyQt6 QMenuBar / QMenu / QAction

**Decision**: `QMainWindow.menuBar()` + `addMenu()` + `addAction()` パターンを使用。

**Findings**:
- `self.menuBar()` は `QMainWindow` に組み込みのメニューバーを返す
- `QMenu.addAction(text, slot)` でアクションを追加
- `QAction.setShortcut(QKeySequence("Ctrl+O"))` でショートカット設定
- `QAction.setCheckable(True)` + `QAction.setChecked(bool)` でトグル表示（常に最前面、再生速度）
- `QActionGroup` で排他的チェックアクション群を管理（再生速度サブメニュー）
- `menu.addSeparator()` でセパレーター追加

**Rationale**: PyQt6 標準 API で追加ライブラリ不要。

---

## 2. VLC 音量制御

**Decision**: `media_player.audio_set_volume(0-100)` / `audio_get_volume()` を直接使用。

**Findings**:
- `audio_set_volume(i_volume)`: 0=ミュート、100=0dB ノーマル。範囲外は -1 を返す。
- `audio_get_volume()`: 現在の音量（%）を返す
- アプリ起動時の初期値: VLC デフォルトは 100。仕様上は 80% を初期値とする。
- ミュート: `audio_set_volume(0)` + 前の音量値を `_pre_mute_volume` に保存して復元

**Alternatives considered**:
- `audio_toggle_mute()`: VLC のネイティブミュートだが `audio_get_volume()` が 0 を返さないケースあり → 手動管理を選択

---

## 3. VLC 再生速度

**Decision**: `media_player.set_rate(float)` を使用。

**Findings**:
- `set_rate(rate)`: 1.0=標準、0.5=半速、2.0=2倍速
- 成功時 0、エラー時 -1 を返す（プロトコル依存で効かない場合あり）
- `get_rate()`: 現在のレートを返す
- ファイルを開き直すたびにリセットが必要（VLC の内部状態がメディアに依存するため `open_file()` 内で `set_rate(1.0)` を明示的に呼ぶ）

---

## 4. PyQt6 フルスクリーン

**Decision**: `QMainWindow.showFullScreen()` / `showNormal()` / `isFullScreen()` を使用。

**Findings**:
- `showFullScreen()`: ウィンドウをフルスクリーンに切り替え（タイトルバー・装飾なし）
- `showNormal()`: 通常ウィンドウに戻す
- `isFullScreen()`: 現在フルスクリーンかどうかを返す
- `controls_panel.hide()` / `menuBar().hide()` と組み合わせてコントロール類を非表示

**FR-016 マウス追跡実装パターン**:
```python
# フルスクリーン遷移時
self.video_frame.setMouseTracking(True)
self.centralWidget().setMouseTracking(True)

# mouseMoveEvent オーバーライド
def mouseMoveEvent(self, event):
    if self.isFullScreen():
        if event.pos().y() < 15:  # 上端15px
            self.menuBar().show()
            self._menu_hide_timer.start(2000)  # 2秒後に非表示
    super().mouseMoveEvent(event)
```

---

## 5. PyQt6 常に最前面

**Decision**: `Qt.WindowType.WindowStaysOnTopHint` フラグのトグル。

**Findings**:
- `setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)` で有効化
- `setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)` で無効化
- **重要**: `setWindowFlags()` の後に必ず `show()` を呼ぶ必要がある（ウィンドウが一時的に非表示になるため）
- フルスクリーン中に常に最前面フラグを変更するとフルスクリーンが解除されるリスクがあるため、フルスクリーン中は常に最前面メニューを無効化する

---

## 6. ショートカットキーの競合対策

**Findings**:
- `QAction.setShortcut()` はウィンドウフォーカス時に有効。ウィジェット（QSpinBox など）がフォーカスを持っている場合、`Space` や矢印キーはそのウィジェットに渡されることがある
- PyQt6 では `QAction.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)` を設定することでウィジェットのフォーカス状態に関わらず常にアクションが発火する
- **採用**: 全アクションに `ApplicationShortcut` コンテキストを設定

**Rationale**: `Space` キーで QSpinBox の値が変化してしまう問題を防ぐ。
