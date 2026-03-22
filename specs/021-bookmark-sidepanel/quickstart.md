# Developer Quickstart: Bookmark Side Panel Toggle

**Branch**: `021-bookmark-sidepanel`

---

## 概要

ブックマーク（＋プレイリスト）パネルを動画右側のサイドパネルとして表示・非表示切り替えできるようにする。QSplitter を使った最小変更レイアウト改修。

---

## 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `looplayer/app_settings.py` | `bookmark_panel_visible`, `bookmark_panel_width` フィールド追加 |
| `looplayer/player.py` | QSplitter 導入・メニュー追加・フルスクリーン連動 |
| `looplayer/i18n.py` | `menu.view.bookmark_panel`, `shortcut.bookmark_panel` キー追加 |

---

## 実装ポイント

### 1. AppSettings への追加（`app_settings.py`）

既存の `mirror_display` プロパティの直後に追加する:

```python
@property
def bookmark_panel_visible(self) -> bool:
    return self._data.get("bookmark_panel_visible", False)

@bookmark_panel_visible.setter
def bookmark_panel_visible(self, value: bool) -> None:
    self._data["bookmark_panel_visible"] = value

@property
def bookmark_panel_width(self) -> int:
    return self._data.get("bookmark_panel_width", 280)

@bookmark_panel_width.setter
def bookmark_panel_width(self, value: int) -> None:
    self._data["bookmark_panel_width"] = max(240, value)
```

### 2. QSplitter レイアウト（`player.py` `_setup_ui()`）

**変更前のコード（295〜296行目付近）:**
```python
controls_layout.addWidget(self._panel_tabs)   # ← 削除
```

**追加するコード（`video_frame` の addWidget 直後）:**
```python
# QSplitter で動画とパネルを横並びに
self._splitter = QSplitter(Qt.Orientation.Horizontal)
self._splitter.setChildrenCollapsible(False)
self._splitter.addWidget(self.video_frame)
self._panel_tabs.setMinimumWidth(240)
self._splitter.addWidget(self._panel_tabs)
self.video_frame.setMinimumWidth(320)
layout.addWidget(self._splitter, stretch=1)   # ← video_frame の代わり

# 初期サイズを AppSettings から遅延復元
QTimer.singleShot(0, self._apply_initial_panel_width)
```

**`layout.addWidget(self.video_frame, stretch=1)` を削除し上記で置き換える。**

### 3. パネル幅の初期設定

```python
def _apply_initial_panel_width(self) -> None:
    total = self._splitter.width()
    visible = self._app_settings.bookmark_panel_visible
    if not visible:
        self._panel_tabs.hide()
    else:
        w = min(self._app_settings.bookmark_panel_width, total - 320)
        w = max(w, 240)
        self._splitter.setSizes([total - w, w])
    self._bookmark_panel_action.setChecked(visible)
```

### 4. トグルメソッド

```python
def _toggle_bookmark_panel(self) -> None:
    visible = not self._panel_tabs.isVisible()
    if visible:
        self._panel_tabs.show()
        total = self._splitter.width()
        w = min(self._app_settings.bookmark_panel_width, total - 320)
        w = max(w, 240)
        self._splitter.setSizes([total - w, w])
    else:
        sizes = self._splitter.sizes()
        if len(sizes) >= 2 and sizes[1] > 0:
            self._app_settings.bookmark_panel_width = sizes[1]
        self._panel_tabs.hide()
    self._app_settings.bookmark_panel_visible = visible
    self._app_settings.save()
    self._bookmark_panel_action.setChecked(visible)
```

### 5. メニュー追加（`_setup_view_menu()`）

`mirror_action` の直後に追加:

```python
self._bookmark_panel_action = QAction(t("menu.view.bookmark_panel"), self)
self._bookmark_panel_action.setCheckable(True)
self._bookmark_panel_action.setChecked(self._app_settings.bookmark_panel_visible)
self._bookmark_panel_action.setShortcut(QKeySequence("B"))
self._bookmark_panel_action.triggered.connect(self._toggle_bookmark_panel)
view_menu.addAction(self._bookmark_panel_action)
```

### 6. フルスクリーン連動

**`_enter_fullscreen_overlay_mode()` に追加:**
```python
self._panel_tabs_was_visible = self._panel_tabs.isVisible()
self._panel_tabs.hide()
```

**`_exit_fullscreen_overlay_mode()` に追加:**
```python
if getattr(self, "_panel_tabs_was_visible", False):
    self._panel_tabs.show()
    total = self._splitter.width()
    w = min(self._app_settings.bookmark_panel_width, total - 320)
    self._splitter.setSizes([total - max(w, 240), max(w, 240)])
```

### 7. closeEvent での幅保存

`closeEvent()` の既存処理の中に追加:

```python
if self._panel_tabs.isVisible():
    sizes = self._splitter.sizes()
    if len(sizes) >= 2 and sizes[1] > 0:
        self._app_settings.bookmark_panel_width = sizes[1]
self._app_settings.save()
```

### 8. `_resize_to_video()` の修正

ウィンドウ目標幅計算に、パネルが表示中の場合パネル幅を加算:

```python
panel_w = self._splitter.sizes()[1] if (
    hasattr(self, "_splitter") and self._panel_tabs.isVisible()
) else 0
target_w = min(w + panel_w, avail.width())
```

---

## 動作確認チェックリスト

- [ ] アプリ起動 → パネルは非表示（初期デフォルト）
- [ ] `B` キー押下 → パネルが動画右に表示
- [ ] 境界をドラッグ → 幅が変更できる
- [ ] アプリ再起動 → 前回の表示状態・幅が復元される
- [ ] フルスクリーン（`F`）→ パネル非表示。解除後に復元
- [ ] メニュー「表示 → ブックマークパネル」のチェックマークが表示状態と同期
- [ ] パネル表示中にブックマーク操作（保存・選択・削除）が正常動作

---

## テスト実行

```bash
# ユニットテスト
pytest tests/unit/test_app_settings_panel.py -v
pytest tests/unit/test_bookmark_panel_toggle.py -v

# 統合テスト
pytest tests/integration/test_bookmark_panel_ui.py -v

# 全テスト（リグレッション確認）
pytest tests/ -v
```
