# Implementation Plan: AB Loop Bookmarks & Sequential Playback

**Branch**: `002-ab-loop-bookmarks` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-ab-loop-bookmarks/spec.md`

## Summary

既存のABループ機能を拡張し、複数のAB区間をブックマークとして保存・管理・即時切り替えできる機能を追加する。さらに登録済みブックマークを順番につなげて連続再生する機能を実装する。永続化はローカルJSONファイル（`~/.looplayer/bookmarks.json`）を用い、動画ファイルパスをキーとして管理する。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2、python-vlc 3.0.21203（既存）
**Storage**: `~/.looplayer/bookmarks.json`（ローカルJSONファイル、追加ライブラリなし）
**Testing**: pytest
**Target Platform**: Linux / Windows デスクトップ
**Project Type**: デスクトップアプリ（PyQt6 GUI）
**Performance Goals**: ブックマーク切り替え 0.5秒以内、連続再生遷移 0.5秒以内
**Constraints**: 追加の外部依存なし、オフライン動作
**Scale/Scope**: ブックマーク最大100件/動画、複数動画対応

## Constitution Check

*GATE: Phase 0 研究前に確認。Phase 1 設計後に再確認。*

| 原則 | 状態 | 確認内容 |
|------|------|---------|
| I. テストファースト | ✅ PASS | 全ての実装ステップでテスト先行（quickstart.md に明記） |
| II. シンプルさ重視 | ✅ PASS | 追加依存なし、既存タイマー流用、JSONファイル直接操作 |
| III. 過度な抽象化の禁止 | ✅ PASS | Repository パターン不使用、`BookmarkStore` は直接操作クラス。1ファイル分離は `main.py` の肥大化防止のため正当化済み |
| IV. 日本語コミュニケーション | ✅ PASS | UIラベル・コメント・コミットメッセージ日本語。ログ・例外は英語可 |

**Complexity Tracking**: 違反なし（記録不要）

## Project Structure

### Documentation (this feature)

```text
specs/002-ab-loop-bookmarks/
├── plan.md              # このファイル
├── research.md          # Phase 0 完了済み
├── data-model.md        # Phase 1 完了済み
├── quickstart.md        # Phase 1 完了済み
└── tasks.md             # /speckit.tasks コマンドで生成
```

### Source Code (repository root)

```text
bookmark_store.py        # LoopBookmark + BookmarkStore（新規）
main.py                  # VideoPlayer拡張（BookmarkPanel, SequentialPlayState 追加）

tests/
├── unit/
│   ├── test_bookmark_store.py      # LoopBookmark バリデーション、BookmarkStore CRUD（新規）
│   └── test_sequential_play.py     # SequentialPlayState 状態遷移（新規）
└── integration/
    └── test_bookmark_integration.py  # パネル統合フロー（新規）
```

**Structure Decision**: 既存の単一プロジェクト構成を維持。`bookmark_store.py` のみ新規追加し、UI統合は `main.py` を拡張する。`main.py` 内に `BookmarkPanel`（`QWidget` サブクラス）を定義し、`VideoPlayer._build_ui()` から組み込む。

## Phase 0: Research — 完了

詳細は [research.md](research.md) 参照。

主な決定事項:
- **保存先**: `~/.looplayer/bookmarks.json`（クロスプラットフォーム、追加依存なし）
- **並び替えUI**: `QListWidget.InternalMove` + `dropEvent` オーバーライドで並び替え後に永続化
- **連続再生**: 既存 `_on_timer()` を拡張して `SequentialPlayState` を制御
- **行ウィジェット**: `QListWidget` + `setItemWidget()` でカスタム行（名前、時刻、繰り返し数、削除ボタン）
- **AB統合**: ブックマーク選択時に `ab_point_a/b` と `ab_loop_active` を直接更新

## Phase 1: Design — 完了

### data-model.md

詳細は [data-model.md](data-model.md) 参照。

- `LoopBookmark`: id / name / point_a_ms / point_b_ms / repeat_count / order
- `BookmarkStore`: JSON永続化（load / save / add / delete / update_order）
- `SequentialPlayState`: 連続再生進行状態（current_index / remaining_repeats / active）

### quickstart.md

詳細は [quickstart.md](quickstart.md) 参照。

実装3ステップ（各ステップでテストファースト）:
1. `bookmark_store.py` のテストと実装
2. `SequentialPlayState` のテストと実装（`main.py` 内）
3. `BookmarkPanel` UI統合と統合テスト

### Contracts

本機能はデスクトップアプリの内部コンポーネントであり、外部向けインターフェースは存在しない。contracts/ は不要。

## Constitution Check（Phase 1 後）

| 原則 | 状態 | 確認内容 |
|------|------|---------|
| I. テストファースト | ✅ PASS | 3テストファイル定義済み、全ステップで RED→GREEN サイクル |
| II. シンプルさ重視 | ✅ PASS | 標準ライブラリのみ追加（`uuid`, `json`, `pathlib`）、既存機構を最大限流用 |
| III. 過度な抽象化の禁止 | ✅ PASS | `BookmarkStore` は単一責任で必要最小限。`SequentialPlayState` は `main.py` 内のデータクラス |
| IV. 日本語コミュニケーション | ✅ PASS | UIラベル・コメント日本語方針を維持 |
