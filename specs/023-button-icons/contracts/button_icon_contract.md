# UI Contract: ボタンアイコン

**Branch**: `023-button-icons` | **Date**: 2026-03-22

---

## VideoPlayer — ボタンアイコン契約

### Contract: `play_btn` アイコン状態

```
Given: VideoPlayer が初期化された（メディア未ロード）
Then:
  - play_btn.icon().isNull() == False
  - play_btn.isEnabled() == False
  - play_btn.text() == t("btn.play")

Given: _open_path(path) が呼ばれた後
Then:
  - play_btn.isEnabled() == True
  - play_btn.icon() == style.standardIcon(SP_MediaPause)  ※再生が開始されるため
  - play_btn.text() == t("btn.pause")

Given: toggle_play() が停止→再生方向に呼ばれた後
Then:
  - play_btn.icon() == style.standardIcon(SP_MediaPause)
  - play_btn.text() == t("btn.pause")

Given: toggle_play() が再生→停止方向に呼ばれた後
Then:
  - play_btn.icon() == style.standardIcon(SP_MediaPlay)
  - play_btn.text() == t("btn.play")

Given: stop() が呼ばれた後
Then:
  - play_btn.icon() == style.standardIcon(SP_MediaPlay)
  - play_btn.text() == t("btn.play")
```

---

### Contract: 静的アイコンボタン（単一状態）

```
Given: VideoPlayer が初期化された
Then（以下すべてのボタンについて）:
  - open_btn.icon().isNull() == False
  - stop_btn.icon().isNull() == False
  - set_a_btn.icon().isNull() == False
  - set_b_btn.icon().isNull() == False
  - ab_reset_btn.icon().isNull() == False
  - save_bookmark_btn.icon().isNull() == False
```

---

### Contract: トグルボタン状態（`ab_toggle_btn`, `_zoom_btn`）

```
Given: VideoPlayer が初期化された
Then:
  - ab_toggle_btn.icon().isNull() == False
  - ab_toggle_btn.isCheckable() == True
  - ab_toggle_btn.isChecked() == False   ← OFF 状態（unchecked）
  - _zoom_btn.icon().isNull() == False
  - _zoom_btn.isCheckable() == True
  - _zoom_btn.isChecked() == False       ← OFF 状態（unchecked）

Given: toggle_ab_loop(True) が呼ばれた後
Then:
  - ab_toggle_btn.isChecked() == True    ← ON 状態（checked/強調）

Given: toggle_ab_loop(False) が呼ばれた後（または reset_ab()）
Then:
  - ab_toggle_btn.isChecked() == False   ← OFF 状態（unchecked）

Given: _toggle_zoom_mode(True) が呼ばれた後
Then:
  - _zoom_btn.isChecked() == True        ← ON 状態（checked/強調）
```

---

### Contract: ツールチップ（FR-010）

```
Given: VideoPlayer が初期化された
Then（以下すべてのボタンについて）:
  - open_btn.toolTip() != ""
  - play_btn.toolTip() != ""
  - stop_btn.toolTip() != ""
  - set_a_btn.toolTip() != ""
  - set_b_btn.toolTip() != ""
  - ab_toggle_btn.toolTip() != ""
  - ab_reset_btn.toolTip() != ""
  - save_bookmark_btn.toolTip() != ""
  - _zoom_btn.toolTip() != ""
```

---

### Contract: FR-009 フォールバック（`_apply_btn_icon`）

```
Given: self.style().standardIcon(sp) が null アイコンを返す（isNull() == True）
When: _apply_btn_icon(btn, sp) が呼ばれた
Then:
  - btn.setIcon() は呼ばれない
  - btn のテキストラベルは変わらない（テキストフォールバックが有効）
  - btn の機能（クリック動作）は失われない

Given: self.style().standardIcon(sp) が有効なアイコンを返す（isNull() == False）
When: _apply_btn_icon(btn, sp) が呼ばれた
Then:
  - btn.icon().isNull() == False
```

---

### Contract: メソッドシグネチャ

```python
# VideoPlayer クラスに追加する 2 つのメソッド

def _apply_btn_icon(self, btn: QPushButton, sp: QStyle.StandardPixmap) -> None:
    """QStyle 標準アイコンを設定する。isNull() ならフォールバック（FR-009）。"""

def _update_play_btn_appearance(self, playing: bool) -> None:
    """FR-001: 再生状態に応じて play_btn のアイコンとテキストを更新する。"""
```
