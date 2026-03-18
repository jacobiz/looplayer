# Data Model: プレイヤー UI バグ修正・操作性改善

**Branch**: `013-player-ui-fixes` | **Date**: 2026-03-18

## 変更対象エンティティ

### BookmarkSlider（`looplayer/widgets/bookmark_slider.py`）

既存属性に以下を追加する。永続化なし（UI の一時状態のみ）。

| 属性 | 型 | デフォルト | 説明 |
|------|----|-----------|------|
| `_ab_preview_a` | `int \| None` | `None` | 設定中 A 点の ms 値。None = 未設定 |
| `_ab_preview_b` | `int \| None` | `None` | 設定中 B 点の ms 値。None = 未設定 |
| `_ab_drag_target` | `str \| None` | `None` | ドラッグ中の対象: `"a"` / `"b"` / `None` |

#### 新規 API

```
set_ab_preview(a_ms: int | None, b_ms: int | None) -> None
    AB 点プレビューを更新して再描画する。
    a_ms=None かつ b_ms=None の場合はマーカーを消去する。

ab_point_drag_finished: pyqtSignal(str, int)
    AB 点マーカーのドラッグ完了時に emit。
    引数: target ("a" or "b"), ms (確定位置ミリ秒)
```

#### 状態遷移

```
AB プレビュー状態:
  (None, None)       → 何も表示しない
  (a_ms, None)       → A 点縦線マーカーのみ表示
  (a_ms, b_ms)       → A〜B 半透明バー表示
  (None, b_ms)       → B 点縦線マーカーのみ表示（通常は発生しないが考慮）

AB ドラッグ状態:
  _ab_drag_target=None   → 通常状態
  _ab_drag_target="a"    → A 点ドラッグ中
  _ab_drag_target="b"    → B 点ドラッグ中
```

#### マウスイベント処理優先順位（拡張後）

1. AB マーカードラッグ開始判定（±6px ヒットエリア）→ `_ab_drag_target` セット
2. ブックマークバークリック判定 → `bookmark_bar_clicked` emit
3. トラックシーク → `seek_requested` emit

---

### VideoPlayer（`looplayer/player.py`）

#### 変更箇所

```
__init__ または _setup_shortcuts:
  QShortcut(QKeySequence("Escape"), self) を追加
  → _exit_fullscreen に接続
  → ShortcutContext: ApplicationShortcut

set_point_a() 末尾に追加:
  self.seek_slider.set_ab_preview(self.ab_point_a, self.ab_point_b)

set_point_b() 末尾に追加:
  self.seek_slider.set_ab_preview(self.ab_point_a, self.ab_point_b)

clear_ab_loop() 末尾（ab_point_a/b を None にした後）に追加:
  self.seek_slider.set_ab_preview(None, None)

新規メソッド _on_ab_drag_finished(target: str, ms: int):
  if target == "a": self.ab_point_a = ms
  elif target == "b": self.ab_point_b = ms
  self._update_ab_ui()
  self.seek_slider.set_ab_preview(self.ab_point_a, self.ab_point_b)
```

---

### BookmarkRow（`looplayer/widgets/bookmark_row.py`）

#### 変更箇所

| 対象ウィジェット | 変更前 | 変更後 |
|-----------------|--------|--------|
| `repeat_spin` | `setFixedWidth(55)` | `setMinimumWidth(68)` |
| `pause_spin` | `setFixedWidth(64)` | `setMinimumWidth(75)` |

---

## 永続化への影響

- AB 点プレビューとドラッグ操作はメモリ内の一時状態のみを更新する
- `bookmarks.json` への書き込みは発生しない（既存の保存フローは変更しない）
- ESC ショートカットと spinbox 幅は UI のみの変更で永続化対象なし
