# Data Model: 表示修正 — サイドパネルデフォルト ON・AB点アイコン改善

**Feature**: 025-ui-display-fixes
**Date**: 2026-03-23

## データモデル変更なし

`~/.looplayer/settings.json` のスキーマは変更しない。`bookmark_panel_visible` キーは既存のまま。

## AppSettings の変更点

| フィールド | 変更前デフォルト | 変更後デフォルト | 説明 |
|----------|--------------|--------------|------|
| `bookmark_panel_visible` | `False` | `True` | 設定ファイルにキーが存在しない場合のフォールバック値のみ変更 |

設定ファイルに `bookmark_panel_visible` キーが **存在する** 場合はその値を優先するため、既存ユーザーへの影響はない。
