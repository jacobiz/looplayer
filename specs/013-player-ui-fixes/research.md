# Research: プレイヤー UI バグ修正・操作性改善

**Branch**: `013-player-ui-fixes` | **Date**: 2026-03-18

## Decision Log

### D-001: ESC キーバグの根本原因

**Decision**: `QShortcut` を MainWindow に直接追加する方式で修正する

**Rationale**:
PyQt6 では `QAction` のショートカットは、アクションが属する QWidget（ここではメニューバー）が非表示（`setVisible(False)`）になると、`ApplicationShortcut` コンテキストであっても**機能しなくなる**。フルスクリーン時に `menuBar().hide()` が呼ばれると `esc_action` のショートカットが失効する。

`QShortcut` は親ウィジェット（MainWindow）に直接アタッチされるため、子ウィジェットの表示状態に影響されない。`ApplicationShortcut` コンテキストを設定すればフォーカス状態にも依存しない。

**Alternatives Considered**:
- `keyPressEvent` オーバーライド: 機能はするが、ショートカット管理と実装が散らばる。フォーカスの奪い合いが起きる可能性もある → 却下
- `event filter` を全ウィジェットに設置: コード複雑度が上がる → 却下
- `QAction` を MainWindow に直接追加（メニューなし）: メニュー項目として表示されなくなる → 既存 esc_action を残すため補完として QShortcut を追加する方式を採用

**PyQt6 仕様確認**:
```python
# 追加する実装
from PyQt6.QtGui import QShortcut, QKeySequence
esc_sc = QShortcut(QKeySequence("Escape"), self)
esc_sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
esc_sc.activated.connect(self._exit_fullscreen)
```

---

### D-002: AB 点プレビューの描画方式

**Decision**: `BookmarkSlider.paintEvent` 内に AB 点プレビュー用の描画レイヤーを追加する

**Rationale**:
既存の paintEvent がブックマークバーをスライダーに重ね描きする実装パターンを踏襲することで、座標系・スケーリングを統一できる。追加の Widget を重ねる方式は z-order 管理・マウスイベント通過処理が複雑になるため非採用。

**描画スタイル決定**:
| 状態 | 描画内容 |
|------|---------|
| A 点のみ | `QColor(255, 255, 255, 200)` の縦線（幅 3px）。GrooveRect の高さに合わせる |
| A・B 両方 | `QColor(255, 255, 255, 120)` の半透明バー + 両端縦線（幅 2px） |
| 未設定 | 描画なし |

既存のブックマークバーは彩色（オレンジ・シアン・パープル・グリーン）。白系を使うことで明確に区別できる。

---

### D-003: AB 点マーカードラッグのヒット判定と優先順位

**Decision**: ヒット判定の優先順位を「AB マーカー > ブックマークバー > トラックシーク」とする

**Rationale**:
AB マーカーを精密に調整する操作はブックマーク選択より意図的なアクションのため、高優先度が適切。ただし AB マーカーが未設定の場合は既存のブックマークバークリック→シークが通常通り機能する。

**ヒット範囲**: マーカー縦線の中心から ±6px（合計 12px）をドラッグ開始判定エリアとする。スライダー全体幅 400px 以上を想定すると約 3% の領域で十分つかみやすい。

**状態管理**:
```python
_ab_drag_target: str | None = None  # "a" / "b" / None
_ab_preview_a: int | None = None
_ab_preview_b: int | None = None
```

**Alternatives Considered**:
- ドラッグ中もリアルタイム emit → spec の決定（ドラッグ終了時のみ更新）に従い却下
- 別の専用 Handle Widget → 座標管理が複雑になるため却下

---

### D-004: スピンボックス幅の修正方針

**Decision**: `setFixedWidth` を廃止し `setMinimumWidth` に変更する

**Rationale**:
`setFixedWidth` は固定幅を強制するため、フォントサイズが大きい環境や高 DPI 環境で数値が切れる問題が起きやすい。`setMinimumWidth` に変更することで、必要最低限の幅を確保しつつ、レイアウトが広い場合は自然に伸縮する。

**具体的な変更**:
| 対象 | 変更前 | 変更後 | 根拠 |
|------|--------|--------|------|
| `repeat_spin` | `setFixedWidth(55)` | `setMinimumWidth(68)` | "99" + アップダウンボタン込みで 68px 以上必要 |
| `pause_spin` | `setFixedWidth(64)` | `setMinimumWidth(75)` | "10.0" + アップダウンボタン込みで 75px 以上必要 |
