# Implementation Plan: 英語 UI 対応

**Branch**: `009-english-ui` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-english-ui/spec.md`

## Summary

新規モジュール `looplayer/i18n.py` を作成し、OS ロケールを起動時に一度だけ検出して日本語/英語を選択する `t(key)` 関数を提供する。`player.py`・`bookmark_panel.py`・`bookmark_row.py` の全ハードコード日本語文字列を `t("key")` 呼び出しに置き換える。外部ライブラリ追加・ビルドステップなし。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2（`QLocale.system()` でロケール検出）
**Storage**: N/A（言語はメモリ内で決定。永続化なし）
**Testing**: pytest
**Target Platform**: Windows / macOS デスクトップ
**Project Type**: desktop-app
**Performance Goals**: 起動時ロケール検出は 1 ms 以下（ユーザーに不可視）
**Constraints**: 外部ライブラリ追加なし。既存文字列パターンを最小限の変更で置換
**Scale/Scope**: 翻訳対象文字列 約 50 件。変更ファイル 3〜4 本

## Constitution Check

| 原則 | Status | 根拠 |
|------|--------|------|
| I. テストファースト | ✅ PASS | `looplayer/i18n.py` の `t()` とロケール検出ロジックをユニットテストで先に書く |
| II. シンプルさ重視 | ✅ PASS | Qt 標準 QTranslator + .ts/.qm ではなく、シンプルな Python dict で実装 |
| III. 過度な抽象化の禁止 | ✅ PASS | i18n クラスではなくモジュールレベルの `t()` 関数。辞書は `_STRINGS` 一本のみ |
| IV. 日本語コミュニケーション | ✅ PASS | コメント・コミットメッセージ日本語 |

違反なし。Complexity Tracking 記入不要。

## Project Structure

### Documentation (this feature)

```text
specs/009-english-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── contracts/
│   └── strings.md       # Phase 1 output（翻訳文字列カタログ）
├── quickstart.md        # Phase 1 output（手動テストシナリオ）
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
looplayer/
├── i18n.py                        # 新規: t(key) 関数・_STRINGS 辞書・ロケール検出
├── player.py                      # 変更: 全日本語ハードコード文字列 → t("key")
└── widgets/
    ├── bookmark_panel.py          # 変更: 日本語文字列 → t("key")
    └── bookmark_row.py            # 変更: 日本語文字列 → t("key")

tests/unit/
└── test_i18n.py                   # 新規: t()・ロケール検出のユニットテスト
```

**Structure Decision**: 単一プロジェクト構成。`looplayer/i18n.py` が唯一の新規ファイル。
