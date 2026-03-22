# Data Model: Bookmark Side Panel Toggle

**Branch**: `021-bookmark-sidepanel`
**Date**: 2026-03-21

---

## 変更対象ファイル一覧

| ファイル | 変更種別 | 概要 |
|----------|----------|------|
| `looplayer/app_settings.py` | 変更 | 新フィールド 2 件追加 |
| `looplayer/player.py` | 変更 | レイアウト・メニュー・フルスクリーン・リサイズ |
| `looplayer/i18n.py` | 変更 | 新 i18n キー 2 件追加 |

---

## 1. AppSettings 新フィールド

```python
# looplayer/app_settings.py に追加するプロパティ（既存パターン踏襲）

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
    self._data["bookmark_panel_width"] = max(240, value)  # 最小 240px 保証
```

**JSON キー**: `"bookmark_panel_visible"`, `"bookmark_panel_width"`
**保存先**: `~/.looplayer/settings.json`（既存ファイル、変更なし）
**デフォルト**: `False`（非表示）, `280`（px）

---

## 2. i18n 新キー

```python
# looplayer/i18n.py — menu.view セクションに追加

"menu.view.bookmark_panel": {
    "ja": "ブックマークパネル (&B)",
    "en": "Bookmark Panel (&B)"
},

# shortcut.* セクションに追加
"shortcut.bookmark_panel": {
    "ja": "ブックマークパネル 表示切り替え (B)",
    "en": "Toggle bookmark panel (B)"
},
```

---

## 3. VideoPlayer 新インスタンス変数

| 変数名 | 型 | 初期値 | 役割 |
|--------|-----|--------|------|
| `self._splitter` | `QSplitter` | `QSplitter(Qt.Orientation.Horizontal)` | video_frame と _panel_tabs を分割するウィジェット |
| `self._bookmark_panel_action` | `QAction` | チェック可能 QAction | メニュー「ブックマークパネル」トグル |
| `self._panel_tabs_was_visible` | `bool` | `False` | フルスクリーン前のパネル表示状態を保存 |

---

## 4. レイアウト変更の差分（概念）

### 変更前

```
centralWidget.layout (QVBoxLayout)
  ├── video_frame               [stretch=1]
  └── controls_panel
        └── controls_layout (QVBoxLayout)
              ├── volume_bar
              ├── seek_layout
              ├── ctrl_layout
              ├── ab_layout
              ├── bookmark_save_layout
              └── _panel_tabs              ← ここから移動
```

### 変更後

```
centralWidget.layout (QVBoxLayout)
  ├── _splitter (QSplitter Horizontal)    [stretch=1]   ← NEW
  │     ├── video_frame          (left pane)
  │     └── _panel_tabs          (right pane, min 240px) ← MOVED
  └── controls_panel
        └── controls_layout (QVBoxLayout)
              ├── volume_bar
              ├── seek_layout
              ├── ctrl_layout
              ├── ab_layout
              └── bookmark_save_layout
              # _panel_tabs を削除
```

---

## 5. 主要メソッドの変更・追加

### 追加メソッド

```python
def _toggle_bookmark_panel(self) -> None:
    """ブックマークパネルの表示・非表示を切り替える。"""
    # panel_tabs の表示/非表示切り替え
    # 非表示前に幅を保存
    # AppSettings を更新して永続化
    # メニューのチェックマークを同期

def _apply_initial_panel_width(self) -> None:
    """起動時にパネル幅を AppSettings から復元する（singleShot 遅延実行）。"""
    # splitter.setSizes([total - panel_w, panel_w])
```

### 変更メソッド

| メソッド | 変更内容 |
|----------|----------|
| `_setup_ui()` | `_panel_tabs` を `controls_layout` から削除、`_splitter` 作成・配置 |
| `_setup_view_menu()` | `_bookmark_panel_action` 追加（mirror_action の後） |
| `_enter_fullscreen_overlay_mode()` | `_panel_tabs_was_visible` を保存して `_panel_tabs.hide()` |
| `_exit_fullscreen_overlay_mode()` | `_panel_tabs_was_visible` が True なら `_panel_tabs.show()` |
| `_resize_to_video(w, h)` | パネルが表示中の場合、目標ウィンドウ幅に `bookmark_panel_width` を加算 |
| `closeEvent(event)` | パネルが表示中なら幅を AppSettings に保存 |

---

## 6. 最小幅・最大幅制約

| ウィジェット | 最小幅 | 備考 |
|-------------|--------|------|
| `_panel_tabs`（右ペイン） | 240px | `setMinimumWidth(240)` |
| `video_frame`（左ペイン） | 320px | `setMinimumWidth(320)`（フォールバック） |
| `QSplitter` 全体 | 560px | ウィンドウの最小幅として設定 |

`QSplitter.setCollapsible(0, False)` で video_frame の折りたたみを禁止する。
`QSplitter.setCollapsible(1, False)` で _panel_tabs の折りたたみも禁止（最小幅制約による自然な制限）。
