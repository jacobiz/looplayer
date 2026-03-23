# Research: 表示修正 — サイドパネルデフォルト ON・AB点アイコン改善

**Feature**: 025-ui-display-fixes
**Date**: 2026-03-23

---

## Decision 1: bookmark_panel_visible のデフォルト値変更

**Decision**: `app_settings.py` の `bookmark_panel_visible` プロパティのフォールバック値を `False` → `True` に変更する（1文字の修正）

**Rationale**: `_data.get("bookmark_panel_visible", False)` の `False` を `True` に変えるだけ。設定ファイルにキーが存在しない場合のみデフォルトが使われるため、既存ユーザーへの影響ゼロ。

**変更箇所**: `looplayer/app_settings.py` L.140

---

## Decision 2: A点・B点ボタンのアイコン選択 ← 選択肢あり

**現状**:
- A点セット: `SP_MediaSeekBackward`（◀◀ 巻き戻し）
- B点セット: `SP_MediaSeekForward`（▶▶ 早送り）

問題：巻き戻し/早送りは「操作方向」を表すアイコンであり、「区間の始点・終点」という概念が伝わりにくい。

---

### 選択肢

#### Option A（推奨）: SP_FileDialogStart / SP_FileDialogEnd

| ボタン | アイコン | 外観 | 意味 |
|-------|---------|------|------|
| A点セット | `SP_FileDialogStart` | \|◀ または ⏮ 相当 | 「先頭へ」= 始点 |
| B点セット | `SP_FileDialogEnd` | ▶\| または ⏭ 相当 | 「末尾へ」= 終点 |

- **メリット**: 名前に "Start" / "End" が含まれており、始点・終点の意味を最も直接的に表現。ペアとして対称的。
- **デメリット**: ファイルダイアログ由来のアイコンのため、OS によっては「ファイル操作」と誤解されるかもしれない。

#### Option B: SP_MediaSkipBackward / SP_MediaSkipForward

| ボタン | アイコン | 外観 | 意味 |
|-------|---------|------|------|
| A点セット | `SP_MediaSkipBackward` | \|◀◀ 相当 | 「先頭トラックへ」= 始まり |
| B点セット | `SP_MediaSkipForward` | ▶▶\| 相当 | 「次トラックへ」= 終わり |

- **メリット**: メディアプレイヤー文脈に沿っており、既存の `SP_MediaSeekBackward/Forward` より "境界" の概念が伝わりやすい。
- **デメリット**: 「前/次のトラックへスキップ」の意味も持つため、「区間の始点・終点をセット」とはやや意味がずれる。

#### Option C: SP_ArrowBack / SP_ArrowForward（不採用）

シンプルすぎて「始点・終点」の意味を持たないため選択肢から除外。

---

**推奨**: **Option A**（`SP_FileDialogStart` / `SP_FileDialogEnd`）

Start/End という名称が始点・終点に最も対応しており、ペアとして視覚的対称性が高い。
ユーザーへの提示で最終確認を行う。
