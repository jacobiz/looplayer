# Implementation Plan: 字幕からのブックマーク自動生成とデータ一括バックアップ

**Branch**: `019-subtitle-bookmark-backup` | **Date**: 2026-03-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/019-subtitle-bookmark-backup/spec.md`

## Summary

SRT/ASS 字幕ファイルの各エントリを A/B 点付きブックマークとして一括生成する機能（F-202）と、`~/.looplayer/` 以下の全データを ZIP アーカイブでバックアップ・復元する機能（F-402）を追加する。既存の字幕読み込みインフラ・BookmarkStore・AppSettings を活用し、標準ライブラリのみで実装する。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2（UI）、標準ライブラリ: `zipfile`, `json`, `re`, `shutil`, `datetime`
**Storage**: `~/.looplayer/bookmarks.json`・`settings.json`・`positions.json`・`recent_files.json`（既存）; バックアップ用 ZIP ファイル
**Testing**: pytest（既存）
**Target Platform**: Windows デスクトップアプリ
**Project Type**: desktop-app（既存アプリへの機能追加）
**Performance Goals**: 100件字幕 → ブックマーク生成 5秒以内; バックアップ操作 10秒以内
**Constraints**: 外部ライブラリ追加なし（`zipfile` は標準ライブラリ）; 既存機能の非退行
**Scale/Scope**: 字幕最大 500件超; バックアップファイルは数百 KB 程度

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 状態 | 備考 |
|------|------|------|
| I. テストファースト | ✅ PASS | 全タスクでテスト先行（tasks.md で明示） |
| II. シンプルさ重視 | ✅ PASS | 外部ライブラリなし・stdlib のみ・既存パターン踏襲 |
| III. 過度な抽象化の禁止 | ✅ PASS | `subtitle_parser.py`（F-202 専用）・`data_backup.py`（F-402 専用）の 2 ファイル追加のみ |
| IV. 日本語コミュニケーション | ✅ PASS | UI 文字列は `i18n.py` 経由、仕様書・コメントは日本語 |

**Post-Phase 1 re-check**: 設計後に複雑さが生じた場合は Complexity Tracking に記録する。

## Project Structure

### Documentation (this feature)

```text
specs/019-subtitle-bookmark-backup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── ui-contracts.md  # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
looplayer/
├── subtitle_parser.py          # 新規: SRT/ASS パーサー（F-202）
├── data_backup.py              # 新規: バックアップ・復元ロジック（F-402）
├── i18n.py                     # 変更: F-202・F-402 用メッセージ文字列追加
├── player.py                   # 変更: メニュー項目追加・ハンドラ実装
└── widgets/
    └── bookmark_panel.py       # 変更: undo_bulk_add() 追加（F-202 Undo 対応）

tests/
├── unit/
│   ├── test_subtitle_parser.py # 新規: SRT/ASS パーサーのユニットテスト
│   └── test_data_backup.py     # 新規: バックアップ・復元のユニットテスト
└── integration/
    └── test_subtitle_bookmark_integration.py  # 新規: 字幕→ブックマーク統合テスト
```

**Structure Decision**: 単一プロジェクト構成（Option 1）。新機能ごとに専用モジュール 1 ファイルを追加するプロジェクト慣習に従う。`subtitle_parser.py` は SRT/ASS 解析専用、`data_backup.py` はバックアップ専用とし、`player.py` からはそれぞれのパブリック API のみを呼び出す。

## Complexity Tracking

> *現時点で Constitution 違反なし — このセクションへの記入は不要*

