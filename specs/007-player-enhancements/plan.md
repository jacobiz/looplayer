# Implementation Plan: プレイヤー機能強化

**Branch**: `007-player-enhancements` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)

## Summary

再生操作の精細化（コマ送り・精細シーク・速度ショートカット）、マルチトラック対応（音声・字幕）、スクリーンショット、再生終了時の動作設定、再生位置の記憶、ブックマークメモ、フォルダドロップのプレイリストを実装する。既存の PyQt6 + python-vlc のパターンを踏襲し、3つの新規モジュール（`playback_position.py`・`app_settings.py`・`playlist.py`）と複数ファイルの変更で構成する。

## Technical Context

**Language/Version**: Python 3.12.13
**Primary Dependencies**: PyQt6 6.10.2、python-vlc 3.0.21203（既存）
**Storage**: `~/.looplayer/positions.json`（新規）、`~/.looplayer/settings.json`（新規）、既存の `bookmarks.json`・`recent_files.json` は変更なし
**Testing**: pytest（既存）
**Target Platform**: Linux / Windows / macOS
**Project Type**: Desktop application
**Performance Goals**: スクリーンショット保存 1秒以内（SC-003）、再生位置復元 3秒以内（SC-005）、フォルダドロップ後再生開始 3秒以内（SC-007）
**Constraints**: 追加ライブラリなし（標準ライブラリと既存依存のみ）、QStatusBar を追加（スクリーンショット通知・速度フィードバック用）

## Constitution Check

| 原則 | 適合状況 | 備考 |
|------|---------|------|
| I. テストファースト | ✅ PASS | 各 US に対してユニット→統合テストを先行 |
| II. シンプルさ重視 | ✅ PASS | 新規ライブラリなし、既存 JSON パターンを踏襲 |
| III. 過度な抽象化禁止 | ✅ PASS | 新規モジュール 3 件は複数箇所から参照されるため正当 |
| IV. 日本語コミュニケーション | ✅ PASS | UIラベル・コメント・コミットを日本語で記述 |

**Complexity Tracking**:

| 追加 | 必要理由 | より単純な代替が不可能な理由 |
|------|---------|--------------------------|
| `playback_position.py`（新規モジュール） | 再生位置の読み書き・上限管理ロジックを `player.py` に直書きすると 300 行超の肥大化 | `player.py` は既に 1020 行。独立モジュール化が保守性を確保する最小の手段 |
| `app_settings.py`（新規モジュール） | 再生終了時の動作設定など将来追加される設定のエントリポイント | `player.py` に直書きすると `recent_files.py` 同様の永続化コードが重複し、Constitution III に違反 |
| `playlist.py`（新規モジュール） | フォルダドロップ由来のプレイリスト状態（インデックス管理・自動進行）を管理 | `player.py` に直書きすると `SequentialPlayState` との責務が混在し、テスト困難になる |
| `QStatusBar` 追加 | スクリーンショット保存先・速度の端通知を SC-003/FR-016 が定める「ステータスバー」で提供 | ウィンドウタイトル変更では速度通知と混在し、モーダルダイアログでは操作フローを中断する |

## Project Structure

### Documentation (this feature)

```text
specs/007-player-enhancements/
├── plan.md              ← このファイル
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
└── tasks.md             ← /speckit.tasks output（未作成）
```

### Source Code

```text
looplayer/
├── player.py              # 変更: コマ送り・精細シーク・速度ショートカット・トラック切替
│                          #       スクリーンショット・再生終了動作・位置記憶・フォルダドロップ
│                          #       QStatusBar 追加
├── bookmark_store.py      # 変更: LoopBookmark に notes フィールド追加
├── bookmark_io.py         # 変更: notes フィールドの export/import 対応
├── playback_position.py   # 新規: PlaybackPosition 読み書き・上限管理
├── app_settings.py        # 新規: AppSettings 読み書き（再生終了時の動作設定等）
├── playlist.py            # 新規: Playlist 状態管理（ファイルリスト・インデックス）
└── widgets/
    ├── bookmark_row.py    # 変更: メモボタン追加・memo_clicked シグナル
    └── bookmark_panel.py  # 変更: メモダイアログ表示・保存連携

tests/
├── unit/
│   ├── test_playback_position.py    # 新規
│   ├── test_app_settings.py         # 新規
│   ├── test_playlist.py             # 新規
│   └── test_bookmark_notes.py       # 新規
└── integration/
    └── test_player_enhancements.py  # 新規（US1〜US7 の統合テスト）
```

**Structure Decision**: 既存プロジェクトのフラットな `looplayer/` 構成を踏襲する。新規モジュールは `recent_files.py`・`sequential.py` と同一レベルに配置し、`widgets/` サブパッケージの変更は最小限に留める。
