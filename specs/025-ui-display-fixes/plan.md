# Implementation Plan: 表示修正 — サイドパネルデフォルト ON・AB点アイコン改善

**Branch**: `025-ui-display-fixes` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/025-ui-display-fixes/spec.md`

## Summary

2 つの独立した表示修正。① `app_settings.py` の `bookmark_panel_visible` デフォルト値を `False` → `True` に変更（1行修正）。② `player.py` の A点・B点ボタンアイコンを `SP_MediaSeekBackward/Forward` から `SP_FileDialogStart/End` に変更（2行修正）。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2
**Storage**: `~/.looplayer/settings.json`（`bookmark_panel_visible` フィールド、変更なし）
**Testing**: pytest + pytest-qt
**Target Platform**: デスクトップアプリ（Linux/Windows/macOS）
**Project Type**: desktop-app
**Performance Goals**: N/A（UI 表示のみ）
**Constraints**: 既存の `_apply_btn_icon()` の仕組みを使う。OS 標準アイコン（QStyle.StandardPixmap）のみ使用。
**Scale/Scope**: 2ファイル・合計3行の変更

## Constitution Check

| 原則 | 評価 | 備考 |
|------|------|------|
| I. テストファースト | ✅ PASS | `bookmark_panel_visible` デフォルト値のユニットテストを先に書く |
| II. シンプルさ重視 | ✅ PASS | 1行変更 × 2箇所。追加抽象化なし |
| III. 過度な抽象化の禁止 | ✅ PASS | 新規クラス・ヘルパー不要 |
| IV. 日本語コミュニケーション | ✅ PASS | コメント・コミットは日本語 |

**Gate result**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/025-ui-display-fixes/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md  (/speckit.tasks で生成)
```

### Source Code (変更対象ファイル)

```text
looplayer/
├── app_settings.py     # bookmark_panel_visible デフォルト値 False → True
└── player.py           # set_a_btn / set_b_btn アイコン変更

tests/
└── unit/
    └── test_app_settings.py  # デフォルト値のテストを追加
```

**Structure Decision**: 既存ファイルのみ変更。新規ファイルなし。

## Complexity Tracking

*Constitution Check に違反なし — この表は空*

## Phase 0: Research Findings

詳細は [research.md](research.md) を参照。ユーザーが **Option A** を選択。

### 決定事項

| 項目 | 変更前 | 変更後 |
|------|--------|--------|
| `bookmark_panel_visible` デフォルト | `False` | `True` |
| A点セットアイコン | `SP_MediaSeekBackward` | `SP_FileDialogStart` |
| B点セットアイコン | `SP_MediaSeekForward` | `SP_FileDialogEnd` |

### 既存設定ファイルへの影響なし

`_data.get("bookmark_panel_visible", True)` — キーが存在する場合はその値を使うため、既存ユーザーの設定は保持される。

## Phase 1: Design Artifacts

### 実装詳細

#### US1: app_settings.py L.140

```python
# 変更前
return bool(self._data.get("bookmark_panel_visible", False))
# 変更後
return bool(self._data.get("bookmark_panel_visible", True))
```

#### US2: player.py L.283-284

```python
# 変更前
self._apply_btn_icon(self.set_a_btn, QStyle.StandardPixmap.SP_MediaSeekBackward)
self._apply_btn_icon(self.set_b_btn, QStyle.StandardPixmap.SP_MediaSeekForward)
# 変更後
self._apply_btn_icon(self.set_a_btn, QStyle.StandardPixmap.SP_FileDialogStart)
self._apply_btn_icon(self.set_b_btn, QStyle.StandardPixmap.SP_FileDialogEnd)
```

### テスト対象

`test_app_settings.py` に以下を追加:
- `bookmark_panel_visible` を設定ファイルに持たない場合のデフォルト値が `True` であることを確認

アイコン変更はコードの1行変更であり、視覚的な確認は手動テストで行う（ユニットテスト不要）。

### 影響チェック

| 既存機能 | 影響 |
|---------|------|
| サイドパネルの手動 ON/OFF | 変化なし（設定ファイルに値があれば優先） |
| A点/B点の設定動作 | 変化なし（アイコンのみ変更） |
| AB ループ再生 | 変化なし |
| その他ボタン | 変化なし |
